"""Authenticated administrative task API. No infrastructure mutation endpoint."""

from contextlib import asynccontextmanager
from typing import Annotated, Literal
from uuid import UUID

import psycopg
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict

from agent_control_plane import __version__, db
from agent_control_plane.auth import Principal, authenticate
from agent_control_plane.models import ExecutionPlan, TaskRequest
from agent_control_plane.routing import plan_task
from agent_control_plane.settings import Settings


class DiagnosticRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    diagnostic: Literal["quantum-platform-pod-readiness"]


Admin = Annotated[Principal, Depends(authenticate)]


def create_app(settings=None):
    configured = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app):
        configured.validate()
        yield

    app = FastAPI(
        title="Agent Control Plane",
        version=__version__,
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.settings = configured

    @app.exception_handler(psycopg.Error)
    async def database_unavailable(request: Request, exc):
        from fastapi.responses import JSONResponse

        return JSONResponse({"detail": "Task store unavailable"}, status_code=503)

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "agent-control-plane", "version": __version__}

    @app.get("/ready")
    def readiness():
        with db.connection(configured.database_url) as conn:
            try:
                db.ready(conn)
            except RuntimeError:
                raise HTTPException(503, "Database role or migration is not ready") from None
        return {"status": "ready"}

    @app.post("/v1/plans/dry-run", response_model=ExecutionPlan)
    def dry_run(request: TaskRequest, principal: Admin):
        if request.subject != principal.subject or request.tenant != principal.tenant:
            raise HTTPException(403, "Plan identity must match authenticated identity")
        return plan_task(request)

    @app.post("/v1/admin/tasks", status_code=202)
    def submit(
        request: DiagnosticRequest,
        principal: Admin,
        response: Response,
        idempotency_key: Annotated[UUID, Header()],
    ):
        with db.connection(configured.database_url) as conn:
            try:
                task_id, created = db.create_task(conn, principal, idempotency_key)
            except db.QueueFull:
                raise HTTPException(
                    429,
                    "An active diagnostic exists or the queue is full",
                    headers={"Retry-After": "30"},
                ) from None
            response.status_code = 202 if created else 200
            response.headers["Location"] = f"/v1/admin/tasks/{task_id}"
            return db.task_detail(conn, principal.tenant, task_id)

    @app.get("/v1/admin/tasks")
    def history(principal: Admin, offset: Annotated[int, Query(ge=0, le=10000)] = 0):
        with db.connection(configured.database_url) as conn:
            rows = db.list_tasks(conn, principal.tenant, offset)
        return {"items": rows, "offset": offset, "page_size": 50}

    @app.get("/v1/admin/tasks/{task_id}")
    def detail(task_id: UUID, principal: Admin):
        with db.connection(configured.database_url) as conn:
            result = db.task_detail(conn, principal.tenant, task_id)
        if result is None:
            raise HTTPException(404, "Task not found")
        return result

    return app


app = create_app()
