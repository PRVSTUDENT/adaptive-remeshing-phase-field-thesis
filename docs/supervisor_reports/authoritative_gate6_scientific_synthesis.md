# Authoritative Gate-6 Mode-I Single-Factor Causal Isolation & Synthesis

**Executive Summary:**
A comprehensive single-factor causal isolation and $2 \times 2$ factorial decomposition of the Gate-6 nominal 1% adaptive mesh ($71{,}320$ finite elements, $70{,}845$ nodes) stiffness anomaly has been executed on the HPC cluster across 10 distinct computational models. Every candidate model has progressed past the frozen intact elastic interval ($u \in [0, 0.0010]\text{ mm}$), yielding unconstrained OLS linear regressions with $R^2 = 1.00000000$.

---

## 1. Complete 10-Model Empirical Stiffness Ledger

| Job ID | Model Tag | `UNSYMM` | Companion Elements Configuration | $K_0$ OLS (kN/mm) | $R^2$ | Status / Classification |
| :--- | :--- | :---: | :--- | :---: | :---: | :--- |
| `1403703` | `PK_M1_DECOMP_MECH_ONLY` | OFF | NONE | **$138.021015$** | $1.00000000$ | Baseline Mechanical DOFs (1,2) only |
| `1403704` | `PK_M1_DECOMP_MECH_PLUS_PHASE` | OFF | NONE | **$138.021015$** | $1.00000000$ | $K_{00}$: Symmetric Direct Sparse Baseline |
| `1403706` | `PK_M1_DECOMP_UNSYMM` | ON | NONE | **$138.021015$** | $1.00000000$ | $K_{10}$: Main Effect `UNSYMM` ($\Delta = 0.000\%$) |
| `1403707` | `PK_M1_DECOMP_COMPANION` | OFF | FULL ($69{,}443$ CPE4 + $1{,}877$ CPE3) | **$138.021015$** | $1.00000000$ | $K_{01}$: Main Effect Companion ($\Delta = 0.000\%$) |
| `1403698` | `PK_M1_FROZEN_INTACT_NOM1` | ON | FULL (Original Immediate-Return UMAT) | **$122.599592$** | $1.00000000$ | $K_{11,\text{std}}$: Full Model ($\Delta = -11.173\%$) |
| `1403711` | `PK_M1_FULL_UNSYMM_COMP_EXPLICIT_ZERO_UMAT` | ON | FULL (Explicit-Zero Assignment UMAT) | **$122.599592$** | $1.00000000$ | $K_{11,\text{zero}}$: Uninitialized Memory Ruled Out |
| `1403712` | `PK_M1_FULL_UNSYMM_COMP_BUILTIN_NEARZERO` | ON | FULL (Native `*ELASTIC: 2.10E-10, 0.3`) | **$122.599592$** | $1.00000000$ | $K_{11,\text{builtin}}$: `UMAT_INTERFACE_NOT_REQUIRED` |
| `1403753` | `PK_M1_UNSYMM_COMP_CPE4_ONLY` | ON | CPE4-ONLY ($69{,}443$ CPE4, 0 CPE3) | **$122.599592$** | $1.00000000$ | $K_{11,\text{cpe4}}$: CPE4-only shows full deficit |
| `1403754` | `PK_M1_UNSYMM_COMP_CPE3_ONLY` | ON | CPE3-ONLY ($1{,}877$ CPE3, 0 CPE4) | **$122.599591$** | $1.00000000$ | $K_{11,\text{cpe3}}$: CPE3-only shows full deficit |
| `1403684` | `PK_M1_ELAST_NOM1` | OFF | NATIVE CONTINUUM ($71{,}320$ standard elements) | **$137.973464$** | $1.00000000$ | Continuum Elasticity Reference |

---

## 2. $2 \times 2$ Factorial ANOVA & Interaction Analysis

