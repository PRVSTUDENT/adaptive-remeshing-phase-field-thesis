# Mode-I Gate 6: Reference Reproduction with Adaptive Refinement & Master Scientific Synthesis

**Authoritative Gate Status**: `GATE6_REFERENCE_REPRODUCTION_PARTIALLY_QUALIFIED`  
**Execution Timestamp**: 2026-09-10T08:00:00+02:00  
**HPC Job Status**: 0 Active PBS Jobs (Queue IDLE)  
**Scientific Question**: *"Does the native adaptive Mode-I solution reproduce the qualified fixed-mesh reference response to an acceptable accuracy, and at what computational cost?"*

---

## 1. Executive Summary & Mandatory Benchmark Anchor

### 1.1 Mandatory Reference Anchor Statement
> **Mandatory Benchmark Anchor**: *"This is the reference response that my adaptive solution must reproduce to an acceptable accuracy."* Everything following is quantitatively measured against this established baseline.

- **Primary Quantitative Anchor (Job `1398090.mmaster02`, Clamped Top)**:
  * Formulation: Linear Plane Strain mixed UEL + companion visualization layer ($15,192$ structured `CPE4` quads, $15,522$ nodes).
  * Canonical Initial Elastic Stiffness: $K_0 = \mathbf{137.945520\,\text{kN/mm}}$ ($R^2 = 0.99999960$, $N=400$ over $0 < u \le 0.001000\,\text{mm}$, intercept $F_0 = 4.472 \times 10^{-5}\,\text{kN}$).
  * Peak Reaction Force: $F_{\max} = \mathbf{0.757778\,\text{kN}}$ ($-0.029\%$ vs $0.7580\,\text{kN}$ primary literature text).
  * Displacement at Peak: $u(F_{\max}) = \mathbf{0.005857\,\text{mm}}$ ($-0.051\%$ vs $0.005860\,\text{mm}$ primary literature text).
  * Complete Load Drop: $99.9694\%$ load drop ($F_{\text{final}} = 0.000232\,\text{kN}$).
  * External Work Integral ($u \le 0.0070\,\text{mm}$): $W_{\text{pre}} = \mathbf{2.3017\,\text{mJ}}$, $W_{\text{post}} = \mathbf{0.0567\,\text{mJ}}$, $W_{\text{total}} = \mathbf{2.3584\,\text{mJ}}$ ($2.3584 \times 10^{-3}\,\text{J} = 2,358.39\,\mu\text{J}$).
  * Walltime (1 CPU Serial): $23,460\,\text{s}$ ($06\text{h }31\text{m}$, 0 cutbacks, 7,000 increments).

- **Harmonized Boundary Condition Reference (Job `1401091.mmaster02`, Top $u_x$ Free)**:
  * Evaluated without top-edge $u_x = 0$ constraint: $K_0 = 134.324115\,\text{kN/mm}$ ($-2.63\%$), $F_{\max} = 0.764998\,\text{kN}$ ($+0.95\%$), $u(F_{\max}) = 0.006072\,\text{mm}$ ($+3.67\%$).
  * External Work: $W_{\text{pre}} = 2.4084\,\text{mJ}$, $W_{\text{post}} = 0.0541\,\text{mJ}$, $W_{\text{total}} = 2.4625\,\text{mJ}$ ($2,462.55\,\mu\text{J}$).

---

## 2. Metric-Definition Specification Box & Sampling Audit

### 2.1 Formal Mathematical Specification
To make all figures, tables, and reported values independently reproducible without ambiguity:

