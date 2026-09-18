import os
import time
from uuid import uuid4

import jwt
import psycopg
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient

from agent_control_plane.api import create_app
from agent_control_plane.migrate import migrate
from agent_control_plane.settings import Settings


@pytest.fixture
def signing_key():
    return Ed25519PrivateKey.generate()


@pytest.fixture
def config(signing_key):
    public = (
        signing_key.public_key()
        .public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        .decode()
    )
    return Settings(
        database_url=os.getenv("ACP_TEST_DATABASE_URL", "postgresql://unused"),
        public_key=public,
        model="test-model",
    )


@pytest.fixture
def client(config):
    with TestClient(create_app(config)) as client:
        yield client


@pytest.fixture
def token(signing_key):
    subject = f"urn:quantum-platform:user:{uuid4()}"

    def make(**changes):
        now = int(time.time())
        claims = dict(
            iss="quantum-platform",
            aud="agent-control-plane",
            sub=subject,
            tenant="nyameko",
            scope="admin:diagnostics",
            iat=now,
            nbf=now,
            exp=now + 60,
            jti=str(uuid4()),
        )
        claims.update(changes)
        return {"Authorization": "Bearer " + jwt.encode(claims, signing_key, algorithm="EdDSA")}

    return make


@pytest.fixture
def database():
    owner = os.getenv("ACP_TEST_OWNER_DATABASE_URL")
    app = os.getenv("ACP_TEST_DATABASE_URL")
    if not owner or not app:
        pytest.skip("Real PostgreSQL test DSNs are required; see docs/12-phase1.md")
    with psycopg.connect(owner, autocommit=True) as conn:
        conn.execute("DROP SCHEMA IF EXISTS acp1 CASCADE")
        if not conn.execute("SELECT 1 FROM pg_roles WHERE rolname='acp_app'").fetchone():
            conn.execute("CREATE ROLE acp_app LOGIN PASSWORD 'test-only'")
    migrate(owner)
    return app
