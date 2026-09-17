"""Deterministic baseline routing.

An intelligent router can later propose a route, but this policy layer remains the validator and
records why the route was accepted. It does not inspect live nodes or submit work.
"""

from __future__ import annotations

from agent_control_plane.models import (
    Channel,
    Domain,
    ExecutionPlan,
    Quality,
    Sensitivity,
    TaskRequest,
)

_AGENTS = {
    Domain.INFRASTRUCTURE: "infra-orchestrator",
    Domain.QUANTUM_PLATFORM: "platform-orchestrator",
    Domain.QUANTUM_WORKFLOW: "quantum-workflow-orchestrator",
    Domain.RESEARCH: "research-orchestrator",
    Domain.SECURITY: "security-orchestrator",
    Domain.EDUCATION: "tutor-orchestrator",
    Domain.COMMUNITY: "community-orchestrator",
    Domain.GENERAL: "general-assistant",
}

_EXTERNAL_CHANNELS = {Channel.TELEGRAM, Channel.DISCORD}


def _model_pool(request: TaskRequest, reasons: list[str]) -> str:
    if request.sensitivity in {Sensitivity.CONFIDENTIAL, Sensitivity.RESTRICTED}:
        reasons.append("sensitive context is restricted to self-hosted inference")
        return "reasoning-private" if request.quality is Quality.DEEP else "general-private"

    if request.quality is Quality.DEEP or request.context_tokens_estimate > 64_000:
        reasons.append("deep or long-context work uses the high-capability logical pool")
        return "reasoning-deep"

    if request.domain in {
        Domain.INFRASTRUCTURE,
        Domain.QUANTUM_PLATFORM,
        Domain.QUANTUM_WORKFLOW,
    }:
        reasons.append("engineering work uses the interactive code pool")
        return "code-interactive"

    if request.quality is Quality.FAST:
        reasons.append("fast interaction uses the low-latency pool")
        return "general-fast"

    reasons.append("balanced work uses the general self-hosted pool")
    return "general-private"


def _execution_class(request: TaskRequest, reasons: list[str]) -> str:
    resource = request.resources
    if resource.qpu_modality:
        reasons.append("QPU requirements are submitted through Slurm/QRMI or QDMI")
        return f"slurm-qpu-{resource.qpu_modality}"

    if resource.multi_node:
        reasons.append("multi-node work belongs to Slurm")
        return "slurm-multinode"

    if resource.gpu_count > 1 or resource.minimum_gpu_memory_gib > 80:
        reasons.append("large GPU work uses the Slurm H200 class")
        return "slurm-h200"

    if resource.gpu_count == 1:
        reasons.append("single-GPU work uses the interactive A100 class")
        return "slurm-a100"

    if resource.cpu_cores > 32 or resource.memory_gib > 128:
        reasons.append("large CPU work uses a 64-vCPU sandbox class")
        return "sandbox-cpu-large"

    if request.mutation_requested:
        reasons.append("change preparation is isolated from the control-plane service")
        return "sandbox-cpu-standard"

    reasons.append("reasoning-only work does not allocate a separate execution worker")
    return "none"


def plan_task(request: TaskRequest) -> ExecutionPlan:
    """Return a policy-valid logical plan without executing it."""

    reasons: list[str] = []
    notes: list[str] = []
    agent = _AGENTS[request.domain]
    reasons.append(f"domain maps to {agent}")

    external_allowed = (
        request.external_model_allowed
        and request.sensitivity in {Sensitivity.PUBLIC, Sensitivity.INTERNAL}
    )
    if request.external_model_allowed and not external_allowed:
        notes.append("external model request denied by sensitivity policy")

    approval_required = request.mutation_requested
    approval_surface: str | None = None
    if approval_required:
        approval_surface = "quantum-platform"
        reasons.append("all mutations require a plan-bound approval")

    if request.channel in _EXTERNAL_CHANNELS:
        notes.append("external chat is an untrusted liaison surface")
        if request.mutation_requested:
            notes.append("Telegram/Discord cannot approve privileged mutations")
            approval_surface = "quantum-platform-webauthn"

    if request.domain is Domain.SECURITY:
        notes.append("security telemetry and attacker-controlled strings are treated as data")

    return ExecutionPlan(
        agent=agent,
        runtime="hermes",
        model_pool=_model_pool(request, reasons),
        execution_class=_execution_class(request, reasons),
        approval_required=approval_required,
        approval_surface=approval_surface,
        external_model_allowed=external_allowed,
        reasons=reasons,
        policy_notes=notes,
    )
