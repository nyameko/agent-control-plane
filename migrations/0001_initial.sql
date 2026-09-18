-- DESIGN REFERENCE ONLY: Phase 1 uses src/agent_control_plane/schema.sql.
-- Do not apply this proposed future schema to the Phase 1 database.
-- Proposed PostgreSQL V0.1 schema.
-- Production rollout should wrap this in the selected migration tool and use a dedicated database
-- role. The agent runtime and model servers must not receive that role.

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE SCHEMA IF NOT EXISTS agent_control_plane;
SET search_path TO agent_control_plane, public;

CREATE TYPE task_status AS ENUM (
  'pending', 'planning', 'approval_required', 'running', 'completed', 'failed', 'cancelled'
);
CREATE TYPE run_status AS ENUM (
  'queued', 'running', 'paused', 'completed', 'failed', 'cancelled'
);
CREATE TYPE approval_status AS ENUM ('pending', 'approved', 'rejected', 'expired', 'consumed');
CREATE TYPE sensitivity AS ENUM ('public', 'internal', 'confidential', 'restricted');

CREATE TABLE tenant (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  external_ref text NOT NULL UNIQUE,
  name text NOT NULL,
  kind text NOT NULL,
  policy_ref text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE subject_ref (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  external_subject text NOT NULL UNIQUE,
  subject_kind text NOT NULL,
  display_name text,
  disabled_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE tenant_membership (
  tenant_id uuid NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
  subject_id uuid NOT NULL REFERENCES subject_ref(id) ON DELETE CASCADE,
  role text NOT NULL,
  external_membership_ref text,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, subject_id, role)
);

CREATE TABLE agent_definition (
  id text NOT NULL,
  version text NOT NULL,
  git_repository text NOT NULL,
  git_revision text NOT NULL,
  content_digest text NOT NULL,
  runtime text NOT NULL,
  specification jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id, version),
  UNIQUE (content_digest)
);

CREATE TABLE agent_instance (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant(id) ON DELETE RESTRICT,
  owner_subject_id uuid REFERENCES subject_ref(id) ON DELETE SET NULL,
  definition_id text NOT NULL,
  definition_version text NOT NULL,
  runtime_profile_ref text NOT NULL,
  status text NOT NULL DEFAULT 'active',
  created_at timestamptz NOT NULL DEFAULT now(),
  disabled_at timestamptz,
  FOREIGN KEY (definition_id, definition_version)
    REFERENCES agent_definition(id, version) ON DELETE RESTRICT
);

CREATE TABLE conversation (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant(id) ON DELETE RESTRICT,
  owner_subject_id uuid NOT NULL REFERENCES subject_ref(id) ON DELETE RESTRICT,
  agent_instance_id uuid REFERENCES agent_instance(id) ON DELETE SET NULL,
  title text,
  sensitivity sensitivity NOT NULL DEFAULT 'internal',
  retention_policy text NOT NULL DEFAULT 'user-default',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  archived_at timestamptz,
  deleted_at timestamptz
);
CREATE INDEX conversation_owner_idx ON conversation (owner_subject_id, updated_at DESC);
CREATE INDEX conversation_tenant_idx ON conversation (tenant_id, updated_at DESC);

CREATE TABLE message (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id uuid NOT NULL REFERENCES conversation(id) ON DELETE CASCADE,
  sequence bigint NOT NULL,
  author_kind text NOT NULL,
  author_ref text NOT NULL,
  content jsonb NOT NULL,
  sensitivity sensitivity NOT NULL,
  source_channel text NOT NULL,
  client_message_id text,
  created_at timestamptz NOT NULL DEFAULT now(),
  supersedes_message_id uuid REFERENCES message(id) ON DELETE SET NULL,
  deleted_at timestamptz,
  UNIQUE (conversation_id, sequence),
  UNIQUE (source_channel, client_message_id)
);

CREATE TABLE memory_item (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
  owner_subject_id uuid REFERENCES subject_ref(id) ON DELETE CASCADE,
  scope text NOT NULL,
  memory_kind text NOT NULL,
  content jsonb NOT NULL,
  sensitivity sensitivity NOT NULL,
  provenance jsonb NOT NULL,
  status text NOT NULL DEFAULT 'active',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  invalidated_at timestamptz
);
CREATE INDEX memory_scope_idx ON memory_item (tenant_id, owner_subject_id, scope, status);

CREATE TABLE task (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant(id) ON DELETE RESTRICT,
  requested_by uuid NOT NULL REFERENCES subject_ref(id) ON DELETE RESTRICT,
  conversation_id uuid REFERENCES conversation(id) ON DELETE SET NULL,
  parent_task_id uuid REFERENCES task(id) ON DELETE SET NULL,
  status task_status NOT NULL DEFAULT 'pending',
  domain text NOT NULL,
  intent text NOT NULL,
  sensitivity sensitivity NOT NULL,
  request jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz
);
CREATE INDEX task_tenant_status_idx ON task (tenant_id, status, created_at DESC);
CREATE INDEX task_conversation_idx ON task (conversation_id, created_at);

CREATE TABLE execution_plan (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  task_id uuid NOT NULL REFERENCES task(id) ON DELETE CASCADE,
  version integer NOT NULL,
  plan jsonb NOT NULL,
  canonical_digest text NOT NULL,
  policy_revision text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (task_id, version),
  UNIQUE (task_id, canonical_digest)
);

