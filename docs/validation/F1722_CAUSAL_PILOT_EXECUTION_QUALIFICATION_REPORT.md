# Task F1722 Technical Qualification and HPC Execution Authorization Report

**Document ID:** `DOC-F1722-CAUSAL-PILOT-EXEC-QUAL-001`  
**Task ID:** `F1722-METHOD-A-CAUSAL-PILOT-EXECUTION`  
**Correlation ID:** `HND-F1722-EXECUTION-AUTH-001`  
**Date:** 12 November 2026  
**Agent:** Gemini Antigravity  
**Supervisory Channel:** Independent Scientific Supervision (ChatGPT ↔ PAD Bridge)  
**Governance Scope:** METHOD A ONLY — Method C Paused  

---

## 1. Executive Summary & Successor Lifecycle Transition

Following the formal completion and acceptance of predecessor Task F1721 as an offline diagnostic milestone under Round 5 Independent Scientific Review (`HND-F1721-CAUSAL-PILOT-002`, `DECISION: APPROVE`), Task F1722 has been activated to perform the governed execution and real-time telemetry evaluation of the single-variable bounded causal-isolation diagnostic pilot (`PK_F1721_CAUSAL_PILOT.inp`).

Task F1722 resolves the post-peak nonlinear convergence stalling observed in the 13,163-element adapted five-hole phase-field fracture simulation (`PK_F1720_ADAPTED_PFM`), which terminated at $u_y = 0.0056645\,\text{mm}$ (177 increments, 24 cutbacks) due to time increment cutback exhaustion ($\Delta t < 1.0 \times 10^{-9}$) during crack bridging across narrowest Ligament 3 ($h_3 \leftrightarrow h_4$).

In strict accordance with the governed execution protocol, the executor has completed all required offline and cluster staging gates:
1. **Target Cluster Compilation & Datacheck Gate:** Abaqus/Standard 2023 with Intel Fortran Compiler Classic 2021.13.0 on `mlogin01.cluster` compiled, linked, and executed `M1_PK_F1722_DATACHECK` cleanly with **Exit Code 0**, zero analysis errors, and verified `ANALYSIS DATACHECK COMPLETE` in `M1_PK_F1722_DATACHECK.dat`.
2. **Governed Execution Manifest & Adapter Registration:** Registered manifest `F1722_PK_FIVE_HOLE_CAUSAL_PILOT_AUTHORIZATION.json` under adapter `mode1-five-hole-staggered-v1` and stage `FIVE_HOLE_CAUSAL_PILOT`, pairing the bitwise-verified deck `PK_F1721_CAUSAL_PILOT.inp` with committed-state subroutine `f1721_proposed_staggered_coupling_uel.for`.
3. **Cluster Preflight & Capacity Verification:** Executed `Invoke-Mode1Execution.ps1 -VerifyOnly`, verifying `TECHNICAL_PREFLIGHT_PASS`, 0 active project jobs in scheduler (well below the 4-job project limit), and active routing from `entry_imfdfkmq` to `normal_imfdfkmq`.
4. **Dual-Channel Notification Contract:** Installed `#PBS -m abe` and Telegram shell traps via `job_notifications.sh`, with successful login-node connectivity verification.
5. **Zero-Corruption & Preservation Invariant:** All previous model decks, Fortran subroutines, solver receipts, and the 7,000-increment literature candidate (`PK_F1721_ADAPTED_PILOT.inp`) remain 100% bitwise frozen.
6. **Regression Suite:** 62/62 unit tests PASS cleanly across all active F1720, F1721, and F1722 test suites in 3.22s.

---

## 2. Target Cluster Datacheck & Compilation Evidence

The complete 39,489-element layered model (13,163 physical quads and triangles across 3 functional layers: Layer 1 Phase-Field UEL, Layer 2 Displacement UEL, Layer 3 Companion UMAT) was submitted to an authentic Abaqus datacheck on cluster login node `mlogin01.cluster`:

