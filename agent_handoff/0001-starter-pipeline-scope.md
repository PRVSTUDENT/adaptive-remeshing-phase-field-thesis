# Decision 0001: Starter Pipeline Scope

Date: 2026-07-14

## Decision

Build a full starter pipeline before numerical implementation. The pipeline includes workspace structure, literature maps, run/config schemas, dry-run validators, deck-integrity checks, postprocessing contracts, and handoff synchronization.

## Thesis Scope

- MISESERI-driven pre-refinement is the first reproducible adaptive milestone.
- Evolving remeshing with state transfer is a mandatory thesis branch.
- No online/evolving remeshing claim is allowed until state transfer is verified on controlled fields and then on a fracture-relevant case.
- HPC is the intended Abaqus runtime, but current maintenance blocks production submissions.

## Consequences

- The first implementation pass may add scripts and config templates, but not modify scientific UEL/UMAT behavior.
- Tolerances are provisional until supervisor-approved values exist.
- A completed environment record is required before HPC submission.
