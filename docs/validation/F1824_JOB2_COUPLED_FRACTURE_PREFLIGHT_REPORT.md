# Task F1824: Job-2 Coupled Phase-Field Fracture Offline Preflight & Deck Audit Report

## Executive Summary

- **Task Identifier**: `F1824-JOB2-COUPLED-FRACTURE-VALIDATION`
- **Correlation ID**: `HND-F1824-JOB2-COUPLED-VALIDATION-001`
- **Predecessor Task**: `F1823-FRAMEWORK-COMPARISON-COARSENING-AND-TARGETED-DONORS` (`HND-F1823-FRAMEWORK-COARSENING-DONORS-001`, **APPROVED**)
- **Assigned Agent**: `gemini-antigravity`
- **Governing Commit**: `87cd5d802d51d13ea7cd732e10dfa30a56dbc90d`
- **Governance & PBS Budget**: Strictly **zero new PBS submissions consumed** (`max_new_pbs_submissions = 0`, `submissions_consumed = 0`); cumulative submissions permanently preserved at **35**.
- **Bitwise Frozen Production UEL**: `models/pandey_kumar_mode1/f42_mixed_uel.for` (SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`).
- **Bitwise Frozen Framework**: `scripts/remeshing/reusable_2d_adaptive_framework.py` (SHA-256: `0578156E5551173307892B8881E4BA772F099187BCF332672F39AC825023E80D`).
- **Governing Mesh Invariant**: F1812 Pareto-Optimal Adapted Meshes across Cases 1, 2, 3, and 5 (total **160,144 physical elements**, **480,432 layered elements**).
- **Current Operational Status**: **PREFLIGHT_COMPLETE_HOLDING_IN_WAIT_FOR_USER_PBS_AUTHORIZATION** (`MASTER_GOAL_STATUS = OPEN`).

---

## 1. Context and Supervisory Decision on Predecessor Task F1823

In Task F1823, independent supervisory review was conducted via the OpenClaw PAD Bridge (`HND-F1823-FRAMEWORK-COARSENING-DONORS-001`). The reviewer officially evaluated and **APPROVED** Task F1823 with the following findings:
1. **Step 1 Framework Parity Verified**: Both framework revisions (`4276A5DC...` and `0578156E...`) generate bitwise-identical meshes under identical resolved kwargs (62,611 elements at 3.0%, Body SHA `D36603D8...`; 25,461 elements at 4.5%, Body SHA `50CB4E3C...`). The 62,611 vs 63,210 difference was confirmed as purely a resolved-arguments difference (`UNIFORM_ERROR` vs `MINIMUM_MAXIMUM`).
2. **Step 1 Case 3 Width Bug Fix Verified**: In `run_f1816_step2_master.py` line 76, the second segment was corrected from `(70, 60)-(120, 60)` to `(50, 60)-(65, 60)` (plate is 65 mm wide). Recomputed concentrations verified.
3. **Step 1 Case 1 $\eta_R = 4.5\%$ Provenance Verified**: Documented as an explicit CLI runtime override in `run_f1812_master.py`.
4. **Step 2 Bounded Coarsening Plateau Verified**: Coarsening ratio plateaus at ~1.56x for Case 2 and ~1.72x for Case 3, both below the 2.0x threshold; F1812 baselines preserved as optimal.
5. **Step 3 Targeted Donor State Ablation Verified**: State 1 is required for notch initiation in Cases 2 and 3; State 4 is required for outer boundary coverage in Case 2; State 3 is uniquely responsible for secondary corridor propagation in Case 3.
6. **Supervisor Next Instruction**:
   > *"Task F1824: Job-2 Coupled Fracture Validation on F1812 Adapted Meshes (CONDITIONAL — requires user authorization to lift max_new_pbs=0). F1823 found no improvement to the adaptive remesh (Gate 06 plateaus below 2.0x; donor states are all required; F1812 baselines preserved). Per the user's 2-day plan ('if nothing improves we proceed with the Job-2 run for all cases'), Job-2 is now the next step. HOWEVER: this instruction is CONDITIONAL. Do NOT submit any PBS job until the user explicitly confirms lifting max_new_pbs=0 and states the PBS budget for Job-2 (number of jobs)... If the user does not authorize the PBS lift, report WAIT and do not proceed. MASTER_GOAL_STATUS stays OPEN."*

---

## 2. Production Input Deck Construction & Architecture

To prepare for Job-2 coupled phase-field fracture simulations without violating the `max_new_pbs_submissions = 0` boundary, all four production input decks were built offline using `ProductionDeckBuilder` in `scripts/remeshing/reusable_2d_adaptive_framework.py`:

```
                       Physical Mesh (Quads + Tris)
                                    │
                                    ▼
       ┌────────────────────────────┼────────────────────────────┐
       │                            │                            │
       ▼                            ▼                            ▼
Layer 1: Phase UEL           Layer 2: Mech UEL           Layer 3: Companion CPE4/3
DOF 3 (Phase d)              DOFs 1, 2 (Displacements)   UMAT Material (d, H, Stress)
Type: U1 (quad), U3 (tri)    Type: U2 (quad), U4 (tri)   SDV Output Capture
```

Each production deck incorporates:
1. **Identical Nodal Coordinates**: Shared physical node set across all 3 layers, plus one reference node `N_RP` at node ID `999999`.
2. **Layer Element Offsets**:
   - Layer 1 (Phase): Element IDs $1 \dots N_{\text{phys}}$
   - Layer 2 (Mechanical): Element IDs $(N_{\text{phys}} + 1) \dots 2N_{\text{phys}}$
   - Layer 3 (Companion): Element IDs $(2N_{\text{phys}} + 1) \dots 3N_{\text{phys}}$
3. **Rigid Kinematic Constraints**: `*EQUATION` constraints tying the pull boundary nodes in DOF 2 to reference node `N_RP` (node 999999).
4. **Step Scheduling**:
   - **Step 1 (Pre-critical linear elastic)**: Resolves initial compliance and stress concentrations up to $u_1$.
   - **Step 2 (Fracture propagation)**: Quasi-static damage evolution up to ultimate failure displacement $u_2$.
5. **Frame-by-Frame Output**:
   - `*OUTPUT, FIELD, FREQUENCY=1`
   - `*ELEMENT OUTPUT, ELSET=umatelem: MISESERI, MISESAVG, S, E, SDV`
   - Guarantees complete capture of damage $d$ (`SDV1`), crack history $H$ (`SDV2`), and recovered stresses.

---

## 3. Discretization Audit Across All Four Benchmarks

| Benchmark Case | Physical Mesh Source INP | Physical Elements | Quad Fraction | Total Layered Elements | Production Deck Size (Bytes) | Production Deck SHA-256 |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Case 1**: Single-Edge Notched Plate (Sec 4.1) | `models/pandey_kumar_mode1/261_f1812_crack_path_refinement/case1/PK_F1812_CASE_1_ADAPT_PHYS.inp` | 25,461 | 97.29% | 76,383 | 3,503,345 | `A9F817983D48CEE3BF590380E908D752A09A614017FEB98C9E0B8A7101F0A4C1` |
| **Case 2**: Off-Axis Hole Plate (Sec 4.4) | `models/pandey_kumar_mode1/261_f1812_crack_path_refinement/case2/PK_F1812_CASE_2_ADAPT_PHYS.inp` | 41,438 | 97.57% | 124,314 | 5,828,189 | `581D2A78D63456B5AD9148EA1FBA982FC6805BE8FA790FB20CF5A203DAC7D1AD` |
| **Case 3**: Notched Plate with Pins (Sec 4.3) | `models/pandey_kumar_mode1/261_f1812_crack_path_refinement/case3/PK_F1812_CASE_3_ADAPT_PHYS.inp` | 77,779 | 97.34% | 233,337 | 11,144,240 | `36760C514A490B5A355139B0F0CD06A6ABA8E52706DAE4EC7535C544563E5BC8` |
| **Case 5**: Seven-Hole Plate (Sec 4.6) | `models/pandey_kumar_mode1/261_f1812_crack_path_refinement/case5/PK_F1812_CASE_5_ADAPT_PHYS.inp` | 15,466 | 97.90% | 46,398 | 2,095,855 | `D50108CE9C20585366A264C02F8F75F24B64627024599092D9AD6C425ED2AF93` |
| **Total Campaign** | — | **160,144** | **97.45%** | **480,432** | **22,571,629** | — |

---

## 4. Technical Preflight & Safety Audits

1. **Abaqus Card Line-Wrapping Audit (Buffer Overflow Protection)**:
   - Abaqus standard parser truncates input lines with excessive tokens.
   - All `*NSET` cards in all four production input decks were scanned for line length.
   - **Result**: Exactly **0 lines** exceed 16 node entries across all 22.5 MB of input decks (**PASS**).
2. **User Subroutine Hash Verification**:
   - Each case directory has an exact copy of `f42_mixed_uel.for`.
   - Verified SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` (**PASS**).
3. **Dual-Channel Notification Integration**:
   - PBS scripts incorporate `#PBS -m abe` and `#PBS -M pr21vyci@mailserver.tu-freiberg.de`.
   - PBS scripts source `job_notifications.sh` and install the terminal trap (`notification_install_terminal_trap`).
4. **Atomic Directory Locking**:
   - Each PBS script creates an atomic directory lock (`${JOB_NAME}.lock`) to prevent concurrent collision.

---

## 5. PBS Submission Scripts & Cluster Staging Specification

| Case | PBS Script Path | Job Name | Queue | Walltime | CPUs | Memory | Scratch Run Directory |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| Case 1 | `models/pandey_kumar_mode1/268_f1824_job2_preflight/case1/submit_case1_job2.pbs` | `F1824_C1_FRAC` | `normal_imfdfkmq` | 08:00:00 | 1 | 16 GB | `/scratch9/pr21vyci/runs/mode1_pk_f1824_job2_batch/case1_mode1_edge_crack` |
| Case 2 | `models/pandey_kumar_mode1/268_f1824_job2_preflight/case2/submit_case2_job2.pbs` | `F1824_C2_FRAC` | `normal_imfdfkmq` | 08:00:00 | 1 | 16 GB | `/scratch9/pr21vyci/runs/mode1_pk_f1824_job2_batch/case2_off_axis_hole` |
| Case 3 | `models/pandey_kumar_mode1/268_f1824_job2_preflight/case3/submit_case3_job2.pbs` | `F1824_C3_FRAC` | `normal_imfdfkmq` | 12:00:00 | 1 | 16 GB | `/scratch9/pr21vyci/runs/mode1_pk_f1824_job2_batch/case3_notched_plate_pins` |
| Case 5 | `models/pandey_kumar_mode1/268_f1824_job2_preflight/case5/submit_case5_job2.pbs` | `F1824_C5_FRAC` | `normal_imfdfkmq` | 08:00:00 | 1 | 16 GB | `/scratch9/pr21vyci/runs/mode1_pk_f1824_job2_batch/case5_seven_hole` |

---

## 6. Artifact Registry & Provenance

| Artifact Identifier | Type | Repo-Relative File Path | Size (Bytes) | SHA-256 Checksum |
| :--- | :--- | :--- | :---: | :--- |
| `SCRIPT_F1824_PREFLIGHT` | Python Script | `scripts/remeshing/run_f1824_job2_preflight.py` | 13,858 | `295ACF16A914488A01683933C40EF5C170B1F54B0EEBC6D428489CEEF9B69B75` |
| `TEST_F1824_PREFLIGHT` | Unit Test | `tests/unit/test_f1824_job2_preflight.py` | 5,593 | `4FEA74BE0D12D83B895C989C942006F799636253457F817112EB114D35591C62` |
| `DECK_F1824_CASE1` | Abaqus INP | `models/pandey_kumar_mode1/268_f1824_job2_preflight/case1/PK_F1824_CASE_1_PROD.inp` | 3,503,345 | `A9F817983D48CEE3BF590380E908D752A09A614017FEB98C9E0B8A7101F0A4C1` |
| `DECK_F1824_CASE2` | Abaqus INP | `models/pandey_kumar_mode1/268_f1824_job2_preflight/case2/PK_F1824_CASE_2_PROD.inp` | 5,828,189 | `581D2A78D63456B5AD9148EA1FBA982FC6805BE8FA790FB20CF5A203DAC7D1AD` |
| `DECK_F1824_CASE3` | Abaqus INP | `models/pandey_kumar_mode1/268_f1824_job2_preflight/case3/PK_F1824_CASE_3_PROD.inp` | 11,144,240 | `36760C514A490B5A355139B0F0CD06A6ABA8E52706DAE4EC7535C544563E5BC8` |
| `DECK_F1824_CASE5` | Abaqus INP | `models/pandey_kumar_mode1/268_f1824_job2_preflight/case5/PK_F1824_CASE_5_PROD.inp` | 2,095,855 | `D50108CE9C20585366A264C02F8F75F24B64627024599092D9AD6C425ED2AF93` |
| `PBS_F1824_CASE1` | Shell Script | `models/pandey_kumar_mode1/268_f1824_job2_preflight/case1/submit_case1_job2.pbs` | 4,061 | `6245FB5AA8B61E5990BB2A1FA22B17AB9AAC1CD85A38669A6788531497FCC4D3` |
| `PBS_F1824_CASE2` | Shell Script | `models/pandey_kumar_mode1/268_f1824_job2_preflight/case2/submit_case2_job2.pbs` | 4,055 | `52316EF05DC7E2591D489F0AB0C10DC241DEEBC7FE1FBEB78656CF139AFCDF5C` |
| `PBS_F1824_CASE3` | Shell Script | `models/pandey_kumar_mode1/268_f1824_job2_preflight/case3/submit_case3_job2.pbs` | 4,065 | `ED58B6EB160425F55733BBB3DBBC750F47EA14CA4771881D426608BA33244B9B` |
| `PBS_F1824_CASE5` | Shell Script | `models/pandey_kumar_mode1/268_f1824_job2_preflight/case5/submit_case5_job2.pbs` | 4,049 | `9D2F975786DA7B78C5D6499580C079BF85EC0373B2ECFE21CB6BC7A8DDC1888E` |
| `SUMMARY_F1824_PREFLIGHT` | JSON | `models/pandey_kumar_mode1/268_f1824_job2_preflight/job2_preflight_summary.json` | 4,505 | `359E695B4679F39313C4AB1856CA1DABEE8E5F3356FEEC30A468530BC03B9737` |
| `RECEIPT_F1824_PREFLIGHT` | JSON | `models/pandey_kumar_mode1/268_f1824_job2_preflight/PK_F1824_JOB2_PREFLIGHT_RECEIPT.json` | 1,844 | `B81683809CD6157DAF149BBAC503A2CADD1F8323874D0AC1CB0961388C11E202` |

---

## 7. Operational Status and Next Actions

- **Current State**: Task F1824 offline preflight is 100% complete and verified. All 4 production input decks, UEL subroutine copies, and PBS execution scripts are staged and qualified.
- **Holding Directive**: Holding in **WAIT** state awaiting user explicit PBS execution authorization.
- **Required User Input**: Confirmation to lift `max_new_pbs_submissions = 0` and designation of the PBS execution budget (e.g., number of parallel jobs, 2 or 4).
- **Execution Mechanism**: Upon user confirmation, jobs will be submitted through `scripts/hpc/Invoke-Mode1Execution.ps1` with strict once-only accounting, zero credential loops, and real dual-channel notifications.
- **Master Continuation Goal**: `MASTER_GOAL_STATUS = OPEN`.
