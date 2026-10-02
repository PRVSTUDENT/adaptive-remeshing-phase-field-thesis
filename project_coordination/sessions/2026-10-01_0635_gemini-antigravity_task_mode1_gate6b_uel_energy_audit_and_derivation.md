# Session Report: Gate 6B UEL Energy Formulation, Mathematical Derivation, and Output Audit

- **Date / Timestamp**: 2026-10-01T06:35:00+02:00
- **Agent**: `gemini-antigravity`
- **Task ID**: `task_mode1_gate6b_uel_energy_audit_and_derivation` / `F1098`
- **Starting Commit**: `42762382e8e0f4a8fc87b43eb0ddfba06028bcaf`
- **Governing Directive**: *"We need to have understood everything related to the first model before we increase complexity."*

---

## 1. Executive Summary & Deliverables

1. **Closure of Pandey--Kumar Job-1 Pre-Analysis Branch**:
   - Reclassified the reproducible 48,329-element mesh as `PROJECT_REPRODUCIBLE_STEP1_1PCT_RESULT`.
   - Corrected unsupported publication claims: the publication details the 500-increment first stage and 1000-increment second stage, but omits the exact `stepName`/frame filtering syntax for `RemeshingRule`.
   - Formally designated the remaining gap to 13,941 as `UNRESOLVED_PUBLICATION_IMPLEMENTATION_DETAIL` and `FRAME_SELECTION_SEMANTICS_UNRESOLVED`.
   - Confirmed that exact 13,941 reproduction is **not an active blocker**.
   - Updated supervisor report (`report_main.pdf`, 26 pages, SHA-256 `D09A54B39357CD847E752363F5EBB9495DB8E2B2750412A0A0EAE577BA32C704`).

2. **Authoritative UEL Energy Weak-Form Derivation & Source Audit**:
   - Source: `models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for` (SHA-256 `5CD0D2C015C9EAD91C99D7A744156CC86F5B5EA26473BBED7D6E5515FE30FA46`, 901 lines).
   - Mapped all mechanical and phase-field residuals and tangents to their rigorous continuous and discrete Gauss-quadrature energy expressions.
   - Proved the non-existence of a conservative total-energy potential during softening/unloading due to cross-derivative asymmetry ($\mathcal{H} \ge \psi_{\text{pos}}$).
   - Validated non-invasive UEL energy array mappings (`ENERGY(2) = E_elas`, `ENERGY(7) = E_frac`) and companion UMAT Layer 3 output routing (`STATEV(17)` to `STATEV(20)`).

3. **Smallest Meaningful Verification Solve (`PK_M1_MINI_ENERGY_64`)**:
   - Executed on cluster with Abaqus 2023 / Intel Fortran classic.
   - Result: 100% convergence across all 30 increments without cutbacks (`THE ANALYSIS HAS COMPLETED SUCCESSFULLY`).
   - Bit-for-bit energy parity verified:
     - UEL $E_{\text{elas}} = 2.501643\times 10^{-3}\,\text{kN}\cdot\text{mm} \equiv \text{Abaqus ALLSE} = 2.501643\times 10^{-3}\,\text{kN}\cdot\text{mm}$.
     - UEL $E_{\text{int}} = E_{\text{elas}} + E_{\text{frac}} = 2.564881\times 10^{-3}\,\text{kN}\cdot\text{mm} \equiv \text{Abaqus ALLIE} = 2.564881\times 10^{-3}\,\text{kN}\cdot\text{mm}$.
     - External work $W_{\text{ext}} = 2.562345\times 10^{-3}\,\text{kN}\cdot\text{mm} \equiv \text{Abaqus ALLWK} = 2.562345\times 10^{-3}\,\text{kN}\cdot\text{mm}$.
     - Relative energy residual $\eta_E = 0.0989\%$ (negligible discrete integration difference).

---

## 2. Detailed Mathematical Derivation of Implemented UEL Formulation

### A. Mechanical Subproblem (JTYPE = 2, 4)
- **Continuum Formulation**:
  $$\boldsymbol{\sigma} = g(d) \mathbb{C} : \boldsymbol{\varepsilon}, \quad g(d) = (1 - d)^2 + k$$
  where $k = 10^{-7}$, $E = 210\,\text{kN/mm}^2$, $\nu = 0.3$.
