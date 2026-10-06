-- M4a: put personal conversation turns onto the canonical task/run/event ledger.
-- Existing administrative diagnostics remain the only tenant-wide task kind.

ALTER TABLE acp1.message
    ADD CONSTRAINT message_owner_id_unique UNIQUE (tenant, owner_subject, id);

ALTER TABLE acp1.task
    DROP CONSTRAINT IF EXISTS task_diagnostic_check;
ALTER TABLE acp1.task
    ALTER COLUMN diagnostic DROP NOT NULL;
ALTER TABLE acp1.task
    ADD COLUMN kind text NOT NULL DEFAULT 'admin_diagnostic',
    ADD COLUMN conversation_id uuid,
    ADD COLUMN input_message_id uuid;

ALTER TABLE acp1.task
    ADD CONSTRAINT task_kind_check
        CHECK (kind IN ('admin_diagnostic', 'personal_turn')),
    ADD CONSTRAINT task_shape_check
        CHECK (
            (
                kind = 'admin_diagnostic'
                AND diagnostic = 'quantum-platform-pod-readiness'
                AND conversation_id IS NULL
                AND input_message_id IS NULL
            )
            OR
            (
                kind = 'personal_turn'
                AND diagnostic IS NULL
                AND conversation_id IS NOT NULL
                AND input_message_id IS NOT NULL
            )
        ),
    ADD CONSTRAINT task_personal_conversation_fk
        FOREIGN KEY (tenant, requested_by, conversation_id)
        REFERENCES acp1.conversation(tenant, owner_subject, id),
    ADD CONSTRAINT task_personal_input_fk
        FOREIGN KEY (tenant, requested_by, input_message_id)
        REFERENCES acp1.message(tenant, owner_subject, id);

ALTER TABLE acp1.task
    DROP CONSTRAINT IF EXISTS task_tenant_requested_by_idempotency_key_key;

CREATE UNIQUE INDEX task_admin_idempotency_unique
    ON acp1.task(tenant, requested_by, idempotency_key)
    WHERE kind = 'admin_diagnostic';

CREATE UNIQUE INDEX task_personal_idempotency_unique
    ON acp1.task(tenant, requested_by, idempotency_key)
    WHERE kind = 'personal_turn';

CREATE UNIQUE INDEX task_personal_input_unique
    ON acp1.task(tenant, requested_by, input_message_id)
    WHERE kind = 'personal_turn';

ALTER TABLE acp1.run
    DROP CONSTRAINT IF EXISTS run_check,
    DROP CONSTRAINT IF EXISTS run_profile_check;
ALTER TABLE acp1.run
    ADD CONSTRAINT run_profile_check
        CHECK (profile IN ('admin-readonly', 'personal-general')),
    ADD CONSTRAINT run_success_payload_check
        CHECK (
            status <> 'succeeded'
            OR (
                profile = 'admin-readonly'
                AND summary IS NOT NULL
                AND evidence IS NOT NULL
            )
            OR (
                profile = 'personal-general'
                AND summary IS NOT NULL
            )
        );

ALTER TABLE acp1.message
    ADD COLUMN run_id uuid,
    ADD CONSTRAINT message_run_fk
        FOREIGN KEY (tenant, run_id) REFERENCES acp1.run(tenant, id);

CREATE UNIQUE INDEX message_personal_run_unique
    ON acp1.message(tenant, run_id)
    WHERE run_id IS NOT NULL AND author_kind = 'assistant';

CREATE INDEX personal_task_queue
    ON acp1.task(tenant, kind, requested_by, created_at, id);

DROP POLICY tenant_task ON acp1.task;
CREATE POLICY task_visibility ON acp1.task
    USING (
        tenant = current_setting('acp.tenant_id', true)
        AND (
            kind = 'admin_diagnostic'
            OR (
                kind = 'personal_turn'
                AND (
                    requested_by = current_setting('acp.subject_id', true)
                    OR current_setting('acp.worker_role', true) = 'personal'
                )
            )
        )
    )
    WITH CHECK (
        tenant = current_setting('acp.tenant_id', true)
        AND (
            kind = 'admin_diagnostic'
            OR (
                kind = 'personal_turn'
                AND (
                    requested_by = current_setting('acp.subject_id', true)
                    OR current_setting('acp.worker_role', true) = 'personal'
                )
            )
        )
    );

DROP POLICY tenant_run ON acp1.run;
CREATE POLICY run_visibility ON acp1.run
    USING (
        tenant = current_setting('acp.tenant_id', true)
        AND EXISTS (
            SELECT 1
            FROM acp1.task t
            WHERE t.tenant = run.tenant AND t.id = run.task_id
        )
    )
    WITH CHECK (
        tenant = current_setting('acp.tenant_id', true)
        AND EXISTS (
            SELECT 1
            FROM acp1.task t
            WHERE t.tenant = run.tenant AND t.id = run.task_id
        )
    );

DROP POLICY tenant_event ON acp1.event;
CREATE POLICY event_visibility ON acp1.event
    USING (
        tenant = current_setting('acp.tenant_id', true)
        AND EXISTS (
            SELECT 1
            FROM acp1.run r
            WHERE r.tenant = event.tenant AND r.id = event.run_id
        )
    )
    WITH CHECK (
        tenant = current_setting('acp.tenant_id', true)
        AND EXISTS (
            SELECT 1
            FROM acp1.run r
            WHERE r.tenant = event.tenant AND r.id = event.run_id
        )
    );
