# Audit Report: Authentic UEL–UMAT–Facsimile–MISESERI Coupling in Pandey & Kumar (2025)

**Task ID**: F1697-PK-SEC43-AUTHENTIC-UEL-UMAT-MISESERI-COUPLING  
**Handoff / Correlation ID**: HND-F1697-COUPLING-AUDIT-001  
**Date**: 9 November 2026  
**Author**: Gemini Antigravity  
**Benchmark**: Pandey & Kumar (2025), Section 4.3, Rectangular Plate with Three Holes ($65 \times 120\,\mathrm{mm}$, Initial Notch $10 \times 0.4\,\mathrm{mm}$, Central Void $R = 10\,\mathrm{mm}$, $E = 210\,\mathrm{GPa}$, $\nu = 0.30$, $\ell_0 = 0.285\,\mathrm{mm}$, Initial Coarse Seed $1.5\,\mathrm{mm}$)  

---

## 1. Executive Summary

This audit reconstructs the complete data flow of the adaptive remeshing workflow proposed in Pandey & Kumar (2025), *Computer Modeling in Engineering & Sciences* (CMES), Vol. 144, No. 3, pp. 3251–3276, and investigates the root cause of the missing continuous dual-branch `MISESERI` error indicator band depicted in published Figure 15(b).

Through direct line-by-line inspection of:
1. Pandey & Kumar (2025) Sections 3.1–3.3, 4.3, Listings 1–4, and Reference [72] (Molnár & Gravouil, 2017);
2. Repository Fortran subroutines `models/pandey_kumar_mode1/f42_mixed_uel.for` and `192_pk_sec43_staggered_job1/f42_staggered_variant_uel.for`;
3. Input deck generation scripts `scripts/remeshing/build_f1692_sec43_staggered_deck.py`; and
4. Direct inspection of the raw Abaqus solver output database `PK_SEC43_COARSE_JOB1.odb` via the Abaqus Python API (`odbAccess`),

the workflow state is rigorously and unambiguously classified as **Situation B**:
> *`MISESERI` and `MISESAVG` were explicitly requested on the companion facsimile element set (`All_elem` / `umatelem`), and the fields exist in the ODB across all 3,923 elements, but every single value is identically zero ($0.000000\,\mathrm{MPa}$) because the companion UMAT subroutine explicitly hardcoded `STRESS(I) = 0.D0` (lines 876–882 in `f42_mixed_uel.for`). Abaqus Superconvergent Patch Recovery (SPR) requires a non-zero Cauchy stress tensor $S$ to compute stress discontinuities $\|\sigma^* - \sigma_h\|_{L_2}$. Because $\sigma_h = \mathbf{0}$ everywhere on `umatelem`, SPR evaluated $\|\mathbf{0} - \mathbf{0}\| \equiv 0.0$.*

---

## 2. Reconstructed End-to-End Data Flow

The published Method A workflow comprises seven sequential stages:

