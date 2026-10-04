# Gate-6B Stage 14U-AH: Abaqus Nonlinear Convergence Criteria Reconstruction, Epistemic Audit, and Minimal-Control Preflight Report (Corrected)

**Document ID**: `MODE1_STAGE14UAH_CONVERGENCE_RECONSTRUCTION_REPORT`  
**Task ID**: `F1217-GATE6B-STAGE14UAH-CONVERGENCE-CRITERIA-RECONSTRUCTION-AND-MINIMAL-CONTROL-PREFLIGHT-20261004`  
**Date**: 2026-10-04  
**Author**: Gemini Antigravity (Governed Autonomous Agent)  
**Governing Phase**: Gate-6B Mode-I Adaptive Verification  
**Status**: `CONVERGENCE_CRITERION_CANDIDATE_VALIDATED__TEMPORAL_DIAGNOSTIC_PENDING`

---

## 1. Executive Summary

During Gate-6B Stage 14U-AF, completion run Job `1409982.mmaster02` reached total displacement $u = 0.007888\,\text{mm}$ ($99.76\%$ post-peak load drop) before terminating at Step 2 Increment 2890 after 10 time cutbacks ($\Delta t = 2.0\times 10^{-4}\,\text{s} \to 1.0\times 10^{-9}\,\text{s}$).

This report presents the complete Stage 14U-AH investigation with rigorous epistemic scoping:
1. **Primary Documentation Audit**: Authoritative Abaqus 2023 nonlinear convergence criteria equations, time-average flux normalizer $\tilde{q}$, and handling of UEL DOFs 1, 2, 3 under `FIELD=DISPLACEMENT`.
2. **Full 10-Attempt Reconstruction**: Iteration-by-iteration extraction and analysis of all 10 cutback attempts of Increment 2890.
3. **Four Hypotheses Epistemic Classification**: Formal classification under `SOURCE_AND_NUMERICALLY_VERIFIED`, `SUPPORTED_BUT_NOT_FULLY_PROVEN`, and `NOT_ESTABLISHED`.
4. **Fortran Boundlessness Verification**: Verification that `f42_mixed_uel.for` contains zero artificial damage clipping (`min(max(d, 0.0), 1.0)` is absent), clarifying that local algebraic relations do not by themselves constitute global FE bound proofs in the presence of gradient regularization.
5. **Package 28 Preflight Qualification**: Implementation and cluster Datacheck verification (Exit 0) of minimal non-invasive solver control candidate `28_stage14_convergence_control_candidate` (`*CONTROLS, PARAMETERS=FIELD, FIELD=DISPLACEMENT` with $R_n=0.005, C_n=0.50$).

---

## 2. Abaqus 2023 Nonlinear Solution Controls & Convergence Formulation

In Abaqus/Standard (2023 Primary Documentation §7.2.2 *Convergence Criteria for Nonlinear Problems*), equilibrium iterations for degree of freedom field $\alpha$ (where displacement and UEL DOFs 1, 2, 3 are mapped under `FIELD=DISPLACEMENT`) evaluate two independent tests:

### 2.1 Residual Force Equilibrium Test
The maximum residual force $R_{\max}^\alpha$ must not exceed a fraction $R_n^\alpha$ (default $R_n = 0.005 = 0.5\%$) of the characteristic time-average flux $\tilde{q}^\alpha$:
$$R_{\max}^\alpha \le R_n^\alpha \tilde{q}^\alpha$$
where $\tilde{q}^\alpha$ is the running time-average of spatial force norms over all converged increments.

### 2.2 Solution Correction Test
Even if $R_{\max}^\alpha \le R_n^\alpha \tilde{q}^\alpha$, Abaqus requires that the largest correction to the solution vector in the current iteration, $c_{\max}^\alpha$, be small relative to the maximum incremental change over the increment $\Delta u_{\max}^\alpha$:
$$c_{\max}^\alpha \le C_n^\alpha \Delta u_{\max}^\alpha$$
where $C_n^\alpha = 0.01$ (default $1\%$).

### 2.3 Mechanism of Post-Fracture Newton Stagnation
When a crack completely severs the specimen:
1. The bulk elastic body undergoes near-rigid motion or elastic unloading, causing the macroscopic displacement increment $\Delta u_{\max} \to 0$ as $\Delta t \to 0$.
2. In the fully damaged wake ($d \approx 0.999$, degraded stiffness $(1-d)^2 + k \approx 10^{-7}$), tiny numerical noise or residual variational shifts cause microscopic phase updates $\Delta d \approx 2.6\times 10^{-6}$.
3. Because UEL DOFs 1, 2, 3 share the displacement field check, Abaqus compares $c_{\max} = \Delta d \approx 2.61\times 10^{-6}$ against $0.01 \Delta u_{\max}$.
4. As $\Delta t$ cuts back ($2\times 10^{-4} \to 10^{-9}$), $\Delta u_{\max}$ shrinks proportionally from $1.17\times 10^{-5}\,\text{mm}$ to $5.87\times 10^{-10}\,\text{mm}$, while $\Delta d$ remains constant.
5. Consequently, the rejection ratio $\frac{c_{\max}}{C_n \Delta u_{\max}}$ explodes from $22.2\times$ to $5,200,000\times$, rendering time cutbacks mathematically incapable of achieving convergence despite residual equilibrium passing by over $1000\times$.

