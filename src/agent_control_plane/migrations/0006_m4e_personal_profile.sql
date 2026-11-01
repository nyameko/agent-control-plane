-- M4e: minimal portable, ACP-owned personal profile (no harness-local identity).
-- Holds only user-editable preferences; no API keys, shell config or authority.
CREATE TABLE acp1.personal_profile (
    id uuid PRIMARY KEY,
    tenant text NOT NULL,
    owner_subject text NOT NULL,
    display_name text NOT NULL CHECK (char_length(display_name) BETWEEN 1 AND 100),
    instructions text NOT NULL DEFAULT '' CHECK (char_length(instructions) <= 2000),
    model_route text NOT NULL DEFAULT 'general'
      CHECK (model_route IN ('general','reasoning','coding')),
    revision integer NOT NULL DEFAULT 1 CHECK (revision > 0),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant,owner_subject),
    UNIQUE (tenant,owner_subject,id)
);
ALTER TABLE acp1.personal_profile ENABLE ROW LEVEL SECURITY;
ALTER TABLE acp1.personal_profile FORCE ROW LEVEL SECURITY;
CREATE POLICY private_personal_profile ON acp1.personal_profile
 USING (
   tenant = current_setting('acp.tenant_id',true)
   AND owner_subject = current_setting('acp.subject_id',true)
 )
 WITH CHECK (
   tenant = current_setting('acp.tenant_id',true)
   AND owner_subject = current_setting('acp.subject_id',true)
 );
GRANT SELECT,INSERT,UPDATE ON acp1.personal_profile TO acp_app;
