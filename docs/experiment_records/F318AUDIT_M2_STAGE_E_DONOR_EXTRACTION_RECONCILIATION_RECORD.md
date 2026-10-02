# Mode-II Stage-E Donor Trajectory Extraction Provenance, Frame/Increment Reconciliation, and Bit-for-Bit Parity Record

**Task ID**: `F318AUDIT-M2-STAGE-E-DONOR-EXTRACTION-PROVENANCE-AND-PARITY-RECONCILIATION1`  
**Date**: 19 August 2026  
**Status**: `DISCREPANCY_RESOLVED / PROVENANCE_RECONCILED / 100PCT_CANONICAL_PARITY_PROVED / BOTH_PATH_NEUTRAL_CONFIRMED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Resolution of Extraction Discrepancy & Trajectory Conventions

```text
======================================================================================================================================================================
Audit Topic                          Earlier Inconsistent Report        Reconciled Authoritative Evidence      Root Cause & Deterministic Resolution
-----------------------------------  ---------------------------------  -------------------------------------  -------------------------------------------------------
Terminal Reaction Force (RF1)        0.00350319 kN                      0.00677165 kN (0.006772 kN)            EXTRACTION_ERROR in previous script table generator;
                                                                                                               actual RP Node 99999 RF1 in ODB is 0.00677165 kN.
-----------------------------------  ---------------------------------  -------------------------------------  -------------------------------------------------------
Frame vs Increment Count             440 inc / 440 frames               439 increments / 440 ODB frames        FRAME_CONVENTION_CLARIFIED: Frame 0 is initial state
                                                                                                               (t=0.0), followed by 439 converged increments.
-----------------------------------  ---------------------------------  -------------------------------------  -------------------------------------------------------
Handoff State (U1 = 0.01051289 mm)   Frame 17, RF1 = 0.12591584 kN      Frame 17, RF1 = 0.12591584 kN          CONFIRMED EXACT MATCH across all 4 donor runs.
Peak State (U1 = 0.01257539 mm)      Frame 20, RF1 = 0.144737 kN        Frame 20, RF1 = 0.14473675 kN          CONFIRMED EXACT MATCH across all 4 donor runs.
======================================================================================================================================================================
```

---

## 2. Canonical Donor Lineage Comparison Matrix (All 5 Jobs)

Extracted using the unified canonical RP pipeline on Node 99999 (`N_RP`), component `RF1` (positive in $+X$ loading direction):

```text
======================================================================================================================================================================
Job ID            Job Description / Label        Step Name  Incs  Frames  Handoff U1 (mm) / RF1 (kN)  Peak U1 (mm) / RF1 (kN)     Terminal U1 (mm) / RF1 (kN)  Max d (Term)
----------------  -----------------------------  ---------  ----  ------  --------------------------  --------------------------  ---------------------------  ------------
1390447.mmaster02 Donor Minimal Continuation     ShearStep  439   440     0.01051289 / 0.12591584     0.01257539 / 0.14473675     0.05000000 / 0.00677165      1.00000024
1390552.mmaster02 Donor Target Baselines (alt)   ShearStep  134   135     0.01051289 / 0.12591584     0.01351289 / 0.14938235     0.05000000 / 0.00893873      1.00000024
1390876.mmaster02 Donor Minimal dt_min Baseline  ShearStep  439   440     0.01051289 / 0.12591584     0.01257539 / 0.14473675     0.05000000 / 0.00677165      1.00000024
1391301.mmaster02 Donor IA13 Isolation           ShearStep  439   440     0.01051289 / 0.12591584     0.01257539 / 0.14473675     0.05000000 / 0.00677165      1.00000024
1391302.mmaster02 Donor DTMIN5E12 Isolation      ShearStep  439   440     0.01051289 / 0.12591584     0.01257539 / 0.14473675     0.05000000 / 0.00677165      1.00000024
======================================================================================================================================================================
```

---

## 3. Input Deck & Subroutine Provenance Verification

```text
======================================================================================================================================================================
Job ID            INP SHA-256 (64 hex)               UEL .for SHA-256 (64 hex)          Nodes / Quads / UELs   *STATIC Card                  *CONTROLS Card
----------------  ---------------------------------  ---------------------------------  ---------------------  ----------------------------  -------------------------
1390876.mmaster02 105d2cc04de25f68c0a1fbeaab8b66d35  62e35f74bbeccd3f5b1ac67312b79211f  9073 n / 8836 q / 8836 0.001, 1.0, 1.0e-11, 0.02     4, 8, 9, 16, 10, 4, 50, 12
                  5881993cf6292e8201ad210137d3db8    4ccb75648ae20dbb8985cb577fe1aab    UELs (RP 99999)
