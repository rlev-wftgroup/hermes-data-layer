# Hermes Data Layer

Stateless ingestion server for the Hermes personal data platform. Receives structured payloads over HTTP, optionally enriches them via LM Studio, and upserts into PostgreSQL. Designed to run as a Docker container from day one for eventual migration to k3s.

## Databases

**bills** — scanned physical document archive  
Provisioned PostgreSQL role: `bills_app` (read/write)  
Primary table: `bills.documents` — stores vendor, document type, dates, amounts, LM Studio summary, and raw extracted text for every scanned PDF.

**hermes** — personal biometric and health data  
Provisioned PostgreSQL role: `hermes_app` (read/write)  
Primary table: `hermes.daily_biometric_readiness` — daily log of resting heart rate, HRV, sleep score, blood pressure, joint pain, and dietary compliance sourced from Health Auto Export.

## Ingestion Routes

| Method | Path | Source | Description |
|--------|------|--------|-------------|
| POST | `/ingest/bills` | scan-watcher | PDF summary payload → upsert `bills.documents` |
| POST | `/ingest/health` | Health Auto Export | Daily biometric JSON → upsert `hermes.daily_biometric_readiness` |
| GET | `/status` | monitoring | Health check; returns last ingest timestamp per domain and DB connectivity |

### LM Studio dependency

Bill ingestion calls LM Studio for AI summarization. If LM Studio is unreachable the ingest still succeeds — raw text is stored and `summary` is set to `NULL`. Health ingestion never calls LM Studio.

## Origin

Bill handling logic and the LM Studio client pattern are migrated from [scan-watcher](../scan-watcher), which previously handled PDF ingestion into Anytype. The `DocumentSummary` model and `summarize()` function are carried over with minimal changes.

## k3s Migration Path

The server is stateless and fully configured via environment variables. No local filesystem state. The `docker-compose.yml` is the local dev/single-host entrypoint; the same image will be deployed to k3s via a Deployment + ConfigMap + Secret when the cluster is ready.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `BILLS_DB_URL` | `postgresql://bills_app:PASSWORD@host/bills` |
| `HERMES_DB_URL` | `postgresql://hermes_app:PASSWORD@host/hermes` |
| `LM_STUDIO_URL` | LM Studio base URL (default: `http://localhost:1234`) |
| `LM_STUDIO_MODEL` | Model name (default: `qwen2.5-7b-instruct-1m`) |
| `INGEST_PORT` | Port to bind (default: `8421`) |
