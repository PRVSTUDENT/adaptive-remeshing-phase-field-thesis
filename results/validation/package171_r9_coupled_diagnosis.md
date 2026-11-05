# Package 171-R9 Stage C3-0 Coupled PDAS Nonconvergence Diagnostic Report

**Task ID:** `F1613-PACKAGE171-R10-C6-COUPLED-CONVERGENCE-DIAGNOSIS`  
**PBS Production Job ID:** `1420215.mmaster02`  
**Receiver Discretization:** C6 locally refined mesh (15,252 CPE4 quads, 15,559 nodes, 59 slit pairs, 61,008 Gauss points)  
**Held Displacement:** $u_y = 0.0018703125\,\text{mm}$  
**Completed Outer Iterations:** 140 / 140  

---

## 1. Executive Diagnostic Findings

1. **Unrelaxed Step Norm Hypothesis Fully Validated:**
   - In predecessor R8 (Job 1420188), evaluating relaxed increments across the stage transition caused 18/18 false divergence rollbacks due to $\omega_{S2}/\omega_{S1} = 0.85/0.50 = 1.70 > 1.50$.
   - In R9 (Job 1420215), evaluating the intrinsic unrelaxed fixed-point step norm $\|\delta d_{\text{raw}}\|_\infty = \|\tilde{d}_{\text{PDAS}} - d^{(k)}\|_\infty$ completely eliminated the artifact.
   - Stage 2 acceleration was admitted at Outer 89 and **sustained for 52 consecutive iterations (Outer 89 through 140) with ZERO rollbacks**.

2. **Strict Active-Set Stationarity & KKT Satisfaction:**
   - The active set contracted from 13,803 active nodes at Outer 1 down to **35 nodes** at Outer 125 (**99.75% reduction**).
   - For the final 15 outer iterations (Outer 126 through 140), the active set was **100% stationary** ($|A_k| = 35$, $|\Delta A_k| = 0$, $\Delta A^+ = 0$).
   - Phase-field KKT conditions were strictly satisfied: free error $6.48 \times 10^{-8} \ll 10^{-6}$, dual error $9.78 \times 10^{-10} \ll 10^{-6}$, complementarity $4.72 \times 10^{-8} \ll 10^{-6}$.
   - Pointwise damage irreversibility ($d \ge d_0$) and history monotonicity ($H^* \ge H_0$) were strictly maintained with **0 violations**.

3. **Decoupled Contraction Dynamics & Cyclic Oscillation Mechanism:**
   - While phase damage $\Delta d$ contracted monotonically at a steady geometric rate $\rho_d = 0.9848$, mechanical displacement $\Delta u$ and driving history $\Delta H$ did **not** contract monotonically.
   - Across the stationary active-set interval (iterations 126–140), displacement increments exhibited a geometric mean ratio $\rho_u = 1.0032 > 1.0$, oscillating cyclically with a period of **5 to 6 outer iterations** around a plateau of $\sim 5.0 \times 10^{-5}\,\text{mm}$.
   - Root cause: The mechanical subproblem solve ($u$) and driving history update ($H$) are completely **unrelaxed** ($\omega_u = 1.0$, $\omega_H = 1.0$). Small stiffness perturbations from $\Delta d \approx 0.008$ around the crack tip induce unrelaxed mechanical displacement adjustments $\Delta u \approx 5 \times 10^{-5}\,\text{mm}$, which amplify quadratically into large strain-energy oscillations $\Delta H \approx 250\text{--}350\,\text{MPa}$, preventing coupled fixed-point closure within 140 iterations.

---

## 2. Quantitative Contraction Factor Analysis

### A. Full Stage 2 Window (Outer Iterations 90 to 140; 51 steps)

| Variable | Arithmetic Mean $\bar{\rho}$ | Geometric Mean $\rho_{\text{geom}}$ | Std Dev $\sigma$ | Min $\rho$ | Max $\rho$ | Coeff of Variation $c_v$ | Monotonicity |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Phase Damage Increment $\Delta d$ | 0.98502 | 0.98501 | 0.00206 | 0.98092 | 0.98912 | 0.0021 | **Strictly Monotone** ($< 1.0$ everywhere) |
| Displacement Increment $\Delta u$ | 1.00156 | 0.99413 | 0.12992 | 0.77844 | 1.63687 | 0.1297 | **Oscillatory** (Spread 0.78 to 1.64) |
| History Increment $\Delta H$ | 0.99773 | 0.99122 | 0.13256 | 0.85651 | 1.82612 | 0.1329 | **Oscillatory** (Spread 0.86 to 1.83) |

### B. Stationary Active-Set Window ($|A_k| = 35$, Outer Iterations 126 to 140; 15 steps)

| Variable | Arithmetic Mean $\bar{\rho}$ | Geometric Mean $\rho_{\text{geom}}$ | Std Dev $\sigma$ | Min $\rho$ | Max $\rho$ | Coeff of Variation $c_v$ | Convergence State |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Phase Damage Increment Delta d | 0.98483 | 0.98483 | 0.00258 | 0.98092 | 0.98912 | 0.0026 | **Monotone Contraction** (~0.9848) |
| Displacement Increment Delta u | 1.01168 | 1.00325 | 0.12748 | 0.77844 | 1.17651 | 0.1260 | **Stagnating / Oscillating Plateau** (> 1.0) |
| History Increment Delta H | 0.99015 | 0.98576 | 0.09347 | 0.85651 | 1.12617 | 0.0944 | **Fluctuating Amplitude** (+/- 10%) |

