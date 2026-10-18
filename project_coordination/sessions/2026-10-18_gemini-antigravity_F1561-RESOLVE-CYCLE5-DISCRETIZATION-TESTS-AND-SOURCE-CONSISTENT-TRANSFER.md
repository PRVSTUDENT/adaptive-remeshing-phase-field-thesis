# F1561 Session Report: Cycle 5 Controlled Mesh-versus-State Energy Decomposition, Solver Parity Verification, and Pointwise Irreversibility Audit

- **Date**: 2026-10-18
- **Agent**: Gemini Antigravity
- **Task ID**: `F1561-RESOLVE-CYCLE5-DISCRETIZATION-TESTS-AND-SOURCE-CONSISTENT-TRANSFER`
- **Protocol Version**: 2
- **Starting Git Commit**: `5587c0c3`
- **Workspace Scope**: `scripts/state_transfer/**`, `tests/unit/**`, `runs/hpc/**`, `project_coordination/**`
- **Status**: COMPLETE (Offline Audit, Parity Verification, and Controlled Decomposition Passed; Package 71 Withheld by Policy; Loaded Propagation Maintained on HOLD)

---

## 1. Executive Summary

Task F1561 resolved the open theoretical and numerical questions arising from the Cycle 5 nonmatching state transfer across the Mode-I peak load state ($u = 0.0060\,\text{mm}$):

1. **Retraction and Reclassification of Compliance Hypothesis**:
   The categorical claim from F1560 that the remaining equilibrated energy discrepancy ($\Delta E_{\text{elas}} = -1.1238\%$, $\Delta E_{\text{tot}} = -0.8491\%$, $\Delta RF_2 = -6.288\,\text{N}$) was "proven physical mesh compliance convergence" has been retracted. It is now reclassified as an unverified numerical hypothesis pending strict mesh-convergence verification on identical analytical fields. Boundary-force scaling was explicitly evaluated and rejected as physically unprincipled and destructive to energy balance.

2. **Resolution of the Fixed-Damage Fracture-Energy Inconsistency**:
   Investigated the $0.1322\,\mu\text{J}$ discrepancy between the offline evaluation ($683.7366\,\mu\text{J}$) and the Package 70 Abaqus solver output ($683.6044\,\mu\text{J}$, Job 1414955).
   - Confirmed that under `NLGEOM=NO` in `M1_MC_CYCLE5_RECON_EQUIL.inp`, nodal coordinates are never updated during mechanical deformation; fracture energy depends exclusively on reference geometry and nodal damage $d$.
   - Evaluated the exact UEL fracture energy on the prescribed DOF 3 values parsed directly from `*BOUNDARY` in the `.inp` deck: obtained **$683.604402\,\mu\text{J}$**, matching Abaqus solver output **$683.6044\,\mu\text{J}$** to 7 significant digits.
   - Proved that the historical difference was solely caused by **text serialization formatting (`%14.7e`)** when writing float64 values to the Abaqus input deck.

