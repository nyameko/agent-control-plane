# Operator runbook

## Prerequisites

Operations are managed from the authorised Kubernetes administration host. The infrastructure repository owns Argo manifests, SealedSecrets, image digests, PostgreSQL Kubernetes deployment and networking; ACP owns API/worker source and its ordered migrations.

## Read-only first

```sh
kubectl -n argocd get application agent-control-plane agent-control-plane-personal-worker
kubectl -n agent-control-plane get deploy,sts,pods,jobs
kubectl -n agent-control-plane get deploy -o custom-columns=NAME:.metadata.name,IMAGE:.spec.template.spec.containers[*].image
```

Check desired Git revision, live image digest and pod events. Investigate `OutOfSync/Healthy` as a drift signal, not a request to force-sync. Never print `ACP_DATABASE_URL`, database passwords, JWT private keys or bearer material to console logs/tickets.

## Schema gates

The source migration list includes versions 1–6: foundational tables, personal agent history, turn ledger, private memories, programme rooms and portable personal profiles. A deployed image may accept multiple schema versions; therefore `/ready` and Argo Healthy do **not** prove migration 5/6 are applied. Use the read-only version/table check in [live conformance runbook](https://github.com/nyameko/agent-control-plane/blob/main/docs/conformance/m4c-m4g-live-release-gates.md) using the already configured app role. Do not independently run schema-owner credentials from an application Pod.

## Promotion and rollback

Stage images with immutable digests and review migration compatibility before promotion. Database migrations can be irreversible: take verified backups and document rollout/rollback at the schema *and* application layer. After deployment perform API readiness, RLS tests, wrong-user requests, canonical history retrieval, project/memory/profile operation checks and approved destructive continuity tests. Do not mark M4g passed until a real brokered SSH session has been observed.

See [M4a conformance](https://github.com/nyameko/agent-control-plane/blob/main/docs/conformance/m4b-live-acceptance.md), [M4c–M4g release gates](https://github.com/nyameko/agent-control-plane/blob/main/docs/conformance/m4c-m4g-live-release-gates.md) and [infrastructure M4 guide](https://github.com/nyameko/infra-hpc-qc-k8s/blob/main/docs/tutorials/15-m4-live-readiness-and-memory-activation.md).