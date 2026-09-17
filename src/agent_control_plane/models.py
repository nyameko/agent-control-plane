"""Portable V0.1 request and plan models.

These models deliberately describe logical requirements. Physical hosts, Kubernetes nodes and
Slurm partitions are resolved by infrastructure-owned adapters after policy approval.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Channel(StrEnum):
    WEB = "web"
    JUPYTER = "jupyter"
    GPTEL = "gptel"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    API = "api"
    SYSTEM = "system"


class Domain(StrEnum):
    GENERAL = "general"
    INFRASTRUCTURE = "infrastructure"
    QUANTUM_PLATFORM = "quantum-platform"
    QUANTUM_WORKFLOW = "quantum-workflow"
    RESEARCH = "research"
    SECURITY = "security"
    EDUCATION = "education"
    COMMUNITY = "community"


class Quality(StrEnum):
    FAST = "fast"
    BALANCED = "balanced"
    DEEP = "deep"


class Sensitivity(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class ResourceRequirements(StrictModel):
    cpu_cores: int = Field(default=1, ge=1, le=4096)
    memory_gib: int = Field(default=2, ge=1, le=32768)
    gpu_count: int = Field(default=0, ge=0, le=64)
    minimum_gpu_memory_gib: int = Field(default=0, ge=0, le=1024)
    multi_node: bool = False
    qpu_modality: str | None = None
    expected_runtime_seconds: int = Field(default=60, ge=1, le=2_592_000)


class TaskRequest(StrictModel):
    subject: str = Field(min_length=1, description="Stable external identity subject")
    tenant: str = Field(min_length=1)
    channel: Channel
    domain: Domain
    intent: str = Field(min_length=1, max_length=32_000)
    quality: Quality = Quality.BALANCED
    sensitivity: Sensitivity = Sensitivity.INTERNAL
    context_tokens_estimate: int = Field(default=8_000, ge=0, le=10_000_000)
    mutation_requested: bool = False
    external_model_allowed: bool = False
    resources: ResourceRequirements = Field(default_factory=ResourceRequirements)


class ExecutionPlan(StrictModel):
    contract_version: str = "1.0"
    agent: str
    runtime: str
    model_pool: str
    execution_class: str
    approval_required: bool
    approval_surface: str | None
    external_model_allowed: bool
    reasons: list[str]
    policy_notes: list[str]


class Health(StrictModel):
    status: str
    service: str
    version: str
