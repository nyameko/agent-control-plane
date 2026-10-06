# 8. Clients, chat and external channels

## 8.1 One canonical conversation, many surfaces

The same conversation should be usable from:

- Quantum Platform web;
- Jupyter/JupyterLab;
- SSH/TUI;
- Spacemacs/gptel;
- future desktop/mobile/API clients;
- linked Telegram/Discord channels where policy allows.

Clients do not synchronise separate histories. They attach to the same ACP project/conversation identifiers.

~~~text
Quantum Platform ─┐
Jupyter ──────────┤
SSH/TUI ──────────┼──> ACP canonical conversation
gptel ────────────┤
API ──────────────┘
~~~

## 8.2 Client state is disposable

Closing a browser, deleting a notebook Pod or exiting an SSH session must not delete canonical state.

Clients may cache UI/session information locally. They must be able to recreate their view from ACP APIs.

## 8.3 Quantum Platform web

Quantum Platform is the primary product surface.

The future Guide/co-scientist can provide:

- project/conversation picker;
- streamed assistant output;
- task/run history;
- attachment/artifact references;
- model/agent logical presets;
- workflow/run links;
- approval cards;
- privacy/retention controls.

The browser authenticates to Quantum Platform. Server-side components issue scoped short-lived assertions to ACP.

Do not put ACP signing keys or privileged runtime tokens in browser JavaScript/localStorage.

## 8.4 Jupyter

The Jupyter Pod is a low-cost workbench client, not the source of agent truth.

A Jupyter extension or notebook client can:

- list projects/conversations;
- attach to an existing conversation;
- send messages;
- inspect runs;
- submit bounded workflows.

Notebook culling must not affect canonical conversation state.

## 8.5 SSH/TUI

M4g makes the terminal a first-class ACP client.

It should support conversation/project operations while always preserving access to the normal Unix shell.

Terminal tooling such as Herdr can improve local/remote agent supervision but does not define identity or history.

## 8.6 gptel/editor clients

gptel/Spacemacs should bind editor buffers/presets to ACP conversation IDs.

The editor may also expose direct-model sessions for disposable work. Those should be visually/semantically distinct from ACP-backed durable conversations.

Credentials belong in secure local credential mechanisms such as auth-source, not checked-in configuration.

## 8.7 External messaging

Telegram/Discord should be channel adapters into ACP, never parallel agent systems.

Account linking must be explicit and authenticated.

A display name, handle or server role is not sufficient proof of Quantum Platform identity.

## 8.8 Channel policy

External channels need:

- account linking/revocation;
- tenant/project scope;
- replay protection;
- rate limits;
- quiet hours;
- sensitivity/redaction policy;
- capability restrictions.

High-impact approvals should deep-link back to a trusted authenticated platform surface.

## 8.9 Notifications

Notify for things that need attention:

- approval requested;
- long job completed/failed;
- security/operational incident;
- scheduled research digest;
- collaborator/research candidate where authorised.

Do not mirror every internal tool event into user chat.
