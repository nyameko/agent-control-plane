# ADR-0002: The control plane is not a resource scheduler

- Status: accepted
- Date: 2026-09-17

## Context

Agent planning needs to choose appropriate CPU/GPU/QPU capability, but Kubernetes, Slurm and
OpenStack already provide scheduling and lifecycle guarantees.

## Decision

The control plane selects a logical execution class and submits a bounded request through an
adapter. Kubernetes, Slurm or OpenStack resolves physical placement.

Model inference placement is a separate logical decision from workload execution placement.

## Consequences

The project avoids reimplementing backfill, quotas, node health, reconciliation and cloud
provisioning. It must maintain adapters and correlate external job IDs.
