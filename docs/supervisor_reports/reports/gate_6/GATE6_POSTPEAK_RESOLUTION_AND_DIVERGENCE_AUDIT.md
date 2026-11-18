# Gate-6 Priority-A Post-Peak Mesh Resolution, Damage Evolution, and Force Divergence Audit

## Executive Summary & Epistemic Classification

* **Investigated Phenomenon:** Post-peak softening response divergence and solver arrest in the nominal 1% 71,320-element adaptive fracture model (`PK_MODE1_PROPOSED_PFM_PHYS_1PCT_71320.inp`).
* **Analyzed Datasets:** Completed/frozen Job `1404933` (strict mechanical twin, Exit 0), Job `1404454` (production solve), Job `1398090` (fixed-mesh reference baseline), and exact finite element mesh connectivity.
* **Verified Classification:** **`SPATIAL_ASSOCIATION_SUPPORTED_NOT_CAUSAL`**
  - *Spatial Association:* The onset of post-peak force divergence ($u \ge 0.006000\,\text{mm}$) and subsequent crack front arrest ($x \approx 0.81\,\text{mm}$) coincide precisely with the crack leaving the refined notch-tip corridor ($h \approx 1.76\,\mu\text{m}$, $h/\ell_0 \approx 0.235$) and entering the coarse downstream ligament ($h = 4.0 - 5.9\,\mu\text{m}$, $h/\ell_0 = 0.535 - 0.785$).
  - *Non-Causal Boundary:* A spatial correlation on a single realization does not demonstrate causality without a controlled multi-step experiment. Therefore, downstream refinement is not claimed as a proven physical/numerical cause.
  - *Solver Job Action:* Zero new solver jobs submitted. Gate 6 remains `CORRECTED_HIGH_BRANCH_ADAPTIVE_REPRODUCTION_PARTIALLY_QUALIFIED`.

---

## 1. Matched Displacement Checkpoint Comparison

Comparison between Strict Diagnostic Twin `1404933` (71,320 elements) and Fixed Reference Baseline `1398090` (15,192 elements):

| Target $u$ [mm] | Twin `1404933` $u$ [mm] | Twin `1404933` $F$ [kN] | Ref `1398090` $u$ [mm] | Ref `1398090` $F$ [kN] | $\Delta F$ [N] | $\Delta F$ [%] | Damage $d_{\max}$ | Crack Front ($d \ge 0.90$) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **$0.005000$** | $0.005000$ | $0.661366$ | $0.005000$ | $0.662052$ | **$-0.69\,\text{N}$** | $-0.10\%$ | $0.3124$ | Not formed ($d < 0.90$) |
| **$0.005500$** | $0.005500$ | $0.719700$ | $0.005500$ | $0.720657$ | **$-0.96\,\text{N}$** | $-0.13\%$ | $0.4390$ | Not formed ($d < 0.90$) |
| **$0.005750$** | $0.005750$ | $0.745325$ | $0.005750$ | $0.748219$ | **$-2.89\,\text{N}$** | $-0.39\%$ | $0.6201$ | Not formed ($d < 0.90$) |
| **$0.006000$** | $0.006000$ | $0.351167$ | $0.006000$ | $0.000546$ | **$+350.62\,\text{N}$**| $+64,173\%$ | $1.0022$ | $x = 0.7955\,\text{mm}$ |
| **$0.006200$** | $0.006200$ | $0.335775$ | $0.006200$ | $0.000520$ | **$+335.25\,\text{N}$**| $+64,418\%$ | $1.0024$ | $x = 0.8109\,\text{mm}$ |

> [!NOTE]
> **Fixed-Reference Spatial Field Limitation:** Matched spatial phase-field distributions ($d(x,y)$) for the fixed reference Job `1398090` are not present in the archived ODB extraction datasets; only global reaction force and displacement history are directly available.

---

## 2. Ligament Mesh Discretization Profile

Detailed element resolution across the ligament corridor ($|y - 0.50| \le 0.015\,\text{mm}, x \ge 0.50\,\text{mm}$, total $1,638$ elements, length scale $\ell_0 = 7.5\,\mu\text{m}$, $2\ell_0 = 15.0\,\mu\text{m}$):