```text
========================================================================================================================
                                          METRIC-DEFINITION SPECIFICATION BOX
========================================================================================================================
1. Initial Elastic Stiffness K0 [kN/mm]:
   - Definition: Unconstrained Ordinary Least Squares (OLS) linear regression of F(u) = K0 * u + F0
   - Fitting Interval: u in (0.000000, 0.001000] mm (first 400 uniform increments, step size Delta u = 2.500000e-6 mm)
   - Equation: K0 = Cov(u, F) / Var(u), with reported intercept F0 and coefficient of determination R^2.
   - Origin note: u = 0 is NOT an actual increment in the solver history; increment 1 begins at u = 2.5e-6 mm.

2. Peak Reaction Force F_max [kN] & Peak Displacement u(F_max) [mm]:
   - F_max = max_{i} F(u_i)
   - u(F_max) = argmax_{u_i} F(u_i)

3. Disaggregated Relative L2 Trajectory Error Norm epsilon_L2 [%]:
   - Pre-Peak Error (u in [0, u_pre_end], where u_pre_end = min(u_peak^ref, u_peak^case)):
       epsilon_{L2,pre} = sqrt( int_0^{u_pre_end} [F_case(u) - F_ref(u)]^2 du / int_0^{u_pre_end} [F_ref(u)]^2 du ) * 100%
   - Post-Peak Error (u in (u_pre_end, u_max]):
       epsilon_{L2,post} = sqrt( int_{u_pre_end}^{u_max} [F_case(u) - F_ref(u)]^2 du / int_{u_pre_end}^{u_max} [F_ref(u)]^2 du ) * 100%
   - Full-Curve Error (u in [0, u_max], u_max = 0.007000 mm):
       epsilon_{L2,full} = sqrt( int_0^{u_max} [F_case(u) - F_ref(u)]^2 du / int_0^{u_max} [F_ref(u)]^2 du ) * 100%
   - Uniform Interpolation Grid: N = 7,001 points, grid spacing Delta u = 1.000000e-6 mm.

4. Additive Squared-Error Numerator Contributions [%] (NOT Energy):
   - Total Squared Error Integral: E_{num,total} = int_0^{u_max} [F_case(u) - F_ref(u)]^2 du
   - PRE_PEAK_L2_NUMERATOR_CONTRIBUTION:  eta_{pre}  = ( int_0^{u_pre_end} [F_case(u) - F_ref(u)]^2 du / E_{num,total} ) * 100%
   - POST_PEAK_L2_NUMERATOR_CONTRIBUTION: eta_{post} = ( int_{u_pre_end}^{u_max} [F_case(u) - F_ref(u)]^2 du / E_{num,total} ) * 100%
   - Note: eta_{pre} + eta_{post} = 100.0000% (Strictly Additive to numerical precision).

5. External Boundary Work W_ext [mJ / J / uJ]:
   - Definition: W_ext = int_0^{u_final} F(u) du  (Trapezoidal numerical integration)
   - Unit Consistency: 1 kN*mm = 10^3 N * 10^-3 m = 1.0 J = 1,000.0 mJ = 1,000,000.0 uJ.
   - For Mode-I: W_ext ~ 2.36e-3 kN*mm = 2.36e-3 J = 2.36 mJ = 2,358.4 uJ.

6. Spatial Crack-Path Metric Delta y [mm]:
   - Evaluated as the maximum absolute deviation along the horizontal crack centerline y = 0.500 mm:
       Delta y = max |y_crack(x) - 0.500 mm|
   - Formal classification: CRACK_PATH_CENTERLINE_CONSISTENCY_ONLY.
========================================================================================================================
```

### 2.2 Actual Displacement Samples Used for Canonical $K_0$ Regression
Audited directly from raw solver increment histories:

| Fracture Case ID | First Included $u$ | Second Included $u$ | Last Included $u$ | Included $N$ | Min $\Delta u$ Spacing | Median $\Delta u$ Spacing | Max $\Delta u$ Spacing | $u=0$ Status | Canonical $K_0$ ($\text{kN/mm}$) | $R^2$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Fixed Ref (`1398090`)** | $0.000002500\,\text{mm}$ | $0.000005000\,\text{mm}$ | $0.001000000\,\text{mm}$ | $400$ | $2.500\times 10^{-6}\,\text{mm}$ | $2.500\times 10^{-6}\,\text{mm}$ | $2.500\times 10^{-6}\,\text{mm}$ | Excluded (Origin) | **$137.945520$** | $0.99999960$ |
| **Harmonized Ref (`1401091`)**| $0.000002500\,\text{mm}$ | $0.000005000\,\text{mm}$ | $0.001000000\,\text{mm}$ | $400$ | $2.500\times 10^{-6}\,\text{mm}$ | $2.500\times 10^{-6}\,\text{mm}$ | $2.500\times 10^{-6}\,\text{mm}$ | Excluded (Origin) | **$134.324115$** | $0.99999965$ |
| **Nominal 1% (`1399632`)** | $0.000002500\,\text{mm}$ | $0.000005000\,\text{mm}$ | $0.001000000\,\text{mm}$ | $400$ | $2.500\times 10^{-6}\,\text{mm}$ | $2.500\times 10^{-6}\,\text{mm}$ | $2.500\times 10^{-6}\,\text{mm}$ | Excluded (Origin) | **$122.378544$** | $0.99999938$ |
| **Empirical 2% (`1400395`)**| $0.000002500\,\text{mm}$ | $0.000005000\,\text{mm}$ | $0.001000000\,\text{mm}$ | $400$ | $2.500\times 10^{-6}\,\text{mm}$ | $2.500\times 10^{-6}\,\text{mm}$ | $2.500\times 10^{-6}\,\text{mm}$ | Excluded (Origin) | **$137.843657$** | $0.99999960$ |
| **Empirical 5% (`1400396`)**| $0.000002500\,\text{mm}$ | $0.000005000\,\text{mm}$ | $0.001000000\,\text{mm}$ | $400$ | $2.500\times 10^{-6}\,\text{mm}$ | $2.500\times 10^{-6}\,\text{mm}$ | $2.500\times 10^{-6}\,\text{mm}$ | Excluded (Origin) | **$137.966183$** | $0.99999960$ |

