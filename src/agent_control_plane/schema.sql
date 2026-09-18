-- Phase 1 executable schema. migrations/0001_initial.sql is a future design only.
CREATE SCHEMA IF NOT EXISTS acp1;
REVOKE ALL ON SCHEMA acp1 FROM PUBLIC;

CREATE TABLE acp1.task (
    id uuid PRIMARY KEY,
    tenant text NOT NULL,
    requested_by text NOT NULL,
    idempotency_key uuid NOT NULL,
    diagnostic text NOT NULL CHECK (diagnostic = 'quantum-platform-pod-readiness'),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant, requested_by, idempotency_key),
    UNIQUE (tenant, id)
);
CREATE TABLE acp1.run (
    id uuid PRIMARY KEY,
    tenant text NOT NULL,
    task_id uuid NOT NULL UNIQUE,
    status text NOT NULL CHECK (status IN ('queued','running','succeeded','failed')),
    profile text NOT NULL CHECK (profile = 'admin-readonly'),
    model text,
    runtime_revision text,
    session_id text,
    started_at timestamptz,
    finished_at timestamptz,
    evidence jsonb,
    summary text,
    failure_code text,
    FOREIGN KEY (tenant, task_id) REFERENCES acp1.task(tenant, id),
    UNIQUE (tenant, id),
    CHECK ((status IN ('succeeded','failed')) = (finished_at IS NOT NULL)),
    CHECK (status <> 'succeeded' OR (summary IS NOT NULL AND evidence IS NOT NULL))
);
CREATE TABLE acp1.event (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant text NOT NULL,
    run_id uuid NOT NULL,
    kind text NOT NULL,
    occurred_at timestamptz NOT NULL DEFAULT now(),
    data jsonb NOT NULL DEFAULT '{}',
    FOREIGN KEY (tenant, run_id) REFERENCES acp1.run(tenant, id)
);
CREATE INDEX task_history ON acp1.task(tenant, created_at DESC, id DESC);
CREATE INDEX run_queue ON acp1.run(tenant, status);
CREATE INDEX event_history ON acp1.event(tenant, run_id, id);

ALTER TABLE acp1.task ENABLE ROW LEVEL SECURITY;
ALTER TABLE acp1.task FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_task ON acp1.task
    USING (tenant = current_setting('acp.tenant_id', true))
    WITH CHECK (tenant = current_setting('acp.tenant_id', true));
ALTER TABLE acp1.run ENABLE ROW LEVEL SECURITY;
ALTER TABLE acp1.run FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_run ON acp1.run
    USING (tenant = current_setting('acp.tenant_id', true))
    WITH CHECK (tenant = current_setting('acp.tenant_id', true));
ALTER TABLE acp1.event ENABLE ROW LEVEL SECURITY;
ALTER TABLE acp1.event FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_event ON acp1.event
    USING (tenant = current_setting('acp.tenant_id', true))
    WITH CHECK (tenant = current_setting('acp.tenant_id', true));

GRANT USAGE ON SCHEMA acp1 TO acp_app;
GRANT SELECT, INSERT ON acp1.task, acp1.event TO acp_app;
GRANT SELECT, INSERT, UPDATE ON acp1.run TO acp_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA acp1 TO acp_app;
