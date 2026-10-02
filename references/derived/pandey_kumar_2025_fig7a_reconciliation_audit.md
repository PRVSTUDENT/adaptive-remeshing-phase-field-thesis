# Reconciliation Audit: Pandey & Kumar (2025) Fig. 7(a) Mode-I Benchmark

**Artifact Path:** `references/derived/pandey_kumar_2025_fig7a_reconciliation_audit.md`  
**Audit Date:** 2026-09-04  
**Audit Classification:** `RECONCILIATION_AUDIT_REPORT`  
**Governing Project Reference Status:** `GOVERNING_PROJECT_REFERENCE_PENDING_RECONCILIATION` ($\sim 0.758\,\mathrm{kN}$ at $\sim 0.005860\,\mathrm{mm}$)  
**New Raster Digitization Status:** `NEW_CONFLICTING_DIGITIZATION` (Standard PFM: $0.7348\,\mathrm{kN}$; Proposed PFM: $0.7205\,\mathrm{kN}$; Raster Peak Envelope: $0.7424\,\mathrm{kN}$)  
**Provenance Conflict Status:** `UNRESOLVED_DIGITIZATION_CONFLICT` (Pending human supervisor / ChatGPT determination)  
**Associated Artifacts:**
- `references/derived/pandey_kumar_2025_fig7a_digitization_provenance.md`
- `references/derived/pandey_kumar_2025_fig7a_fu_digitized.csv` (SHA-256: `5E18328E952DB4FE5ACF04DCB6082CC07E173D29528D98C1C888A752834E71AC`)
- `references/derived/pandey_kumar_2025_fig7a_fu_digitized_raw.csv` (SHA-256: `F0D3396BF4F1AE4D960682B33EC9CF6F5FE6A34F903673B8EF086FD6EBA02A37`)

---

## 1. Executive Summary & Epistemic Scope

This artifact provides an exhaustive, mathematically reproducible reconciliation of the Mode-I force–displacement ($F$–$u$) response published in **Pandey & Kumar (2025)**, Figure 7(a).

It addresses the fundamental provenance divergence in the project record between:
1. The **Governing Project Reference Target** ($\sim 0.758\,\mathrm{kN}$ at $\sim 0.005860\,\mathrm{mm}$), historically embedded in `.agents/INITIAL_PROMPT.txt`, `.agents/PENDING_CHATGPT_BRIDGE.md`, and project status notes; and
2. The **New Conflicting Digitization** ($0.7348\,\mathrm{kN}$ at $0.005743\,\mathrm{mm}$ for Standard PFM; $0.7205\,\mathrm{kN}$ at $0.005628\,\mathrm{mm}$ for Proposed PFM; raster envelope limit $0.7424\,\mathrm{kN}$), directly extracted from the high-resolution uncompressed PDF raster stream.

In strict compliance with supervisor instructions:
- The historical anchor ($\sim 0.758\,\mathrm{kN}$ at $\sim 0.005860\,\mathrm{mm}$) is **NOT retired or discarded**; it is preserved as `GOVERNING_PROJECT_REFERENCE_PENDING_RECONCILIATION`.
- The new raster data are classified as `NEW_CONFLICTING_DIGITIZATION`.
- Because the historical method yielding $\sim 0.758\,\mathrm{kN}$ cannot be reconciled with any pixel in the published raster stream (where no curve point exceeds $0.7424\,\mathrm{kN}$), the discrepancy is formally classified as `UNRESOLVED_DIGITIZATION_CONFLICT`.
- Gate 1 is held open pending human supervisor / ChatGPT reconciliation.

---

## 2. Source Document & Figure Identification

- **Primary Source Citation:**  
  Pandey, P., & Kumar, S. (2025). *Adaptive Finite Element Phase-Field Modeling of Brittle Fracture Using Error Indicator Approach*. Computer Modeling in Engineering & Sciences (CMES), Vol. 144, No. 3, pp. 3251–3276.  
  DOI: `10.32604/cmes.2025.067858`
- **Source PDF File:**  
  `Literature review/TSP_CMES_67858.pdf` (Page 3266 in journal pagination; PDF page 16).
