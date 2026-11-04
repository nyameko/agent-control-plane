# M4e — second sandbox harness baseline (source-only until release)

The initial canonical personal execution path is **Hermes**. The second adapter
option is now **PydanticAI**, running against the same operator-configured
OpenAI-compatible gateway (including local vLLM/LiteLLM) with **zero tools**.
This reuses an existing framework rather than inventing an agent harness.

- `ACP_PERSONAL_HARNESS=hermes` is the default in the existing deployment.
- `ACP_PERSONAL_HARNESS=pydantic-ai` is a **reviewed worker deployment setting**,
  never a browser/user prompt toggle. The isolated ephemeral subprocess
  reconstructs the same source conversation, profile revision and approved
  memory list from ACP PostgreSQL. It does not read Hermes runtime caches
  or own a second conversation database.
- The shared `canonical_prompt` treats prior text and user preferences as
  **untrusted data**, not tool authority. Neither harness is allowed tools in
  this minimal M4e cross-runtime baseline.
- `pydantic-ai-slim[openai]` is installed in the immutable worker image under
  the narrow `alternate-harness` optional dependency. A fixture test uses a
  locally served OpenAI protocol endpoint, not a commercial model API.
- The ACP run records a distinct `pydantic-ai-slim:<installed version>` runtime
  revision; never label this run Hermes. Model identity remains the configured
  logical gateway route, and unreported tokens/effort should remain unreported.

## Not yet accepted live

The default worker will **not** automatically switch to PydanticAI. A human
operator must review the pinned image, memory/RLS controls, budgets and network
policies before promoting an alternate-harness staging worker. To close M4e,
the human should observe `nlisa` owner-created C1/profile/memory, stop the
ephemeral Hermes runtime, run the real PydanticAI adapter against the authorized
model gateway, inspect ACP's same UUIDs and actual different runtime revision,
and establish wrong-user denials. Do not set a live environment variable or
delete user data as part of source PR review.

The current harness choice is **operator-fixed per worker process**, not a
routing system or a user-selected provider/model list. Adaptive harness policy
is future work and must not block baseline science development.

Reference: https://pydantic.dev/docs/ai/models/compatible-apis/
