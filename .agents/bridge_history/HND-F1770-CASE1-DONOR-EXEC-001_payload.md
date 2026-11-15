# Task F1770 Execution Payload: Case 1 Advancing Coupled Donor Distinct Replacement Execution Plan & Gate Specification

**Correlation ID:** `HND-F1770-CASE1-DONOR-EXEC-001`  
**Predecessor Correlation ID:** `HND-F1769-CASE1-DONOR-R2-AUTH-001` (Decision: `INSUFFICIENT_EVIDENCE`, Formally Approving R2 Technical Repair & Directing Registration of Distinct Replacement Successor F1770)  
**Task ID:** `F1770-CASE1-ADVANCING-COUPLED-DONOR-REPLACEMENT-EXECUTION`  
**Commit SHA:** (commit-pinned on GitHub `origin/main`)  
**Timestamp:** `2026-11-15T09:52:00+01:00`  
**Author:** `gemini-antigravity`  
**Scope Boundary:** `DONOR_EXECUTION_BOUNDED_ONE_PBS` (Prospective Budget: Exactly 1 PBS Replacement Solve; Current Consumed in F1770: 0/1; Cumulative Historical Submissions: 28 Preserved in Ledger; Bitwise Frozen UEL Preserved)

---

## 1. Executive Summary & Review Governance Transition

In direct response to independent scientific review evaluation `HND-F1769-CASE1-DONOR-R2-AUTH-001`:

1. **R2 Technical Repair Approved:** Reviewer formally confirmed that Revision R2 resolved all safety defects (`r2_wrapper_safety_assessment: APPROVED`):
   - Implemented POSIX atomic directory lock guard (`mkdir "${LOCK_GUARD_DIR}"` with `rmdir` trap).
   - Removed all unconditional `rm -f *.lck` statements from the wrapper.
   - Enforced fail-closed termination if an Abaqus lock file `${JOB_NAME}.lck` pre-exists.
   - Verified zero lingering Abaqus processes, zero active cluster jobs, and zero `.lck` files.
2. **Administrative Separation & One-Job Replacement Allowance:**
   - Reviewer noted that Task F1769's initial one-job allowance was consumed by failed Job `1423603.mmaster02`.
   - Task F1769 has been formally closed as `COMPLETED_TECHNICAL_REPAIR_APPROVED_CONSUMED`.
   - Task F1770 is registered as the distinct, bounded successor task for executing the single replacement solve.
   - Cumulative historical submissions remain permanently at **28** in `HPC_JOB_LEDGER.csv`.
   - The prospective replacement job is accounted as **Job 29 of 29** upon launch.

---

## 2. Technical Evidence & Preflight File Hashes

| Artifact | Repository Path | SHA-256 Digest | Status |
| :--- | :--- | :--- | :---: |
| **Physical Coarse Mesh** | `models/pandey_kumar_mode1/02_proposed_adaptive_refined/PK_PREANALYSIS_COARSE.inp` | `37AE41961556C6CD323BD822C0AC6EC62C5B42284CFFC5D30F8712C209A01B05` | Verified (2,906 el) |
| **Coarse Coupled Deck** | `models/pandey_kumar_mode1/237_f1768_case1_donor/PK_F1768_CASE_1_COARSE_COUPLED.inp` | `7B37F167AF520ED2B10C1B4034507F22E923ECABC9CE4F3E7019933D872931C6` | Verified (8,718 layered el) |
| **Frozen Fortran UEL** | `models/pandey_kumar_mode1/f42_mixed_uel.for` | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` | Bitwise Unmodified |
| **Approved PBS Script (R2)** | `models/pandey_kumar_mode1/237_f1768_case1_donor/submit_f1769_case1_donor_r2.pbs` | `3A9033581AF1FF5E876FC7367DE6FEC7C94787B0D176B68A8FCCE478AEA78716` | Verified on Cluster (Mode 755) |
| **Replacement Plan**    | `docs/validation/F1770_CASE1_DONOR_REPLACEMENT_PLAN.md` | `8CFE0DA946FB26CE2C59747BE9FD0073B1DC152EECD08CF8B34E587ACB4E30ED` | Published |
| **Failed Job Receipt**   | Official PBS Receipt for Job `1423603.mmaster02` (Exit 1) | Recorded in Execution Report | Published |
| **Regression Tests**     | `tests/unit/test_f1770_case1_donor_replacement_execution.py` | 4/4 PASS in 0.39s | 35/35 Suite PASS |

---

## 3. Predeclared Scientific Acceptance Gates (G1–G7)

Execution of `PK_F1769_C1_DONOR` under Task F1770 will be strictly evaluated against:

- **Gate G1 (Solver Exit Status):** Clean termination with Exit Code `0`, zero fatal errors.
- **Gate G2 (Step 2 Loading Progress):** Prescribed displacement $u_y \ge 0.0075\,\text{mm}$ (Step 2 completion $\ge 50\%$).
- **Gate G3 (Damage Field Bounds):** $0.0 \le d \le 1.005$ across all nodes; zero numerical divergence.
- **Gate G4 (History Monotonicity):** $\min \Delta \mathcal{H} \ge 0.0\,\text{MPa}$ across all increments and elements.
- **Gate G5 (Crack Advancement Extent):** Crack tip ($d \ge 0.90$) advances $\ge 0.15\,\text{mm}$ beyond initial notch ($x \ge 0.65\,\text{mm}$).
- **Gate G6 (Companion Field Output):** `MISESERI, MISESAVG, S, E, SDV` present and non-empty in all saved frames on Layer 3 continuum visualizer instance `PART-1-1`.
- **Gate G7 (Global Force-Displacement):** Monotonic elastic loading to peak, smooth post-peak softening drop $\ge 50\%$.

---

## 4. Replacement Execution Request & Authorization Scope

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
