# Digitization Provenance: Pandey & Kumar (2025) Fig. 7(a) Mode-I F-u Response

**Artifact Name:** `pandey_kumar_2025_fig7a_digitization_provenance.md`  
**Classification:** `digitized_raster_reference`  
**Governing Project Reference:** $\sim 0.758\,\mathrm{kN}$ at $\sim 0.005860\,\mathrm{mm}$ (`GOVERNING_PROJECT_REFERENCE_PENDING_RECONCILIATION`)  
**New Conflicting Digitization Status:** `NEW_CONFLICTING_DIGITIZATION` (Pending human/supervisor reconciliation)  
**Conflict Classification:** `UNRESOLVED_DIGITIZATION_CONFLICT`  
**Dedicated Reconciliation Audit:** `references/derived/pandey_kumar_2025_fig7a_reconciliation_audit.md`  
**Associated Data Files:**
- `references/derived/pandey_kumar_2025_fig7a_fu_digitized_raw.csv` (SHA-256: `F0D3396BF4F1AE4D960682B33EC9CF6F5FE6A34F903673B8EF086FD6EBA02A37`)
- `references/derived/pandey_kumar_2025_fig7a_fu_digitized.csv` (SHA-256: `5E18328E952DB4FE5ACF04DCB6082CC07E173D29528D98C1C888A752834E71AC`)

---

## 1. Source Document & Figure Identification

- **Full Citation:**  
  Pandey, P., & Kumar, S. (2025). *Adaptive Finite Element Phase-Field Modeling of Brittle Fracture Using Error Indicator Approach*. Computer Modeling in Engineering & Sciences (CMES), Vol. 144, No. 3, pp. 3251–3276.  
  DOI: `10.32604/cmes.2025.067858`
- **Local PDF Source:**  
  `Literature review/TSP_CMES_67858.pdf` (Page 3266 in journal pagination; PDF page 16).
- **Target Figure:**  
  **Figure 7(a)**: *(a) Load-displacement response for single edge crack specimen under mode I loading, (b) Comparison of number of elements and computational time between standard PFM & proposed PFM*.

### Plotted Series & Re-Audited Visual Mapping (Updated 2026-09-04)
High-resolution pixel cropping of the published legend box directly from the PDF raster stream (xref 613, resolution $1405 \times 694\,\text{px}$) confirms the exact publication mapping:
1. **`miehe_et_al_2010` (Open Plus Markers `+`):**  
   Legend Entry 1: Black/gray plus markers (`+`) representing the independent benchmark from Miehe et al. (2010) [citation 32]. Peak occurs at $u \approx 0.005514\,\text{mm}$, $F \approx 0.734\text{--}0.744\,\text{kN}$.
2. **`standard_pfm` (Blue Dashed Line `--`):**  
   Legend Entry 2: **Blue dashed curve (`--`)** representing the benchmark fixed-mesh standard PFM solution ($h_{\text{refined}} = 0.003\,\mathrm{mm}$ in crack corridor; 26,282 mixed elements). Discrete peak occurs at $u = 0.005785 \pm 0.000016\,\mathrm{mm}$, $F = 0.7348 \pm 0.0017\,\mathrm{kN}$ (binned median: $u = 0.005743\,\mathrm{mm}, F = 0.734831\,\mathrm{kN}$).
3. **`proposed_pfm` (Red Solid Line `—`):**  
   Legend Entry 3: **Red solid curve (`—`)** representing the proposed adaptive remeshing solution ($h = 0.001\,\mathrm{mm}$; 13,941 mixed elements). Discrete peak occurs at $u = 0.005812 \pm 0.000011\,\mathrm{mm}$, $F = 0.7205 \pm 0.0017\,\mathrm{kN}$ (binned median: $u = 0.005628\,\mathrm{mm}, F = 0.720506\,\mathrm{kN}$).

*(Note on Data Mapping: In the CSV data files `pandey_kumar_2025_fig7a_fu_digitized_raw.csv` and `pandey_kumar_2025_fig7a_fu_digitized.csv`, the column series label `standard_pfm` corresponds to the Red curve ($0.7205\,\mathrm{kN}$) and `proposed_pfm` corresponds to the Blue curve ($0.7348\,\mathrm{kN}$). While the numerical coordinates are accurate within raster uncertainty, users must note that the published legend assigns Blue to Standard PFM and Red to Proposed PFM).*

---

## 2. Coordinate System & Axis Calibration

The plot bounding box and outward tick marks were calibrated from the uncompressed raster stream (xref 613, resolution $1405 \times 694\,\text{px}$):

### Horizontal Axis (Abscissa): Prescribed Displacement $u$
- **Physical Quantity:** Mode-I tensile prescribed displacement $u$.
- **Physical Units:** $\text{mm}$.
- **Axis Range:** $0.000\,\text{mm} \le u \le 0.007\,\text{mm}$ across 8 major ticks ($0.000$ to $0.007\,\text{mm}$).
- **Calibrated Pixel Bounds:**
  - $x(u = 0.000\,\text{mm}) = 109.5\,\text{px}$
  - $x(u = 0.007\,\text{mm}) = 752.5\,\text{px}$
  - Pixel span: $\Delta x = 643.0\,\text{px}$ across $\Delta u = 0.007\,\text{mm}$.
  - Scale factor: $S_x = \frac{643.0}{0.007} = 91{,}857.14\,\text{px/mm}$ ($\approx 91.857\,\text{px}$ per $0.001\,\text{mm}$).
- **Transformation Formula:**
  $$u(x) = \frac{x - 109.5}{643.0} \times 0.007\,\text{mm}$$

