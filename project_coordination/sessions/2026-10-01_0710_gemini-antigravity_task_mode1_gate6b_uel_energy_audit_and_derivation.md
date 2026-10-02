# Session Report: Gate 6B UEL Energy Formulation, Weak-Form Derivation & Epistemological Audit

**Session ID:** `2026-10-01_0710_gemini-antigravity_task_mode1_gate6b_uel_energy_audit_and_derivation`  
**Agent:** `gemini-antigravity`  
**Date:** `2026-10-01T07:10:00+02:00`  
**Task ID:** `F1101` (`task_mode1_gate6b_uel_energy_audit_and_derivation`)  
**Parent Commit:** `42762382e8e0f4a8fc87b43eb0ddfba06028bcaf`  
**Classification:** `GATE6B_UEL_ENERGY_FORMULATION_AND_WEAK_FORM_AUDIT_QUALIFIED`

---

## 1. Executive Summary & Context

Under the supervisor directive (*"We need to have understood everything related to the first model before we increase complexity"*), this session executed a comprehensive mathematical and source-code audit of the authoritative User Element subroutine `f42_mixed_uel.for` (SHA-256 `5CD0D2C015C9EAD91C99D7A744156CC86F5B5EA26473BBED7D6E5515FE30FA46`, 901 lines) governing the Mode-I benchmark.

In addition, all reproduction and spatial localization findings were epistemologically calibrated:
1. The 13,941-vs-project-mesh reproduction question is strictly preserved as **`SUPERVISOR_ACCEPTED_REPRODUCTION_LIMITATION_CLOSED`**; all explanations for the discrepancy (global error percolation, localized sub-partitioning, fixed boundary edge seeds, error normalization differences) are formally designated as **`UNVERIFIED_HYPOTHESES`**, not established causes.
2. The element size bounds are calibrated to state **bounded compliance** ($99.47\%$ of element edges within $[1.0, 20.0]\,\mu\text{m}$, with minor edge cuts $0.73\text{--}0.99\,\mu\text{m}$ and corner transitions $20.1\text{--}27.4\,\mu\text{m}$ typical of unconstrained free meshing), avoiding absolute claims of "strict enforcement".
3. The authoritative UEL source was mapped line by line to the continuum weak form, deriving exact Gauss-point expressions for stored elastic strain energy, AT2 fracture surface energy, external work, and the global energy balance identity under plane strain unit thickness $B = 1.0\,\text{mm}$.
4. A non-invasive output architecture was verified: exposing `ENERGY(2) = E_elas` ($\to$ `ALLSE`) and `ENERGY(7) = E_frac` in UEL, and `STATEV(17-20)` in companion visualizer Layer 3 without modifying residual `RHS`, stiffness `AMATRX`, constitutive update, or existing `STATEV` semantics, and without double-counting Layer 3 elements ($E_{\mathrm{comp}} = 10^{-11}\,\text{GPa}$).
5. Pre-meeting deliverables were separated into **Verified**, **Derived-but-not-yet-numerically-qualified**, and **Unknown/Open** categories.

---

## 2. Line-by-Line UEL Source Code to Weak-Form Equation Mapping

Authoritative Source: `models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for`