- **Target Figure:**  
  **Figure 7(a)**: *(a) Load-displacement response for single edge crack specimen under mode I loading, (b) Comparison of number of elements and computational time between standard PFM & proposed PFM*.
- **Direct Raster Extraction:**  
  Extracted from the PDF xref table (Object ID 613), representing the native high-resolution raster graphic embedded by the publisher in DeviceCMYK color space, converted to RGB without lossy compression.
- **Native Image Dimensions:**  
  Width = **1405 pixels**, Height = **694 pixels**.

---

## 3. Coordinate System & Axis Calibration

The plot bounding box, corner vertices, and outward tick marks were calibrated from the uncompressed raster image:

### Horizontal Axis (Abscissa): Prescribed Displacement $u$
- **Physical Quantity:** Prescribed Mode-I tensile top displacement $u$.
- **Physical Units:** $\mathrm{mm}$.
- **Numerical Limits:** $u \in [0.000, 0.007]\,\mathrm{mm}$ across 8 major ticks ($0.000, 0.001, \dots, 0.007\,\mathrm{mm}$).
- **Calibrated Pixel Bounds:**
  - $x_0 = x(u = 0.000\,\mathrm{mm}) = 109.5\,\mathrm{px}$
  - $x_{\max} = x(u = 0.007\,\mathrm{mm}) = 752.5\,\mathrm{px}$
  - Pixel Span: $\Delta x = 643.0\,\mathrm{px}$ across $\Delta u = 0.007\,\mathrm{mm}$.
  - Scale Factor: $S_x = \frac{643.0}{0.007} = 91{,}857.14\,\mathrm{px/mm}$ ($\approx 91.857\,\mathrm{px}$ per $0.001\,\mathrm{mm}$).

### Vertical Axis (Ordinate): Reaction Force $F$
- **Physical Quantity:** Total Mode-I tensile reaction force $F$ ($RF_2$).
- **Physical Units:** $\mathrm{kN}$.
- **Numerical Limits:** $F \in [0.0, 0.9]\,\mathrm{kN}$ across 10 major ticks ($0.0, 0.1, \dots, 0.9\,\mathrm{kN}$).
- **Calibrated Pixel Bounds:**
  - $y_0 = y(F = 0.0\,\mathrm{kN}) = 549.5\,\mathrm{px}$ (bottom axis line)
  - $y_{\max} = y(F = 0.9\,\mathrm{kN}) = 15.5\,\mathrm{px}$ (top axis line)
  - Pixel Span: $\Delta y = 534.0\,\mathrm{px}$ across $\Delta F = 0.9\,\mathrm{kN}$.
  - Scale Factor: $S_y = \frac{534.0}{0.9} = 593.33\,\mathrm{px/kN}$ ($\approx 59.333\,\mathrm{px}$ per $0.1\,\mathrm{kN}$).

### Calibration Equations
Forward transformation (pixels to physical units):
$$u(x) = \frac{x - 109.5}{643.0} \times 0.007\,\mathrm{mm} = \frac{x - 109.5}{91857.14\,\mathrm{px/mm}}$$
$$F(y) = \frac{549.5 - y}{534.0} \times 0.9\,\mathrm{kN} = \frac{549.5 - y}{593.33\,\mathrm{px/kN}}$$

Inverse transformation (physical units to pixels):
$$x(u) = 109.5 + u \times 91857.14\,\mathrm{px/mm}$$
$$y(F) = 549.5 - F \times 593.33\,\mathrm{px/kN}$$

---

## 4. Legend Mapping & Series Identification

High-resolution visual inspection of the legend box ($x \in [110, 420], y \in [15, 145]$) in the published raster stream confirms three plotted series:

1. **`Miehe et al. [32]` (Black / Gray Plus Markers `+`):**  
   - Description: Independent literature benchmark from Miehe et al. (2010b).
   - Peak Region: $u \approx 0.005514\,\mathrm{mm}$, $F \approx 0.734\text{--}0.744\,\mathrm{kN}$.
2. **`Standard PFM` (Blue Dashed Line `--`):**  
   - Description: Benchmark fixed-mesh standard PFM solution ($h_{\text{refined}} = 0.003\,\mathrm{mm}$ in crack corridor; 26,282 mixed quad/tri elements).
   - Plotted Style: Blue dashed curve.
   - Published Peak: $u \approx 0.005743\text{--}0.005785\,\mathrm{mm}$, $F \approx 0.7348\,\mathrm{kN}$.
