# F1597-CORRECT-PACKAGE72-STATE-TRANSFER controlled scientific step

Bootstrap completed once; stage=Preparation.

## Verified Research Preparation Finding

Evidence compiled and review-ready operation definition prepared for evaluating Package 146 donor (Job 1418753.mmaster02) and Package 147 continuous reference (Job 1418768.mmaster02) at target displacement u = 0.0018003125442191958 mm under RF2 <= 5% and raw total-energy <= 2% continuity gates with zero coarsening. Operation is unregistered in controller inventory; DEFINITION_REVIEW_REQUIRED before execution.

Evidence: results/validation/preparation-cc0835d6-740f-4a0f-9ec1-03ccce9d807b.json

Status: PREPARATION_COMPLETE

### 1. HPC Evidence Inventory
- **Package 146 Donor**:
  - PBS Job ID: `1418753.mmaster02`
  - Job Name: `M1_C3_FINE_PACKAGE146_DONOR`
  - Remote Directory: `/scratch9/pr21vyci/runs/mode1_c3_fine_package146_donor`
  - Ledger State: `SUBMITTED` (authenticated submission; live solver output pending verification)
  - Elements: 5,112 CPE4 quads (5,290 nodes, h=0.81 um)
  - Input Deck SHA256: `9F93419A4F1E090286007A7291693BD3B783D984CE276E102D22D404AD4C5475`
  - Target Displacement: Step 1 completes at exact Frame-77 displacement `u = 0.0018003125442191958 mm`; Step 2 continues to `0.0020 mm`.

- **Package 147 Corrected Continuous Reference**:
  - PBS Job ID: `1418768.mmaster02`
  - Job Name: `M1_C4_CORRECTED_PACKAGE147_REF`
  - Remote Directory: `/scratch9/pr21vyci/runs/mode1_c4_corrected_package147_ref`
  - Ledger State: `SUBMITTED` (authenticated submission; live solver output pending verification)
  - Elements: 7,056 CPE4 quads (7,265 nodes, h_tip ~ 0.68 um)
  - Coarsened Elements: 0 (100% refined, h_ratio in [0.777, 0.926])
  - Input Deck SHA256: `FFFE51D5348F6E4B5E9B4742D783CA1645B480B229189168493AEDA10C91722A`
  - Target Displacement: Step 1 completes at exact Frame-77 displacement `u = 0.0018003125442191958 mm`; Step 2 continues to `0.0020 mm`.

### 2. Review-Ready Operation Definition
- **Operation ID**: `evaluate_mode1_package146_donor_and_package147_reference`
- **Candidate Implementation**: `scripts/validation/evaluate_package146_package147_evaluation_spec.py`
- **Unit Test Coverage**: `tests/unit/test_mode1_f1597_package146_147_evaluation_definition.py` (5 tests PASS)
- **Scope and Deliverables**:
  1. Authenticate Abaqus execution outputs (.odb, .dat, .msg, .sta) on remote cluster scratch.
  2. Extract Step-1 reaction force (RF2) and energy components (ALLSE, ALLPD, ALLFD) at displacement `u = 0.0018003125442191958 mm`.
  3. Continuous comparison against predeclared acceptance gates: RF2 discrepancy <= 5.0%, raw total-energy discrepancy <= 2.0%.
  4. Pointwise damage irreversibility (delta_d >= 0, zero healing nodes) and history monotonicity (H >= H0).
  5. Assess readiness for genuine nonmatching state transfer with zero mesh coarsening.
- **Registration Status**: UNREGISTERED in `scripts/controller/Controller-Operations.ps1`.
- **Review Prerequisite**: DEFINITION_REVIEW_REQUIRED before execution authorization can be granted.

### 3. Preserved Scientific Constraints
- Frozen UEL SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`
- Retained Gate Failures: `P113_GATE_VALID_FAILURE`, `H47_PACKAGE142_C1_1_FAILED`, `STAGE_C1_2_STEP2_ENERGY_GATE_FAILED`
- Acceptance Thresholds: RF2 <= 5%, total energy <= 2%
- No new solver execution, no speculative submissions, no unreviewed scientific parameter modifications.

Turn complete. No unqualified HPC job submitted.

Finished
