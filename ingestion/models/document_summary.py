"""DocumentSummary model and LM Studio client — migrated from scan-watcher/summarizer.py.

Changes from scan-watcher:
- requests → httpx (already a FastAPI dep)
- Config injected instead of module-level os.environ reads
- to_markdown() removed (Anytype-specific, not needed here)
- summarize() never raises; errors captured in DocumentSummary.raw_error
"""
from __future__ import annotations

import json
from dataclasses import dataclass

import httpx

from config import Config

SYSTEM_PROMPT = """\
You are a document processor. Analyze the provided document text and respond with \
a JSON object only — no markdown, no explanation, no code fences.

The JSON must have exactly these keys:
{
  "summary": "2-3 sentence plain English summary of what this document is",
  "vendor": "company or sender name, or null",
  "document_type": "e.g. utility bill, invoice, statement, letter, receipt, contract, or other",
  "date": "document date in YYYY-MM-DD format, or null",
  "due_date": "payment due date in YYYY-MM-DD format, or null",
  "amount_due": "total amount due as a string e.g. '$142.50', or null",
  "account_number": "account or reference number, or null"
}

If a field is not present in the document, use null. Do not invent values.\
"""


def _strip_json_fences(content: str) -> str:
    """Strip accidental markdown code fences from an LLM response."""
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()
    return content


@dataclass
class DocumentSummary:
    summary: str = ""
    vendor: str | None = None
    document_type: str | None = None
    date: str | None = None
    due_date: str | None = None
    amount_due: str | None = None
    account_number: str | None = None
    raw_error: str | None = None  # set if LM Studio call failed

    @property
    def succeeded(self) -> bool:
        return self.raw_error is None and bool(self.summary)


def summarize(text: str, config: Config, max_input_chars: int = 12_000) -> DocumentSummary:
    """Call LM Studio and return a DocumentSummary. Never raises."""
    if not text or not text.strip():
        return DocumentSummary(raw_error="No text to summarize")

    truncated = text[:max_input_chars]
    if len(text) > max_input_chars:
        truncated += "\n\n[document truncated for summarization]"

    payload = {
        "model": config.lm_studio_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Document:\n\n{truncated}"},
        ],
        "temperature": 0.1,
        "max_tokens": 512,
    }

    try:
        resp = httpx.post(
            f"{config.lm_studio_url}/v1/chat/completions",
            json=payload,
            timeout=120.0,
        )
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        return DocumentSummary(raw_error=f"LM Studio request failed: {exc}")

    try:
        content = resp.json()["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as exc:
        return DocumentSummary(raw_error=f"Unexpected LM Studio response shape: {exc}")

    content = _strip_json_fences(content)

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        return DocumentSummary(raw_error=f"Model returned non-JSON: {exc} — got: {content[:200]}")

    return DocumentSummary(
        summary=data.get("summary", ""),
        vendor=data.get("vendor"),
        document_type=data.get("document_type"),
        date=data.get("date"),
        due_date=data.get("due_date"),
        amount_due=data.get("amount_due"),
        account_number=data.get("account_number"),
    )
