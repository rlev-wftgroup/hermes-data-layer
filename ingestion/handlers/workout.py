from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from db import hermes as db_hermes
from models.workout import WorkoutRecord

logger = logging.getLogger(__name__)
router = APIRouter()

# HAE date format: "2026-06-14 09:00:00 -0400"
_DATE_FMT = "%Y-%m-%d %H:%M:%S %z"


def _parse_dt(s: str) -> datetime:
    return datetime.strptime(s, _DATE_FMT)


class _Qty(BaseModel):
    qty: float
    units: str | None = None


class _HRStats(BaseModel):
    min: _Qty | None = None
    avg: _Qty | None = None
    max: _Qty | None = None


class _RoutePoint(BaseModel):
    latitude: float
    longitude: float
    altitude: float | None = None
    course: float | None = None
    courseAccuracy: float | None = None
    horizontalAccuracy: float | None = None
    verticalAccuracy: float | None = None
    timestamp: str | None = None
    speed: float | None = None
    speedAccuracy: float | None = None


class _HRDataPoint(BaseModel):
    date: str
    Min: float | None = None
    Avg: float | None = None
    Max: float | None = None
    units: str | None = None
    source: str | None = None


class _TimedQty(BaseModel):
    date: str
    qty: float
    units: str | None = None
    source: str | None = None


class _Workout(BaseModel):
    id: str
    name: str
    start: str
    end: str
    duration: float | None = None
    location: str | None = None
    isIndoor: bool | None = None
    activeEnergyBurned: _Qty | None = None
    totalEnergy: _Qty | None = None
    intensity: _Qty | None = None
    distance: _Qty | None = None
    avgSpeed: _Qty | None = None
    maxSpeed: _Qty | None = None
    elevationUp: _Qty | None = None
    elevationDown: _Qty | None = None
    heartRate: _HRStats | None = None
    avgHeartRate: _Qty | None = None
    maxHeartRate: _Qty | None = None
    heartRateData: list[_HRDataPoint] = []
    heartRateRecovery: list[_HRDataPoint] = []
    stepCount: list[_TimedQty] = []
    cyclingCadence: list[_TimedQty] = []
    cyclingPower: list[_TimedQty] = []
    route: list[_RoutePoint] = []
    strokeStyle: str | None = None
    salinity: str | None = None
    swolfScore: float | None = None
    lapLength: _Qty | None = None
    totalSwimmingStrokeCount: _Qty | None = None


class _WorkoutData(BaseModel):
    workouts: list[_Workout]


class WorkoutPayload(BaseModel):
    data: _WorkoutData


def _to_record(w: _Workout) -> WorkoutRecord:
    avg_hr = (
        round(w.heartRate.avg.qty) if w.heartRate and w.heartRate.avg
        else round(w.avgHeartRate.qty) if w.avgHeartRate
        else None
    )
    max_hr = (
        round(w.heartRate.max.qty) if w.heartRate and w.heartRate.max
        else round(w.maxHeartRate.qty) if w.maxHeartRate
        else None
    )
    return WorkoutRecord(
        id=w.id,
        name=w.name,
        start_time=_parse_dt(w.start),
        end_time=_parse_dt(w.end),
        duration_seconds=w.duration,
        location=w.location,
        is_indoor=w.isIndoor,
        active_energy_kcal=w.activeEnergyBurned.qty if w.activeEnergyBurned else None,
        total_energy_kcal=w.totalEnergy.qty if w.totalEnergy else None,
        distance=w.distance.qty if w.distance else None,
        distance_unit=w.distance.units if w.distance else None,
        avg_heart_rate_bpm=avg_hr,
        max_heart_rate_bpm=max_hr,
        avg_speed=w.avgSpeed.qty if w.avgSpeed else None,
        avg_speed_unit=w.avgSpeed.units if w.avgSpeed else None,
        max_speed=w.maxSpeed.qty if w.maxSpeed else None,
        elevation_up=w.elevationUp.qty if w.elevationUp else None,
        elevation_unit=w.elevationUp.units if w.elevationUp else None,
        elevation_down=w.elevationDown.qty if w.elevationDown else None,
        avg_mets=w.intensity.qty if w.intensity else None,
    )


@router.post("/ingest/health/workout")
def ingest_workout(payload: WorkoutPayload, request: Request):
    config = request.app.state.config
    upserted: list[str] = []

    for w in payload.data.workouts:
        record = _to_record(w)
        try:
            db_hermes.upsert_workout(config, record)
            upserted.append(w.id)
        except Exception as exc:
            logger.error("workout upsert failed for %s (%s): %s", w.id, w.name, exc)
            raise HTTPException(status_code=500, detail=str(exc))

    request.app.state.last_ingest["workout"] = datetime.now(timezone.utc).isoformat()
    logger.info("Workout ingest: upserted %d workout(s)", len(upserted))
    return {"status": "ok", "upserted_ids": upserted}
