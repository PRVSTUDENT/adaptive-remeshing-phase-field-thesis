# Mode-I Gate-6B: Authoritative Equation-to-Code-to-Output Map and Energy Bookkeeping Specification

**Document Version:** 2.3 (Two-Tier Dimensional Framework & Thickness Provenance Reconciled)  
**Date:** 02 October 2026  
**Governing Subroutine Source:** `models/pandey_kumar_mode1/reproduction_package_gate6b_energy/f42_mixed_uel.for` (SHA-256 `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`)  
**Governing Extractor:** `extract_authoritative_mode1_energy_complete.py` (SHA-256 `9270C0F2DC77F84799E2B6435E2D5BCB4FF693204A08EF76BD815D6414332E8A`)  
**Parent Commit:** `42762382e8e0f4a8fc87b43eb0ddfba06028bcaf`  
**Governing Directive:** *"We need to have understood everything related to the first model before we increase complexity."*

---

## 1. Executive Summary & Epistemological Boundaries

This document establishes the canonical mathematical formulations, Fortran 77 implementation details, state-variable assignments, ODB/CSV data channels, unit systems, and reduction rules governing energetic bookkeeping for the Mode-I crack propagation benchmark (Pandey & Kumar, 2025).

### Epistemological Distinctions & Dimensional Rigor

1. **Phase-Field Surface Energy vs. Dissipated Energy:**  
   $E_{\text{frac}}$ represents the *regularized crack surface energy functional* $\Gamma_d(d) = \int_\Omega G_c \left[ \frac{d^2}{2l_0} + \frac{l_0}{2} |\nabla d|^2 \right] d\Omega$. Under damage irreversibility ($\dot{d} \ge 0$), it acts as the phase-field proxy for accumulated surface energy. It must **never** be conflated with viscous dissipation, plastic dissipation, or thermal losses.

2. **Local Volumetric Densities vs. Integrated Energies in the $\text{kN}-\text{mm}$ System:**  
   - In the adopted $\text{kN}-\text{mm}$ consistent unit system:
     * Stress and volumetric energy density have dimensions $\text{kN/mm}^2$.
     * Numerically, $1\,\text{kN/mm}^2 = 10^3\,\text{N}/(10^{-3}\,\text{m})^2 = 10^9\,\text{N/m}^2 = 10^9\,\text{Pa} = 1000\,\text{MPa} = 1\,\text{GPa}$ (**not** $1\,\text{MPa}$).
     * Volumetric energy density equivalence: $1\,\text{kN/mm}^2 = 1\,(\text{kN}\cdot\text{mm})/\text{mm}^3 \equiv 1\,\text{J/mm}^3 = 10^3\,\text{mJ/mm}^3 = 10^9\,\text{J/m}^3$ (**not** $\text{J/mm}^2$, which is surface energy density).
     * Fracture toughness / critical energy release rate: $G_c = 0.0027\,\text{kN/mm} = 2.7\,\text{N/mm} = 2700\,\text{N/m} = 2700\,\text{J/m}^2 = 0.0027\,\text{J/mm}^2 = 2.7\times 10^{-3}\,\text{J/mm}^2$ (**not** $2.7\,\text{J/mm}^2$).
   - $\psi_f$ ($\text{SDV19}$) and $\psi_e$ ($\text{SDV20}$) are **local volumetric energy densities** with dimensions $\text{kN/mm}^2 \equiv \text{GPa} = 1000\,\text{MPa} \equiv \text{J/mm}^3 = 10^3\,\text{mJ/mm}^3$.
   - $E_{\text{frac}}$ ($\text{SDV17}$) and $E_{\text{elas}}$ ($\text{SDV18}$) are **element-integrated scalar energies** for the physical out-of-plane thickness $t = 1.0\,\text{mm}$, with dimensions $\text{kN}\cdot\text{mm} \equiv \text{J} = 10^3\,\text{mJ}$.
   - **Crucial Semantic Distinction**: $\text{SDV17}$ and $\text{SDV18}$ are whole-element integrated energies, whereas $\text{SDV19}$ and $\text{SDV20}$ are local pointwise densities. Summing $\psi_f$ or $\psi_e$ directly across finite elements without volume integration produces severe dimensional error and unphysical numerical inflation.

