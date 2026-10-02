# Gate-6B Global Energy Identity: Supervisor Decision Packet
**Target Meeting:** 01 October 2026, 10:00  
**Active Phase:** `MODE1_ENERGY_CONVERGENCE_AND_STATE_TRANSFER_FOUNDATIONS_ACTIVE`  
**Governance State:** `GATE_6B_OPEN` | `GLOBAL_ENERGY_IDENTITY — NOT_YET_CLOSED`  
**Authoritative Subroutine:** `f42_mixed_uel.for` (SHA-256: `5cd0d2c015c9ead91c99d7a744156cc86f5b5ea26473bbed7d6e5515fe30fa46`)

---

## 1. Problem Definition: The Energetic Requirement for Mode-I Phase-Field Fracture

In the numerical modeling of quasi-static brittle fracture via the phase-field approach, the primary supervisor governing directive states:
> *"We need to have understood everything related to the first model before we increase complexity."*

Under Gate 6B, the supervisor explicitly requested meaningful **global energy measures and energy balance**, establishing that peak reaction force ($F_{\mathrm{max}}$) and external work integration alone are insufficient to declare numerical convergence or state-transfer readiness.

The benchmark boundary value problem consists of a $1.0\,\mathrm{mm} \times 1.0\,\mathrm{mm}$ square elastic plate ($\Omega$) with an initial sharp crack of length $a_0 = 0.5\,\mathrm{mm}$ along the symmetry line $y = 0.5\,\mathrm{mm}$. Tensile displacement $u$ is prescribed on the top boundary ($y = 1.0\,\mathrm{mm}$) while the bottom boundary ($y = 0.0\,\mathrm{mm}$) is supported on roller boundary conditions ($u_y = 0$) with a pinned midpoint ($u_x = 0$) to eliminate rigid body modes.

---

## 2. Expected Solution: Continuum Thermodynamic Balance

In continuum mechanics, the first law of thermodynamics for a quasi-static, rate-independent, isothermal brittle fracture process dictates the energy balance:
$$\mathcal{W}_{\mathrm{ext}}(t) = \mathcal{E}_{\mathrm{elas}}(t) + \mathcal{E}_{\mathrm{frac}}(t) + \mathcal{D}_{\mathrm{num}}(t)$$

where:
1. **External Boundary Work:** $\mathcal{W}_{\mathrm{ext}}(t) = \int_0^{u(t)} F(\tilde{u}) \, \mathrm{d}\tilde{u}$.
2. **Elastic Strain Energy:** $\mathcal{E}_{\mathrm{elas}}(t) = \int_{\Omega} \psi_e(\boldsymbol{\varepsilon}, d) \, \mathrm{d}\Omega = \int_{\Omega} \frac{1}{2} \left[(1-d)^2 + k_{\mathrm{res}}\right] \boldsymbol{\varepsilon} : \mathbb{C}_0 : \boldsymbol{\varepsilon} \, \mathrm{d}\Omega$.
3. **Phase-Field Fracture Surface Energy:** $\mathcal{E}_{\mathrm{frac}}(t) = \int_{\Omega} \psi_f(d, \nabla d) \, \mathrm{d}\Omega = \int_{\Omega} G_c \left( \frac{d^2}{2 l_0} + \frac{l_0}{2} |\nabla d|^2 \right) \mathrm{d}\Omega$.
4. **Numerical / Algorithmic Dissipation:** $\mathcal{D}_{\mathrm{num}}(t)$, representing any dissipation introduced by discrete time integration, staggered operator splitting, or irreversibility enforcement.

---

## 3. Reference Implementation: Authoritative Fortran Weak Form (`f42_mixed_uel.for`)

