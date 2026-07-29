# Pandey & Kumar (2025) Remeshing Formulation & Parameter Audit

**Date:** 2026-07-29  
**Protocol Version:** 1  
**Author:** `gemini-antigravity`  
**Status:** `formulation_and_parameter_audit_completed`

---

## 1. Context & Method Overview

Pandey and Kumar (2025) propose a Python-driven adaptive remeshing methodology for phase-field fracture simulations using Abaqus native error indicators.

Because Abaqus User Elements (`UEL`) do not natively evaluate built-in stress recovery error indicators (`MISESERI`), the Pandey-Kumar workflow uses a **coarse auxiliary-continuum pre-analysis** stage on standard continuum elements (`CPS4`) to calculate the stress discretization error field, followed by an Abaqus adaptive remeshing rule execution to generate a locally refined mesh prior to running the phase-field solver.

---

## 2. Benchmark Plane-Stress Formulation & Parity Verification

| Parameter / Feature | Specification | Category | Rationale & Parity Justification |
|---|---|---|---|
| **Element Type** | `CPS4` (4-node plane stress) | **project decision** | Chosen for 100% elastic matrix $\mathbf{D}$ parity with the Molnár & Gravouil (2017) baseline benchmark ($1.0\text{ mm}$ thickness, plane stress). `CPE4` (plane strain) would introduce an out-of-plane stress constraint $\sigma_{33} = \nu(\sigma_{11} + \sigma_{22})$ inconsistent with the reference benchmark. |
| **Pre-Analysis Continuum** | Standard linear elastic material ($E = 210\text{ kN/mm}^2, \nu = 0.3$) | **Abaqus/API-required** | Required because UEL user elements do not support built-in Abaqus `MISESERI` output. |
| **Notch Topology** | True physical slit ($y=0, x \in [-0.5, 0.0]\text{ mm}$) | **Abaqus/API-required** | 15 coincident node pairs along the notch faces ($y=0.0$), 0 shared nodes across the slit, Node 2 $(0,0)$ as single shared notch tip node. |
| **Pre-Analysis Load Level** | Elastic load stage ($U_1 = 0.001\text{ mm}$) | **project decision** | Evaluates stress concentration around notch tip prior to damage initiation ($d \ge 0.5$). |

---

## 3. Parameter Categorization & Source Traceability Audit

| Parameter | Value | Audit Category | Exact Source / Rationale |
|---|---|---|---|
| `errorTarget` | `0.05` (5%) | **sensitivity parameter** | Initial order-of-magnitude target for relative von Mises SPR recovery error indicator; to be evaluated in Stage C sensitivity studies. |
| `refinementFactor` | `2.0` | **project decision** | Achieves factor-of-two size reduction moving local resolution from $h_0 = 0.005\text{ mm}$ to $h_1 = 0.0025\text{ mm}$ in a single pass. |
| `minElementSize` | `0.0025 mm` ($h_1$) | **project decision** | Floors local element resolution at the $H_1$ uniform reference resolution ($0.0025\text{ mm}$). |
| `maxElementSize` | `0.025 mm` | **project decision** | Hard upper bound preserving far-field element scale ($0.025\text{ mm}$). |
| `remeshingPasses` | `1` | **project decision** | Single-pass pre-refinement for clean cost/accuracy evaluation relative to uniform reference. |
| `coarsening` | `false` (disabled) | **project decision** | Prevents coarsening low-error background regions. |
| `pre-analysis U1` | `0.001 mm` | **project decision** | Pre-peak linear elastic load stage (~8.3% of $U_{1,\mathrm{peak}}$). |

> [!IMPORTANT]
> None of the quantitative values above (`errorTarget = 0.05`, `minElementSize = 0.0025 mm`, etc.) are claimed as direct numerical constants from Pandey & Kumar (2025). They represent **project-specific choices** designed for the Molnár $H_0 \to H_1$ benchmark campaign.

---

## 4. Validated Field Output Syntax

The auxiliary `CPS4` pre-analysis deck specifies the following field output requests:

```inp
*Output, field, frequency=1
*Node Output
 U, RF
*Element Output, elset=All_elem
 MISESERI, MISESAVG, S, E, EVOL
```

- `MISESERI`: SPR-based (Superconvergent Patch Recovery) von Mises stress discretization error indicator.
- `MISESAVG`: Average element von Mises stress.
- `S`: Stress tensor components ($S_{11}, S_{22}, S_{33}, S_{12}$).
- `E`: Total strain tensor components ($E_{11}, E_{22}, E_{33}, E_{12}$).
- `EVOL`: Element volume.
- `U`, `RF`: Nodal displacement and reaction force vectors.
