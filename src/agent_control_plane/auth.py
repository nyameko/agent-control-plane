"""Only quantum-platform may assert an administrative identity."""

from dataclasses import dataclass
from uuid import UUID

import jwt
from fastapi import HTTPException, Request


@dataclass(frozen=True)
class Principal:
    subject: str
    tenant: str


def authenticate(request: Request) -> Principal:
    settings = request.app.state.settings
    header = request.headers.get("authorization", "")
    if not header.startswith("Bearer ") or len(header) > 8192:
        raise HTTPException(401, "Administrative service assertion required")
    try:
        claims = jwt.decode(
            header[7:],
            settings.public_key,
            algorithms=["EdDSA"],
            audience=settings.audience,
            issuer=settings.issuer,
            options={"require": ["sub", "tenant", "scope", "exp", "iat", "nbf", "jti"]},
            leeway=5,
        )
        subject = claims["sub"]
        prefix = "urn:quantum-platform:user:"
        if not subject.startswith(prefix):
            raise ValueError("Invalid subject")
        UUID(subject.removeprefix(prefix))
        UUID(claims["jti"])
        if (
            claims["tenant"] != settings.tenant
            or claims["scope"] != "admin:diagnostics"
            or claims["exp"] - claims["iat"] > 90
        ):
            raise ValueError("Invalid scope, tenant or lifetime")
    except (jwt.PyJWTError, ValueError, TypeError, KeyError, AttributeError):
        raise HTTPException(401, "Invalid administrative service assertion") from None
    return Principal(subject, claims["tenant"])