---

## 3. Investigation of Inter-Field Mechanical/Phase Coupling

### Coupling Ratios Across Stage 2
- **Displacement-to-Damage Ratio:** ||Delta u|| / ||Delta d|| = 6.6583e-03 +/- 7.1954e-04 mm (bounded in [4.4792e-03, 7.9486e-03]).
- **History-to-Damage Ratio:** ||Delta H|| / ||Delta d|| = 41525.20 +/- 5307.97 MPa (bounded in [27151.83, 50297.32]).

### The Resolution Paradox: Why KKT Passes While the Fixed Point Fails
Within each outer staggered iteration, the phase-field linear system on the stationary free nodes:
$$K_{\text{free}}(H) d_{\text{free}} = F(H)$$
is solved by the PDAS solver to high numerical precision, yielding post-update KKT residuals:
- Free error: 6.4798e-08 <= 1.0e-6
- Dual error: 9.7837e-10 <= 1.0e-6
- Complementarity error: 4.7248e-08 <= 1.0e-6

However, because the mechanical displacement $u$ is updated without relaxation ($\omega_u = 1.0$), each update of $d$ perturbs the elastic stiffness tensor $(1-d)^2 + \eta$, inducing an immediate shift in $u$ of magnitude $\|\Delta u\|_\infty \approx 6.66 \times 10^{-3} \|\Delta d\|_\infty$. Because crack-driving history $H = \max(H_0, \psi_+)$ is quadratic in strains, this displacement change creates a large history shift $\|\Delta H\|_\infty \approx 4.15 \times 10^4 \|\Delta d\|_\infty$.

Consequently, even though the internal phase subproblem satisfies KKT stationarity, the outer fixed-point mapping $(u, d, H) \mapsto (u^+, d^+, H^+)$ has a dominant spectral radius close to unity ($\rho \approx 0.985$), which exhibits oscillatory ringing when $u$ is unrelaxed.

---

## 4. Evidence-Based Formulation of Candidate Package 171-R10

### Falsifiable Corrective Hypothesis
> **Hypothesis (Dual Relaxation with Stage 3 Damping):**  
> Introducing under-relaxation on the mechanical displacement field ($\omega_u = 0.85$) or driving history ($\omega_H = 0.85$) once active-set stationarity is established ($|\Delta A_k| \le 1$), combined with an asymptotic Stage 3 relaxation ($\omega_d = 0.95$), will damp the 5-iteration mechanical ringing, compress the coupled fixed-point spectral radius from $\rho \approx 0.985$ to $\rho \le 0.80$, and drive $\Delta d \le 10^{-5}$, $\Delta u \le 10^{-9}\,\text{mm}$, and $\Delta H \le 10^{-4}\,\text{MPa}$ within an allocated budget of 250 outer iterations.

### Algorithmic Specification for Candidate R10 Driver
1. **Displacement Under-Relaxation in Stage 2/3:**
   $$u^{(k)} = (1 - \omega_u) u^{(k-1)} + \omega_u u_{\text{Abaqus}}^{(k)}, \quad \omega_u = 0.85$$
   Eliminates the raw displacement overshoot and dampens stiffness-induced ringing.

2. **Driving History Filtering:**
   $$H^{(k)} = (1 - \omega_H) H^{(k-1)} + \omega_H \max(H_0, \psi_+(u^{(k)})), \quad \omega_H = 0.85$$
   Prevents quadratic strain energy spikes from destabilizing the phase-field subproblem.

3. **Asymptotic Stage 3 Phase Acceleration:**
   - **Trigger:** Admitted only when $|A_k| \le 50$ and $|\Delta A_k| = 0$ for $\ge 10$ consecutive iterations.
   - **Relaxation Factor:** $\omega_{S3} = 0.95$.
   - **Safeguard:** Preserves the verified unrelaxed step norm divergence guard $\|\delta d_{\text{raw}}\|_\infty \le 1.50 \|\delta d_{\text{raw, prev}}\|_\infty$.

4. **Budget & Execution Envelope:**
   - `max_outer`: 250 iterations (estimated CPU time: $\sim 1.8$ hours; queue limit: 12.0 hours).

### Explicit Numerical Acceptance Criteria (Strictly Preserved)
- Phase increment: $\Delta d \le 1.0 \times 10^{-5}$
- Displacement increment: $\Delta u \le 1.0 \times 10^{-9}\,\text{mm}$
- History increment: $\Delta H \le 1.0 \times 10^{-4}\,\text{MPa}$
- KKT Free Error: $\le 1.0 \times 10^{-6}$
- KKT Dual Error: $\le 1.0 \times 10^{-6}$
- KKT Complementarity: $\le 1.0 \times 10^{-6}$
- Pointwise Damage Healing: 0 violations ($d \ge d_0$)
- History Monotonicity: 0 violations ($H^* \ge H_0$)
- Reaction Force Discrepancy: $\le 2.0\%$ vs donor reference ($0.179924\,\text{kN}$)
- Total Energy Discrepancy: $\le 2.0\%$ vs donor reference ($0.000226399\,\text{kN}\cdot\text{mm}$)
- Frozen UEL SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` strictly preserved.