3. **Source-Level Unit-Thickness Normalization & Two-Tier Dimensional Framework:**
   - **Tier 1 (Native 2D UEL Assembly):**
     In `f42_mixed_uel.for`, the UEL integrates over in-plane area $\text{CJAC} = \det(J) \cdot \text{WT} \sim \text{mm}^2$. There is **no explicit thickness multiplier anywhere in the UEL**.
     Consequently:
     * The raw mechanical residual is natively a force per unit thickness: $F_{\text{raw}} = \int_A B^T \sigma \, dA \sim (\text{mm}^2) \cdot (1/\text{mm}) \cdot (\text{kN/mm}^2) = \text{kN/mm}$.
     * The raw integrated energies are natively energies per unit thickness: $E_{\text{raw}} = \int_A \psi \, dA \sim (\text{mm}^2) \cdot (\text{kN/mm}^2) = \text{kN} \equiv (\text{kN}\cdot\text{mm})/\text{mm} \equiv \text{J/mm}$.
     Both mechanical residual and energy integrals share the exact same 2D area quadrature without thickness scaling, proving 100% internal mathematical consistency at the source level.
   - **Tier 2 (Project Implementation Convention $t_{\text{ref}} = 1.0\,\text{mm}$):**
     Pandey & Kumar (2025) Section 4.1 formulate the Mode-I benchmark strictly as a 2D problem without prescribing an out-of-plane thickness $t$.
     To convert native per-unit-thickness 2D quantities into reported resultant tensile force and total scalar energy, the project adopts the standardized unit slice convention $t_{\text{ref}} \equiv 1.0\,\text{mm}$.
     Multiplying by $t_{\text{ref}}$ maps native per-unit-thickness quantities to resultant force and total scalar energy:
     * Resultant applied force: $F = F_{\text{raw}} \cdot t_{\text{ref}} = (\text{kN/mm}) \cdot (1.0\,\text{mm}) = \text{kN}$.
     * Total external work: $W_{\text{ext}} = \int F \, du = W_{\text{ext, raw}} \cdot t_{\text{ref}} = \text{kN}\cdot\text{mm} \equiv \text{J} = 1000\,\text{mJ}$.
     * Total internal energy: $E_{\text{model}} = (E_{\text{elas, raw}} + E_{\text{frac, raw}}) \cdot t_{\text{ref}} = \text{kN}\cdot\text{mm} \equiv \text{J} = 1000\,\text{mJ}$.
     * Bookkeeping residual: $\Delta_{\text{book}} = E_{\text{model}} - W_{\text{ext}} = \Delta_{\text{book, raw}} \cdot t_{\text{ref}} = \text{kN}\cdot\text{mm} \equiv \text{J}$.
   - **Numerical Invariance:** Because $t_{\text{ref}} = 1.0\,\text{mm}$ has magnitude $1.0$, numerical floating-point values are identically preserved, while the physical dimensional interpretation is rigorously established.

4. **Bookkeeping Residual as a Diagnostic Metric:**  
   The bookkeeping difference $\Delta_{\text{book}} = E_{\text{model}} - W_{\text{ext}} = (E_{\text{elas}} + E_{\text{frac}}) - W_{\text{ext}}$ is a **trend-only diagnostic quantity** that measures spatial discretization error, numerical integration approximations, and temporal cutback effects. It is **not** an exact thermodynamic conservation law or a hard solver convergence prerequisite.

---

## 2. Mathematical Formulations & Physical Definitions

### 2.1 Degraded Elastic Strain Energy ($E_{\text{elas}}$)
The degraded elastic strain energy over the domain $\Omega$ is defined by:
$$E_{\text{elas}} = \int_\Omega \psi_e(\boldsymbol{\varepsilon}, d) \, d\Omega = \int_A \frac{1}{2} g(d) \boldsymbol{\varepsilon} : \mathbf{C} : \boldsymbol{\varepsilon} \cdot t \, dA$$
where:
- $\boldsymbol{\varepsilon} = \frac{1}{2}(\nabla \mathbf{u} + (\nabla \mathbf{u})^T)$ is the infinitesimal strain tensor.
- $\mathbf{C}$ is the 4th-order isotropic plane-strain elasticity tensor defined by Young's modulus $E = 210.0\,\text{kN/mm}^2$ ($210\,\text{GPa} = 210{,}000\,\text{MPa}$) and Poisson's ratio $\nu = 0.3$.
- $g(d) = (1-d)^2 + k$ is the quadratic degradation function with residual stiffness parameter $k = 10^{-7}$.
- $t = 1.0\,\text{mm}$ is the out-of-plane unit thickness.
- Dimension of local density $\psi_e$: $[\text{Stress}] = \text{kN/mm}^2 \equiv \text{GPa} = 1000\,\text{MPa} \equiv \text{J/mm}^3 = 10^3\,\text{mJ/mm}^3$.
- Dimension of integrated energy $E_{\text{elas}}$: $[ \text{Force} ] \times [ \text{Length} ] = \text{kN}\cdot\text{mm} \equiv \text{J} = 10^3\,\text{mJ}$.

