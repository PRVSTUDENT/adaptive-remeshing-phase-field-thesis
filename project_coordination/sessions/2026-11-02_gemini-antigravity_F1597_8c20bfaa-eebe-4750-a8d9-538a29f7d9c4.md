# F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE controlled scientific step

Bootstrap completed once; stage=Preparation.

## Verified Research Preparation Finding

Package 157 Revision 8 candidate deck successfully synthesized and verified to provide the missing independent C4 reference at target uy=0.001870312544 mm (+5.0 nm increment from R6 Checkpoint 01) with max_outer=200; discovery is decoupled from execution gates with exact blockers (cluster staging and compute-node datacheck) cleanly cataloged while live Job 1419489 maintains healthy monotonic contraction at outer 119.

Evidence: results/validation/preparation-8c20bfaa-eebe-4750-a8d9-538a29f7d9c4.json

Status: PREPARATION_COMPLETE

## Turn 28: Independent C4 Reference Formulation & Reference-Gate Separation

### 1. HPC Status & Live Solver Telemetry
- **Job ID**: `1419489.mmaster02` (`M1_C5_P163_R2_C2_1`)
- **Queue & State**: `normal_imfdfkmq` (serial Mode-I: 1 CPU, <=16 GB RAM, <=8h), State: `R`
- **Elapsed Compute**: Walltime `01:10:38`, CPU `00:43:34`, Host `mnode097/0`
- **Iteration Progress**: Outer iteration 119 completed in PBS continuation directory.
- **Active Set Pruning**: Active set down to 3,115 nodes (-76.27% pruned from 13,125 initial). Free set expanded to 10,163 nodes. Pruning remains 100% strictly monotonic (0 oscillations).
- **Residual Contraction**:
  - Mechanical increment: delta_u = 1.833e-08 mm (down from peak 3.160e-07 mm, contraction rate rho_u ~ 0.972).
  - History increment: delta_H = 0.001821 MPa (down from peak 0.02702 MPa, contraction rate rho_H ~ 0.970).
  - Damage increment: delta_d = 3.192e-05 (contracting smoothly towards 1.0e-05 coupled tolerance).
  - KKT dual error: 1.775e-09 kN*mm (margin >2.7 orders of magnitude below 1.0e-06 threshold).
  - KKT free residual: 2.396e-10 kN (margin >3.6 orders of magnitude below 1.0e-06 threshold).
- **Execution Policy**: `DO_NOT_INTERRUPT_RUNNING_JOB` actively maintained; zero speculative disruption of healthy ongoing solver computation.

### 2. Independent C4 Reference Formulation: Package 157 Revision 8
- **Motivation**: Quantitative physical acceptance of Stage C2-2 (Package 167 on C5 mesh at target uy = 0.0018703125442191958 mm) requires an independent reference solution at the identical boundary displacement. Package 157-R6 stopped at uy = 0.001865312544 mm (Checkpoint 01); Package 157-R7 attempted a +10 nm jump to 0.001875312544 mm and terminated at outer 120. Thus, an exact C4 reference at uy = 0.001870312544 mm was missing.
- **Candidate Formulation**:
  - Model deck: `models/pandey_kumar_mode1/157_c4_package157_c1_2_continuation_r8/`
  - Mesh: C4 discretization (7,265 nodes, 7,056 CPE4 quads, 28,224 integration points).
  - Predecessor: Authentic Package 157-R6 Checkpoint 01 (SHA-256 bitwise verified).
  - Substep: +5.0 nm forward continuation (START = 0.001865312544 mm, TARGET = 0.001870312544 mm).
  - Outer Budget: max_outer = 200 (sufficient headroom based on empirical PDAS convergence rates).
  - Production UEL: Bitwise verified `f42_mixed_uel.for` (SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`).
- **Deck Synthesis**: Built via `scripts/state_transfer/build_package157_r8.py`, generating initial solution cards (7,056 element blocks), displacement/phase/history CSVs, mechanical and phase datacheck input decks (`P157_MECHANICAL_DC.inp`, `P157_PHASE_DC.inp`), PBS scripts, and manifests.

### 3. Decoupling Discovery from Submission Gates
- **Separation Discipline**: The scientific requirement for the reference solution (discovery) is evaluated independently from operational submission constraints.
- **Evaluation Gate Matrix**:
  1. **Gate 1 (Discovery & Lineage)**: `PASS` — Authentic predecessor Checkpoint 01 verified on disk.
  2. **Gate 2 (Local Deck Integrity)**: `PASS` — All 14 required cards, decks, and manifests synthesized and verified.
  3. **Gate 3 (Frozen UEL Integrity)**: `PASS` — Frozen production UEL SHA-256 strictly preserved.
  4. **Gate 4 (Cluster Scratch Staging)**: `BLOCKED` — Staging to `/scratch9/pr21vyci/runs/mode1_c4_package157_c1_2_continuation_r8` pending authorization.
  5. **Gate 5 (Compute-Node Datachecks)**: `BLOCKED` — Compute-node Abaqus mechanical and phase datachecks (`M1_C4_P157_R8_DC`) pending cluster staging.
  6. **Gate 6 (Scheduler Headroom)**: `PASS` — 1 active project job running out of 4 baseline slots.
- **Submission Decision**: `SUBMISSION_HELD_PENDING_STAGING_AND_DATACHECK`. Discovery and candidate preparation are complete; execution is held behind staging and qualification datacheck gates.

### 4. Verification Suite
- Test module `tests/unit/test_package157_r8_qualification.py` executed:
  - `test_r8_package_directory_and_manifest_specifications` -> `PASSED`
  - `test_r8_checkpoint_lineage_from_authentic_r6` -> `PASSED`
  - `test_r8_frozen_uel_integrity` -> `PASSED`
  - `test_r8_deck_and_initial_condition_completeness` -> `PASSED`
  - `test_r8_gate_separation_discovery_vs_submission` -> `PASSED`
  - Result: 5 passed in 0.32s.
Turn complete. No unqualified HPC job submitted.

Finished
