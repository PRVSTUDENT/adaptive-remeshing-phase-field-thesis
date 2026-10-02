# Mode-II Stage-F Synthetic Topology Benchmark Submission Record

**Task ID**: `F335SUB-M2-STAGE-F-SYNTHETIC-TOPOLOGY-SUBMISSION1`  
**Date**: 21 August 2026  
**Status**: `JOB SUBMITTED / PBS ID 1393159.mmaster02 RECORDED / QUEUED ON CLUSTER (entry_imfdfkmq -> normal_imfdfkmq)`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Executive Summary

Under direct human authorization, the qualified Mode-II Stage-F synthetic topology-transfer validation package (`M2CORR_STAGE_F_TOPOLOGY_CHANGE_TRANSFER_VAL`) was submitted to the HPC cluster as a single governed job.

### Authorized Job & Allocation
- **PBS Job ID**: `1393159.mmaster02`
- **Job Name**: `M2STAGE_F_VAL`
- **Requested Queue**: `entry_imfdfkmq`
- **Routed Execution Queue**: `normal_imfdfkmq`
- **Initial Scheduler State**: `Q` (Queued)
- **Execution Working Directory**: `/home/pr21vyci/Adaptive_remeshing_clean/models/generated/mode_ii/stage_f_topology_batch/M2CORR_STAGE_F_TOPOLOGY_CHANGE_TRANSFER_VAL`
- **Compute Resources**: 1 CPU (`select=1:ncpus=1:mem=16gb`), 16 GB RAM, 24:00:00 walltime
- **Environment Modules**: `gcc/11.4.0`, `intel/2024.2.0`, `abaqus/2023`
- **Submission Wrapper**: `scripts/hpc/qsub_with_submitted_notify.sh`
- **Submissions Consumed**: 1 of 1 permitted (0 additional submissions permitted)

---

## 2. Scientific & Mesh Topology Configuration

- **Scientific Stage**: Stage F / Mode-II Discrete Synthetic Topology Benchmark
- **Scientific Purpose**: `DECISION_A_STAGE_F_PURPOSE = SYNTHETIC_BENCHMARK` (authoritative human decision)
- **Donor Source**: `1390447.mmaster02` (Frame 17, $U_1 = 0.01051289\text{ mm}$, $d_{\max} = 0.304318$)
- **Topology Delta**: Exactly 1 newly separated facet ($\Delta a = 0.002\text{ mm} = 1\times h_{\text{tip}}$) along $y = 0.0\text{ mm}$:
  - Lower flank node: `16962` $(x = 0.002, y = 0.0)$
  - Upper duplicate node: `34028` $(x = 0.002, y = 0.0)$
  - Transition unsplit crack-tip node: `16963` $(x = 0.004, y = 0.0)$
  - Total slit pairs: 57 pairs (56 original + 1 newly separated)
- **Mesh Inventory**:
  - Total Abaqus nodes: 34,029 (34,028 physical continuum + 1 RP 99999)
  - Total Abaqus elements: 67,200 (33,600 U1 Phase UEL + 33,600 U2 Mechanics UEL)
  - Passive CPE4 elements: 0
  - Target Gauss points: 134,400

---

## 3. Pre-Submission Package Hashes Verification (100% Exact Match)

| Package File | Exact Disk SHA-256 | Manifest Hash | Match |
|---|---|---|---|
| `M2CORR_STAGE_F_TOPOLOGY_CHANGE_TRANSFER_VAL.inp` | `168f4fd6777c3e7c110747b800c0565fa93f16fec32e655adf67f2cb3ef470aa` | `168f4fd6...` | True |
| `f44_mixed_uel_restart_stateinit.for` | `62e35f74bbeccd3f5b1ac67312b79211f4ccb75648ae20dbb8985cb577fe1aab` | `62e35f74...` | True |
| `STAGE_D_COMMITTED_STATE.bin` | `c63681b1c0b029f7b3bf5a1ee986e3fabfbbd240cf0bc89a030a811b82a84722` | `c63681b1...` | True |
| `STAGE_F_PRIMARY_STATE_BOUNDARY.inp` | `710702897c6b82f11bb38dd6c3a40f7f7b44236935c563b0cf077d94d5f6cdf1` | `71070289...` | True |
| `STAGE_F_U3_ONLY_BOUNDARY.inp` | `8a619e254ecd379462c6c52461d6caf818f0a16242ba6c881785f37e2417bbd5` | `8a619e25...` | True |
| `abaqus_v6.env` | `5508d0ea56a78675b0ad0b01b256ae34f4d73d3878f0ec397ca8b1e1017ee98e` | `5508d0ea...` | True |
| `MODE_STAGED.flag` | `44aecc3345af89ebdf6c6f22abcab9a76149a562dfc8d6b1ce50968c9318f9a4` | `44aecc33...` | True |
| `submit_job.pbs` | `393b247498e998c280c19410ff0f77779332b30d71bdf32d88a43e5a19c72000` | `393b2474...` | True |
| `PACKAGE_MANIFEST.json` | `978bc742e6b8f7bf2716475ae76fd410276eb347924c04540df353fd7d990c75` | `978bc742...` | True |

---

## 4. Dual-Channel Notification Dispatch Audit

- **Preflight Notification Test**:
  - `EMAIL_TRANSPORT_TEST = PASS` (rc=0 to `pr21vyci@mailserver.tu-freiberg.de` and `Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de`)
  - `TELEGRAM_TRANSPORT_TEST = PASS` (rc=0 via Bot API)
- **Submission Notification Dispatch**:
  - `TELEGRAM_SUBMISSION = PASS` (`telegram_ok event=SUBMITTED job=1393159.mmaster02`)
  - `EMAIL_SUBMISSION = PASS` (mailx dispatch rc=0)
- **PBS Built-in Directives**: `#PBS -m abe` and `#PBS -M pr21vyci@mailserver.tu-freiberg.de` embedded in `submit_job.pbs`.
- **In-Job Lifecycle Hooks**: Sourced `pbs_notify.sh` with `pbs_notify_install_traps`, `pbs_notify_begin`, and `pbs_notify_finish`.

---

## 5. Governed Runtime Acceptance Basis (Preserved)

1. Staged-state ingestion via `UEXTERNALDB` succeeds.
2. Step 1 (`STATE_INSTALL`) completes with zero syntax or state errors.
3. Step 2 (`MECH_EQUILIBRATION`) completes with phase locked and zero displacement drift.
4. Step 3 (`PHASE_RELEASE`) completes under $\Delta t_{\min} = 5.0\times 10^{-12}\text{ s}$ and $I_A = 13$.
5. Step 4 (`CONTINUATION`) is entered under $\Delta t_{\min} = 1.0\times 10^{-11}\text{ s}$ and $I_A = 12$.
6. Pointwise phase irreversibility holds: $0 \le d \le 1$, $\Delta d \ge 0$.
7. Committed history monotonicity holds: $\mathcal{H} \ge 0$, $\mathcal{H}_{n+1} \ge \mathcal{H}_n$.
8. Zero topology-transfer contamination or cross-slit leakage.
9. Full continuation to $U_1 = 0.050\text{ mm}$ is **DIAGNOSTIC_ONLY** / **NOT_PREDECLARED**.
10. Reaction force $RF_1$ comparisons remain **DIAGNOSTIC_ONLY**.