```
+-----------------------------------------------------------------------------------+
| 1. Coarse Input Deck: Job-1.inp                                                   |
|    - Standard 2D geometry (65 x 120 mm), initial seed 1.5 mm                     |
|    - 3,923 physical elements (3,814 quads, 109 tris), 4,040 nodes                 |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| 2. Layered Input Deck Generation: Job-1_UEL.inp                                   |
|    - Layer 1 (EIDs 1..N): Phase-field UEL (Active DOF 3: phase field d)           |
|    - Layer 2 (EIDs N+1..2N): Displacement UEL (Active DOFs 1,2: u_x, u_y)         |
|    - Layer 3 (EIDs 2N+1..3N): Companion elements (`umatelem` / `All_elem`)        |
|      Standard CPE4/CPE3 or CPS4/CPS3 elements on identical physical nodes         |
|      Material: `*USER MATERIAL` invoking `SUBROUTINE UMAT`                        |
|    - Output Requests (Listing 3):                                                 |
|      `*ELEMENT OUTPUT, ELSET=Instance-1.All_elem, DIRECTION=YES`                  |
|      `MISESERI, MISESAVG, S, EVOL`                                                |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| 3. Phase-Field Solver Execution (Job-1_UEL.inp + Subroutine)                      |
|    - UEL solves coupled phase-field fracture equations                            |
|    - Damage d and history H are computed at UEL integration points                |
|    - Common block `/CB_STATE_TRANS/` transmits trial phase d to UMAT              |
|    - Companion UMAT executes on Layer 3 elements at each increment                |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| 4. Abaqus Stress Recovery on Companion Facsimile Set                              |
|    - Abaqus queries Cauchy stress tensor S returned by UMAT on `All_elem`         |
|    - Abaqus native Superconvergent Patch Recovery (SPR) constructs patch-smoothed |
|      polynomial stress field sigma* across adjacent element patches               |
|    - Native energy-norm error indicator evaluated:                                |
|      MISESERI = ||sigma* - sigma_h||_L2                                           |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| 5. Remeshing Rule Initialization (Listing 1): `create_remeshing_rule(...)`        |
|    - `m1.RemeshingRule(name='RR: 1', region=reg, variables=('MISESERI',),        |
|                        sizingMethod=UNIFORM_ERROR, errorTarget=1.0..5.0,           |
|                        maxElementSize=1.5, minElementSize=0.143, ...)`            |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| 6. Native Adaptive Remeshing Execution (Listing 4): `implement_remesh(odb, model)`|
|    - Opens Job-1 ODB, reads last frame of specified step                          |
|    - Evaluates element sizing field: h_new = h_old * (errorTarget / e_elem)^(1/p) |
|    - Native Abaqus CAE kernel generates adapted mesh `Job-2.inp`                  |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| 7. Production Phase-Field Solve on Adapted Mesh: Job-2_UEL.inp                    |
|    - Re-generates 3-layer UEL deck on adapted mesh                                |
|    - Solves full fracture propagation to complete structural severance            |
+-----------------------------------------------------------------------------------+
```

---

## 3. Detailed Answers to the Seven Audit Questions

### Question 1: Whether MISESERI is generated on the physical elements or companion visualization elements.
**Answer: Companion visualization elements.**  
*Evidence*:
- In Abaqus FEA architecture, user-defined elements (`*USER ELEMENT` / UEL) do not support built-in continuum field variables (`S`, `E`, `MISESERI`, `MISESAVG`). Abaqus SPR requires standard isoparametric continuum elements (`CPE4`, `CPS4`, etc.) with standard element shape functions to form the patch recovery matrix and integrate $\| \sigma^* - \sigma_h \|$.
- Pandey & Kumar (2025) Section 3.2, lines 3262–3263:
  > *"Two identical sets containing the element ids are defined in the input file—'umatelem' and 'All_elem'... The set 'All_elem' is the facsimile set with the same element connectivity as the 'umatelem' set (Listing 2). This guarantees that the field output variable values at the integration points in the elements of 'umatelem' set are also mapped to corresponding elements in this facsimile set within the solver's data structure, therefore allowing the refinement to be triggered by the Remeshing Rule."*
- Listing 2 defines `All_elem` with element IDs 29609–44412 (matching Layer 3 companion elements `umatelem`). Listing 3 requests `MISESERI` exclusively on `ELSET=Instance-1.All_elem`.

