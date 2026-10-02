# ANTI-DEVIATION CARD: GATE-5 PRE-ANALYSIS LOAD SENSITIVITY INVESTIGATION

**Task ID**: `GATE5-PREANALYSIS-LOAD-SENSITIVITY-001`  
**Date**: 2026-09-10  
**Status**: ACTIVE  
**Parent Objective**: Priority Question B: Provenance audit of the 13,941 vs 71,320 element count discrepancy and investigation of pre-analysis displacement sensitivity.

---

## 1. Mathematical & Physical Hypothesis
Under Abaqus native adaptive remeshing with `sizingMethod=UNIFORM_ERROR` and `variables=('MISESERI',)`:
- The error indicator $\eta_e = \|\boldsymbol{\sigma}^* - \boldsymbol{\sigma}_h\|_{L_2}$ has dimensions of stress ($\text{MPa}$).
- In a linear elastic pre-analysis (`Step-1`, $E=210\,\text{GPa}, \nu=0.3$, $nlgeom=\text{OFF}$), all stress fields $\boldsymbol{\sigma}(\mathbf{x})$ scale strictly linearly with the applied boundary displacement $u_{\text{top}}$:
  $$\boldsymbol{\sigma}(\mathbf{x}; u_{\text{top}}) = \left(\frac{u_{\text{top}}}{u_0}\right) \boldsymbol{\sigma}(\mathbf{x}; u_0)$$
  $$\eta_e(\mathbf{x}; u_{\text{top}}) = \left(\frac{u_{\text{top}}}{u_0}\right) \eta_e(\mathbf{x}; u_0)$$
- Since the Remeshing Rule specifies a constant absolute `errorTarget = 1.0` (in stress error units), the target element size calculation is:
  $$h_{\text{new}}(\mathbf{x}) = h_{\text{old}}(\mathbf{x}) \cdot \left(\frac{\text{errorTarget}}{\eta_e(\mathbf{x})}\right)^{1/p} = h_{\text{old}}(\mathbf{x}) \cdot \left(\frac{\text{errorTarget}}{\frac{u_{\text{top}}}{u_0} \eta_e(\mathbf{x}; u_0)}\right)^{1/p}$$
- Consequently, varying the pre-analysis displacement $u_{\text{top}}$ directly shifts the mesh refinement sizing field without changing the geometric error distribution pattern.

---

## 2. Experimental Design Matrix

| Case ID | Applied $u_{\text{top}}$ | Relative Load | `errorTarget` | `minSize` | `maxSize` | `refinementFactor` | Expected Mesh Behavior |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `LOAD_0p2X` | $0.0010\,\text{mm}$ | $0.2\times$ | $1.0$ | $0.001\,\text{mm}$ | $0.020\,\text{mm}$ | $10$ | Significantly coarser / fewer elements |
| `LOAD_0p5X` | $0.0025\,\text{mm}$ | $0.5\times$ | $1.0$ | $0.001\,\text{mm}$ | $0.020\,\text{mm}$ | $10$ | Intermediate refinement density |
| `LOAD_1p0X` | $0.0050\,\text{mm}$ | $1.0\times$ (Canonical) | $1.0$ | $0.001\,\text{mm}$ | $0.020\,\text{mm}$ | $10$ | Baseline ($71,320$ elements) |
| `LOAD_2p0X` | $0.0100\,\text{mm}$ | $2.0\times$ | $1.0$ | $0.001\,\text{mm}$ | $0.020\,\text{mm}$ | $10$ | Broader saturated refinement zone |

---

## 3. Strict Verification & Invariance Checks
1. All geometry (1.0 mm $\times$ 1.0 mm square, 0.5 mm crack seam), material properties ($E=210\,\text{GPa}, \nu=0.3$), and coarse mesh seeds ($h_{\text{cms}}=0.02\,\text{mm}$) are strictly identical.
2. The running job `1404306.mmaster02` on `mnode097.cluster` remains completely undisturbed.
3. All scripts are prepared and verified in the conversation brain before cluster deployment.
