# M4c–M4g: read-only cluster checks, controlled multiuser proof, alternate harness and release gate

**Status: procedure only — not observed deployment, migration or acceptance evidence.**
**Owner:** [ACP M4 #45](https://github.com/nyameko/agent-control-plane/issues/45), #48, #54, #55, #56; [QP Guide](https://github.com/nyameko/quantum-platform/issues/71).
**Operator location:** `k8s-cp-01`; `kubectl` and ArgoCD are **not** operated from the workstation.
**No script or command in the read-only block below merges, synchronizes, migrates, edits credentials, restarts a service or deletes data.**

## 1. Source/image identity and Argo drift — READ ONLY

The reported Quantum Platform state on 2026-11-04 was `Synced/Healthy` with
`users@sha256:0072b778c9515c49c723a8cee84e7423b8ed0f34933bed57e5b3a22deb466bca` and
`user-api@sha256:d7341da53384ef8229780d26e2b9cd24e60a3463f72495b805368069928376d3`.
These are **M4c/M4d**, not the newer M4f Guide-status image. The latter is staged separately in the Infra PR linked from #45.

```bash
# Commands for k8s-cp-01; record sanitized stdout and timestamps.
kubectl -n argocd get application quantum-platform agent-control-plane agent-control-plane-personal-worker
kubectl -n argocd get application agent-control-plane   -o jsonpath='{range .status.resources[*]}{.kind}{" "}{.namespace}{"/"}{.name}{" "}{.status}{"\n"}{end}'

kubectl -n agent-control-plane get deploy,sts,pods,jobs -o wide
kubectl -n agent-control-plane get deployment agent-control-plane-api   -o jsonpath='{.spec.template.spec.containers[*].image}{"\n"}'
kubectl -n agent-control-plane get pods   -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{range .status.containerStatuses[*]}{.name}{"="}{.imageID}{" "}{end}{"\n"}{end}'

kubectl -n quantum-platform get deployments   -o custom-columns=NAME:.metadata.name,IMAGE:.spec.template.spec.containers[*].image
kubectl -n quantum-platform get pods   -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{range .status.containerStatuses[*]}{.name}{"="}{.imageID}{" "}{end}{"\n"}{end}'
```

**Do not run `kubectl apply`, `argocd app sync`, migrations, Argo force/prune, `rollout restart`, `helm upgrade`, or a destructive test as part of diagnosis.** In particular, ACP `OutOfSync/Healthy` can mean drift between Git and live objects; preserve the actual delta for human review before changing state.

## 2. ACP schema readiness — READ ONLY

The repository's ACP `db.ready()` deliberately accepts schema versions **3, 4, 5 or 6**. Thus Argo `Healthy` and `/ready` **cannot** prove that the M4c programme tables (migration 5) or M4e portable profile (migration 6) exist. Read the live `acp1.schema_version` using the **already configured application role**, without printing `ACP_DATABASE_URL`, credentials or row content.

```bash
kubectl -n agent-control-plane exec deployment/agent-control-plane-api --   python -c 'import os, psycopg; c=psycopg.connect(os.environ["ACP_DATABASE_URL"]); print("schema:", c.execute("SELECT version FROM acp1.schema_version ORDER BY version").fetchall()); print("tables:", c.execute("SELECT to_regclass(%s), to_regclass(%s)", ("acp1.programme_conversation", "acp1.personal_profile")).fetchone()); c.close()'
```

Pass conditions:
- Migration **5** present *and* `programme_conversation` table resolvable for **M4c read-only rooms**.
- Migration **6** present *and* `personal_profile` table resolvable for **M4e profile**.
- Operator compares live API/worker image digests with the reviewed migrations and checksums before any schema action. A live version less than 5 means M4c must fail closed; a live version less than 6 means M4e profile hydration cannot be claimed.
- This command does not prove RLS, current membership, long-term durability or any client functionality.

## 3. M4f browser check — controlled tests after a human-approved image promotion

Use Firefox, researcher account `nlisa` if approved/available, and an administrator separately. Capture screenshot and video with private content redacted.

- Five clicks `New chat` and abandoned drafts must create **zero** ACP records; first `Send` makes **one** conversation; verify existing project association. Do not assume source tests prove live behavior.
- Existing transcript, workspace menus, memory correction and user/API compatibility still work.
- Confirm Guide **does not expose a model/provider dropdown**, and has one small **read-only** brain/status disclosure.
- With current fixed-model Hermes the brain must display `Processing class unavailable`/clear. Do not label a historical run yellow/red without canonical observed `routing.policy_revision` and `effective_effort_class`. No fabricated token counts; click must not enqueue inference.
- Keyboard/screen-reader labels, contrast at two widths and red-versus-error distinction must be tested.
- Read the exact imageIDs of *Pods* after rollout, not only Deployment spec strings.

## 4. M4c/M4d — approved identities, real membership and reproducible science handoff

**Prerequisite:** live v5, compatible API image, explicitly approved disposable research programme and real authenticated accounts: a PI, two approved researchers, and a member to revoke; plus outsider or second programme. Existing signed server-side proxy in Quantum Platform is authoritative on **every request**. The UI is presently a *read-only* programme-room preview; creating/posting may require separately approved API tests.

Record:
- [ ] PI creates a room under an approved test programme (existing REST path, **approved** mutation); the exact canonical room UUID persists.
- [ ] Member A and B each see the same room and transcript; outsider and other programme cannot list/read it; private projects/memories never appear in group history.
- [ ] Revoke member B in Quantum Platform. Their **next** list/read/post returns denial, including a browser already displaying an opened programme folder. Reopening must refresh and not resurrect a cached list. Other approved members remain authorized.
- [ ] Concurrent posts preserve sequence; duplicate `client_message_id` retries do not create duplicate messages (staging-only test if operational use is not approved).
- [ ] A portal researcher opens the **immutable** Qiskit/Bell notebook at `quantum-workflows` commit `6867222b0eda57e55796143c466a61660102a6d7` from Guide, reads requirements, and opens their ordinary Jupyter Workbench. The currently published feature links/imports; it does **not** silently install, execute, approve a skill, allocate GPUs, QPUs or Slurm jobs.
- [ ] A reviewed skill manifest, capability/entitlement binding and revocation must be verified separately before M4d full closeout.
- [ ] Log denied cases and UUIDs without actual message bodies, secret headers, signing assertions or full memory content.

## 5. M4e — portable profile and **actual** alternate-harness proof

Prerequisites: live v6, owner/tenant RLS, two independent real identities, and a disposable/test-only approved project. Current production worker code invokes **Hermes** from a fresh `TemporaryDirectory`; it *does* hydrate ACP-stored profile data into context at v6, but it does **not** prove an alternate harness can execute authenticated turns. `personal_profile.model_route` remains a legacy preference; it is not dynamic model routing.

- [ ] Account A sets a harmless profile instruction and saves revision/UUID through the full Guide. Account B cannot read/modify it (verify signed API and SQL RLS).
- [ ] A sends C1, records canonical project, conversation, message, run and profile IDs, and verifies a real successful response from the configured inference endpoint.
- [ ] After operator-approved **ephemeral runtime** replacement, send C2 in the same conversation. Confirm profile UUID/revision, retrieved *approved* memory, project association and complete transcript are identical; Hermes runtime-local files are not the state authority. Do not delete PostgreSQL PVCs or durable home volumes.
- [ ] In a **disposable sandbox only**, run one installed independent harness (e.g. Codex/Claude Code *if its local endpoint and licensing actually permit*, otherwise a previously reviewed OpenAI-compatible agent harness) using an ACP-provided **authorized read-only context snapshot** plus a real approved model route; it must not own another user database or write a conflicting transcript. Record exact harness name/version, model, context IDs and result. If no approved adapter exists, record **BLOCKED** and keep M4e open; a mock responder is not cross-harness proof.
- [ ] The alternate client resumes through canonical ACP APIs and the same `AgentPrincipal`; B and revoked resources denied. Record realized inference usage if reported, otherwise `not reported`.

Do not launch a new orchestration stack, grant additional GitHub/K8s privileges or call this passing without observed alternate-harness output.

## 6. M4g and destructive continuity — human approval required

The current `terminal_client.py` **requires an assertion from stdin** and has **no trusted SSH session broker**. Proposed architecture is [ADR 0012](../adr/0012-portal-mediated-terminal-authentication.md): browser-approved short-lived Platform pairing + server-side authenticated relay to ACP; no QP signer or browser cookie on login nodes. Until implemented and tested, **M4g is blocked**; a manual bearer token does not pass.

Approved staging acceptance flow once the broker is deployed:

1. A uses browser to create C1; Jupyter A reads and posts; SSH A pairs through portal, reads C1, and posts through trusted relay. New browser session sees exact same UUIDs and message ordering.
2. B attempts C1 and is denied; revoke A's terminal session, then prove the next relay request is denied even if the old process is still running. The normal shell and Slurm account continue working.
3. Back up ACP PostgreSQL with a tested restore plan (backup metadata only in evidence). Define explicit destructive scope and recovery criteria with operator; gain **separate human approval**.
4. Replace an *ephemeral* API pod, personal worker and Hermes runtime, then separately validate Jupyter/browser/terminal continuity. Any actual PostgreSQL restore/PVC replacement is a later controlled exercise with backups and rollback, **never** an ad hoc `kubectl delete` instruction.
5. Sign off full M4a–M4g only with observed run IDs, authorized/denied endpoint matrix, migration/checksum, immutable images, platform health, authenticated client transcripts (redacted), timings and owner review in ACP #45.

## SSH warning is not ACP broker evidence

The workstation's OpenSSH message about lack of post-quantum key exchange means the negotiated SSH KEX was not a recognized post-quantum/hybrid scheme. This is a separate OpenSSH client/server algorithm and upgrade assessment, not the ACP `AgentPrincipal` identity broker. For non-mutating diagnostics, inspect `ssh -Q kex` on the client and `ssh -vv ...` negotiated KEX; do not change sshd/PAM or disable warnings as part of M4 acceptance.

**Stop rule:** preserve live data and security; source merges, green GitHub CI, Argo health and notebook links do not by themselves complete the integrated M4 gate.