### 2.2 Phase-Field / Fracture Surface Energy ($E_{\text{frac}}$)
The regularized crack surface energy over the domain $\Omega$ is defined by:
$$E_{\text{frac}} = \int_\Omega \psi_f(d, \nabla d) \, d\Omega = \int_A G_c \left[ \frac{d^2}{2l_0} + \frac{l_0}{2} |\nabla d|^2 \right] \cdot t \, dA$$
where:
- $G_c = 0.0027\,\text{kN/mm} = 2.7\,\text{N/mm} = 2700\,\text{N/m} = 2700\,\text{J/m}^2 = 0.0027\,\text{J/mm}^2 = 2.7\times 10^{-3}\,\text{J/mm}^2$ is the critical fracture energy release rate (surface energy per unit crack area).
- $l_0 = 0.0075\,\text{mm} = 7.5\,\mu\text{m}$ is the phase-field regularization length scale.
- $d \in [0, 1]$ is the scalar phase field ($d = 0$ intact, $d = 1$ broken).
- $\nabla d = \left( \frac{\partial d}{\partial x}, \frac{\partial d}{\partial y} \right)^T$ is the spatial gradient of the phase field (dimension $1/\text{mm}$, with $|\nabla d|^2$ having dimension $1/\text{mm}^2$).
- Dimensional analysis of local density $\psi_f$:
  $$[\psi_f] = [G_c] \times \left[ \frac{1}{l_0} \right] = \left(\frac{\text{kN}}{\text{mm}}\right) \times \left(\frac{1}{\text{mm}}\right) = \frac{\text{kN}}{\text{mm}^2} \equiv \frac{\text{kN}\cdot\text{mm}}{\text{mm}^3} = \frac{\text{J}}{\text{mm}^3} = 10^3\,\frac{\text{mJ}}{\text{mm}^3} = 1000\,\text{MPa} = 1\,\text{GPa}$$
- Dimension of integrated energy $E_{\text{frac}}$: $[ \text{Force} ] \times [ \text{Length} ] = \text{kN}\cdot\text{mm} \equiv \text{J} = 10^3\,\text{mJ}$.

### 2.3 Total Internal Model Energy ($E_{\text{model}}$)
$$E_{\text{model}} = E_{\text{elas}} + E_{\text{frac}}$$
Dimension: $\text{kN}\cdot\text{mm} \equiv \text{J} = 1000\,\text{mJ}$.

### 2.4 Cumulative External Work ($W_{\text{ext}}$)
For Mode-I monotonic tensile displacement loading applied at the Reference Point (RP 999999) along the $+y$ axis:
$$W_{\text{ext}}(u) = \int_0^u F(\tilde{u}) \, d\tilde{u}$$
where:
- $u = \text{U2}_{\text{RP}} \ge 0$ is the prescribed vertical displacement ($\text{mm}$).
- $F = -\text{RF2}_{\text{RP}} \ge 0$ is the conjugate vertical reaction force across the $1.0\,\text{mm}$ thickness slice ($\text{kN}$). (Abaqus reports negative reaction forces for restrained tensile boundaries; physical load on the specimen is positive).
- Evaluated incrementally via the composite trapezoidal rule:
  $$W_{\text{ext}}(u_k) = \sum_{i=1}^k \frac{1}{2}(F_i + F_{i-1})(u_i - u_{i-1})$$
- Dimension: $[ \text{Force} ] \times [ \text{Length} ] = \text{kN}\cdot\text{mm} \equiv \text{J} = 10^3\,\text{mJ}$.

### 2.5 Energy Bookkeeping Residuals
- **Signed Bookkeeping Difference:**
  $$\Delta_{\text{book}}(u) = E_{\text{model}}(u) - W_{\text{ext}}(u) = \left( E_{\text{elas}}(u) + E_{\text{frac}}(u) \right) - W_{\text{ext}}(u)$$
- **Signed Relative Discrepancy (%):**
  $$\delta_{\text{book}}(u) = \frac{\Delta_{\text{book}}(u)}{\max\left(|W_{\text{ext}}(u)|, 10^{-12}\right)} \times 100\%$$
- **Absolute Normalized Error (%):**
  $$\varepsilon_{\text{book}}(u) = \frac{|\Delta_{\text{book}}(u)|}{\max\left(|W_{\text{ext}}(u)|, |E_{\text{model}}(u)|, 10^{-12}\right)} \times 100\%$$

---

## 3. Authoritative Equation-to-Code-to-Output Map

