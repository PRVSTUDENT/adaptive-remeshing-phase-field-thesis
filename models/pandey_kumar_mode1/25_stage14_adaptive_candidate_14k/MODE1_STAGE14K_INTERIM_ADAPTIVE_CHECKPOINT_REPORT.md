# Mode-I Stage 14K: Non-Invasive Interim Adaptive-Response Checkpoint Report

**Task ID:** `F1188-GATE6B-STAGE14K-INTERIM-ADAPTIVE-CHECKPOINT-20261003`  
**Gate:** Gate-6B (Production Mode-I Adaptive Remeshing & Energy Convergence)  
**Date:** October 3, 2026  
**Agent:** Gemini Antigravity  
**Interim Classification:** `INTERIM_ONLY__FINAL_VERDICT_PENDING_TERMINAL_COMPLETION`  
**Active PBS Job:** `1409947.mmaster02` (`PK_M1_ADAPT_14K_FRACTURE`, node `mnode097`, queue `normal_imfdfkmq`)  
**Solver State at Checkpoint:** Running Step 2, Increment >2937 ($u = 0.007937\text{ mm}$), Total Runtime >01:42:00.

---

## 1. Executive Summary & Epistemological Stance

This interim report records the non-invasive, runtime audit of the Stage-14 14,483-element adaptive fracture simulation (PBS Job `1409947.mmaster02`). In strict accordance with the mandatory project rules:
1. **Zero Interference:** PBS Job `1409947.mmaster02` remains completely untouched on the cluster compute node (`mnode097`) and is allowed to run to natural terminal completion.
2. **Censored State Boundary:** Only reached target displacement states ($u \in \{0.0010, 0.0030, 0.0050, 0.005857, 0.0060, 0.0065, 0.0070\}\text{ mm}$) are evaluated and compared against the qualified fixed reference (Job `1409734.mmaster02`, 15,192 finite elements). Unreached states ($u \in \{0.0080, 0.0090, 0.0100\}\text{ mm}$) are strictly excluded and not extrapolated.
3. **Property ABI Audit & Root Cause Discovery:** A rigorous audit of the solve deck and user subroutine revealed a parameter card ordering mismatch between the Molnar convention and the `f42_mixed_uel.for` subroutine ABI, explaining the observed linear elastic behavior and absence of cutbacks.

---

## 2. Reached Displacement States Comparison Table

| Target $u$ [mm] | Ref $F$ [kN] | Adapt Interim $F$ [kN] | Ref $E_{\text{elas}}$ [mJ] | Adapt Interim $E_{\text{elas}}$ [mJ] | Ref $E_{\text{frac}}$ [mJ] | Adapt Interim $E_{\text{frac}}$ [mJ] | Ref $d_{\max}$ | Adapt Interim $d_{\max}$ | Ref $x_{\text{tip}}$ [mm] | Adapt $x_{\text{tip}}$ [mm] |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0.0010** | 0.137924 | $4.37\times 10^{-6}$ | 0.068962 | $2.19\times 10^{-6}$ | $5.55\times 10^{-5}$ | $2.26\times 10^{-26}$ | 0.0091 | 0.0000 | 0.500 | 0.500 |
| **0.0030** | 0.408418 | $1.31\times 10^{-5}$ | 0.612627 | $1.97\times 10^{-5}$ | 0.004534 | $1.84\times 10^{-24}$ | 0.0875 | 0.0000 | 0.500 | 0.500 |
| **0.0050** | 0.662052 | $2.19\times 10^{-5}$ | 1.655130 | $5.47\times 10^{-5}$ | 0.036541 | $1.42\times 10^{-23}$ | 0.2981 | 0.0000 | 0.500 | 0.500 |
| **0.005857** | 0.757778 | $2.56\times 10^{-5}$ | 2.219151 | $7.50\times 10^{-5}$ | 0.082690 | $2.68\times 10^{-23}$ | 0.6297 | 0.0000 | 0.500 | 0.500 |
| **0.0060** | 0.000546 | $2.62\times 10^{-5}$ | 0.001639 | $7.87\times 10^{-5}$ | 2.338772 | $2.95\times 10^{-23}$ | 1.0004 | 0.0000 | 0.998 | 0.500 |
| **0.0065** | 0.000485 | $2.84\times 10^{-5}$ | 0.001576 | $9.24\times 10^{-5}$ | 2.338978 | $4.07\times 10^{-23}$ | 1.0004 | 0.0000 | 0.998 | 0.500 |
| **0.0070** | 0.000430 | $3.06\times 10^{-5}$ | 0.001504 | $1.07\times 10^{-4}$ | 2.339204 | $5.47\times 10^{-23}$ | 1.0004 | 0.0000 | 0.998 | 0.500 |

