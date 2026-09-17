# Contributing

This repository defines contracts used across infrastructure, platform and scientific workflow
projects. Treat contract changes as architecture changes rather than local refactors.

## Workflow

1. Open an issue or architectural discussion for a new capability or cross-repository contract.
2. Create a short-lived feature branch from `main`.
3. Add or update tests for policy and routing changes.
4. Update the relevant JSON Schema and documentation together.
5. Run `make check`.
6. Submit a pull request; do not let an agent merge its own infrastructure-affecting proposal.

## Compatibility

- Additive fields may remain within `contracts/v1` when clients can safely ignore them.
- Renames, removals or semantic changes require a new contract version.
- Runtime- or vendor-specific fields belong below namespaced `extensions`, not in the portable core.

## Security-sensitive changes

Changes to capabilities, approval policy, channel linking, credential access, tool execution,
sandbox escape boundaries or administrator scope require an explicit security review.
