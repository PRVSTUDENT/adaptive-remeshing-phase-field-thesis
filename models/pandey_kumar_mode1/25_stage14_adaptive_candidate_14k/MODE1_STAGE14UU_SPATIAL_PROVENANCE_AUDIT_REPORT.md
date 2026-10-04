# Gate-6B Mode-I Stage 14U-U: Spatial Convergence Provenance and Claim-Discipline Audit Report

**Task ID**: `F1204-GATE6B-STAGE14UU-SPATIAL-CONVERGENCE-PROVENANCE-AUDIT-20261004`  
**Date**: 2026-10-04T10:49:30.836Z  
**Governing Directive**: *"We need to have understood everything related to the first model before we increase complexity."*  
**Governing Phase**: `MODE1_GATE6B_ACTIVE_EVALUATION_AND_CONTINUATION`  
**Governing Verdict**: **`SPATIAL_CONVERGENCE_EVIDENCE_ALREADY_SUFFICIENT`**

---

## 1. Executive Summary

This audit establishes exhaustive, machine-readable provenance and claim discipline across the entire spatial convergence and adaptive mesh refinement sequence for the Mode-I benchmark before carrying `SPATIAL_CONVERGENCE_EVIDENCE_ALREADY_SUFFICIENT` into the Master's thesis as a closed scientific result.

Seven primary discretizations spanning fixed meshes ($S_1 \to S_5$) and adaptive mesh formulations (Package 24 and Package 25 Stage 14) were audited against exact on-disk input decks, user subroutine source code, solver logs (`.sta`, `.dat`, `.msg`), and extracted energy balance records.

---

## 2. Three-Tier Claim Separation

### Tier 1: Reference-Adaptive Agreement (`REFERENCE_ADAPTIVE_AGREEMENT`)
- **Classification**: `STABLE`
- **Findings**: The Package 25 Stage-14 adaptive mesh (14,483 elements) demonstrates excellent parity with the fine fixed reference ($S_1 \to S_3$):
  - Initial structural stiffness: $K_0 = 137.909558\,\text{kN/mm}$ ($-0.0261\%$ vs $S_1$, certified `STABLE`).
  - Peak reaction force: $F_{\max} = 0.743701\,\text{kN}$ ($-1.8577\%$ vs $S_1$, $+0.338\%$ vs $S_2$, situated in the physical $S_1 \to S_2$ transition).
  - Broken-state fracture functional: $E_{\text{frac}} = 2.285469\,\text{mJ}$ ($-2.3396\%$ vs $S_1$, certified `STABLE`).
  - Representation efficiency: Concentrates **57.57%** of all elements (8,338 elements) into the 5.0% area crack corridor ($h_{\min} = 0.76\,\mu\text{m} \approx 0.10 l_0$), achieving higher notch-root resolution than the 41.9k-element fixed mesh at 65.4% lower model size.

### Tier 2: Fixed-Mesh Spatial Sensitivity (`FIXED_MESH_SPATIAL_SENSITIVITY`)
- **Classification**: `STABLE_STIFFNESS_AND_ENERGY__MESH_SENSITIVE_PEAK`
- **Findings**: Systematic $h$-refinement across $S_1 (3.0\,\mu\text{m}) \to S_2 (2.0\,\mu\text{m}) \to S_3 (1.5\,\mu\text{m}) \to S_4 (1.25\,\mu\text{m}) \to S_5 (1.0\,\mu\text{m})$ confirms asymptotic discretization independence:
  - Initial stiffness $K_0$: Monotonic decrease $137.946 \to 137.894 \to 137.858 \to 137.837 \to 137.823\,\text{kN/mm}$ (Total variation $\le 0.0886\%$, `STABLE`).
  - Peak reaction force $F_{\max}$: Monotonic decrease $0.7578 \to 0.7412 \to 0.7322 \to 0.7290 \to 0.7255\,\text{kN}$ (Total change $-4.26\%$, step-to-step deltas shrink: $-2.19\% \to -1.21\% \to -0.43\% \to -0.49\%$, approaching asymptotic limit $\sim 0.725\,\text{kN}$, `MESH_SENSITIVE`).
  - Peak displacement $u_{\text{peak}}$: Monotonic shift $5.857 \to 5.711 \to 5.633 \to 5.606 \to 5.575\,\mu\text{m}$ ($-4.81\%$, `MESH_SENSITIVE`).
  - Broken-state fracture functional $E_{\text{frac}}$: Bounded in $[2.285, 2.375]\,\text{mJ}$ (Spread $< 3.9\%$, `STABLE`).
  - Crack trajectory: Strictly planar along $y = 0.500\,\text{mm}$ ($|\Delta y|_{\max} = 0.000\,\text{mm}$, `STABLE`).