| Mathematical Quantity | Mathematical Formulation | Subroutine & Line Numbers | Fortran Variable | State Array / Layer | ODB Field & Set | CSV Column (`uel_energy_balance.csv`) | Density vs Integrated | Native Unit & Conversion | Reduction / Deduplication Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Fracture Surface Energy** ($E_{\text{frac}}$) | $\int_A G_c \left[ \frac{d^2}{2l_0} + \frac{l_0}{2}\|\nabla d\|^2 \right] t \, dA$ | `f42_mixed_uel.for`<br>Lines 357–373 (Quad)<br>Lines 645–659 (Tri) | `E_FRAC_ELEM`<br>`SV_E_FRAC(PHYSIDX)` | Layer 3 Companion:<br>`STATEV(17)` | `SDV17` on `All_elem` (Layer 3) | `E_fracture_kNmm` | **Element-Integrated Scalar Energy** ($t=1\,\text{mm}$) | $\text{kN}\cdot\text{mm} \equiv \text{J}$<br>($\times 1000 \to \text{mJ}$) | Single-IP1 or unique element deduplication ($\sum_{e=1}^{N_{\text{phys}}} E_{\text{frac}, e}$) |
| **Elastic Strain Energy** ($E_{\text{elas}}$) | $\int_A \frac{1}{2} g(d) \boldsymbol{\varepsilon} : \mathbf{C} : \boldsymbol{\varepsilon} \, t \, dA$ | `f42_mixed_uel.for`<br>Lines 534–549 (Quad)<br>Lines 806–816 (Tri) | `E_ELAS_ELEM`<br>`SV_E_ELAS(PHYSIDX)` | Layer 3 Companion:<br>`STATEV(18)` | `SDV18` on `All_elem` (Layer 3) | `E_elastic_kNmm` | **Element-Integrated Scalar Energy** ($t=1\,\text{mm}$) | $\text{kN}\cdot\text{mm} \equiv \text{J}$<br>($\times 1000 \to \text{mJ}$) | Single-IP1 or unique element deduplication ($\sum_{e=1}^{N_{\text{phys}}} E_{\text{elas}, e}$) |
| **Fracture Energy Density** ($\psi_f$) | $G_c \left[ \frac{d^2}{2l_0} + \frac{l_0}{2}\|\nabla d\|^2 \right]$ | `f42_mixed_uel.for`<br>Lines 375, 661 | `SV_PSI_F(PHYSIDX)` | Layer 3 Companion:<br>`STATEV(19)` | `SDV19` on `All_elem` (Layer 3) | *(Not in global CSV)* | **Local Volumetric Density** | $\text{kN/mm}^2 \equiv \text{GPa} = 1000\,\text{MPa} \equiv \text{J/mm}^3$ | Pointwise field variable; **NEVER SUM DIRECTLY** |
| **Elastic Energy Density** ($\psi_e$) | $\frac{1}{2} g(d) \boldsymbol{\varepsilon} : \mathbf{C} : \boldsymbol{\varepsilon}$ | `f42_mixed_uel.for`<br>Lines 551, 818 | `SV_PSI_E(PHYSIDX)` | Layer 3 Companion:<br>`STATEV(20)` | `SDV20` on `All_elem` (Layer 3) | *(Not in global CSV)* | **Local Volumetric Density** | $\text{kN/mm}^2 \equiv \text{GPa} = 1000\,\text{MPa} \equiv \text{J/mm}^3$ | Pointwise field variable; **NEVER SUM DIRECTLY** |
| **Total Internal Model Energy** ($E_{\text{model}}$) | $E_{\text{elas}} + E_{\text{frac}}$ | `UEXTERNALDB`<br>Line 137 | `TOT_E_INT` | Global Reduction | Derived: `SDV17 + SDV18` | `E_total_kNmm` | **Domain-Integrated Scalar Energy** ($t=1\,\text{mm}$) | $\text{kN}\cdot\text{mm} \equiv \text{J}$<br>($\times 1000 \to \text{mJ}$) | Global sum over $1 \dots N_{\text{phys}}$ |
| **External Work** ($W_{\text{ext}}$) | $\int_0^u -\text{RF2}_{\text{RP}} \, du$ | Extractor script<br>Lines 124–130 | `w_cum` | ODB Assembly History | Derived from `U` & `RF` at RP node (999999) | *(Derived in postprocessing)* | **Cumulative Boundary Work** ($t=1\,\text{mm}$) | $\text{kN}\cdot\text{mm} \equiv \text{J}$<br>($\times 1000 \to \text{mJ}$) | Composite trapezoidal integration over time history |
| **Bookkeeping Residual** ($\Delta_{\text{book}}$) | $E_{\text{model}} - W_{\text{ext}}$ | Extractor script<br>Line 167 | `delta_book` | Postprocessed Diagnostic | Derived: $E_{\text{model}} - W_{\text{ext}}$ | *(Diagnostic output)* | **Scalar Energy Discrepancy** | $\text{kN}\cdot\text{mm} \equiv \text{J}$<br>($\times 1000 \to \text{mJ}$) | Point-by-point subtraction along displacement path |

---

## 4. Multi-Layer Finite-Element Architecture & Zero Double-Counting Proof

### 4.1 Co-Located 3-Layer Finite Element Structure
The Mode-I discretization comprises three co-located element layers sharing identical node coordinates:
1. **Layer 1 (Phase-Field UEL, Elements $1 \dots N_{\text{phys}}$):**
   - User elements (`JTYPE=1` quad, `JTYPE=3` tri).
   - Solves active Degree of Freedom 3 (phase-field $d$).
   - Computes element fracture energy $E_{\text{frac}, e}$ and stores it in common block `SV_E_FRAC(PHYSIDX)`.
