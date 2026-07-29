# Standalone Audit Report: Mode-II H0–H1 Parity and Initial Stiffness Discrepancy

**Date:** 2026-07-29  
**Protocol Version:** 1  
**Author:** `gemini-antigravity`  
**Status:** `h0_h1_mesh_convergence_claims_blocked`  

---

## 1. Executive Summary

A systematic audit was conducted to investigate the ~72% discrepancy in initial shear stiffness between the Stage F Mode-II baseline H0 mesh ($K_{0,\mathrm{H0}} \approx 46.24\text{ kN/mm}$) and the uniform reference H1 mesh ($K_{0,\mathrm{H1}} \approx 12.83\text{ kN/mm}$).

**Key Finding:** The stiffness difference is **not** caused by ordinary physical mesh refinement ($h_0 = 0.005\text{ mm} \to h_1 = 0.0025\text{ mm}$). Instead, it is an artifact of **notch topology omission** in the legacy H0 mesh deck:
- **H0 Deck:** Contains zero duplicated node pairs along the notch line $y=0, x \in [-0.5, 0.0]\text{ mm}$. The upper and lower domains are topologically continuous across the notch line, causing the specimen to respond as an un-notched solid continuum.
- **H1 Deck:** Contains 32 duplicated node pairs (`notch_lower_face` vs `notch_upper_face`) along the notch line $y=0, x \in [-0.5, 0.0]\text{ mm}$, forming a true physical slit/notch that allows free displacement and stress concentration.

**Decision & Limitation:** Any scientific claim of spatial mesh convergence between H0 and H1 is **EXPLICITLY BLOCKED** until an H0 mesh deck with corrected notch topology is generated and evaluated.

---

## 2. Comparative Audit Matrix

| Parameter / Feature | H0 Mesh (`ModeII_H0_endpoint_corrected_serial`) | H1 Mesh (`m2h1_u015` / `ModeII_H1_uniform_serial`) | Parity Status |
|---|---|---|---|
| **Domain Geometry** | $1.0\text{ mm} \times 1.0\text{ mm}$ ($X, Y \in [-0.5, 0.5]$) | $1.0\text{ mm} \times 1.0\text{ mm}$ ($X, Y \in [-0.5, 0.5]$) | **IDENTICAL** |
| **Specimen Thickness** | $1.0\text{ mm}$ ($h = 1.0$) | $1.0\text{ mm}$ ($h = 1.0$) | **IDENTICAL** |
| **Element Count ($N_{\mathrm{elem}}$)** | 3,930 U1, 3,930 U2, 3,930 CPS4 | 12,064 U1, 12,064 U2, 12,064 CPS4 | Refined ($h_1 = h_0 / 2$) |
| **Node Count ($N_{\mathrm{nodes}}$)** | 3,998 | 12,381 | Refined |
| **Coincident Duplicate Nodes** | **0** | **32 pairs** (64 nodes along $y=0, x \in [-0.5, 0.0]$) | **MISMATCH (Critical)** |
| **Notch Topology** | Continuous continuum (no slit) | Physical cut/slit (duplicated face nodes) | **MISMATCH (Critical)** |
| **Material Properties ($E, \nu$)** | $E = 210\text{ kN/mm}^2, \nu = 0.3$ | $E = 210\text{ kN/mm}^2, \nu = 0.3$ | **IDENTICAL** |
| **Phase Field ($l_c, G_c$)** | $l_c = 0.015\text{ mm}, G_c = 0.0027\text{ kN/mm}$ | $l_c = 0.015\text{ mm}, G_c = 0.0027\text{ kN/mm}$ | **IDENTICAL** |
| **UEL Fortran Code** | Staggered UEL (U1 phase, U2 displacement) | Staggered UEL (U1 phase, U2 displacement) | **IDENTICAL** (except `N_ELEM`) |
| **Boundary Conditions** | Bottom $U_1=U_2=0$, Top $U_2=0$, Top $U_1=\mathrm{RP}$ | Bottom $U_1=U_2=0$, Top $U_2=0$, Top $U_1=\mathrm{RP}$ | **IDENTICAL** |
| **Initial Stiffness ($K_0$)** | **$46.24\text{ kN/mm}$** | **$12.83\text{ kN/mm}$** | **DISCREPANT (~72%)** |

---

## 3. Detailed Technical Analysis

### 3.1 Notch Topology Mechanism
In linear elastic fracture mechanics (LEFM) and phase-field fracture modeling, an initial notch is represented by duplicating nodes along the crack faces so that upper and lower elements are uncoupled prior to damage propagation. 

- In **H1**, 32 node pairs along $y=0, x \in [-0.5, 0.0]\text{ mm}$ are separated into `notch_upper_face` (nodes 6060, 6062, ...) and `notch_lower_face` (nodes 6059, 6061, ...). Under shear displacement $U_1$, the notch faces slide past each other freely, concentrating shear stress at the notch tip ($x = 0.0, y = 0.0$).
- In **H0**, nodes along $y=0, x \in [-0.5, 0.0]\text{ mm}$ were generated as single continuous nodes. Consequently, the left half of the specimen carries full shear stress, preventing notch opening/sliding and drastically overestimating initial shear stiffness ($46.24\text{ kN/mm}$ vs $12.83\text{ kN/mm}$).

### 3.2 UEL Code & Material Property Parity
Direct byte-level and diff inspection of `ModeII_H0_endpoint_corrected_serial.for` and `m2h1_u015.for` confirmed that the Fortran UEL implementation for `U1` (phase field) and `U2` (displacement field) is 100% identical. The property vector passed to `U2` (`210, 0.3, 1.0, 1e-07`) and `U1` (`0.015, 0.0027, 1.0`) is identical in property order, units, and values.

---

## 4. Policy & Scientific Action Items

1. **Mesh Convergence Restriction:** No spatial mesh-convergence rates or $H_0 \to H_1$ error metrics may be claimed in thesis documentation until an $H_0$ deck with 16 duplicated notch-face node pairs is generated and benchmarked.
2. **Reference Mesh Freeze:** The $H_1$ uniform reference mesh ($N_{\mathrm{elem}} = 12,064$) with true notch topology is confirmed as the valid baseline for all Mode-II benchmark studies.