CREATE TABLE run (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  task_id uuid NOT NULL REFERENCES task(id) ON DELETE CASCADE,
  plan_id uuid NOT NULL REFERENCES execution_plan(id) ON DELETE RESTRICT,
  agent_instance_id uuid REFERENCES agent_instance(id) ON DELETE SET NULL,
  parent_run_id uuid REFERENCES run(id) ON DELETE SET NULL,
  runtime text NOT NULL,
  runtime_run_ref text,
  runtime_session_ref text,
  status run_status NOT NULL DEFAULT 'queued',
  started_at timestamptz,
  finished_at timestamptz,
  error_class text,
  result_summary jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX run_task_idx ON run (task_id, created_at);
CREATE INDEX run_runtime_ref_idx ON run (runtime, runtime_run_ref);

CREATE TABLE delegation (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  parent_run_id uuid NOT NULL REFERENCES run(id) ON DELETE CASCADE,
  child_task_id uuid NOT NULL REFERENCES task(id) ON DELETE CASCADE,
  capability_ceiling jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (parent_run_id, child_task_id)
);

CREATE TABLE model_decision (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id uuid NOT NULL REFERENCES run(id) ON DELETE CASCADE,
  logical_pool text NOT NULL,
  resolved_model text,
  resolved_runtime text,
  resolved_endpoint_ref text,
  reasons jsonb NOT NULL,
  policy_constraints jsonb NOT NULL,
  input_tokens bigint,
  output_tokens bigint,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE tool_call (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id uuid NOT NULL REFERENCES run(id) ON DELETE CASCADE,
  tool_name text NOT NULL,
  capability text NOT NULL,
  request_summary jsonb NOT NULL,
  request_artifact_ref text,
  response_summary jsonb,
  response_artifact_ref text,
  policy_decision text NOT NULL,
  status text NOT NULL,
  started_at timestamptz,
  finished_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE approval (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  task_id uuid NOT NULL REFERENCES task(id) ON DELETE CASCADE,
  plan_id uuid NOT NULL REFERENCES execution_plan(id) ON DELETE CASCADE,
  capability text NOT NULL,
  resource_selector jsonb NOT NULL,
  plan_digest text NOT NULL,
  status approval_status NOT NULL DEFAULT 'pending',
  requested_by uuid NOT NULL REFERENCES subject_ref(id) ON DELETE RESTRICT,
  decided_by uuid REFERENCES subject_ref(id) ON DELETE RESTRICT,
  strong_auth_context jsonb,
  decision_reason text,
  expires_at timestamptz NOT NULL,
  decided_at timestamptz,
  consumed_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX approval_pending_idx ON approval (status, expires_at);

CREATE TABLE execution_job (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id uuid NOT NULL REFERENCES run(id) ON DELETE CASCADE,
  execution_class text NOT NULL,
  scheduler text NOT NULL,
  external_job_ref text,
  request jsonb NOT NULL,
  status text NOT NULL,
  resource_usage jsonb,
  submitted_at timestamptz,
  finished_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (scheduler, external_job_ref)
);

CREATE TABLE artifact (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant(id) ON DELETE RESTRICT,
  task_id uuid REFERENCES task(id) ON DELETE SET NULL,
  run_id uuid REFERENCES run(id) ON DELETE SET NULL,
  artifact_kind text NOT NULL,
  uri text NOT NULL,
  sha256 text NOT NULL,
  media_type text,
  size_bytes bigint CHECK (size_bytes IS NULL OR size_bytes >= 0),
  sensitivity sensitivity NOT NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX artifact_task_idx ON artifact (task_id, created_at);

CREATE TABLE channel_binding (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
  subject_id uuid NOT NULL REFERENCES subject_ref(id) ON DELETE CASCADE,
  platform text NOT NULL,
  platform_account_id text NOT NULL,
  destination_ref text,
  scope text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  revoked_at timestamptz,
  UNIQUE (platform, platform_account_id, tenant_id)
);

CREATE TABLE audit_event (
  sequence bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  event_id uuid NOT NULL DEFAULT gen_random_uuid() UNIQUE,
  tenant_id uuid REFERENCES tenant(id) ON DELETE SET NULL,
  actor_subject_id uuid REFERENCES subject_ref(id) ON DELETE SET NULL,
  actor_agent_instance_id uuid REFERENCES agent_instance(id) ON DELETE SET NULL,
  task_id uuid REFERENCES task(id) ON DELETE SET NULL,
  run_id uuid REFERENCES run(id) ON DELETE SET NULL,
  event_type text NOT NULL,
  occurred_at timestamptz NOT NULL DEFAULT now(),
  payload jsonb NOT NULL,
  previous_event_digest text,
  event_digest text NOT NULL
);
CREATE INDEX audit_tenant_time_idx ON audit_event (tenant_id, occurred_at DESC);
CREATE INDEX audit_task_idx ON audit_event (task_id, sequence);

CREATE TABLE outbox_event (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  aggregate_type text NOT NULL,
  aggregate_id uuid NOT NULL,
  event_type text NOT NULL,
  payload jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  published_at timestamptz,
  attempts integer NOT NULL DEFAULT 0
);
CREATE INDEX outbox_unpublished_idx ON outbox_event (created_at) WHERE published_at IS NULL;

-- Application-enforced tenancy is required in V0.1. Before general multi-tenancy, add and test
-- PostgreSQL row-level security policies using transaction-local subject/tenant settings. Do not
-- enable untested RLS and assume it is protective.