The finite element model contains three co-located layers:
- **Layer 1 (Phase UEL):** 4-node quad (`JTYPE = 1`) or 3-node tri (`JTYPE = 3`) user element solving the phase-field Helmholtz-type equation for nodal damage $d$ (DOF 3).
- **Layer 2 (Mechanical UEL):** 4-node quad (`JTYPE = 2`) or 3-node tri (`JTYPE = 4`) user element solving quasi-static mechanical momentum balance for nodal displacements $\mathbf{u} = (u_x, u_y)$ (DOFs 1, 2).
- **Layer 3 (Companion Visualizer UMAT):** Standard Abaqus continuum elements (`CPE4` / `CPE3`) with dummy visualizer UMAT (`DUMMY_MAT`). These elements invoke `SUBROUTINE UMAT` directly; they are standard Abaqus elements and do **NOT** have a UEL `JTYPE` (`UEL_JTYPE: NOT_APPLICABLE`).

### Three Distinct Energy Quantities in the Implementation:

To prevent conflating local integrands, whole-element energies, and density surrogates, three distinct categories are rigorously defined ([`UEL_UMAT_ENERGY_ARCHITECTURE_AUDIT.csv`](UEL_UMAT_ENERGY_ARCHITECTURE_AUDIT.csv)):

1. **Local Gauss-Point Density Integrands ($\psi_e, \psi_f$):**
   - Degraded elastic energy density integrand inside UEL Gauss loop (`JTYPE = 2`, line 528):
     $$\psi_{e, k} = \frac{1}{2} \boldsymbol{\sigma}_k : \boldsymbol{\varepsilon}_k = \frac{1}{2} \left[(1-d_k)^2 + k_{\mathrm{res}}\right] \boldsymbol{\varepsilon}_k : \mathbb{C}_0 : \boldsymbol{\varepsilon}_k \quad [\mathrm{kN/mm^2} = 1\,\mathrm{J/mm^3} = 1000\,\mathrm{mJ/mm^3}]$$
   - Fracture surface energy density integrand inside UEL Gauss loop (`JTYPE = 1`, line 351):
     $$\psi_{f, k} = G_c \left[ \frac{d_k^2}{2 l_0} + \frac{l_0}{2} \|\nabla d_k\|^2 \right] \quad [\mathrm{kN/mm^2} = 1\,\mathrm{J/mm^3} = 1000\,\mathrm{mJ/mm^3}]$$
2. **Whole-Underlying-Element Integrated Energies ($E_{\mathrm{elas}, e}, E_{\mathrm{frac}, e}$):**
   - Mechanical UEL computes: $E_{\mathrm{elas}, e} = \sum_{k=1}^4 w_k \det(J_k) \psi_{e, k}$ [$\mathrm{mJ} = \mathrm{kN\cdot mm}$], stored in `ENERGY(2)` and shared `SV_E_ELAS(PHYSIDX)`.
   - Phase UEL computes: $E_{\mathrm{frac}, e} = \sum_{k=1}^4 w_k \det(J_k) \psi_{f, k}$ [$\mathrm{mJ} = \mathrm{kN\cdot mm}$], stored in `ENERGY(7)` and shared `SV_E_FRAC(PHYSIDX)`.
   - Companion UMAT receives `STATEV(17) = SV_E_FRAC(PHYSIDX)` and `STATEV(18) = SV_E_ELAS(PHYSIDX)`. These whole-element values are replicated across all 4 companion integration points for visualization.
   - **Global Summation Rule:** The domain total is $E_{\mathrm{elas}} = \sum_{e=1}^{N_{\mathrm{elem}}} E_{\mathrm{elas}, e}$ and $E_{\mathrm{frac}} = \sum_{e=1}^{N_{\mathrm{elem}}} E_{\mathrm{frac}, e}$. When extracting from ODB field outputs `SDV17` and `SDV18`, postprocessors must extract **one integration point per element (e.g. IP1)** to avoid four-fold ($\times 4$) double counting.
3. **Element Volume-Averaged Density Surrogates ($\bar{\psi}_e, \bar{\psi}_f$):**
   - Formed by dividing whole-element energy by element volume: $\bar{\psi}_{e, e} = E_{\mathrm{elas}, e} / V_e$ (`SV_PSI_E` $\to$ `STATEV(20)`) and $\bar{\psi}_{f, e} = E_{\mathrm{frac}, e} / V_e$ (`SV_PSI_F` $\to$ `STATEV(19)`) in $[\mathrm{kN/mm^2} = 1\,\mathrm{J/mm^3} = 1000\,\mathrm{mJ/mm^3}]$ (under unit thickness $B = 1.0\,\mathrm{mm}$).

