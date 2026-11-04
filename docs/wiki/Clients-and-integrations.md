# Clients, Quantum Guide and integration boundaries

## Quantum Guide

The browser Guide should give every authorised research user one consistent entry point to canonical ACP context. The Quantum Platform backend, **not** the browser, creates scoped assertions for ACP. Authentication and programme membership remain Platform responsibilities.

## Notebook and editor clients

A Jupyter notebook, SSH terminal or editor may attach to an existing authorised conversation through approved brokered sessions. They should preserve stable project/conversation IDs and display the same message history. Never store a permanent agent signing key in notebook code, a home-directory config, browser localStorage or a GitHub repository.

## Terminal client status

The source contains a minimal `acp` terminal client. Its existing `--token-stdin` mode accepts a **pre-issued, short-lived trusted assertion**; it is **not** a complete login or identity broker. The safer portal-mediated device-style pairing flow in [ADR 0012](https://github.com/nyameko/agent-control-plane/blob/main/docs/adr/0012-portal-mediated-terminal-authentication.md) is a proposed review gate rather than a user-ready feature. Standard SSH login must not be silently converted into ACP identity.

Do not tell users to paste their browser session, JWT, WireGuard or private SSH key into a terminal command to make the client work. Until the trusted broker is implemented, use the authorised browser Guide or a sanctioned development fixture.

## Programme rooms

Programme-conversation data is separate from private user conversations. The Platform must check current programme membership and forward only authorised scopes; ACP independently enforces room boundaries. Revoked membership should immediately prevent future reads and writes, while retained canonical records follow policy.

See [client architecture](https://github.com/nyameko/agent-control-plane/blob/main/docs/08-clients-chat-telegram-discord.md), [terminal client source](https://github.com/nyameko/agent-control-plane/blob/main/src/agent_control_plane/terminal_client.py), and [Quantum Platform agent proxy](https://github.com/nyameko/quantum-platform/blob/main/apps/user-api/portal/agent_api.py).