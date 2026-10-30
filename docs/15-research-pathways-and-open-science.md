# Research pathways, PI studio and open-science federation (cross-repository RFC)

Status: **proposal / draft for review**. This is not an M4a scope change or a deployment approval.

## Product ethos

> A student in Cape Town, Nairobi, Lagos or Kigali should be able to ask to learn quantum error correction and progress from prerequisites to decoding, benchmarking, a published-paper reproduction and a research question. An experienced researcher should be able to review, edit and publish specialist pathways grounded in their verified work.

Do **not** respond to a new learner by dumping 87 notebooks on them. Ask for the learning goal, invite an optional self-assessment, propose an editable route through versioned lessons, offer the first executable lesson, and persist progress with evidence. A learner may skip, revisit, fork or take a different path. An LLM's confidence does not determine mastery or scientific correctness.

## Repository authority and research pathway (capturing the cross-repository architecture)

| Component | Authoritative responsibility |
| --- | --- |
| `quantum-platform` | Human identity, PI/programme roles, entitlements, researcher UI, learning catalogue/enrolment, progress presentation, publication permissions |
| `agent-control-plane` | AgentPrincipal-scoped canonical projects, conversations, memory, skills, tasks/runs, agent-assisted draft plans, approvals and context across clients |
| `quantum-workflows` | Versioned curricula, notebook source, assessment specifications, scientific runners, results and reproducibility/provenance |
| `infra-hpc-qc-k8s` | Infrastructure and GitOps, NFS, JupyterHub deployment, CPU/GPU/Slurm/QPU access paths, telemetry and security |
| Slurm / QPU provider | Actual compute scheduling and execution authority |

Flow: authenticated researcher -> selected learning/research goal -> authorised ACP draft plan -> optional instructor/PI approval -> immutable `quantum-workflows` curriculum revision -> platform course/workbench -> controlled scientific execution -> graded/reviewed evidence and progress -> next recommendation.

ACP persists *agent* task and conversation state, and stores references to learning records; it must not become a second scientific result store, a second portal enrolment database or a scheduler.

## M4a–M4g versus researcher releases R1–R5

Two **orthogonal** roadmaps, not a renaming. Dependencies refer to capabilities, not a requirement to wait until all of M4 ships.

| Product release | Outcome | M4 relationship |
| --- | --- | --- |
| R1 Researcher workbench | Approved user opens, executes, saves and resumes a versioned teaching notebook | Runs independently of M4a; uses existing Quantum Platform/Jupyter/NFS foundations |
| R2 Persistent research assistant | Research project and chat resume across browser, Jupyter and worker loss | Depends on *verified* M4a; enrich with M4b memory and M4c projects; M4f UI |
| R3 Curated learning paths | Prerequisite DAG, progress/evidence, grounded reading, versioned curriculum | Built with M4b/c/d and M4f; a deterministic non-agent catalogue can ship sooner |
| R4 PI research studio | Verified bibliography, editable/reviewable learning track, cohort release | Extends M4c/d/f; optional M4e runtime continuity, never canonical authority |
| R5 Research-grade execution | CPU/GPU/QPU scientific provenance and reproductions at fixed accuracy | Cross-repository scientific integration; M4g adds terminal access, not prerequisite for notebook execution |

M4e (persistent Hermes profile) remains runtime convenience, never source-of-truth. M4g (SSH client) is another client, not a prerequisite for R1–R4. **Do not declare M4a complete without the destructive PostgreSQL continuity evidence and automated conformance test defined in `docs/M4-PERSISTENT-AGENTS.md`.** LiteLLM and Paperclip are not closeout criteria.

## Pathway semantics and adaptability

