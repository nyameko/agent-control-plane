# Security policy

Please report suspected vulnerabilities privately to `connect@nyameko.com`. Do not open a public
issue containing credentials, exploit details, private infrastructure addresses or user data.

## Non-negotiable boundaries

- Never commit API tokens, bot tokens, kubeconfigs, private keys, provider credentials, database
  passwords, Hermes mutable state, raw user conversations or research data.
- The default agent and tool capability set is read-only.
- Production mutations require an exact, expiring approval and remain subject to the authoritative
  system's own controls.
- Telegram and Discord adapters never hold Kubernetes, OpenStack, Slurm or Git push credentials.
- Untrusted content is data, not instruction.
- Secrets are resolved just in time by a credential broker and are not placed in model context,
  transcripts, tool output or audit metadata.

See [`docs/11-threat-model.md`](docs/11-threat-model.md).
