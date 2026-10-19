# Finkraft UAE E-Invoicing Platform — Starter

GitHub-ready FastAPI starter for durable invoice intake, ASP routing metadata, normalized status handling, and ASP B webhook deduplication.

**Not production-certified:** full PINT AE rules, ASP credentials/signatures, regulatory semantics, external reconciliation, and a production worker must be implemented against official specs and ASP contracts.

## Key safety behavior
- Invoice identity is unique by `(tenant_id, seller_id, invoice_number)`.
- Bulk intake writes invoice, submission attempt, and outbox intent in one SQLite transaction.
- ASP timeouts are ambiguous: mark `SUBMISSION_UNKNOWN`; do not blindly retry.
- ASP B has no duplicate check or polling endpoint in the supplied mock spec. An uncertain ASP B request must not be automatically resubmitted.
- Webhook inbox deduplicates provider event IDs. Verify webhook signatures before production use.
- SQLite is for local demo. Use PostgreSQL, durable workers/workflows, shared rate limiting, backups, and monitoring in production.

## Run
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload
pytest
```
API docs: http://127.0.0.1:8000/docs

## Example intake
```bash
curl -X POST http://127.0.0.1:8000/api/v1/invoices/bulk \
  -H 'Content-Type: application/json' -H 'X-Tenant-ID: tenant_demo' \
  -d '{"asp_id":"asp_a","invoices":[{"seller_id":"seller_demo","invoice_number":"INV-1001","issue_date":"2026-10-19","currency":"AED","buyer":{"name":"Buyer LLC"},"lines":[{"description":"Service","quantity":1,"unit_price":100}],"total":100}]}'
```
Intake means accepted by Finkraft, not accepted by an ASP. This starter persists outbox work but does not run an external submission worker yet.

## GitHub
```bash
git init && git add . && git commit -m 'Initial Finkraft e-invoicing platform starter'
gh repo create finkraft-einvoice-platform --private --source=. --push
```
