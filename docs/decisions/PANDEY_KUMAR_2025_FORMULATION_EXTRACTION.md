# Pandey & Kumar (2025) Remeshing Formulation Extraction & Specifications

**Date:** 2026-07-29  
**Protocol Version:** 1  
**Author:** `gemini-antigravity`  
**Status:** `formulation_extracted_for_stage_f3_prep`  

---

## 1. Context & Method Overview

Pandey and Kumar (2025) propose a Python-driven adaptive remeshing methodology for phase-field fracture simulations using Abaqus native error indicators. 

Because Abaqus User Elements (`UEL`) do not natively evaluate built-in stress recovery error indicators (`MISESERI`), the Pandey-Kumar workflow uses a **coarse auxiliary-continuum pre-analysis** stage on standard continuum elements (`CPS4`) to calculate the stress discretization error field, followed by an Abaqus adaptive remeshing rule execution to generate a locally refined mesh prior to running the phase-field solver.

---

## 2. Formulation & Output Requirements

| Parameter / Feature | Specification | Scientific Rationale |
|---|---|---|
| **Pre-Analysis Continuum** | Standard `CPS4` 4-node plane stress continuum elements | Required because UELs do not support native Abaqus `MISESERI` output. |
| **Material Properties** | Elastic auxiliary continuum ($E = 210\text{ kN/mm}^2, \nu = 0.3$) | Matches linear elastic properties of phase-field matrix before damage. |
| **Pre-Analysis Load Level** | Elastic load stage ($U_1 = 0.001\text{ mm}$, ~8.3% of $U_{1,\mathrm{peak}}$) | Evaluates stress concentration around notch tip prior to damage initiation ($d \ge 0.5$). |
| **Field Output Requests** | `*Element Output`: `MISESERI`, `MISESAVG`, `S`, `E` | `MISESERI` represents the SPR-based (Superconvergent Patch Recovery) von Mises stress discretization error indicator. |

---

## 3. Adaptive Remeshing Rule Settings

| Parameter | Value | Description & Constraints |
|---|---|---|
| `errorTarget` | `0.05` (5%) | Target relative von Mises stress recovery error. |
| `refinementFactor` | `2.0` | Sizing aggressiveness factor per pass. |
| `minElementSize` | `0.0025 mm` ($h_1$) | Hard lower bound; floors local refinement at $H_1$ resolution. |
| `maxElementSize` | `0.025 mm` | Hard upper bound; preserves far-field mesh sizing. |
| `remeshingPasses` | `1` | One-pass pre-refinement from coarse $H_0$ to local $H_1$. |
| `coarsening` | `false` (disabled) | Prevents unintended coarsening of far-field elements. |

---

## 4. Element Set & Field Mapping Rules

1. **Pre-Analysis Mesh (Auxiliary):** Standard `CPS4` elements defined over `elset=All_elem`. `MISESERI` indicator is computed at standard integration points and output to ODB.
2. **Remeshing Rule Application:** Abaqus CAE / Python API reads `MISESERI` from the ODB and applies the remeshing rule to refine the mesh locally around the notch corridor.
3. **Phase-Field Mesh Synthesis:** The exported refined mesh nodes and elements are processed by Python model generator `build_miseseri_preanalysis_package.py` to construct the 3-layer UEL structure (`U1` phase field, `U2` displacement, `CPS4` visualization layer) for phase-field FE analysis.