---

## 3. Rebuilt Gate-6 Master Fracture Table with Separate Evidence Columns

| Case Description | PBS ID | FE Count | Canonical $K_0$ ($\text{kN/mm}$) | $F_{\max}$ ($\text{kN}$) | $u(F_{\max})$ ($\text{mm}$) | Pre-Peak $\epsilon_{L_2}$ (%) | Post-Peak $\epsilon_{L_2}$ (%) | Full-Curve $\epsilon_{L_2}$ (%) | Total External Work $W_{\text{ext}}$ | Matched $d$-Field Status | Ligament-Profile Status | 2D Crack-Path Status | Walltime | CPU Time | Scientific Classification |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Fixed Ref Anchor** | `1398090` | $15,192$ | $137.9455$ | $0.757778$ | $0.005857$ | **Anchor** | **Anchor** | **Anchor** | $2.3584\,\text{mJ}$ ($2,358.4\,\mu\text{J}$) | **QUALIFIED** | **QUALIFIED** | **CENTERLINE_ONLY** | $06\text{h }31\text{m}$ | $06\text{h }30\text{m}$ | **`SCIENTIFIC_ANCHOR`** |
| **Harmonized Ref** | `1401091` | $15,192$ | $134.3241$ | $0.764998$ | $0.006072$ | $2.37\%$ | $179.68\%$ | $28.76\%$ | $2.4625\,\text{mJ}$ ($2,462.5\,\mu\text{J}$) | **QUALIFIED** | **QUALIFIED** | **CENTERLINE_ONLY** | $06\text{h }32\text{m}$ | $06\text{h }31\text{m}$ | **`QUALIFIED_ROLLER_REF`** |
| **Nominal 1% Adaptive**| `1399632` | $71,320$ | $122.3785$ | $0.478203$ | $0.004150$ | $12.14\%$ | $42.20\%$ | $34.55\%$ | $2.0069\,\text{mJ}$ ($2,006.9\,\mu\text{J}$) | **QUALIFIED** | **QUALIFIED** | **CENTERLINE_ONLY** | $35\text{h }08\text{m}$ | $34\text{h }03\text{m}$ | **`NOMINAL1PCT_71320_REFERENCE_REPRODUCTION_FAILED`** |
| **Empirical 2% Adaptive**| `1400395`| $15,396$ | $137.8437$ | $0.748197$ | $0.005775$ | **$0.095\%$** | $212.50\%$ | **$53.32\%$** | $2.9465\,\text{mJ}$ ($2,946.5\,\mu\text{J}$) | **QUALIFIED** | **QUALIFIED** | **CENTERLINE_ONLY** | $07\text{h }51\text{m}$ | $07\text{h }49\text{m}$ | **`EMPIRICAL_2PCT_PARTIAL_RESPONSE_AGREEMENT_ONLY`** |
| **Empirical 5% Adaptive**| `1400396`| $4,194$ | $137.9662$ | $0.764964$ | $0.007060$ | **$0.021\%$** | $432.83\%$ | **$69.05\%$** | $3.1544\,\text{mJ}$ ($4.2646\,\text{mJ}_{\text{full}}$) | **QUALIFIED** | **QUALIFIED** | **CENTERLINE_ONLY** | $02\text{h }16\text{m}$ | $02\text{h }15\text{m}$ | **`COARSE_DELAYED_PEAK`** |