- Content is a **versioned directed acyclic graph** of prerequisites, learning outcomes, notebook/lab IDs, evidence and optional branches; not a rigid linear list.
- A published course references immutable `quantum-workflows` Git commit SHA, environment/digest, validated assessment and bibliography; new releases never silently rewrite past student work.
- Distinguish `draft`, `scientific-review`, `approved`, `published`, `deprecated`. An agent may propose and test a draft, but never impersonate a PI or approve its own work.
- Student progress is a platform-owned evidence ledger linked to an approved course revision and execution manifest, not a claim extracted from a chat.
- For PI onboarding, seek consent to review **verified ORCID/publications**, allow manual author disambiguation, citation correction, private drafts and opt-out. Do not infer competence, assign personal rankings or publish an endorsement.
- Literature recommendations retain DOI/URL, retrieval date, explicit source identity, uncertainties, editions and human-reviewed citations.
- A researcher may build a private path without a PI; group/course publication needs an authorised reviewer.
- Minimise personal information and scope retrieval by principal/programme; isolate grants, licences and embargoed research outputs.

## Minimal contracts (proposed)

```text
PathwayRef { id, semver, workflow_repo, commit_sha, status, prerequisites[], modules[] }
ModuleRef  { id, outcomes[], notebook_path, environment_ref, assessment_ref, references[] }
LearningProgressRef { principal_uuid, pathway_revision, module_id, evidence_ref, review_state }
AgentPlanRef { principal_uuid, project_uuid, conversation_uuid, proposed_pathway_revision, provenance[] }
```

Cross-service joins use the immutable AgentPrincipal UUID and explicitly authorised programme membership; keep POSIX UID/GID for execution only. All references are typed, validated, access-controlled and auditable. Details must be settled by contracts/ADRs before implementing an API.

## Open science, African ownership and interoperability

Design for alignment with **EOSC** (European Open Science Cloud), **AOSP** (African Open Science Platform; sometimes informally referred to as African OSC), and **GOSC** (Global Open Science Cloud / CODATA), **without claiming membership or formal federation**.

- Open, reusable content with explicit licence and citation; include ORCID, DOI, ROR where appropriate.
- FAIR machine-actionable dataset, software, notebook and execution manifests, persistent identifiers, provenance, schemas and controlled vocabularies; support export/import rather than proprietary LMS lock-in.
- Consider Research Object Crate (RO-Crate), W3C PROV, CodeMeta, DataCite and OIDC/OAuth2 federation where appropriate, **subject to architecture/security review**, not mandatory in R1.
- Identity federation must never grant HPC/QPU compute entitlements by itself.
- Support institutional/regional data sovereignty, embargoes, culturally appropriate governance, Africa-led curriculum authorship, multilingual/local adaptations and offline-first reproducibility where feasible.
- Future integration: service catalogue description -> federated discovery -> policy-aware data/workflow exchange -> institutional identity/entitlement federation -> bilateral pilot with an actual partner.

Background: https://research-and-innovation.ec.europa.eu/strategy/strategy-research-and-innovation/our-digital-future/open-science/european-open-science-cloud-eosc_en ; https://www.nrf.ac.za/wp-content/uploads/2024/08/AOSP-Brochure_1pager.pdf ; https://codata.org/initiatives/making-data-work/global-open-science-cloud/

## Implementation sequence and release gates

1. **M4a**: observe and record the destructive continuity drill across supported clients, worker loss, API restart and second-user denial, then establish automated conformance. No speculative closeout.
2. **R1**: approved researcher logs in, opens `labs/01-intro-quantum-computing/Intro_QC_Demo.ipynb` via JupyterHub, executes it, stores a result/manifest in the shared persistent home, loses/restarts the workbench and returns to unchanged results. Require independent verification of identity isolation.
3. **R3 seed**: `quantum-workflows` publishes one approved, testable, credential-free four-week QEC route. ACP may suggest optional personalised ordering; platform persists enrolment and evidence.
4. **R4**: PI-confirmed profile, reviewed bibliography and draft/edit/approve/publish course lifecycle with audit.
5. **R5**: resource estimates, Slurm/GPU/QPU adapters, checksums, independently reproduced paper figure, evidence-level labelling.

Non-goals now: moving notebook code into ACP; fabricating course completion; deploying 87 unreviewed lessons as a mandatory default; blanket PR merge; privileged/prod changes without human approval.

## Next review questions

Who is the canonical authorisation authority for course approvals? What is the smallest progress-evidence schema that survives a notebook revision? Which FAIR research objects should be exportable in R1 versus later federation? Which module should become the first expert-reviewed QEC reference course?
