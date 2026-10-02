# Session Log: Mode-II Stage-F Synthetic Topology Benchmark Submission

- **Task ID**: `F335SUB-M2-STAGE-F-SYNTHETIC-TOPOLOGY-SUBMISSION1`
- **Agent**: `gemini-antigravity`
- **Date**: 2026-08-21
- **Status**: `STAGE_F_SYNTHETIC_BENCHMARK_SUBMITTED_RUNNING`

---

## 1. Human Authorization & Submission Execution

- **Authorization Received**: Human explicitly authorized submission of exactly ONE PBS job for package `models/generated/mode_ii/stage_f_topology_batch/M2CORR_STAGE_F_TOPOLOGY_CHANGE_TRANSFER_VAL`.
- **Submission Wrapper**: `scripts/hpc/qsub_with_submitted_notify.sh`
- **Captured PBS Job ID**: `1393159.mmaster02`
- **Submissions Count**: 1 of 1 (strictly enforced, 0 additional submissions).

---

## 2. Immediate Scheduler Verification (`qstat -x 1393159.mmaster02`)

- **Job ID**: `1393159.mmaster02`
- **Job Name**: `M2STAGE_F_VAL`
- **Job State**: `Q` (Queued)
- **Requested Queue**: `entry_imfdfkmq` (`PBS_O_QUEUE=entry_imfdfkmq`)
- **Routed Execution Queue**: `normal_imfdfkmq` (`queue = normal_imfdfkmq`)
- **Server**: `mmaster02`
- **Resources**: `select=1:ncpus=1:mem=16gb`, `walltime=24:00:00`
- **Working Directory**: `/home/pr21vyci/Adaptive_remeshing_clean/models/generated/mode_ii/stage_f_topology_batch/M2CORR_STAGE_F_TOPOLOGY_CHANGE_TRANSFER_VAL`

---

## 3. Package & State Verification

- **Package Hashes**: 100% exact match against `PACKAGE_MANIFEST.json` across all 8 files on disk and cluster.
- **Canonical UEL**: SHA-256 `62e35f74bbeccd3f5b1ac67312b79211f4ccb75648ae20dbb8985cb577fe1aab`.
- **Staged Mode**: `MODE_STAGED.flag` and `STAGE_D_COMMITTED_STATE.bin` (6,400,016 bytes) verified with fail-closed UEXTERNALDB state ingestion.
- **Topology Delta**: Exactly 1 newly separated facet ($\Delta a = 0.002\text{ mm}$), nodes `16962` / `34028`, tip node `16963` (57 slit pairs).

---

## 4. Dual-Channel Notification Status

- **Telegram Submission Notification**: Dispatched via `qsub_with_submitted_notify.sh` (`telegram_ok event=SUBMITTED job=1393159.mmaster02`).
- **Email Submission Notification**: Dispatched via `notify_hpc_event.py` (`rc=0` via mailx).
- **PBS In-Job Notifications**: `#PBS -m abe` active; `pbs_notify.sh` lifecycle hooks active in `submit_job.pbs`.