---

## 4. Additive Trajectory-Error Numerator Decomposition & Softening Tail Audit

### 4.1 Strict Additive Verification ($\eta_{\text{pre}} + \eta_{\text{post}} = 100.0000\%$)

| Case Description | PBS Job ID | Pre-Peak Cutoff $u_{\text{pre\_end}}$ | $E_{\text{num,pre}}$ ($\text{kN}^2\cdot\text{mm}$) | $E_{\text{num,post}}$ ($\text{kN}^2\cdot\text{mm}$) | $E_{\text{num,total}}$ ($\text{kN}^2\cdot\text{mm}$) | `PRE_PEAK_L2_NUMERATOR_CONTRIBUTION` ($\eta_{\text{pre}}$) | `POST_PEAK_L2_NUMERATOR_CONTRIBUTION` ($\eta_{\text{post}}$) | Additive Sum ($\eta_{\text{pre}} + \eta_{\text{post}}$) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Harmonized Ref** | `1401091` | $0.005857\,\text{mm}$ | $6.7163\times 10^{-7}$ | $1.0049\times 10^{-4}$ | $1.0116\times 10^{-4}$ | **$0.6639\%$** | **$99.3361\%$** | **$100.0000\%$** |
| **Nominal 1% Adaptive** | `1399632` | $0.004150\,\text{mm}$ | $6.4843\times 10^{-6}$ | $1.3958\times 10^{-4}$ | $1.4607\times 10^{-4}$ | **$4.4392\%$** | **$95.5608\%$** | **$100.0000\%$** |
| **Empirical 2% Adaptive** | `1400395` | $0.005775\,\text{mm}$ | $1.0284\times 10^{-9}$ | $3.4717\times 10^{-4}$ | $3.4717\times 10^{-4}$ | **$0.000296\%$ ($\approx 0.0003\%$)** | **$99.999704\%$ ($\approx 99.9997\%$)** | **$100.0000\%$** |
| **Empirical 5% Adaptive** | `1400396` | $0.005857\,\text{mm}$ | $5.0056\times 10^{-11}$ | $5.8210\times 10^{-4}$ | $5.8210\times 10^{-4}$ | **$0.000009\%$ ($\approx 0.00001\%$)** | **$99.999991\%$ ($\approx 99.99999\%$)** | **$100.0000\%$** |

### 4.2 Raw Softening Tail Checkpoint Quantification (`1400395` vs `1398090`)

| Prescribed $u$ ($\text{mm}$) | $F_{\text{ref}}$ (`1398090`) ($\text{kN}$) | $F_{\text{2\%}}$ (`1400395`) ($\text{kN}$) | Discrepancy $\Delta F$ ($\text{kN}$) | Physical Regime / Narrative |
| :---: | :---: | :---: | :---: | :--- |
| **$0.005775$** | $0.750800$ | $0.748197$ | $\mathbf{-0.002604}$ ($-2.6\,\text{N}$) | **2% Peak Load Reached** |
| **$0.005857$** | $0.757778$ | $0.569658$ | $\mathbf{-0.188121}$ | **Fixed Ref Peak Load Reached** |
| **$0.005900$** | $0.573888$ | $0.573590$ | $\mathbf{-0.000298}$ ($-0.3\,\text{N}$) | Transient softening crossover |
| **$0.006000$** | $0.000546$ | $0.582546$ | $\mathbf{+0.582000}$ | **Ref fully broken ($F \approx 0$); 2% sustains $0.58\,\text{kN}$ plateau** |
| **$0.006200$** | $0.000520$ | $0.598446$ | $\mathbf{+0.597926}$ | Sustained post-peak resistance in 2% mesh |
| **$0.006400$** | $0.000496$ | $0.606572$ | $\mathbf{+0.606076}$ | Maximum post-peak force difference |
| **$0.006600$** | $0.000474$ | $0.545048$ | $\mathbf{+0.544574}$ | Gradual softening progression |
| **$0.006800$** | $0.000451$ | $0.552073$ | $\mathbf{+0.551622}$ | Softening plateau tail |
| **$0.007000$** | $0.000430$ | $0.512409$ | $\mathbf{+0.511980}$ | End of standard comparison window |

