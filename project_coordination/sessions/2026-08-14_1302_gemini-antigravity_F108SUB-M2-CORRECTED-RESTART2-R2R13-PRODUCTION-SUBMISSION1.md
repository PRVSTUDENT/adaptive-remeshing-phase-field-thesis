# Session Report: F108SUB Production Submission of Qualified Candidate M2STATE_FRACFIX_RESTART2R13

- **Date**: 2026-08-14
- **Agent**: `gemini-antigravity`
- **Task ID**: `F108SUB-M2-CORRECTED-RESTART2-R2R13-PRODUCTION-SUBMISSION1`
- **Job ID**: `1389325.mmaster02`
- **Candidate Name**: `M2STATE_FRACFIX_RESTART2R13`
- **Source Job**: `1389278.mmaster02` (`M2STATE_FRACFIX_RESTART1R1R11`, $u_1 = 0.010000\text{ mm}$, $RF_1 = 0.123223\text{ kN}$)
- **Target Mesh**: `PK10R1` nonmatching mesh (9,849 nodes, 9,612 physical elements: 9,588 quads, 24 tris)
- **Status**: **`SUBMITTED_RUNNING_ON_CLUSTER`**

---

## 1. Submission Execution & Resource Contract

1. **Pre-Submission Manifest Verification**:
   - Manifest SHA256: `4ce01ef69fe1ce016de3f5bc1849b0a1689bd99fcf9bfebb12e22554bbdfa2b7` (**`PASS`**)
   - All 9 package files verified intact.

2. **Resource Contract & Scheduler Placement**:
   - `select=1:ncpus=1:mem=16gb`
   - `walltime=24:00:00`
   - `queue=entry_imfdfkmq` (routed to `normal_imfdfkmq` on `mnode104`)
   - Directives: `#PBS -m abe -M pr21vyci@mailserver.tu-freiberg.de`
   - `automatic_retry=false`

3. **Guarded Submission Execution**:
   - Invocation: `./submit_m2state_fracfix_restart2r13.sh --execute`
   - PBS Job ID: `1389325.mmaster02`
   - Initial Scheduler State: `R` (Running on `mnode104[0]`)
   - `qsub_call_count`: Exactly **1** (authorization fully consumed).

4. **Dual-Channel Notification**:
   - Wrapper issued `notify_submitted` for `1389325.mmaster02`.
   - PBS directives `#PBS -m abe` active.
   - Script level `notify_start` and terminal trap installed.

---

## 2. Policy & Invariants

- `candidate = M2STATE_FRACFIX_RESTART2R13`
- `package_manifest_sha256 = 4ce01ef69fe1ce016de3f5bc1849b0a1689bd99fcf9bfebb12e22554bbdfa2b7`
- `pre_submission_manifest_contract = PASS`
- `qsub_call_count = 1`
- `pbs_job_id = 1389325.mmaster02`
- `submission_result = SUBMITTED`
- `authorization_consumed = true`
- `automatic_retry = false`
- `qdel_called = false`
- `qmove_called = false`
