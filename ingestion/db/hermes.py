from __future__ import annotations

import psycopg2

from config import Config
from models.biometric_reading import BiometricReading
from models.workout import WorkoutRecord


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


def upsert_workout(config: Config, w: WorkoutRecord) -> None:
    sql = """
    INSERT INTO workouts (
        id, name, start_time, end_time, duration_seconds,
        location, is_indoor,
        active_energy_kcal, total_energy_kcal,
        distance, distance_unit,
        avg_heart_rate_bpm, max_heart_rate_bpm,
        avg_speed, avg_speed_unit, max_speed,
        elevation_up, elevation_unit, elevation_down,
        avg_mets
    ) VALUES (
        %(id)s, %(name)s, %(start_time)s, %(end_time)s, %(duration_seconds)s,
        %(location)s, %(is_indoor)s,
        %(active_energy_kcal)s, %(total_energy_kcal)s,
        %(distance)s, %(distance_unit)s,
        %(avg_heart_rate_bpm)s, %(max_heart_rate_bpm)s,
        %(avg_speed)s, %(avg_speed_unit)s, %(max_speed)s,
        %(elevation_up)s, %(elevation_unit)s, %(elevation_down)s,
        %(avg_mets)s
    )
    ON CONFLICT (id) DO UPDATE SET
        name                 = EXCLUDED.name,
        start_time           = EXCLUDED.start_time,
        end_time             = EXCLUDED.end_time,
        duration_seconds     = EXCLUDED.duration_seconds,
        location             = EXCLUDED.location,
        is_indoor            = EXCLUDED.is_indoor,
        active_energy_kcal   = EXCLUDED.active_energy_kcal,
        total_energy_kcal    = EXCLUDED.total_energy_kcal,
        distance             = EXCLUDED.distance,
        distance_unit        = EXCLUDED.distance_unit,
        avg_heart_rate_bpm   = EXCLUDED.avg_heart_rate_bpm,
        max_heart_rate_bpm   = EXCLUDED.max_heart_rate_bpm,
        avg_speed            = EXCLUDED.avg_speed,
        avg_speed_unit       = EXCLUDED.avg_speed_unit,
        max_speed            = EXCLUDED.max_speed,
        elevation_up         = EXCLUDED.elevation_up,
        elevation_unit       = EXCLUDED.elevation_unit,
        elevation_down       = EXCLUDED.elevation_down,
        avg_mets             = EXCLUDED.avg_mets
    """
    with psycopg2.connect(config.hermes_db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, {
                "id": w.id,
                "name": w.name,
                "start_time": w.start_time,
                "end_time": w.end_time,
                "duration_seconds": w.duration_seconds,
                "location": w.location,
                "is_indoor": w.is_indoor,
                "active_energy_kcal": w.active_energy_kcal,
                "total_energy_kcal": w.total_energy_kcal,
                "distance": w.distance,
                "distance_unit": w.distance_unit,
                "avg_heart_rate_bpm": w.avg_heart_rate_bpm,
                "max_heart_rate_bpm": w.max_heart_rate_bpm,
                "avg_speed": w.avg_speed,
                "avg_speed_unit": w.avg_speed_unit,
                "max_speed": w.max_speed,
                "elevation_up": w.elevation_up,
                "elevation_unit": w.elevation_unit,
                "elevation_down": w.elevation_down,
                "avg_mets": w.avg_mets,
            })
