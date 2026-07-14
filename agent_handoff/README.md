# Adaptive Remeshing Phase-Field Thesis - Codex Starter Pack

This starter pack converts the supplied thesis study guide, papers, and previous-project agent pattern into a thesis-specific Codex workspace policy.

The workspace is now set up as a full starter pipeline: structured literature notes, run/config contracts, dry-run validators, environment records, and handoff mirroring. Abaqus/HPC production runs remain blocked until the environment record is completed and HPC maintenance clears.

Current baseline status: the local user-subroutine smoke gate passed, the unchanged Molnar one-element technical gate passed, and the unchanged one-element ODB passed source-defined scientific checks under provisional numerical tolerances. Notched benchmark reproduction, remeshing, state transfer, and ABAQUSER integration are not validated yet.

## Included files

- `.agent.md` - primary Codex agent instructions, scientific boundaries, gates, run discipline, and handoff rules.
- `THESIS_PLAN.md` - work packages, deliverables, validation matrix, and proposed thesis structure.
- `WORKSPACE_STRUCTURE.md` - recommended repository layout and bootstrap workflow.
- `docs/EXPERIMENT_RECORD_TEMPLATE.md` - repeatable run/experiment record.
- `docs/methods/ENVIRONMENT.md` - Abaqus/HPC environment record required before production submission.
- `references/notes/` - structured paper notes plus equation, benchmark, and implementation-decision maps.
- `configs/` - starter run, benchmark, remeshing, state-transfer, and postprocessing contracts.
- `scripts/validation/` and `scripts/preprocessing/` - dependency-free starter checks.
- `scripts/sync_agent_handoff.py` - flat snapshot helper modeled on the previous project's mirror behavior.
- `agent_handoff/` - destination for the most recent operation's touched files.

## First use

1. Complete `docs/methods/ENVIRONMENT.md` with Abaqus, compiler, and HPC details.
2. Put original reference examples in a preserved `models/baseline_original/` area.
3. Fill the paper notes and maps in `references/notes/` from the original sources.
4. Run the dependency-free starter checks:

```bash
python scripts/validation/check_literature_index.py --dry-run
python scripts/validation/validate_manifest.py configs/run_manifest.example.json --dry-run
python scripts/preprocessing/check_deck_integrity.py --dry-run
```

5. Run the next original notched benchmark unchanged before modifying source code.
6. At the end of a Codex edit operation, mirror the touched files:

```bash
python scripts/sync_agent_handoff.py .agent.md THESIS_PLAN.md
```

## Important scope note

The attached Pandey-Kumar method is treated as MISESERI-driven pre-refinement for the first adaptive milestone. Evolving remeshing with state transfer is a mandatory thesis branch, but no online-remesh claim is allowed until controlled field transfer and fracture-relevant state transfer are verified. The agent file prevents Codex from presenting pre-refinement as online adaptivity or a successful Abaqus job as scientific validation.

## GitHub hygiene

The supplied PDFs and starter ZIP are ignored by Git. Track structured notes, configs, scripts, and small reproducibility artifacts; keep raw papers, Abaqus ODBs, scratch files, and large generated outputs local unless explicitly approved.
