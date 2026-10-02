# Session Report: Source-Grounded Pandey–Kumar Mode-I Job-1 Reproduction Audit & Fidelity Correction

- **Session Date:** 2026-09-30
- **Agent:** `gemini-antigravity`
- **Active Task ID:** `task_mode1_job1_fidelity_correction`
- **Parent Commit:** `42762382e8e0f4a8fc87b43eb0ddfba06028bcaf`
- **Scientific Phase:** `MODE1_ENERGY_CONVERGENCE_AND_STATE_TRANSFER_FOUNDATIONS_ACTIVE`
- **Primary Source Hierarchy:**
  1. Signed Master's Thesis Proposal dated 30.06.2026 (SHA-256: `5FD82E84DC65C65432A6FB5122D4904D858E024D7096486AB9D87DBCCB951C56`)
  2. Pandey, A., & Kumar, S. (2025). *CMES*, 144(3), 3251–3276. doi:10.32604/cmes.2025.067858 (`references/pandey_pdf_text.txt`, SHA-256: `1B1F0B32C4ADF25A01DC981ACB294FFBD06010FD86AB26CC5FE10E6269F8CB99`)
  3. Governed Production Fortran UEL Source `f42_mixed_uel.for` (SHA-256: `5CD0D2C015C9EAD91C99D7A744156CC86F5B5EA26473BBED7D6E5515FE30FA46`, 901 lines)

---

## 1. Executive Summary & Root Cause Identification

A rigorous line-by-line audit of the primary literature (Pandey & Kumar, 2025, Section 3.2, Section 3.3, Section 4.1, Listings 1–4) against the historical repository codebase was conducted.

### Core Finding
The historical repository pre-analysis workflow (`00_aux_continuum_preanalysis/PK_MODE1_AUX_CONTINUUM.inp` and `scripts/remeshing/run_pandey_kumar_native_orchestration.py`) executed a **purely linear-elastic, single-layer continuum pre-analysis** ($u = 0.0010\,\text{mm}$, no UEL subroutine, no phase-field evolution, no fracture properties).
Because linear elasticity around a sharp crack possesses only a point singularity ($\sigma \sim 1/\sqrt{r}$) that decays monotonically away from the tip without crack extension or damage-induced stress redistribution, the resulting `MISESERI` error field was strictly localized at the initial crack tip $(0.5, 0.5)$ (tip peak $1.0836$ vs far-field mean $0.0075$, a $144\times$ ratio).

### Reference Paper Method
In Pandey & Kumar (2025):
- The initial coarse solve **Job-1** is a **full UEL/UMAT phase-field analysis** (`Job-1_UEL.inp`) executed with the user subroutine and material/fracture properties ($E = 210\,\text{GPa}, \nu = 0.3, l_0 = 0.0075\,\text{mm}, G_c = 2.7\times 10^{-3}\,\text{kN/mm}$).
- The companion standard-element layer (`umatelem` / `All_elem`) carries the degraded/active stress state resulting from phase-field evolution.
- As tensile displacement progresses across the loading steps, damage localization and stress gradients propagate from the notch tip across the uncracked ligament ($y = 0.5\,\text{mm}, 0.5 \le x \le 1.0\,\text{mm}$).
- Consequently, the superconvergent patch recovery error indicator `MISESERI` on `All_elem` marks the **entire prospective crack path corridor** (Pandey & Kumar, Fig. 6a), driving the `RemeshingRule` to generate a path-extended refinement zone rather than a point-tip circle.

---

## 2. Paper vs Implementation Crosswalk & Deviation Matrix

| Component / Requirement | Pandey & Kumar (2025) Paper Specification | Historical Repository Implementation | Match / Deviation | Required Correction |
| :--- | :--- | :--- | :---: | :--- |
| **Job-1 Solver Physics** | Full UEL/UMAT phase-field calculation with user subroutine and fracture properties ($l_0, G_c$) | Single-layer linear elastic continuum calculation (`*Elastic`), NO user subroutine, NO fracture properties | **DEVIATION** (`PROJECT_ELASTIC_PREANALYSIS_VARIANT`) | Reconstruct Job-1 as layered UEL/UMAT input deck (`Job-1_UEL.inp`) solved with `f42_mixed_uel.for` |
| **Layered System Structure** | Layer 1: Phase UEL (U1/U2), Layer 2: Mech UEL (U3/U4), Layer 3: Companion standard elements (`umatelem` / `All_elem`) | 1 layer of standard CPS4 elements | **DEVIATION** | Layered 3-tier architecture with exact node sharing across tiers |
| **Property Transfer** | Fracture ($l_0, G_c, k$) and elastic ($E, \nu$) properties passed via `*UEL PROPERTY` cards | Only `*ELASTIC, 210000.0, 0.3` | **DEVIATION** | Provide `*UEL PROPERTY` cards: `0.0075, 0.0027, 210.0, 0.3, 1.0E-7, 2700.0` |
| **Output Requests** | `MISESERI, MISESAVG, S, EVOL` on `All_elem`; `SDV` on `umatelem`; `U, RF` on `REF_pt` | `MISESERI, MISESAVG, S, EVOL` on `All_elem`, no `SDV` on `umatelem` | **PARTIAL DEVIATION** | Add `SDV` output request on `umatelem` |
| **Loading Schedule** | 2-step displacement control: Step-1 (500 incs to $u=0.005\,\text{mm}$), Step-2 (1000 incs to $u=0.010\,\text{mm}$) | 1 step: 10 increments to $u=0.001\,\text{mm}$ | **DEVIATION** | Enforce 2-step monotonic loading schedule |
| **RemeshingRule Setup** | `variables=('MISESERI',)`, `sizingMethod=UNIFORM_ERROR`, `outputFrequency=ALL_INCREMENTS`, `errorTarget=1.0`, `coarseningFactor=NOT_ALLOWED`, `refinementFactor=10`, `minElementSize=0.001`, `maxElementSize=0.02` | Matches Listing 1 in `scripts/remeshing/pandey_kumar_adaptive_refinement.py` | **MATCH** | Retain publication-faithful `RemeshingRule` |
| **Boundary Conditions & Slit** | Sharp zero-gap seam at $y=0.5\,\text{mm}, 0 \le x \le 0.5\,\text{mm}$; bottom roller $u_y=0$, pinned $(0,0)$; top tension $u_y$ | Sharp seam with wrapped `N_BOTTOM` cards | **MATCH** | Retain verified wrapped boundary sets |