### Source-Verified Material & Model Parameters:
- **Residual Stiffness Parameter:** $k_{\mathrm{res}} = 1.0 \times 10^{-7}$ (source-verified from `PROPS(5) = 1.0e-7` in input decks, `E_K = PROPS(5)` in UEL line 210, and UMAT line 891 `+ 1.D-7`; prior draft mentions of $1.0 \times 10^{-6}$ are superseded).
- **Specimen Thickness:** Unit thickness $B = 1.0\,\mathrm{mm}$ (plane strain assumption; matches companion CPE4 `*Solid Section` card).
- **Elasticity Parameters:** $E = 210.0\,\mathrm{kN/mm^2} = 210.0\,\mathrm{GPa}$, $\nu = 0.3$ (source-verified from `PROPS(3)` and `PROPS(4)`).
- **Fracture Properties:** $G_c = 0.0027\,\mathrm{kN/mm} = 2.7\,\mathrm{N/mm}$ (`PROPS(2)`), $l_0 = 0.0075\,\mathrm{mm} = 7.5\,\mu\mathrm{m}$ for nominal $S_3$ (`PROPS(1)`).

### Derived Two-Term Bookkeeping Difference ($\mathcal{R}_{\mathrm{book}}$):
$$\mathcal{R}_{\mathrm{book}} \equiv W_{\mathrm{trap}} - (E_{\mathrm{elas}} + E_{\mathrm{frac}})$$
- Evaluated purely at discrete increment endpoints from post-processed solver outputs.
- Staggered operator splitting solves $\mathbf{u}$ and $d$ in decoupled alternating sub-steps. Because cross-derivatives do not commute ($\frac{\partial^2 \Pi}{\partial \mathbf{u} \partial d} \ne \frac{\partial^2 \Pi}{\partial d \partial \mathbf{u}}$), no single discrete scalar potential exists governing the joint update.

---

## 4. Applied Observable Quantities & Epistemic Classification Ledger

To maintain strict scientific epistemology, every energetic and structural metric is classified into one of three tiers ([`GLOBAL_ENERGY_IDENTITY_EVIDENCE_LEDGER.csv`](GLOBAL_ENERGY_IDENTITY_EVIDENCE_LEDGER.csv)):

```
+----------------------------------------------------------------------------------------------------+
|                                    EPISTEMIC CLASSIFICATION SYSTEM                                 |
+----------------------------------------------------------------------------------------------------+
| LEVEL 1: SOURCE-DEFINED / VERIFIED FROM IMPLEMENTATION                                             |
| - Quantities directly integrated at Gauss points in Fortran UEL source and stored deterministically.|
|   Examples: E_elas (ENERGY(2), STATEV18 IP1), E_frac (ENERGY(7), STATEV17 IP1),                    |
|   k_res = 1.0e-7, B = 1.0 mm, AT2 profile alpha(d)=d^2, g(d)=(1-d)^2+k_res.                        |
+----------------------------------------------------------------------------------------------------+
| LEVEL 2: DERIVED / VERIFIED ANALYTICALLY OR NUMERICALLY                                            |
| - Quantities computed from converged solver outputs via post-processing; reproducible across runs. |
|   Examples: W_trap, R_book, observed pre-peak two-term endpoint equality (|R_book| <= 0.008%),     |
|   crack centroid path y_c(x), exact-plane localization width w_0.5 = 22.974 +- 0.212 um.          |
+----------------------------------------------------------------------------------------------------+
| LEVEL 3: NOT PROVEN / MUST NOT BE CLAIMED                                                          |
| - Claims not observable from standard uninstrumented ODB files; unverified mechanisms.             |
|   Examples: Exact continuous identity closure Delta R_closed = 0, snap-through onset attribution,  |
|   sub-increment operator dissipation breakdown without subiteration logging.                       |
+----------------------------------------------------------------------------------------------------+
```