2. **Layer 2 (Mechanical UEL, Elements $N_{\text{phys}}+1 \dots 2N_{\text{phys}}$):**
   - User elements (`JTYPE=2` quad, `JTYPE=4` tri).
   - Solves active Degrees of Freedom 1, 2 (displacements $u_x, u_y$).
   - Computes element elastic strain energy $E_{\text{elas}, e}$ and stores it in common block `SV_E_ELAS(PHYSIDX)`.
3. **Layer 3 (Companion Visualizer UMAT, Elements $2N_{\text{phys}}+1 \dots 3N_{\text{phys}}$):**
   - Standard Abaqus continuum elements (`CPE4` quad, `CPE3` tri) assigned material `DUMMY_MAT`.
   - Passive constitutive behavior ($\sigma \equiv 0$, stiffness $10^{-11}$).
   - Ingests common block states at index $\text{PHYSIDX} = \text{NOEL} - 2 N_{\text{phys}}$:
     - `STATEV(17) = SV_E_FRAC(PHYSIDX)`
     - `STATEV(18) = SV_E_ELAS(PHYSIDX)`
     - `STATEV(19) = SV_PSI_F(PHYSIDX)`
     - `STATEV(20) = SV_PSI_E(PHYSIDX)`

### 4.2 De-duplication and Anti-Overcounting Proofs
1. **Zero Multi-Layer Overcounting in Fortran `UEXTERNALDB`:**
   `UEXTERNALDB` loops strictly over physical element indices:
   ```fortran
   DO I = 1, N_CAPACITY
     TOT_E_ELAS = TOT_E_ELAS + SV_E_ELAS(I)
     TOT_E_FRAC = TOT_E_FRAC + SV_E_FRAC(I)
   ENDDO
   ```
   Because each physical finite element ($1 \dots N_{\text{phys}}$) occupies exactly one slot $I = \text{PHYSIDX}$, `UEXTERNALDB` integrates each physical element exactly once. Layer 1, Layer 2, and Layer 3 do not create duplicate slots.

2. **Zero $4\times$ Integration-Point Overcounting in ODB Extraction:**
   In Abaqus ODB field output, `CPE4` elements write their state variables to all 4 integration points (IP1, IP2, IP3, IP4). Because `STATEV(17)` and `STATEV(18)` are whole-element integrated values, summing across all integration points would overestimate domain energy by a factor of 4.  
   The authoritative extractor (`extract_authoritative_mode1_energy_complete.py`) enforces **single-value element deduplication**:
   ```python
   seen_elems = set()
   for v17, v18 in zip(sdv17.values, sdv18.values):
       eid = v17.elementLabel
       if eid not in seen_elems:
           seen_elems.add(eid)
           e_frac_sum += float(v17.data)
           e_elas_sum += float(v18.data)
   ```
   This guarantees that each unique finite element is summed exactly once.

3. **Cross-Channel Parity Verification:**
   On the 64-element benchmark (`PK_M1_MINI_OUTDIR`), the deduplicated ODB sum and the `UEXTERNALDB` CSV global energy agreed to $< 10^{-10}\,\text{kN}\cdot\text{mm}$ ($0.000000\%$ relative difference), confirming exact mathematical parity across independent output paths.

### 4.3 Source-Level Out-of-Plane Thickness Normalization & Two-Tier Dimensional Framework

#### 4.3.1 Tier 1: Native 2D UEL Assembly & Residual Quadrature (Source-Line Audit)
A line-by-line audit of `f42_mixed_uel.for` confirms that the UEL subroutine operates strictly on 2D in-plane differential areas:
1. **In-Plane Differential Area (`CJAC`):**
   - For 4-node quadrilateral elements (`JTYPE = 1, 2`, Lines 323, 469):
     $$\text{CJAC} = \text{DETJ} \cdot \text{WT} \quad (\text{mm}^2)$$
   - For 3-node triangular elements (`JTYPE = 3, 4`, Lines 607, 725):
     $$\text{CJAC} = \text{DETJ} \cdot \text{WT} \quad (\text{mm}^2)$$
2. **Mechanical Residual Assembly (Lines 501, 772):**
   ```fortran
   F_INT(I) = F_INT(I) + CJAC * B(J,I) * STRESS(J)
   RHS(I,1) = -F_INT(I)
   ```
   Checking dimensions:
   $$[\text{CJAC}] \sim \text{mm}^2, \quad [B] \sim 1/\text{mm}, \quad [\sigma] \sim \text{kN/mm}^2$$
   $$[F_{\text{int}}] = (\text{mm}^2) \cdot (1/\text{mm}) \cdot (\text{kN/mm}^2) = \frac{\text{kN}}{\text{mm}}$$
   The native mechanical residual vector and solver reaction forces are dimensionally **force per unit thickness** ($\text{kN/mm}$).
