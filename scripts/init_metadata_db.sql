-- QueryPilot metadata database schema (see PROJECT_BLUEPRINT.md §8.1)

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS connections (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    host            TEXT NOT NULL,
    port            INTEGER NOT NULL DEFAULT 5432,
    database        TEXT NOT NULL,
    username        TEXT NOT NULL,
    encrypted_credentials BYTEA NOT NULL,
    schema_version  TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS conversations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connection_id   UUID NOT NULL REFERENCES connections(id) ON DELETE CASCADE,
    state_json      JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS traces (
    id              BIGSERIAL PRIMARY KEY,
    request_id      UUID NOT NULL,
    span_id         UUID NOT NULL,
    parent_span_id  UUID,
    agent           TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'ok',
    start_ts        TIMESTAMPTZ NOT NULL,
    duration_ms     INTEGER NOT NULL,
    prompt_tokens   INTEGER,
    completion_tokens INTEGER,
    cost_usd        NUMERIC(10, 6),
    cache_hit       BOOLEAN,
    retry_count     INTEGER DEFAULT 0,
    prompt_ref      TEXT,
    response_ref    TEXT,
    metadata_json   JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_traces_request_id ON traces(request_id);
CREATE INDEX IF NOT EXISTS idx_traces_agent_start ON traces(agent, start_ts);

CREATE TABLE IF NOT EXISTS eval_results (
    id              BIGSERIAL PRIMARY KEY,
    run_id          TEXT NOT NULL,
    dataset_version TEXT NOT NULL,
    model_version   TEXT NOT NULL,
    question_id     TEXT NOT NULL,
    execution_accuracy BOOLEAN NOT NULL,
    safety_passed   BOOLEAN NOT NULL,
    latency_ms      INTEGER,
    prompt_tokens   INTEGER,
    completion_tokens INTEGER,
    cost_usd        NUMERIC(10, 6),
    error_message   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_eval_run ON eval_results(run_id);
