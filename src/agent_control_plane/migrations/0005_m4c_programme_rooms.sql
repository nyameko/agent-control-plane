-- M4c: separate PI-governed programme conversations from private ACP projects.
-- All access requires a short-lived Quantum Platform signed programme assertion
-- freshly minted after its authoritative approved-membership check.
-- No project/memory policies are widened and no automated group agent execution.
CREATE TABLE acp1.programme_conversation (
    id uuid PRIMARY KEY,
    tenant text NOT NULL,
    programme_id bigint NOT NULL CHECK (programme_id > 0),
    title text NOT NULL CHECK (char_length(title) BETWEEN 1 AND 200),
    created_by_subject text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant, programme_id, id)
);

CREATE TABLE acp1.programme_message (
    id uuid PRIMARY KEY,
    tenant text NOT NULL,
    programme_id bigint NOT NULL CHECK (programme_id > 0),
    conversation_id uuid NOT NULL,
    sequence integer NOT NULL CHECK (sequence > 0),
    author_subject text NOT NULL,
    content jsonb NOT NULL,
    source_channel text NOT NULL CHECK (source_channel IN ('web','jupyter','ssh','api')),
    client_message_id text CHECK (client_message_id IS NULL OR
      char_length(client_message_id) BETWEEN 1 AND 200),
    created_at timestamptz NOT NULL DEFAULT now(),
    FOREIGN KEY (tenant, programme_id, conversation_id)
      REFERENCES acp1.programme_conversation (tenant, programme_id, id)
      ON DELETE RESTRICT,
    UNIQUE (tenant, programme_id, conversation_id, sequence)
);
CREATE UNIQUE INDEX programme_message_idempotency
 ON acp1.programme_message
 (tenant, programme_id, conversation_id, author_subject, client_message_id)
 WHERE client_message_id IS NOT NULL;
CREATE INDEX programme_conversation_index
 ON acp1.programme_conversation(tenant, programme_id, created_at DESC, id DESC);

-- Ownership and membership are authorized by Quantum Platform on each request;
-- ACP enforces the signed programme boundary again at the database layer.
-- A user may read other authorized members' messages in this room but may only
-- create messages carrying their own authenticated subject.
ALTER TABLE acp1.programme_conversation ENABLE ROW LEVEL SECURITY;
ALTER TABLE acp1.programme_conversation FORCE ROW LEVEL SECURITY;
CREATE POLICY programme_conversation_read ON acp1.programme_conversation
 FOR SELECT USING (
    tenant = current_setting('acp.tenant_id',true)
    AND programme_id = NULLIF(current_setting('acp.programme_id',true),'')::bigint
);
CREATE POLICY programme_conversation_create ON acp1.programme_conversation
 FOR INSERT WITH CHECK (
    tenant = current_setting('acp.tenant_id',true)
    AND programme_id = NULLIF(current_setting('acp.programme_id',true),'')::bigint
    AND created_by_subject = current_setting('acp.subject_id',true)
);

ALTER TABLE acp1.programme_message ENABLE ROW LEVEL SECURITY;
ALTER TABLE acp1.programme_message FORCE ROW LEVEL SECURITY;
CREATE POLICY programme_message_read ON acp1.programme_message
 FOR SELECT USING (
    tenant = current_setting('acp.tenant_id',true)
    AND programme_id = NULLIF(current_setting('acp.programme_id',true),'')::bigint
);
CREATE POLICY programme_message_create ON acp1.programme_message
 FOR INSERT WITH CHECK (
    tenant = current_setting('acp.tenant_id',true)
    AND programme_id = NULLIF(current_setting('acp.programme_id',true),'')::bigint
    AND author_subject = current_setting('acp.subject_id',true)
);

GRANT SELECT,INSERT ON acp1.programme_conversation TO acp_app;
GRANT SELECT,INSERT ON acp1.programme_message TO acp_app;