3. **Mechanical Tangent Matrix (Lines 506-507, 777-778):**
   $$[K] = (\text{mm}^2) \cdot (1/\text{mm}) \cdot (\text{kN/mm}^2) \cdot (1/\text{mm}) = \frac{\text{kN}}{\text{mm}^2}$$
   The native tangent stiffness is dimensionally **stiffness per unit thickness** ($\text{kN/mm}^2$).
4. **Energy Quadrature Assembly (Lines 359, 537, 656, 808):**
   ```fortran
   E_FRAC_ELEM = E_FRAC_ELEM + CJAC * PSI_F_PT
   E_ELAS_ELEM = E_ELAS_ELEM + CJAC * PSI_E_PT
   ```
   With local volumetric densities $[\psi_f], [\psi_e] \sim \text{kN/mm}^2 \equiv \text{J/mm}^3$:
   $$[E_{\text{elem}}] = (\text{mm}^2) \cdot (\text{kN/mm}^2) = \text{kN} \equiv \frac{\text{kN}\cdot\text{mm}}{\text{mm}} \equiv \frac{\text{J}}{\text{mm}}$$
   The native integrated element energies are dimensionally **energy per unit thickness** ($\text{J/mm} \equiv \text{kN}$).
5. **Absence of Explicit Thickness Multiplier in UEL:**
   There is **no explicit thickness variable ($t$) or property multiplier** anywhere in `f42_mixed_uel.for`. Both the mechanical residual and the energy integrals are assembled using the identical 2D area differential $\text{CJAC} = dA$. Because both equations lack a thickness multiplier, the native mechanical and energetic formulations are **100% mathematically and dimensionally consistent** at the source level.

#### 4.3.2 Tier 2: Project Implementation Convention ($t_{\text{ref}} = 1.0\,\text{mm}$)

**Literature Provenance Audit (Pandey & Kumar, 2025):**
A detailed audit of the primary publication (CMES 144(3), 3251–3276) confirms that in Section 4.1 (pages 3264–3265), the authors formulate the Mode-I benchmark strictly as a 2D problem ($\Omega = 1.0\,\text{mm} \times 1.0\,\text{mm}$ square domain, $a_0 = 0.5\,\text{mm}$ edge crack, $E = 210\,\text{GPa}$, $\nu = 0.3$, $l_0 = 0.0075\,\text{mm}$, $G_c = 2.7\times 10^{-3}\,\text{kN/mm}$). **The publication does NOT prescribe or report an out-of-plane thickness $t$ for the Mode-I specimen.** (In contrast, Section 4.4 explicitly specifies $t = 100\,\text{mm}$ for the L-panel).

Therefore, any statement that "the Pandey–Kumar benchmark prescribes $t = 1.0\,\text{mm}$" is scientifically unverified and rejected. Instead, the project maintains three clear, distinct definitions:
1. **Literature Formulation:** Pure 2D Mode-I formulation as documented by Pandey & Kumar (2025).
2. **Project Implementation Convention:** $t_{\text{ref}} \equiv 1.0\,\text{mm}$ adopted by the project for converting native per-unit-thickness 2D UEL quantities into reported resultant tensile force ($F = F_{\text{raw}} \cdot t_{\text{ref}}$ in $\text{kN}$) and total scalar energy ($E = E_{\text{raw}} \cdot t_{\text{ref}}$ in $\text{kN}\cdot\text{mm} \equiv \text{J} = 1000\,\text{mJ}$) for a standardized $1.0\text{-mm}$ slice, matching external boundary work $W_{\text{ext}} = \int F \, du$.
3. **Companion Visualization Layer:** The card `*Solid Section, elset=All_elem, material=DUMMY_MAT` with explicit `1.0` thickness in the input decks provides secondary project-level corroboration that the companion visualization layer uses the same $1.0\,\text{mm}$ convention, but is strictly rejected as proof of a literature-prescribed thickness.

Multiplying native 2D quantities by the project convention $t_{\text{ref}} = 1.0\,\text{mm}$ yields:
1. **Total Tensile Reaction Force:**
   $$F = F_{\text{raw}} \cdot t_{\text{ref}} = \left( \frac{\text{kN}}{\text{mm}} \right) \cdot (1.0\,\text{mm}) = \text{kN}$$
2. **Total External Work:**
   $$W_{\text{ext}} = \int_0^u F \, du = \left( \int_0^u F_{\text{raw}} \, du \right) \cdot t_{\text{ref}} = W_{\text{ext, raw}} \cdot t_{\text{ref}} = \text{kN}\cdot\text{mm} \equiv \text{J} = 1000\,\text{mJ}$$
