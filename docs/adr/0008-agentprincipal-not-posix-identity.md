# ADR 0008 — AgentPrincipal UUID is the durable ACP subject

Status: accepted.

## Context

Users also receive POSIX UID/GID identities for Unix files, SSH and Slurm.

UID/GID is an execution identity, not a universal application identity. Usernames and email addresses are mutable and Django integer IDs are implementation-local.

## Decision

ACP uses Quantum Platform's immutable AgentPrincipal UUID as its stable external subject:

~~~text
urn:quantum-platform:user:<AgentPrincipal UUID>
~~~

POSIX UID/GID, username, SSH keys, WireGuard identity and programme memberships are linked attributes.

## Consequences

Changing/federating execution identity does not change project/conversation/memory ownership.

Web/Jupyter/SSH/editor clients share one durable subject.

ACP does not become a second user-account authority.
