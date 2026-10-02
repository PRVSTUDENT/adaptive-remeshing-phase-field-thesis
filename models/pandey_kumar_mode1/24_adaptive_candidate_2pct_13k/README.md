# Mode-I 2.0% Efficiency-Calibrated Adaptive Package (13,897 Finite Elements)

**Document Identifier:** `models/pandey_kumar_mode1/24_adaptive_candidate_2pct_13k/README.md`  
**Literature Reference:** Pandey, P., & Kumar, S. (2025). *Adaptive Finite Element Phase-Field Modeling of Brittle Fracture Using Error Indicator Approach*. CMES, Vol. 144, No. 3, pp. 3251–3276. DOI: `10.32604/cmes.2025.067858`  
**Discretization:** 13,897 Finite Elements ($13,506$ CPE4 quads $+ 391$ CPE3 triangles, $13,884$ nodes)  
**Layered Implementation:** 41,691 Layered Elements ($13,897$ Phase U1/U3 $+ 13,897$ Disp U2/U4 $+ 13,897$ Companion CPE4/CPE3)  
**Status:** `DATACHECK_PASSED_SUBMITTED_TO_PBS_AS_JOB_1409846`

---

## 1. Epistemic Role & Literature Distinction

This package contains the authoritative Mode-I adaptive production fracture simulation deck (`PK_MODE1_ADAPT_2PCT_13K_ENERGY.inp`) generated from the canonical 2,906-element coarse mesh with corrected Poisson lateral boundary conditions under native Abaqus `adaptiveRemesh` with `errorTarget=2.0%`.

### Critical Scientific Qualification:
- **Efficiency-Calibrated Variant**: The 13,897-element mesh was obtained with `errorTarget=2.0%`, whereas Pandey & Kumar (2025) report the literature-literal remeshing setting as `errorTarget=1.0%`. Therefore, this case is evaluated as an **efficiency-calibrated adaptive configuration**, not as the literal Pandey–Kumar 1% reproduction.
- **Element-Count Delta**:
  $$\frac{|13897 - 13941|}{13941} \times 100\% = 0.32\%$$
  A close total element count ($13,897$ vs reported $13,941$) reflects similar discretization scale and corridor resolution ($h_{\text{tip}} = 0.81\,\mu\text{m}$), but does not prove geometric or topological identity.
- **Directional Classification**: **`TOWARD_TARGET_LOCALIZATION`** (recovers clean crack-tip refinement and narrow propagation corridor along $y=0.5\,\text{mm}$ without arbitrary mesh tuning).

---

## 2. Boundary Condition Influence on Adaptive Remeshing

Correcting the pre-analysis lateral boundary condition (allowing natural Poisson contraction across the top edge) significantly reduces unnecessary adaptive refinement by removing artificial corner shear stress concentrations (dropping 1.0% elements from $72,085$ to $56,302$). However, the literature-literal 1% Abaqus remesh still remains substantially denser ($56,302$ finite elements) than the published mesh ($13,941$ elements in Pandey & Kumar, 2025). The 2.0% project variant yields a much more efficient 13,897-element mesh with improved localization.

---

## 3. Package Checksums & Execution Constraints

- `f42_mixed_uel.for`: `ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6`
- `PK_MODE1_ADAPT_2PCT_13K_ENERGY.inp`: `9113c5f609b86de03fd0ad4a18a971ec3ed5424664bfe44e695e96789d4d6ecc` ($N_{\text{phys}}=13897.0$, `*Depvar 20`, All_elem SDV17–20, `CALL GETOUTDIR` CSV)
- **Execution Directives**: 1 CPU serial, 16 GB RAM, 12 h walltime, queue `normal_imfdfkmq` via `entry_imfdfkmq` (PBS Job ID: `1409846.mmaster02`).