3. **Total Internal Model Energy:**
   $$E_{\text{model}} = (E_{\text{elas, raw}} + E_{\text{frac, raw}}) \cdot t_{\text{ref}} = \text{kN}\cdot\text{mm} \equiv \text{J} = 1000\,\text{mJ}$$
4. **Global Bookkeeping Residual:**
   $$\Delta_{\text{book}} = E_{\text{model}} - W_{\text{ext}} = (E_{\text{model, raw}} - W_{\text{ext, raw}}) \cdot t_{\text{ref}} = \text{kN}\cdot\text{mm} \equiv \text{J}$$

**Numerical Neutrality:** Because $t_{\text{ref}} = 1.0\,\text{mm}$ has a numerical magnitude of exactly $1.0$, multiplying by $t_{\text{ref}}$ does **not** change any floating-point value. However, the dimensional interpretation is rigorously converted from per-unit-thickness ($\text{kN/mm}$, $\text{J/mm}$) to total physical force and energy ($\text{kN}$, $\text{J}$) for the 1-mm slice.

#### 4.3.3 Role of Companion Section `*Solid Section, ... 1.0`
The companion visualization layer in all input decks specifies:
```abaqus
*Solid Section, elset=All_elem, material=DUMMY_MAT
1.0
```
- **Epistemological Status:** This card is **NOT** proof of a literature-prescribed thickness, nor is it the primary proof of UEL dimensionality. The Fortran UEL execution is completely independent of the companion UMAT section card.
- **Corroborating Evidence:** Rather, this card confirms that Abaqus built-in continuum elements and the companion visualization layer adopt the exact same project implementation convention ($t_{\text{ref}} = 1.0\,\text{mm}$). The primary mathematical proof of UEL consistency rests on the identical 2D area quadrature evaluated in the UEL Fortran source lines.

#### 4.3.4 Historical Reference Anchor Interpretation
Under this explicit normalization framework:
- The canonical reference peak force $F_{\max} = 0.757778\,\text{kN}$ represents the resultant tensile force on the $1.0\,\text{mm}$ slice under the project convention (or equivalently $F_{\max, \text{raw}} = 0.757778\,\text{kN/mm}$ in native 2D continuum terms).
- The initial structural stiffness $K_0 = 137.945520\,\text{kN/mm}$ represents the global stiffness for the $1.0\,\text{mm}$ slice (or equivalently $K_{0, \text{raw}} = 137.945520\,\text{kN/mm}^2$ per unit thickness).
- The cumulative external work $W_{\text{ext}}$ and internal energies $E_{\text{elas}}, E_{\text{frac}}$ represent scalar energy for the $1.0\,\text{mm}$ slice in $\text{kN}\cdot\text{mm} \equiv \text{J} = 1000\,\text{mJ}$.
All reports and publications must maintain consistency by explicitly stating this project-adopted $1.0\,\text{mm}$ slice normalization.

---

## 5. Offline Unit Regression Matrix

The following 19-test matrix is codified in `tests/unit/test_mode1_energy_equation_code_map.py` to prevent regression:

