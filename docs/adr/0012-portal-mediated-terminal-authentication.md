# ADR 0012 — Quantum Platform-mediated terminal authentication for M4g

**Status:** Proposed; review gate, **not implemented or deployed**
**Date:** 2026-11-04
**Owners:** [ACP M4g #56](https://github.com/nyameko/agent-control-plane/issues/56), [M4 integrated #45](https://github.com/nyameko/agent-control-plane/issues/45)
**Related:** ADR 0008 (AgentPrincipal, not POSIX identity), ADR 0011 (routing/provenance), M4c #48, M4e #55.

## Decision and scope

Use **Quantum Platform as the sole identity/session issuer and entitlement authority**. The initial SSH/TUI path uses an existing portal-browser-authenticated, **device-style user approval** to pair a disposable terminal session with a Quantum Platform `AgentPrincipal`. The thin terminal client sends operations to a **Quantum Platform-authenticated terminal relay**, not directly to the ACP bearer-authenticated API. The relay authenticates the live pairing/session **on every call**, rechecks account state and operation permissions, and invokes the already-existing server-side Quantum Platform `agent_client.call` to ACP with a fresh short-lived EdDSA assertion. ACP maintains its existing canonical private projects, conversation UUIDs, messages, run IDs, force-RLS and signature validation. No additional conversation store, CLI framework or independent agent identity provider.

This is an explicit **portal authorization of a terminal session**, not a claim that a POSIX UID, SSH username or SSH public key proves an ACP identity. The standard OpenSSH login remains intact. A verified POSIX/resource mapping can be checked as an *additional* constraint when such a trusted mapping is available; it is never the sole authentication step. Users must be able to cancel pairing without affecting their shell.

### Minimal trust sequence (reviewed design, not existing endpoints)

1. From an ordinary SSH shell, the user invokes the existing thin `acp` client with a terminal-pairing option. It creates an ephemeral high-entropy verifier in **process memory** (not argv, shell history, disk or environment logs) and requests a short-lived pairing challenge from the Platform. The Platform returns an opaque high-entropy `device_code`, a human-checkable verification code, and an allowlisted HTTPS Platform approval URL. Validity <= 5 minutes; poll frequency and rate limits enforced.
2. The terminal displays the URL and verification code. Independently, the user opens the Platform site, authenticates with the **normal existing** account/session security, and approves a displayed challenge matching the terminal. The approval page clearly names the scope (`agent:personal` initially), terminal/client name, duration and revocation option; require step-up authentication when security policy demands. CSRF protection applies to approval. Never approve based merely on viewing or copying the code.
3. The Platform resolves the approving user to its existing **immutable AgentPrincipal UUID**. It verifies account active/not suspended, terminal entitlement if configured, and the challenge status/expiry/one-time-use constraints. It records an auditable pairing/session with random ID and expiry, scoped to the specific approver; **do not trust any user/tenant/scope passed by the client**. Pending, expired, reused, revoked or mismatched challenges fail closed.
4. The terminal exchanges its `device_code` plus ephemeral verifier for a **Platform-only, opaque, short-lived session capability**. Store capability and verifier in process memory only; secure stdin/pipe handoff if needed by the existing client. The capability cannot sign ACP assertions and carries no Kubernetes, Slurm, provider, GitHub, QP signing-key or cross-programme authority. To reduce token theft, bind session to the verifier where supported and rotate or reauthenticate on expiry.
5. Each terminal request goes to the **Platform relay** over validated TLS. Platform checks the session is still active, its binding and scopes, the mapped AgentPrincipal, resource authorization and rate/budget policy. It forwards through the *existing* signed Platform->ACP client with a fresh `agent:personal` assertion (issuer `quantum-platform`, audience `agent-control-plane`, immutable `sub`, tenant, `jti`, `iat/nbf/exp`). No ACP signing key, browser cookie, bearer JWT or refresh token is ever written or copied to a login node. ACP responds with the same canonical records.
6. Logout, account suspension, session revocation, browser approval cancellation, server expiry and denied entitlement block the **next relay call**. The Platform never returns the internal ACP assertion to the terminal. Terminal surfaces a clear reauthentication error; independent shell commands continue working.

Avoid conflating a *short-lived signed JWT* with actual one-time use: the current ACP auth verifier enforces signature, audience, tenant, scope and expiry, but not a persistent `jti` replay ledger. Immediate revocation is therefore enforced **at the Platform terminal relay**, not asserted for a stolen bare JWT sent directly to ACP. In this design, clients never receive the bare JWT; ACP API remains network-restricted.

### API contract proposal (names not yet implemented)

- `POST /api/v1/agent/terminal/pairings/` — create pending device challenge; no authentication grant.
- `GET/POST /agent/terminal/approve/` — browser-authenticated, CSRF-protected, explicit approve/deny. Never place a terminal capability into frontend URL or JavaScript-visible logs.
- `POST /api/v1/agent/terminal/pairings/{id}/exchange/` — rate-limited, single-use redemption of approved challenge with possession verifier; returns a terminal-only opaque, session-scoped credential, *not* ACP-signed JWT.
- `POST /api/v1/agent/terminal/logout/` — revoke credential; expiry also automatic.
- `GET /api/v1/agent/terminal/projects/`, `conversations/`, `runs/{id}/` and `POST .../turns/` — existing Platform->ACP server proxy logic reused behind terminal session permission checks; one transport adapter for the current `terminal_client.py`, not another data model. Prefer established device authorization/OIDC libraries or existing framework auth components over handwritten cryptographic grants. These paths are examples awaiting a concrete framework/CSRF/API review.

Keep `agent:programme` out of initial terminal scope. Add it only after M4c revoked-membership proof, and recheck membership **on each action** through the current Platform authority. Do not use a signed stale programme role from a terminal as an access decision.

### Boundaries and negative tests

- No `ACP_JWT_PRIVATE_KEY`, Django signing key, cloud credentials, browser cookies, database password, provider keys or durable bearer tokens on SSH/login hosts. No changes to `sshd_config`, PAM, shell startup, `sudo`, Slurm or JupyterHub for the initial pairing implementation.
- Enforce TLS destination pinning/allowlist and no redirects; sensitive material never appears in argv, environment dumps, crash logs, referrer headers, shell history or telemetry. Avoid terminal OAuth tokens as CLI arguments. A token used for a sensitive `send` must not be printed in debug responses. Avoid chat-body text in shell history as well.
- Deny: anonymous request; wrong or reused code; unapproved/expired code; token exfiltration into second client without verifier; user B attempting A's session; disabled account; revoked session; wrong tenant; cross-user project, transcript, memory and run; programme scope; ambiguous POSIX mapping; replayed messages (existing UUID/idempotency).
- Verify terminal A and browser/Jupyter A read/write **the same ACP UUIDs**, B cannot read them, and revoked session cannot access the next request. Run after operator-reviewed staging release and collect redacted evidence.
- Concurrency: simultaneous requests have bounded ordering and idempotent retry. Short-lived credentials are not a substitute for owner/tenant SQL force-RLS.
- Never represent a device-pairing design PR, mock tests or a successful local `acp --token-stdin` demonstration as proof that a trusted broker was deployed.

### Rejected alternatives

| Alternative | Reason |
|---|---|
| Map SSH `whoami` or UID/GID directly to AgentPrincipal | Mutable/untrusted userland identity, easy impersonation across home/accounts |
| Put Quantum Platform EdDSA signer or long-lived ACP token on each login node | Catastrophic blast radius; undermines isolation |
| Reuse browser session cookies or browser JWTs on the shell host | Cross-origin session/token leakage and lifecycle bypass |
| Recreate an auth provider inside ACP or an agent-specific login database | Duplicates Platform authority and extends critical infrastructure |
| Make the terminal a privileged SSH/PAM hook | Unnecessary and high risk for a thin research client |

## Implementation/approval order

1. Approve this ADR with Platform identity/security owners; choose a reviewed OIDC/device grant library and a narrowly scoped Platform session-relay API. Threat-model phishing, verifier binding, entropy, polling, replay, audit, expiry, revocation and cross-tenant denial.
2. Land Platform pairing+relay behind disabled feature flag, tests and audit. Use a disposable client/session in staging only.
3. Adapt the existing ACP thin terminal client to use relay transport; no custom shell emulator, no new canonical state.
4. Operator performs authenticated browser/Jupyter/SSH cross-client checks **without** changing login-node configuration. Only then consider packaging through reviewed IaC; keep regular SSH working.
5. Post real evidence to ACP #56 and #45. No production activation without human authorization.

**Stop rule:** if the broker adds more identity machinery than an ordinary HTTPS device-style handoff plus existing signed proxy, reuse an established identity/access broker or defer M4g rather than growing ACP.
