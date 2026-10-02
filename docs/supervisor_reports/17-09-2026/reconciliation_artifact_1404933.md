# Lightweight Numerical Provenance Reconciliation: Job 1404933.mmaster02

**Target Simulation:** Job `1404933.mmaster02` (Corrected Nominal 1% Adaptive Model)  
**Raw Curve CSV:** `D:\Master thesis\Adaptive remeshing\results\pandey_kumar_mode1\master_fracture_curves\curve_1404933_extracted.csv`  
**Raw CSV SHA-256:** `f71f01d150b12355f7a9f4a4a19563fe6e046ec31d94fe5abe85c103eadf3d56`  
**Archived Verification Script:** `reconcile_k0_1404933.py`  
**Selected Rows CSV:** `reconciliation_1404933_selected_rows.csv`  
**Selected Rows CSV SHA-256:** `ca4426baef68393521d8b9ba31c80c09d57a2754972bbffae7ebc794ce05a415`

---

## 1. Zero-Displacement Row & Discretization Provenance
- In `curve_1404933_extracted.csv`, **Row 0 does contain an un-deformed zero-displacement record**:  
  `u = 0.000000 mm, F = -0.000000 kN, Step-1, frame 0`.
- The active displacement loading increments start at frame 1 with $\Delta u = 2.5 \times 10^{-6}\,\text{mm}$ ($2.5\,\mu\text{m}$ nominal).
- Due to numerical floating-point accumulation in Abaqus' solver time integrator, frame 400 is recorded in the CSV as:  
  `u = 1.0000000475e-03 mm, F = 1.3779945672e-01 kN, Step-1, frame 400`.
- This is $+4.75 \times 10^{-11}\,\text{mm}$ above nominal $0.0010000000\,\text{mm}$.

---

## 2. Root Cause of the Obsolete $137.821802$ / $137.822\,\text{kN/mm}$ Artifact
- **Why an unhedged value filter failed:**  
  A naive Python condition `u <= 0.0010` (or `u <= 0.00100000001`) evaluated `1.0000000475e-03 <= 0.0010` as `False`, dropping frame 400.
- **Why positional slicing failed:**  
  An unhedged Python slice `df.iloc[1:400]` extracted rows 1 through 399 ($N=399$), stopping at $u = 0.0009975\,\text{mm}$.
- **Consequence:**  
  Both bugs produced an incomplete sample of $N=399$ points, yielding:
  $$K_0 = 137.821801967446\,\text{kN/mm} \to \mathbf{137.821802\,\text{kN/mm}}$$
  When rounded to 3 decimals, $137.8218 \to 137.822\,\text{kN/mm}$.

---

## 3. Authoritative Value-Based Regression ($N=400$)
Using the standard discrete half-bin selection rule:
$$\frac{1}{2}\Delta u < u \le u_{\max} + \frac{1}{2}\Delta u \quad (\Delta u = 2.5 \times 10^{-6}\,\text{mm}, \; u_{\max} = 0.0010\,\text{mm})$$
which robustly eliminates the zero-displacement initial state ($u=0$) while correctly including all $N=400$ active loading increments up to the nominal $1.0\,\mu\text{m}$ boundary:

- **Sample Size:** $N = 400$ points
- **Displacement Bounds:**
  - $u_{\min} = 2.4999999368 \times 10^{-6}\,\text{mm}$ (Increment 1)
  - $u_{\max} = 1.0000000475 \times 10^{-3}\,\text{mm}$ (Increment 400)
- **Unconstrained OLS Regression ($F = K_0 u + b$):**
  - **Initial Stiffness $K_0$ (Exact):** $137.820803658295\,\text{kN/mm}$
  - **Intercept $b$:** $4.470213 \times 10^{-5}\,\text{kN}$
  - **Goodness of Fit ($R^2$):** $0.999999599190$

---

## 4. Mathematically Correct Rounding Conventions
Because the 4th decimal digit of $137.820804...$ is `8` ($8 \ge 5$), the mathematically correct roundings are:
- **Six decimal places:** $\mathbf{137.820804\,\text{kN/mm}}$
- **Three decimal places:** $\mathbf{137.821\,\text{kN/mm}}$ *(NOT $137.822$)*
- **Two decimal places:** $\mathbf{137.82\,\text{kN/mm}}$

---

## 5. Recomputed Exact Relative Shifts vs Anchors
- **Fixed Reference Anchor (Job 1398090):**  
  $K_0 = 137.945520\,\text{kN/mm}$, $b = 4.472368 \times 10^{-5}\,\text{kN}$, $R^2 = 0.99999960$, $N=400$.  
  $$\text{Shift} = \frac{137.820804 - 137.945520}{137.945520} \times 100\% = \mathbf{-0.0904\%}$$
- **Frozen Corrected Model (Job 1405044):**  
  $K_0 = 138.021013\,\text{kN/mm}$, $b = 9.948 \times 10^{-12}\,\text{kN}$, $R^2 = 1.00000000$, $N=400$.  
  $$\text{Shift vs Reference} = \frac{138.021013 - 137.945520}{137.945520} \times 100\% = \mathbf{+0.0547\%}$$