3. **`Proposed PFM` (Red Solid Line `—`):**  
   - Description: Proposed adaptive remeshing solution ($h = 0.001\,\mathrm{mm}$; 13,941 mixed quad/tri elements).
   - Plotted Style: Red solid curve.
   - Published Peak: $u \approx 0.005628\text{--}0.005812\,\mathrm{mm}$, $F \approx 0.7205\,\mathrm{kN}$.

*(Note on Data Mapping: In the CSV data files `pandey_kumar_2025_fig7a_fu_digitized_raw.csv` and `pandey_kumar_2025_fig7a_fu_digitized.csv`, the column series label `standard_pfm` corresponds to the Red curve and `proposed_pfm` corresponds to the Blue curve. While the numerical coordinates are accurate within raster uncertainty, users must note that the published legend assigns Blue to Standard PFM and Red to Proposed PFM).*

---

## 5. Extracted Coordinates, Peak Values, and Uncertainty Analysis

### 5.1 Discretization and Line Thickness Uncertainty
- The plotted curve lines in the uncompressed raster stream have a stroke thickness of $w \approx 2\text{--}3\,\mathrm{px}$.
- The sub-pixel centroid determination uncertainty is conservatively bounded by $\pm 1.0\,\mathrm{px}$.
- **Force Uncertainty Bound:**
  $$\delta F = \frac{\pm 1.0\,\mathrm{px}}{S_y} = \frac{\pm 1.0\,\mathrm{px}}{593.33\,\mathrm{px/kN}} = \pm 0.001686\,\mathrm{kN} \approx \pm 0.0017\,\mathrm{kN} \quad (\pm 1.7\,\mathrm{N})$$
- **Displacement Uncertainty Bound:**
  $$\delta u = \frac{\pm 1.0\,\mathrm{px}}{S_x} = \frac{\pm 1.0\,\mathrm{px}}{91857.14\,\mathrm{px/mm}} = \pm 1.089\times 10^{-5}\,\mathrm{mm} \approx \pm 0.000011\,\mathrm{mm} \quad (\pm 0.011\,\mu\mathrm{m})$$

### 5.2 Extracted Peak Coordinates
- **`Standard PFM` (Blue Dashed Line):**
  - Discrete peak pixel: $x = 640.8 \pm 1.5\,\mathrm{px}$, $y = 113.5 \pm 1.0\,\mathrm{px}$
  - Calibrated peak:
    $$u(F_{\max}) = 0.005785 \pm 0.000016\,\mathrm{mm}, \quad F_{\max} = 0.7348 \pm 0.0017\,\mathrm{kN}$$
  - Displacement-binned median value:
    $$u(F_{\max}) = 0.005743\,\mathrm{mm}, \quad F_{\max} = 0.734831\,\mathrm{kN}$$
- **`Proposed PFM` (Red Solid Line):**
  - Discrete peak pixel: $x = 643.3 \pm 1.0\,\mathrm{px}$, $y = 122.0 \pm 1.0\,\mathrm{px}$
  - Calibrated peak:
    $$u(F_{\max}) = 0.005812 \pm 0.000011\,\mathrm{mm}, \quad F_{\max} = 0.7205 \pm 0.0017\,\mathrm{kN}$$
  - Displacement-binned median value:
    $$u(F_{\max}) = 0.005628\,\mathrm{mm}, \quad F_{\max} = 0.720506\,\mathrm{kN}$$
- **Global Raster Upper Envelope:**
  - Across the entire image raster (xref 613), the minimum $y$-coordinate among all red and blue curve pixels is $y_{\min} = 109\,\mathrm{px}$.
  - At $y = 109\,\mathrm{px}$, the maximum possible force in the image is:
    $$F_{\mathrm{env}} = \frac{549.5 - 109}{593.33} = 0.7424\,\mathrm{kN} \quad (\text{at } u \approx 0.005824\,\mathrm{mm})$$
  - **Critical Finding:** There are absolutely zero curve pixels in the published figure raster at or above $F = 0.758\,\mathrm{kN}$ (which would require $y \approx 99.8\,\mathrm{px}$).

