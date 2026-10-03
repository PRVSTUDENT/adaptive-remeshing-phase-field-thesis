# Pre-Job Isolation Card: Package 92 Layered Companion Pre-Analysis Solve

**Package:** `models/pandey_kumar_mode1/92_mode1_preanalysis_layered_companion_2906`  
**Deck Name:** `PK_M1_JOB1_LAYERED_COMPANION_2906.inp`  
**Subroutine:** `f42_mixed_uel.for`  
**Authoritative Subroutine SHA-256:** `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`  
**Deck SHA-256:** `27AAB773A116E3C8A832E4980D0E25F48A435F34DEDECE4ABE78FFA232C0C1FF`  
**Execution Mode:** 1 CPU Serial, Shared-Memory single rank (`normal_imfdfkmq`)  

---

### Pre-Job Gate Alignment
1. **Proposal Task:** Task 3 / Task 4 Prerequisite (Mode-I Adaptive Refinement Workflow & Pre-Analysis Semantics).
2. **Active Gate:** Gate-6B Stage 7 (Layered Companion-Element Reference-Fidelity Test).
3. **Scientific Question:** Does the layered 3-layer UEL/UMAT companion architecture (`All_elem` / `umatelem`) produce a different or localized `MISESERI` error field compared to the standard continuum control, or does the governed companion UMAT setting `STRESS = 0` result in identically zero stress output?
4. **Single Intended Difference:** 3-layer UEL/UMAT architecture using the authoritative governed companion UMAT implementation vs standard single-layer continuum control (`PK_M1_JOB1_CONTINUUM_MATCHED_2906.inp`).
5. **Frozen Variables:**
   - Specimen geometry: $1.0\,\text{mm} \times 1.0\,\text{mm}$ with $0.5\,\text{mm}$ zero-gap sharp seam.
   - Mesh topology: 2,906 physical elements (2,818 CPE4 quads, 88 CPE3 triangles) and 2,988 mesh nodes.
   - Boundary conditions: bottom roller + pin, top tied in DOF 2 to `N_RP` (lateral-free).
   - Loading schedule: Step 1 ($u=0.005\,\text{mm}$, 500 incs), Step 2 ($u=0.010\,\text{mm}$, 1000 incs).
   - Material parameters: $E=210.0\,\text{GPa}$, $\nu=0.3$, $G_c=0.0027\,\text{kN/mm}$, $l_0=0.0075\,\text{mm}$, $k=10^{-7}$.
6. **Pre-Declared Acceptance Criteria:**
   - Solver execution: Converges cleanly (`Exit 0`) without Newton iteration matrix divergence.
   - Reaction force & stiffness: Matches the continuum reference response ($K_0 \approx 137.8\,\text{kN/mm}$).
   - ODB output inspection: Evaluates whether `MISESERI` on `All_elem` is populated or identically zero, confirming the source audit analysis.