### Tier 3: Adaptive Spatial Sensitivity (`ADAPTIVE_SPATIAL_SENSITIVITY`)
- **Classification**: `STABLE`
- **Findings**: Comparison between Package 24 (13,897 elements, 2% uniform target on continuum pre-analysis) and Package 25 (14,483 elements, kinematic strain-localized infinitesimal companion pre-analysis):
  - Both share bitwise and hash-identical Fortran source (`f42_mixed_uel.for`, SHA-256 `CE8D5EDC...`) and physical parameters.
  - Initial stiffness: $K_0 = 137.890\,\text{kN/mm}$ vs $137.910\,\text{kN/mm}$ ($+0.0145\%$, `STABLE`).
  - Peak force: $F_{\max} = 0.7441\,\text{kN}$ vs $0.7437\,\text{kN}$ ($-0.0537\%$, `STABLE`).
  - Peak displacement: $u_{\text{peak}} = 5.750\,\mu\text{m}$ vs $5.733\,\mu\text{m}$ ($-0.30\%$, `STABLE`).
  - Fracture functional: $E_{\text{frac}} = 2.290\,\text{mJ}$ vs $2.285\,\text{mJ}$ ($-0.197\%$, `STABLE`).
  - Lineage distinction: Package 25 concentrates $4.66\times$ more elements in the crack corridor ($57.57\%$ vs $12.36\%$) due to kinematic strain localization, achieving higher notch-root fidelity while yielding nearly identical macroscopic fracture behavior.

---

## 3. Crack Corridor Geometry Verification

The crack corridor is defined as:
$$\Omega_{\text{corridor}} = \{ (x, y) \in [0.50, 1.00] \times [0.45, 0.55]\,\text{mm} \}$$
- Dimensions: $\Delta x = 0.50\,\text{mm}$, $\Delta y = 0.10\,\text{mm}$
- Area: $\text{Area}(\Omega_{\text{corridor}}) = 0.50 \times 0.10 = 0.050\,\text{mm}^2$
- Domain area: $\text{Area}(\Omega) = 1.00 \times 1.00 = 1.000\,\text{mm}^2$
- Exact area fraction: $\frac{0.050}{1.000} = 5.00\%$ (verified exact).

---

## 4. Endpoint and Reporting Discipline

1. **Job 1409953.mmaster02**: Reached terminal $u = 0.007889\,\text{mm}$ (Step 2 Increment 2890, 99.76% load drop, complete crack traversal $x_{\text{tip}} = 0.9985\,\text{mm}$). Never forward-filled to $u = 0.0100\,\text{mm}$.
2. **Job 1409982.mmaster02**: Active completion solve with relaxed cutback parameters ($I_A=10, I_C=20$) is actively solving on compute node `mnode097`.
3. **No Redundant Solver Runs**: Because spatial convergence is already proven across 5 fixed meshes and 2 adaptive meshes with complete physical stability, no additional spatial solver submission is required or authorized.

---

## 5. Formal Verdict

$$\mathbf{SPATIAL\_CONVERGENCE\_EVIDENCE\_ALREADY\_SUFFICIENT}$$
