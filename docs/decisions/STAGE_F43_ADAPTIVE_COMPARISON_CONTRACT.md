# Stage F43 Decision Record: Frozen Adaptive Mode-II Comparison Contract

**Task ID:** `F43ADAPT-COMPARE-CONTRACT1`  
**Date:** 2026-08-10  
**Status:** `FROZEN_FOR_ADAPTIVE_PRODUCTION`  
**Classification:** `scientific_comparison_contract_frozen`  

---

## 1. Executive Summary & Purpose

This decision record establishes the **frozen scientific comparison contract** for upcoming adaptive Mode-II production runs ($\text{MM}$ and $\text{PK5}$ candidates), grounded in the censoring-corrected uniform grid refinement evidence ($H_0$, $H_1$, $H_2$).

### Primary Scientific Rules Frozen:
1. **Uniform Reference Roles**:
   - $H_0$ (`1386372.mmaster02`, $N_{\text{phys}}=3930$): Coarse baseline reference ($h/l_0 = 2.0$).
   - $H_1$ (`1386447.mmaster02`, $N_{\text{phys}}=12064$): Minimum supported uniform comparison mesh ($h/l_0 = 1.0$) for initial elastic stiffness, pre-peak $RF_1\text{--}u_1$ response, damage initiation ($u_1 = 7.75\,\mu\text{m}$), and common-window global response ($0 \le u_1 \le 0.009250\,\text{mm}$).
   - $H_2$ (`1386448.mmaster02`, $N_{\text{phys}}=33852$): Fine spatial-resolution diagnostic ($h/l_0 = 0.5$) for $H_1/H_2$ refinement sensitivity and matched-state crack geometry.
2. **Explicit Crack-Path Classification**:
   - Matched-state Hausdorff distance ($H_1$ vs $H_2$ at $u_1 = 0.009250\,\text{mm}$): **$0.005443\,\text{mm}$ ($5.44\,\mu\text{m}$)**.
   - Frozen geometric gate: $\le 0.00375\,\text{mm}$.
   - **Classification: `matched_state_crack_path_convergence = FAIL`**.
   - Meaning: $H_1$ is **not** accepted as a geometrically converged crack-path reference. Spatial fracture geometry remains mesh-sensitive at the matched state despite high global force convergence ($0.518\%$ $L_2$).
3. **Censored Peak Force Rule**:
   - $H_1$ ($361.66\,\text{N}$ at $9.63\,\mu\text{m}$) and $H_2$ ($354.08\,\text{N}$ at $9.25\,\mu\text{m}$) terminated while reaction force was monotonically increasing.
   - These values are **maximum observed forces before termination**, not global peaks.
   - `global_peak_force_convergence = UNRESOLVED_CENSORED`.
   - `full_postpeak_uniform_convergence = UNRESOLVED`.
   - `complete_uniform_fracture_reference = NONE`.
   - The $1\%$ peak force gate is strictly prohibited when the comparator's peak is censored.

---

## 2. Comparison Domains

The loading trajectory is divided into two distinct scientific domains:

```
[==================== DOMAIN A ====================][======== DOMAIN B ========]
0.0 mm                                      0.009250 mm                   0.0100 mm
(Common Pre-Peak / Uniform Domain)            (Adaptive Continuation Domain)
- Valid like-for-like vs H1/H2                - No completed uniform reference
- L2 curve error <= 2%                        - Internal adaptive convergence
- Stiffness, initiation, matched state        - Energy balance & physical stability
```

### Domain A: Common Pre-Peak / Uniform Domain ($0 \le u_1 \le 0.009250\,\text{mm}$)
- Evaluates:
  - $RF_1\text{--}u_1$ normalized $L_2$ error versus $H_1$ (Gate: $\le 2.0\%$)
  - Relative curve area (work) error versus $H_1$
  - Initial elastic shear stiffness $K_0$ (Origin OLS on $0 < u_1 \le 2\,\mu\text{m}$)
  - Damage initiation threshold $u_1(d \ge 0.5)$ (Parity target: $7.75\,\mu\text{m}$)
  - Fully broken threshold $u_1(d \ge 0.9)$
  - Matched-state crack contour and Hausdorff distance at $u_1 = 0.009250\,\text{mm}$

### Domain B: Post-$0.009250\,\text{mm}$ Adaptive Domain ($0.009250 < u_1 \le 0.0100\,\text{mm}$)
- Used for adaptive-run continuation only.
- Because no completed uniform $H_1/H_2$ reference exists here, post-$9.25\,\mu\text{m}$ conclusions must be drawn from:
  1. Internal adaptive convergence between $\text{MM}$ and $\text{PK5}$;
  2. Physical consistency and energy balance ($\text{ETOTAL}$ conservation);
  3. Crack-path stability and localization smoothness;
  4. Consistency with established phase-field literature.
