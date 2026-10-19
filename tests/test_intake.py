import os,tempfile
os.environ["DATABASE_PATH"]=tempfile.mktemp(suffix=".db")
from fastapi.testclient import TestClient
from app.main import app
from app.db import init_db
init_db()
client=TestClient(app)
def payload(n="INV-1"):
 return {"seller_id":"seller-1","invoice_number":n,"issue_date":"2026-10-19","currency":"AED","buyer":{"name":"Buyer"},"lines":[{"description":"Service","quantity":1,"unit_price":100}],"total":100}
def test_duplicate_invoice_is_rejected():
 h={"X-Tenant-ID":"tenant-1"}
 a=client.post("/api/v1/invoices/bulk",headers=h,json={"asp_id":"asp_a","invoices":[payload()]})
 b=client.post("/api/v1/invoices/bulk",headers=h,json={"asp_id":"asp_a","invoices":[payload()]})
 assert a.json()["accepted_count"]==1
 assert b.json()["rejected"][0]["code"]=="DUPLICATE_INVOICE"
