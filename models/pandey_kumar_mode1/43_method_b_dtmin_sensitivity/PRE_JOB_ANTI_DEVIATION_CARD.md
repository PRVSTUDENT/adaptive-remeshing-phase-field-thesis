# Pre-Job Anti-Deviation Card: Package 43 (Mode-I dt_min Post-Peak Sensitivity)

## 1. Governance & Proposal Mapping
- **Proposal Task**: Task 3 (Conventional Reference & Verification) & Task 4 (Native Remeshing Evaluation)
- **Active Gate**: Gate 6B (Mode-I Energetic & Convergence Qualification)
- **Scientific Roadmap Stage**: MODE1_GATE6B_ACTIVE_EVALUATION_AND_CONTINUATION

## 2. Scientific Hypothesis & Research Question
- **Research Question**: Can a controlled reduction of the minimum permitted solution increment from $1.0\times 10^{-9}$ to $1.0\times 10^{-15}$ extend the retrospective fracture calculation to its prescribed final displacement ($u = 0.0100\text{ mm}$) while preserving the validated response over the previously completed loading interval ($u \le 0.007889\text{ mm}$)?
- **Hypothesis**: The previous termination of Jobs 1412465, 1412873, and 1413022 at $u = 0.007889\text{ mm}$ (Step 2 increment 2890) was caused by minimum increment cutback exhaustion ($dt < dt_{\min} = 1.0\times 10^{-9}$ with 10 cutbacks). Reducing $dt_{\min}$ to $1.0\times 10^{-15}$ tests whether the solver can traverse the localized residual softening step or whether physical equilibrium instability prevents further static convergence.

## 3. Single Intended Change & Frozen Baseline
- **Single Intended Change**: Step 2 `*STATIC` line parameter 3 ($dt_{\min}$) changed from `1.0E-9` to `1.0E-15`.
- **Frozen Properties**:
  - Domain geometry: $\Omega = 1.0\times 1.0\text{ mm}^2$, initial sharp slit $a_0 = 0.5\text{ mm}$ along $y = 0.5\text{ mm}$.
  - Mesh: 14,483 finite elements (14,357 CPE4 + 126 CPE3), 14,646 nodes, 43,449 3-layer records.
  - Boundary conditions: $u_y = 0$ on bottom edge (N_BOTTOM wrapped cards), pinned corner $(0,0)$ $u_x = 0$, displacement control on RP 999999.
  - Material parameters: $E = 210\text{ GPa}$, $\nu = 0.3$, $G_c = 2.7\times 10^{-3}\text{ kN/mm}$, $l_0 = 0.0075\text{ mm}$.
  - User subroutine: `f42_mixed_uel.for` (SHA-256 `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`).
  - Solver controls: NLGEOM=NO, `*CONTROLS, PARAMETERS=TIME INCREMENTATION` (`4, 10, 9, 20, 10, 4, 0, 10`).

## 4. Pre-Declared Acceptance Criteria
1. Initial structural stiffness $K_0 = 137.9096 \pm 0.05\text{ kN/mm}$.
2. Peak load $F_{\max} = 0.743701 \pm 0.0005\text{ kN}$ at $u(F_{\max}) = 0.005733\text{ mm}$.
3. Parity with Jobs 1412465 / 1412873 / 1413022 over $u \in [0, 0.007889\text{ mm}]$.
4. Quantitative record of increment 2890 behavior: cutback trajectory down to $dt < 1.0\times 10^{-9}$ and terminal state ($u_{\text{final}}$, $RF_{\text{final}}$, exit code).
