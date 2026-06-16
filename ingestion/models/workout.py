from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class WorkoutRecord:
    id: str                          # UUID from HAE — primary key
    name: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float | None = None
    location: str | None = None
    is_indoor: bool | None = None
    active_energy_kcal: float | None = None
    total_energy_kcal: float | None = None
    distance: float | None = None
    distance_unit: str | None = None
    avg_heart_rate_bpm: int | None = None
    max_heart_rate_bpm: int | None = None
    avg_speed: float | None = None
    avg_speed_unit: str | None = None
    max_speed: float | None = None
    elevation_up: float | None = None
    elevation_unit: str | None = None
    elevation_down: float | None = None
    avg_mets: float | None = None