### Complete 16-Claim Classification Summary:

| Claim ID | Metric / Quantity | Epistemic Classification | Source / Governing Basis | Defensible Status |
| :--- | :--- | :--- | :--- | :--- |
| **CLAIM-01** | Stored Elastic Strain Energy $E_{\mathrm{elas}}$ | Level 1: SOURCE-DEFINED | `f42_mixed_uel.for` (`JTYPE=2`, `ENERGY(2)`, `SV_E_ELAS`, companion `STATEV(18)` IP1) | **`SOURCE-DEFINED`** |
| **CLAIM-02** | Fracture Surface Energy $E_{\mathrm{frac}}$ | Level 1: SOURCE-DEFINED | `f42_mixed_uel.for` (`JTYPE=1`, `ENERGY(7)`, `SV_E_FRAC`, companion `STATEV(17)` IP1) | **`SOURCE-DEFINED`** |
| **CLAIM-03** | AT2 Degradation and Crack Surface Functionals | Level 1: SOURCE-DEFINED | $\alpha(d)=d^2$, $g(d)=(1-d)^2+k_{\mathrm{res}}$, $k_{\mathrm{res}} = 1.0\times 10^{-7}$ (`PROPS(5)`) | **`SOURCE-DEFINED`** |
| **CLAIM-04** | Plate Specimen Thickness Convention | Level 1: SOURCE-DEFINED | Unit thickness $B = 1.0\,\mathrm{mm}$ (plane strain, Solid Section card) | **`SOURCE-DEFINED`** |
| **CLAIM-05** | External Boundary Work $W_{\mathrm{trap}}$ | Level 2: DERIVED | Discrete trapezoidal integration: $W_{\mathrm{trap}} = \sum \frac{1}{2}(F_i+F_{i-1})\Delta u_i$ | **`NUMERICALLY VERIFIED`** |
| **CLAIM-06** | Two-Term Bookkeeping Difference $\mathcal{R}_{\mathrm{book}}$ | Level 2: DERIVED | Algebraic endpoint difference: $\mathcal{R}_{\mathrm{book}} \equiv W_{\mathrm{trap}} - (E_{\mathrm{elas}} + E_{\mathrm{frac}})$ | **`NUMERICALLY VERIFIED`** |
| **CLAIM-07** | Pre-Peak Two-Term Endpoint Equality | Level 2: DERIVED | Exact same-frame extraction: $|\mathcal{R}_{\mathrm{book}}| \le 0.008\%$ for $u \le 5.856\,\mu\mathrm{m}$ | **`NUMERICALLY VERIFIED`** |
| **CLAIM-08** | Crack Centroid Path Trajectory $y_c(x)$ | Level 2: DERIVED | Damage-weighted centroid $\max |y_c - 0.5\,\mathrm{mm}| \le 3.10\,\mu\mathrm{m}$ across all meshes | **`CONVERGED / STABLE`** |
| **CLAIM-09** | Authoritative Exact-Plane Localization Width $w_{0.5}$ | Level 2: DERIVED | 2D continuous linear interpolation: $w_{d=0.5} = 22.974 \pm 0.212\,\mu\mathrm{m}$ ($\pm 0.92\%$) | **`STABLE ON REFINED SET`** |
| **CLAIM-10** | Initial Structural Stiffness $K_0$ | Level 2: DERIVED | 400-point OLS regression: $K_0 = 137.945520\,\mathrm{kN/mm}$ ($R^2 = 0.99999960$) | **`NUMERICALLY VERIFIED`** |
| **CLAIM-11** | Closed Continuous Energy Identity $\Delta \mathcal{R}_{\mathrm{closed}} = 0$ | Level 3: NOT PROVEN | Continuous path conservation is unestablished for staggered split in standard ODB | **`NOT YET CLOSED`** |
| **CLAIM-12** | Snap-Through Onset Mechanism Attribution | Level 3: NOT PROVEN | Quasi-static implicit solver; dynamic inertia / snap-through is unverified | **`NOT PROVEN`** |
| **CLAIM-13** | Mechanistic Decomposition of $\mathcal{R}_{\mathrm{book}}$ | Level 3: NOT PROVEN | Sub-increment Newton iteration states and dissipation are unpersisted | **`NOT PROVEN`** |
| **CLAIM-14** | Pre-Peak Damage Extrema Asymptotic Convergence | Level 3: NOT PROVEN | $d_{\max}$ increases monotonically with refinement due to notch singularity | **`MESH-SENSITIVE`** |
| **CLAIM-15** | Authentic Nodal Phase-Field Extraction ($q_d$) | Level 3: NOT PROVEN | True UEL DOF 3 not exported directly to ODB nodal blocks; companion used | **`NOT PERSISTED`** |
| **CLAIM-16** | Universal Spatial Convergence of Core Zone ($w_{0.9}$) | Level 3: NOT PROVEN | Core zone ($d \ge 0.9$) exhibits sensitivity to discrete element spacing | **`MESH-SENSITIVE`** |