### Question 2: Whether the companion UMAT supplies authentic degraded stress consistent with the UEL mechanical state.
**Answer: In the repository implementation, no; it was explicitly zeroed out (the paper's exact companion subroutine is unstated).**  
*Evidence*:
- In `models/pandey_kumar_mode1/f42_mixed_uel.for` (lines 876–882) and `192_pk_sec43_staggered_job1/f42_staggered_variant_uel.for` (lines 887–893):
  ```fortran
        DO I=1, NTENS
          STRESS(I) = 0.D0
          DO J=1, NTENS
            DDSDDE(I,J) = 0.D0
          ENDDO
          DDSDDE(I,I) = 1.D-11
        ENDDO
  ```
- The companion UMAT sets Cauchy stress `STRESS(I) = 0.D0` and tangent stiffness `DDSDDE(I,I) = 1.D-11`. It passes only scalar solution-dependent variables (`STATEV(1) = d`, `STATEV(2) = H`, `STATEV(15) = (1-d)^2 + 10^-7`).
- In the foundational reference cited by Pandey & Kumar (Molnár & Gravouil, 2017 [Ref 72], `SingleNotch.for`, lines 69–73), Molnár's UMAT evaluates **undamaged linear-elastic stress**:
  ```fortran
        DO K1=1, NTENS
         DO K2=1, NTENS
          STRESS(K2)=STRESS(K2)+DDSDDE(K2, K1)*DSTRAN(K1)
         END DO
        END DO
  ```
  Neither Molnár nor the repository UMAT supplied authentic degraded Cauchy stress $\sigma_d = [(1-d)^2 + k] \mathbb{C} : \varepsilon$. Importantly, while this explains the zero-stress observation in the repository, the exact internal UMAT code used by Pandey & Kumar (2025) was not published, so whether their private codebase used undamaged linear elasticity or an alternative feedback formulation remains unstated in the literature.

### Question 3: Whether the UMAT output is actually used by Abaqus stress recovery.
**Answer: Yes, absolutely.**  
*Evidence*:
- Abaqus Superconvergent Patch Recovery (SPR) for `MISESERI` operates directly on the integration-point Cauchy stress tensor `S` output by the material model. If UMAT outputs `STRESS = 0`, Abaqus sees $\sigma_h = \mathbf{0}$, evaluates $\sigma^* = \mathbf{0}$, and reports `MISESERI = 0.0`.
- When UMAT outputs non-zero stress values $\sigma_h$, Abaqus SPR evaluates the polynomial stress recovery error over element patches surrounding each node.

### Question 4: Whether physical, mechanical and visualization element connectivity is correctly mapped.
**Answer: Yes, 1-to-1 exact nodal coincidence.**  
*Evidence*:
- In `scripts/remeshing/build_f1692_sec43_staggered_deck.py` (lines 104–138):
  - Layer 1 (Phase U1): EID $e$, connectivity $[n_1, n_2, n_3, n_4]$
  - Layer 2 (Disp U2): EID $e + N_{\mathrm{phys}}$, connectivity $[n_1, n_2, n_3, n_4]$
  - Layer 3 (UMAT CPE4): EID $e + 2 N_{\mathrm{phys}}$, connectivity $[n_1, n_2, n_3, n_4]$
- All three layers share identical physical node coordinates and node IDs. In the UMAT subroutine, `PHYSIDX = NOEL - 2 * NPHYS_VAL` exactly maps companion element $e + 2 N_{\mathrm{phys}}$ back to physical element index $e$.

### Question 5: Whether MISESERI and MISESAVG are explicitly requested and populated in the correct output element set.
**Answer: Yes, requested and populated in the ODB, but populated with zeros.**  
*Evidence*:
- In `scripts/remeshing/build_f1692_sec43_staggered_deck.py` (line 166) and `PK_SEC43_COARSE_JOB1.inp`:
  `*ELEMENT OUTPUT, ELSET=umatelem: MISESERI, MISESAVG, S, E, SDV`
- Direct inspection of `PK_SEC43_COARSE_JOB1.odb` via `abaqus python`:
  - `MISESERI`: 3,923 values exist; `min = 0.0, max = 0.0, all_zero = True`.
  - `MISESAVG`: 3,923 values exist; `min = 0.0, max = 0.0, all_zero = True`.
  - `S`: 15,365 values exist; `S Mises min = 0.0, max = 0.0, all_zero = True`.
  - `SDV1` (damage $d$): 15,365 values exist; range $0.0217$ to $0.9846$.
  - `SDV15` (degradation $g(d)$): 15,365 values exist; range $0.0002$ to $0.9570$.
- The output requests and element set binding (`umatelem` / `All_elem`) functioned as intended, but received zero stress data.

### Question 6: Whether published Figure 15(b) uses native MISESERI values, normalized values, or a transformed plotting quantity.
**Answer: Native MISESERI request, but the origin of the continuous dual-branch refinement pattern remains unproven under single-frame evaluations.**  
*Evidence*:
- Pandey & Kumar Section 4.3 states:
  > *"The MISESERI plot is obtained as shown in Fig. 15b. The Python script specifies two specific functions for initializing the remeshing rule (refer to Listing 1) and its implementation (refer to Listing 3)."*
- Listing 1 sets `variables=('MISESERI', )`, confirming native `MISESERI` is the remeshing trigger.
- However, Figure 15(b) displays a continuous, dual-branch elevated error band following both the primary trajectory (notch to central hole) and the secondary trajectory (central hole to right boundary).
- As established across all donor states and reconstructed recovery formulations tested:
  - Intact linear-elastic pre-analysis (F1688, F1693 Case A, F1696) produces secondary error $\le 7.56\%$ of peak error.
  - Intermediate mid-propagation (F1694 Donor b, F1697 midprop) produces elevated secondary error ($32.1\%$ to $54.4\%$), but primary corridor error collapses ($\le 3.61\%$) as the severed primary ligament relaxes.
  - Terminal severance (F1693 Case B, F1694 Donor c, F1697 terminal) produces secondary error $\le 17.1\%$ of peak error, while both ligaments relax and peak error transfers to far-field pin holes.
  - Across the tested donor states and reconstructed recovery models, no individual instantaneous deformation state exhibited simultaneous elevated discretization error along both fracture corridors.
- Possible explanations for published Figure 15(b) include:
  1. A multi-frame maximum envelope aggregation across loading increments ($\max_t \mathrm{MISESERI}_e(t)$), similar to the Candidate E10/E12 framework;
  2. Alternative contour normalization, display scaling, or interpolation differences;
  3. An alternative companion formulation definition not disclosed in the published text.
- Because native remeshing was not executed on the F1697 recovered fields (gated closed by indicator-band thresholds), the adapted mesh generated directly by native Abaqus from this specific field remains untested.

### Question 7: Which step and final frame native adaptiveRemesh() actually reads.
**Answer: The final frame of the step specified in `RemeshingRule`.**  
*Evidence*:
- In Listing 1, `create_remeshing_rule_assembly_instance(...)` takes argument `step_name` and assigns:
  `m1.RemeshingRule(name='RR: 1', stepName=step_name, region=reg, ... outputFrequency=ALL_INCREMENTS, ...)`
- In Listing 4, `implement_remesh(odb_path, model_name)` executes:
  `mdb.models[model_name].adaptiveRemesh(odb=o1)`
- Under the Abaqus Python API documentation, when `adaptiveRemesh` is called without explicit frame indices, it reads the **last available frame** of the step associated with the rule (`stepName`).
- In a two-step analysis where Step 1 is pre-load and Step 2 is displacement pulling, if `step_name='Step-1'`, it reads the intact pre-analysis state. If `step_name='Step-2'`, it reads the terminal state.

---

## 4. ODB Classification: Situation B

Based on the empirical inspection of `PK_SEC43_COARSE_JOB1.odb`:

| Diagnostic Item | Observation in Raw UEL ODB | Classification Significance |
| :--- | :--- | :--- |
| `MISESERI` Field Presence | Exists (3,923 element values) | Confirms output request was active |
| `MISESERI` Numerical Values | Identically $0.000000\,\mathrm{MPa}$ everywhere | Confirms error indicator evaluated zero |
| Cauchy Stress $S$ Values | Identically $\mathbf{0.0}$ at all 15,365 integration points | Confirms companion elements carried zero stress |
| Damage Variables (`SDV1`, `SDV14`) | Active and non-zero ($0 \le d \le 0.985$) | Confirms UEL physical solution existed |
| Stiffness Tan `DDSDDE` in UMAT | Hardcoded to $10^{-11}\,\mathrm{MPa}$ | Zeroed to prevent parallel stiffness |
| Stress `STRESS` in UMAT | Hardcoded to $0.D0$ | Zeroed to prevent parallel internal force |

**Definitive Verdict**: **SITUATION B**.  
The zero error indicator in all raw UEL ODBs was caused by `SUBROUTINE UMAT` explicitly setting `STRESS(I) = 0.D0`, preventing Abaqus SPR from evaluating discretization error.
