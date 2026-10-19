def validate_invoice(p):
    errors=[]
    for f in ("seller_id","invoice_number","issue_date","currency","buyer","lines","total"):
        if f not in p or p[f] in (None,"",[]):
            errors.append({"field":f,"code":"REQUIRED","message":f"{f} is required"})
    if p.get("currency") and len(str(p["currency"])) != 3:
        errors.append({"field":"currency","code":"FORMAT","message":"currency must be 3 letters"})
    if not isinstance(p.get("lines"),list) or not p.get("lines"):
        errors.append({"field":"lines","code":"MIN_ITEMS","message":"at least one line required"})
    return errors