---

## 5. Authoritative Evidence Chain Table

| Simulation Case | Job ID | Mesh Details | Peak Force $F_{\mathrm{max}}$ | Work $W_{\mathrm{trap}}$ at Peak | $E_{\mathrm{frac}}$ at Terminal | $\mathcal{R}_{\mathrm{book}}$ Endpoint Observation | Governance Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **$S_1$ Nominal Baseline** | `1406015` | 15,192 CPE4 ($h/l_0 = 0.400$) | $0.7578\,\mathrm{kN}$ | $2.3019\,\mathrm{mJ}$ | $2.3402\,\mathrm{mJ}$ ($u=10.0\,\mu\mathrm{m}$) | $|\mathcal{R}_{\mathrm{book}}| \le 0.008\%$ pre-peak; $+0.76\%$ at subterminal | Qualified Baseline |
| **$S_1$ Diagnostic Twin** | `1406839` | 15,192 CPE4 (Unit 105) | $0.7578\,\mathrm{kN}$ | $2.3019\,\mathrm{mJ}$ | $2.3402\,\mathrm{mJ}$ ($|\Delta E| < 1.4\times 10^{-6}$) | Matches ODB bit-for-bit | Diagnostic Parity Pass |
| **$S_3$ Fine Mesh Anchor** | `1406017` | 41,912 CPE4 ($h/l_0 = 0.200$) | $0.7188\,\mathrm{kN}$ | $2.1896\,\mathrm{mJ}$ | $2.3572\,\mathrm{mJ}$ ($u=7.836\,\mu\mathrm{m}$) | $-7.65\%$ at cutback termination | Authoritative Raw Anchor |
| **$T_1$ Coarse Time Step** | `1406020` | $\Delta u = 1.0\times 10^{-5}\,\mathrm{mm}$ | $0.7579\,\mathrm{kN}$ | $2.3016\,\mathrm{mJ}$ | $2.3384\,\mathrm{mJ}$ ($u=10.0\,\mu\mathrm{m}$) | $+0.38\%$ at $u=9.398\,\mu\mathrm{m}$ | Temporal Series |
| **$T_2$ Nominal Time Step** | `1406015` | $\Delta u = 5.0\times 10^{-6}\,\mathrm{mm}$ | $0.7578\,\mathrm{kN}$ | $2.3019\,\mathrm{mJ}$ | $2.3402\,\mathrm{mJ}$ ($u=10.0\,\mu\mathrm{m}$) | $+0.76\%$ at $u=9.398\,\mu\mathrm{m}$ | Temporal Series |
| **$T_3$ Fine Time Step** | `1406021` | $\Delta u = 2.5\times 10^{-6}\,\mathrm{mm}$ | $0.7578\,\mathrm{kN}$ | $2.3020\,\mathrm{mJ}$ | $2.3411\,\mathrm{mJ}$ ($u=10.0\,\mu\mathrm{m}$) | $+3.54\%$ at $u=9.398\,\mu\mathrm{m}$ | Temporal Series |

---

## 6. What Is and Is Not Knowable from Current Solver Output

