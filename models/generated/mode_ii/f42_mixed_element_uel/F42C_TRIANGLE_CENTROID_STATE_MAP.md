# F42C Triangle Centroid State Variable Mapping Specification

## 1. Dedicated Centroid State Slot Definition
- **Quad Elements (`U1` / `U2`)**: Use quadrature slots `1, 2, 3, 4` in `USRVAR(PHYSIDX, SDV_ID, 1..4)`.
- **Triangle Elements (`U3` / `U4`)**: Use numerical quadrature slots `1, 2, 3` for numerical integration, and dedicated **Slot 4** (`USRVAR(PHYSIDX, SDV_ID, 4)`) as the **CENTROID / FACSIMILE OUTPUT SLOT**.

## 2. Per-State-Variable Centroid Reconstruction Rules

| SDV ID | State Variable Name | Physical Meaning | Field Topology Over T3 | Centroid Reconstruction Rule |
|---|---|---|---|---|
| `SDV 1` | `PHASE` ($\phi$) | Phase field damage ($0 \le \phi \le 1$) | Spatially Linear | Arithmetic mean: $\phi_c = \frac{1}{3}(\phi_1 + \phi_2 + \phi_3)$ |
| `SDV 2` | `HIST` ($\mathcal{H}$) | Crack driving energy history | Monotonic History | Maximum value: $\mathcal{H}_c = \max(\mathcal{H}_1, \mathcal{H}_2, \mathcal{H}_3)$ |
| `SDV 3..5` | `EPS` ($\boldsymbol{\varepsilon}$) | Strain tensor ($\varepsilon_{11}, \varepsilon_{22}, \gamma_{12}$) | Spatially Constant (CST) | Identity check: $\boldsymbol{\varepsilon}_c = \boldsymbol{\varepsilon}_1 = \boldsymbol{\varepsilon}_2 = \boldsymbol{\varepsilon}_3$ |
| `SDV 6..8` | `STRESS_E` ($\boldsymbol{\sigma}_e$) | Undegraded elastic stress tensor | Spatially Constant (CST) | Identity check: $\boldsymbol{\sigma}_{e,c} = \boldsymbol{\sigma}_{e,1} = \boldsymbol{\sigma}_{e,2} = \boldsymbol{\sigma}_{e,3}$ |
| `SDV 9..11` | `STRESS_D` ($\boldsymbol{\sigma}_d$) | Degraded stress tensor | Nonlinear Phase-Dependent | Physically reconstructed: $g_c = (1-\phi_c)^2 + k$, $\boldsymbol{\sigma}_{d,c} = g_c \boldsymbol{\sigma}_{e,c}$ |
| `SDV 12` | `ENERGY_E` ($\psi_e$) | Undegraded elastic energy density | Spatially Constant (CST) | Identity check: $\psi_{e,c} = \psi_{e,1} = \psi_{e,2} = \psi_{e,3}$ |
| `SDV 13` | `ENERGY_D` ($\psi_d$) | Degraded strain energy density | Nonlinear Phase-Dependent | Physically reconstructed: $\psi_{d,c} = g_c \psi_{e,c}$ |
| `SDV 14` | `KSTEP` | Current analysis step | Integer | Stamp: `KSTEP` |
| `SDV 15` | `KINC` | Current increment number | Integer | Stamp: `KINC` |
| `SDV 16` | `PHYSIDX` | Physical element index | Integer | Stamp: `PHYSIDX` |
| `SDV 17` | `TOPOLOGY` | Element topology marker | Marker | `3` for T3, `4` for Q4 |
| `SDV 18` | `VALID_STAMP` | Call validity stamp | Stamp | `KSTEP*100000 + KINC` |

## 3. History / Irreversibility Aggregation Contract
- Centroid slot 4 is **OUTPUT-ONLY** for visualization and post-processing.
- Core `U3` / `U4` numerical integration **never** reads centroid slot 4; `U3` / `U4` continue reading and updating their true 3 quadrature points (`NPT = 1, 2, 3`) independently to preserve strict historical irreversibility.

## 4. Element Topology Marker Specification
- Material parameter `PROPS(topology_marker)` explicitly declares element topology:
  - `PROPS(3) = 4` or `PROPS(4) = 4` $\rightarrow$ Quad Facsimile (`CPE4`).
  - `PROPS(3) = 3` or `PROPS(4) = 3` $\rightarrow$ Triangle Facsimile (`CPE3`).
- Subroutine `UMAT` inspects `PROPS` topology marker:
  - If `TOPOLOGY == 4`: Reads `USRVAR(PHYSIDX, :, NPT)` for $NPT \in [1, 4]$.
  - If `TOPOLOGY == 3`: Reads **ONLY** `USRVAR(PHYSIDX, :, 4)` (the dedicated centroid slot).
  - If `TOPOLOGY` is unknown: Fails closed (`CALL XIT` or error log).

## 5. Call-Order & Stale-State Protection Contract
- Centroid cache validity stamp: `USRVAR(PHYSIDX, 18, 4) = KSTEP * 100000 + KINC`.
- When `CPE3 UMAT` executes at `(KSTEP, KINC)`:
  - Verifies `USRVAR(PHYSIDX, 18, 4) == KSTEP * 100000 + KINC`.
  - If the stamp matches, reads centroid slot 4.
  - If stamp is stale or uninitialized, computes centroid on-the-fly from slots 1..3 or rejects stale cache safely.
