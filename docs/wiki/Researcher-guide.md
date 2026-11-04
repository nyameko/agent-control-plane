# Researcher guide: projects, conversations, memory

## Getting started

Authenticate to Quantum Platform, then open its [agent interface](https://quantum.nyameko.com/agent/) when enabled for your account. The portal calls ACP with a scoped server-issued assertion; users normally do **not** need ACP credentials, a direct bearer token or a model-provider subscription to use a configured local route.

Create a project for a research objective and a separate conversation for a subproblem. Keep scientific files and generated artifacts in the approved research directory or scientific results store; ACP is the canonical **context**, not a replacement for source control or large data storage.

## Conversation lifecycle

Create/open an authorised project; create a conversation; send a turn; check the returned task/run status and resulting canonical messages. Persist exact run IDs, source references, notebook links and experimental assumptions in messages. If a response reports code execution, inspect the actual task/run/provenance; textual claims are not computation evidence.

A browser refresh, notebook restart or approved worker restart must not cause canonical transcript loss. Conversation IDs stay stable, and user A cannot retrieve user B's UUID even if guessed. If missing, see [Troubleshooting](Troubleshooting.md) rather than creating a shadow account.

## Memory lifecycle

Private memory is not an unreviewed dump of every chat. Candidate memories derive from authorised source messages, have revisions, scope, verification status and sensitivity, and require approval before active retrieval. Review suggestions for mistakes and sensitive information. Corrections append new revisions; revocation makes a memory ineligible for future retrieval rather than pretending it never existed. Respect expiry and access controls.

## Model/skill choice

Users should ask for a task, not have to manage raw GPU/model names. ACP may route work through available configured model capabilities with transparent observed processing status. Skills are governed references to notebooks or manuals until separately authorised for execution; clicking a skill is not a GPU reservation.

See [memory contract](https://github.com/nyameko/agent-control-plane/blob/main/docs/M4b-MINIMAL-MEMORY-CONTRACT.md), [projects contract](https://github.com/nyameko/agent-control-plane/blob/main/docs/M4c-PROJECT-WORKSPACE-CONTRACT.md), and [personal agent milestone](https://github.com/nyameko/agent-control-plane/blob/main/docs/M4-PERSISTENT-AGENTS.md).