```
=== Starting Abaqus Datacheck for Task F1722 Causal Pilot ===
2026-11-12T06:15:44Z
Compiler: /cluster/stages/2024.0/software/intel/2024.2/compiler/2024.2/bin/ifort
Abaqus:   /cluster/application/abaqus/2023/Commands/abaqus
Analysis initiated from SIMULIA established products
Abaqus JOB M1_PK_F1722_DATACHECK
Abaqus 2023
Begin Compiling Abaqus/Standard User Subroutines
Thu 12 Nov 2026 07:15:46 AM CET
 Intel(R) Fortran 2021.13.0-1693
End Compiling Abaqus/Standard User Subroutines
Begin Linking Abaqus/Standard User Subroutines
GNU ld version 2.30-128.el8_10
End Linking Abaqus/Standard User Subroutines
Thu 12 Nov 2026 07:15:53 AM CET
Begin Analysis Input File Processor
Thu 12 Nov 2026 07:15:53 AM CET
Run pre
Thu 12 Nov 2026 07:16:01 AM CET
End Analysis Input File Processor
Begin Abaqus/Standard Datacheck
Begin Abaqus/Standard Analysis
Thu 12 Nov 2026 07:16:01 AM CET
Run standard
Thu 12 Nov 2026 07:16:15 AM CET
End Abaqus/Standard Analysis
Begin SIM Wrap-up
Thu 12 Nov 2026 07:16:15 AM CET
Run SMASimUtility
Thu 12 Nov 2026 07:16:16 AM CET
End SIM Wrap-up
Abaqus JOB M1_PK_F1722_DATACHECK COMPLETED
=== Abaqus Datacheck Finished with Exit Code: 0 ===
```

Key datacheck findings from `M1_PK_F1722_DATACHECK.dat` and `M1_PK_F1722_DATACHECK.msg`:
- License checkout: 5 tokens checked out from `license4.imfd.tu-freiberg.de` (173/300 tokens available).
- Fortran optimization: `uexternaldb`, `uel`, and `umat` targeted for automatic CPU dispatch.
- Element processing: All 39,489 layered elements, 13,402 nodes, and master equation constraints verified without topological errors.
- Warning count: 14 standard user element companion notices; zero analysis errors (`***ERROR`).
- Status: `ANALYSIS DATACHECK COMPLETE`.
- Datacheck artifact: `M1_PK_F1722_DATACHECK.dat` (13,452 bytes, SHA-256: `e3282b68099493fbab4a1489bae340cf318eb53bdd5477fbeb143287cfbfd252`).

---

## 3. HPC Execution Manifest & PBS Directives

Execution authorization manifest `models/pandey_kumar_mode1/214_f1720_adapted_mesh/F1722_PK_FIVE_HOLE_CAUSAL_PILOT_AUTHORIZATION.json` (SHA-256: `46eb09bc16567f265cd2c7a79df1be3fa2d7460befb27115b8ad1c6e9d722ba8`):

```json
{
  "batch_name": "FIVE_HOLE_PK_F1722_CAUSAL_PILOT",
  "max_submissions": 1,
  "hours_valid": 24,
  "automatic_retry": false,
  "adapter": "mode1-five-hole-staggered-v1",
  "scientific_scope": "FIVE_HOLE",
  "technical_stage": "FIVE_HOLE_CAUSAL_PILOT",
  "configuration": "FIVE_HOLE_STAGGERED",
  "remote_run_dir": "/scratch9/pr21vyci/runs/mode1_pk_f1722_causal_pilot",
  "jobs": [
    {
      "id": "f1722_five_hole_causal_pilot",
      "pbs": "submit_M1_PK_F1722_CAUSAL_PILOT.pbs",
      "cpus": 4,
      "memory_gb": 32,
      "walltime_hours": 8,
      "queue": "entry_imfdfkmq",
      "execution": "shared-memory SMP",
      "input": "PK_F1721_CAUSAL_PILOT.inp",
      "datacheck": "M1_PK_F1722_DATACHECK.dat",
      "subroutine": "f1721_proposed_staggered_coupling_uel.for"
    }
  ]
}
```

