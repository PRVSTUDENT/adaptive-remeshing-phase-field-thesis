# Task F1770: Case 1 Advancing Coupled Donor Replacement Execution Plan & Gate Specification

**Task ID:** `F1770-CASE1-ADVANCING-COUPLED-DONOR-REPLACEMENT-EXECUTION`  
**Classification:** `DONOR_EXECUTION_BOUNDED_ONE_PBS`  
**Agent:** `gemini-antigravity`  
**Date:** 15 November 2026  
**Status:** `INITIALIZED_AWAITING_REVIEW_AUTHORIZATION`  
**Predecessor Review:** `HND-F1769-CASE1-DONOR-R2-AUTH-001` (Decision: `INSUFFICIENT_EVIDENCE`, Approving R2 Technical Repair & Directing Registration of Distinct Replacement Successor F1770)  
**Prospective PBS Submissions Budget:** Exactly 1 (Current consumed in F1770: 0/1; cumulative historical submissions strictly preserved at 28)  
**Production Fortran UEL SHA-256:** `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` (Bitwise Frozen)  
**Candidate Production Deck SHA-256:** `7B37F167AF520ED2B10C1B4034507F22E923ECABC9CE4F3E7019933D872931C6` (Bitwise Unchanged)  
**Repaired PBS Script (R2) SHA-256:** `3A9033581AF1FF5E876FC7367DE6FEC7C94787B0D176B68A8FCCE478AEA78716`  
**Remote Execution Directory:** `/scratch9/pr21vyci/runs/mode1_pk_f1768_case1_donor_prep/`  
**Failed Predecessor Job ID:** `1423603.mmaster02` (Exit 1 after 3s, wrapper lock collision, accounted as submission 28)  

---

## 1. Executive Summary & Review Governance Transition

In accordance with independent scientific review evaluation `HND-F1769-CASE1-DONOR-R2-AUTH-001`, the technical wrapper repair implemented in Revision R2 was formally **APPROVED** (`r2_wrapper_safety_assessment: APPROVED`).

To maintain strict submission accounting and eliminate ambiguity regarding execution allowances:
1. The original F1769 allowance of exactly one PBS submission is acknowledged as fully consumed by Job `1423603.mmaster02` (Exit 1). Task F1769 is formally closed as `COMPLETED_TECHNICAL_REPAIR_APPROVED_CONSUMED`.
2. Cumulative historical submissions remain permanently at **28**.
3. Successor Task F1770 is registered as a distinct, bounded one-job technical-replacement task for the Case 1 Advancing Coupled Donor experiment, using the approved Revision R2 execution script.
4. The prospective replacement job will be accounted as **Job 29 of 29** only upon genuine launch following authenticated independent review approval.

---

## 2. Approved Technical R2 Execution Package

The execution package for Task F1770 has been fully verified on both the local repository and the remote cluster:

1. **PBS Execution Script (Revision R2):**
   - Path: `models/pandey_kumar_mode1/237_f1768_case1_donor/submit_f1769_case1_donor_r2.pbs`
   - SHA-256: `3A9033581AF1FF5E876FC7367DE6FEC7C94787B0D176B68A8FCCE478AEA78716`
   - Remote Path: `/scratch9/pr21vyci/runs/mode1_pk_f1768_case1_donor_prep/submit_f1769_case1_donor_r2.pbs` (Mode 755, 100% bitwise hash match verified on cluster)
   - **Safety Features:**
     - Atomic POSIX directory lock guard: `mkdir "${RUN_DIR}/${JOB_NAME}.pbs_guard_d"` with clean `rmdir` trap.
     - Fail-closed check on pre-existing Abaqus lock files: `if [ -e "${RUN_DIR}/${JOB_NAME}.lck" ]; then exit 1; fi`.
     - Zero unconditional lock deletions (`rm -f *.lck` completely removed).
     - Scratch storage preflight ($> 5\,\text{GB}$ required).
     - User subroutine bitwise hash check before execution.
     - Dual-channel notifications (`#PBS -m abe` + Telegram shell trap).
2. **Production Input Deck:**
   - Path: `models/pandey_kumar_mode1/237_f1768_case1_donor/PK_F1768_CASE_1_COARSE_COUPLED.inp`
   - SHA-256: `7B37F167AF520ED2B10C1B4034507F22E923ECABC9CE4F3E7019933D872931C6` (8,718 layered elements: Layer 1 Phase U1/U3, Layer 2 Mech U2/U4, Layer 3 Companion CPE4/CPE3).
   - Boundary Conditions: `N_BOTTOM, 2, 2, 0.0`, `N_PIN, 1, 1, 0.0`, `N_TOP, 1, 1, 0.0`, `N_RP, 2, 2, \bar{u}` (100% concordant with reference benchmark `PK_MODE1_STANDARD_PFM.inp` and production deck `PK_F1739_CASE_1_PROD.inp`).
   - Loading Schedule: Step 1 to $u_y = 0.0050\,\text{mm}$ ($\Delta t = 0.02$); Step 2 to $u_y = 0.0100\,\text{mm}$ (initial $\Delta t = 0.002$, min $\Delta t = 10^{-8}$).
   - Field Outputs: `*OUTPUT, FIELD, FREQUENCY=1` outputting `MISESERI, MISESAVG, S, E, SDV`.
3. **Production Fortran UEL:**
   - Path: `models/pandey_kumar_mode1/f42_mixed_uel.for`
   - SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` (Bitwise Frozen).
4. **Cluster State & Scheduler Verification:**
   - Active Abaqus processes: 0 (verified via guarded `ps -u pr21vyci`).
   - Active cluster queue jobs: 0 (verified via guarded `qstat -u pr21vyci`).
   - Run directory lock files: 0 (verified via guarded `ls -la *lck*`).
   - Datacheck Status: Exit Code 0 (verified in job `PK_F1768_CASE_1_DC`).

---

## 3. Predeclared Scientific Acceptance Gates (G1–G7)

Execution of `PK_F1769_C1_DONOR` under Task F1770 will be strictly evaluated against the following predeclared criteria:

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

## 4. Replacement Execution Request

Gemini Antigravity formally requests independent review authorization to execute the single technical replacement solve under Task F1770:

```bash
Task ID:        F1770-CASE1-ADVANCING-COUPLED-DONOR-REPLACEMENT-EXECUTION
Job Name:       PK_F1769_C1_DONOR
PBS Script:     submit_f1769_case1_donor_r2.pbs (SHA-256: 3A9033581AF1FF5E876FC7367DE6FEC7C94787B0D176B68A8FCCE478AEA78716)
Queue / Node:   entry_imfdfkmq (1 CPU, 8 GB RAM, walltime <= 02:00:00)
Input Deck:     PK_F1768_CASE_1_COARSE_COUPLED.inp (SHA-256: 7B37F167..., Bitwise Unmodified)
User Subroutine: f42_mixed_uel.for (SHA-256: CE8D5EDC..., Bitwise Frozen)
Accounting:     Job 29 of 29 upon launch (Cumulative 28 -> 29)
```
