# Release, conformance and deployment evidence

## Separate source from live runtime

A pull request, migration SQL, configured image digest and running Pod are four different stages of delivery. A GitHub CI pass is **source acceptance** only. A ready API is **service availability** only. M4 acceptance also requires authorisation, client continuity, proper schema version, alternate harness tests where promised and non-destructive evidence capture. Do not report a milestone “complete” because its ADR or UI button exists.

## Release gate matrix

| Subsystem | Required evidence |
|---|---|
| M4a conversation | same project/message history survives API/worker/browser restart; wrong user denied |
| M4b private memory | v4 schema, explicit approval and revisions, cross-user protection, expiry/revocation |
| M4c programme rooms | v5 table, approved membership, revocation and forbidden-room requests |
| M4d skills | reviewed immutable reference; no automatic execution |
| M4e profile | v6 table, profile versioning, alternate harness reads canonical context |
| M4f browser Guide | observed UI/API behavior, safe processing status with real telemetry |
| M4g terminal | actual trusted portal pairing and relay, not simply an `acp` binary |

## Read-only checks before a change

Use `kubectl -n argocd get application agent-control-plane agent-control-plane-personal-worker`, `kubectl -n agent-control-plane get deploy,pods,jobs` and inspect deployed images. Check migration table using only a read-only app role query per the [conformance guide](https://github.com/nyameko/agent-control-plane/blob/main/docs/conformance/m4c-m4g-live-release-gates.md). A healthy Argo app may still report OutOfSync for a migration Job or required resource. Preserve exact drift for review.

## Promotion and rollback

Use immutable image digests, source-linked release notes, migration preflight and backups, scoped GitOps sync, and targeted acceptance tests. Reject a migration checksum mismatch rather than editing historical SQL. Do not force/prune Argo or restart a production worker to “see if it helps.” Any destructive continuity drill must have explicit approval, isolation and a known restoration plan.

## Incident records

Report commit, image digest, schema versions, Pod status, error classification, exact time, affected HTTP route, run ID and redacted outcome. Keep research conversations and secrets out of public ticket screenshots.

Reference: [M4 release gates](https://github.com/nyameko/agent-control-plane/blob/main/docs/conformance/m4c-m4g-live-release-gates.md), [M4b live acceptance](https://github.com/nyameko/agent-control-plane/blob/main/docs/conformance/m4b-live-acceptance.md), [M4a design](https://github.com/nyameko/agent-control-plane/blob/main/docs/M4-PERSISTENT-AGENTS.md).