# Project Current State

Last Updated: 2026-08-09T16:36:00+02:00
Active Agent: gemini-antigravity
Protocol Version: 1

## Active Task
- Task ID: `F43MODEREF-FRACFIX-VERIFY1`
- Task Description: Scientific mapping audit, SDV producer ownership repair, exact-P qualification, and two-job verification-batch preparation.
- Status: `verification_batch_ready_awaiting_authorization`
- Preparation Tag: `P43MODEREF5-FINAL1` (`3f4f23d9fca381e1899efc6ab721ce5cf0b02411`)
- Qualification Tag: `Q43MODEREF5` (`926fbb5001ffae01e63a15afbf1a7008cf36eecb`)
- Qualification Worktree: `/home/pr21vyci/projects/adaptive-remeshing-worktree-p5` (Detached HEAD, 618/618 tests pass, naturally clean)

## Key Technical & Scientific Audit Results
1. **Phase Residual & Tangent Formulations**:
   - Quad U1 and Triangle U3 phase residual and tangent audited against historical Mode-II H0 (`ModeII_H0_serial.for`), Molnár source architecture, and published weak form $(G_c/l_0 + 2H) d - G_c l_0 \nabla^2 d = 2H$.
   - Confirmed exact equivalence and 100% exact tangent matrix consistency $\frac{\partial (-\text{RHS})}{\partial d} = \text{AMATRX}$.

2. **SDV Producer Ownership Separation**:
   - `SDV14` = Phase carried/exposed by Displacement UEL (Type 2/4).
   - `SDV15` = Phase solved by Phase-field UEL (Type 1/3).
   - `SDV16` = History $H$ written by Displacement UEL (Type 2/4).
   - Diagnostic distinction between `SDV14` and `SDV15` preserved. `SDV14` vs `SDV15` may differ within staggered iterations/steps due to staggered synchronization.

3. **UEL Variables Contract**:
   - Quad Phase U1: `VARIABLES = 8`
   - Quad Displacement U2: `VARIABLES = 56`
   - Triangle Phase U3: `VARIABLES = 6`
   - Triangle Displacement U4: `VARIABLES = 42`

4. **Accepted H0 Reference Identity**:
   - Accepted benchmark job ID: `1378942.mmaster02`.
   - `accepted_H0_ODB_available = false` (raw ODB purged per repository policy; all extracted CSV evidence retained).
   - `1376411_equivalent_extractor_fixture_for_1378942 = true` (ODB 1376411 retained and formulation-equivalent for extractor testing).

5. **Phase Bounds & Overshoot Analysis**:
   - Theoretical bounds: $[0, 1]$
   - Observed maximum phase in benchmark H0 fixture: $d_{\max} = 1.0105$
   - Phase overshoot: $+0.0105$ ($+1.05\%$)
   - Classification: `original_historical_molnar_unconstrained_formulation_behavior` (unconstrained linear solver permits slight numerical overshoot near crack tip; recorded explicitly without artificial clipping).

6. **Two-Job Staged Batch Strategy**:
   - **Verification Batch (Pair 1)**: `M2REF_ONEEL_FRACFIX_VERIFY`, `M2REF_H0_FRACFIX_REPRO`
   - **Production Batch (Pair 2)**: `M2REF_H1_FRACFIX`, `M2REF_H2_FRACFIX`
   - Maximum concurrent running jobs: 2

## Current HPC Authority Boundary
- `authorization_ready_for_verification_batch = true`
- `execution_authorized = false`
- `submission_approved = false`
- `maximum_jobs_now = 0`
- `qsub_called = false`
- `HPC_submissions = 0`
