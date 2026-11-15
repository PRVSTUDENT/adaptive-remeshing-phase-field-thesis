# Task F1769 Execution Payload: Case 1 Advancing Coupled Donor Execution Plan, Boundary Condition Audit & Acceptance Gate Specification

**Correlation ID:** `HND-F1769-CASE1-DONOR-EXEC-001`  
**Predecessor Correlation ID:** `HND-F1768-CASE1-DONOR-AUTH-001` (Decision: `APPROVE`, Directing Successor Execution Task F1769 with 1-Job Bounded Budget)  
**Task ID:** `F1769-CASE1-ADVANCING-COUPLED-DONOR-EXECUTION`  
**Commit SHA:** (commit-pinned on GitHub `origin/main`)  
**Timestamp:** `2026-11-15T09:30:00+01:00`  
**Author:** `gemini-antigravity`  
**Scope Boundary:** `DONOR_EXECUTION_BOUNDED_ONE_PBS` (Prospective Budget: Exactly 1 PBS Job; Consumed in F1769: 0/1; Cumulative Submissions Preserved at 27; Bitwise Frozen UEL Preserved)

---

## 1. Executive Summary & Review Directives Addressed

Following the independent review approval `HND-F1768-CASE1-DONOR-AUTH-001`, Task F1768 was formally closed as `COMPLETED_PREFLIGHT_APPROVED` and successor Task F1769 was initialized.

Task F1769 presents the formal execution plan and scientific acceptance gates for running the single authorized coarse coupled fracture simulation (`PK_F1768_C1_DONOR`) to generate the authentic advancing donor ODB for Case 1 (Mode-I Single-Edge Notched Plate, Pandey & Kumar 2025, Section 4.2).

### Reviewer Findings Resolution (F1768-R01 to F1768-R06)

1. **Finding F1768-R01 (Datacheck vs Convergence & Crack Advancement):**
   - The donor remains classified as `PREPARED_NOT_EXECUTED` until actual solver output and ODB fields are verified. Gates G1 (Exit 0) and G2/G5 (Crack Advancement) are formally predeclared.
2. **Finding F1768-R02 (ODB Field Output Population Verification):**
   - Predeclared Gate G6 mandates post-execution programmatic inspection of the actual ODB (`MISESERI`, `MISESAVG`, `S`, `E`, and `SDV` on Layer 3 visualizer elements) before any adaptive remeshing is authorized.
3. **Finding F1768-R03 (Damage Localization & Physical Validity on Coarse Mesh):**
   - Predeclared Gate G5 mandates verification of crack advancement ($\Delta a \ge 0.15\,\text{mm}$ beyond initial notch) and monotonic damage transition along $y = 0.5\,\text{mm}$.
4. **Finding F1768-R04 (Top-Edge Horizontal Constraint Audit & Benchmark Concordance):**
   - A forensic comparison confirmed that `N_TOP, 1, 1, 0.0` is the exact boundary condition in both:
     - `models/pandey_kumar_mode1/01_standard_pfm_reference/PK_MODE1_STANDARD_PFM.inp` (which achieved 0.029% error vs literature $F_{\max}$ in Gate G1-07), and
     - `models/pandey_kumar_mode1/227_f1739_case1_adapted_fracture/PK_F1739_CASE_1_PROD.inp` (which solved 2,050 increments Exit 0 to 99.96% load drop in Job 1423321).
   - Preserving this constraint maintains 100% boundary condition concordance across all Case 1 models.
5. **Finding F1768-R05 (Runtime & Resource Bounding):**
   - The PBS script enforces `#PBS -l walltime=02:00:00`, 1 CPU, 8 GB RAM, and verifies scratch space $>5\,\text{GB}$.
6. **Finding F1768-R06 (Accounting as One Donor Fracture Solve):**
   - The task and execution ledgers explicitly record this job as `case1_donor_coupled_fracture_solve`, with prospective consumption of exactly 1 PBS submission (updating cumulative submissions from 27 to 28 upon launch).

---

## 2. Technical Evidence & Preflight File Hashes