- **Elemental Internal Force Vector**:
  $$\boldsymbol{F}_{\text{int}} = \int_{\Omega_e} \boldsymbol{B}^T \boldsymbol{\sigma} \, d\Omega = \sum_{k=1}^{N_{\text{gp}}} w_k \det(\boldsymbol{J}_k) \boldsymbol{B}_k^T [g(d) \mathbb{C} \boldsymbol{B}_k \boldsymbol{u}_e]$$
- **Elemental Tangent Stiffness Matrix**:
  $$\boldsymbol{K}_{\text{mech}} = \frac{\partial \boldsymbol{F}_{\text{int}}}{\partial \boldsymbol{u}_e} = \sum_{k=1}^{N_{\text{gp}}} w_k \det(\boldsymbol{J}_k) \boldsymbol{B}_k^T [g(d) \mathbb{C}] \boldsymbol{B}_k$$
- **Residual**: $\mathtt{RHS} = -\boldsymbol{F}_{\text{int}}$, $\mathtt{AMATRX} = \boldsymbol{K}_{\text{mech}}$.
- **Stored Elastic Strain Energy**:
  $$E_{\text{elas}} = \int_{\Omega_e} \frac{1}{2} \boldsymbol{\sigma} : \boldsymbol{\varepsilon} \, d\Omega = \sum_{k=1}^{N_{\text{gp}}} w_k \det(\boldsymbol{J}_k) \left[ \frac{1}{2} \boldsymbol{\sigma}_k : \boldsymbol{\varepsilon}_k \right]$$
  Under 2D plane strain with implicit unit thickness $B = 1.0\,\text{mm}$, $[E_{\text{elas}}] = \text{kN}\cdot\text{mm} = \text{J}$.

### B. Phase-Field Subproblem (JTYPE = 1, 3)
- **Continuum AT2 Governing Equation**:
  $$G_c \left( \frac{d}{l_0} - l_0 \nabla^2 d \right) = 2 (1 - d) \mathcal{H}(\boldsymbol{x}, t) \quad \text{in } \Omega$$
- **Weak Form**:
  $$\int_\Omega \left[ \left(\frac{G_c}{l_0} d - 2(1-d)\mathcal{H}\right) \delta d + G_c l_0 \nabla d \cdot \nabla(\delta d) \right] d\Omega = 0$$
- **Elemental Tangent & Load Vector**:
  $$\boldsymbol{K}_{\text{phase}} = \sum_{k=1}^{N_{\text{gp}}} w_k \det(\boldsymbol{J}_k) \left[ G_c l_0 \boldsymbol{B}_{d,k}^T \boldsymbol{B}_{d,k} + \left( \frac{G_c}{l_0} + 2 \mathcal{H}_k \right) \boldsymbol{N}_{d,k}^T \boldsymbol{N}_{d,k} \right]$$
  $$\boldsymbol{F}_{\text{phase,load}} = \sum_{k=1}^{N_{\text{gp}}} w_k \det(\boldsymbol{J}_k) \left[ 2 \mathcal{H}_k \boldsymbol{N}_{d,k}^T \right]$$
- **Residual**: $\mathtt{RHS} = \boldsymbol{F}_{\text{phase,load}} - \boldsymbol{K}_{\text{phase}} \boldsymbol{d}_e$, $\mathtt{AMATRX} = \boldsymbol{K}_{\text{phase}}$.
- **AT2 Fracture Surface Energy**:
  $$E_{\text{frac}} = \int_{\Omega_e} G_c \left( \frac{1}{2 l_0} d^2 + \frac{l_0}{2} |\nabla d|^2 \right) d\Omega = \sum_{k=1}^{N_{\text{gp}}} w_k \det(\boldsymbol{J}_k) \left[ G_c \left( \frac{1}{2 l_0} d_k^2 + \frac{l_0}{2} |\nabla d|_k^2 \right) \right]$$