| Continuum Mathematical Term | Equation / Definition | Source Routine & Lines | Fortran Variable / Matrix Name | Numerical Implementation & Status |
| :--- | :--- | :--- | :--- | :--- |
| **Phase Bilinear Operator $a(d, \delta d)$** | $\int_{\Omega} \left[ G_c l_0 \nabla d \cdot \nabla(\delta d) + \left(\frac{G_c}{l_0} + 2\mathcal{H}\right) d \, \delta d \right] \mathrm{d}\Omega$ | `UEL` Lines 335–339 (Quad), Lines 623–627 (Tri) | `AMATRX(I,J)` | Exact Gauss integration: $2 \times 2$ for quads, 1-pt centroid for triangles. |
| **Phase Linear Functional $\ell(\delta d)$** | $\int_{\Omega} 2 \mathcal{H} \, \delta d \, \mathrm{d}\Omega$ | `UEL` Line 340 (Quad), Line 628 (Tri) | `RHS(I,1)` | Exact Gauss integration of history driving source. |
| **Mechanical Internal Force $\mathbf{F}_{\mathrm{int}}$** | $\int_{\Omega} \mathbf{B}^T \boldsymbol{\sigma} \, \mathrm{d}\Omega = \int_{\Omega} g(d) \mathbf{B}^T \mathbb{C}_0 \mathbf{B} \mathbf{u} \, \mathrm{d}\Omega$ | `UEL` Line 495 (Quad), Line 766 (Tri) | `F_INT(I)` | Degraded stress $\boldsymbol{\sigma} = g(\bar{d}_e) \mathbb{C}_0 \boldsymbol{\varepsilon}$. |
| **Mechanical Stiffness Matrix $\mathbf{K}_u$** | $\int_{\Omega} g(d) \mathbf{B}^T \mathbb{C}_0 \mathbf{B} \, \mathrm{d}\Omega$ | `UEL` Lines 500–502 (Quad), Lines 771–773 (Tri) | `AMATRX(I,J)` | Linear-elastic tangent with element-average degradation $g(\bar{d}_e) = (1-\bar{d}_e)^2 + k$. |
| **Stored Elastic Energy Density $\psi_e$** | $\frac{1}{2} \boldsymbol{\sigma} : \boldsymbol{\varepsilon} = \frac{1}{2} g(d) \boldsymbol{\varepsilon} : \mathbb{C}_0 : \boldsymbol{\varepsilon}$ | `UEL` Lines 528–530 (Quad), Lines 799–801 (Tri) | `PSI_E_PT` | Evaluated at each Gauss point; units $\text{kN/mm}^2 = \text{J/mm}^3$ ($B=1\,\text{mm}$). |
| **Integrated Element Elastic Energy $E_{\mathrm{elas}}^e$** | $\int_{\Omega_e} \psi_e \, \mathrm{d}\Omega = \sum_{k=1}^4 \text{CJAC}_k \cdot \psi_{e,k}$ | `UEL` Line 531 (Quad), Line 802 (Tri) | `E_ELAS_ELEM`, `ENERGY(2)`, `SV_E_ELAS` | Units $\text{kN}\cdot\text{mm} = \text{J}$. Routed to `ENERGY(2)` ($\to$ Abaqus `ALLSE`). |
| **AT2 Fracture Surface Energy Density $\psi_f$** | $G_c \left[ \frac{d^2}{2 l_0} + \frac{l_0}{2} |\nabla d|^2 \right]$ | `UEL` Lines 351–352 (Quad), Lines 647–648 (Tri) | `PSI_F_PT` | Evaluated at each Gauss point from shape function derivatives. |
| **Integrated Element Fracture Energy $E_{\mathrm{frac}}^e$** | $\int_{\Omega_e} \psi_f \, \mathrm{d}\Omega = \sum_{k=1}^4 \text{CJAC}_k \cdot \psi_{f,k}$ | `UEL` Line 353 (Quad), Line 649 (Tri) | `E_FRAC_ELEM`, `ENERGY(7)`, `SV_E_FRAC` | Units $\text{kN}\cdot\text{mm} = \text{J}$. Routed to `ENERGY(7)` and `SV_E_FRAC`. |
| **Companion Layer 3 Mapping** | Transfer UEL states to standard visualization | `UMAT` Lines 887–898 | `STATEV(17-20)` | `STATEV(17)=E_frac`, `STATEV(18)=E_elas`, `STATEV(19)=psi_f`, `STATEV(20)=psi_e`. |
| **Global Increment Energy Logging** | $\sum_{e} E_{\mathrm{elas}}^e$, $\sum_e E_{\mathrm{frac}}^e$, $E_{\mathrm{int}} = E_{\mathrm{elas}} + E_{\mathrm{frac}}$ | `UEXTERNALDB` Lines 127–144 | `TOT_E_ELAS`, `TOT_E_FRAC`, `TOT_E_INT` | Appended to `uel_energy_balance.csv` at `LOP=2` (increment acceptance). |

---

## 3. Mathematical Derivation of Global Energy Balance & Discrete Potential Asymmetry

### 3.1 Continuum Energy Balance
For quasi-static loading of a 2D domain $\Omega$ with crack surface $\Gamma$:
$$\dot{W}_{\mathrm{ext}} = \int_{\partial \Omega_t} \bar{\mathbf{t}} \cdot \dot{\mathbf{u}} \, \mathrm{d}\Gamma = \dot{E}_{\mathrm{elas}} + \mathcal{D}_{\mathrm{frac}}$$
where $\mathcal{D}_{\mathrm{frac}}$ is the internal crack dissipation power:
$$\mathcal{D}_{\mathrm{frac}} = \int_{\Omega} \left( -\frac{\partial \psi_e}{\partial d} \dot{d} \right) \mathrm{d}\Omega = \int_{\Omega} 2(1-d) \psi_0^+ \dot{d} \, \mathrm{d}\Omega$$
When the phase field is in energetic equilibrium ($\frac{\delta \psi_f}{\delta d} = 2(1-d)\mathcal{H}$) and monotonically propagating ($\dot{d} > 0, \mathcal{H} = \psi_0^+$), the rate of energy dissipation matches the rate of creation of fracture surface energy:
$$\mathcal{D}_{\mathrm{frac}} = \dot{E}_{\mathrm{frac}} \implies W_{\mathrm{ext}}(u) = E_{\mathrm{elas}}(u) + E_{\mathrm{frac}}(u)$$

