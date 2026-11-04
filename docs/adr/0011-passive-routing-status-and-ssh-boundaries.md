# ADR 0011 — Report observed routing effort, never a user-selected "thinking mode"

**Status:** Proposed — interface and telemetry contract only; no runtime, model or database migration
**Date:** 2026-11-04
**Owners:** ACP M4e [#55](https://github.com/nyameko/agent-control-plane/issues/55), Quantum Guide M4f [#71](https://github.com/nyameko/quantum-platform/issues/71)
**Related:** M4d [#54](https://github.com/nyameko/agent-control-plane/issues/54), M4g [#56](https://github.com/nyameko/agent-control-plane/issues/56), integrated M4 [#45](https://github.com/nyameko/agent-control-plane/issues/45)

## Scope and problem

Guide is a small platform navigation and science-resource handoff, not a Claude/ChatGPT/Codex clone. ACP is the canonical context/permission and provenance authority; LiteLLM/model policy and external harness adapters own actual inference and orchestration. Do **not** add a provider dropdown or a fake "deeper thinking" switch.

The full Guide may show a small **passive brain status icon** in the composer/last-answer provenance area. An outlined/clear brain means the effective processing class is **unreported**, **not** that the model did no reasoning. When metadata is available, the colour describes the **policy-approved execution class actually used**, not an assertion about the model's private mental process.

| State | Wireframe icon | Accessible label | Permitted interpretation |
|---|---|---|---|
| `unreported` | outline / clear | Processing class unavailable | No certified route-effort classification for this run |
| `lookup` | blue | Quick answer / lookup | One short bounded response route or retrieved/help reference |
| `standard` | green | Standard response | Ordinary single-route dialogue under standard budget |
| `extended` | yellow | Extended analysis | Approved higher-budget synthesis or multi-step agent execution |
| `intensive` | red | Intensive synthesis | Expensive, bounded multi-agent/multi-model or higher-effort processing |

A red brain means *intensive work*, **not** failure or a warning; actual failed jobs must have a separate visible failure state. Colours must be accompanied by text/tooltip and accessible icon labels; no colour-only semantics. This is lightweight visual feedback, not a reward system, per-user performance ranking, or incentive for higher token spending.

## Source of truth / honesty

- Assign `effective_effort_class` **server-side only** from a versioned routing policy and the *observed* execution plan/adapter. Never infer it in browser JavaScript from prompt length, elapsed walltime, token count, model family, latency, colour preference or the presence of an essay-length reply.
- Existing M4e `personal_profile.model_route = general|reasoning|coding` is **a preference**. Current Hermes personal runtime uses fixed `ACP_MODEL`. It does not implement dynamic route selection: **do not display a coloured classification based on that field**.
- A future *optional* additive run provenance object, without overwriting existing run fields:
  ```json
  {
    "routing": {
      "policy_revision": "reviewed-ref",
      "effective_effort_class": "standard",
      "logical_route": "general-private",
      "model": "observed-model-id",
      "harness": "hermes",
      "agent_roles": ["research-guide"],
      "input_tokens": null,
      "output_tokens": null,
      "token_source": null,
      "execution_ms": null,
      "source_skill_refs": []
    }
  }
  ```
  These are **contract examples, not claims about current data**. All optional metrics are nullable. Record the actual model/harness used for each invocation, not merely a preferred route. For MoE, provide a redacted user-readable aggregate plus permitted per-agent route entries without exposing credentials, private prompts or hidden chain-of-thought.
- Never expose raw provider internal chain-of-thought, secret tool arguments, other users' programme data, undisclosed context, or privileged orchestration details. Human-facing explanation and citations are separate public answer artifacts, not hidden reasoning traces.
- Status updates during a run may show `queued`/`running`, but a completed class is displayed only when the response's own canonical run/provenance entry supports it. Unavailable or legacy data remains **unreported**, not guessed.
- The short sidebar Guide remains simple: send, brief answer, platform links. Detailed provenance belongs to full Guide, Jupyter and an authenticated run-detail view.
- No model/provider dropdown in MVP. A researcher can inspect chosen routes. Advanced override policy, if ever needed for notebooks/coding, belongs to entitled harness client settings, not primary Guide navigation.

## Acceptance before activation

1. Unit test every allowed status and missing/invalid metadata; unknown data always shows clear outline.
2. Verify simple vs extended routes with recorded runtime evidence; an inaccurate route claim fails the gate.
3. Simulate provider that omits token usage; UI shows `not reported` instead of a fabricated number.
4. Cross-user/tenant denial and programme revocation still apply to provenance details.
5. Confirm no increase in inference budget occurs merely because a user clicks the brain status; it is a read-only indicator, no toggle.
6. User/browser check with accessibility labels, low contrast and colour-blind modes. The icon cannot be mistaken for an error indicator.

## Boundaries for M4g

Existing `terminal_client.py` forwards only an explicitly supplied short-lived bearer assertion from stdin and validates the HTTPS endpoint; it **does not provide a trusted SSH session broker**. Operator must not distribute signing keys, bearer credentials or browser cookies to SSH/login nodes.

M4g completion depends on a reviewed, short-lived **Quantum Platform-issued**, AgentPrincipal-bound session exchange with revocation and fail-closed tests on a separate existing client. POSIX UID/GID, username, SSH keys and Slurm account alone are **never** ACP identity proof (ADR 0008). Keep normal OpenSSH shells available; do not install new shell hooks or new credential authorities until security review and operator approval.
