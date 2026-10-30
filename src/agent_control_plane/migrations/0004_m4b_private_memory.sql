-- M4b proposal: narrow, private owner-scoped durable memory.
-- Do not run until schema-v3/v4-compatible API AND worker are deployed.
-- This migration is transactional under existing migrate.py with checksum tracking.
ALTER TABLE acp1.message
    ADD CONSTRAINT message_owner_conversation_id_unique
    UNIQUE (tenant, owner_subject, conversation_id, id);

CREATE TABLE acp1.memory_item (
    id uuid PRIMARY KEY,
    tenant text NOT NULL,
    owner_subject text NOT NULL,
    creation_key uuid NOT NULL,
    creation_payload_sha256 char(64) NOT NULL CHECK (creation_payload_sha256 ~ '^[a-f0-9]{64}$'),
    scope_kind text NOT NULL DEFAULT 'private_user'
      CHECK (scope_kind = 'private_user'),
    kind text NOT NULL CHECK (kind IN ('preference','episodic','semantic','project_note')),
    status text NOT NULL DEFAULT 'candidate'
      CHECK (status IN ('candidate','active','revoked')),
    current_revision integer NOT NULL DEFAULT 1 CHECK (current_revision > 0),
    source_conversation_id uuid NOT NULL,
    source_message_id uuid NOT NULL,
    source_sha256 char(64) NOT NULL CHECK (source_sha256 ~ '^[a-f0-9]{64}$'),
    sensitivity text NOT NULL DEFAULT 'internal'
      CHECK (sensitivity IN ('internal','confidential')),
    verification_status text NOT NULL DEFAULT 'user_asserted'
      CHECK (verification_status IN ('user_asserted','source_supported','unverified')),
    expires_at timestamptz,
    approved_at timestamptz,
    revoked_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant, owner_subject, id),
    UNIQUE (tenant, owner_subject, creation_key),
    CONSTRAINT memory_source_fk
      FOREIGN KEY (tenant, owner_subject, source_conversation_id, source_message_id)
      REFERENCES acp1.message (tenant, owner_subject, conversation_id, id)
      ON DELETE RESTRICT,
    CONSTRAINT memory_status_timestamps CHECK (
      (status = 'candidate' AND approved_at IS NULL AND revoked_at IS NULL)
      OR (status = 'active' AND approved_at IS NOT NULL AND revoked_at IS NULL)
      OR (status = 'revoked' AND revoked_at IS NOT NULL)
    )
);

CREATE TABLE acp1.memory_revision (
    memory_id uuid NOT NULL,
    tenant text NOT NULL,
    owner_subject text NOT NULL,
    revision integer NOT NULL CHECK (revision > 0),
    event_type text NOT NULL CHECK (event_type IN ('candidate_created','approved','corrected','revoked')),
    body text CHECK (body IS NULL OR char_length(body) BETWEEN 1 AND 2000),
    actor_subject text NOT NULL,
    reason text,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (memory_id, revision),
    UNIQUE (tenant, owner_subject, memory_id, revision),
    FOREIGN KEY (tenant, owner_subject, memory_id)
      REFERENCES acp1.memory_item (tenant, owner_subject, id) ON DELETE RESTRICT,
    CHECK ((event_type='revoked') = (body IS NULL)),
    CHECK (actor_subject = owner_subject)
);

ALTER TABLE acp1.memory_item
    ADD CONSTRAINT memory_current_revision_fk
    FOREIGN KEY (tenant, owner_subject, id, current_revision)
    REFERENCES acp1.memory_revision (tenant, owner_subject, memory_id, revision)
    DEFERRABLE INITIALLY DEFERRED;

-- The original source must be the researcher's own user-authored message.
CREATE FUNCTION acp1.memory_check_source() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM acp1.message m
        JOIN acp1.conversation c
          ON c.tenant=m.tenant AND c.owner_subject=m.owner_subject
         AND c.id=m.conversation_id
        WHERE m.tenant=NEW.tenant AND m.owner_subject=NEW.owner_subject
          AND m.conversation_id=NEW.source_conversation_id
          AND m.id=NEW.source_message_id
          AND m.author_kind='user' AND c.archived_at IS NULL
    ) THEN
        RAISE EXCEPTION 'Invalid memory source' USING ERRCODE='23514';
    END IF;
    IF NEW.status <> 'candidate' OR NEW.current_revision <> 1
       OR NEW.approved_at IS NOT NULL OR NEW.revoked_at IS NOT NULL THEN
        RAISE EXCEPTION 'New memory must begin candidate revision 1' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER memory_source_guard BEFORE INSERT ON acp1.memory_item
    FOR EACH ROW EXECUTE FUNCTION acp1.memory_check_source();