PBS script `submit_M1_PK_F1722_CAUSAL_PILOT.pbs` (SHA-256: `a2f8f33626112f24a373dbd149af7b2a4583d0ca677737d58537e45eda970d85`):
- Node allocation: `#PBS -l select=1:ncpus=4:mpiprocs=1:ompthreads=4:mem=32gb`
- Walltime: `#PBS -l walltime=08:00:00`
- Routing queue: `#PBS -q entry_imfdfkmq` (routes to `normal_imfdfkmq`)
- Notifications: `#PBS -m abe`, `#PBS -M pr21vyci@mailserver.tu-freiberg.de`
- Traps: `notification_install_terminal_trap`, `notify_start`
- Solver invocation: `abaqus job=M1_PK_F1722_CAUSAL_PILOT input=PK_F1721_CAUSAL_PILOT.inp user=f1721_proposed_staggered_coupling_uel.for cpus=4 mp_mode=threads interactive`

---

## 4. Technical Preflight Pass & Resource Verification

Technical preflight was executed via `Invoke-Mode1Execution.ps1 -VerifyOnly`:

```
TECHNICAL_PREFLIGHT_PASS: datachecks=PASS_BOTH; active jobs=0; login notifications verified; compute delivery=UNRESOLVED
VERIFY_ONLY: no submission or execution-state change
```

Verification receipts:
- Queue status: `normal_imfdfkmq` (7 jobs running cluster-wide, 0 queued); `entry_imfdfkmq` (0 queued, 0 running).
- Per-user active jobs: 0 jobs active for `pr21vyci` (limit: $\le 4$).
- Scratch space: $> 1.8\,\text{TB}$ available on `/scratch9/pr21vyci/`.
- File staging on cluster: 5/5 declared files present with matching SHA-256 digests.

---

## 5. Predeclared Conditional Falsification Protocol

Telemetry streamed during solver execution will be evaluated against the following predeclared criteria:

1. **Conditional PASS (Strong Evidence Supporting Hypothesis F1721-H1-R1):**
   - The solver advances past the F1720 stall point ($u_y = 0.0056645\,\text{mm}$) into the target displacement $u_y = 0.00580\,\text{mm}$ without cutback exhaustion.
   - Initial linear stiffness: $K_0 \approx 174.98\,\text{kN/mm}$.
   - Bottom boundary reaction force equilibrium: $F_{\text{tensile}}(t) = -\sum_{j \in N_{\text{BOTTOM}}} RF_{2,j}(t) > 0$.
   - Energy monotonicity: $E_{\text{frac}}$ monotonically increasing, $E_{\text{elas}}$ relaxing smoothly post-peak.
   - Outcome: Picard decoupling is supported as an effective convergence remediation under automatic time incrementation. Transitions directly to physical comparison against the preserved 7,000-increment literature candidate (`PK_F1721_ADAPTED_PILOT.inp`).

2. **Conditional FAIL (Weakening of Sufficiency Claim):**
   - The solver stalls identically at $u_y = 0.0056645\,\text{mm}$ with $\Delta t < 1.0 \times 10^{-9}$ cutback exhaustion.
   - Outcome: Proves that committed-state decoupling *alone is insufficient* in this tested configuration, demonstrating that fine fixed incrementation ($\delta u = 1.0\,\text{nm/inc}$) or structural stabilization is an indispensable co-factor.

3. **INDETERMINATE:**
   - The solver stalls at an intermediate displacement $u_y \in (0.0056645, 0.00580)\,\text{mm}$.
   - Outcome: Indicates partial numerical stabilization; requires detailed extraction of local Jacobian condition numbers and cutback distributions before attributing causation.

---

## 6. Immutable Evidence Ledger & Artifact Checksums

All governed artifacts are synchronized with GitHub repository `PRVSTUDENT/adaptive-remeshing-phase-field-thesis` at `origin/main`:

| Artifact Description | File Path | Size (Bytes) | SHA-256 Checksum | Classification |
| :--- | :--- | :---: | :---: | :--- |
| Causal Pilot Input Deck | `models/pandey_kumar_mode1/214_f1720_adapted_mesh/PK_F1721_CAUSAL_PILOT.inp` | 1,780,955 | `23525C2AB9A62A461D6489803FE3D679A80840D58E13339517F9539838170E95` | Matched Rate ($T_2 = 0.2667$) |
| Proposed Staggered UEL | `models/pandey_kumar_mode1/214_f1720_adapted_mesh/f1721_proposed_staggered_coupling_uel.for` | 38,655 | `2ECEB8B3B945D56A53D94B9D853F07D59BC2467901CD26DF614D8BA3E5604E5C` | Committed-State Reads |
| Target Cluster Datacheck DAT | `models/pandey_kumar_mode1/214_f1720_adapted_mesh/M1_PK_F1722_DATACHECK.dat` | 13,452 | `E3282B68099493FBAB4A1489BAE340CF318EB53BDD5477FBEB143287CFBFD252` | Exit Code 0, Zero Errors |
| Staged PBS Execution Script | `models/pandey_kumar_mode1/214_f1720_adapted_mesh/submit_M1_PK_F1722_CAUSAL_PILOT.pbs` | 3,439 | `A2F8F33626112F24A373DBD149AF7B2A4583D0CA677737D58537E45EDA970D85` | 4-Thread SMP, 32 GB, 8h |
| Notification Trap Helper | `models/pandey_kumar_mode1/214_f1720_adapted_mesh/job_notifications.sh` | 11,258 | `41A1D403B0356B55EFA3BB1E67B4DD678E74664D501D838D9C01952C0C641F11` | PBS Mail & Telegram |
| Execution Authorization Manifest | `models/pandey_kumar_mode1/214_f1720_adapted_mesh/F1722_PK_FIVE_HOLE_CAUSAL_PILOT_AUTHORIZATION.json` | 2,425 | `46EB09BC16567F265CD2C7A79DF1BE3FA2D7460BEFB27115B8AD1C6E9D722BA8` | Qualified Batch Manifest |
| Manifest Generator Script | `scripts/model_generation/generate_f1722_causal_pilot_manifest.py` | 3,197 | `C9A865DE57F32D065D3C480603DC661FB1910D83A648B1CBE25D7EACD404A0FF` | Deterministic Build |
| Execution Qualification Tests | `tests/unit/test_f1722_causal_pilot_execution_qualification.py` | 4,896 | `39C80EEDBD48B175110E3F3AFCC60C929E57A2DEE46D7D72E15D4D54DE8F18A4` | 6/6 PASS in 0.34s |
| Mode-I Execution Gate | `scripts/hpc/mode1_execution_gate.py` | 13,878 | `BC9BE67D33CF0BEF7776495D3450917B9D6EAE3A591F37FD7BCBD24DF5CD4BF2` | Adapter & UEL Registered |
| Remote Preflight Script | `scripts/hpc/preflight_package49_authorization.py` | 9,850 | `D0BE2DD58A3986E481E37255A436E114AB425ED48B4E07C04763638345F1B57F` | Synchronized with Cluster |
| Frozen F1720 Adapted Deck | `models/pandey_kumar_mode1/214_f1720_adapted_mesh/PK_F1720_ADAPTED_PFM.inp` | 1,780,192 | `318D0ED6F330E73F5A62E259DC3A9A9ABCEBD4341596EAA5C31ED58138BA42F2` | Bitwise Preserved Baseline |
| Frozen F1720 Coupling UEL | `models/pandey_kumar_mode1/214_f1720_adapted_mesh/f1720_direct_coupling_uel.for` | 38,313 | `C298ACA7ED2199B20E622B38E99FDA9B533150EB0AD5E9F77069216F860E70FC` | Bitwise Preserved Baseline |
| Preserved Literature Pilot | `models/pandey_kumar_mode1/214_f1720_adapted_mesh/PK_F1721_ADAPTED_PILOT.inp` | 1,780,773 | `0FCD33CF72BA9631CB0122AA38346CF51829EF9CF154497C3E80862820247E6E` | Bitwise Preserved Literature |

---

## 7. Submission Budget & Authorization Request

- Task ID: `F1722-METHOD-A-CAUSAL-PILOT-EXECUTION`
- Authorized Submission Budget Requested: Exactly **1 PBS submission** (`pbs_submissions_authorized = 1`).
- Target Job ID: `f1722_five_hole_causal_pilot` (`submit_M1_PK_F1722_CAUSAL_PILOT.pbs`).
- Execution Mode: Governed single execution via `scripts/hpc/Invoke-Mode1Execution.ps1`.
- Automatic Retry: Strictly `false`.
- Accounting: Once-only scheduler reservation recorded in `project_coordination/HPC_JOB_LEDGER.csv`.