*Note on unreached states:* Target states $u = 0.0080\text{ mm}$, $u = 0.0090\text{ mm}$, and $u = 0.0100\text{ mm}$ were not yet reached at the interim checkpoint time ($u_{\text{current}} = 0.007937\text{ mm}$) and are strictly excluded from numerical comparison.

---

## 3. Property ABI Card Inversion Analysis

### 3.1 Subroutine Parameter Parsing ABI
The Fortran subroutine `f42_mixed_uel.for` defines its parameter input mapping in lines 45–50 as:
```fortran
E_L0   = PROPS(1)   ! Length scale parameter l0 [mm]
E_GC   = PROPS(2)   ! Critical fracture energy Gc [kN/mm]
E_MOD  = PROPS(3)   ! Young's modulus E [kN/mm^2]
E_NU   = PROPS(4)   ! Poisson's ratio nu [-]
E_K    = PROPS(5)   ! Residual stiffness k [-]
N_PHYS = PROPS(6)   ! Total physical finite element count [-]
```

### 3.2 Comparison of Solved Input Decks
- **Qualified Reference (Job 1409734):**
  `*UEL Property: 0.0075, 0.0027, 210.0, 0.3, 1.0e-7, 15192.0`
  - $l_0 = 0.0075\text{ mm}$, $G_c = 0.0027\text{ kN/mm}$, $E = 210.0\text{ kN/mm}^2$, $\nu = 0.30$, $N_{\text{phys}} = 15192.0$.
  - Result: Correct physical crack initiation at $u=5.86\ \mu\text{m}$, peak load $F_{\max} = 0.758\text{ kN}$, complete propagation.

- **Stage-14 Adaptive Candidate Deck (Job 1409947):**
  `*UEL PROPERTY: 210.0, 0.3, 0.0075, 0.0027, 1.0E-7, 1.0`
  - Subroutine interpreted parameters:
    - $l_0 = 210.0\text{ mm}$ ($28,000\times$ larger than intended, domain-wide diffuse)
    - $G_c = 0.30\text{ kN/mm}$ ($111\times$ tougher than intended)
    - $E = 0.0075\text{ kN/mm}^2$ ($28,000\times$ softer than intended)
    - $\nu = 0.0027$
    - $N_{\text{phys}} = 1.0$

### 3.3 Physical and Numerical Consequences
1. The effective Young's modulus $E = 0.0075\text{ kN/mm}^2$ produces an initial linear stiffness $K_0 \approx 0.00437\text{ kN/mm}$, which is exactly $31,500\times$ lower than the reference stiffness $K_0 = 137.95\text{ kN/mm}$ (accounting for Young's modulus scaling and minor Poisson ratio effect $(1-\nu^2)$).
2. The strain energy generated at $u = 0.007\text{ mm}$ is only $E_{\text{elas}} \approx 1.07\times 10^{-4}\text{ mJ}$.
3. Because $G_c$ is interpreted as $0.30\text{ kN/mm}$ and $l_0 = 210.0\text{ mm}$, the fracture energy required for damage initiation is vastly greater than the available elastic strain energy. Consequently, damage remains strictly $d(x,y) \approx 0.0$ throughout the domain, no crack initiates, and the solver experiences zero nonlinear cutbacks, converging in exactly 1 iteration per increment.

---

## 4. Generated Figures Summary

The following four publication-quality figures with interim watermarks have been generated:
1. `results/figures/mode1_gate6b/fig_mode1_stage14k_interim_fu_comparison.png` (and `.pdf`): Force-displacement response comparison up to reached states ($u \le 0.0070\text{ mm}$).
2. `results/figures/mode1_gate6b/fig_mode1_stage14k_interim_energy_evolution.png` (and `.pdf`): Elastic strain energy and fracture dissipation partitioned evolution.
3. `results/figures/mode1_gate6b/fig_mode1_stage14k_interim_property_abi_audit.png` (and `.pdf`): Parameter ABI card comparison table diagram.
4. `results/figures/mode1_gate6b/fig_mode1_stage14k_interim_damage_localization.png` (and `.pdf`): Maximum damage growth ($d_{\max}$ vs $u$) and crack tip trajectory ($x_{\text{tip}}$ vs $u$).

---

## 5. Governance Action Plan & Next Steps

1. **Job 1409947 Lifecycle:** Allow PBS Job `1409947.mmaster02` to run to its natural terminal completion without intervention.
2. **Post-Termination Extraction:** Upon job completion, transfer and archive all runtime solver outputs (`.log`, `.dat`, `.msg`, `.sta`, `uel_energy_balance.csv`, `.odb`).
3. **Stage 14L Resubmission Preparation:**
   - Prepare package `models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k/` with the corrected UEL property line:
     `*UEL PROPERTY: 0.0075, 0.0027, 210.0, 0.3, 1.0e-7, 14483.0`
   - Run complete local datacheck and preflight verification.
   - Seek formal human authorization before executing the resubmitted Stage 14 production solve.
