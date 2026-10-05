# PRE-JOB ANTI-DEVIATION CARD: Mode-II Job-1_UEL Preanalysis

## 1. Governing Reference & Objective
- **Reference**: Pandey & Kumar (2025), *Comput. Model. Eng. Sci.* 144(3):3255–3283, Section 4.2, Figs. 6(b), 12(b).
- **Objective**: Execute the paper-grounded Phase-Field UEL pre-analysis (`Job-1_UEL.inp`) to generate the true propagating shear damage field and extract `MISESERI` for subsequent native adaptive remeshing.

## 2. Model & Discretization Specification
- **Domain**: $1.0 \times 1.0$ mm square plate ($x \in [0, 1], y \in [0, 1]$ mm).
- **Crack Notch**: Sharp crack seam along $y = 0.5$ mm, $x \in [0.0, 0.5]$ mm.
- **Physical Discretization**: Uniform coarse mesh $h = 0.02$ mm, 2,960 elements (2,860 CPE4 quads, 100 CPE3 triangles), 3,036 nodes.
- **Architecture**: 3-Layer Mixed UEL/UMAT:
  - Layer 1 (IDs 1..2960): Phase elements (U1 quads, U3 tris, active DOF 3).
  - Layer 2 (IDs 2961..5920): Mechanical elements (U2 quads, U4 tris, active DOFs 1, 2).
  - Layer 3 (IDs 5921..8880): Companion visualization elements (CPE4 quads, CPE3 tris in `All_elem` / `umatelem`).

## 3. Physical Parameters & ABI Contract
- $l_0 = 0.015$ mm ($15\,\mu\text{m}$)
- $G_c = 0.0027$ kN/mm ($2.7\times 10^{-3}$ kN/mm = 2,700 J/m$^2$)
- $E = 210.0$ kN/mm$^2$ (210 GPa)
- $\nu = 0.3$
- $k = 1.0\times 10^{-7}$
- $N_{\text{phys}} = 2960.0$

## 4. Boundary & Loading Conditions
- **Bottom Edge** ($y = 0$): $u_x = 0, u_y = 0$.
- **Top Edge** ($y = 1$): Horizontal shear $u_x$ applied via Reference Point (RP 999999) tied to top nodes with `*EQUATION`; $u_y = 0$.
- **Step 1**: 2,100 increments at $\Delta u_1 = 5\times 10^{-4}$ mm ($u \to 0.0105$ mm).
- **Step 2**: 5,000 increments at $\Delta u_2 = 10^{-5}$ mm ($u \to 0.0600$ mm).

## 5. Output Verification
- `*Element Output, elset=All_elem, directions=YES`: `MISESERI, MISESAVG, S, EVOL`
- `*Element Output, elset=umatelem`: `SDV`
- `*Node Output, nset=N_RP`: `U, RF`
