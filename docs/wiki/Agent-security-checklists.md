# Security checklist for agents and platform developers

## Before an agent reads

Authenticate with a Quantum Platform issued assertion carrying a stable AgentPrincipal UUID and appropriate audience/scope. Resolve the intended project, conversation and programme from *authorized server records*; do not trust a guessed UUID or a client-supplied tenant string. Public docs and code can be indexed, but private user messages and memory must be filtered by tenant, owner, scope and consent before entering a prompt.

## Before an agent acts

Classify the action: plain answer, read-only introspection, code suggestion, Git issue/PR modification, resource allocation, secret access, application deployment, DB mutation, shell command or deletion. Reading a wiki does not grant the ability to execute its command. Human approval and trusted policy enforcement are mandatory for sensitive mutations, expensive QPU/GPU work, and any elevated terminal, scheduler or cluster action.

## Before using models and tools

Keep credentials in approved secret stores; pass only narrowly scoped short-lived tokens to services, not to model prompts or tool descriptions. Restrict outbound network, filesystem mounts, subprocess privileges and allowed tool set. Validate tool argument schemas and target resource ownership independently. Set timeout, budget, cancellation and log redaction policies; treat retrieved web, code and log text as untrusted input capable of prompt injection.

## Before calling it complete

Run negative tests: two users with same-named projects cannot see each other's messages; a revoked programme member loses room access; a stale memory revision cannot overwrite active state; a missing signing key fails closed; a worker restart doesn't lose canonical context; a malicious document cannot trigger an unapproved shell; a failed provider route does not silently send private data to a paid remote API.

## Support and incident reporting

Preserve a timestamp and correlation ID with minimal non-secret evidence. Rotate compromised keys and deny sessions at the issuer; verify RLS and audit events; do not reprint a private transcript into a public issue to demonstrate a leak. Security incidents must use a private report channel.

Sources: [ACP threat model](https://github.com/nyameko/agent-control-plane/blob/main/docs/11-threat-model.md), [identity/tenancy policy](https://github.com/nyameko/agent-control-plane/blob/main/docs/04-identity-tenancy-and-policy.md), [approval ADR](https://github.com/nyameko/agent-control-plane/blob/main/docs/adr/0005-human-approval-for-mutations.md) and [model routing contract](https://github.com/nyameko/agent-control-plane/blob/main/docs/06-model-and-compute-routing.md).