| Artifact | Repository Path | SHA-256 Digest | Status |
| :--- | :--- | :--- | :---: |
| **Physical Coarse Mesh** | `models/pandey_kumar_mode1/02_proposed_adaptive_refined/PK_PREANALYSIS_COARSE.inp` | `37AE41961556C6CD323BD822C0AC6EC62C5B42284CFFC5D30F8712C209A01B05` | Verified (2,906 el) |
| **Coarse Coupled Deck** | `models/pandey_kumar_mode1/237_f1768_case1_donor/PK_F1768_CASE_1_COARSE_COUPLED.inp` | `7B37F167AF520ED2B10C1B4034507F22E923ECABC9CE4F3E7019933D872931C6` | Verified (8,718 layered el) |
| **Frozen Fortran UEL** | `models/pandey_kumar_mode1/f42_mixed_uel.for` | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` | Bitwise Unmodified |
| **PBS Execution Script** | `models/pandey_kumar_mode1/237_f1768_case1_donor/submit_f1768_case1_donor.pbs` | `B01A50AF39083E315EE167C6CE5469EC9F8B0D026E9678DFD75D2AA3B191ADA6` | Verified (1 CPU, 8 GB, 2h) |
| **Execution Plan Report**| `docs/validation/F1769_CASE1_DONOR_EXECUTION_PLAN.md` | `FC1A3E67431CBC9F2745C5CAD129AC9086EEA9F2A8C6759217C45182BB92A81A` | Published |
| **Cluster Datacheck**    | `/scratch9/pr21vyci/runs/mode1_pk_f1768_case1_donor_prep/PK_F1768_CASE_1_DC.*` | Exit Code 0 | Verified on Node |
| **Regression Tests**     | `tests/unit/test_f1769_case1_donor_execution_plan.py` | 4/4 PASS in 0.38s | 30/30 Suite PASS |

---

## 3. Predeclared Scientific Acceptance Gates (G1–G7)

Execution of `PK_F1768_C1_DONOR` under Task F1769 will be judged against:

- **Gate G1 (Solver Exit Status):** Clean termination with Exit Code `0`, zero fatal errors.
- **Gate G2 (Step 2 Loading Progress):** Prescribed displacement $u_y \ge 0.0075\,\text{mm}$ (Step 2 completion $\ge 50\%$).
- **Gate G3 (Damage Field Bounds):** $0.0 \le d \le 1.005$ across all nodes; zero divergence.
- **Gate G4 (History Monotonicity):** $\min \Delta \mathcal{H} \ge 0.0\,\text{MPa}$ across all increments and elements.
- **Gate G5 (Crack Advancement Extent):** Crack tip ($d \ge 0.90$) advances $\ge 0.15\,\text{mm}$ beyond initial notch ($x \ge 0.65\,\text{mm}$).
- **Gate G6 (Companion Field Output):** `MISESERI, MISESAVG, S, E, SDV` present and non-empty in all saved frames on Layer 3 continuum visualizer instance `PART-1-1`.
- **Gate G7 (Global Force-Displacement):** Monotonic elastic loading to peak, smooth post-peak softening drop $\ge 50\%$.

---

## 4. Execution Request & Authorization Scope

Gemini Antigravity formally requests authorization to execute the single prepared coarse coupled donor job:

```bash
# PBS Job Parameters
Job Name:       PK_F1768_C1_DONOR
Run Directory:  /scratch9/pr21vyci/runs/mode1_pk_f1768_case1_donor_prep/
Queue:          entry_imfdfkmq (routing to normal_imfdfkmq)
Resources:      select=1:ncpus=1:mem=8gb, walltime=02:00:00
Input Deck:     PK_F1768_CASE_1_COARSE_COUPLED.inp (SHA-256: 7B37F167...)
User Subroutine: f42_mixed_uel.for (SHA-256: CE8D5EDC...)
Notifications:  PBS Mail (#PBS -m abe) + Telegram Shell Trap (notifications.env mode 600)
Submission Mode: Exactly 1 PBS job (Cumulative submissions 27 -> 28 upon launch)
```

No multi-job regression batch, no modification to the frozen UEL, and no additional PBS submissions are requested under this turn.
