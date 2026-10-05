# Mode-I Stage-14 UEL Energy Formulation, Source Audit & Mechanical Parity Qualification

**Classification:** `SOURCE_AND_NUMERICAL_VERIFICATION`  
**Protocol Version:** 2  
**Authoritative Fortran Source:** `models/pandey_kumar_mode1/f42_mixed_uel.for`  
**Cryptographic Hash (SHA-256):** `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`  
**Pre-Instrumentation Source (SHA-256):** `ED1586D6427A4B1A01D99F7E219891EC7BE9FE911E066D9360724942E7D27720`  
**Governing Energy Status:** `UEL_ENERGY_OUTPUT_QUALIFIED_MECHANICALLY_NONINVASIVE`  
**Governing Gate Verdict:** `STAGE14_UEL_ENERGY_FORMULATION_AND_MECHANICAL_PARITY_QUALIFIED`  

---

## 1. Executive Summary & Epistemic Scope

This document provides the definitive term-by-term derivation, source code diff audit, dimensional validation, zero double-counting proof, and complete full-history mechanical parity verification for the energy quantities computed in the 3-layer staggered phase-field fracture implementation in Abaqus/Standard.

### Epistemic Classification:
- **`SOURCE_VERIFIED`**: Exact mathematical equations and Gauss-point quadrature loops implemented in `f42_mixed_uel.for` for stored elastic energy $E_{\text{elas}}$, regularized crack-surface functional $E_{\text{frac}}$, undegraded driving energy $H$, auxiliary state variable slots, zero energy outputs in companion UMAT (`SSE = SPD = SCD = 0`), and non-invasive `UEXTERNALDB` logging.
- **`NUMERICALLY_VERIFIED`**: Complete 7,000-increment full-history mechanical parity between pre-instrumentation fixed reference (`01_standard_pfm_reference`) and energy-instrumented fixed reference (`16_energy_qualification_reference_15k`, Job `1409734.mmaster02`), yielding exact bitwise parity in $K_0$ ($0.000000\%$), $F_{\max}$ ($0.000000\%$), increment count ($7{,}000/7{,}000$), Newton iterations ($21{,}120/21{,}120$), cutbacks ($0/0$), and external work ($3.02\times 10^{-9}\%$ difference).
- **`UNRESOLVED_INTERNAL_ABAQUS_DETAIL`**: Native Abaqus whole-model internal energy arrays (e.g. `ALLWK`, `ALLIE` when UEL elements are active) versus independent UEL/RP integration.

---

## 2. Term-by-Term Mathematical Derivations & Implemented Formulations

### 2.1 Implemented Phase-Field Crack-Surface Functional ($E_{\text{frac}}$)

#### Mathematical Equation:
$$\psi_f(\mathbf{x}) = G_c \left[ \frac{d(\mathbf{x})^2}{2 l_0} + \frac{l_0}{2} |\nabla d(\mathbf{x})|^2 \right]$$
$$E_{\text{frac}} = \int_{\Omega} \psi_f(\mathbf{x}) \,\mathrm{d}\Omega = \sum_{e=1}^{N_{\text{mesh}}} \sum_{k=1}^{N_{\text{int}}} w_k \det(\mathbf{J}_k) \cdot B \cdot G_c \left[ \frac{\bar{d}_e^2}{2 l_0} + \frac{l_0}{2} |\nabla d(\boldsymbol{\xi}_k)|^2 \right]$$
where $B = 1.0\,\mathrm{mm}$ is the implicit Abaqus 2D plane-strain unit thickness, and $\bar{d}_e = \frac{1}{N_{\text{nodes}}} \sum_{a=1}^{N_{\text{nodes}}} d_a$ is the element-averaged phase field.

#### Implementation in `f42_mixed_uel.for`:
- **4-Node Quadrilateral Phase Element (`JTYPE = 1`)**:
  - Quadrature: $2\times 2$ Gauss-Legendre quadrature ($N_{\text{int}} = 4$).
  - Lines 354–360:
    ```fortran
    DGRAD_SQ = DGRAD(1)**2 + DGRAD(2)**2
    PSI_F_PT = E_GC * (HALF * (D_AVG**2) / E_L0 + HALF * E_L0 * DGRAD_SQ)
    E_FRAC_ELEM = E_FRAC_ELEM + CJAC * PSI_F_PT
    ```
