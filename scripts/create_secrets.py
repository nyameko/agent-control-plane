#!/usr/bin/env python3
"""Generate local Secret JSON for kubeseal; never writes into the Git checkout.

The output contains plaintext credentials. Seal it for the target cluster, then
store the sealed resources in infra-hpc-qc-k8s. This script never deploys anything.
"""

import argparse
import base64
import json
import os
import secrets
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model-api-key-file", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    # Refuse any Git working tree, including sibling repositories.
    if any((parent / ".git").exists() for parent in [output, *output.parents]):
        parser.error("Choose a private output directory outside every Git working tree")
    os.umask(0o077)
    output.mkdir(parents=True, exist_ok=False)
    private = Ed25519PrivateKey.generate()
    public_pem = (
        private.public_key()
        .public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        .decode()
    )
    private_pem = private.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    ).decode()
    owner_password, app_password = secrets.token_urlsafe(36), secrets.token_urlsafe(36)
    host = ("agent-control-plane-postgres.agent-control-plane.svc.cluster.local:5432/"
            "agent_control_plane")
    items = [
        (
            "agent-control-plane",
            "acp-db-owner",
            {
                "POSTGRES_PASSWORD": owner_password,
                "ACP_MIGRATION_DATABASE_URL": f"postgresql://acp_owner:{owner_password}@{host}",
            },
        ),
        (
            "agent-control-plane",
            "acp-db-app",
            {
                "ACP_APP_PASSWORD": app_password,
                "ACP_DATABASE_URL": f"postgresql://acp_app:{app_password}@{host}",
            },
        ),
        ("agent-control-plane", "acp-verification", {"public.pem": public_pem}),
        (
            "agent-control-plane",
            "acp-model",
            {
                "ACP_MODEL_API_KEY": args.model_api_key_file.read_text().strip(),
            },
        ),
        ("quantum-platform", "acp-signing", {"private.pem": private_pem}),
    ]
    for namespace, name, data in items:
        if any(not value for value in data.values()):
            raise ValueError("Empty credential supplied")
        resource = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {"name": name, "namespace": namespace},
            "type": "Opaque",
            "data": {key: base64.b64encode(value.encode()).decode() for key, value in data.items()},
        }
        (output / f"{name}.json").write_text(json.dumps(resource, indent=2) + "\n")
    print(f"Created {len(items)} Secret files in {output}; seal them before committing.")


if __name__ == "__main__":
    main()