### C. History Variable $\mathcal{H}(t)$ & Non-Conservative Cross-Derivative Analysis
- $\mathcal{H}(\boldsymbol{x}, t) = \max_{\tau \in [0, t]} \psi_{\text{pos}}(\boldsymbol{\varepsilon}(\boldsymbol{x}, \tau))$ is an irreversible history variable, **not** a conserved thermodynamic potential.
- **Cross-Derivative Test**:
  $$\frac{\partial^2 \Pi}{\partial d \, \partial \boldsymbol{u}} = -2(1-d) \mathbb{C} : \boldsymbol{\varepsilon}$$
  $$\frac{\partial^2 \Pi}{\partial \boldsymbol{u} \, \partial d} = -2(1-d) \frac{\partial \mathcal{H}}{\partial \boldsymbol{\varepsilon}} = \begin{cases} -2(1-d) \mathbb{C} : \boldsymbol{\varepsilon} & \text{if } \mathcal{H} = \psi_{\text{pos}} \text{ (monotonic loading)} \\ \mathbf{0} & \text{if } \mathcal{H} > \psi_{\text{pos}} \text{ (softening/unloading)} \end{cases}$$
- **Conclusion**: A conservative discrete potential exists **only** in the purely elastic regime. In the softening regime, irreversibility breaks potentiality, and the discrete energy balance:
  $$\Delta_{\text{book}}(u) = W_{\text{ext}}(u) - [E_{\text{elas}}(u) + E_{\text{frac}}(u)]$$
  must strictly be documented as a discrete bookkeeping difference (`GLOBAL_ENERGY_IDENTITY — NOT_YET_CLOSED`).

---

## 3. Telemetry and Parity Results for `PK_M1_MINI_ENERGY_64`

```
=== FINAL GLOBAL ENERGY BALANCE EVALUATION ===
External Work W_ext:      2.562345e-03 kN*mm
Stored Elastic E_elas:    2.501643e-03 kN*mm
Fracture Surface E_frac:  6.323756e-05 kN*mm
Total Internal Energy:    2.564881e-03 kN*mm
Energy Residual R_E:      -2.535237e-06 kN*mm
Relative Error eta_E:     0.0989 %
Abaqus History ALLSE:     2.501643e-03 kN*mm (100.000% exact parity with E_elas)
Abaqus History ALLWK:     2.562345e-03 kN*mm (100.000% exact parity with W_ext)
Abaqus History ALLIE:     2.564881e-03 kN*mm (100.000% exact parity with E_int)
```

---

## 4. State Variable & Output Map

| Variable | Definition | Routing / Purpose |
| :--- | :--- | :--- |
| `ENERGY(2)` | Elemental stored elastic energy $E_{\text{elas}}$ ($\text{kN}\cdot\text{mm}$) | Abaqus global history `ALLSE` |
| `ENERGY(7)` | Elemental fracture surface energy $E_{\text{frac}}$ ($\text{kN}\cdot\text{mm}$) | Integrated phase-field fracture energy |
| `SVARS(17)` | Whole-element $E_{\text{elas}}$ / $E_{\text{frac}}$ in UEL | UEL state variable tracking |
| `SVARS(18)` | Area-normalized energy density $\psi_e$ / $\psi_f$ ($\text{kN/mm}$) | UEL density tracking |
| `STATEV(17)` | Whole-element $E_{\text{frac}}$ in Companion UMAT | ODB field visualization (Layer 3) |
| `STATEV(18)` | Whole-element $E_{\text{elas}}$ in Companion UMAT | ODB field visualization (Layer 3) |
| `STATEV(19)` | $\psi_f = E_{\text{frac}} / V_{\text{elem}}$ ($\text{kN/mm} = \text{J/mm}^2$) | ODB field visualization (Layer 3) |
| `STATEV(20)` | $\psi_e = E_{\text{elas}} / V_{\text{elem}}$ ($\text{kN/mm} = \text{J/mm}^2$) | ODB field visualization (Layer 3) |
| `UEXTERNALDB` | Summed $E_{\text{elas}}$, $E_{\text{frac}}$, $E_{\text{tot}}$ written at `LOP=2` | `uel_energy_balance.csv` output |