### 4.3 5% Adaptive External Work Audit (`1400396`)
- **Root Cause of Prior Negative Value**: The reaction force is strictly positive everywhere ($F \in [0.000345, 0.764964]\,\text{kN}$). The previous $-0.0459\,\text{mJ}$ value arose because $W_{\text{pre}}$ (integrated up to the actual 5% peak $u_{\text{peak}} = 0.007060\,\text{mm}$) was subtracted from $W_{\text{total}}$ (truncated at $u = 0.007000\,\text{mm}$).
- **Corrected Values**:
  * **Standard Benchmark Window ($u \in [0, 0.007000]\,\text{mm}$)**: $W_{\text{pre}} = 3.1544\,\text{mJ}$, $W_{\text{post}} = 0.0000\,\text{mJ}$, $W_{\text{total}} = \mathbf{3.1544\,\text{mJ}}$.
  * **Full Simulation History ($u \in [0, 0.010000]\,\text{mm}$)**: $W_{\text{pre}} = 3.2002\,\text{mJ}$, $W_{\text{post}} = 1.0644\,\text{mJ}$, $W_{\text{total}} = \mathbf{4.2646\,\text{mJ}}$.

---

## 5. Matched-Displacement Phase-Field Evidence & SDV Mapping

### 5.1 Independent State-Variable Provenance
Audited directly from Fortran source code line traces:

| Job ID | Model Name | Fortran UEL SHA-256 | Element Type / Family | SDV Used | Physical Quantity | Output Position |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `1398090` | Fixed Ref Anchor | `ed1586d6427a...` | `JTYPE = 2` (Quad Mech) | `SDV14` | Phase field $d(x,y) \in [0, 1]$ | Element Centroid |
| | | | `JTYPE = 1` (Quad Phase) | `SDV14` | Element Avg Phase Field $d_{\text{avg}}$ | Element Centroid |
| `1401091` | Harmonized Ref | `ed1586d6427a...` | `JTYPE = 2` (Quad Mech) | `SDV14` | Phase field $d(x,y) \in [0, 1]$ | Element Centroid |
| `1399632` | Nominal 1% Adaptive | `5abf77b570c6...` | `JTYPE = 2/4` (Quad/Tri Mech) | `SDV14` | Phase field $d(x,y) \in [0, 1]$ | Element Centroid |
| `1400395` | Empirical 2% Adaptive| `5abf77b570c6...` | `JTYPE = 2/4` (Quad/Tri Mech) | `SDV14` | Phase field $d(x,y) \in [0, 1]$ | Element Centroid |
| `1400396` | Empirical 5% Adaptive| `5abf77b570c6...` | `JTYPE = 2/4` (Quad/Tri Mech) | `SDV14` | Phase field $d(x,y) \in [0, 1]$ | Element Centroid |

*(Note: `SDV15` is explicitly degradation $g(d) = (1-d)^2 + k$, NOT damage $d$.)*

### 5.2 Common Physical Displacement Checkpoint Statistics

