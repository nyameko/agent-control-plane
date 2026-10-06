-- M4a: canonical personal-agent continuity.
-- Projects are deliberately minimal stubs here; M4c will expand project/workspace semantics.
-- Conversation/message history is canonical ACP state and must not depend on a Hermes profile.

CREATE TABLE acp1.project (
    id uuid PRIMARY KEY,
    tenant text NOT NULL,
    owner_subject text NOT NULL,
    title text NOT NULL CHECK (char_length(title) BETWEEN 1 AND 200),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    archived_at timestamptz,
    UNIQUE (tenant, owner_subject, id)
);

CREATE TABLE acp1.conversation (
    id uuid PRIMARY KEY,
    tenant text NOT NULL,
    owner_subject text NOT NULL,
    project_id uuid,
    title text NOT NULL CHECK (char_length(title) BETWEEN 1 AND 200),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    archived_at timestamptz,
    UNIQUE (tenant, owner_subject, id),
    FOREIGN KEY (tenant, owner_subject, project_id)
        REFERENCES acp1.project(tenant, owner_subject, id)
);

CREATE TABLE acp1.message (
    id uuid PRIMARY KEY,
    tenant text NOT NULL,
    owner_subject text NOT NULL,
    conversation_id uuid NOT NULL,
    sequence bigint NOT NULL CHECK (sequence > 0),
    author_kind text NOT NULL CHECK (author_kind IN ('user','assistant','system','tool')),
    content jsonb NOT NULL,
    source_channel text NOT NULL
        CHECK (source_channel IN ('web','jupyter','ssh','gptel','api','system')),
    client_message_id text,
    created_at timestamptz NOT NULL DEFAULT now(),
    FOREIGN KEY (tenant, owner_subject, conversation_id)
        REFERENCES acp1.conversation(tenant, owner_subject, id) ON DELETE CASCADE,
    UNIQUE (conversation_id, sequence),
    UNIQUE (conversation_id, client_message_id)
);

CREATE INDEX project_owner_history
    ON acp1.project(tenant, owner_subject, updated_at DESC, id DESC);
CREATE INDEX conversation_owner_history
    ON acp1.conversation(tenant, owner_subject, updated_at DESC, id DESC);
CREATE INDEX message_conversation_history
    ON acp1.message(tenant, owner_subject, conversation_id, sequence);

ALTER TABLE acp1.project ENABLE ROW LEVEL SECURITY;
ALTER TABLE acp1.project FORCE ROW LEVEL SECURITY;
CREATE POLICY personal_project ON acp1.project
    USING (
        tenant = current_setting('acp.tenant_id', true)
        AND owner_subject = current_setting('acp.subject_id', true)
    )
    WITH CHECK (
        tenant = current_setting('acp.tenant_id', true)
        AND owner_subject = current_setting('acp.subject_id', true)
    );

ALTER TABLE acp1.conversation ENABLE ROW LEVEL SECURITY;
ALTER TABLE acp1.conversation FORCE ROW LEVEL SECURITY;
CREATE POLICY personal_conversation ON acp1.conversation
    USING (
        tenant = current_setting('acp.tenant_id', true)
        AND owner_subject = current_setting('acp.subject_id', true)
    )
    WITH CHECK (
        tenant = current_setting('acp.tenant_id', true)
        AND owner_subject = current_setting('acp.subject_id', true)
    );

ALTER TABLE acp1.message ENABLE ROW LEVEL SECURITY;
ALTER TABLE acp1.message FORCE ROW LEVEL SECURITY;
CREATE POLICY personal_message ON acp1.message
    USING (
        tenant = current_setting('acp.tenant_id', true)
        AND owner_subject = current_setting('acp.subject_id', true)
    )
    WITH CHECK (
        tenant = current_setting('acp.tenant_id', true)
        AND owner_subject = current_setting('acp.subject_id', true)
    );

GRANT SELECT, INSERT, UPDATE ON acp1.project, acp1.conversation TO acp_app;
GRANT SELECT, INSERT ON acp1.message TO acp_app;
