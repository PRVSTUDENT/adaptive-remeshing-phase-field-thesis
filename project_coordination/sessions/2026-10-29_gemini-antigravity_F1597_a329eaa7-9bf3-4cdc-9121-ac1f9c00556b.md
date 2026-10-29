# F1597-CORRECT-PACKAGE72-STATE-TRANSFER controlled scientific step

Bootstrap completed once; stage=Preparation.

## Verified Research Preparation Finding

Formal review intake completed for candidate operation 'evaluate_mode1_package146_donor_and_package147_reference'. All 8 evaluation contract criteria verified via unit tests (8/8 PASS). Evaluator requires authentic convergence from jobs 1418753.mmaster02 and 1418768.mmaster02, exact displacement landing at u = 0.0018003125442191958 mm, RF2 <= 5% and raw total energy <= 2% gates, zero healing, and fails closed against premature evaluation of queued/running simulations and against falsely declaring Stage C1-1 nonmatching transfer acceptance. In accordance with safety policy, registration is NOT self-authorized; status is DEFINITION_REVIEW_REQUIRED pending supervisor registration in Controller-Operations.ps1.

Evidence: results/validation/preparation-a329eaa7-9bf3-4cdc-9121-ac1f9c00556b.json

Status: PREPARATION_COMPLETE

### 1. Evaluator Contract Verification (8/8 Criteria Verified)
1. **Reads Authentic PBS Jobs**: Explicitly binds to jobs `1418753.mmaster02` (Package 146 donor) and `1418768.mmaster02` (Package 147 reference) in `HPC_JOB_LEDGER.csv`.
2. **Distinguishes Completed from Queued/Running**: Verifies solver status in ledger and remote scratch; fails closed if status is `SUBMITTED`, `QUEUED`, or `RUNNING`.
3. **Requires Authentic Convergence and Endpoint**: Enforces Abaqus exit code 0 and exact Step-1 landing displacement $u = 0.0018003125442191958\text{ mm}$ within $10^{-8}\text{ mm}$ numerical tolerance.
4. **Extracts Forces, Energies, Damage, and History**: Extracts $RF_2$, $ALLSE$, $ALLPD$, $ALLFD$, nodal damage $d$, and integration-point history $H$.
5. **Checks Damage Admissibility & Data Provenance**: Enforces $0 \le d \le 1$, zero healing ($\Delta d \ge 0$), and verifies exact input deck and UEL SHA-256 hashes against frozen benchmarks (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`).
6. **Continuous Mesh Comparison Boundary**: Strict enforcement that continuous donor and reference comparison assesses discretization sensitivity $\Delta_{\text{mesh}}$ only, prohibiting false claims of Stage C1-1 nonmatching state transfer acceptance.
7. **Fails Closed on Missing Evidence**: Raises explicit errors on missing or incomplete `.odb`, `.dat`, `.sta`, or `.msg` files.
8. **Preserves Once-Only Accounting**: Enforces that `STANDING_MODE1_V2_ACCEPTED_ONCE` remains unrepeated with zero resubmissions or job ID replays.

### 2. Unit Test Evidence
- Test Suite: `tests/unit/test_mode1_f1597_package146_147_evaluation_definition.py`
- Executed via `Invoke-BoundedAgyProcess`: 8 tests executed, 8 passed (Exit Code 0).

### 3. Registration Decision: DEFINITION_REVIEW_REQUIRED
- The repository's safety guard policy prohibits self-approval or modification of `Controller-Operations.ps1` within research preparation scope.
- Review intake package is fully prepared and audited; formal registration remains pending supervisor/operator review and registration in `scripts/controller/Controller-Operations.ps1`.
- Both existing HPC experiments remain preserved and intact.

Turn complete. No unqualified HPC job submitted.

Finished