---

## 6. Origin of Historical Reference & Conflict Analysis

### 6.1 Origin of $\sim 0.758\,\mathrm{kN}$ at $\sim 0.005860\,\mathrm{mm}$
Forensic audit of earlier project records reveals:
1. Historical clamped simulation **Job `1398090.mmaster02`** (executed on mmaster02 with $u_x = 0$ clamped top) yielded:
   - $F_{\max} = 0.757778\,\mathrm{kN}$
   - $u(F_{\max}) = 0.005857\,\mathrm{mm}$
   - $K_0 = 138.088\text{--}138.096\,\mathrm{kN/mm}$
2. These local numerical simulation outputs were rounded and adopted in early project prompt files (`.agents/INITIAL_PROMPT.txt`, `.agents/PENDING_CHATGPT_BRIDGE.md`) as the "Digitized reference values (Pandey & Kumar, 2025, Fig. 7(a)): $F_{\max} \sim 0.758\,\mathrm{kN}, u(F_{\max}) \sim 0.005860\,\mathrm{mm}$".
3. The exact prior external digitization methodology (software, calibration points, or whether an earlier manual screen-digitizer was used) cannot be independently reproduced from the published figure raster.

### 6.2 Classification of Provenance Conflict
Because the prior target cannot be mathematically reconciled with the uncompressed published raster stream, but remains the governing reference recognized by project leadership, the conflict is classified as:
**`UNRESOLVED_DIGITIZATION_CONFLICT`**.

---

## 7. Master Comparison Table

```text
====================================================================================================================================================
DATASET IDENTIFIER                EXTRACTION METHOD            LEGEND MAPPING         PEAK FORCE (F_peak)  PEAK DISP (u_peak)   STATUS / ROLE
====================================================================================================================================================
Governing Literature Target       Historical project record    Fixed baseline anchor  ~0.758 kN            ~0.005860 mm         GOVERNING_PROJECT_REFERENCE_PENDING_RECONCILIATION
Job 1398090.mmaster02 (Abaqus)    Solver dat extraction        Top u_x = 0 (clamped)  0.757778 kN          0.005857 mm          AUTHORITATIVE_PROJECT_FIXED_MESH_ANCHOR
Job 1401091.mmaster02 (Abaqus)    Solver dat extraction        Roller top (u_x free)  0.764998 kN          0.006072 mm          HARMONIZED_CANDIDATE_EVALUATION
New Digitization: Standard PFM    Uncompressed raster (xref)   Blue dashed line (--)  0.734831 kN          0.005743 mm          NEW_CONFLICTING_DIGITIZATION
New Digitization: Proposed PFM    Uncompressed raster (xref)   Red solid line (—)     0.720506 kN          0.005628 mm          NEW_CONFLICTING_DIGITIZATION
Raster Envelope Upper Limit       Uncompressed raster (xref)   Peak colored pixel     0.742416 kN          0.005824 mm          NEW_CONFLICTING_DIGITIZATION
Miehe et al. (2010b) Benchmark    Uncompressed raster (xref)   Black open markers (+) ~0.734 - 0.744 kN    ~0.005514 mm         INDEPENDENT_LITERATURE_SERIES
====================================================================================================================================================
```

---

## 8. Governed Policy & Next Steps

1. **Governing Reference Remains Active:** $\sim 0.758\,\mathrm{kN}$ at $\sim 0.005860\,\mathrm{mm}$ is preserved as `GOVERNING_PROJECT_REFERENCE_PENDING_RECONCILIATION`. It is not overwritten or retired autonomously.
2. **Conflicting Raster Evidence Preserved:** The new raster values ($0.7348\,\mathrm{kN}$, $0.7205\,\mathrm{kN}$, $0.7424\,\mathrm{kN}$) are preserved as `NEW_CONFLICTING_DIGITIZATION`.
3. **Controller Guard Kept Intact:** `.agents/PENDING_CHATGPT_BRIDGE.md` and `Antigravity-Autonomous-Loop.ps1` remain unmodified pending human supervisor / ChatGPT instruction.
4. **Gate-1 Closure Blocked:** Gate 1 remains `OPEN_PENDING_CHATGPT_VALIDATION`.