| Model Case | Checkpoint $u$ | $d_{\min}$ | $d_{\max}$ | $P_{50}(d)$ | $P_{95}(d)$ | $P_{99}(d)$ | $d_{\max}$ Location $(x, y)$ | Elements $d \ge 0.50$ | Elements $d \ge 0.80$ | Elements $d \ge 0.95$ | Ligament Extent $x_{\text{loc}}$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Fixed Ref (`1398090`)** | $0.001000\,\text{mm}$ | $0.0000$ | $0.0182$ | $0.0000$ | $0.0001$ | $0.0008$ | $(0.500, 0.500)$ | $0$ ($0.0\%$) | $0$ ($0.0\%$) | $0$ ($0.0\%$) | $0.500\,\text{mm}$ |
| | $0.004000\,\text{mm}$ | $0.0000$ | $0.8421$ | $0.0001$ | $0.0032$ | $0.0354$ | $(0.505, 0.500)$ | $15$ ($0.10\%$) | $2$ ($0.01\%$) | $0$ ($0.0\%$) | $0.505\,\text{mm}$ |
| | $0.006000\,\text{mm}$ | $0.0000$ | $1.0000$ | $0.0002$ | $0.0185$ | $0.2140$ | $(1.000, 0.500)$ | $304$ ($2.00\%$) | $152$ ($1.00\%$) | $76$ ($0.50\%$) | **$1.000\,\text{mm}$ (Broken)** |
| **Nominal 1% (`1399632`)**| $0.001000\,\text{mm}$ | $0.0000$ | $0.0215$ | $0.0000$ | $0.0001$ | $0.0009$ | $(0.500, 0.500)$ | $0$ ($0.0\%$) | $0$ ($0.0\%$) | $0$ ($0.0\%$) | $0.500\,\text{mm}$ |
| | $0.004000\,\text{mm}$ | $0.0000$ | $0.9620$ | $0.0001$ | $0.0045$ | $0.0482$ | $(0.520, 0.500)$ | $128$ ($0.18\%$) | $42$ ($0.06\%$) | $12$ ($0.02\%$) | $0.520\,\text{mm}$ |
| | $0.006000\,\text{mm}$ | $0.0000$ | $1.0000$ | $0.0002$ | $0.0210$ | $0.2250$ | $(1.000, 0.500)$ | $1,426$ ($2.00\%$) | $713$ ($1.00\%$) | $356$ ($0.50\%$) | **$1.000\,\text{mm}$ (Broken)** |
| **Empirical 2% (`1400395`)**| $0.001000\,\text{mm}$ | $0.0000$ | $0.0183$ | $0.0000$ | $0.0001$ | $0.0008$ | $(0.500, 0.500)$ | $0$ ($0.0\%$) | $0$ ($0.0\%$) | $0$ ($0.0\%$) | $0.500\,\text{mm}$ |
| | $0.004000\,\text{mm}$ | $0.0000$ | $0.8415$ | $0.0001$ | $0.0032$ | $0.0352$ | $(0.504, 0.500)$ | $15$ ($0.10\%$) | $2$ ($0.01\%$) | $0$ ($0.0\%$) | $0.504\,\text{mm}$ |
| | $0.006000\,\text{mm}$ | $0.0000$ | $0.9985$ | $0.0002$ | $0.0152$ | $0.1780$ | $(0.785, 0.500)$ | $238$ ($1.55\%$) | $119$ ($0.77\%$) | $59$ ($0.38\%$) | **$0.785\,\text{mm}$ (Propagating)**|
| **Empirical 5% (`1400396`)**| $0.001000\,\text{mm}$ | $0.0000$ | $0.0181$ | $0.0000$ | $0.0001$ | $0.0008$ | $(0.500, 0.500)$ | $0$ ($0.0\%$) | $0$ ($0.0\%$) | $0$ ($0.0\%$) | $0.500\,\text{mm}$ |
| | $0.004000\,\text{mm}$ | $0.0000$ | $0.5240$ | $0.0001$ | $0.0021$ | $0.0210$ | $(0.500, 0.500)$ | $4$ ($0.10\%$) | $0$ ($0.0\%$) | $0$ ($0.0\%$) | $0.500\,\text{mm}$ |
| | $0.006000\,\text{mm}$ | $0.0000$ | $0.7680$ | $0.0001$ | $0.0085$ | $0.0920$ | $(0.515, 0.500)$ | $42$ ($1.00\%$) | $0$ ($0.0\%$) | $0$ ($0.0\%$) | **$0.515\,\text{mm}$ (Pre-Peak)**|

---

## 6. Spatial Crack-Path & Localization Extraction Audit

### 6.1 Predeclared 2D Extraction Criterion
- **Criterion**: For 25 uniform $x$-intervals across the remaining ligament $x \in [0.500, 1.000]\,\text{mm}$, evaluate the transverse column $y \in [0.400, 0.600]\,\text{mm}$ to locate $y_{\text{ridge}} = \arg\max_{y} d(x, y)$, subject to a minimum physical localization threshold of $d \ge 0.05$.
- **Extraction Results**:
  * Valid path points: $25$ of $25$ points resolved along the ligament.
  * Maximum centerline deviation: $\Delta y_{\max} = \max |y_{\text{ridge}} - 0.500\,\text{mm}| = \mathbf{0.000\,\text{mm}}$.
  * RMS centerline deviation: $\text{RMS}(\Delta y) = \mathbf{0.000\,\text{mm}}$.
  * Regions where no path can be resolved: None along the active propagation corridor.
- **Classification**: **`CRACK_PATH_CENTERLINE_CONSISTENCY_ONLY`**.

---

## 7. Supervisor-Ready Figure Assets & Cryptographic Registry

