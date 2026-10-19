import hashlib, json, uuid
from datetime import datetime, timezone
from fastapi import FastAPI, Header, HTTPException
from app.db import init_db, connect
from app.validation import validate_invoice
from app.status import normalize, can_advance, Status

app=FastAPI(title="Finkraft UAE E-Invoicing Platform",version="0.1.0")
def now(): return datetime.now(timezone.utc).isoformat()
def digest(p): return hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
@app.on_event("startup")
def startup(): init_db()
@app.get("/health")
def health(): return {"status":"ok"}
@app.post("/api/v1/invoices/bulk")
def bulk(body:dict,x_tenant_id:str=Header(...)):
    if body.get("asp_id") not in ("asp_a","asp_b") or not isinstance(body.get("invoices"),list) or not body["invoices"]:
        raise HTTPException(400,"asp_id and non-empty invoices are required")
    accepted=[]; rejected=[]; c=connect()
    try:
        c.execute("BEGIN IMMEDIATE")
        for p in body["invoices"]:
            errs=validate_invoice(p)
            if errs:
                rejected.append({"invoice_number":p.get("invoice_number"),"errors":errs}); continue
            iid=str(uuid.uuid4()); sid=str(uuid.uuid4()); eid=str(uuid.uuid4()); ts=now(); ph=digest(p)
            try:
                c.execute("INSERT INTO invoices(invoice_id,tenant_id,seller_id,invoice_number,asp_id,payload_json,payload_hash,status,submission_status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                  (iid,x_tenant_id,p["seller_id"],p["invoice_number"],body["asp_id"],json.dumps(p),ph,Status.READY_TO_SUBMIT.value,"READY_TO_SUBMIT",ts))
            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    old=c.execute("SELECT invoice_id FROM invoices WHERE tenant_id=? AND seller_id=? AND invoice_number=?",(x_tenant_id,p["seller_id"],p["invoice_number"])).fetchone()
                    rejected.append({"invoice_number":p["invoice_number"],"code":"DUPLICATE_INVOICE","existing_invoice_id":old[0] if old else None}); continue
                raise
            c.execute("INSERT INTO submission_attempts(submission_id,invoice_id,attempt_number,asp_id,payload_hash,status,created_at) VALUES(?,?,?,?,?,?,?)",(sid,iid,1,body["asp_id"],ph,"READY_TO_SUBMIT",ts))
            c.execute("INSERT INTO outbox(event_id,aggregate_id,event_type,payload_json,created_at) VALUES(?,?,?,?,?)",(eid,iid,"SUBMIT_INVOICE",json.dumps({"invoice_id":iid,"submission_id":sid,"asp_id":body["asp_id"]}),ts))
            accepted.append({"invoice_id":iid,"invoice_number":p["invoice_number"]})
        c.execute("COMMIT")
    except Exception:
        c.execute("ROLLBACK"); raise
    finally: c.close()
    return {"batch_id":str(uuid.uuid4()),"status":"ACCEPTED_FOR_PROCESSING","accepted_count":len(accepted),"rejected_count":len(rejected),"accepted":accepted,"rejected":rejected}
@app.get("/api/v1/invoices/{invoice_id}")
def get_invoice(invoice_id:str,x_tenant_id:str=Header(...)):
    with connect() as c: r=c.execute("SELECT * FROM invoices WHERE invoice_id=? AND tenant_id=?",(invoice_id,x_tenant_id)).fetchone()
    if not r: raise HTTPException(404,"Invoice not found")
    return {k:r[k] for k in ("invoice_id","invoice_number","asp_id","status","submission_status","buyer_delivery_status","tax_reporting_status","payload_hash")}
@app.post("/api/v1/webhooks/asp-b")
def webhook(event:dict):
    # TODO: authenticate ASP B signature before exposing publicly.
    eid,jid,ext=event.get("event_id"),event.get("job_id"),event.get("status")
    if not all((eid,jid,ext)): raise HTTPException(400,"event_id, job_id and status are required")
    try: mapped=normalize("asp_b",ext)
    except ValueError as e: raise HTTPException(400,str(e))
    with connect() as c:
        c.execute("BEGIN IMMEDIATE")
        try:
            c.execute("INSERT INTO webhook_inbox(asp_id,event_id,job_id,status,payload_json,received_at) VALUES('asp_b',?,?,?,?,?)",(eid,jid,ext,json.dumps(event),now()))
        except Exception as e:
            c.execute("ROLLBACK")
            if "UNIQUE constraint failed" in str(e): return {"accepted":True,"duplicate":True}
            raise
        row=c.execute("SELECT s.invoice_id,i.status FROM submission_attempts s JOIN invoices i ON i.invoice_id=s.invoice_id WHERE s.asp_id='asp_b' AND s.external_id=? ORDER BY s.attempt_number DESC LIMIT 1",(jid,)).fetchone()
        if not row:
            c.execute("COMMIT"); return {"accepted":True,"processed":False,"reason":"job_not_linked_yet"}
        iid,current=row["invoice_id"],row["status"]
        if can_advance(current,mapped):
            c.execute("UPDATE invoices SET status=? WHERE invoice_id=?",(mapped.value,iid))
            if mapped==Status.DELIVERED: c.execute("UPDATE invoices SET buyer_delivery_status=? WHERE invoice_id=?",(ext,iid))
            elif mapped==Status.REPORTED: c.execute("UPDATE invoices SET buyer_delivery_status='BUYER_RECEIVED',tax_reporting_status=? WHERE invoice_id=?",(ext,iid))
            elif mapped in (Status.REJECTED,Status.FAILED): c.execute("UPDATE invoices SET submission_status=? WHERE invoice_id=?",(mapped.value,iid))
        c.execute("UPDATE webhook_inbox SET processed_at=? WHERE asp_id='asp_b' AND event_id=?",(now(),eid)); c.execute("COMMIT")
    return {"accepted":True,"processed":True}
@app.post("/api/v1/sellers/{seller_id}/routing")
def routing(seller_id:str,body:dict,x_tenant_id:str=Header(...)):
    asp=body.get("asp_id")
    if asp not in ("asp_a","asp_b"): raise HTTPException(400,"asp_id must be asp_a or asp_b")
    with connect() as c:
        c.execute("INSERT INTO seller_routing(tenant_id,seller_id,asp_id,updated_at) VALUES(?,?,?,?) ON CONFLICT(tenant_id,seller_id) DO UPDATE SET asp_id=excluded.asp_id,updated_at=excluded.updated_at",(x_tenant_id,seller_id,asp,now()))
    return {"seller_id":seller_id,"asp_id_for_future_invoices":asp}