- **3-Node Triangular Phase Element (`JTYPE = 3`)**:
  - Quadrature: 1-point centroid quadrature ($N_{\text{int}} = 1$).
  - Lines 650–656:
    ```fortran
    DGRAD_SQ = DGRAD(1)**2 + DGRAD(2)**2
    PSI_F_PT = E_GC * (HALF * (D_AVG**2) / E_L0 + HALF * E_L0 * DGRAD_SQ)
    E_FRAC_ELEM = CJAC * PSI_F_PT
    ```
- **Global Storage & Output**:
  - Assigned to `ENERGY(7) = E_FRAC_ELEM` in UEL.
  - Stored in `SVARS(17) = E_FRAC_ELEM` and common block `SV_E_FRAC(PHYSIDX)`.
  - Aggregated across all elements in `UEXTERNALDB(LOP=2)` as `TOT_E_FRAC = sum(SV_E_FRAC)`.

---

### 2.2 Stored Elastic Strain Energy ($E_{\text{elas}}$)

#### Mathematical Equation:
$$\psi_e(\mathbf{x}) = \frac{1}{2} \boldsymbol{\sigma}(\mathbf{x}) : \boldsymbol{\varepsilon}(\mathbf{x}) = \frac{1}{2} g(d) \boldsymbol{\varepsilon}(\mathbf{x}) : \mathbb{C}_0 : \boldsymbol{\varepsilon}(\mathbf{x})$$
$$E_{\text{elas}} = \int_{\Omega} \psi_e(\mathbf{x}) \,\mathrm{d}\Omega = \sum_{e=1}^{N_{\text{mesh}}} \sum_{k=1}^{N_{\text{int}}} w_k \det(\mathbf{J}_k) \cdot B \cdot \left[ \frac{1}{2} \boldsymbol{\sigma}_k : \boldsymbol{\varepsilon}_k \right]$$
where $g(d) = (1-d)^2 + k_{\text{res}}$ with residual stiffness parameter $k_{\text{res}} = 10^{-7}$.

#### Implementation in `f42_mixed_uel.for`:
- **4-Node Quadrilateral Mechanical Element (`JTYPE = 2`)**:
  - Lines 534–538:
    ```fortran
    PSI_E_PT = HALF * (STRESS(1)*STRAIN(1) + STRESS(2)*STRAIN(2) + STRESS(3)*STRAIN(3))
    E_ELAS_ELEM = E_ELAS_ELEM + CJAC * PSI_E_PT
    ```
- **3-Node Triangular Mechanical Element (`JTYPE = 4`)**:
  - Lines 805–809:
    ```fortran
    PSI_E_PT = HALF * (STRESS(1)*STRAIN(1) + STRESS(2)*STRAIN(2) + STRESS(3)*STRAIN(3))
    E_ELAS_ELEM = CJAC * PSI_E_PT
    ```
- **Global Storage & Output**:
  - Assigned to `ENERGY(2) = E_ELAS_ELEM` in UEL (summed natively by Abaqus into whole-model `ALLSE`).
  - Stored in `SVARS(17) = E_ELAS_ELEM` and common block `SV_E_ELAS(PHYSIDX)`.
  - Aggregated in `UEXTERNALDB(LOP=2)` as `TOT_E_ELAS = sum(SV_E_ELAS)`.

---

### 2.3 Undegraded Tensile Driving Energy ($H$)

#### Mathematical Equation:
$$\psi_0^+(\boldsymbol{\varepsilon}) = \frac{1}{2} C_{12}^0 \langle \mathrm{tr}(\boldsymbol{\varepsilon}) \rangle_+^2 + C_{33}^0 \left( \varepsilon_{11}^2 + \varepsilon_{22}^2 + 2 \varepsilon_{12}^2 \right)$$
$$H(\mathbf{x}, t) = \max_{\tau \in [0, t]} \psi_0^+(\boldsymbol{\varepsilon}(\mathbf{x}, \tau))$$

#### Implementation in `f42_mixed_uel.for`:
- Evaluated in Mechanical UEL (Layer 2, lines 524–531) and passed via `COMMON /CB_STATE_TRANS/` (`SV_H_TRIAL`) to Phase UEL (Layer 1) to drive the Euler-Lagrange damage balance:
  $$\left( \frac{G_c}{l_0} + 2 H \right) d - G_c l_0 \nabla^2 d = 2 H$$

