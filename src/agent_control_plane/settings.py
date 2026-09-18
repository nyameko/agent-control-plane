"""Deployment configuration. No implicit credentials or external model fallback."""

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Settings:
    database_url: str
    public_key: str
    tenant: str = "nyameko"
    issuer: str = "quantum-platform"
    audience: str = "agent-control-plane"
    prometheus_url: str = "http://prometheus-server.monitoring.svc.cluster.local"
    model: str = ""
    model_base_url: str = ""
    profile_home: str = "/var/lib/hermes/admin-readonly"
    run_timeout: int = 180

    @classmethod
    def from_env(cls):
        key_file = os.environ.get("ACP_JWT_PUBLIC_KEY_FILE", "")
        return cls(
            database_url=os.environ.get("ACP_DATABASE_URL", ""),
            public_key=Path(key_file).read_text() if key_file else "",
            tenant=os.environ.get("ACP_TENANT_ID", "nyameko"),
            prometheus_url=os.environ.get("ACP_PROMETHEUS_URL", cls.prometheus_url).rstrip("/"),
            model=os.environ.get("ACP_MODEL", ""),
            model_base_url=os.environ.get("ACP_MODEL_BASE_URL", "").rstrip("/"),
            profile_home=os.environ.get("HERMES_HOME", cls.profile_home),
            run_timeout=int(os.environ.get("ACP_RUN_TIMEOUT_SECONDS", "180")),
        )

    def validate(self, *, worker=False):
        if not self.database_url or not self.tenant:
            raise ValueError("Database and tenant configuration are required")
        if worker:
            for value in (self.prometheus_url, self.model_base_url):
                url = urlsplit(value)
                if (
                    url.scheme not in {"http", "https"}
                    or not url.hostname
                    or url.username
                    or url.password
                    or url.query
                    or url.fragment
                ):
                    raise ValueError("A fixed HTTP(S) upstream URL without credentials is required")
            if not self.model or not 30 <= self.run_timeout <= 600:
                raise ValueError("A model and a 30–600 second run budget are required")
        elif not self.public_key:
            raise ValueError("JWT verification key is required")
