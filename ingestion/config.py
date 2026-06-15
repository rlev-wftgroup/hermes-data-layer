from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Config:
    bills_db_url: str
    hermes_db_url: str
    lm_studio_url: str
    lm_studio_model: str
    ingest_port: int

    @classmethod
    def from_env(cls) -> Config:
        bills_db_url = os.environ.get("BILLS_DB_URL", "")
        hermes_db_url = os.environ.get("HERMES_DB_URL", "")
        errors: list[str] = []
        if not bills_db_url:
            errors.append("BILLS_DB_URL is not set")
        if not hermes_db_url:
            errors.append("HERMES_DB_URL is not set")
        if errors:
            raise ValueError("Configuration errors:\n" + "\n".join(f"  • {e}" for e in errors))
        return cls(
            bills_db_url=bills_db_url,
            hermes_db_url=hermes_db_url,
            lm_studio_url=os.environ.get("LM_STUDIO_URL", "http://localhost:1234"),
            lm_studio_model=os.environ.get("LM_STUDIO_MODEL", "qwen2.5-7b-instruct-1m"),
            ingest_port=int(os.environ.get("INGEST_PORT", "8421")),
        )