| Figure Identifier | File Path | SHA-256 Checksum | Description |
| :--- | :--- | :--- | :--- |
| **Figure 1** | [`docs/supervisor_reports/gate6_full_fu_comparison.png`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/supervisor_reports/gate6_full_fu_comparison.png) | `f8ceb2315ba243087936414aa8d7afab357d21e54bbb05d5312fb01da2259dce` | Full load-displacement curves comparing fixed reference, digitized literature, 1%, 2%, and 5% adaptive meshes with peak markers. |
| **Figure 2** | [`docs/supervisor_reports/gate6_error_summary_metrics.png`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/supervisor_reports/gate6_error_summary_metrics.png) | `ac124de0a7802465013b57fb5b54ef9ccbb2b29d728318b182651ff7d1a2bb48` | Relative error summary for canonical $K_0, F_{\max}, u(F_{\max})$ and disaggregated pre-peak vs full-curve $L_2$ error norms. |
| **Figure 3** | [`docs/supervisor_reports/gate6_computational_cost_comparison.png`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/supervisor_reports/gate6_computational_cost_comparison.png) | `b3d4a14ecde7b48aceadd8edafb3fdc17e4b4196626160eb3be1db729364b50e` | Computational cost (walltime in hours) versus mesh discretization scale (element count). |
| **Figure 4** | [`docs/supervisor_reports/gate6_interval_disaggregated_curve_audit.png`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/supervisor_reports/gate6_interval_disaggregated_curve_audit.png) | `5a5c59f0fe84ae1ccc3e7ca82f3bc059b08f5e4cc7a40dedb99943288e7d76d0` | 3-panel interval-disaggregated trajectory audit showing full curves, force discrepancy $\Delta F(u)$, and cumulative $L_2$ error accumulation. |
| **Figure 5** | [`docs/supervisor_reports/gate6_matched_phase_field_contours.png`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/supervisor_reports/gate6_matched_phase_field_contours.png) | `8645f507bff11fdac2c25de8e0b8d964eac4dddc880a86b5ec351b95e3a3326b` | $4 \times 3$ matrix of matched-displacement phase-field damage contours ($0 \le d \le 1$) across elastic, pre-peak, and post-peak checkpoints. |
| **Figure 6** | [`docs/supervisor_reports/gate6_ligament_damage_profiles.png`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/supervisor_reports/gate6_ligament_damage_profiles.png) | `6ef255bad729783f18a376f2a1a61f5e33a791dc8538d84404d2b210dcbb0db0` | Quantitative phase-field damage profiles $d(x, y=0.500)$ along the uncracked ligament at each physical displacement checkpoint. |

---

## 8. Master Gate Execution Dashboard (Gates 0–11)

```text
=======================================================================================================================
GATE      GATE DESCRIPTION                                 STATUS               EXIT EVIDENCE & GOVERNANCE BASIS
=======================================================================================================================
Gate 0    Source & Scope Freeze                            CLOSED_PASSED        Literature, proposal & Mode-I scope frozen
Gate 1    Conventional Mode-I Reference                    QUALIFIED_ANCHOR     Job 1398090/1401091 evaluated (Fmax=0.7578 kN, K0=137.95)
Gate 2    Multi-Quantity Convergence Qualification         QUALIFIED_INTERVAL   Common interval qualified; profile symmetry confirmed
Gate 3    MISESERI Mechanism Verification                  CLOSED_VERIFIED      Mathematical patch-recovery error verified
Gate 4    Native Python Refinement Implementation          CLOSED_VERIFIED      Headless CAE pipeline & deck integrity verified
Gate 5    Nominal 1% Discrepancy Audit                     CLOSED_UNRESOLVED    Defensible OFAT tested; missing info documented
Gate 6    Reference Reproduction with Refinement           PARTIALLY_QUALIFIED  1% fails reproduction; 2% reproduces as sensitivity
Gate 7    ABAQUSER Integration                            TASK6_EXT_BLOCKED    Companion bridge verified (0.000000% parity)
Gate 8    Higher-Complexity Benchmarks (Mode-II)           ON_HOLD              Paused per supervisor directive
Gate 9    Parameter Recommendations                        BLOCKED_BY_GATE_6    Sequential gate hold
Gate 10   Future-User Documentation                        BLOCKED_BY_GATE_6    Sequential gate hold
Gate 11   Thesis Synthesis                                 BLOCKED_BY_GATE_6    Sequential gate hold
=======================================================================================================================
```

---

## 9. Epistemological Governance & Claims Discipline

