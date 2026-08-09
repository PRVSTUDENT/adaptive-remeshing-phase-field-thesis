# Session Report: F43MODEREF-SUB1

- **Task ID**: `F43MODEREF-SUB1`
- **Agent**: `gemini-antigravity`
- **Date**: `2026-08-09`
- **Status**: `complete_pass`
- **Classification**: `f43_mode_ii_reference_batch_submission_pass`

---

## 1. Direct Human Chat Authorization Evidence

- **Explicit Authorization Sentence Received**:
  > *"I authorize exactly two guarded HPC submissions for the Mode-II uniform phase-field reference convergence batch using preparation commit f8237054c6b55e0a318c0f5b1ce820be8c1cc20b (P43MODEREF1-FINAL4) and qualification commit 6c76ad77507ab331640963fb7425e36a7212137d (Q43MODEREF1-FINAL4). I authorize exactly these two independent jobs: M2REF_H1 using input deck SHA256 e3f804510ec777ee210ae46ab56b1bce2576d3e7a12eb91085e9af28f7a41421 with 12,064 physical elements, 36,192 layered elements, 1 CPU, 16 GB memory and 06:00:00 walltime; and M2REF_H2 using input deck SHA256 b6fd1c30253c65cb3d982132c65cd0c8d2960ee0e02ced5114437ee55b7a0cf0 with 33,852 physical elements, 101,556 layered elements, 1 CPU, 32 GB memory and 18:00:00 walltime. Both jobs shall use user subroutine SHA256 5dc005383773a2923b943024b97dc15590a4f220e319fd289c891b15c30844f3, Abaqus 2023, gcc/11.4.0 and intel/2024.2.0, and queue entry_imfdfkmq. MAX_SUBMISSIONS=2 and both jobs may run concurrently. Historical Mode-II H0 job 1378942.mmaster02 is accepted as the coarse convergence point and is not authorized for resubmission. No automatic retries, no replacement submissions, no qmove, no qdel, no MM or PK5 production phase-field run, no additional uniform-reference job, and no downstream job are authorized."*
- **Authorization Record Commit**: `17721c7849edaf0dbe5afbfd30cb4112e4313f88`
- **Submission Authorization Record**: `models/generated/mode_ii/reference_convergence/M2REF_BATCH_SUBMISSION_RECORD.json` (Commit `6a3bd86`)

---

## 2. Preflight Verification & Cluster Forward Sync

- **Cluster Fast-Forward Merge**: Executed `git fetch origin main && git merge --ff-only origin/main` on `tu_freiberg`. Clean fast-forward merge succeeded without dirty path blocks.
- **Reference Contract Validation**: Executed `python3 scripts/validation/validate_mode_ii_reference_contract.py` on cluster -> **`PASS`**.
- **Hash Checks**:
  - `M2REF_H1` input SHA256: `e3f804510ec777ee210ae46ab56b1bce2576d3e7a12eb91085e9af28f7a41421` (**MATCH**)
  - `M2REF_H2` input SHA256: `b6fd1c30253c65cb3d982132c65cd0c8d2960ee0e02ced5114437ee55b7a0cf0` (**MATCH**)
  - `f42_mixed_uel.for` SHA256: `5dc005383773a2923b943024b97dc15590a4f220e319fd289c891b15c30844f3` (**MATCH**)

---

## 3. HPC Job Submissions

Executed guarded submission scripts `submit_m2ref_h1.sh` and `submit_m2ref_h2.sh` on `tu_freiberg`:

1. **Job 1: `M2REF_H1`**:
   - **PBS Job ID**: `1385728.mmaster02`
   - **Queue**: `entry_imfdfkmq` (mapped to `normal_imfdfkmq`)
   - **Resources**: 1 CPU, 16 GB memory, 06:00:00 walltime
   - **Status**: `Q` (Queued / Running)
2. **Job 2: `M2REF_H2`**:
   - **PBS Job ID**: `1385729.mmaster02`
   - **Queue**: `entry_imfdfkmq` (mapped to `normal_imfdfkmq`)
   - **Resources**: 1 CPU, 32 GB memory, 18:00:00 walltime
   - **Status**: `Q` (Queued / Running)

- **Total Submissions**: Exactly 2 jobs (`MAX_SUBMISSIONS=2` consumed).
- **Concurrency**: Both jobs queued independently and running concurrently on HPC.

---

## 4. Current Authority Boundary

- `execution_authorized`: `false` (consumed for this 2-job batch)
- `submission_approved`: `false`
- `maximum_jobs_now`: `0`
- `qsub_called`: `true` (2 calls: `1385728.mmaster02` and `1385729.mmaster02`)
- No replacement, retry, or downstream submissions permitted.