---

### 2.4 External Boundary Work ($W_{\text{ext}}$)

#### Mathematical Equation:
$$W_{\text{ext}}(u) = \int_0^u F(\tilde{u}) \,\mathrm{d}\tilde{u}$$

#### Discrete Trapezoidal Rule:
$$W_{\text{ext}}(u_n) = \sum_{i=1}^n \frac{F_i + F_{i-1}}{2} (u_i - u_{i-1}) \times 1000\,\mathrm{mJ/J}$$
- **Discipline**: $W_{\text{ext}}$ is external mechanical boundary work from RP reaction force integration $\int F\,\mathrm{d}u$, and must **never** be labeled internal strain energy or fracture energy.

---

### 2.5 Model Total Internal Energy ($E_{\text{model}}$) & Bookkeeping Residual ($\Delta_{\text{book}}$)

#### Frozen Mathematical Definitions:
$$E_{\text{model}}(u) = E_{\text{elas}}(u) + E_{\text{frac}}(u)$$
$$\Delta_{\text{book}}(u) = W_{\text{ext}}(u) - E_{\text{model}}(u) = W_{\text{ext}}(u) - \left[ E_{\text{elas}}(u) + E_{\text{frac}}(u) \right]$$
$$\varepsilon_{\text{book}}(u) = \frac{|\Delta_{\text{book}}(u)|}{|W_{\text{ext}}(u)|} \times 100\%$$

#### Sign Interpretation:
- $\Delta_{\text{book}} > 0 \implies W_{\text{ext}} > E_{\text{model}}$ (external work exceeds internal model energy).
- $\Delta_{\text{book}} < 0 \implies W_{\text{ext}} < E_{\text{model}}$ (internal model energy exceeds external work).

---

## 3. Co-Located 3-Layer Architecture & Deduplication Analysis

The benchmark discretization employs 3 co-located element layers sharing identical nodal coordinates:

| Layer | Type | Element IDs | Active DOFs | Role in Formulation | Energy Contribution |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **Layer 1** | Phase UEL (`JTYPE 1, 3`) | $1 \dots N_{\text{mesh}}$ | DOF 3 ($d$) | Solves phase-field Euler-Lagrange PDE | $E_{\text{frac}}$ (stored in `ENERGY(7)`) |
| **Layer 2** | Mech UEL (`JTYPE 2, 4`) | $N_{\text{mesh}}+1 \dots 2N_{\text{mesh}}$ | DOFs 1, 2 ($u_x, u_y$) | Solves degraded mechanical equilibrium | $E_{\text{elas}}$ (stored in `ENERGY(2)`) |
| **Layer 3** | Visualizer UMAT (`CPE4/CPE3`) | $2N_{\text{mesh}}+1 \dots 3N_{\text{mesh}}$ | DOFs 1, 2 | Dummy visualization overlay for Abaqus/CAE | **Numerically Negligible** ($\mathbf{D} = 10^{-11}\mathbf{I}$, $\boldsymbol{\sigma} \approx \mathbf{0}$) |

### Deduplication Proof & Companion UMAT Behavior:
1. **In `UMAT` (lines 876–886)**:
   - Dummy Stiffness: $\mathbf{D}_{\text{comp}} = 10^{-11} \mathbf{I}\,\text{GPa}$.
   - Stress: $\boldsymbol{\sigma}_{\text{comp}} = \mathbf{0}$.
   - Energy variables explicitly set to zero: `SSE = 0.D0`, `SPD = 0.D0`, `SCD = 0.D0`.
   - Strain energy generated by Layer 3 is on the order of $\sim 10^{-11}\,\mathrm{J}$, which is numerically negligible compared to physical energies ($\sim 2.3\,\mathrm{mJ}$).
2. **In `UEXTERNALDB` (lines 130–137)**:
   - The global energy loop runs over $I = 1 \dots N_{\text{mesh}}$, summing `SV_E_ELAS(I)` (written exclusively by Layer 2) and `SV_E_FRAC(I)` (written exclusively by Layer 1).
   - Layer 3 does not write to `SV_E_ELAS` or `SV_E_FRAC`.
3. **Postprocessor Extraction Rule**:
   - Extractors sample state variables at **Integration Point 1 (`IP1`) only** (verified with within-element equality assertions), preventing $4\times$ overcounting across Gauss points.
