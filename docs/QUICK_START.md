# Contributor quick start

## Start with the architecture

ACP is the durable state/policy/coordination layer between Quantum Platform users and interchangeable agent runtimes/models/execution systems.

Read in this order:

1. [Vision, objectives and principles](01-vision-and-principles.md)
2. [Reference architecture](02-reference-architecture.md)
3. [Repository boundaries](03-repository-boundaries.md)
4. [Identity, tenancy and policy](04-identity-tenancy-and-policy.md)
5. [Memory, state and storage](05-memory-state-and-storage.md)
6. [Runtimes, harnesses and sandboxes](07-runtimes-harnesses-and-sandboxes.md)
7. [M4 persistent personal agent](M4-PERSISTENT-AGENTS.md)
8. [Roadmap](10-integration-roadmap.md)

## Four questions before adding an integration

1. Who owns canonical state?
2. Which stable identity owns/authorises it?
3. Which portable contract separates the component from ACP?
4. Which failure/restart test proves that separation?

## Current milestone

M4a is intentionally narrow:

~~~text
authenticated AgentPrincipal
        |
minimal project
        |
conversation
        |
canonical messages
        |
personal agent turn/run
        |
runtime adapter
        |
assistant message committed
~~~

Then destroy/restart clients and runtime workers and prove the conversation survives.

Do not pull M4b memory, M4c rich projects, M4d skills, M4e persistent personal Hermes profiles, M4f Guide or M4g SSH UX into M4a.

## Canonical state rule

~~~text
human identity                  -> Quantum Platform
conversation / agent context    -> ACP PostgreSQL
runtime cache/session           -> runtime
scientific result               -> quantum-workflows
scheduler job                   -> scheduler/provider
source/shared definitions       -> Git
large artifact                  -> project/object storage
~~~

## Identity rule

Use AgentPrincipal UUID for durable ACP ownership.

Do not use username, email or POSIX UID/GID as the ACP primary identity.

## Local validation

Use the repository Python environment and run:

~~~sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
ruff check src tests scripts
pytest
~~~

Database/concurrency tests require the documented disposable PostgreSQL test DSNs.

## Branch discipline

Ordinary work:

~~~text
feature/* / agent/*
       |
       v
      dev
       |
 release/vX.Y.Z
       |
      main
~~~

Do not bypass review/protection because a change was authored by an agent.
