"""Bounded M4a personal Hermes adapter hydrated entirely from canonical ACP context."""

import json
import os
import sys
from pathlib import Path

from agent_control_plane.personal_context_prompt import canonical_prompt

PERSONAL_SOUL = """You are a personal research and engineering assistant for Quantum Platform.
The conversation supplied by Agent Control Plane is the canonical conversation history for this
turn. Use it as context, but do not invent memories or facts that are not present. You have no
tools in M4a and cannot execute commands, modify infrastructure, submit jobs, contact people, or
claim that external actions occurred. Be useful, concise, and explicit about uncertainty.
For Quantum Platform navigation: researchers can request membership or submit a new
research-programme PI application at https://quantum.nyameko.com/programmes/; submitting
does not confer approval. Public SSH and WireGuard keys are registered through Account
Security, never by sending private keys to an agent. The Jupyter Workbench is at
https://quantum.nyameko.com/workbench/ and Slurm runs are at
https://quantum.nyameko.com/runs/ when scheduler integration is working. Explain these
existing self-service routes accurately, even though you cannot click or submit for a user.
Never invent a GPU/QPU allocation, programme approval or external provider credential.
"""


def respond(context, session_id):
    from hermes_state import SessionDB
    from run_agent import AIAgent

    home = Path(os.environ["HERMES_HOME"])
    state = SessionDB(home / "state.db")
    agent = None
    try:
        # Model-specific OpenAI-compatible fields are supplied by the deployment.
        # The M4a personal adapter itself stays independent of the model vendor.
        extra_body_text = os.environ.get("ACP_PERSONAL_MODEL_EXTRA_BODY_JSON", "").strip()
        extra_body = json.loads(extra_body_text) if extra_body_text else {}
        if not isinstance(extra_body, dict):
            raise ValueError("ACP_PERSONAL_MODEL_EXTRA_BODY_JSON must be a JSON object")
        prompt = canonical_prompt(context)
        agent = AIAgent(
            model=os.environ["ACP_MODEL"],
            base_url=os.environ["ACP_MODEL_BASE_URL"],
            api_key=os.environ["ACP_MODEL_API_KEY"],
            provider="custom",
            api_mode="chat_completions",
            enabled_toolsets=[],
            disabled_toolsets=[],
            max_iterations=1,
            max_tokens=1600,
            request_overrides={"extra_body": extra_body} if extra_body else None,
            skip_context_files=True,
            load_soul_identity=False,
            skip_memory=True,
            skip_background_review=True,
            checkpoints_enabled=False,
            session_id=session_id,
            session_db=state,
            quiet_mode=True,
            run_budget_seconds=int(os.environ["ACP_RUN_TIMEOUT_SECONDS"]),
        )
        if agent.tools or agent.valid_tool_names:
            raise RuntimeError("Hermes tool surface is not empty; refusing personal M4a run")
        result = agent.run_conversation(prompt, system_message=PERSONAL_SOUL)
        if result.get("failed") or result.get("error") or not result.get("completed"):
            raise RuntimeError("Hermes personal turn did not complete")
        if any(message.get("tool_calls") for message in result.get("messages", [])):
            raise RuntimeError("Unexpected tool call")
        answer = result.get("final_response")
        if not isinstance(answer, str) or not answer.strip() or len(answer) > 30000:
            raise RuntimeError("Invalid Hermes personal response")
        return answer
    finally:
        if agent is not None:
            agent.close()
        state.close()


def main():
    request = json.loads(Path(sys.argv[1]).read_text())
    answer = respond(request["context"], request["session_id"])
    Path(sys.argv[2]).write_text(json.dumps({"response": answer}))


if __name__ == "__main__":
    main()