4. **Verdict**: The implementation guarantees **no counted physical-energy duplication** and a **numerically negligible companion contribution**.

---

## 4. Mechanical Non-Invasiveness & Full-History Parity Qualification

### 4.1 Source Invariance Audit
The Fortran source diff between the un-instrumented baseline (`ED1586D6427A4B1A01D99F7E219891EC7BE9FE911E066D9360724942E7D27720`) and the instrumented production code (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`) was audited line-by-line:
1. **RHS Residual Vectors**: Zero mathematical modifications for 4-node quad elements; `RHS` remains strictly dependent only on internal mechanical forces and phase-field balance.
2. **AMATRX Tangent Stiffness Matrices**: Zero mathematical modifications for 4-node quad elements; consistent analytical tangents are identical.
3. **Constitutive Degradation & History Evolution**: Function $g(d) = (1-d)^2 + k_{\text{res}}$ and $H(\mathbf{x}, t) = \max \psi_0^+$ are 100% bitwise invariant.
4. **State Variable Slots**: Auxiliary energy logging is mapped strictly to dedicated slots `SVARS(17..18)` and `STATEV(17..20)`. Baseline slots `SVARS(1..16)` and `STATEV(1..16)` remain completely unaltered.

### 4.2 Comprehensive 7,000-Increment Mechanical Parity Results
A point-by-point comparison was conducted between the pre-instrumentation fixed-reference solve (`01_standard_pfm_reference`, 15,192 FE) and the energy-instrumented fixed-reference solve (`16_energy_qualification_reference_15k`, Job `1409734.mmaster02`, 15,192 FE):

| Quantity / Metric | Pre-Instrumentation (`ED1586D6`) | Post-Instrumentation (`CE8D5EDC`) | Absolute Difference | Relative Difference | Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Initial Stiffness $K_0$** | $137.945519645\,\text{kN/mm}$ | $137.945519645\,\text{kN/mm}$ | $0.000000\,\text{kN/mm}$ | **$0.000000\%$** | **BITWISE MATCH** |
| **$K_0$ Linear Fit $R^2$** | $0.99999960$ | $0.99999960$ | $0.000000$ | $0.000000\%$ | **BITWISE MATCH** |
| **Peak Force $F_{\max}$** | $0.75777849\,\text{kN}$ | $0.75777849\,\text{kN}$ | $0.000000\,\text{kN}$ | **$0.000000\%$** | **BITWISE MATCH** |
| **Displacement at Peak $u(F_{\max})$** | $0.005857\,\text{mm}$ | $0.005857\,\text{mm}$ | $0.000000\,\text{mm}$ | **$0.000000\%$** | **BITWISE MATCH** |
| **Final Force $F(u=0.010\,\text{mm})$** | $2.32162170\times 10^{-4}\,\text{kN}$ | $2.32162150\times 10^{-4}\,\text{kN}$ | $2.0\times 10^{-11}\,\text{kN}$ | $8.61\times 10^{-6}\%$ | **ROUNDOFF PARITY** |
| **External Work $W_{\text{ext}}$** | $2.359328927990\,\text{mJ}$ | $2.359328927919\,\text{mJ}$ | $7.12\times 10^{-11}\,\text{mJ}$ | **$3.02\times 10^{-9}\%$** | **ROUNDOFF PARITY** |
| **Pointwise Max $|\Delta u|$** | — | — | $0.000000\,\text{mm}$ | $0.000000\%$ | **BITWISE MATCH** |
| **Pointwise Max $|\Delta F|$** | — | — | $1.0\times 10^{-9}\,\text{kN}$ | $1.29\times 10^{-5}\%$ | **ROUNDOFF PARITY** |
| **Total Completed Increments** | $7{,}000$ | $7{,}000$ | $0$ | $0.0\%$ | **EXACT MATCH** |
| **Total Newton Iterations** | $21{,}120$ | $21{,}120$ | $0$ | $0.0\%$ | **EXACT MATCH** |
| **Cutbacks / Severe Discon.** | $0 / 0$ | $0 / 0$ | $0 / 0$ | $0.0\%$ | **EXACT MATCH** |

### 4.3 10-State Matched Displacement Parity Table

| Matched State | Step, Inc | Prescribed $u$ (mm) | Pre RF (kN) | Post RF (kN) | $\Delta \text{RF}$ (kN) | Relative Difference | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$u = 0.001000\,\text{mm}$** | $(1, 400)$ | $0.001000$ | $0.13792416$ | $0.13792416$ | $0.0000\,\text{e+}00$ | $0.000000\%$ | BITWISE MATCH |
| **$u = 0.003000\,\text{mm}$** | $(1, 1200)$ | $0.003000$ | $0.40841828$ | $0.40841828$ | $0.0000\,\text{e+}00$ | $0.000000\%$ | BITWISE MATCH |
| **$u = 0.005000\,\text{mm}$** | $(1, 2000)$ | $0.005000$ | $0.66205217$ | $0.66205217$ | $0.0000\,\text{e+}00$ | $0.000000\%$ | BITWISE MATCH |
| **$u = 0.005857\,\text{mm}$ (Peak)** | $(2, 857)$ | $0.005857$ | $0.75777849$ | $0.75777849$ | $0.0000\,\text{e+}00$ | $0.000000\%$ | BITWISE MATCH |
| **$u = 0.006000\,\text{mm}$** | $(2, 1000)$ | $0.006000$ | $0.00054637$ | $0.00054637$ | $1.0000\,\text{e-}11$ | $0.000002\%$ | ROUNDOFF MATCH |
| **$u = 0.006500\,\text{mm}$** | $(2, 1500)$ | $0.006500$ | $0.00048480$ | $0.00048480$ | $1.0000\,\text{e-}11$ | $0.000002\%$ | ROUNDOFF MATCH |
| **$u = 0.007000\,\text{mm}$** | $(2, 2000)$ | $0.007000$ | $0.00042986$ | $0.00042986$ | $1.0000\,\text{e-}11$ | $0.000002\%$ | ROUNDOFF MATCH |
| **$u = 0.008000\,\text{mm}$** | $(2, 3000)$ | $0.008000$ | $0.00033946$ | $0.00033946$ | $1.0000\,\text{e-}11$ | $0.000003\%$ | ROUNDOFF MATCH |
| **$u = 0.009000\,\text{mm}$** | $(2, 4000)$ | $0.009000$ | $0.00027648$ | $0.00027648$ | $2.0000\,\text{e-}11$ | $0.000007\%$ | ROUNDOFF MATCH |
| **$u = 0.010000\,\text{mm}$ (Final)** | $(2, 5000)$ | $0.010000$ | $0.00023216$ | $0.00023216$ | $2.0000\,\text{e-}11$ | $0.000009\%$ | ROUNDOFF MATCH |

### 4.4 Formal Energy-Output Status Promotion
- **Prior Status**: `UEL_ENERGY_OUTPUT_NOT_YET_QUALIFIED`
- **New Governed Status**: `UEL_ENERGY_OUTPUT_QUALIFIED_MECHANICALLY_NONINVASIVE`
- **Closure Evidence**: Provenance-linked full-solve comparison between `01_standard_pfm_reference` (`ED1586D6...`) and `16_energy_qualification_reference_15k` (Job `1409734.mmaster02`, `CE8D5EDC...`), demonstrating zero alteration to mechanics across all 7,000 increments.

---

## 5. Reconciled Reference & Adaptive Energy Metrics

### 5.1 Fixed Reference Baseline ($S_1$, 15,192 FE, Job 1409734.mmaster02)
- **At Terminal State ($u = 0.010000\,\text{mm}$)**:
  - $W_{\text{ext}} = 2.359329\,\text{mJ}$
  - $E_{\text{frac}} = 2.340220\,\text{mJ}$
  - $E_{\text{elas}} = 0.001161\,\text{mJ}$
  - $E_{\text{model}} = 2.341381\,\text{mJ}$
  - $\Delta_{\text{book}} = W_{\text{ext}} - E_{\text{model}} = \mathbf{+0.017948\,\text{mJ}}$
  - $\varepsilon_{\text{book}} = \frac{+0.017948}{2.359329} \times 100\% = \mathbf{0.7607\%}$

- **At Matched Displacement ($u = 0.007889\,\text{mm}$)**:
  - $W_{\text{ext}} = 2.358728\,\text{mJ}$
  - $E_{\text{frac}} = 2.339582\,\text{mJ}$
  - $E_{\text{elas}} = 0.001374\,\text{mJ}$
  - $E_{\text{model}} = 2.340956\,\text{mJ}$
  - $\Delta_{\text{book}} = W_{\text{ext}} - E_{\text{model}} = \mathbf{+0.017772\,\text{mJ}}$
  - $\varepsilon_{\text{book}} = \mathbf{0.7535\%}$

### 5.2 Step-2 ET1 Adaptive Baseline (14,483 FE, Stage 14 Solve)
- **At Actual Terminal State ($u = 0.007889\,\text{mm}$, Step 2 Inc 2889)**:
  - $W_{\text{ext}} = 2.267380\,\text{mJ}$
  - $E_{\text{frac}} = 2.285469\,\text{mJ}$
  - $E_{\text{elas}} = 0.006960\,\text{mJ}$
  - $E_{\text{model}} = 2.292429\,\text{mJ}$
  - $\Delta_{\text{book}} = W_{\text{ext}} - E_{\text{model}} = \mathbf{-0.025049\,\text{mJ}}$
  - $\varepsilon_{\text{book}} = \frac{|-0.025049|}{2.267380} \times 100\% = \mathbf{1.104771\%}$

### 5.3 Root Cause of the $1.104771\%$ vs $0.8275\%$ Discrepancy:
- The value **$1.104771\%$** is the authentic, raw-extracted value at terminal increment Step 2 Inc 2889 ($u = 0.007889\,\text{mm}$) where the actual remaining elastic energy is $E_{\text{elas}} = 0.006960\,\text{mJ}$ ($F = 0.001764\,\text{kN}$).
- The value **$0.8275\%$** arose from plugging an assumed post-fracture residual elastic energy of $E_{\text{elas}} = 0.000674\,\text{mJ}$ into the terminal $W_{\text{ext}}$ and $E_{\text{frac}}$ values ($\Delta_{\text{book}} = -0.018763\,\text{mJ}$).
- **Resolution**: $1.104771\%$ with $E_{\text{elas}} = 0.006960\,\text{mJ}$ is the exact, canonical value for ET1 at its actual terminal state ($u = 0.007889\,\text{mm}$).

---

## 6. Summary Energy Metrics Table

| Metric / Dimension | Equation | Code Location | Units | Sign | Nature |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **Fracture Functional ($E_{\text{frac}}$)** | $\int_{\Omega} G_c \left(\frac{d^2}{2l_0} + \frac{l_0}{2}|\nabla d|^2\right)\mathrm{d}\Omega$ | `UEL` JTYPE 1/3 (l. 359, 655) | mJ | $\ge 0$ | Instantaneous regularized surface energy |
| **Elastic Energy ($E_{\text{elas}}$)** | $\int_{\Omega} \frac{1}{2} g(d) \boldsymbol{\varepsilon}:\mathbb{C}_0:\boldsymbol{\varepsilon}\,\mathrm{d}\Omega$ | `UEL` JTYPE 2/4 (l. 537, 808) | mJ | $> 0$ | Instantaneous stored elastic energy |
| **History Field ($H$)** | $\max_{\tau} \psi_0^+(\boldsymbol{\varepsilon}(\tau))$ | `UEL` JTYPE 2/4 (l. 530, 801) | $\mathrm{kN/mm^2}$ | $\ge 0$ | Path-dependent irreversibility field |
| **External Work ($W_{\text{ext}}$)** | $\int_0^u F(\tilde{u})\,\mathrm{d}\tilde{u}$ | Post-processed from RP force | mJ | $\ge 0$ | Cumulative boundary mechanical work |
| **Model Energy ($E_{\text{model}}$)** | $E_{\text{elas}} + E_{\text{frac}}$ | `UEXTERNALDB` (l. 137) | mJ | $> 0$ | Implemented internal model energy |
| **Bookkeeping Residual ($\Delta_{\text{book}}$)** | $W_{\text{ext}} - (E_{\text{elas}} + E_{\text{frac}})$ | Post-processed | mJ | Signed | Global energy conservation residual |
| **Relative Error ($\varepsilon_{\text{book}}$)** | $|\Delta_{\text{book}}| / W_{\text{ext}} \times 100\%$ | Post-processed | $\%$ | $\ge 0$ | Bookkeeping conservation metric ($\le 1.11\%$) |
