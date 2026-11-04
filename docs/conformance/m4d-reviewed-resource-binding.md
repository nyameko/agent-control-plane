# M4d — reviewed immutable notebook resources, enabled per researcher

This is deliberately a **small owner-private resource binding**, not a
new scientific SDK, an agent tool runner, Kubernetes plugin, workflow
engine or GitHub marketplace.

## Provenance and trust

Source-of-truth separation:
- `quantum-workflows/catalog/agent-skills/*.json`: **proposed**, inert
  notebook/source records, not automatically approved. Both currently
  proposed entries must remain **unapproved** until independent review.
- `agent-control-plane/reviewed_skills.json`: an **empty-by-default**
  developer-reviewed, image-pinned allowlist. Promoting one reviewed
  resource requires an explicit Git PR with independently verified source
  SHA, manifest SHA-256, reviewer, and resource path. This is not a
  browser-controlled endpoint.
- `acp1.skill_binding` / `acp1.skill_binding_revision` (new **schema v8**):
  owner/tenant `FORCE ROW LEVEL SECURITY` with immutable Git source
  reference, CAS revision, enable/revoke history and no delete grants.
  It **never** contains a secret, arbitrary script, shell command or QPU key.

Only `required_capabilities=["resource:read"]` and
`automatic_code_execution=false` are admitted by the v1 catalog parser.
The reference points to a `labs/.../*.ipynb` path on a particular
Git commit; it does not grant Jupyter/Slurm/provider permissions.
ACP *cannot* register reviewed entries through a user or model API.

## ACP API (all signed `agent:personal`)

- `GET /v1/skills/catalog`: only packaged, reviewed **inert** entries.
- `GET /v1/skills/bindings`: current signed owner's enabled/revoked entries;
  `currently_reviewed=false` if a formerly accepted catalog version was
  subsequently removed. Revocation stays auditable.
- `PUT /v1/skills/{id}/versions/{version}/binding` with `If-Match: "0"`
  to enable a new reviewed version; `"n"` to idempotently confirm or
  re-enable a revoked version. Unknown/proposed → **403**.
- `POST /v1/skills/{id}/versions/{version}/revoke` with current
  `If-Match: "n"` to revoke; wrong owner → **404**, stale → **412**.

These do not mutate user projects, install tools, execute code or allocate
resources. Runtime tools remain disabled in M4a–M4e. A future M5
scientific runner requires independent Quantum Platform entitlement,
scheduler authorization and numerical validation.

## Release order and acceptance

1. **Never deploy source/CI as live proof.** Source PR to `dev` first,
   CI with synthetic owner and cross-user RLS, migration checksum checks.
2. ACP live was last observed at schema v4. Operator separately reviews
   backup/restore, v5→v6→v7, then **v8** migration and compatible API.
   The Argo sync migration hook can change live databases and must be
   explicitly authorized.
3. Human `nlisa` accepts only after a real notebook entry has been
   reviewed and pinned in the packaged catalog via separate source PR.
   `nlisa` and another user verify owner enable, listing, stale
   rejection, revocation and no unauthorized code execution.
4. M4d notebook opening is a separate ordinary Jupyter user action.
   A link is not evidence of scientific simulation.