-- DB-level lifecycle guard validates the new immutable revision already inserted
-- in the same transaction. Application code must lock the item before updating it.
CREATE FUNCTION acp1.memory_guard_update() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE transition text;
BEGIN
    IF ROW(NEW.id,NEW.tenant,NEW.owner_subject,NEW.creation_key,
           NEW.creation_payload_sha256,NEW.scope_kind,NEW.kind,
           NEW.source_conversation_id,NEW.source_message_id,NEW.source_sha256,
           NEW.sensitivity,NEW.created_at)
       IS DISTINCT FROM
       ROW(OLD.id,OLD.tenant,OLD.owner_subject,OLD.creation_key,
           OLD.creation_payload_sha256,OLD.scope_kind,OLD.kind,
           OLD.source_conversation_id,OLD.source_message_id,OLD.source_sha256,
           OLD.sensitivity,OLD.created_at)
    THEN
        RAISE EXCEPTION 'Immutable memory identity/provenance' USING ERRCODE='23514';
    END IF;
    IF OLD.status='revoked' OR NEW.current_revision <> OLD.current_revision+1 THEN
        RAISE EXCEPTION 'Invalid memory revision transition' USING ERRCODE='23514';
    END IF;
    IF OLD.status='candidate' AND NEW.status='active' THEN
        transition := 'approved';
    ELSIF OLD.status='candidate' AND NEW.status='revoked' THEN
        transition := 'revoked';
    ELSIF OLD.status='active' AND NEW.status='active' THEN
        transition := 'corrected';
    ELSIF OLD.status='active' AND NEW.status='revoked' THEN
        transition := 'revoked';
    ELSE
        RAISE EXCEPTION 'Unsupported memory status transition' USING ERRCODE='23514';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM acp1.memory_revision r
        WHERE r.tenant=NEW.tenant AND r.owner_subject=NEW.owner_subject
          AND r.memory_id=NEW.id AND r.revision=NEW.current_revision
          AND r.event_type=transition
    ) THEN
        RAISE EXCEPTION 'Missing correct memory revision event' USING ERRCODE='23514';
    END IF;
    IF (NEW.status='active' AND
        (NEW.approved_at IS NULL OR NEW.revoked_at IS NOT NULL))
        OR (NEW.status='revoked' AND NEW.revoked_at IS NULL)
        OR (OLD.status='active' AND NEW.approved_at IS DISTINCT FROM OLD.approved_at)
    THEN
        RAISE EXCEPTION 'Invalid lifecycle timestamps' USING ERRCODE='23514';
    END IF;
    NEW.updated_at := now();
    RETURN NEW;
END $$;
CREATE TRIGGER memory_update_guard BEFORE UPDATE ON acp1.memory_item
    FOR EACH ROW EXECUTE FUNCTION acp1.memory_guard_update();

-- Revisions must remain append-only, with a valid ordering of events.
CREATE FUNCTION acp1.memory_guard_revision() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE current_status text; current_rev integer;
BEGIN
    IF TG_OP <> 'INSERT' THEN
        RAISE EXCEPTION 'Memory revisions are immutable' USING ERRCODE='23514';
    END IF;
    SELECT status,current_revision INTO current_status,current_rev
      FROM acp1.memory_item
      WHERE tenant=NEW.tenant AND owner_subject=NEW.owner_subject AND id=NEW.memory_id
      FOR UPDATE;
    IF NOT FOUND OR current_status='revoked' OR
       (NEW.revision=1 AND (current_status<>'candidate' OR
                           NEW.event_type<>'candidate_created' OR current_rev<>1))
       OR (NEW.revision>1 AND
           (NEW.revision<>current_rev+1 OR NEW.event_type='candidate_created' OR
           (current_status='candidate' AND NEW.event_type NOT IN ('approved','revoked')) OR
           (current_status='active' AND NEW.event_type NOT IN ('corrected','revoked'))))
    THEN
        RAISE EXCEPTION 'Invalid memory revision insertion' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER memory_revision_guard BEFORE INSERT OR UPDATE OR DELETE
    ON acp1.memory_revision FOR EACH ROW EXECUTE FUNCTION acp1.memory_guard_revision();

CREATE INDEX memory_owner_active
    ON acp1.memory_item (tenant,owner_subject,updated_at DESC,id DESC)
    WHERE status='active';
CREATE INDEX memory_owner_history
    ON acp1.memory_item (tenant,owner_subject,created_at DESC,id DESC);

ALTER TABLE acp1.memory_item ENABLE ROW LEVEL SECURITY;
ALTER TABLE acp1.memory_item FORCE ROW LEVEL SECURITY;
CREATE POLICY private_memory_item ON acp1.memory_item
 USING (tenant=current_setting('acp.tenant_id',true)
    AND owner_subject=current_setting('acp.subject_id',true))
 WITH CHECK (tenant=current_setting('acp.tenant_id',true)
    AND owner_subject=current_setting('acp.subject_id',true));
ALTER TABLE acp1.memory_revision ENABLE ROW LEVEL SECURITY;
ALTER TABLE acp1.memory_revision FORCE ROW LEVEL SECURITY;
CREATE POLICY private_memory_revision ON acp1.memory_revision
 USING (tenant=current_setting('acp.tenant_id',true)
    AND owner_subject=current_setting('acp.subject_id',true))
 WITH CHECK (tenant=current_setting('acp.tenant_id',true)
    AND owner_subject=current_setting('acp.subject_id',true));
GRANT SELECT,INSERT,UPDATE ON acp1.memory_item TO acp_app;
GRANT SELECT,INSERT ON acp1.memory_revision TO acp_app;
