# Molnar Gate A3 — Supervisor Decisions 1A and 2B

Status: `recorded_from_supervisor_response`  
Recorded: 2026-07-21  
Basis: supervisor operating policy after RF–U h-convergence review  
Related evidence: `docs/decisions/MOLNAR_LC015_H_CONVERGENCE_SCIENTIFIC_DECISION.md`  
Analysis commit: `db4c1fadfb3a4f7b33b6b653c261e6da90036c48`

This file freezes the supervisor’s Decision **1A** and Decision **2B**. It supersedes the “awaiting supervisor” wording for those two questions only. It does **not** claim full Gate A3 closure, full-curve mesh independence, or crack-path convergence.

---

## Decision 1A — Mesh roles for RF–U validation and production

| Role | Mesh | Local \(h\) | Policy |
|---|---|---:|---|
| **Uniform validation reference** | **H2-PUB** | 0.001 mm | Fine RF–U validation reference; **not** the default production mesh |
| **Production / thesis / report mesh** | **H1** | 0.0025 mm | Practical final-simulation mesh; closely reproduces H2 peak/pre-peak at lower cost |
| **Development / testing / debug mesh** | **H0** | ≈ 0.00494 mm | Fast testing only; use only when the specific test shows no mesh-related issue |

### Interpretation

- H2-PUB is accepted as the fine RF–U validation reference.
- H1 is the practical production mesh for thesis/report final simulations.
- H0 is the development mesh for preprocessing, smoke tests, and first MISESERI implementation trials.
- H0 is **not** an RF–U validation or report reference.

---

## Decision 2B — Contour / crack-path requirement

| Item | Policy |
|---|---|
| Matched-state contour / crack-path convergence | **Deferred** |
| Blocks Gate A3 RF–U component | **No** |
| Blocks MISESERI Stage C preparation | **No** |
| Blocks full scientific closure of crack-path claims | **Yes** (path reproducibility remains a planned later task) |

### Interpretation

- Contour convergence is deferred and does **not** block preparation of the MISESERI workflow.
- Crack-path reproducibility is a deferred planned task, not a present acceptance gate for Stage C preparation.
- No crack-path mesh independence claim is authorized by this decision.

---

## Gate A3 status after 1A + 2B

```text
Gate A3: conditionally accepted for RF–U validation
Uniform validation reference: H2-PUB
Production/report mesh: H1
Development/testing mesh: H0
Crack-path reproducibility: deferred planned task
External/analytical validation: parallel lower-priority task
```

Internal status tags:

```text
gate_a3_conditionally_accepted_rf_u
contour_validation_deferred
stage_c_miseseri_preparation_authorized
```

### What is accepted

- RF–U peak and pre-peak h-convergence support for selecting H2-PUB as the fine validation reference.
- Use of H1 as the production comparison mesh for Stage C (MISESERI-refined vs uniform H1).
- Use of H0 for automated preprocessing development and the first MISESERI implementation campaign **preparation**.

### What remains open / limited

- Full unconditional Gate A3 closure for every historical Stage A claim is not asserted.
- Post-peak mesh dependence remains a documented limitation (~20% post-peak NRMSE H1→H2).
- Crack-path / matched-state SDV15 convergence is not assessed.
- Supervisor-approved numeric tolerances for absolute paper-curve comparison remain separate if still required for other Stage A narratives.
- External literature and analytical validation are parallel, lower-priority tasks.

---

## Stage C authorization boundary

```text
Stage C MISESERI preparation: AUTHORIZED
Stage C HPC submission (qsub / CAE / Abaqus solve): NOT AUTHORIZED until explicit new approval
```

Authorized now:

1. Record decisions 1A and 2B (this file).
2. Freeze mesh roles and existing H0/H1/H2 results/hashes.
3. Build the automated H0/H1 preprocessing pipeline.
4. Prepare the five-job MISESERI campaign as plan and scripts (no submission).
5. Prepare deferred crack-path tooling design and secondary validation matrices without execution.

Not authorized without a further explicit approval:

- Any new PBS `qsub`
- Any new Abaqus solver or CAE remeshing job
- Multicore qualification campaign
- `errorTarget` retuning after seeing final crack results
- State-transfer / online evolving remesh claims

---

## Mesh-use policy (frozen)

| Context | Mesh |
|---|---|
| Fast testing and debugging | **H0** |
| Final simulations for thesis/report | **H1** |
| Fine convergence evidence only | **H2-PUB** |
| Stage C primary comparison reference | **uniform H1** |
| Stage C secondary fine check (optional) | **H2-PUB** |
| First MISESERI implementation trials | **H0** → refine toward H1 local resolution |

---

## Traceability

| Artifact | Path |
|---|---|
| Scientific RF–U decision | `docs/decisions/MOLNAR_LC015_H_CONVERGENCE_SCIENTIFIC_DECISION.md` |
| Result and source freeze | `docs/decisions/MOLNAR_MESH_ROLE_AND_RESULT_FREEZE.md` |
| Mesh role policy (ops) | `docs/decisions/MESH_USE_POLICY.md` |
| Stage C preparation plan | `docs/studies/STAGE_C_MISESERI_PREPARATION_PLAN.md` |
| Five-job campaign (plan only) | `docs/studies/STAGE_C_FIVE_JOB_CAMPAIGN_PLAN.md` |
| Status matrix | `docs/decisions/MOLNAR_GATE_A3_STATUS_MATRIX.md` |