| Test Case | Defect Mode Tested | Expected Behavior | Verification Logic |
| :--- | :--- | :--- | :--- |
| `test_detects_swapped_sdv17_sdv18` | Swapped SDV17 ($E_{\text{elas}}$) and SDV18 ($E_{\text{frac}}$) labels | Fails verification if fracture energy is mapped to SDV18 | Asserts $\text{SDV17} \equiv E_{\text{frac}}$ and $\text{SDV18} \equiv E_{\text{elas}}$ |
| `test_rejects_summation_of_energy_densities` | Accidental direct summation of SDV19 ($\psi_f$) or SDV20 ($\psi_e$) | Flags dimensional error if $\psi_f, \psi_e$ are treated as energies | Validates units ($\text{kN/mm}^2$ vs $\text{kN}\cdot\text{mm}$) and requires area/volume integration |
| `test_detects_4x_gauss_point_overcounting` | Omitting element deduplication on 4-IP CPE4 companion elements | Detects $4\times$ inflation factor | Compares naive IP sum ($4E$) with deduplicated sum ($E$) |
| `test_validates_energy_unit_conversions` | Incorrect unit scaling (e.g. $1\,\text{kN}\cdot\text{mm} \ne 1000\,\text{mJ}$) | Enforces exact physical conversion | $1.0\,\text{kN}\cdot\text{mm} = 1.0\,\text{J} = 1000.0\,\text{mJ} = 10^6\,\mu\text{J}$ |
| `test_detects_reversed_work_sign_convention` | Using un-negated Abaqus reaction force ($F = +\text{RF2}_{\text{RP}} < 0$) | Rejects negative work calculation ($W_{\text{ext}} < 0$) | Enforces $F = -\text{RF2}_{\text{RP}} > 0 \implies W_{\text{ext}} \ge 0$ |
| `test_verifies_companion_layer_mapping_formula` | Companion index lookup out-of-bounds error | Verifies Layer 3 mapping $\text{PHYSIDX} = \text{NOEL} - 2N_{\text{phys}}$ | Validates physical element index range $[1, N_{\text{phys}}]$ |
| `test_verifies_energy_balance_bookkeeping_formula` | Incorrect formula for $\Delta_{\text{book}}$, $\delta_{\text{book}}$ | Verifies exact residual formulas | Enforces signed difference and normalization rules |
| `test_stress_and_energy_density_units_kN_mm2` | Typographical error equating $1\,\text{kN/mm}^2$ to $1\,\text{MPa}$ | Rejects $1\,\text{kN/mm}^2 = 1\,\text{MPa}$ ($1000\times$ error) | Validates $1\,\text{kN/mm}^2 = 1000\,\text{MPa} = 1\,\text{GPa}$ |
| `test_rejects_kn_per_mm2_equals_j_per_mm2` | Equating volumetric density $\text{kN/mm}^2$ to surface density $\text{J/mm}^2$ | Rejects $\text{kN/mm}^2 = \text{J/mm}^2$ | Validates $\text{kN/mm}^2 = (\text{kN}\cdot\text{mm})/\text{mm}^3 \equiv \text{J/mm}^3$ |
| `test_at2_phase_field_density_dimensions` | Incorrect dimensional analysis of AT2 crack surface energy density $\psi_f$ | Confirms $[G_c/l_0] = \text{kN/mm}^2 \equiv \text{J/mm}^3$ | Evaluates $[G_c] = \text{kN/mm}$, $[l_0] = \text{mm} \implies [\psi_f] = \text{kN/mm}^2$ |
| `test_2d_plane_strain_thickness_energy_consistency` | Disregarding $t = 1.0\,\text{mm}$ out-of-plane thickness in 2D volume integrals | Verifies area integral $\times t$ yields $\text{kN}\cdot\text{mm} \equiv \text{J}$ matching $W_{\text{ext}}$ | Proves $E_{\text{model}}$ and $W_{\text{ext}}$ are dimensionally identical |
| `test_fails_if_2d_integral_lacks_thickness_handling` | Missing explicit thickness documentation or handling | Fails validator if thickness $t$ is omitted or invalid | Enforces unit thickness $t = 1.0\,\text{mm}$ specification |
| `test_uel_mechanical_residual_dimensions_per_unit_thickness` | Assuming raw UEL residual is total force $\text{kN}$ without thickness | Proves raw residual has dimension $\sigma B \, dA \sim \text{kN/mm}$ | Traces UEL lines 501, 772 proving force per unit thickness |
| `test_uel_energy_quadrature_dimensions_per_unit_thickness` | Assuming raw UEL energy integral is total scalar energy without thickness | Proves raw energy has dimension $\psi \, dA \sim \text{J/mm} \equiv \text{kN}$ | Traces UEL lines 359, 537 proving energy per unit thickness |
| `test_rejects_companion_solid_section_as_sole_uel_proof` | Claiming companion `*Solid Section` alone establishes UEL thickness | Rejects claim unless UEL source audit confirms identical area quadrature | Enforces independent UEL source proof over passive visualization overlay |
| `test_unit_thickness_normalization_preserves_values_restores_dimensions` | Altering numerical values during unit thickness normalization | Verifies $t = 1.0\,\text{mm}$ preserves numerical values while restoring dimensions | Confirms scaling by $1.0\,\text{mm}$ is numerically neutral |
| `test_consistent_thickness_convention_across_all_energy_quantities` | Comparing quantities under mismatched thickness conventions | Fails validator if $W_{\text{ext}}, E_{\text{elas}}, E_{\text{frac}}, \Delta_{\text{book}}$ mix thickness assumptions | Enforces unified $t = 1.0\,\text{mm}$ convention across all terms |
| `test_historical_reference_anchor_under_unit_thickness_normalization` | Silently switching between per-unit-thickness and total 3D terminology | Verifies $F_{\max} = 0.757778\,\text{kN}, K_0 = 137.945520\,\text{kN/mm}$ under $t=1\,\text{mm}$ | Enforces explicit reporting of $1.0\,\text{mm}$ project convention normalization |
| `test_rejects_unsupported_claim_that_pandey_kumar_prescribes_thickness` | Unsupported claim that Pandey & Kumar (2025) prescribes 1-mm thickness | Rejects claim unless primary-source citation with explicit thickness is proven | Audits Sec. 4.1 confirming 2D formulation; enforces three-part distinction |

---

## 6. Document Governance & Acceptance Sign-Off

- **Authoritative Status:** Frozen for supervisor review (08 October 2026 meeting).
- **Code Lineage:** Fully audited against production Fortran `f42_mixed_uel.for` (`CE8D5EDC...`).
- **Execution Rule:** Zero unauthorized HPC submissions; Job `1409734.mmaster02` actively computing authoritative reference data.