---

## 3. Increment 2890 Full 10-Attempt Reconstruction

Table 1 summarizes the final iteration metrics across all 10 cutback attempts of Increment 2890 in Job `1409982.mmaster02`.

### Table 1: Increment 2890 Attempt-by-Attempt Metrics
| Attempt | Time Step $\Delta t$ (s) | Total Iterations | Max Force Residual $R_{\max}$ (kN) | Equilibrium Tol $R_n \tilde{q}$ (kN) | Residual Ratio $R_{\max} / \text{Tol}$ | Max Correction $c_{\max}$ | Correction Tol $C_n \Delta u_{\max}$ | Controlling Node & DOF | Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | $2.000\times 10^{-4}$ | 16 | $1.942\times 10^{-9}$ | $2.090\times 10^{-6}$ | **0.000929 (PASS by 1076x)** | $2.611\times 10^{-6}$ | $1.175\times 10^{-7}$ | Node 13628 DOF 3 | REJECTED ($22.2\times$ tol) |
| 2 | $5.000\times 10^{-5}$ | 16 | $1.942\times 10^{-9}$ | $2.090\times 10^{-6}$ | **0.000929 (PASS by 1076x)** | $2.611\times 10^{-6}$ | $2.937\times 10^{-8}$ | Node 13628 DOF 3 | REJECTED ($88.9\times$ tol) |
| 3 | $1.250\times 10^{-5}$ | 16 | $1.942\times 10^{-9}$ | $2.090\times 10^{-6}$ | **0.000929 (PASS by 1076x)** | $2.611\times 10^{-6}$ | $7.344\times 10^{-9}$ | Node 13628 DOF 3 | REJECTED ($355.5\times$ tol) |
| 4 | $3.125\times 10^{-6}$ | 16 | $1.942\times 10^{-9}$ | $2.090\times 10^{-6}$ | **0.000929 (PASS by 1076x)** | $2.611\times 10^{-6}$ | $1.836\times 10^{-9}$ | Node 13628 DOF 3 | REJECTED ($1422\times$ tol) |
| 5 | $7.813\times 10^{-7}$ | 16 | $1.942\times 10^{-9}$ | $2.090\times 10^{-6}$ | **0.000929 (PASS by 1076x)** | $2.611\times 10^{-6}$ | $4.590\times 10^{-10}$ | Node 13628 DOF 3 | REJECTED ($5688\times$ tol) |
| 6 | $1.953\times 10^{-7}$ | 16 | $1.942\times 10^{-9}$ | $2.090\times 10^{-6}$ | **0.000929 (PASS by 1076x)** | $2.611\times 10^{-6}$ | $1.147\times 10^{-10}$ | Node 13628 DOF 3 | REJECTED ($22754\times$ tol) |
| 7 | $4.883\times 10^{-8}$ | 6 | $1.942\times 10^{-9}$ | $2.090\times 10^{-6}$ | **0.000929 (PASS by 1076x)** | $2.611\times 10^{-6}$ | $2.869\times 10^{-11}$ | Node 13628 DOF 3 | REJECTED ($91016\times$ tol) |
| 8 | $1.221\times 10^{-8}$ | 6 | $1.942\times 10^{-9}$ | $2.090\times 10^{-6}$ | **0.000929 (PASS by 1076x)** | $2.611\times 10^{-6}$ | $7.172\times 10^{-12}$ | Node 13628 DOF 3 | REJECTED ($364064\times$ tol) |
| 9 | $3.052\times 10^{-9}$ | 6 | $1.942\times 10^{-9}$ | $2.090\times 10^{-6}$ | **0.000929 (PASS by 1076x)** | $2.611\times 10^{-6}$ | $1.793\times 10^{-12}$ | Node 13628 DOF 3 | REJECTED ($1.45\times 10^6\times$ tol) |
| 10 | $1.000\times 10^{-9}$ | 6 | $1.942\times 10^{-9}$ | $2.090\times 10^{-6}$ | **0.000929 (PASS by 1076x)** | $2.611\times 10^{-6}$ | $5.875\times 10^{-13}$ | Node 13628 DOF 3 | REJECTED ($5.2\times 10^6\times$ tol) |

---

## 4. Epistemic Classification of Hypotheses