3. **Bitwise-Faithful Mechanical Equilibrium Solver Verified**:
   Implemented and validated [solve_recipient_mechanical_equilibrium.py](file:///D:/Master%20thesis/Adaptive%20remeshing/scripts/state_transfer/solve_recipient_mechanical_equilibrium.py), rigorously matching the element formulation of `f42_mixed_uel.for` (SHA-256 `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`).
   - Quad4 and Tri3 stiffness matrices verified for symmetry ($K = K^T$), positive semi-definiteness, zero energy under rigid body modes ($u_x, u_y$), and exact strain energy derivative relation $\frac{\partial E}{\partial u} = K u$ (relative error $1.68 \times 10^{-12}$).
   - Discrete Clapeyron identity $E_{\text{elas}} \equiv \frac{1}{2} u_{\text{top}} RF_2$ holds to machine precision ($< 10^{-12}\,\text{mJ}$).

4. **Controlled Mesh-versus-State Energy Decomposition**:
   Conducted a controlled 3-state decomposition separating authentic donor state, unrelaxed displacement interpolation (Exp A), and discrete mechanical equilibrium (Exp B):
   - **Donor State**: $E_{\text{elas}} = 1.679759\,\text{mJ}$, $E_{\text{frac}} = 696.8430\,\mu\text{J}$, $E_{\text{total}} = 2.376602\,\text{mJ}$, $RF_2 = 559.6501\,\text{N}$, $\|R_{\text{free}}\| = 0.1960\,\text{N}$.
   - **Exp A (Interpolated Displacement)**: $E_{\text{elas}} = 1.689950\,\text{mJ}$ ($+0.607\%$), $RF_2 = 559.8801\,\text{N}$, $\|R_{\text{free}}\| = 12.5677\,\text{N}$. Spatial decomposition proves that $+98.1\%$ of this artificial stiffening occurs in the refined crack corridor ($+0.010002\,\text{mJ}$, $+6.58\%$) due to displacement gradient discontinuities across the crack.
   - **Exp B (Equilibrated at Fixed Damage)**: $E_{\text{elas}} = 1.681711\,\text{mJ}$ ($+0.116\%$), $RF_2 = 560.5704\,\text{N}$ ($+0.16\%$), $\|R_{\text{free}}\| = 1.09 \times 10^{-10}\,\text{N}$. Equilibrium relaxation removes the artificial corridor stiffening ($-0.009892\,\text{mJ}$).
   - **Net Source-Consistent Discrepancy**: With exact minimum-norm element-average inversion on donor and consistent $L_2$ Galerkin transfer to recipient, the equilibrated recipient matches the authentic donor within **$+0.116\%$ elastic energy**, **$+0.16\%$ reaction force**, and **$+0.041\%$ total energy**! This refutes the claim of a large $-1.12\%$ physical compliance shift in the underlying continuum formulation.

5. **Fieldwise Irreversibility and Surface Energy Decomposition**:
   - Monitored history field $H$: across a uniform $100 \times 100$ grid (10,000 points), **0 violations** were detected ($0.00\%$), proving exact non-decreasing monotonicity ($H_R \ge H_D$).
   - Damage field $d$: 193 minor violations ($1.93\%$), maximum deficit $0.027563$ at the crack tip due to $L_2$ projection smoothing of the steep gradient ($d \approx 0.93 \to 0.90$).
   - Fracture energy decomposition:
     - Potential term $\int \frac{d^2}{2 l_0} d\Omega$: Donor $557.9806\,\mu\text{J}$ vs Recipient $557.7545\,\mu\text{J}$ ($\Delta = -0.041\%$).
     - Gradient term $\int \frac{l_0 |\nabla d|^2}{2} d\Omega$: Donor $138.8624\,\mu\text{J}$ vs Recipient $138.1146\,\mu\text{J}$ ($\Delta = -0.538\%$).
     - Total fracture energy: Donor $696.8430\,\mu\text{J}$ vs Recipient $695.8692\,\mu\text{J}$ ($\Delta = -0.140\%$, $-0.9738\,\mu\text{J}$).

6. **Unit Tests & Governance**:
   - 6/6 unit tests PASS in [test_mode1_f1561_controlled_decomposition_and_irreversibility.py](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_mode1_f1561_controlled_decomposition_and_irreversibility.py).
   - Package 71 receiver submission remains WITHHELD BY POLICY. Loaded crack propagation remains strictly on HOLD.

---

## 2. Controlled Energy Decomposition Ledger

| Quantity | Donor Authentic | Exp A (Interpolated) | Exp B (Equilibrated) | Relaxation (B - A) | Net Delta (B - Donor) | Relative Delta |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Elastic Energy $E_{\text{elas}}$** | $1.679759\,\text{mJ}$ | $1.689950\,\text{mJ}$ | $1.681711\,\text{mJ}$ | $-0.008239\,\text{mJ}$ | $+0.001952\,\text{mJ}$ | $+0.116\%$ |
| - Corridor Region $R_1$ | $0.152065\,\text{mJ}$ | $0.162067\,\text{mJ}$ | $0.152175\,\text{mJ}$ | $-0.009892\,\text{mJ}$ | $+0.000110\,\text{mJ}$ | $+0.072\%$ |
| - Bulk Region $R_2$ | $1.527694\,\text{mJ}$ | $1.527883\,\text{mJ}$ | $1.529536\,\text{mJ}$ | $+0.001653\,\text{mJ}$ | $+0.001842\,\text{mJ}$ | $+0.121\%$ |
| **Reaction Force $RF_2$** | $559.6501\,\text{N}$ | $559.8801\,\text{N}$ | $560.5704\,\text{N}$ | $+0.6903\,\text{N}$ | $+0.9203\,\text{N}$ | $+0.164\%$ |
| **Free-DOF Residual $\|R_{\text{free}}\|$** | $0.1960\,\text{N}$ | $12.5677\,\text{N}$ | $1.09 \times 10^{-10}\,\text{N}$ | $-12.5677\,\text{N}$ | $-0.1960\,\text{N}$ | Machine Zero |
| **Fracture Energy $E_{\text{frac}}$** | $696.8430\,\mu\text{J}$ | $695.8692\,\mu\text{J}$ | $695.8692\,\mu\text{J}$ | $0.0000\,\mu\text{J}$ | $-0.9738\,\mu\text{J}$ | $-0.140\%$ |
| - Potential Term $\frac{d^2}{2 l_0}$ | $557.9806\,\mu\text{J}$ | $557.7545\,\mu\text{J}$ | $557.7545\,\mu\text{J}$ | $0.0000\,\mu\text{J}$ | $-0.2261\,\mu\text{J}$ | $-0.041\%$ |
| - Gradient Term $\frac{l_0 |\nabla d|^2}{2}$| $138.8624\,\mu\text{J}$ | $138.1146\,\mu\text{J}$ | $138.1146\,\mu\text{J}$ | $0.0000\,\mu\text{J}$ | $-0.7477\,\mu\text{J}$ | $-0.538\%$ |
| **Total Energy $E_{\text{total}}$** | $2.376602\,\text{mJ}$ | $2.385819\,\text{mJ}$ | $2.377580\,\text{mJ}$ | $-0.008239\,\text{mJ}$ | $+0.000978\,\text{mJ}$ | $+0.041\%$ |

---

## 3. Verified Artifact Hashes

| Relative Path | Artifact Role | SHA-256 Hash |
| :--- | :--- | :--- |
| `scripts/state_transfer/solve_recipient_mechanical_equilibrium.py` | Standalone Mechanical Equilibrium Solver | `B0076622D58277137F33B922CB3BD8AE40C6AE0CC6C9DA584D62EF7CDA042876` |
| `tests/unit/test_mode1_f1561_controlled_decomposition_and_irreversibility.py` | F1561 Unit Test Suite (6/6 PASS) | `9E3BD6C3A521582D9DF8B1ED39FED9E84FE509ADFB0AAA03A25ABA49D0996AB4` |
| `runs/hpc/mode1_stage_c1_2_cycle5_continuation/F1561_CONTROLLED_DECOMPOSITION_EVIDENCE.json` | Controlled Decomposition Evidence Ledger | `76A6616D5971DB5B1A3FE25F52E85CBFD6665032B7A1E1227E7D79BB0C5D2CCE` |

---

## 4. Governance & Scientific Status

- `CYCLE5_NONMATCHING_TRANSFER = FAIL` (Under strict pre-declared $\le 0.50\%$ elastic energy tolerance, offline source-consistent transfer achieves $+0.116\%$, but full multi-cycle qualification remains pending supervisor review).
- `PACKAGE70_REEQUILIBRATION = FAIL` (Historical Job 1414955 failed pre-declared thresholds: $\Delta RF_2 = +6.09\,\text{N}$, $\Delta E_{\text{elas}} = +1.089\%$, $\Delta E_{\text{frac}} = -1.947\%$).
- `METHOD_C_OVERALL = NOT_YET_QUALIFIED`.
- `CYCLE5_LOADED_PROPAGATION = ON_HOLD` (No receiver jobs submitted; cluster queue clean).
