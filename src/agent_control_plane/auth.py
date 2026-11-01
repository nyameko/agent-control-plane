"""Verify short-lived identity assertions issued by Quantum Platform."""

from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request

KNOWN_SCOPES = frozenset({"admin:diagnostics", "agent:personal", "agent:programme"})


@dataclass(frozen=True)
class Principal:
    subject: str
    tenant: str
    scopes: frozenset[str] = frozenset()
    programme_id: int | None = None
    programme_role: str | None = None


def authenticate(request: Request) -> Principal:
    settings = request.app.state.settings
    header = request.headers.get("authorization", "")
    if not header.startswith("Bearer ") or len(header) > 8192:
        raise HTTPException(401, "Quantum Platform service assertion required")
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
        raw_scope = claims["scope"]
        if not isinstance(raw_scope, str):
            raise ValueError("Invalid scope")
        scopes = frozenset(raw_scope.split())
        programme_id = None
        programme_role = None
        if "agent:programme" in scopes:
            # Dedicated scope only: never mix private or administrative authority.
            if scopes != {"agent:programme"}:
                raise ValueError("Mixed programme scope")
            programme_id = claims.get("programme_id")
            programme_role = claims.get("programme_role")
            if (
                type(programme_id) is not int
                or programme_id <= 0
                or programme_role not in {"pi", "admin", "researcher"}
            ):
                raise ValueError("Untrusted programme entitlement")
        elif "programme_id" in claims or "programme_role" in claims:
            raise ValueError("Unexpected programme entitlement")
        if (
            claims["tenant"] != settings.tenant
            or not scopes
            or not scopes.issubset(KNOWN_SCOPES)
            or claims["exp"] - claims["iat"] > 90
        ):
            raise ValueError("Invalid scope, tenant or lifetime")
    except (jwt.PyJWTError, ValueError, TypeError, KeyError, AttributeError):
        raise HTTPException(401, "Invalid Quantum Platform service assertion") from None
    return Principal(subject, claims["tenant"], scopes, programme_id, programme_role)


Authenticated = Annotated[Principal, Depends(authenticate)]


def require_admin(principal: Authenticated) -> Principal:
    if "admin:diagnostics" not in principal.scopes:
        raise HTTPException(401, "Administrative service assertion required")
    return principal


def require_personal(principal: Authenticated) -> Principal:
    if "agent:personal" not in principal.scopes:
        raise HTTPException(401, "Personal-agent service assertion required")
    return principal


def require_programme(principal: Authenticated) -> Principal:
    if (
        principal.scopes != {"agent:programme"}
        or principal.programme_id is None
        or principal.programme_role is None
    ):
        raise HTTPException(401, "Current programme membership assertion required")
    return principal
