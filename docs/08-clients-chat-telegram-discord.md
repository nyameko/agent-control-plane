# 8. Clients, persistent chat, Telegram and Discord

## 8.1 One conversation service, many views

The persistent assistant should feel continuous across:

- `quantum.nyameko.com` and the authenticated user portal;
- the JupyterHub landing page;
- each spawned JupyterLab session;
- Spacemacs/gptel;
- Telegram and Discord where the user has linked them.

Clients do not synchronise transcripts with one another. They connect to the same canonical
conversation API and subscribe to the same ordered run events.

## 8.2 Web chat

Add a shared Astro component/package in `quantum-platform`:

- collapsible persistent side panel on the portal;
- conversation picker, search, rename, archive and export;
- streaming answer/tool timeline;
- model/agent mode selector expressed as logical presets;
- attachment and research/workflow context controls;
- clear pending approval cards and deep links;
- task/job/result links;
- privacy, sharing and retention controls.

The browser uses the existing same-origin Django session. Django exchanges it for a short-lived,
audience-limited control-plane token containing subject, tenant/programme roles and strong-auth
time. The browser never receives service credentials.

## 8.3 JupyterHub and JupyterLab

Use the same SSO identity and conversation API. A JupyterLab extension or server proxy can supply
explicit context references:

```text
notebook path + content digest
selected cell/range
kernel/environment metadata
Slurm allocation/job ID
workflow/result manifest URI
```

Do not upload an entire home directory or notebook automatically. Context is user-selected or
policy-approved and recorded with the message.

The chat can survive the notebook pod because its canonical history is in PostgreSQL; notebook
files survive according to the user's Jupyter/Cinder storage policy.

## 8.4 Spacemacs/gptel

Spacemacs remains the advanced cockpit. Expose separate presets:

- direct low-latency model endpoint for simple completion/explanation;
- control-plane/Hermes agent endpoint for tool-using tasks;
- `@infra`, `@research`, `@quantum`, `@review` logical modes;
- local Ollama fallback.

Credentials live in `auth-source`, not `config.el`. Presets select logical pools and agents; the
server resolves physical models. gptel conversations may bind to a platform `conversation_id` so
the web UI can resume them. Editor buffer contents are sent only when the user selects them.

## 8.5 Telegram and Discord are liaison adapters

Each bot runs as a separate, unprivileged service:

```text
Telegram/Discord event
        ↓
signature/platform validation + rate limit
        ↓
normalised channel envelope
        ↓
linked platform subject + tenant policy
        ↓
conversation/task API
        ↓
sanitised streamed/final response
```

The adapter holds only its bot token and a short-lived control-plane service credential. It has no
kubeconfig, OpenStack credential, Slurm SSH key or Git push token.

## 8.6 Account linking

1. The authenticated user requests a short-lived one-time linking code in `quantum-platform`.
2. The user sends that code to the bot/DM.
3. The adapter redeems it once and creates a channel binding to the immutable subject.
4. The portal shows the binding and allows revocation.

Never identify a user merely by matching email, display name or Discord nickname.

## 8.7 Channel policy

| Surface | Default scope | Mutation approval |
| --- | --- | --- |
| portal | personal/programme conversations | allowed through strong-auth approval UI |
| Jupyter | notebook/research context | portal approval link |
| gptel | selected buffers/repos | portal approval link or local development policy |
| Telegram DM | status, questions, research digest, read-only tasks | never high-risk in chat; deep-link to portal |
| Discord DM | same as Telegram | deep-link to portal |
| Discord project channel | explicitly bound programme context, mention-triggered | no privileged approval |

In public/group channels, default to minimal responses and never disclose private task details,
security telemetry, quotas, collaborator suggestions or cross-tenant memories.

## 8.8 Discord versus Telegram roles

Discord is useful for persistent topic/project channels, educational communities and multi-agent
observatories. Telegram is useful for personal notifications, concise commands and urgent status.
Neither should become the database. Channel history is a presentation record; canonical task and
conversation state stays in the control plane.

## 8.9 Notification discipline

Notify on outcomes that need attention: approval requested, long job completed/failed, security
incident summary or scheduled research digest. Avoid mirroring every tool event into chat. Users
need per-channel quiet hours, digesting and severity thresholds.