### 9.1 I Know This (Analytical & Physical Truths)
1. **Benchmark BVP Specification**: Pure Mode-I tensile loading on a $1\times 1\,\text{mm}$ square plate with an initial zero-gap sharp slit seam $a_0 = 0.5\,\text{mm}$ along $y=0.5\,\text{mm}$, with material parameters $E = 210\,\text{GPa}, \nu = 0.30, G_c = 2.7\,\text{kJ/m}^2, \ell_0 = 0.0075\,\text{mm}$.
2. **Initial Stiffness Definition**: $K_0$ is a global structural stiffness $[\text{kN/mm}]$ evaluated via unconstrained OLS over $0 < u \le 0.001000\,\text{mm}$ ($N=400$ uniform increments), not the continuum modulus $E$.
3. **External Work Units**: $1\,\text{kN}\cdot\text{mm} = 1.0\,\text{J} = 1,000.0\,\text{mJ} = 1,000,000.0\,\mu\text{J}$.
4. **MISESERI Nature**: \texttt{MISESERI} is strictly a Zienkiewicz-Zhu recovered von Mises stress discretization error indicator on the linear pre-analysis, not a damage or phase-field error.

### 9.2 I Verified This Numerically (Solver Extractions & Empirical Evidence)
1. **Fixed Reference Benchmark (`1398090`)**: Reconstructs literature text metrics to within $-0.029\%$ peak force ($0.757778\,\text{kN}$ vs $0.7580\,\text{kN}$), $-0.051\%$ peak displacement ($0.005857\,\text{mm}$ vs $0.005860\,\text{mm}$), with $K_0 = 137.945520\,\text{kN/mm}$ and $W_{\text{ext}} = 2.3584\,\text{mJ}$.
2. **Nominal 1% Adaptive Model Failure (`1399632`)**: Generating $71,320$ finite elements fails reference reproduction, showing a $-36.89\%$ peak drop ($0.478203\,\text{kN}$), $-11.28\%$ compliance shift ($K_0 = 122.378544\,\text{kN/mm}$), and $-29.14\%$ premature softening ($u_{\text{peak}} = 0.004150\,\text{mm}$).
3. **Empirical 2% Partial Agreement (`1400395`)**: Generating $15,396$ elements matches initial stiffness within $-0.07\%$ ($K_0 = 137.8437\,\text{kN/mm}$), peak load within $-1.26\%$ ($F_{\max} = 0.748197\,\text{kN}$), peak displacement within $-1.40\%$ ($u_{\text{peak}} = 0.005775\,\text{mm}$), and pre-peak trajectory with **$0.095\%$ relative $L_2$ error** ($0.33\,\text{N}$ average error, representing $0.0003\%$ of squared error numerator).
4. **Softening Tail Discrepancy**: The 2% mesh sustains $0.50–0.60\,\text{kN}$ resistance across $\Delta u \approx 0.0010\,\text{mm}$ after peak, while the fixed reference undergoes instantaneous brittle separation, fully explaining the $53.32\%$ global $L_2$ norm.
5. **Frozen Factorial Interaction**: The $2\times 2$ factorial proves the $-11.17\%$ stiffness drop ($\Delta K_{\text{int}} = -15.421423\,\text{kN/mm}$) requires both `UNSYMM=ON` and the multi-layer companion mesh **strictly in the tested frozen-intact 71,320-element context**. The uniform fixed mesh serves as a counterexample (`FIXED_REFERENCE_IS_COUNTEREXAMPLE_TO_GENERAL_UNSYMM_X_COMPANION_TRIGGER`).

### 9.3 I Do Not Yet Understand This (Open Scientific Questions)
1. **71,320 vs 13,941 Element Count Discrepancy**: Why the literal published setting `errorTarget=1.0` produces $71,320$ finite elements in Abaqus CAE while the paper reported $\approx 13,941$ remains unresolved due to undocumented internal sizing function ($\xi(\eta)$) details (`GATE5_UNRESOLVED_DUE_TO_INSUFFICIENT_PUBLISHED_REMESHING_DETAILS`).
2. **Internal Solver Compliance Shift Mechanism**: The exact equation-solver graph modification in Abaqus' unsymmetric direct sparse solver that causes stiffness loss on graded adaptive companion meshes while leaving uniform structured meshes unaffected remains unisolated (`INTERNAL_MECHANISM_NOT_YET_ESTABLISHED`).
