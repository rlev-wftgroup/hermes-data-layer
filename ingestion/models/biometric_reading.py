"""BiometricReading — mirrors DocumentSummary pattern for health data."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class BiometricReading:
    log_date: date
    resting_heart_rate: int | None = None
    hrv_ms: float | None = None
    sleep_score: float | None = None
    # bloodPressure HAE field is split into two integer columns
    systolic_bp: int | None = None
    diastolic_bp: int | None = None
    subjective_joint_pain: int | None = None
    trailing_dietary_compliance: float | None = None
