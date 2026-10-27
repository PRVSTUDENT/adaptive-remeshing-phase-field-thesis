# Session Report: Turn 236 - Package 123 Technical Qualification and HPC Submission (Increment 86 Stationarity Bracket Test)

- **Task ID**: `F1597-CORRECT-PACKAGE72-STATE-TRANSFER`
- **Run ID**: `ad45bfdf-8bf8-4982-9cd9-db9b83e5121d`
- **Date**: 2026-10-27
- **Agent**: `gemini-antigravity`
- **Protocol Version**: 2

---

## 1. Executive Summary

Turn 236 completed the technical qualification and autonomous HPC submission of Package 123 (`M1_C4_INC86_HOLDOUT`, PBS Job `1417938.mmaster02`) under standing Mode-I authorization:

1. **Context & Hypothesis H4 Formulation**:
   - Following Turn 235 refutation of Hypothesis H3 (proving that prior C3 same-mesh donor re-equilibration does not restore C4 stationarity at Increment 88, matching Package 120 within 0.0017%), the research requires bracketing the exact transition boundary where fine-mesh crack-tip propagation triggers within-step nonstationarity.
   - Increment 79 (Package 115) converged to stationary equilibrium in 7 cycles.
   - Increment 85 (Package 119) converged to stationary equilibrium in 10 cycles ($\rho_d = 0.9972$, residual $-0.209\%$).
   - Increment 88 (Packages 120 and 122) reached the 15-cycle iteration cap, expanding in Cycles 12–15 ($\rho_d > 1.0$) due to localized crack propagation.
   - Package 123 tests intermediate state Increment 86 ($u_{\text{top}} = 0.00192951\,\text{mm}$) transferred from authentic C3 donor Package 76 ($RF_2 = 185.889602\,\text{N}$, $E_{\text{tot}} = 0.228665\,\text{mJ}$) to Candidate C4 (4,422 quads, 4,588 nodes) under the established 15-cycle AM-PDAS solver with bitwise frozen UEL (`AB0A5A71335ECB445E91EC13A645E280FF3310B561A5E78ABA4A49C8E81DD8AC`).
   - **Hypothesis H4**: The intermediate C3 state (Increment 86) admits a stationary C4 equilibrium within the established 15-cycle AM-PDAS budget, bracketing the physical-numerical stationarity transition between Increment 85 and Increment 88.

2. **Technical Qualification & Staging Verification**:
   - Verified existence and integrity of all 12 package files on local disk and remote scratch (`/scratch9/pr21vyci/runs/mode1_c4_inc86_holdout_diagnostic`).
   - Mesh topology verified: 4,422 quadrilateral elements, 4,588 nodes.
   - Material parameters verified: `[0.0075, 0.0027, 210.0, 0.3, 1.0E-07]`.
   - Executed full unit test suite `tests/unit/test_mode1_f1597_package123_qualification.py`: 7/7 checks passed.
   - Remote interactive datacheck executed with Abaqus 2023: `ANALYSIS DATACHECK COMPLETE` with 0 errors (CPU time 0.14 s, walltime 1 s).

3. **Guarded Autonomous HPC Submission**:
   - Invoked `scripts/hpc/Invoke-Mode1Execution.ps1` under standing Mode-I authorization.
   - Technical preflight passed: `datachecks=PASS_BOTH`, 0 active jobs on cluster, dual-channel notifications verified.
   - Submitted as PBS Job **`1417938.mmaster02`** to `entry_imfdfkmq` and transitioned to running status `R` in `normal_imfdfkmq` on single-rank serial configuration (1 CPU, 16 GB, 8h).
   - Recorded once-only reservation in `project_coordination/HPC_JOB_LEDGER.csv`.

---

## 2. Deliverables and Artifact Hashes

1. Preparation Checkpoint Artifact: `results/validation/preparation-ad45bfdf-8bf8-4982-9cd9-db9b83e5121d.json`
2. Package Manifest: `models/pandey_kumar_mode1/123_c4_inc86_holdout_diagnostic/PACKAGE_MANIFEST.json` (`71BBA066568EC2C8F9E7E0886F3F53CE00FDBD39231481CA546BA46F1018BAD3`)
3. Authorization & Recipe: `models/pandey_kumar_mode1/123_c4_inc86_holdout_diagnostic/M1_C4_INC86_HOLDOUT_AUTHORIZATION.json` (`C5C5DCB55EE91700015F5411AF07AE346F88875C3E5995514C6CF1BEFAB1023B`)
4. Model Input Deck: `models/pandey_kumar_mode1/123_c4_inc86_holdout_diagnostic/M1_C4_INC86_HOLDOUT.inp` (`474D50436EAE655D5068E184401E171DCC77503C70D41E5A443591519793C0A6`)
5. Bitwise Frozen UEL: `models/pandey_kumar_mode1/123_c4_inc86_holdout_diagnostic/f42_unified_12dof_active_set_uel.for` (`AB0A5A71335ECB445E91EC13A645E280FF3310B561A5E78ABA4A49C8E81DD8AC`)
6. Submission Script: `models/pandey_kumar_mode1/123_c4_inc86_holdout_diagnostic/submit_M1_C4_INC86_HOLDOUT.pbs` (`93A2F4262C5E06EA55C3CA22114DD956C0A1F3A8E4075B49AFFEDBA808C8290D`)
7. Driver Script: `models/pandey_kumar_mode1/123_c4_inc86_holdout_diagnostic/driver_c4_inc86_holdout.py` (`BA6795BC6A6E5B3546C50ADD6BD8412ED886A73484603BE47B639E18208DFA75`)
8. Qualification Test Suite: `tests/unit/test_mode1_f1597_package123_qualification.py` (`FE8A368C89C868DB8D2A2A2A7B7BE7863AB00CA53780B0513AAFCBD6015BB480`)
9. Hash Computation Utility: `scripts/validation/compute_turn236_hashes.py`

---

## 3. HPC Job Ledger Reconciliation

| PBS Job ID | Job Name | Queue | Resources | State | Outcome |
| :---: | :---: | :---: | :---: | :---: | :---: |
| `1417938.mmaster02` | `M1_C4_INC86_HOLDOUT` | `entry_imfdfkmq` $\to$ `normal_imfdfkmq` | 1 CPU, 16 GB, 8h | Running (`R`) | `SUBMITTED_AWAITING_RESULT` |

Accounting integrity preserved: zero duplicate submissions, once-only accounting upheld.

---

## 4. Governance & Next Steps

- Gate status: **`STAGE_C1_2_STEP2_ENERGY_GATE_FAILED__PACKAGE123_HOLDOUT_SUBMITTED`** retained.
- Autonomous C5 remeshing remains strictly blocked.
- Production UEL remains 100% bitwise frozen.
- Upon solver completion of Job `1417938.mmaster02`: retrieve terminal deliverables (`c4_inc86_holdout_summary.json`), evaluate stationarity metrics ($d_{\max}$, $RF_2$, $E_{\text{tot}}$, active set, $\rho_d$), and assess Hypothesis H4.

Finished

## Verified Research Preparation Finding

Package 123 qualified and submitted to cluster queue (PBS Job 1417938.mmaster02, 1 CPU, 16 GB, 8h walltime, entry_imfdfkmq -> normal_imfdfkmq) under standing Mode-I authorization; tests Hypothesis H4 (Increment 86 intermediate holdout stationarity bracket between Increment 85 and Increment 88).

Evidence: results/validation/preparation-ad45bfdf-8bf8-4982-9cd9-db9b83e5121d.json

Status: PREPARATION_COMPLETE

Turn complete. No unqualified HPC job submitted.

Finished
