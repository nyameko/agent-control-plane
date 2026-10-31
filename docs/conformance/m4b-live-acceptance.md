# M4b: operator-guided live acceptance

**Owner:** Agent Control Plane issue #31 and integrated release issue #45.
**Status:** Proposed operator test procedure, not live acceptance evidence.

## Already implemented

ADR 0009, minimal memory API contract, schema version 4 with forced
PostgreSQL RLS, candidate/approve/correct/revoke APIs and feature-flagged
Hermes hydration are already in Git. Issue #31 records observed v4
deployment and a real approved-memory C1-to-C2 recall. The memory
correction UI and corresponding immutable image GitOps PRs are separately
tracked in Quantum Platform and infra. **Do not rerun migration hooks.**

This adds only a repeatable optional client-side acceptance probe, not
another agent runtime, state store, UI or scheduler.

## Operator and security preconditions

1. Use a dedicated test account and a second independent researcher's
   test identity. Tokens must be short-lived, signed agent:personal
   assertions from the trusted Quantum Platform backend, not browser
   tokens exposed to client JavaScript.
2. Verify actual schema version, API/worker image digests, readiness,
   parent/child Argo resource differences, backups and gateway on
   k8s-cp-01. No kube commands run from this script.
3. The test creates four *private* test conversations and a temporary
   synthetic preference. Memory is revoked on success and best-effort on
   failure. Conversations remain and must be handled according to
   retention policy. This is not a no-write test.
4. Use only an approved HTTPS ACP API URL, or localhost HTTP over an
   explicitly approved secure tunnel. Never paste credentials into PRs,
   chat, shell command arguments or browser JavaScript.
5. Any Pod restart, Helm/Argo sync or migration is a separate
   human-approved action. The script cannot perform or authorize one.

## Invocation

    export ACP_M4B_TEST_TOKEN='<short-lived test-user assertion>'
    export ACP_M4B_OTHER_TOKEN='<different test-user assertion>'

    # Dry-run: makes no HTTP calls
    python scripts/m4b_live_acceptance.py \
      --base-url https://YOUR-APPROVED-ACP-API-ORIGIN

    # Perform user-scoped acceptance writes and model turns
    python scripts/m4b_live_acceptance.py \
      --base-url https://YOUR-APPROVED-ACP-API-ORIGIN \
      --execute --pause-for-restart

    unset ACP_M4B_TEST_TOKEN ACP_M4B_OTHER_TOKEN

With --pause-for-restart, after approving the memory the script waits
for an operator to authorize and observe independent API/worker/ephemeral
runtime replacement before continuing. It does not cause a restart.

The acceptance probe checks: candidate excluded from retrieval; approval
visible to retrieval; fresh C2 real model recall of PennyLane; correction
visible to retrieval; fresh C3 model recall of Qiskit; second signed user
denied access and modification; past-expiry rejected; revocation excluded
from retrieval and a new C4 turn after revocation.

Passing model output does *not* prove model context omitted revoked text;
the model may guess. Verify hydrated inputs or inspected code together
with RLS, tests and observable runs. This probe tests past-expiry
rejection, not expiry *after* approval.

## Required observed evidence for M4b closeout

- [ ] Exact live schema/checksum and immutable API/worker image digests.
- [ ] C1 source/provenance, approved memory UUID and revision.
- [ ] Real Hermes C2 after approved destructive runtime replacement.
- [ ] Corrected revision, new C3, no old body in retrieval.
- [ ] Revoked memory, C4, no recalled content from memory hydration.
- [ ] Expiry and source invalidation policy tested.
- [ ] Second subject and second tenant denied at API and SQL RLS layers.
- [ ] Reopened browser and alternate Jupyter/SSH continuity; M4a #21
      remaining tests tracked distinctly.
- [ ] Parent Argo drift diagnosed and reconciled declaratively;
      isolated restore tested, database archives never posted.
- [ ] Two researchers validate the actual browser memory controls and
      useful error messages, not only API responses.

No CI check, accepted PR or synthetic probe alone closes issue #31.

## M4c–M4g and real research value

Keep the integrated gate in issue #45; no new agent-management framework.

- M4c: enforce actual project and PI-authorized programme access (#48).
  Only expose sidebar pin/rename/move/archive where canonical APIs work.
- M4d: reviewed, versioned skill contracts. Seed one Bloch/Bell teaching
  workflow and one narrow diagnostic, not a marketplace.
- M4e: portable Hermes profile materialization with ACP authoritative;
  prove an alternative agent harness adapter, no competing memory.
- M4f: reusable Quantum Guide rail across portal/Jupyter, clear errors,
  run status, visible memory review and strong onboarding. Benchmark
  existing frontend components before writing custom product surfaces.
- M4g: thin authenticated terminal client over ACP APIs, preserving
  canonical UUIDs and the ordinary SSH shell.
- In parallel NOW: a real quantum-workflows notebook-to-run-to-evidence
  vertical slice with versioned manifests, initially Bell or Ising.
- After M4: measured LiteLLM routing/budgets, dedicated A100 benchmark
  before additional H200 provisioning, bounded Paperclip/GitHub
  engineering agents, and opt-in research intelligence only once the
  fundamental scientific journey is usable.

**Stop rule:** if ACP work cannot be traced to a user-visible improvement,
a verified continuity/security contract or a reproducible scientific
result, defer it in favor of quantum-workflows.
