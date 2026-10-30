# Package 148 runtime repair — 30 October 2026

Status: REPAIRED_OFFLINE_PENDING_INDEPENDENT_ABAQUS_RUNTIME_REVIEW.
Registration, Abaqus datacheck, and HPC submission remain unperformed. This is
an implementation milestone, not scientific acceptance of state transfer.

Starting commit: 99d2665dd120cf366a1fa4d476d9567e8754f107.
Bootstrap verified an inactive session and claimed it before writes. Existing
dirty work was preserved. All nine original Package 148 artifact bindings in
the old review packet still match. Frozen UEL remains
CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6.

## Implemented runtime

The canonical driver now has a CLI and an actual bounded serial execution loop.
Each mechanical and phase solve runs Abaqus/Standard in a fresh directory with
its own input, launcher log, read-only ODB export and receipt. There are no qsub
calls, retries or changes to submission accounting inside the loop.

1. Mechanics: prescribe the current damage at all physical nodes and retain the
   source model's bottom, pin, top-horizontal and reference-point conditions.
2. Reconstruct the frozen UEL's POS_M from the authentic displacement endpoint,
   then set H=max(transferred donor H0, current POS_M). Unconverged outer iterates
   never replace the donor baseline. This avoids history ratcheting across cold
   Abaqus subproblems.
3. Phase: prescribe the mechanical endpoint displacements and seed the current H;
   clamp only the active damage nodes to d0. Remove the top/reference-point
   equations in this displacement-prescribed subproblem to avoid dependent-DOF
   overconstraint. Free damage nodes are solved by Abaqus.
4. Assemble the frozen phase equations and update the active set using signed
   Kd-f residuals. Require nonnegative active multipliers, small free residuals,
   complementarity and admissible complete damage before accepting phase KKT.
5. Repeat mechanics/phase. Re-evaluate KKT with the newly reconstructed history
   at the final mechanical endpoint; require damage, displacement and history
   stabilization. Check the unchanged 5% force and 2% energy continuity gates.

Default bounds are 20 outer iterations, 20 phase iterations per outer iteration,
one CPU, 16 GB and a shared 780-second runtime deadline inside the existing
15-minute PBS allocation. Every Abaqus solve has one full-load static increment;
no cutback or speculative replacement is introduced. Linux timeout handling
terminates only the spawned solve process group. Failures preserve evidence and
stop without retry. These settings require review and real Abaqus qualification.

The endpoint extractor rejects missing/duplicate physical nodes, absent U3,
incomplete energy integration-point coverage and wrong endpoints. It verifies
read-only ODB identity and counts the repeated SDV17/18 element energy totals once
per element. Full finite damage bounds and field completeness are checked before
KKT or gate evaluation. The old three counterexample tests now require rejection.

Runtime reports keep physical equilibrium/gates separate from scientific
acceptance. An equilibrium checkpoint records complete displacement, damage and
history arrays. Continuation remains disabled and scientific_acceptance=false
until independent review establishes donor committed-history equivalence and
authentic coupled endpoint validity. The donor source is accepted-frame UMAT
SDV2; this repair does not prove its equivalence to the full committed UEL state.

## Additional Gauss-point correction

Inspection found that the spatial mapper uses row order (-,-),(+,-),(-,+),(+,+)
while the frozen UEL uses perimeter order (-,-),(+,-),(+,+),(-,+). The donor
UMAT exposes UEL history by NPT index. The generator now explicitly converts
donor perimeter values to mapper row order and converts mapped history back to
UEL order for SVARS injection. Runtime history assembly uses UEL order.

The legacy package is preserved. The distinct R1 technical correction is at
models/pandey_kumar_mode1/148_c4_package148_state_transfer_r1/. Its manifest binds
source evidence, runtime sources and candidate files; it is explicitly not an
execution manifest or qualification certificate. Generation refuses to overwrite
an existing package manifest. Source paths are portable forward-slash paths.

The R1 PBS invokes the coupled Python runtime instead of a single all-clamped
solve. Notification config loading, STARTED and terminal traps fail closed.
telegram_notification_contract=UNRESOLVED: no real notification delivery test or
compute-node verification was performed. No SUBMITTED event is claimed.

## Verification

- Existing full donor/receiver transfer-driver suite: 15/15 PASS (24.597 s).
  Includes full R1 load, all 7,265 nodes and all 28,224 history values.
- New runtime and rejection suite: 16/16 PASS (0.622 s). Covers all three original
  counterexamples, signed active/free KKT, a complete mechanical/phase/mechanical
  control-flow cycle, node release, failure/no-retry paths, iteration exhaustion,
  process timeout/nonzero exit, read-only extraction, energy counting and GP order.
- Nonuniform skew-element matrix/RHS agree with the separate existing
  PhaseResidualEvaluator to 13 decimal places; its finite-difference residual
  check passes. An affine strain patch matches the frozen POS_M expression.
- Actual R1 offline load verifies source/data hashes and complete field coverage.
- Generated PBS passes Git Bash `bash -n` and has LF line endings.
- All nine legacy model artifact hashes remain unchanged. Scoped whitespace
  checks pass; unrelated pre-existing whitespace findings were left untouched.

The solver responses and ODB API in control-flow/extractor tests are synthetic;
the process tests run Python, not Abaqus. None of these results establishes
Abaqus API compatibility, physical convergence, notifications or state-transfer
acceptance. No HPC job or scheduler mutation occurred.

## Next scientific action

Review the R1 numerical split, GP permutation, residual tolerances, baseline
history semantics and command/extractor contract independently. Then perform
real Abaqus 2023 datacheck and bounded runtime qualification through the governed
execution workflow, after generating its exact once-only execution manifest and
verifying notifications. Review authentic results before any loaded continuation.
No enrollment, permission issuance or machine activation is needed.

The repair commits the previously untracked canonical transfer generator, driver
and associated test suite. The existing Package 147 reference input is included
without modification because it is a hash-bound R1 reproduction prerequisite.
No duplicate source tree, solver binary or bulky runtime output is included.

Local check recovery: py_compile encountered Windows access denial replacing an existing __pycache__ file. No cache permissions were changed. In-memory compile() of all three sources passed without cache writes; the imported test suites had already passed.