| Spatial Bin [mm] | Total Elements | CPE4 | CPE3 | Mean $h$ [$\mu\text{m}$] | Min–Max $h$ [$\mu\text{m}$] | Mean $h/\ell_0$ | Elements across $2\ell_0$ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **$[0.50, 0.55)$** | $473$ | $460$ | $13$ | **$1.76$** | $0.91 - 2.61$ | **$0.235$** | **$8.5$** |
| **$[0.55, 0.60)$** | $445$ | $433$ | $12$ | **$1.82$** | $0.89 - 2.68$ | **$0.242$** | **$8.3$** |
| **$[0.60, 0.70)$** | $326$ | $319$ | $7$ | **$2.97$** | $1.08 - 5.08$ | **$0.396$** | **$5.0$** |
| **$[0.70, 0.80)$** | $185$ | $182$ | $3$ | **$4.01$** | $1.89 - 5.30$ | **$0.535$** | **$3.7$** |
| **$[0.80, 0.90)$** | $85$ | $84$ | $1$ | **$5.89$** | $2.32 - 8.43$ | **$0.785$** | **$2.5$** |
| **$[0.90, 0.96)$** | $62$ | $58$ | $4$ | **$5.15$** | $3.11 - 6.17$ | **$0.687$** | **$2.9$** |
| **$[0.96, 1.00)$** | $29$ | $29$ | $0$ | **$6.29$** | $5.41 - 7.47$ | **$0.838$** | **$2.4$** |

### Local Resolution at Job 1404454 Failure Region
* **Failure Node 61805:** Coordinates $(x = 0.940192\,\text{mm}, y = 0.509091\,\text{mm})$.
* **Local Discretization ($N=38$ elements within $20\,\mu\text{m}$):**
  - Mean $h = 5.15\,\mu\text{m}$ ($h/\ell_0 = 0.687$).
  - Elements spanning $2\ell_0 = 15\,\mu\text{m}$: **$2.9$ elements** (coarse, below the $h \le \ell_0/2$ recommendation).

---

## 3. Transverse Localization Width Evolution ($x = 0.55\,\text{mm}$)

* **Explicit Metric 1 (Full Width at Half Maximum - FWHM):** Distance between transverse locations where $d(y) = d_{\max}(x=0.55)/2$.
* **Explicit Metric 2 (Integral Width):** $w_{\text{int}} = \frac{1}{d_{\max}} \int d(y)\,dy$.

| Checkpoint $u$ [mm] | Peak $d(x=0.55)$ | Peak Location $y$ [mm] | FWHM [$\mu\text{m}$] | Integral Width $w_{\text{int}}$ [$\mu\text{m}$] | Local Elements across FWHM |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **$0.005000$** | $0.0415$ | $0.532841$ | N/A (unbounded) | $90.31$ | N/A (diffuse elastic) |
| **$0.005500$** | $0.0520$ | $0.532841$ | N/A (unbounded) | $90.97$ | N/A (diffuse elastic) |
| **$0.005750$** | $0.0603$ | $0.513880$ | N/A (unbounded) | $91.26$ | N/A (diffuse elastic) |
| **$0.006000$** | $0.9735$ | $0.496128$ | **$24.94$** | **$32.77$** | **$13.7$ elements** |
| **$0.006200$** | $0.9735$ | $0.496128$ | **$24.94$** | **$32.77$** | **$13.7$ elements** |

---

## 4. Synthesis of Findings & Scientific Governance

1. **Pre-Peak Verification:** Pre-peak behavior ($u \le 0.00575\,\text{mm}$) is thoroughly verified and qualified ($|\Delta F| \le 2.89\,\text{N}$, $\Delta K_0 = -0.09\%$).
2. **Post-Peak Spatial Association:** Force divergence occurs precisely as the crack front moves from $[0.50, 0.60)\,\text{mm}$ ($h \approx 1.8\,\mu\text{m}$, $8.5$ el/$2\ell_0$) into $[0.70, 0.90)\,\text{mm}$ ($h \approx 4.0 - 5.9\,\mu\text{m}$, $2.5 - 3.7$ el/$2\ell_0$).
3. **Epistemic Discipline:** Without a controlled multi-step experiment, causality cannot be claimed. Status remains **`SPATIAL_ASSOCIATION_SUPPORTED_NOT_CAUSAL`**.
