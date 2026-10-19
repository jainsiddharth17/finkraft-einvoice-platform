import os, sqlite3
DB_PATH = os.getenv("DATABASE_PATH", "./finkraft.db")
def connect():
    c = sqlite3.connect(DB_PATH, timeout=30, isolation_level=None)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    c.execute("PRAGMA journal_mode=WAL")
    return c
def init_db():
    with connect() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS invoices(
          invoice_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, seller_id TEXT NOT NULL,
          invoice_number TEXT NOT NULL, asp_id TEXT NOT NULL, payload_json TEXT NOT NULL,
          payload_hash TEXT NOT NULL, status TEXT NOT NULL, submission_status TEXT NOT NULL,
          buyer_delivery_status TEXT NOT NULL DEFAULT 'PENDING',
          tax_reporting_status TEXT NOT NULL DEFAULT 'PENDING', created_at TEXT NOT NULL,
          UNIQUE(tenant_id,seller_id,invoice_number));
        CREATE TABLE IF NOT EXISTS submission_attempts(
          submission_id TEXT PRIMARY KEY, invoice_id TEXT NOT NULL REFERENCES invoices(invoice_id),
          attempt_number INTEGER NOT NULL, asp_id TEXT NOT NULL, external_id TEXT,
          payload_hash TEXT NOT NULL, status TEXT NOT NULL, error_json TEXT,
          created_at TEXT NOT NULL, UNIQUE(invoice_id,attempt_number));
        CREATE TABLE IF NOT EXISTS outbox(
          event_id TEXT PRIMARY KEY, aggregate_id TEXT NOT NULL, event_type TEXT NOT NULL,
          payload_json TEXT NOT NULL, created_at TEXT NOT NULL, published_at TEXT);
        CREATE TABLE IF NOT EXISTS webhook_inbox(
          asp_id TEXT NOT NULL, event_id TEXT NOT NULL, job_id TEXT NOT NULL,
          status TEXT NOT NULL, payload_json TEXT NOT NULL, received_at TEXT NOT NULL,
          processed_at TEXT, PRIMARY KEY(asp_id,event_id));
        CREATE TABLE IF NOT EXISTS seller_routing(
          tenant_id TEXT NOT NULL, seller_id TEXT NOT NULL, asp_id TEXT NOT NULL,
          updated_at TEXT NOT NULL, PRIMARY KEY(tenant_id,seller_id));
        ''')
