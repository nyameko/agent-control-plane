"""HTTP surface for health and policy dry-runs."""

from fastapi import FastAPI

from agent_control_plane import __version__
from agent_control_plane.models import ExecutionPlan, Health, TaskRequest
from agent_control_plane.routing import plan_task

app = FastAPI(
    title="Agent Control Plane",
    version=__version__,
    description="Logical routing and policy API. V0.1 does not execute plans.",
)


@app.get("/health", response_model=Health)
def health() -> Health:
    return Health(status="ok", service="agent-control-plane", version=__version__)


@app.post("/v1/plans/dry-run", response_model=ExecutionPlan)
def dry_run(request: TaskRequest) -> ExecutionPlan:
    return plan_task(request)