$$\begin{aligned}
K_{00} &= 138.021015\text{ kN/mm} \quad (\text{Mech + Phase, Symmetric}) \\
K_{10} &= 138.021015\text{ kN/mm} \quad (\text{Mech + Phase, Unsymmetric}) \implies \Delta K_{\text{UNSYMM}} = 0.000000\text{ kN/mm} \ (0.0000\%) \\
K_{01} &= 138.021015\text{ kN/mm} \quad (\text{Mech + Phase + Companion, Symmetric}) \implies \Delta K_{\text{Comp}} = 0.000000\text{ kN/mm} \ (0.0000\%) \\
K_{11} &= 122.599592\text{ kN/mm} \quad (\text{Mech + Phase + Companion, Unsymmetric}) \\
\Delta K_{\text{int}} &= K_{11} - K_{10} - K_{01} + K_{00} = \mathbf{-15.421423\text{ kN/mm}} \quad (\mathbf{-11.1732\%})
\end{aligned}$$

Neither solver unsymmetry alone nor companion element presence alone alters the structural stiffness by even $0.001\%$. The anomaly occurs strictly when both factors interact.

---

## 3. Single-Factor Mechanism Diagnostics

### 3.1 Empirical UMAT Runtime Probe (Job `1403768`)
Instrumentation of the immediate-return UMAT at element 1, integration point 1 during increment 1 recorded incoming array values:
- `IN_STRESS = [0.0, 0.0, 0.0, 0.0]`
- `IN_DDSDDE = 0.0` (all 16 components)
- `IN_SSE = 0.0, IN_SPD = 0.0, IN_SCD = 0.0`
- `IN_PROPS = [210.0, 0.3]`

**Finding:** Abaqus 2023 pre-initializes incoming UMAT output arrays to exact zeros on increment 1. Uninitialized memory or floating-point residuals are definitively ruled out.

### 3.2 UMAT Call Path Bypass (Job `1403712`)
Replacing `*USER MATERIAL` with native Abaqus `*ELASTIC: 2.10E-10, 0.3` produced identical stiffness ($122.599592\text{ kN/mm}$, 8 significant figures). The UMAT interface, compiler conventions, and Fortran runtime memory are not required for the trigger (`UMAT_INTERFACE_NOT_REQUIRED_FOR_TRIGGER`).

### 3.3 Companion Family Decomposition (Jobs `1403753` and `1403754`)
- **CPE4-Only ($69{,}443$ elements, 0 CPE3):** $K_0 = 122.599592\text{ kN/mm}$
- **CPE3-Only ($1{,}877$ elements, 0 CPE4):** $K_0 = 122.599591\text{ kN/mm}$

**Finding:** Both element families individually produce the exact same deficit. The trigger is the generic presence of co-located standard continuum elements in the unsymmetric global equation graph.

---

## 4. Preserved Scientific Classifications

- `underlying continuum mesh`: **`RULED_OUT`** (Supports $137.97 \dots 138.02\text{ kN/mm}$ in all single-layer models).
- `local UEL quad/triangle formulations`: **`RULED_OUT_LOCALLY`** (Matches offline global assembly to 7 significant figures).
- `early damage/degradation`: **`RULED_OUT`** (Forced intact $d=0, g(d)=1$ preserves exact linear elasticity across interval).
- `offline assembly contradiction`: **`DEFINITIVELY_RESOLVED`** ($134.445519\text{ kN/mm}$ retired due to transposition bug; corrected value = $138.021015\text{ kN/mm}$).
- `immediate-return/uninitialized UMAT output`: **`RULED_OUT_AS_REQUIRED_TRIGGER`** (Empirical probe confirms zero initialization; explicit zero assignment and native `*ELASTIC` produce identical $122.599592\text{ kN/mm}$).
- `UMAT interface requirement`: **`UMAT_INTERFACE_NOT_REQUIRED_FOR_TRIGGER`** (Trigger reproduced identically with native Abaqus `*ELASTIC`).
- `UNSYMM × companion`: **`VERIFIED_UNSYMM_X_COMPANION_FACTORIAL_TRIGGER_ON_FROZEN_INTERVAL`**.
- `companion CPE4 vs CPE3 contribution`: **`BOTH_INDIVIDUALLY_SUFFICIENT`** (CPE4-only yields $122.599592\text{ kN/mm}$, CPE3-only yields $122.599591\text{ kN/mm}$).
- `internal Abaqus mechanism`: **`INTERNAL_MECHANISM_NOT_YET_ESTABLISHED`**.
- `MISESERI→size mapping`: **`UNRESOLVED / INTERNAL_SIZING_MAPPING_NOT_DOCUMENTED`**.
- `INTERNAL_ENERGY_CONVERGENCE_NOT_AVAILABLE`.
