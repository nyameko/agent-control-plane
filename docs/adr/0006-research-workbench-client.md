# ADR 0006 — Research workbench is a client, not the compute authority

Status: accepted direction.

## Context

Researchers spend most notebook time reading, editing, plotting modest data, preparing workloads and interacting with agents. Reserving large CPU/GPU resources for that entire period wastes scarce capacity.

## Decision

The normal Jupyter session is a low-cost KubeSpawner workbench. Agent Control Plane exposes durable conversation/task services to that workbench, the portal and SSH/TUI clients.

Heavy CPU/GPU/QPU execution is requested through bounded execution/workflow contracts. The agent may assist with target selection and submission, but Slurm/provider policy remains authoritative.

BatchSpawner remains a supported exception for interactive HPC kernels.

## State

Canonical conversation and memory remain platform-owned durable data. A Jupyter pod or harness PVC may cache runtime state but cannot be the sole copy.

## Security

Notebook pods receive only user-scoped delegated capabilities. They do not receive broad scheduler credentials, platform signing keys, administrator tokens or provider secrets.

## Consequence

A notebook can disappear while its authorized scientific job, QPU queue entry or agent conversation continues. This is required for the future quantum-workflows staged execution model.
