# M4g — browser-approved, no-JWT-on-SSH terminal baseline

This candidate extends the existing `acp` thin terminal client. With
`--browser-pair`, it contacts **Quantum Platform**, receives only an
anonymous short-lived pairing code plus an unguessable RAM-only proof, and
shows a URL to visit in the **researcher's own authenticated browser**.
Approval is explicit and limited to five minutes. Each requested command
is then sent to a narrow Quantum Platform gateway which rechecks expiry
and revocation and signs the ACP assertion server-side.

A source-level example (not an operator instruction to install on live
login nodes):

```text
acp --url https://quantum.example.invalid --browser-pair chats
acp --url https://quantum.example.invalid --browser-pair new "Research notes"
acp --url https://quantum.example.invalid --browser-pair show <owned-conversation-uuid>
acp --url https://quantum.example.invalid --browser-pair send <owned-conversation-uuid> "Hello"
acp --url https://quantum.example.invalid --browser-pair run <owned-run-uuid>
```

The SSH user **must not** supply their username, UID/GID or project ID
as identity proof. They do not receive an ACP signing key, user cookie,
long-lived API key or token stored in a file. This is an ephemeral
**single-command** pairing baseline, with each invocation asking the
human to approve; a later interaction/agent integration can reuse one
in-memory approved session within its short validity period.

`--token-stdin` remains a restricted backward-compatibility/development
mode; it is NOT the M4g trusted SSH pairing acceptance path.

The matching Quantum Platform PR adds an explicit model/migration,
rate-limited pairing initiation, browser approval and revoke controls,
and a per-request owner-only ACP proxy. Never run this on live SSH
nodes until separate operator approval, backend migration and security
review. It does not change sshd, PAM, shell configuration, Slurm, NFS,
or production Kubernetes. Unit tests use synthetic identities and
HTTP fixtures; the human operator performs the actual `nlisa` and
second-user client tests.

Source success is **not** end-to-end M4g completion. Revalidate
wrong-user denial, live revocation and three-surface canonical UUIDs
after approved promotion.
