# Security, tenancy and approvals

## Identity and data isolation

The AgentPrincipal UUID is the trusted external user reference. ACP accepts only short-lived, signature-verified, correctly scoped assertions from the registered Quantum Platform issuer. **Do not** infer ACP ownership from username, email, tenant string, SSH key, Slurm account or POSIX UID/GID. PostgreSQL row-level security must be enabled and forced on private data tables, using constrained database roles; test cross-user reads, writes, guessed UUIDs and room authorization.

## Secrets and tools

Model keys, DB DSNs, bearer assertions, WireGuard keys, and Kubernetes tokens are not conversation memories. Do not save them as skill content, PR comments or prompt examples. A tool-call request is untrusted input until a separate trusted policy authorizes it. Review allowlisted actions, shell access, network egress, filesystem mounts and budget limits.

## Execution levels

Reading docs/metadata may be allowed. Mutations to source or issues require repository permission and audit; cluster changes, DB migrations, provisioning, QPU charging and deletion must require explicit approval and policy checks. Agents cannot self-approve their own resource grants.

## Incident response

Revoke credentials at the issuer, preserve minimal redacted audit, isolate the affected worker, inspect RLS enforcement and scope validation, rotate compromised keys, rerun unauthorized-access tests, and restore from verified PostgreSQL/secret backups where needed. Security vulnerabilities should be privately reported.

References: [threat model](https://github.com/nyameko/agent-control-plane/blob/main/docs/11-threat-model.md), [identity policy](https://github.com/nyameko/agent-control-plane/blob/main/docs/04-identity-tenancy-and-policy.md), [ADR 0005](https://github.com/nyameko/agent-control-plane/blob/main/docs/adr/0005-human-approval-for-mutations.md).