- **Prohibition**: Comparison against fabricated or extrapolated uniform curves is strictly disallowed.

---

## 3. Adaptive Candidates & Roles

| Parameter | MM Candidate (`F43REM4_MM`) | PK5 Candidate (`F43REM4_PK5`) |
| :--- | :--- | :--- |
| **Sizing Method** | `MINIMUM_MAXIMUM` (Solution error $[1.0\%, 5.0\%]$) | `UNIFORM_ERROR` (Target error $5.0\%$, coarsening disallowed) |
| **Physical Elements** | 2,206 ($2,137$ quads, $69$ trias) | 4,894 ($4,766$ quads, $128$ trias) |
| **Physical Nodes** | 2,294 | 4,998 |
| **Layered Elements** | 6,618 | 14,682 |
| **Local $h/l_0$ Range** | $[0.3004, 2.0015]$ | $[0.4500, 2.0000]$ |
| **Crack-Corridor $h/l_0$ (Median)** | $0.8170$ | $0.6033$ |
| **Top-5% Area $h \le l_0/2$** | $3.01\%$ (Top-1%: $4.62\%$) | $10.64\%$ (Top-1%: $12.63\%$) |
| **Scientific Role** | Stronger adaptive localization / lowest global cost | Higher crack-corridor resolution / intermediate cost |

**Physical Formulation Parity**: Both candidates share identical material and phase-field constants ($l_0 = 0.015\,\mathrm{mm}$, $G_c = 1.0\times 10^{-3}\,\mathrm{kN/mm}$, $E = 210\,\mathrm{GPa}$, $\nu = 0.3$) and user-element kinematics (18 SDVs).  
**Selection Policy**: Neither candidate is declared superior prior to full fracture analysis.

---

## 4. Frozen Acceptance Criteria & Decision Logic

An adaptive production result is judged jointly from:
1. **Pre-Peak Global Fidelity**: Matches $H_1$ in Domain A ($L_2 \le 2.0\%$, relative curve area / work error $\le 2.0\%$, inherited from the established $2.0\%$ curve difference gate).
2. **Damage Initiation Parity**: Accurately reproduces initiation threshold $u_1(d \ge 0.5) \approx 7.75\,\mu\text{m}$.
3. **Matched-State Spatial Agreement**: Crack contour at $u_1 = 9.25\,\mu\text{m}$ aligns smoothly with $H_2$ fine-mesh corridor.
4. **Adaptive-to-Adaptive Consistency**: $\text{MM}$ and $\text{PK5}$ trajectories converge internally in post-peak fracture propagation.
5. **Computational Cost Scaling**: Achieves significant CPU efficiency gains relative to uniform $H_2$ ($14,455\,\mathrm{s}$).


---

## 5. Uniform Cost Baselines (Primary Scheduler Evidence)

- **$H_0$ Baseline**: $2,000\,\mathrm{s}$ CPU ($2,004\,\mathrm{s}$ walltime, $N_{\text{phys}}=3930$)
- **$H_1$ Refined**: $5,434\,\mathrm{s}$ CPU ($5,453\,\mathrm{s}$ walltime, $N_{\text{phys}}=12064$, $2.72\times H_0$)
- **$H_2$ Ultra-Fine**: $14,455\,\mathrm{s}$ CPU ($14,501\,\mathrm{s}$ walltime, $N_{\text{phys}}=33852$, $7.23\times H_0$, $2.66\times H_1$)

---

## 6. Output Sufficiency Audit

- `MM_output_sufficiency`: **`PASS`**
- `PK5_output_sufficiency`: **`PASS`**
- Both models define output requests for: Reference Point $U_1$, $RF_1$; User Element state variables $\text{SDV14}$ ($d$), $\text{SDV15}$ (damage status), $\text{SDV16}$ ($\psi_e$); element volume $\text{EVOL}$; whole-model energy balances ($\text{ALLAE}, \text{ALLSE}, \text{ALLWK}, \text{ETOTAL}$); and solver diagnostics.

---

## 7. Governance Boundary

- `authorization_ready_for_adaptive_production`: `false`
- `execution_authorized`: `false`
- `submission_approved`: `false`
- `maximum_jobs_now`: `0`
- `qsub_called`: `false`
- `HPC_submissions`: `0`
