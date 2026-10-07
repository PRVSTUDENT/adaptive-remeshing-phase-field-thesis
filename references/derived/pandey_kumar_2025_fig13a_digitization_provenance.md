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
| Boundary Conditions | Bottom: $u_x=u_y=0$, Top: $u_x$ applied | Fixed bottom, Top shear | — | `PAPER_VERIFIED` |
| Strain Energy Split | Miehe Anisotropic Split | Spectral decomposition | — | `PAPER_VERIFIED` |
| Literature Remeshing Rule `errorTarget` | `errorTarget` | **Unpublished / Not stated** | — | `UNRESOLVED` |
| Project Remeshing Selection | `ET_2PCT` | $22{,}530$ elements | — | `INFERRED / PROJECT_SELECTED_FOR_M2_4` |
| Literature Adaptive Mesh | Proposed PFM | $19{,}963$ elements | — | `POST_HOC_REPRODUCTION_COMPARISON` ($+12.86\%$) |

---

## 2. Quantitative Summary of Digitized Figure 13(a)

| Quantity | Proposed Adaptive ($19{,}963$ FEs) | Standard PFM ($37{,}155$ FEs) | Literature Reference Basis | Defensible Gate M2-4 Tolerance Window |
| :--- | :---: | :---: | :---: | :---: |
| **Initial Shear Stiffness $K_{0,\text{shear}}$** | $\mathbf{12.80\,\text{kN/mm}}$ | $\mathbf{12.80\,\text{kN/mm}}$ | Linear elastic range ($u_x \le 0.006\,\text{mm}$) | $[11.5, 14.5]\,\text{kN/mm}$ ($\pm 12\%$) |
| **Peak Reaction Force $F_{\max}$** | $\mathbf{0.1455\,\text{kN}}$ ($145.5\,\text{N}$) | $\mathbf{0.1435\,\text{kN}}$ ($143.5\,\text{N}$) | Fig. 13(a) peak load | $[0.125, 0.165]\,\text{kN}$ ($\pm 14\%$) |
| **Displacement at Peak $u(F_{\max})$** | $\mathbf{0.0128\,\text{mm}}$ ($12.8\,\mu\text{m}$) | $\mathbf{0.0125\,\text{mm}}$ ($12.5\,\mu\text{m}$) | Fig. 13(a) peak location | $[0.0110, 0.0145]\,\text{mm}$ ($\pm 13\%$) |
| **Reaction Force at $u_x=0.020\,\text{mm}$** | $\mathbf{0.0380\,\text{kN}}$ ($38.0\,\text{N}$) | $\mathbf{0.0480\,\text{kN}}$ ($48.0\,\text{N}$) | Step 2 horizon endpoint ($u=20\,\mu\text{m}$) | $\le 0.060\,\text{kN}$ (load drop $\ge 60\%$) |
| **Softening Load Drop at $u_x=0.020\,\text{mm}$** | $\mathbf{73.88\%}$ | $\mathbf{66.55\%}$ | Softening extent at $u=20\,\mu\text{m}$ | $\ge 60.0\%$ load reduction |
| **Full Separation Horizon ($u_x \ge 0.030\,\text{mm}$)** | $0.0140\,\text{kN}$ ($14.0\,\text{N}$, $90.4\%$ drop) | $0.0180\,\text{kN}$ ($18.0\,\text{N}$, $87.5\%$ drop) | Final asymptotic tail in Fig. 13(a) | Beyond active $20\,\mu\text{m}$ solve horizon |

---

## 3. Quantitative Summary of Figures 6(b) and 12(a,b) Crack Trajectory

| Geometric Metric | Observed Literature Value | Derivation / Coordinate Basis | Defensible Acceptance Window |
| :--- | :---: | :---: | :---: |
| **Crack Tip Origin** | $(x_0, y_0) = (0.50, 0.50)\,\text{mm}$ | Initial slit right end at specimen mid-plane | Exact $(0.50, 0.50)\,\text{mm}$ |
| **Bottom Boundary Exit** | $x_{\text{exit}} \approx 0.930\,\text{mm}$ ($y=0$) | Fig. 6(b) & Fig. 12(b) intersection with bottom boundary | $x_{\text{exit}} \in [0.85, 1.00]\,\text{mm}$ |
| **Mean Trajectory Chord Angle** | $\theta_{\text{chord}} \approx -49.3^\circ$ | $\arctan\left(\frac{0.0 - 0.50}{0.930 - 0.50}\right) = \arctan(-1.1628)$ | $\theta \in [-60^\circ, -40^\circ]$ |
| **Initial Crack Kink Angle** | $\theta_{\text{kink}} \approx -55^\circ \text{ to } -60^\circ$ | Angle near crack tip $(0.50, 0.50)$ under pure shear | Local angle $\in [-65^\circ, -45^\circ]$ |
| **Trajectory Morphology** | Smooth curved path toward lower-right corner | No horizontal unzipping ($y=0.5$), no upward propagation | Distinctly oblique shear fracture |

---

## 4. Provenance Audit Findings on Frozen Criteria M2_4_CHK6 & M2_4_CHK7

1. **Audit of Check `M2_4_CHK6` ($F_{\max}$ and $u(F_{\max})$):**
   - **Finding:** The previously drafted interval $F_{\max} \in [0.45, 0.70]\,\text{kN}$ was an erroneous legacy transfer from Mode-I (tensile $F_{\max} \approx 0.758\,\text{kN}$). In Mode-II shear, primary Fig. 13(a) shows $F_{\max} \approx 0.1455\,\text{kN}$.
   - **Finding on Peak Location:** The previously drafted $u(F_{\max}) \in [0.0090, 0.0125]\,\text{mm}$ was too narrow and cut off before the literature peak at $u_x = 0.0128\,\text{mm}$.
   - **Finding on Residual Load:** The previously drafted requirement of $> 90\%$ load drop at the end of the simulation applied to $u \ge 0.030\,\text{mm}$, whereas our simulation horizon terminates at $u_x = 0.0200\,\text{mm}$ where Fig. 13(a) shows $F \approx 0.038\,\text{kN}$ (a $73.9\%$ load drop).
   - **Resolution:** Replaced with audited primary benchmark values:
     $F_{\max} \in [0.125, 0.165]\,\text{kN}$, $u(F_{\max}) \in [0.0110, 0.0145]\,\text{mm}$, and $F(u=0.020\,\text{mm}) \le 0.060\,\text{kN}$ (load drop $\ge 60\%$).

2. **Audit of Check `M2_4_CHK7` (Crack Path & Bottom Exit):**
   - **Finding:** The bottom-exit window $x_{\text{exit}} \in [0.85, 1.00]\,\text{mm}$ and trajectory angle interval $[-65^\circ, -40^\circ]$ are directly confirmed by Fig. 6(b), Fig. 12(b), and literature shear fracture physics (chord angle $-49.3^\circ$, exit $x \approx 0.930\,\text{mm}$).
   - **Resolution:** Retained with explicit mathematical and coordinate provenance.