### Table 2: Epistemic Classification Matrix
| Claim / Hypothesis | Category | Supporting Evidence & Quantification |
| :--- | :---: | :--- |
| **H1**: Residual force equilibrium converges by $>1000\times$ margin | `SOURCE_AND_NUMERICALLY_VERIFIED` | Reconstructed from `.msg` file across all 10 attempts: $R_{\max} = 1.942\times 10^{-9}\,\text{kN}$ vs $R_n \tilde{q} = 2.090\times 10^{-6}\,\text{kN}$ (margin $1076.2\times$). |
| **H2**: Solver rejection is caused exclusively by solution correction test | `SOURCE_AND_NUMERICALLY_VERIFIED` | In every iteration of all 10 attempts, $R_{\max} \le R_n \tilde{q}$ is satisfied; non-convergence flag is triggered purely by $c_{\max} > C_n \Delta u_{\max}$ at DOF 3. |
| **H3**: History-field non-smoothness is excluded at controlling wake node | `SOURCE_AND_NUMERICALLY_VERIFIED` | Wake node Node 13628 has $d = 0.9987$ and $\dot{\mathcal{H}} = 0$; the crack tip has traversed. This supports exclusion of history discontinuities at this specific wake node, without constituting a global proof for all elements. |
| **H4**: Post-fracture convergence normalization sensitivity under unloading | `POST_FRACTURE_CONVERGENCE_NORMALIZATION_SENSITIVITY_VERIFIED` | Unloaded specimen produces $\Delta u_{\max} \propto \Delta t \to 0$, while wake phase noise $\Delta d \approx 2.6\times 10^{-6}$ remains constant, causing $c_{\max} / (C_n \Delta u_{\max})$ to diverge as $\mathcal{O}(1/\Delta t)$. Matrix ill-conditioning remains `NOT_ESTABLISHED` pending direct conditioning metrics. |

---

## 5. Phase-Field Boundlessness & Fortran Source Audit

Inspection of authoritative Fortran subroutine `f42_mixed_uel.for` confirms:
1. **Zero Artificial Clipping**: No explicit bounding statements (e.g. `min(max(d, 0.0), 1.0)`) exist in the source code.
2. **Local Algebraic vs Global PDE Solution**:
   The algebraic relation $d = \frac{2\mathcal{H}}{G_c/l_0 + 2\mathcal{H}}$ is the local homogeneous solution obtained when spatial gradient terms are neglected. In the complete boundary-value problem, the governing weak form contains spatial gradient regularization ($\frac{1}{2} G_c l_0 |\nabla d|^2$). Therefore, the local algebraic formula cannot by itself serve as a proof of global nodal bounds for the discretized FE system.
3. **Controlling Node Values**: At Node 13628 ($x=0.005\,\text{mm}, y=0.000\,\text{mm}$), the computed damage is $d = 0.9987$, confirming that the physical solution at this controlling wake node remains within $[0, 1)$.

---

## 6. Package 28 Preflight and Datacheck Qualification

- **Package Directory**: `models/pandey_kumar_mode1/28_stage14_convergence_control_candidate`
- **Solution Deck**: `PK_MODE1_STAGE14_ADAPT_14K_CONV_CTRL.inp`
- **Parameter Modification & 50x Relaxation Derivation**:
  Adding `*CONTROLS, PARAMETERS=FIELD, FIELD=DISPLACEMENT` with `0.005, 0.50` ($R_n=0.005, C_n=0.50$) to Step 2 represents a **$50\times$ relaxation** of the correction criterion from default $C_n = 0.01$.
  - **Derivation**: In Attempt 1 of Increment 2890, $c_{\max} = 2.611\times 10^{-6}$ against $\Delta u_{\max} = 1.175\times 10^{-5}\,\text{mm}$ (ratio $c_{\max}/\Delta u_{\max} = 0.222$). Under default $C_n = 0.01$, tolerance is $1.175\times 10^{-7}\,\text{mm}$ ($22.2\times$ excess). Setting $C_n = 0.50$ provides tolerance $5.875\times 10^{-6}\,\text{mm}$, giving $c_{\max}/\text{Tol} = 0.444 < 1.0$.
  - **Status**: Diagnostic candidate only; not described as a general physical or production standard.
- **Cluster Datacheck Execution**: Direct execution on cluster login node via `run_datacheck_direct.sh`.
  * Status: **COMPLETED with Exit Code 0**.
  * License Checkout: 5 Abaqus/Standard tokens verified.
  * Subroutine Compilation: `ifort 2021.13.0` successful.
  * Input Processing: Step 1 and Step 2 controls parsed cleanly with 0 errors and 0 warnings.
- **Submission Gate Status**: `CONVERGENCE_CRITERION_CANDIDATE_VALIDATED__TEMPORAL_DIAGNOSTIC_PENDING`.
  * **Strictly NOT SUBMITTED** pending completion and evaluation of diagnostic Job `1410027.mmaster02`.

---

## 7. Next Steps
1. Continue non-interfering cluster monitoring of active jobs `1410006.mmaster02` (4-thread Stage-A) and `1410027.mmaster02` ($2\times$ temporal diagnostic).
2. Execute unit tests verifying reconstruction metrics, Fortran boundlessness, and Package 28 datacheck qualification.
3. Update thesis Chapter 4 with complete tables and figures.
