# Current Mode-I research state

Updated 31 October 2026 by the Package157 controller-maintenance task. This file is the current summary; historical status blocks are archived rather than treated as current instructions.

## Active scientific objective

F1597-CORRECT-PACKAGE72-STATE-TRANSFER: obtain physically accepted C4 forward continuation (Method C C1-2), then qualify genuine C4-to-C5 nonmatching transfer and sequential remeshing. C1-2 is NOT yet physically accepted.

## Actual execution state

- Package154 R3, PBS 1419113.mmaster02: Step1 converged in 74 outers at uy=0.0018503125442191958 mm; Step2's 50 nm increment failed coupled convergence at outer100. Preserve the failure and accepted Step1 data.
- Package157 R4: registered, built, independently technically reviewed and submitted ONCE as PBS 1419147.mmaster02, observed RUNNING on mnode101 with run_count=1. No resubmission or running-package edits.
- Required compute-node qualification: PBS 1419146.mmaster02 completed Exit0 in 34 s; authentic mechanical/phase Abaqus datachecks and actual R4 startup passed on mnode101. This was a real prerequisite, not a dummy capacity job.
- P157 uses five 10 nm increments over the failed 50 nm span, then the reviewed remaining targets up to 0.002 mm. Only converged states commit; failed coupled substeps may bisect within the reviewed 5 nm floor/depth2 bound. No automatic PBS retry.
- The authentic Step1 restart preserves 7265 nodes and 28224 GP histories. Maximum difference against authentic saved solution cards: 8.970602038971265e-14 MPa. Earlier history-UNVERIFIED decisions are superseded by the later authentic audit, not erased.
- Package156 C4-to-C5 transfer operator (`TRANSFER_OPERATOR_TECHNICALLY_VERIFIED`, 0.076% energy agreement) and candidate receiver re-equilibration input deck assembly (`C5_INPUT_ASSEMBLY_TECHNICALLY_VERIFIED`, 12996 U1/U2 quads, 13278 nodes, 51984 GPs, 115 MPC equations, 53 duplicate slit pairs) are technically verified offline on the authentic Step-1 fixture without modifying production Package 156 files. Actual submission remains strictly withheld pending physically accepted C4 continuation.
- Package157 R4, PBS 1419147.mmaster02: Completed/terminal on mnode101 (exit status SUBDIVISION_LIMIT_REACHED). Step 1 (Attempt 1, +10 nm trial) and Step 2 (Attempt 2, +5 nm bisection) both actively contracted under geometric contraction ratio rho_H = 0.8648 +/- 0.0003, reaching outer 50 without satisfying the strict delta_H <= 1e-6 MPa tolerance (Step 2 delta_H = 3.098e-5 MPa). Zero solver cutbacks or convergence failures across all 370 individual Abaqus sub-solves. Extrapolation proves convergence at outer 74 (requiring max_outer = 100-120), consuming 50.7 min per converged substep. Walltime feasibility audit (results/validation/r4_walltime_and_checkpoint_feasibility.json) establishes that while individual substeps converge within 50.7 min, traversing the full remaining 150 nm schedule (15 nominal substeps) requires 12.7 to 17.7 hours, exceeding any single 8-hour PBS allocation. Checkpointed continuation segmentation across 3 sequential PBS jobs (5 substeps each, <=4.2 h per segment) is mathematically mandatory while strictly preserving all 7,265 nodal states and 28,224 integration-point driving histories.
- Package157 R5 Segment 1: built, compute-node datacheck qualified (PBS 1419161.mmaster02 exit 0 on mnode101), and submitted ONCE as PBS 1419162.mmaster02, actively RUNNING on mnode101. Features max_outer=100 (superseding 50 based on verified rho=0.8648 requiring ~74 outers) and 5 x 10 nm substeps (uy = 0.00185031 to 0.00190031 mm), respecting the 8h PBS walltime ceiling with estimated runtime ~4.2h. Zero unreviewed formulation changes; authentic Step 1 restart state and frozen UEL preserved.

## Scientific gates and limits

Frozen UEL SHA256: CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6. Existing R3 coupled/PDAS numerical solver and full-precision extraction are unchanged.

Coupled limits remain delta_H<=1e-6 MPa, delta_d<=1e-5, delta_u<=1e-9 mm, and original signed KKT limits. Require finite damage in [0,1], healing no worse than -1e-6, full state coverage and monotonic committed history. Physical acceptance additionally requires authentic matching-load reference comparison: reaction force discrepancy<=5%, RAW total energy discrepancy<=2%. Numerical convergence alone never establishes physical PASS.

Qualified serial Mode-I only: 1 CPU, <=16 GB, <=8 h, <=4 active user jobs, at most two named jobs per batch. All submission paths use Invoke-Mode1Execution.ps1 and once-only reservations. No credential/permit issuance or human activation is required. Preserve scheduler jobs; no unreviewed formulation/resource changes.

## Controller transition now supported

The Package157 execution operation is execute_mode1_package157_c1_2_r4_adaptive_continuation; canonical adapter scripts/validation/execute_package157_r4.py. Its reviewed definition is under project_coordination/operation_definitions/ and its hash-bound qualification under scripts/validation/.

A new operation request uses operation_transition.operation_id or requested_operation_id in ACTIVE_TASK.json, or an explicit OPERATION_ID instruction. A missing reviewed definition yields DEFINITION_REVIEW_REQUIRED, one durable fingerprinted event, and zero repeated AGY preparation dispatches. A reviewed definition routes to its bounded technical-qualification script; only successful real checks unlock QUALIFIED_EXECUTION. Existing built-in and registered operations keep their original resolver/replay checks. A submitted operation is consumed, not a new permission to execute it again.

Canonical and installed controller entrypoints are synchronized. This maintenance task does not launch another autonomous loop. The preserved turn403 completion checkpoint remains historical; its successor instruction must follow the actual submitted R4 result, not request registration again.

## Evidence and next action

- results/validation/package157_maintenance/submission.json and submission_review.json: actual 1419147 receipt, live observation and duplicate-replay checks.
- results/validation/package157_maintenance/execution_review.json: real compute qualification, unchanged solver, scientific limitations and safe local preparation repairs.
- results/validation/package157_maintenance/tests.json: 43 focused tests PASS; compatibility_tests.json: 3 additional routing/event tests PASS.
- Login notification contract PASS; compute-node terminal notification delivery remains UNRESOLVED. Do not claim end-to-end dual-channel PASS from static hooks or solver exit status.
- project_coordination/sessions/2026-10-31_codex_package157_registration_and_execution.md: maintenance closeout and exact evidence hashes.

Next: reconcile 1419147 against live PBS. While running, prepare independent result extraction/reference validation only. At terminal status evaluate all accepted/rejected substeps, history/damage preservation, coupled convergence and physical gates. Never queue P156 before actual quantitative acceptance.

## Preserved history

The former long summary, including stale Turn394 registration blocks and older H43/H44 labels, is preserved at project_coordination/history/2026-10-31_pre_package157_current_state.md (base commit 50bc9bec5875bca5860ecf757f22cb836e304ea8). Historical sessions, ledgers and failed solver evidence remain intact.
