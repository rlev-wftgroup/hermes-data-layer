from __future__ import annotations

import logging
from datetime import date, datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from db import hermes as db_hermes
from models.biometric_reading import BiometricReading

logger = logging.getLogger(__name__)
router = APIRouter()


class HealthIngestPayload(BaseModel):
    log_date: date
    restingHeartRate: int | None = None
    heartRateVariabilitySDNN: float | None = None
    sleepScore: float | None = None           # HAE sleepAnalysis.efficiency (0.0–1.0)
    bloodPressure: str | None = None          # e.g. "118/76" — split into systolic/diastolic
    subjectiveJointPain: int | None = None    # 0–10 scale, caller-supplied
    trailingDietaryCompliance: float | None = None  # 0.0–1.0


def _parse_blood_pressure(value: str | None) -> tuple[int | None, int | None]:
    if not value:
        return None, None
    parts = value.replace(" ", "").split("/")
    if len(parts) != 2:
        logger.warning("Unparseable bloodPressure value: %r", value)
        return None, None
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        logger.warning("Non-integer bloodPressure parts: %r", value)
        return None, None


@router.post("/ingest/health")
def ingest_health(payload: HealthIngestPayload, request: Request):
    config = request.app.state.config

    systolic, diastolic = _parse_blood_pressure(payload.bloodPressure)

    reading = BiometricReading(
        log_date=payload.log_date,
        resting_heart_rate=payload.restingHeartRate,
        hrv_ms=payload.heartRateVariabilitySDNN,
        sleep_score=payload.sleepScore,
        systolic_bp=systolic,
        diastolic_bp=diastolic,
        subjective_joint_pain=payload.subjectiveJointPain,
        trailing_dietary_compliance=payload.trailingDietaryCompliance,
    )

    try:
        db_hermes.upsert_biometric_reading(config, reading)
    except Exception as exc:
        logger.error("hermes DB upsert failed for %s: %s", payload.log_date, exc)
        raise HTTPException(status_code=500, detail=str(exc))

    request.app.state.last_ingest["health"] = datetime.now(timezone.utc).isoformat()
    return {"status": "ok", "log_date": payload.log_date.isoformat()}