----------------  ---------------------------------  ---------------------------------  ---------------------  ----------------------------  -------------------------
1391301.mmaster02 593cfc59ed9f2b76d8186bdf5c144be90  62e35f74bbeccd3f5b1ac67312b79211f  9073 n / 8836 q / 8836 0.001, 1.0, 1.0e-11, 0.02     4, 8, 9, 16, 10, 4, 50, 13
                  2ff53155baf5c930a7e7eb3b6a3d834    4ccb75648ae20dbb8985cb577fe1aab    UELs (RP 99999)        (DIFF ONLY: I_A = 13)
----------------  ---------------------------------  ---------------------------------  ---------------------  ----------------------------  -------------------------
1391302.mmaster02 346543717faf73e85fabffb008bcda8e5  62e35f74bbeccd3f5b1ac67312b79211f  9073 n / 8836 q / 8836 0.001, 1.0, 5.0e-12, 0.02     4, 8, 9, 16, 10, 4, 50, 12
                  2b19a9a9a081c7e197c943d65fa1fc5    4ccb75648ae20dbb8985cb577fe1aab    UELs (RP 99999)        (DIFF ONLY: dt_min = 5e-12)
======================================================================================================================================================================
```

---

## 4. Full-Trajectory Bit-for-Bit Parity Evaluation

Compared increment-by-increment across all 440 frames against donor control `1390876.mmaster02`:

```text
======================================================================================================================================================================
Comparison vs 1390876.mmaster02      Max |ΔRF1| (kN)          Max |ΔU1| (mm)           Max |Δd| (Phase)         First Differing State  Classification
-----------------------------------  -----------------------  -----------------------  -----------------------  ---------------------  -------------------------------
1390447.mmaster02 (Base Minimal)     0.00000e+00 (0.0 N)      0.00000e+00 (0.0 mm)     0.00000e+00              None                   IDENTICAL_CONTINUATION_CONTROL
1391301.mmaster02 (IA13 Isolation)   0.00000e+00 (0.0 N)      0.00000e+00 (0.0 mm)     0.00000e+00              None                   PATH_NEUTRAL_VALIDATED
1391302.mmaster02 (DTMIN5E12 Isol.)  0.00000e+00 (0.0 N)      0.00000e+00 (0.0 mm)     0.00000e+00              None                   PATH_NEUTRAL_VALIDATED
======================================================================================================================================================================
```

- **Reconciliation JSON**: [`models/generated/mode_ii/stage_e_refinement_coarsening_batch/canonical_donor_lineage_reconciliation.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/stage_e_refinement_coarsening_batch/canonical_donor_lineage_reconciliation.json)

---

## 5. Preserved Scientific Gates

```text
coarsened_stage_e_transfer_validation = VALIDATED
refined_stage_e_transfer_validation = REFINED_STAGE_E_CONTINUATION_GATE_UNRESOLVED
stage_e_continuous_baselines_validation = PARTIALLY_USABLE_UNDER_FORENSIC_REVIEW
same_mesh_restart_validation = VALIDATED
history_transfer_rule_resolved = true
selected_production_history_operator = HOST_ISOPARAMETRIC_BILINEAR_WITH_LOCAL_GP_BOUNDS_CLAMP
stage_d_nonmatching_transfer_validation = VALIDATED
nonmatching_transfer_algorithm_scientifically_unblocked = true
production_adaptive_accuracy_validation_scientifically_unblocked = false
PK10R1_topology_repair_required = true
telegram_delivery_observed = true
telegram_human_receipt_confirmed = true
email_delivery_observed = true
email_human_receipt_confirmed = false / unverified
notification_pre_submission_gate_passed = true
new_submission_authorized = false
qsub_called = false
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```
