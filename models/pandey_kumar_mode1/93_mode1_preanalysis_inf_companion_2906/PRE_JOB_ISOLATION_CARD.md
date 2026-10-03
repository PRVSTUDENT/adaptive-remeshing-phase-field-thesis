# Pre-Job Isolation Card: Package 93 Infinitesimal Companion Pre-Analysis Solve

**Package:** `models/pandey_kumar_mode1/93_mode1_preanalysis_inf_companion_2906`  
**Deck Name:** `PK_M1_JOB1_INF_COMPANION_2906.inp`  
**Subroutine:** `f42_mixed_uel_inf_stress.for`  
**Authoritative Subroutine SHA-256:** `472CA0C5CC8B762BF83DAEA961988502DBFAE36DB7A32565B8C13FA69D839084`  
**Deck SHA-256:** `D452369305FF67A2B0CFA4E5D07FAB810C9123ECF500A05BBA3E498437883613`  
**Execution Mode:** 1 CPU Serial, Shared-Memory single rank (`normal_imfdfkmq`)  

---

### Pre-Job Gate Alignment
1. **Proposal Task:** Task 3 / Task 4 Prerequisite (Mode-I Adaptive Refinement Workflow & Pre-Analysis Semantics).
2. **Active Gate:** Gate-6B Stage 8 (Infinitesimal-Stiffness Companion-Stress Reference-Fidelity Audit).
3. **Scientific Question:** Does the 3-layer UEL/UMAT architecture with Molnár & Gravouil (2017) infinitesimal isotropic companion elasticity ($E_{\text{dummy}} = 10^{-11}$) generate non-zero Cauchy stresses and `MISESERI` on the order of $10^{-12}$, reproducing the magnitude and spatial distribution of published Pandey & Kumar (2025) Fig. 6(a)?
4. **Single Intended Difference:** Restoring the Molnár & Gravouil (2017) linear elastic stress update in companion UMAT (`STRESS(K2) = STRESS(K2) + DDSDDE(K2, K1)*DSTRAN(K1)` with $E_{\text{dummy}} = 10^{-11}, \nu = 0.3$) vs Package 92 forced-zero stress update.
5. **Frozen Variables:**
   - Specimen geometry: $1.0\,\text{mm} \times 1.0\,\text{mm}$ with $0.5\,\text{mm}$ zero-gap sharp seam.
   - Mesh topology: 2,906 physical elements (2,818 CPE4 quads, 88 CPE3 triangles) and 2,988 mesh nodes.
   - Boundary conditions: bottom roller + pin, top tied in DOF 2 to `N_RP` (lateral-free).
   - Loading schedule: Step 1 ($u=0.005\,\text{mm}$, 500 incs), Step 2 ($u=0.010\,\text{mm}$, 1000 incs).
   - Material parameters: $E=210.0\,\text{GPa}$, $\nu=0.3$, $G_c=0.0027\,\text{kN/mm}$, $l_0=0.0075\,\text{mm}$, $k=10^{-7}$.
6. **Pre-Declared Acceptance Criteria:**
   - Solver execution: Converges cleanly (`Exit 0`) without Newton iteration matrix divergence.
   - Reaction force & stiffness: Preserves mechanical parity ($K_0 \approx 137.82\,\text{kN/mm}$, perturbation $< 10^{-13}$).
   - ODB output inspection: Evaluates whether `MISESERI` on `All_elem` is populated on the order of $10^{-12}$, quantitatively matching published Fig. 6(a).
