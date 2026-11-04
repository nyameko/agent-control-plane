"""Optional second, non-Hermes personal harness over the existing model gateway.

This deliberately has no tools, filesystem operations, SDK config persistence,
scheduler permissions or its own conversation database. ACP remains canonical.
"""
import os

from agent_control_plane.personal_context_prompt import canonical_prompt
from agent_control_plane.personal_runtime import PERSONAL_SOUL


def respond(context, session_id):
    # Optional dependency is installed in the reviewed worker image. Import is
    # deferred so the default Hermes profile never needs PydanticAI at runtime.
    from pydantic_ai import Agent
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.openai_compatible import OpenAICompatibleProvider

    if not isinstance(session_id, str) or not session_id.startswith("acp-"):
        raise ValueError("Canonical ACP run/session identifier required")
    model = OpenAIChatModel(
        os.environ["ACP_MODEL"],
        provider=OpenAICompatibleProvider(
            "acp-inference-gateway",
            base_url=os.environ["ACP_MODEL_BASE_URL"],
            api_key=os.environ["ACP_MODEL_API_KEY"],
        ),
    )
    # No tools or delegation; this is a bounded inference-only harness.
    agent = Agent(model, instructions=PERSONAL_SOUL, tools=[], retries=0)
    result = agent.run_sync(canonical_prompt(context))
    answer = result.output
    if not isinstance(answer, str) or not answer.strip() or len(answer) > 30000:
        raise RuntimeError("Invalid alternate personal harness response")
    return answer