### 3.2 Discrete Staggered Asymmetry & Bookkeeping Difference
In the staggered numerical implementation, displacement $\mathbf{u}$ and damage $d$ are solved sequentially in decoupled blocks. The discrete Jacobian is block-triangular during the staggered pass:
$$\frac{\partial^2 \Pi}{\partial \mathbf{u} \, \partial d} \neq \left( \frac{\partial^2 \Pi}{\partial d \, \partial \mathbf{u}} \right)^T$$
This non-commutativity means the discrete incremental trajectory does not strictly conserve a path-independent discrete potential across rapid snap-backs. The resulting two-term bookkeeping difference:
$$\Delta_{\mathrm{book}}(u) \equiv W_{\mathrm{trap}}(u) - \left[ E_{\mathrm{elas}}(u) + E_{\mathrm{frac}}(u) \right]$$
is strictly classified as an **endpoint bookkeeping difference**, governed under **`GLOBAL_ENERGY_IDENTITY — NOT_YET_CLOSED`**.

---

## 4. Rigorous Epistemological Tri-Partition

```
====================================================================================================
CATEGORY 1: VERIFIED / NUMERICALLY QUALIFIED QUANTITIES
====================================================================================================
1. Reference structural stiffness: K_0 = 137.945520 kN/mm (R^2 = 0.99999960, N = 400 increments).
2. Reference baseline response: F_max = 0.757778 kN, u(F_max) = 0.005857 mm (Job 1398090).
3. Pre-peak energy balance: Delta_book < 0.007% across u <= 5.50 um.
4. Mini 64-element exact energy parity: ALLSE = 2.501643 mJ, ALLIE = 2.564881 mJ, ALLWK = 2.562345 mJ (diff = 0.0989%).
5. Spatial energy convergence S1 -> S4 (15k -> 51k elements): Post-peak E_frac = 2.33886 -> 2.37531 mJ (+1.56% variation).
6. Bounded mesh size compliance: 99.47% of element edge lengths within [1.0, 20.0] um.

====================================================================================================
CATEGORY 2: DERIVED-BUT-NOT-YET-NUMERICALLY-QUALIFIED QUANTITIES
====================================================================================================
1. Continuous internal dissipation path integral: D_frac(t) = \int_0^t \int_\Omega 2(1-d) H \dot{d} d\Omega d\tau.
2. Full multi-element production deck energy streaming via ENERGY(2) -> ALLSE and ENERGY(7) -> ALLIE.

====================================================================================================
CATEGORY 3: UNVERIFIED HYPOTHESES / OPEN QUESTIONS (NOT ESTABLISHED CAUSES)
====================================================================================================
1. Cause of 13,941 vs 48,329 element gap: UNVERIFIED HYPOTHESES (localized sub-partition, fixed outer seeds, normalization).
   Status: SUPERVISOR_ACCEPTED_REPRODUCTION_LIMITATION_CLOSED.
2. Origin of post-peak bookkeeping difference (-9.49% on fine meshes): Open discussion item for supervisor review.
   Status: GLOBAL_ENERGY_IDENTITY — NOT_YET_CLOSED.
====================================================================================================
```

---

## 5. Ledger & Coordination Updates

- **`TASK_LEDGER.csv`:** Task `F1101` recorded as `COMPLETED`.
- **`CURRENT_STATE.md`:** Updated with complete weak-form line mapping, energy derivations, and epistemological bounds.
- **`ACTIVE_TASK.json`:** Synced to `MODE1_PRE_MEETING_PACKAGE_COMPLETED_FROZEN_FOR_SUPERVISOR_REVIEW`.
- **`ACTIVE_SESSION.json`:** Released (`active: false`).
- **Cluster Status:** 0 jobs active; pre-meeting package strictly frozen for 01 October 2026 meeting (10:00).
