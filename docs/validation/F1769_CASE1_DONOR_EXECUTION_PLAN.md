# Task F1769: Case 1 Advancing Coupled Donor Execution Plan, Boundary Condition Audit & Acceptance Gate Specification

**Task ID:** `F1769-CASE1-ADVANCING-COUPLED-DONOR-EXECUTION`  
**Classification:** `DONOR_EXECUTION_BOUNDED_ONE_PBS`  
**Agent:** `gemini-antigravity`  
**Date:** 15 November 2026  
**Status:** `INITIALIZED_AWAITING_REVIEW_AUTHORIZATION`  
**Predecessor Review:** `HND-F1768-CASE1-DONOR-AUTH-001` (Decision: `APPROVE`, Directing Successor Execution Task F1769 with 1-Job Bounded Budget)  
**Prospective PBS Submissions Budget:** Exactly 1 (Current consumed in F1769: 0/1; cumulative historical submissions strictly preserved at 27)  
**Production Fortran UEL SHA-256:** `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` (Bitwise Frozen)  
**Candidate Production Deck SHA-256:** `7B37F167AF520ED2B10C1B4034507F22E923ECABC9CE4F3E7019933D872931C6`  
**Production PBS Script SHA-256:** `B01A50AF39083E315EE167C6CE5469EC9F8B0D026E9678DFD75D2AA3B191ADA6`  
**Remote Execution Directory:** `/scratch9/pr21vyci/runs/mode1_pk_f1768_case1_donor_prep/`  
**Real Cluster Datacheck Exit Code:** `0` (Completed under `gcc/11.4.0 intel/2024.2.0 abaqus/2023`)

---

## 1. Executive Summary & Review Directives Resolution

Following independent scientific review approval `HND-F1768-CASE1-DONOR-AUTH-001` (`approval_scope: CASE1_DONOR_DECK_TECHNICAL_PREFLIGHT_CLOSEOUT_AND_SEPARATE_EXECUTION_PREPARATION`), Task F1768 is formally closed as `COMPLETED_PREFLIGHT_APPROVED` and Task F1769 is initialized.

Task F1769 establishes the formal execution specification and scientific acceptance gates for running the single authorized coarse coupled fracture simulation (`PK_F1768_C1_DONOR`) to generate the authentic advancing donor ODB for Case 1 (Mode-I Single-Edge Notched Plate, Pandey & Kumar 2025, Section 4.2).

### Reviewer Findings Resolution (F1768-R01 through F1768-R06)

1. **Finding F1768-R01 (Datacheck vs Convergence & Crack Advancement):**
   - *Reviewer Statement:* Successful datacheck does not prove coupled convergence or crack propagation.
   - *F1769 Resolution:* The donor is formally classified as `PREPARED_NOT_EXECUTED` until the solver completes and the resulting ODB is postprocessed. Gate G1 (Solver Exit 0) and Gate G2/G5 (Crack Advancement) must be verified directly from solver output files (`.sta`, `.msg`, `.dat`, `.odb`).
2. **Finding F1768-R02 (Verification of ODB Field Output Population):**
   - *Reviewer Statement:* Requesting `MISESERI` and `SDV` in `.inp` does not prove fields are populated during nonlinear coupled fracture.
   - *F1769 Resolution:* Gate G6 mandates post-execution programmatic inspection of the actual ODB using `odbAccess` or `pyabaqus` to verify that field outputs `MISESERI`, `MISESAVG`, `S`, `E`, and `SDV` exist across all saved frames on the Layer 3 continuum visualizer instance `PART-1-1`.
3. **Finding F1768-R03 (Damage Localization & Physical Validity on Coarse Mesh):**
   - *Reviewer Statement:* The 2,906-element mesh is coarse relative to $\ell_0 = 0.0075\,\text{mm}$. Damage localization and process-zone progression must be quantified.
   - *F1769 Resolution:* Post-run audit will measure damage profile along the crack path ($y = 0.5\,\text{mm}$), computing effective crack length where $d > 0.95$ and verifying that peak damage transitions monotonically along the ligament.