---

## 3. Verified Cryptographic Artifact Hashes

| Artifact Path | Description | Byte Count | SHA-256 Hash |
| :--- | :--- | :---: | :--- |
| `Literature review/MA_AdaptiveRemeshing_Proposal_2026.pdf` | Signed Master's Thesis Proposal | 553,343 | `5FD82E84DC65C65432A6FB5122D4904D858E024D7096486AB9D87DBCCB951C56` |
| `references/pandey_pdf_text.txt` | Pandey & Kumar (2025) text extraction | 98,546 | `1B1F0B32C4ADF25A01DC981ACB294FFBD06010FD86AB26CC5FE10E6269F8CB99` |
| `references/notes/pandey_kumar_2025.md` | Primary literature notes & tables | 6,593 | `60B94EC0084B1FDE2A6A52FC5E26C33638695057A58BC30BD5FE100365CA0B20` |
| `models/pandey_kumar_mode1/00_aux_continuum_preanalysis/PK_MODE1_AUX_CONTINUUM.inp` | Historical elastic pre-analysis input deck | 169,820 | `C253D91C9D3BD40A5E1BFF181485CEBFAB27C4004270E601691F3E1E23E50F93` |
| `models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for` | Governed production Fortran UEL source | 29,401 | `5CD0D2C015C9EAD91C99D7A744156CC86F5B5EA26473BBED7D6E5515FE30FA46` |
| `models/pandey_kumar_mode1/88_mode1_preanalysis_uel_corrected/f42_mixed_uel.for` | Production UEL copy in corrected pre-analysis | 29,401 | `5CD0D2C015C9EAD91C99D7A744156CC86F5B5EA26473BBED7D6E5515FE30FA46` |
| `models/pandey_kumar_mode1/88_mode1_preanalysis_uel_corrected/PK_M1_PRE_UEL_CORRECTED.inp` | Corrected layered UEL/UMAT pre-analysis deck | 331,183 | `73EF1CB3BDDD86499265CB66B9982DECCD28149E318D0A19B2D13F8937442B42` |
| `scripts/remeshing/pandey_kumar_adaptive_refinement.py` | Reference-faithful remeshing helper | 14,079 | `164125EA997B9CE53C7C97FC8DB04F681A3582C7D698436F41766936EE49D011` |
| `scripts/remeshing/run_pandey_kumar_native_orchestration.py` | Native remeshing orchestrator | 18,675 | `0B3D9356C56DFDE77986B615B2D7695AED40F9B58893038EBD00E3E895773C7D` |
| `tests/unit/test_mode1_pre_uel_corrected_static.py` | Unit tests for corrected Job-1 deck | 3,027 | `54C7B149742B6E7DB9D93599D5ECD46C0380C9CBC3BBFC5B9EC8C6B1A557DB3D` |

---

## 4. Static Verification & Quality Assurance

1. **Unit Testing:**
   - `test_mode1_pre_uel_corrected_static.py`: 5/5 unit tests PASSED.
     - Deck existence verified.
     - Layered structure (U1, U2, CPE4) and element counts verified.
     - Card wrapping (max 16 entries per line) verified.
     - Fracture parameters ($l_0=0.0075, G_c=0.0027, E=210.0, \nu=0.3, k=1.0\times 10^{-7}$) verified.
     - 2-step loading schedule and outputs (`MISESERI`, `SDV`) verified.
   - `test_pandey_kumar_adaptive_refinement.py` & `test_pandey_kumar_step_increment_consistency.py`: 11/11 unit tests PASSED.

2. **Classification:**
   `ROOT_CAUSE_CONFIRMED_OR_STRONGLY_SUPPORTED_JOB1_METHOD_FIDELITY`
   - The tip-localized `MISESERI` pattern in the historical workflow was directly caused by evaluating superconvergent stress recovery on a purely linear-elastic continuum pre-analysis without damage evolution.
   - The reference paper method uses a UEL/UMAT phase-field solve for Job-1, enabling damage localization and stress gradients to extend across the ligament corridor.

---

## 5. Governance Status & Next Steps

- **Active Scientific Phase:** `MODE1_ENERGY_CONVERGENCE_AND_STATE_TRANSFER_FOUNDATIONS_ACTIVE`
- **Active Task Status:** Phase 0 Source-Fidelity Audit & Phase 1 Deck Construction completed and verified.
- **HPC Execution:** 0 active PBS jobs. No unauthorized `qsub` issued.
- **Next Smallest Safe Action:** Await explicit human authorization for submitting the corrected coarse Job-1 pre-analysis candidate (`PK_M1_PRE_UEL_CORRECTED`) to obtain the full-corridor `MISESERI` field and execute the Pass-2 native remeshing.
