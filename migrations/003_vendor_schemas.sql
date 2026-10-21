-- Migration 003: vendor schema registry
-- Lets the ingestion client learn, per vendor, which static fields to
-- extract beyond the fixed `documents` columns, instead of hardcoding a
-- branch per vendor (see duke_energy_usage, migration 002).

CREATE TABLE vendor_schemas (
    id          SERIAL PRIMARY KEY,
    vendor_name TEXT NOT NULL,
    vendor_key  TEXT NOT NULL,
    version     INTEGER NOT NULL,
    schema      JSONB NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (vendor_key, version)
);

CREATE INDEX ON vendor_schemas (vendor_key);

-- Schema-driven static fields beyond the documents table's fixed columns
-- (vendor, document_type, document_date, due_date, amount_due,
-- account_number). duke_energy_usage stays as-is for existing rows; new
-- vendor-specific fields (including future Duke Energy extractions) land
-- here instead of a new per-vendor table.
ALTER TABLE documents ADD COLUMN IF NOT EXISTS extra_fields JSONB;
