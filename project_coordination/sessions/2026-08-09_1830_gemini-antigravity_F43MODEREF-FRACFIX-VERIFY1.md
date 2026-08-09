# Session Report: F43MODEREF-FRACFIX-VERIFY1

**Date**: 2026-08-09 18:30:00 +02:00  
**Agent**: gemini-antigravity  
**Task ID**: `F43MODEREF-FRACFIX-VERIFY1`  
**Preparation Tag**: `P43MODEREF5-FINAL1` (`3f4f23d9fca381e1899efc6ab721ce5cf0b02411`)  
**Qualification Tag**: `Q43MODEREF5` (`926fbb5001ffae01e63a15afbf1a7008cf36eecb`)  
**Qualification Location**: `/home/pr21vyci/projects/adaptive-remeshing-worktree-p5` (Detached HEAD on `tu_freiberg`)

---

## 1. Governance & Session Claim
- `ACTIVE_SESSION.json` successfully claimed before any editing (`active: true`, task `F43MODEREF-FRACFIX-VERIFY1`).
- Preserved historical failure evidence for `1385728`, `1385729`, `1385895`, `1385896`. Jobs `1385895` and `1385896` remain classified as:
  - `scheduler_result = PASS`
  - `technical_result = PASS`
  - `scientific_result = HOLD_phase_field_result_inconsistent_with_historical_H0`
- Strictly enforced `execution_authorized = false`, `submission_approved = false`, `maximum_jobs_now = 0`, `qsub_called = false`.

---

## 2. Scientific Phase Residual & Tangent Equivalence
- **Quad U1 & Triangle U3 Audit**:
  Audited `f42_mixed_uel.for` quad Type 1 and triangle Type 3 against historical Mode-II H0 (`ModeII_H0_serial.for`), Molnár source architecture, and published weak-form equation $(G_c / l_0 + 2H) d - G_c l_0 \nabla^2 d = 2H$.
- **Local Structure**:
  - Gradient term: $G_c l_0 \nabla N^T \nabla d$
  - Local term: $(G_c / l_0 + 2H) N d$
  - Driving term: $-2 H N$
- **Tangent Matrix Consistency**:
  Verified $\text{AMATRX}_{ij} = \frac{\partial (-\text{RHS}_i)}{\partial d_j}$ exactly for both Quad U1 and Triangle U3.

---

## 3. SDV Producer Ownership Repair
- Established explicit producer ownership across element layers:
  - `SDV14`: Phase carried/exposed by **Displacement/Mechanical UEL (Type 2 / Type 4)** $\to$ `USRVAR(PHYSIDX, 14, INPT) = PHASE`.
  - `SDV15`: Phase solved by **Phase-field UEL (Type 1 / Type 3)** $\to$ `USRVAR(PHYSIDX, 15, INPT) = PHASE`.
  - `SDV16`: History $H$ updated by **Displacement UEL (Type 2 / Type 4)** $\to$ `USRVAR(PHYSIDX, 16, INPT) = USRVAR(PHYSIDX, 13, INPT)`.
- Diagnostic distinction between `SDV14` and `SDV15` is fully preserved. In staggered execution, `SDV14` vs `SDV15` may differ within an increment due to staggered iteration synchronization.

---

## 4. UEL Variables Contract Verification
- Quad Phase U1: `VARIABLES = 8`
- Quad Displacement U2: `VARIABLES = 56`
- Triangle Phase U3: `VARIABLES = 6`
- Triangle Displacement U4: `VARIABLES = 42`
- Verified deck declarations and Fortran SVARS array bounds match exactly.

---

## 5. Accepted H0 Reference Identity & Fixture Disambiguation
- Accepted convergence benchmark job: `1378942.mmaster02`.
- `accepted_H0_ODB_available = false` (raw ODB purged per repository policy; extracted CSV evidence retained).
- `1376411_equivalent_extractor_fixture_for_1378942 = true` (ODB `1376411` retained and formulation-equivalent for extractor testing).

---

## 6. Phase Bounds & Overshoot Analysis
- Theoretical bounds: $[0, 1]$
- Observed maximum phase in benchmark H0 fixture: $d_{\max} = 1.0105$
- Phase overshoot: $+0.0105$ ($+1.05\%$)
- Classification: `original_historical_molnar_unconstrained_formulation_behavior` (unconstrained linear solver permits slight numerical overshoot near crack tip; recorded explicitly without artificial clipping).

---

## 7. Lineage & Detached Qualification
- Reconciled `P43MODEREF4` lineage: Recorded historical `git checkout --` on cluster as a governance deviation. Created fresh preparation commit `P43MODEREF5-FINAL1` (`3f4f23d9fca381e1899efc6ab721ce5cf0b02411`).
- Exact-P Qualification in detached worktree `/home/pr21vyci/projects/adaptive-remeshing-worktree-p5` on `tu_freiberg`:
  - 618 out of 618 unit tests passed cleanly (100%).
  - Mode-II reference regression gate passed.
  - Bash syntax checks on all 8 `.pbs` and `submit_*.sh` scripts passed.
  - `git status --porcelain=v1`, `git diff --exit-code`, `git diff --cached --exit-code` verified naturally clean.
- Fresh qualification tag `Q43MODEREF5` (`926fbb5001ffae01e63a15afbf1a7008cf36eecb`) pushed to origin.

---

## 8. Two-Job Verification Batch Preparation (Pair 1)
Created generator `build_mode_ii_fracfix_verification_batch.py` and generated two independent verification packages:
1. **`M2REF_ONEEL_FRACFIX_VERIFY`**:
   - 1-element analytical/source verification deck
   - Input SHA256: `0a86b66a541604a116b4feae2572b8d578ebc6d9a1f5cebd249f310f845c43d2`
   - Subroutine SHA256: `0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8`
   - PBS SHA256: `240969e9bee6289b4cfb06df0e61ec233ef0c0d12efee3fd4114757c918ef0e9`
   - Resources: 1 CPU, 8 GB memory, `00:15:00` walltime, Queue `entry_imfdfkmq`
2. **`M2REF_H0_FRACFIX_REPRO`**:
   - H0 benchmark mesh reproduction deck (3,812 quad elements)
   - Input SHA256: `4bcc529509dfb0fb849e7b23aa4cfef639b7bf6beceb816a7f053503ed3fbbbc`
   - Subroutine SHA256: `0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8`
   - PBS SHA256: `9c326977bf5a2f5f9037c7689975765955fe4fd6840742f9bcf01b183617beaa`
   - Resources: 1 CPU, 8 GB memory, `01:00:00` walltime, Queue `entry_imfdfkmq`

Both jobs are ready for future concurrent execution (`planned_future_submissions = 2`, `maximum_running_jobs = 2`).

---

## 9. Future Production Batch Policy (Pair 2)
Only after BOTH verification jobs (`M2REF_ONEEL_FRACFIX_VERIFY` and `M2REF_H0_FRACFIX_REPRO`) pass scientifically, the next scientific batch will be:
- `M2REF_H1_FRACFIX`
- `M2REF_H2_FRACFIX`
