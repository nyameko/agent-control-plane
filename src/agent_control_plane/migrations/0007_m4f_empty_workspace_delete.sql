-- M4f: deliberately restricted hard-delete capability for EMPTY private workspaces.
-- Existing historical conversations, task/run provenance and M4b memory sources
-- must never be cascaded into deletion. Enforcement lives in owner-only ACP API,
-- row-locked guards and existing forced RLS; no DELETE granted on messages/runs.
GRANT DELETE ON acp1.project, acp1.conversation TO acp_app;
