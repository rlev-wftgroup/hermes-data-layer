from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import psycopg2
from fastapi import FastAPI, Request

from config import Config
from handlers import bills, health

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = Config.from_env()
    app.state.config = config
    app.state.last_ingest = {"bills": None, "health": None}

    for label, url in [("bills", config.bills_db_url), ("hermes", config.hermes_db_url)]:
        try:
            conn = psycopg2.connect(url, connect_timeout=5)
            conn.close()
            logger.info("DB %s: connection OK", label)
        except Exception as exc:
            logger.warning("DB %s: connection FAILED — %s", label, exc)

    yield


app = FastAPI(title="Hermes Ingestion Server", lifespan=lifespan)
app.include_router(bills.router)
app.include_router(health.router)


@app.get("/status")
def status(request: Request):
    config = request.app.state.config
    db_status: dict[str, str] = {}
    for label, url in [("bills", config.bills_db_url), ("hermes", config.hermes_db_url)]:
        try:
            conn = psycopg2.connect(url, connect_timeout=5)
            conn.close()
            db_status[label] = "ok"
        except Exception as exc:
            db_status[label] = f"error: {exc}"
    return {
        "status": "ok",
        "db": db_status,
        "last_ingest": request.app.state.last_ingest,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
