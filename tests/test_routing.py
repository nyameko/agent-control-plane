from agent_control_plane.models import (
    Channel,
    Domain,
    Quality,
    ResourceRequirements,
    Sensitivity,
    TaskRequest,
)
from agent_control_plane.routing import plan_task


def request(**overrides):
    values = {
        "subject": "django:user:1",
        "tenant": "nyameko-lab",
        "channel": Channel.WEB,
        "domain": Domain.GENERAL,
        "intent": "Help me understand this result",
    }
    values.update(overrides)
    return TaskRequest(**values)


def test_infrastructure_deep_work_routes_model_and_execution_separately():
    plan = plan_task(
        request(
            domain=Domain.INFRASTRUCTURE,
            quality=Quality.DEEP,
            resources=ResourceRequirements(cpu_cores=64, memory_gib=128),
        )
    )
    assert plan.agent == "infra-orchestrator"
    assert plan.model_pool == "reasoning-deep"
    assert plan.execution_class == "sandbox-cpu-large"


def test_restricted_context_cannot_enable_external_models():
    plan = plan_task(
        request(
            sensitivity=Sensitivity.RESTRICTED,
            external_model_allowed=True,
        )
    )
    assert plan.external_model_allowed is False
    assert plan.model_pool == "general-private"
    assert "external model request denied by sensitivity policy" in plan.policy_notes


def test_discord_mutation_requires_portal_webauthn_approval():
    plan = plan_task(
        request(
            channel=Channel.DISCORD,
            domain=Domain.SECURITY,
            mutation_requested=True,
        )
    )
    assert plan.approval_required is True
    assert plan.approval_surface == "quantum-platform-webauthn"
    assert plan.execution_class == "sandbox-cpu-standard"


def test_qpu_requirement_uses_scheduler_mediated_class():
    plan = plan_task(
        request(
            domain=Domain.QUANTUM_WORKFLOW,
            resources=ResourceRequirements(qpu_modality="gate"),
        )
    )
    assert plan.execution_class == "slurm-qpu-gate"
    assert plan.agent == "quantum-workflow-orchestrator"
