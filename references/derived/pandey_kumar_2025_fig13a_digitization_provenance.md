# Digitization & Provenance Record: Pandey & Kumar (2025) Section 4.2 (Mode-II)

**Benchmark Reference:** Pandey & Kumar (2025), *Computer Modeling in Engineering & Sciences*, 144(3), pp. 3270–3272, Section 4.2.  
**DOI:** [10.32604/cmes.2025.067858](https://doi.org/10.32604/cmes.2025.067858)  
**Primary Figures Audited:**
- Figure 6(b): Error indicator (MISESERI) plot for Mode-II loading (p. 3266)
- Figure 12(a,b): Discretized specimen and phase-field contours for Standard ($37{,}155$ FEs) and Proposed Adaptive ($19{,}963$ FEs) implementations at $l_0 = 0.015\,\text{mm}$ (p. 3271)
- Figure 13(a): Load-displacement ($F_x - u_x$) response for single edge crack under Mode-II loading (p. 3272)
- Figure 13(b): Computational time and element count comparison (p. 3272)

---

## 1. Primary Physical & Geometric Benchmark Parameters

| Parameter | Symbol | Paper Value | Unit | Status |
| :--- | :---: | :---: | :---: | :---: |
| Domain Dimensions | $\Omega$ | $1.0 \times 1.0$ | $\text{mm}$ | `PAPER_VERIFIED` |
| Initial Edge Slit / Notch | $a_0$ | $0.5$ (along $y=0.5\,\text{mm}$) | $\text{mm}$ | `PAPER_VERIFIED` |
| Young's Modulus | $E$ | $210$ | $\text{GPa}$ | `PAPER_VERIFIED` |
| Poisson's Ratio | $\nu$ | $0.3$ | — | `PAPER_VERIFIED` |
| Critical Energy Release Rate | $G_c$ | $2.7 \times 10^{-3}$ | $\text{kN/mm}$ ($2.7\,\text{N/mm}$) | `PAPER_VERIFIED` |
| Phase-Field Length Scale | $l_0$ | $0.015$ | $\text{mm}$ ($15.0\,\mu\text{m}$) | `PAPER_VERIFIED` |
| Boundary Conditions | Bottom: $u_x=u_y=0$, Top: $u_x$ applied, $u_y=0$ | Fixed bottom, Constrained top shear | — | `PAPER_VERIFIED` |
| Strain Energy Split | Miehe Anisotropic Split | Spectral decomposition | — | `PAPER_VERIFIED` |
| Literature Remeshing Rule `errorTarget` | `errorTarget` | **Unpublished / Not stated** | — | `SUPERVISOR_ACCEPTED_REPRODUCTION_LIMITATION` |
| Literature Coarse Mesh | Job-1 | $2{,}960$ FEs ($3{,}037$ nodes) | — | `PAPER_VERIFIED` |
| Literature Adaptive Mesh | Proposed PFM (Job-2) | $19{,}963$ FEs | — | `PAPER_VERIFIED` |
| Project Remeshing Selection | `ET_2PCT` | $22{,}530$ FEs | — | `PROJECT_REPRESENTATIVE_MESH` ($+12.86\%$) |

---

## 2. Authoritative High-Resolution Redigitization of Figure 13(a)

High-resolution (600 DPI) rendering of Page 3272 from the primary publisher PDF (`Literature review/TSP_CMES_67858.pdf`).

### Calibration Coordinates & Scaling
- **Horizontal Axis ($u_x$):** Span $u \in [0.000, 0.016]\,\text{mm}$ ($[0, 16.0]\,\mu\text{m}$). Pixel coordinate range $X \in [574, 1758]$ px ($\Delta X = 1184\text{ px} \implies 74.0\text{ px}/\mu\text{m}$, $\Delta u = 0.01351\,\mu\text{m}/\text{px}$).
- **Vertical Axis ($F_x$):** Span $F \in [0.00, 0.40]\,\text{kN}$ ($[0, 400.0]\,\text{N}$). Pixel coordinate range $Y \in [1040, 36]$ px ($\Delta Y = 1004\text{ px} \implies 2.510\text{ px}/\text{N}$, $\Delta F = 0.3984\,\text{N}/\text{px}$).
- **Legend Exclusion:** Inset box filter applied at $X \in [574, 1060]$, $Y \le 270$.

### Extracted Quantitative Benchmark Values

| Quantity | Proposed Adaptive ($19{,}963$ FEs) | Standard PFM ($37{,}155$ FEs) | Navidtehrani (2021) [73] | Reference Basis |
| :--- | :---: | :---: | :---: | :---: |
| **Initial Elastic Stiffness $K_0$** | $\mathbf{47.70\,\text{kN/mm}}$ | $\mathbf{46.75\,\text{kN/mm}}$ | $\mathbf{45.51\,\text{kN/mm}}$ | Linear fit $u \in [0.5, 4.0]\,\mu\text{m}$ ($R^2 > 0.999$) |
| **Peak Reaction Force $F_{\max}$** | $\mathbf{365.74\,\text{N}}$ ($0.3657\,\text{kN}$) | $\mathbf{351.99\,\text{N}}$ ($0.3520\,\text{kN}$) | $\mathbf{332.67\,\text{N}}$ ($0.3327\,\text{kN}$) | Exact curve maximum |
| **Displacement at Peak $u(F_{\max})$** | $\mathbf{8.284\,\mu\text{m}}$ ($0.008284\,\text{mm}$) | $\mathbf{8.081\,\mu\text{m}}$ ($0.008081\,\text{mm}$) | $\mathbf{8.068\,\mu\text{m}}$ ($0.008068\,\text{mm}$) | Peak location |
| **Terminal Softening / Separation** | Vertical drop to 0 at $16.18\,\mu\text{m}$ | Vertical drop to 0 at $14.82\,\mu\text{m}$ | Vertical drop to 0 at $14.32\,\mu\text{m}$ | Complete fracture load drop |

---

## 3. Scientific Falsification Audit & Historical Corrections

### A. Falsification of Legacy $2\times$ Horizontal Axis Scaling
- **Historical Error:** In earlier task notes (F1345), Fig. 13(a) was incorrectly assumed to have a displacement axis spanning up to $0.038\,\text{mm}$ ($38\,\mu\text{m}$), producing false peak displacements of $u(F_{\max}) \approx 18.5 - 19.1\,\mu\text{m}$.
- **Audited Truth:** The primary PDF axis ticks are: `0`, `0.004`, `0.008`, `0.012`, `0.016 mm`. Peak reaction force occurs at $u_x = 8.07 - 8.28\,\mu\text{m}$.

### B. Falsification of $u_y$-Free Top Boundary Condition Hypothesis
- **Historical Conjecture:** When the peak displacement was falsely believed to be $\sim 19\,\mu\text{m}$, the implied initial stiffness was $K_0 \approx 23.2\,\text{kN/mm}$, which led to a hypothesis that the published model left the top edge free in $u_y$ ($K_{0,\text{free}} \approx 23.2\,\text{kN/mm}$).
- **Audited Truth:** The redigitized published stiffness is $K_0 = 47.19 - 47.70\,\text{kN/mm}$. The standard constrained Mode-II shear benchmark ($u_y=0$ on top) yields $K_0 = 45.80\,\text{kN/mm}$ (agreement within $3.2\%$). Both the literature and the project benchmark use standard constrained shear boundary conditions ($u_y = 0$).

### C. Falsification of Linear-Elastic Pre-Analysis for Fracture Remeshing
- **Historical Defect:** In Job `1410790.mmaster02`, an uninitialized UEL RHS vector caused damage to remain zero ($d \equiv 0$). The resulting pre-analysis generated an isotropic circular mesh cluster around the notch tip $(0.5, 0.5)$ because linear elasticity has only a static $1/\sqrt{r}$ tip singularity.
- **Audited Truth:** Pandey & Kumar Fig. 6(b) displays an inclined refinement corridor from $(0.5, 0.5)$ to $(0.85, 0.15)$ because their pre-analysis was an actual **damage-evolving fracture simulation** on the coarse mesh (`Job-1_UEL.inp`). As the crack propagates diagonally, high stress gradients and MISESERI errors track the moving crack tip, producing the complete diagonal refinement path. Job `1411104.mmaster02` verified this behavior, propagating fully to the bottom surface at an angle of $-57.95^\circ$ with $F_{\max} = 514.51\,\text{N}$.

---

## 4. Derived Data Files
- High-resolution redigitized curve: `references/derived/pandey_kumar_2025_fig13a_authoritative_redigitized.csv`
- Primary figure provenance: `Literature review/TSP_CMES_67858.pdf`, p. 3272, Fig. 13(a)
- Verification script: `scripts/postprocessing/plot_mode2_root_cause_and_literature_reconciliation.py`
