FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN adduser --disabled-password --gecos "" appuser

COPY . .

USER appuser

EXPOSE 8421

CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${INGEST_PORT:-8421}"]
