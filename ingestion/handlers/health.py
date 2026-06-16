from __future__ import annotations

import logging
import statistics
from collections import defaultdict
from datetime import date, datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from db import hermes as db_hermes
from models.biometric_reading import BiometricReading

logger = logging.getLogger(__name__)
router = APIRouter()

# HAE metric name → BiometricReading field
_METRIC_MAP = {
    "resting_heart_rate": "resting_heart_rate",
    "heart_rate_variability": "hrv_ms",
}


class _DataPoint(BaseModel):
    date: str   # "2026-06-14 09:00:00 -0400"
    qty: float
    source: str | None = None


class _Metric(BaseModel):
    name: str
    units: str | None = None
    data: list[_DataPoint]


class _HAEData(BaseModel):
    metrics: list[_Metric]


class HAEPayload(BaseModel):
    data: _HAEData


def _extract_date(date_str: str) -> date:
    """Parse HAE date string — take only the YYYY-MM-DD prefix."""
    return datetime.strptime(date_str[:10], "%Y-%m-%d").date()


@router.post("/ingest/health")
def ingest_health(payload: HAEPayload, request: Request):
    config = request.app.state.config

    # Accumulate qty values per (date, metric_name) — HAE sends multiple
    # readings per day per metric (e.g. hourly HRV). Average them per day.
    by_date: dict[date, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    for metric in payload.data.metrics:
        if metric.name not in _METRIC_MAP:
            logger.debug("Ignoring unmapped HAE metric: %s", metric.name)
            continue
        for point in metric.data:
            day = _extract_date(point.date)
            by_date[day][metric.name].append(point.qty)

    if not by_date:
        return {"status": "ok", "upserted_dates": []}

    upserted: list[str] = []
    for log_date, metrics in sorted(by_date.items()):
        rhr = metrics.get("resting_heart_rate", [])
        hrv = metrics.get("heart_rate_variability", [])

        reading = BiometricReading(
            log_date=log_date,
            resting_heart_rate=round(statistics.mean(rhr)) if rhr else None,
            hrv_ms=round(statistics.mean(hrv), 2) if hrv else None,
        )

        try:
            db_hermes.upsert_biometric_reading(config, reading)
            upserted.append(log_date.isoformat())
        except Exception as exc:
            logger.error("hermes DB upsert failed for %s: %s", log_date, exc)
            raise HTTPException(status_code=500, detail=str(exc))

    request.app.state.last_ingest["health"] = datetime.now(timezone.utc).isoformat()
    logger.info("Health ingest: upserted %d date(s): %s", len(upserted), upserted)
    return {"status": "ok", "upserted_dates": upserted}
