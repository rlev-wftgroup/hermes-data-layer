from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from db import bills as db_bills
from models.document_summary import summarize

logger = logging.getLogger(__name__)
router = APIRouter()


class BillIngestPayload(BaseModel):
    filename: str
    raw_text: str
    file_path: str
    file_size_bytes: int
    scanned_at: str  # ISO 8601 from scan-watcher


@router.post("/ingest/bills")
def ingest_bill(payload: BillIngestPayload, request: Request):
    config = request.app.state.config

    doc_summary = summarize(payload.raw_text, config)
    if not doc_summary.succeeded:
        logger.warning(
            "LM Studio summarization failed for %s — storing raw text only. Error: %s",
            payload.filename,
            doc_summary.raw_error,
        )

    try:
        db_bills.upsert_document(
            config,
            filename=payload.filename,
            scanned_at=payload.scanned_at,
            file_path=payload.file_path,
            file_size_bytes=payload.file_size_bytes,
            raw_text=payload.raw_text,
            summary=doc_summary,
        )
    except Exception as exc:
        logger.error("bills DB upsert failed for %s: %s", payload.filename, exc)
        raise HTTPException(status_code=500, detail=str(exc))

    request.app.state.last_ingest["bills"] = datetime.now(timezone.utc).isoformat()
    return {
        "status": "ok",
        "filename": payload.filename,
        "summarized": doc_summary.succeeded,
    }
