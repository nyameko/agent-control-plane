-- M4d: private, operator-reviewed, immutable skill/reference bindings.
-- This schema grants NO capabilities, shell, tools, scheduler or provider access.
-- Only the ACP application may attach already trusted Git catalog entries.
CREATE TABLE acp1.skill_binding (
    id uuid PRIMARY KEY,
    tenant text NOT NULL,
    owner_subject text NOT NULL,
    skill_id text NOT NULL CHECK (char_length(skill_id) BETWEEN 1 AND 120),
    version text NOT NULL CHECK (char_length(version) BETWEEN 1 AND 60),
    source_commit char(40) NOT NULL CHECK (source_commit ~ '^[0-9a-f]{40}$'),
    manifest_sha256 char(64) NOT NULL CHECK (manifest_sha256 ~ '^[0-9a-f]{64}$'),
    status text NOT NULL CHECK (status IN ('enabled', 'revoked')),
    revision integer NOT NULL DEFAULT 1 CHECK (revision >= 1),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    revoked_at timestamptz,
    UNIQUE (tenant, owner_subject, skill_id),
    CHECK ((status = 'revoked') = (revoked_at IS NOT NULL))
);
ALTER TABLE acp1.skill_binding ENABLE ROW LEVEL SECURITY;
ALTER TABLE acp1.skill_binding FORCE ROW LEVEL SECURITY;
CREATE POLICY private_skill_binding ON acp1.skill_binding
 USING (tenant=current_setting('acp.tenant_id',true)
   AND owner_subject=current_setting('acp.subject_id',true))
 WITH CHECK (tenant=current_setting('acp.tenant_id',true)
   AND owner_subject=current_setting('acp.subject_id',true));
GRANT SELECT,INSERT,UPDATE ON acp1.skill_binding TO acp_app;

CREATE TABLE acp1.skill_binding_revision (
    binding_id uuid NOT NULL,
    tenant text NOT NULL,
    owner_subject text NOT NULL,
    revision integer NOT NULL CHECK (revision >= 1),
    action text NOT NULL CHECK (action IN ('enabled','revoked')),
    actor_subject text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (binding_id,revision),
    FOREIGN KEY (binding_id) REFERENCES acp1.skill_binding(id) ON DELETE RESTRICT,
    CHECK (actor_subject = owner_subject)
);
ALTER TABLE acp1.skill_binding_revision ENABLE ROW LEVEL SECURITY;
ALTER TABLE acp1.skill_binding_revision FORCE ROW LEVEL SECURITY;
CREATE POLICY private_skill_revision ON acp1.skill_binding_revision
 USING (tenant=current_setting('acp.tenant_id',true)
   AND owner_subject=current_setting('acp.subject_id',true))
 WITH CHECK (tenant=current_setting('acp.tenant_id',true)
   AND owner_subject=current_setting('acp.subject_id',true));
GRANT SELECT,INSERT ON acp1.skill_binding_revision TO acp_app;
