# M4g: interactive ACP view inside an ordinary Herdr terminal pane

**Source-only candidate.** This does not install ACP on the login nodes,
change any shell, create an ACP identity, deploy a model or change PostgreSQL.

## Why

Herdr already owns per-user panes and detach/reattach. ACP owns canonical
conversations and permissions. Previously each separate `acp --browser-pair
chats` invocation prompted an additional approval. This small `session`
subcommand keeps **one short-lived portal approval** in the memory of a
single terminal process, without writing keys or history to the filesystem.
It can run inside any Herdr pane, tmux pane or ordinary SSH shell.

Once the approved **existing** ACP terminal client is installed, from the
researcher's SSH session on an authorized login node:

```bash
herdr
# Inside a normal Herdr terminal pane:
acp --url https://quantum.nyameko.com --browser-pair session
```

Approve the displayed code via
`https://quantum.nyameko.com/agent/pair/`. Within the connected pane:

```text
acp> chats
acp> show <existing-conversation-uuid>
acp> send <existing-conversation-uuid> Continue this research topic.
acp> projects
acp> run <run-uuid>
acp> help
acp> quit
```

The command `connect` starts a fresh **explicit browser approval**, not
an automatic renewal. The current QP pairing backend enforces a
**300-second absolute expiry**, even if Herdr itself remains attached for
days. Revoked, expired or unauthorized replies are fail-closed and discard
the process's headers. The CLI cannot improve that TTL on its own.
Do not store approvals in Herdr session metadata or environment variables.
Logout in the browser is not equivalent to revoking an already-approved
terminal pairing: explicitly revoke it in the portal.

Herdr detach/reattach keeps the running `acp session` process live.
If the server/pane restarts, the process and approval are lost; the layout
may return, but a new browser approval is needed. The transcript is
reloaded from ACP when an authorized `show` request is made. Herdr
screen history must not be treated as a canonical ACP data store.

This is a **first usable slice**, not the eventual seamless "Recent chats"
Herdr plugin or backend-to-Herdr status bridge in
[ACP #88](https://github.com/nyameko/agent-control-plane/issues/88).
Herdr's upstream plugin and socket API should be the extension point
if a persistent navigation panel proves valuable after human usage;
do not build a custom TUI framework.

## Provisioning constraints

Ansible's `research_terminal_clients_acp_cli_enabled` defaults to false.
The role requires a separately approved Python 3.13/3.14 on login nodes
and installs this existing package in an isolated venv. The commit pin
must be updated **only after source PR review**. Do not install `pip`
packages into Rocky's system Python. No entry in `~/.bashrc`,
`~/.bash_profile`, `/etc/profile` or Slurm service configuration is
needed for an interactive ACP pane.

## Acceptance

- Human browser approves one pairing; `chats`, `show`, `send` all work
  on the original C1 UUID without repeated approvals while still valid.
- Correct owner/tenant response, real model completion/run ID and same UUID
  in Quantum Guide/Jupyter/SSH.
- Revoked pairing blocks next command and no automatic re-pair occurs.
- Malformed command is not interpreted as shell and sends no HTTP request.
- After server expiry, only the explicit `connect` and fresh human approval
  can resume ACP calls; original Herdr shell/session remains usable.
- Never log tokens, session proofs, private messages or full transcripts
  to CI or GitHub. Human-only live `nlisa` acceptance.
