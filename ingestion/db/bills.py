from __future__ import annotations

import psycopg2

from config import Config
from models.document_summary import DocumentSummary


def get_conn(config: Config):
    return psycopg2.connect(config.bills_db_url)


def upsert_document(
    config: Config,
    *,
    filename: str,
    scanned_at: str,
    file_path: str,
    file_size_bytes: int,
    raw_text: str,
    summary: DocumentSummary,
) -> None:
    sql = """
    INSERT INTO documents (
        filename, scanned_at, file_path, file_size_bytes,
        vendor, document_type, document_date, due_date,
        amount_due, account_number, summary, raw_text
    ) VALUES (
        %(filename)s, %(scanned_at)s, %(file_path)s, %(file_size_bytes)s,
        %(vendor)s, %(document_type)s, %(document_date)s, %(due_date)s,
        %(amount_due)s, %(account_number)s, %(summary)s, %(raw_text)s
    )
    ON CONFLICT (filename) DO UPDATE SET
        scanned_at      = EXCLUDED.scanned_at,
        file_path       = EXCLUDED.file_path,
        file_size_bytes = EXCLUDED.file_size_bytes,
        vendor          = EXCLUDED.vendor,
        document_type   = EXCLUDED.document_type,
        document_date   = EXCLUDED.document_date,
        due_date        = EXCLUDED.due_date,
        amount_due      = EXCLUDED.amount_due,
        account_number  = EXCLUDED.account_number,
        summary         = EXCLUDED.summary,
        raw_text        = EXCLUDED.raw_text
    """
    # anytype_object_id is not touched — preserve any existing value
    params = {
        "filename": filename,
        "scanned_at": scanned_at,
        "file_path": file_path,
        "file_size_bytes": file_size_bytes,
        "vendor": summary.vendor if summary.succeeded else None,
        "document_type": summary.document_type if summary.succeeded else None,
        "document_date": summary.date if summary.succeeded else None,
        "due_date": summary.due_date if summary.succeeded else None,
        "amount_due": summary.amount_due if summary.succeeded else None,
        "account_number": summary.account_number if summary.succeeded else None,
        "summary": summary.summary if summary.succeeded else None,
        "raw_text": raw_text,
    }
    with psycopg2.connect(config.bills_db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