### Vertical Axis (Ordinate): Reaction Force $F$
- **Physical Quantity:** Total Mode-I tensile reaction force $F$ ($RF_2$).
- **Physical Units:** $\text{kN}$.
- **Axis Range:** $0.0\,\text{kN} \le F \le 0.9\,\text{kN}$ across 10 major ticks ($0.0$ to $0.9\,\text{kN}$).
- **Calibrated Pixel Bounds:**
  - $y(F = 0.0\,\text{kN}) = 549.5\,\text{px}$ (bottom axis line)
  - $y(F = 0.9\,\text{kN}) = 15.5\,\text{px}$ (top axis line)
  - Pixel span: $\Delta y = 534.0\,\text{px}$ across $\Delta F = 0.9\,\mathrm{kN}$.
  - Scale factor: $S_y = \frac{534.0}{0.9} = 593.33\,\text{px/kN}$ ($\approx 59.33\,\text{px}$ per $0.1\,\text{kN}$).
- **Transformation Formula:**
  $$F(y) = \frac{549.5 - y}{534.0} \times 0.9\,\text{kN}$$

---

## 3. Digitization Methodology & Processing Pipeline

1. **Raster Stream Extraction:**  
   The image stream (xref 613, DeviceCMYK converted to RGB without lossy compression) was extracted directly via PyMuPDF and Pillow.
2. **Legend Masking:**  
   The legend box ($x \in [110, 420], y \in [15, 145]$) was masked to isolate curve trajectories from legend line samples.
3. **Color Segmentation:**  
   - Red trajectory: $R > 130, G < 110, B < 110$.
   - Blue trajectory: $B > 130, R < 110, G < 130$.
4. **Data Artifacts Produced:**
   - **Raw Extraction (`pandey_kumar_2025_fig7a_fu_digitized_raw.csv`):**  
     Contains all 2,549 identified pixels (1,272 red pixels; 1,277 blue pixels).
   - **Processed Curve (`pandey_kumar_2025_fig7a_fu_digitized.csv`):**  
     Binned by displacement with uniform bin width $\Delta u = 0.00005\,\text{mm}$ ($0.05\,\mu\text{m}$). Each bin reports the median $u$ and median $F$ without artificial numerical smoothing:
     * Red Curve: 105 processed bins covering $u \in [0.000093, 0.006973]\,\text{mm}$. Peak: $u = 0.005628\,\text{mm}, F = 0.7205\,\text{kN}$.
     * Blue Curve: 133 processed bins covering $u \in [0.000038, 0.006924]\,\text{mm}$. Peak: $u = 0.005743\,\text{mm}, F = 0.7348\,\text{kN}$.

---

## 4. Multi-Reference Digitization Reconciliation

```text
====================================================================================================================================================
DATASET IDENTIFIER                EXTRACTION METHOD            LEGEND MAPPING         PEAK FORCE (F_peak)  PEAK DISP (u_peak)   STATUS
====================================================================================================================================================
Historical Literature Target      Draft reports / prompt       Fixed baseline anchor  ~0.758 kN            ~0.005860 mm         GOVERNING_PROJECT_REFERENCE_PENDING_RECONCILIATION
Job 1398090.mmaster02 (Abaqus)    Solver dat extraction        Top u_x = 0 (clamped)  0.757778 kN          0.005857 mm          AUTHORITATIVE_PROJECT_FIXED_MESH_ANCHOR
Job 1401091.mmaster02 (Abaqus)    Solver dat extraction        Roller top (u_x free)  0.764998 kN          0.006072 mm          HARMONIZED_CANDIDATE_EVALUATION
New Digitization: Standard PFM    Uncompressed raster (xref)   Blue dashed line (--)  0.734831 kN          0.005743 mm          NEW_CONFLICTING_DIGITIZATION
New Digitization: Proposed PFM    Uncompressed raster (xref)   Red solid line (—)     0.720506 kN          0.005628 mm          NEW_CONFLICTING_DIGITIZATION
Raster Envelope Upper Limit       Uncompressed raster (xref)   Peak colored pixel     0.742416 kN          0.005824 mm          NEW_CONFLICTING_DIGITIZATION
Miehe et al. (2010b) Benchmark    Uncompressed raster (xref)   Black open markers (+) ~0.734 - 0.744 kN    ~0.005514 mm         INDEPENDENT_LITERATURE_SERIES
====================================================================================================================================================
```

### Reconciliation Findings & Governed Policy
1. **Governing Reference Remains Active:**  
   The project record continues to recognize $\sim 0.758\,\mathrm{kN}$ at $\sim 0.005860\,\mathrm{mm}$ as the **`GOVERNING_PROJECT_REFERENCE_PENDING_RECONCILIATION`**. In accordance with supervisor directives, this value is **not** overwritten or deleted autonomously.
2. **Identification of Discrepancy Origin:**  
   The numerical value $F_{\text{peak}} = 0.757778\,\mathrm{kN}$ at $u = 0.005857\,\mathrm{mm}$ is identical to the output of local clamped baseline Job `1398090.mmaster02`. Earlier project notes adopted this numerical simulation output as the literature check value.
3. **Conflict Status:**  
   The newly re-digitized values from Fig. 7(a) (Standard PFM: $0.734831\,\mathrm{kN}$; Proposed PFM: $0.720506\,\mathrm{kN}$; Raster envelope limit: $0.742416\,\mathrm{kN}$) are classified as **`NEW_CONFLICTING_DIGITIZATION`** and submitted for **human / ChatGPT supervision review**. The conflict is classified as **`UNRESOLVED_DIGITIZATION_CONFLICT`**. Both datasets are preserved transparently in the repository.
