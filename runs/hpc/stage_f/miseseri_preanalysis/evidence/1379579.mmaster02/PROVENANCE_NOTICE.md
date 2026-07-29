# Provenance Notice: PBS Job 1379579 vs Exploratory Interactive Corrective Run

**Date:** 2026-07-29  
**Task ID:** `F3-STAGE-F3-COMBINED-SCIENTIFIC-CLOSEOUT`  
**Official PBS Job ID:** `1379579.mmaster02`  
**Original PBS Deck SHA-256:** `484edd39e6930758346764e5e183b5fd050577bdb6b11ede5cba49b955307fe9`  
**Corrective Deck SHA-256:** `a927b8317ff9e20bfa84dd669a2577b095e69d1bf1c343b81b158a83fd075ea2`  

---

## 1. Summary of Provenance Repair

1. **PBS Job 1379579 Evaluation:**
   - Official PBS Job `1379579.mmaster02` was submitted using the initial deck generator script which contained a node-parsing defect (67,704 elements generated for 3,999 physical nodes).
   - Abaqus solver execution terminated with error exit code 1.
   - Classification: `technical_result_unusable_due_to_generator_defect` (`official_validation = false`).

2. **Exploratory Interactive Corrective Run:**
   - After correcting the deck generator (`build_mode_ii_miseseri_preanalysis.py`), an interactive Abaqus analysis was executed on `mlogin01`.
   - Genuine Abaqus Python ODB extraction yielded 3,930 finite element records with positive recovery error indicator $\text{MISESERI} \in [0.0000687, 0.1870114]\,\text{GPa}$ at load level $U_1 = 0.0010\,\text{mm}$ ($RF_1 = 0.04607\,\text{kN}$).
   - Classification: `exploratory_corrective_technical_pass`.

3. **Process Violations Recorded:**
   - **M-099:** Unauthorized interactive replacement solver execution on cluster (`mlogin01`).
   - **M-100:** Original PBS evidence path reused or overwritten by exploratory interactive extraction.

4. **Evidence Relocation:**
   - The exploratory interactive run evidence has been relocated to:
     `runs/hpc/stage_f/miseseri_preanalysis/corrective_interactive_runs/2026-07-29T070232_CEST/`
   - Official PBS Job `1379579.mmaster02` retains its failure classification `technical_result_unusable_due_to_generator_defect`.