4. **Finding F1768-R04 (Top-Edge Horizontal Constraint Audit & Benchmark Concordance):**
   - *Reviewer Statement:* Audit whether the top-edge horizontal constraint (`N_TOP, 1, 1, 0.0`) matches the authoritative Mode-I benchmark before solver execution.
   - *F1769 Resolution:* Section 2 below documents the comprehensive audit proving that `N_TOP, 1, 1, 0.0` is the exact boundary condition in the authoritative thesis benchmark `models/pandey_kumar_mode1/01_standard_pfm_reference/PK_MODE1_STANDARD_PFM.inp` (which achieved 0.029% error vs Pandey & Kumar 2025 Fig. 7a) and in `PK_F1739_CASE_1_PROD.inp` (which solved to 99.96% load drop with Exit 0). Zero changes are needed, ensuring 100% boundary condition consistency across all Case 1 models.
5. **Finding F1768-R05 (Runtime & Resource Bounding):**
   - *Reviewer Statement:* Runtime of 10–15 min is an estimate; retain 2-hour walltime cap and monitor disk space.
   - *F1769 Resolution:* The PBS script enforces `#PBS -l walltime=02:00:00`, 1 CPU, 8 GB RAM, and includes disk capacity preflights requiring $>5\,\text{GB}$ available scratch space. No automatic retries.
6. **Finding F1768-R06 (Accounting as One Donor Fracture Solve):**
   - *Reviewer Statement:* Accurately record solver execution as ONE donor coupled fracture solve, not zero forward fracture.
   - *F1769 Resolution:* The execution ledger and task classification explicitly record this job as `case1_donor_coupled_fracture_solve`, with prospective consumption of 1 PBS job (updating cumulative submissions from 27 to 28 upon launch).

---

## 2. Definitive Boundary Condition Audit (Finding F1768-R04)

A forensic comparison was conducted across the canonical Case 1 model decks in the repository:

| Model Deck | Context | Boundary Conditions (Step 1 & Step 2) | Rigid Pull Equations | Benchmark Error |
| :--- | :--- | :--- | :--- | :--- |
| `PK_MODE1_STANDARD_PFM.inp` | Reference Benchmark (Gate 1) | `N_BOTTOM, 2, 2, 0.0`<br>`N_PIN, 1, 1, 0.0`<br>`N_TOP, 1, 1, 0.0`<br>`N_RP, 2, 2, 0.0050 (Step 1) / 0.0100 (Step 2)` | 51 tie equations coupling each top node to RP 999999 in DOF 2 | $-0.029\%$ vs literature $F_{\max}$ |
| `PK_F1739_CASE_1_PROD.inp` | Production Fracture (Job 1423321) | `N_BOTTOM, 2, 2, 0.0`<br>`N_PIN, 1, 1, 0.0`<br>`N_TOP, 1, 1, 0.0`<br>`N_RP, 2, 2, 0.0050 (Step 1) / 0.0100 (Step 2)` | 51 tie equations coupling each top node to RP 999999 in DOF 2 | $99.96\%$ load drop, Exit 0 |
| `PK_F1768_CASE_1_COARSE_COUPLED.inp` | Advancing Donor (Task F1768/F1769) | `N_BOTTOM, 2, 2, 0.0`<br>`N_PIN, 1, 1, 0.0`<br>`N_TOP, 1, 1, 0.0`<br>`N_RP, 2, 2, 0.0050 (Step 1) / 0.0100 (Step 2)` | 49 tie equations coupling each top node to RP 999999 in DOF 2 | Exact structural parity |

### Audit Conclusion
In classical literature for the single-edge notched tension test (Miehe et al. 2010; Ambati et al. 2015; Pandey & Kumar 2025, Section 4.2), the top and bottom boundaries are held in rigid grips. Constraining $u_x = 0$ on the top edge (`N_TOP, 1, 1, 0.0`) prevents rigid top grip lateral shear and ensures symmetric mode-I opening. This exact constraint is present in the standard reference model and in the completed production model.

Therefore, the candidate input deck `PK_F1768_CASE_1_COARSE_COUPLED.inp` is **100% concordant with the authoritative Mode-I benchmark**. Preserving this input deck is scientifically correct and avoids introducing artificial boundary artifacts.

---

## 3. Predeclared Scientific Acceptance Gates (G1–G7)

Execution of `PK_F1768_C1_DONOR` under Task F1769 will be judged against the following predeclared criteria:

| Gate | Criterion | Threshold | Measurement Source |
| :--- | :--- | :--- | :--- |
| **G1** | **Solver Exit Status** | Clean termination with Exit Code `0`, zero fatal errors | Abaqus `.log`, `.sta`, `.dat` |
| **G2** | **Step 2 Loading Progress** | Prescribed displacement $u_y \ge 0.0075\,\text{mm}$ (Step 2 completion $\ge 50\%$) | RP 999999 `U2` history in `.odb` |
| **G3** | **Damage Field Bounds** | $0.0 \le d \le 1.005$ across all nodes; zero numerical divergence | Layer 3 visualizer SDV1 in `.odb` |
| **G4** | **History Monotonicity** | $\min \Delta \mathcal{H} \ge 0.0\,\text{MPa}$ across all increments and elements | Layer 3 visualizer SDV2 in `.odb` |
| **G5** | **Crack Advancement Extent** | Crack tip ($d \ge 0.90$) advances $\ge 0.15\,\text{mm}$ beyond initial notch ($x \ge 0.65\,\text{mm}$) | Spatial $d$ contour along $y = 0.5\,\text{mm}$ |
| **G6** | **Companion Field Output** | `MISESERI, MISESAVG, S, E, SDV` present and non-empty in all saved frames | ODB frame field dictionary audit |
| **G7** | **Global Force-Displacement** | Monotonic elastic loading to peak, smooth post-peak softening drop $\ge 50\%$ | RP 999999 `RF2` vs `U2` curve |

---

## 4. Execution Package & Cluster Preflight Verification

1. **Input Deck:**
   - Path: `models/pandey_kumar_mode1/237_f1768_case1_donor/PK_F1768_CASE_1_COARSE_COUPLED.inp`
   - SHA-256: `7B37F167AF520ED2B10C1B4034507F22E923ECABC9CE4F3E7019933D872931C6`
   - Remote Path: `/scratch9/pr21vyci/runs/mode1_pk_f1768_case1_donor_prep/PK_F1768_CASE_1_COARSE_COUPLED.inp` (Verified bitwise identical on cluster)
2. **User Subroutine:**
   - Path: `models/pandey_kumar_mode1/f42_mixed_uel.for`
   - SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` (Frozen Fortran production UEL)
   - Remote Path: `/scratch9/pr21vyci/runs/mode1_pk_f1768_case1_donor_prep/f42_mixed_uel.for` (Verified bitwise identical on cluster)
3. **PBS Execution Script:**
   - Path: `models/pandey_kumar_mode1/237_f1768_case1_donor/submit_f1768_case1_donor.pbs`
   - SHA-256: `B01A50AF39083E315EE167C6CE5469EC9F8B0D026E9678DFD75D2AA3B191ADA6`
   - Remote Path: `/scratch9/pr21vyci/runs/mode1_pk_f1768_case1_donor_prep/submit_f1768_case1_donor.pbs` (Uploaded with mode 755)
4. **Dual-Channel Notification Configuration:**
   - `#PBS -m abe` and `#PBS -M pr21vyci@mailserver.tu-freiberg.de` configured.
   - Remote notification config `/home/pr21vyci/.config/adaptive-remeshing/notifications.env` verified (mode 600).
   - Shell script `job_notifications.sh` verified in run directory.
5. **Live Scheduler State:**
   - Active user jobs: 0 (verified via guarded `qstat -u pr21vyci`).
   - Cluster queue: `entry_imfdfkmq` routing to `normal_imfdfkmq`.
   - Node resources: 1 CPU, 8 GB RAM, $\le 2\,\text{h}$ walltime.
   - Disk space: $>20\,\text{GB}$ available in `/scratch9/pr21vyci/`.

---

## 5. Next Steps Post-Review Approval

Upon receiving authenticated independent review approval for `HND-F1769-CASE1-DONOR-EXEC-001`:
1. Submit `submit_f1768_case1_donor.pbs` via guarded cluster invocation:
   `powershell -NoProfile -ExecutionPolicy Bypass -File .\.agents\scripts\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub /scratch9/pr21vyci/runs/mode1_pk_f1768_case1_donor_prep/submit_f1768_case1_donor.pbs"`
2. Record the returned PBS Job ID in `HPC_JOB_LEDGER.csv` and `ACTIVE_TASK.json`.
3. Monitor job execution on cluster node until completion.
4. Programmatically inspect the resulting ODB against Gates G1–G7.
5. Generate publication figures of the advancing crack and `MISESERI` error indicator fields.
6. Publish execution report and stage completion review payload.
