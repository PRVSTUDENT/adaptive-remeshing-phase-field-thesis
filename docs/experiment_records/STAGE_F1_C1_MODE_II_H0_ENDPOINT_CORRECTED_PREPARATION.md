# Stage F1-C1 Mode-II H0 Endpoint-Corrected Serial Package Preparation Record

- **Stage**: Stage F (Mode-II mixed-mode benchmark)
- **Task ID**: `F1-C1-CORRECTED-H0-PREP`
- **Classification**: `stage_f_mode_ii_h0_endpoint_corrected_prepared_unauthorized`
- **Base Commit**: `71751047bbb05bdb1561e250c62a890989cdd349`
- **Endpoint Audit Revision**: `49d7d4f1a941a09fbfd3aca147fd612a0a9a6a4c`
- **Preparation Main Revision**: `e2e40b08fee23799da9518c118232af756610e0b`
- **Date**: 2026-07-27
- **Author**: gemini-antigravity

---

## 1. Provenance & Scientific Context

Following task `F1-C0-ENDPOINT-AUDIT` (`49d7d4f1a941a09fbfd3aca147fd612a0a9a6a4c`), job `1378942.mmaster02` failed the scientific acceptance gate ($U_1 = 0.0070\text{ mm}$ vs $0.0100\text{ mm}$ expected) because the amplitude table `Amp-2` specified an endpoint at step time $0.5$ while `Step-2` ended at step time $0.2$.

As audited in `ModeII_H0_serial.for`, the phase-field UEL/UMAT formulation is strictly rate-independent quasi-static elasticity with an irreversible phase-field history variable. Physical time $t$ serves purely as a load parameter. Changing `Amp-2` endpoint time from $0.5$ to $0.2$ changes only the numerical load schedule, preserving physical constitutive behavior.

---

## 2. Corrected Package & Execution Lane Architecture

- **Historical Failed Package (Frozen)**: `models/generated/mode_ii/h0_serial/`
- **Historical Failed Job ID**: `1378942.mmaster02`
- **Proposed Corrected Package Path**: `models/generated/mode_ii/h0_endpoint_corrected_serial/`
- **Proposed Corrected Execution Lane**: `runs/hpc/stage_f/mode_ii_h0_endpoint_corrected/`

---

## 3. Package Hashes & Byte-Identity Proof

| File | SHA-256 | Note |
|---|---|---|
| Historical Deck (`ModeII_H0_serial.inp`) | `32a25380767bbb0e9e76eb55b3bb7a97d78bb75c4f86c7e8585aa2032ce2d33b` | Frozen input |
| Historical Source (`ModeII_H0_serial.for`) | `5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c` | Frozen input |
| Corrected Deck (`ModeII_H0_endpoint_corrected_serial.inp`) | `c9160d50c944de7037a9f05dc1dbccfa9718f69b198bb48659f784bac220ddef` | Single line edit (`0.5` $\to$ `0.2`) |
| Corrected Source (`ModeII_H0_endpoint_corrected_serial.for`) | `5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c` | **100% byte-identical** |

---

## 4. Offline Qualification Results

- **Static Validation**: `stage_f_mode_ii_h0_endpoint_corrected_static_pass` (45 checks passed)
- **Local Pre-Solver Smoke**: `stage_f_mode_ii_h0_endpoint_corrected_pre_solver_smoke_pass`
- **Evidence Bundle Verification**: `stage_f_mode_ii_h0_endpoint_corrected_smoke_evidence_complete`
- **Submission Preflight**: `stage_f_mode_ii_h0_endpoint_corrected_preflight_preparation_pass`
- **Unit Tests**: All unit tests passed cleanly (including historical regression tests).

---

## 5. HPC Resource Plan & Guarded Wrappers

- **Datacheck Plan**: Queue `entry_imfdfkmq`, 1 CPU, 16 GB RAM, 00:30:00 walltime.
- **Solver Plan**: Queue `entry_imfdfkmq`, 1 CPU, 16 GB RAM, 04:00:00 walltime.
- **Guarded Wrappers**: `submit_mode_ii_h0_endpoint_corrected_datacheck.sh` & `submit_mode_ii_h0_endpoint_corrected_serial.sh`. Both default to preflight check and exit without `qsub` when authorization is missing or `ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_*_SUBMIT` flag is unset.

---

## 6. Execution Boundary

- **Jobs Executed**: `0`
- **Abaqus Runs**: `0`
- **PBS Submissions**: `0`
- **Datacheck Authorized**: `false`
- **Solver Authorized**: `false`
- **Next Task**: `F1-C2-DATACHECK-AUTH`
