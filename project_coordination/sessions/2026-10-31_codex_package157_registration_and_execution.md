# Package157 R4 controller maintenance, qualification and once-only execution

Base commit: 50bc9bec5875bca5860ecf757f22cb836e304ea8. User requested resolution of the repeated operation-registration deadlock and execution of the reviewed recovery experiment. Bootstrap found released turn403 and no live AGY/controller process. Claimed Codex ownership normally; preserved all unrelated dirty work, including .agents/INITIAL_PROMPT.txt. No additional autonomous controller loop was started.

## HPC STATUS

- Required compute-node technical qualification: 1419146.mmaster02, M1_C4_P157_R4_DC, terminal F/Exit0, run_count=1, mnode101, 34 s. Actual mechanical/phase Abaqus datachecks and R4 startup passed on compute hardware.
- Main numerical experiment: 1419147.mmaster02, M1_C4_P157_C1_2_R4, submitted ONCE via the registered adapter and Invoke-Mode1Execution.ps1. Live qstat observed RUNNING on mnode101, run_count=1, 1 CPU/16 GB/8 h.
- Both manifests reserved exactly once, real PBS receipts preserved, compute-job terminal reconciled in HPC ledger. Engine status has zero ready duplicate jobs; Resolve-ControllerOperation rejects the consumed operation.
- Live preflight verified email/Telegram login paths, config permissions, compiler, resources, runtime/package hashes and datachecks. telegram_notification_contract=PASS_LOGIN_NODE; compute-node terminal delivery remains UNRESOLVED, not claimed PASS.

## NEW EXPERIMENT

Canonical reviewed operation: execute_mode1_package157_c1_2_r4_adaptive_continuation. Definition: project_coordination/operation_definitions/execute_mode1_package157_c1_2_r4_adaptive_continuation.json. Adapter: scripts/validation/execute_package157_r4.py. Hash-bound qualification: scripts/validation/execute_mode1_package157_c1_2_r4_adaptive_continuation.qualification.json.

Built the previously nonexistent 157_c4_package157_c1_2_continuation_r4 package from authentic accepted R3 Step1 data. The historical handoff used both P150_R4 and P157_R4 job labels; the distinct registered/submitted name is M1_C4_P157_C1_2_R4. No historical alias was submitted.

Baseline uy=0.0018503125442191958 mm. First five targets advance by 10 nm across the failed 50 nm span; subsequent reviewed targets reach 0.0019503125442191958 and 0.002 mm. Numerical wrapper reuses the UNMODIFIED R3 coupled solver, frozen UEL and full-precision extractor. Each attempt is bounded to 50 outer iterations; only identified coupled nonconvergence triggers reviewed within-allocation subdivision, with 5 nm floor and depth2 ceiling. Technical failures do not trigger subdivision or PBS retry. Failed iterates never become committed baselines. Every converged checkpoint explicitly retains physical_acceptance=UNVERIFIED until independent physical review.

## SCIENTIFIC PROGRESS

All 7265 nodal states and 28224 GP histories preserved. Independently decoded authentic 7+8+3 cards and checked against recovered full history: maximum difference 8.970602038971265e-14 MPa. The early handoff's textual 28420 count is superseded by the verified actual count 28224, without modifying historical evidence.

P154 R3 1419113 Step1 remains the accepted equilibrium source; its Step2 outer100 numerical failure is preserved. R4 tests a reviewed loading-subdivision hypothesis, not an identical rerun. Solver tolerances, damage/history gates and force<=5% / RAW total-energy<=2% physical thresholds are unchanged. Matching-load reference review is still required. C1-2 is NOT accepted and P156 C4-to-C5 transfer remains dependent. No artificial damage clipping, reference substitution or forward-transfer success is claimed.

## DOCUMENTATION AND CONTROLLER CORRECTION

Added a reviewed operation-definition transition: declared candidate -> bounded real technical qualification -> hash-bound QUALIFIED_EXECUTION. Missing definitions yield DEFINITION_REVIEW_REQUIRED and one fingerprinted event, stopping before repeated AGY preparation dispatches. Registry changes and distinct scientific-review hashes change the event fingerprint; an unchanged blocker does not rewrite the event or create another agent session. Existing built-in research_preparation and already registered operations preserve their original routes. Safeguards and once-only submission accounting remain active.

The installed controller entrypoint matches canonical tested source, with prior installed version preserved under OpenClawPAD/backups. New registration module is included in controller evidence hashing. Updated historical tests to verify preserved absence/pending receipts without rerunning a utility that overwrites those historical artifacts.

43 focused solver/rollback/registration/once-only tests PASS, plus 3 compatibility/scientific-event tests PASS (46 total). Tested rejected-step rollback with deliberate candidate mutation, minimum increment and depth bounds, technical-failure stop, damage/history rejection, actual startup coverage, unchanged missing-definition event deduplication, existing-operation compatibility and distinct scientific-event fingerprints.

Preserved local failures and minimal repairs: first PBS preflight rejected missing explicit command -v ifort before any reservation; added compiler resolution and refreshed exact file hashes, then actual preflight passed. Initial pytest run finished all tests but hit an inaccessible shared pytest-current cleanup link; isolated test work directories avoid unrelated cache state. A nested Windows test process launch with inherited stdin raised WinError50; explicit DEVNULL repaired the deterministic test launch. No HPC rerun or accounting reset occurred for these repairs.

CURRENT_STATE.md is now a compact authoritative summary; the entire former 1530-line summary is preserved under project_coordination/history/2026-10-31_pre_package157_current_state.md. Turn403 remains completed; its runtime successor instruction now follows actual 1419147 results instead of requesting registration again. Original runtime checkpoint is preserved locally with its hash in the resolved registration event. Original user prompt is untouched.

All input/source/review/test/command/manifest hashes are recorded in the qualification, engine ledger, receipts, maintenance evidence and artifact registry. Bulky solver outputs and runtime logs remain on HPC; raw local controller checkpoint backup is not committed. Selective forward-only Git closeout follows this report.

## NEXT ACTION

Evaluate actual 1419147 results. While running, prepare only independent extraction/reference validation. On completion review all substeps, coupled convergence, committed damage/history, force and raw-energy gates. Do not resubmit R4 or execute P156 before scientific acceptance.

Finished
