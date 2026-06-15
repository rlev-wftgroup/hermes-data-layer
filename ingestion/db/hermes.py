from __future__ import annotations

import psycopg2

from config import Config
from models.biometric_reading import BiometricReading


def get_conn(config: Config):
    return psycopg2.connect(config.hermes_db_url)


def upsert_biometric_reading(config: Config, reading: BiometricReading) -> None:
    # Schema note: daily_biometric_readiness requires INTEGER columns
    # systolic_bp and diastolic_bp instead of the original morning_blood_pressure TEXT.
    sql = """
    INSERT INTO daily_biometric_readiness (
        log_date, resting_heart_rate, hrv_ms, sleep_score,
        systolic_bp, diastolic_bp,
        subjective_joint_pain, trailing_dietary_compliance
    ) VALUES (
        %(log_date)s, %(resting_heart_rate)s, %(hrv_ms)s, %(sleep_score)s,
        %(systolic_bp)s, %(diastolic_bp)s,
        %(subjective_joint_pain)s, %(trailing_dietary_compliance)s
    )
    ON CONFLICT (log_date) DO UPDATE SET
        resting_heart_rate          = EXCLUDED.resting_heart_rate,
        hrv_ms                      = EXCLUDED.hrv_ms,
        sleep_score                 = EXCLUDED.sleep_score,
        systolic_bp                 = EXCLUDED.systolic_bp,
        diastolic_bp                = EXCLUDED.diastolic_bp,
        subjective_joint_pain       = EXCLUDED.subjective_joint_pain,
        trailing_dietary_compliance = EXCLUDED.trailing_dietary_compliance
    """
    with psycopg2.connect(config.hermes_db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, {
                "log_date": reading.log_date,
                "resting_heart_rate": reading.resting_heart_rate,
                "hrv_ms": reading.hrv_ms,
                "sleep_score": reading.sleep_score,
                "systolic_bp": reading.systolic_bp,
                "diastolic_bp": reading.diastolic_bp,
                "subjective_joint_pain": reading.subjective_joint_pain,
                "trailing_dietary_compliance": reading.trailing_dietary_compliance,
            })