### What IS Knowable:
1. Exact converged equilibrium states $(\mathbf{u}^{n+1}, d^{n+1})$ at completed increment endpoints.
2. Endpoint external work $W_{\mathrm{trap}}$, whole-element elastic strain energy $E_{\mathrm{elas}}$, and whole-element fracture surface energy $E_{\mathrm{frac}}$.
3. Observed pre-peak two-term endpoint equality ($|\mathcal{R}_{\mathrm{book}}| \le 0.008\%$) across all time discretizations ($T_1, T_2, T_3$).
4. Structural response invariance: initial stiffness $K_0 = 137.95\,\mathrm{kN/mm}$ and crack path symmetry $|y_c - 0.5\,\mathrm{mm}| \le 3.10\,\mu\mathrm{m}$.
5. Regularized localization band width stability ($w_{d=0.5} = 22.974 \pm 0.212\,\mu\mathrm{m}$, $\pm 0.92\%$) across refined meshes ($S_3, S_4, A_1, A_2$).

### What IS NOT Knowable (Without Custom Within-Increment Instrumentation):
1. The continuous sub-increment equilibrium trajectory $\mathbf{u}(\tau)$ between increments.
2. Newton subiteration work and operator dissipation generated by the staggered split within an increment.
3. The exact numerical dissipation contribution associated with the history-variable irreversibility threshold ($H_n$).
4. The isolated mechanistic breakdown of the post-peak bookkeeping difference $\mathcal{R}_{\mathrm{book}}$.

---

## 7. Supervisor Decision Required (01 October 2026 Meeting)

The supervisor is presented with a clear, defensible decision regarding Gate-6B closure and the boundary for subsequent phases:

```
+----------------------------------------------------------------------------------------------------+
|                                    SUPERVISOR DECISION TREE                                        |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|  +----------------------------------------------------+  +---------------------------------------+ |
|  | PATH A: ACCEPT PRESENT QUALIFICATION & LIMITATIONS |  | PATH B: MANDATE FUTURE WITHIN-STEP    | |
|  |                                                    |  |         ENERGY INSTRUMENTATION /      | |
|  |                                                    |  |         ALGORITHMIC REFORMULATION     | |
|  +----------------------------------------------------+  +---------------------------------------+ |
|  | - Accept Gate-6B qualification under documented   |  | - Mandate dedicated within-increment  | |
|  |   epistemic status: pre-peak two-term endpoint     |  |   operator-path instrumentation and/  | |
|  |   equality verified (<= 0.008%), post-peak book   |  |   or algorithmic reformulation.       | |
|  |   difference tracked as derived quantity.          |  | - Subroutine modifications, output    | |
|  | - Maintain GLOBAL_ENERGY_IDENTITY as NOT_YET_     |  |   variable design, rerun scope, and   | |
|  |   CLOSED for staggered standard ODB output.        |  |   effort to be determined after a     | |
|  | - Keep Gate 6C / Mode-II / Transfer on HOLD until |  |   separate derivation & code review.  | |
|  |   explicit supervisor authorization.               |  | - Postpone subsequent thesis phases.  | |
|  +----------------------------------------------------+  +---------------------------------------+ |
+----------------------------------------------------------------------------------------------------+
```

- **Pathway A:** Accept the present observable endpoint energetic qualification with its documented epistemic boundaries. Acknowledge that standard uninstrumented ODB files provide observed pre-peak two-term endpoint equality ($|\mathcal{R}_{\mathrm{book}}| \le 0.008\%$) while post-peak differences reflect unpersisted staggered operator dissipation. Proceed to Mode-I state transfer evaluation under explicitly documented energy boundaries.
- **Pathway B:** If an exact algorithmic closed energy identity is strictly required, future work would need dedicated within-increment/operator-path instrumentation and/or algorithmic reformulation, with the exact design, output variables, rerun scope, and effort to be determined after a separate derivation and code review.

**Governance Commitment:** The decision between Pathway A and Pathway B rests entirely with the supervisor. The project maintains `GATE_6B_OPEN` and `GLOBAL_ENERGY_IDENTITY — NOT_YET_CLOSED` pending supervisor directive at the 01 October 2026 meeting.
