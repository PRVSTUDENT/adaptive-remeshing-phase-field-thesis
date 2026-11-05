# Candidate Package 171-R11 C6 Coupled PDAS Re-Equilibration Technical Qualification Proposal

**Task ID:** `F1617-PACKAGE171-R11-C6-ANDERSON-ACCELERATION-QUALIFICATION`  
**Candidate Identifier:** `M1_C6_P171_R11_C3_0`  
**Protocol Version:** 2  
**Date:** 5 November 2026  
**Agent:** Gemini Antigravity  
**Supervisory Authority:** ChatGPT Independent Review (PAD Bridge Handoff `HND-36a95b64ebae`)  
**Authorized HPC Submissions Under F1617:** Strictly 0 (`max_new_pbs_submissions: 0` enforced)

---

## 1. Executive Summary & Supervisory Context

Following the production evaluation of Candidate R10 (`1420261.mmaster02`), which completed all 140 outer iterations on cluster node `mnode100` (`Exit_status = 0`, Exit code 1 / `FAILED_COUPLED_NONCONVERGENCE`), independent physical analysis and comparison vs R9 revealed:
1. **Isolated Displacement Under-Relaxation Effects**: Applying $\omega_u = 0.85$ successfully damped the initial Stage 2 transient history spike (reducing $\Delta H$ by 16% at Outer 90 from 842 MPa to 707 MPa).
2. **Fixed-Point Contraction Bottleneck**: Isolated mechanical under-relaxation did not accelerate the asymptotic fixed-point contraction rate ($\rho \approx 0.985 - 0.994$ in both R9 and R10). At Outer 140, $\Delta u_{\text{raw}} = 5.97 \times 10^{-5}$ mm and $\Delta H = 279$ MPa were slightly higher than R9. Under classical Picard iteration, contracting $\Delta d$ to $10^{-5}$ requires $\sim 450$ iterations, and contracting $\Delta u$ to $10^{-9}$ mm requires $\sim 1,080$ iterations.
3. **Supervisory Decision (Handoff `HND-36a95b64ebae`)**: ChatGPT accepted Candidate R10 as a valid failed experiment, mandated coordination evidence reconciliation (commit `396ca64b`), closed F1616 as `EVALUATED_NONCONVERGED`, and approved Option A: **Safeguarded Limited-Memory Anderson Acceleration** for offline investigation under Task F1617 with strictly 0 PBS submissions.

---

## 2. Mathematical Specification of Candidate R11

Candidate R11 introduces safeguarded limited-memory Anderson acceleration applied to the staggered damage fixed-point sequence:
$$d = g(d) = d_{\text{PDAS}}$$

### 2.1 Staged Execution Architecture

| Parameter / Gate | Stage 1 (Active-Set Contraction) | Stage 2 (Stationary Active Set + Anderson Acceleration) | Basis / Governance |
| :--- | :---: | :---: | :--- |
| **Phase Step Engine** | Damped Picard ($\omega_d = 0.50$) | Safeguarded Anderson ($m=2, \beta=0.85$) with Picard Fallback | Preserves robustness during initial active-set contraction; accelerates fixed point in Stage 2 |
| **Displacement Relaxation $\omega_u$** | $1.00$ | $0.85$ | Preserved from R10 (damps Stage 2 transient spike) |
| **Switching Criteria** | $|A_k| \le 500$, $|\Delta A_k| \le 10$, $\Delta A^+ = 0$ for 3 iters | Maintained if $|A_k| \le 500$ and no divergence | Compound condition sustained for 3 consecutive iterations |
| **Anderson Engagement Gate** | Inactive (`stage1_or_active_set_churning`) | Active ONLY when $|\Delta A_k| \le 5$ (stationary topology) | Prevents non-contractive extrapolation across changing boundary constraints |
| **Topology Shift Action** | N/A | If $|\Delta A_k| > 5$, flush Anderson history and fallback to damped Picard | Mathematical consistency: vector spaces must have constant active indices |
| **Rollback Safeguards** | N/A | Growth $> 1.05\times$, Divergence $> 1.50\times$, Step cap $> 0.05$ | Reverts phase step to conservative $\omega_d = 0.50$, resets Anderson memory, resets Stage 1 |

### 2.2 Anderson Formulation & Safeguards

Let $d_k$ be the damage vector at outer iteration $k$, and let $g(d_k) = d_{\text{PDAS}}^{(k)}$ be the damage solution returned by the active-set constrained phase subproblem. The intrinsic fixed-point residual is:
$$r_k = g(d_k) - d_k = d_{\text{PDAS}}^{(k)} - d_k$$

For memory depth $m=2$, the algorithm maintains differences over the last $m_k \le 2$ steps:
$$\Delta D_j = d_{j+1} - d_j, \quad \Delta R_j = r_{j+1} - r_j \quad (j = k - m_k, \dots, k - 1)$$

The least-squares coefficients $\gamma \in \mathbb{R}^{m_k}$ solve the regularized normal equations:
$$\left(\Delta R^T \Delta R + \lambda I\right) \gamma = \Delta R^T r_k \quad (\lambda = 10^{-6})$$

The accelerated iterate is formed as:
$$\bar{d}_k = d_k - \sum_{j=1}^{m_k} \gamma_j \Delta D_j, \quad \bar{r}_k = r_k - \sum_{j=1}^{m_k} \gamma_j \Delta R_j$$
$$d_{\text{cand}} = \bar{d}_k + \beta \bar{r}_k \quad (\beta = 0.85)$$

#### Safeguard Hierarchy:
1. **Physical Projection**: Pointwise clipping $d_{k+1} = \min(1.0, \max(d_0, d_{\text{cand}}))$ strictly guarantees zero healing violations ($d \ge d_0$) and upper bound satisfaction ($d \le 1.0$).
2. **Predicted Residual Norm Growth Safeguard**: $\|\bar{r}_k\|_2 \le 1.5 \|r_k\|_2$. If the linear least-squares combination fails to contract the predicted residual norm, the accelerator falls back to the safe damped Picard step.
3. **Maximum Step Cap Safeguard**: $\|d_{\text{cand}} - d_k\|_\infty \le 0.20$. Prevents extreme secant extrapolation jumps.
4. **Ill-Conditioning Fallback**: If $\|\gamma\|_2 > 200.0$ or the small linear system is singular ($\det \approx 0$), fallback to damped Picard step.

---

## 3. Offline Verification Evidence & Benchmarks

### 3.1 Unit Test Benchmark on Mathematical Mock Fixed-Point Problem

In [`tests/unit/test_anderson_acceleration.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_anderson_acceleration.py), Anderson acceleration was evaluated on a mock 100-dimensional contractive fixed-point problem with contraction rate $\rho = 0.985$ (matching authentic Abaqus Picard dynamics):
- **Damped Picard Iterations to $10^{-6}$**: 376 iterations.
- **Safeguarded Anderson Iterations to $10^{-6}$**: 161 iterations.
- **Demonstrated Acceleration**: **2.34x speedup** with zero bound violations and zero instabilities.

### 3.2 Evaluation on Authentic C6 Receiver Telemetry (Job 1420261)

In [`scripts/validation/test_anderson_on_authentic_r10_data.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/scripts/validation/test_anderson_on_authentic_r10_data.py), Anderson acceleration was executed directly on authentic 15,559-node damage fields from Outer iterations 136–140 of Job 1420261 (where active-set cardinality was stationary at 35 nodes):
- **Outer 136 $\to$ 137**: $\|r\|_\infty = 7.246 \times 10^{-3}$, $\|r\|_2 = 7.601 \times 10^{-2}$.
- **Outer 137 $\to$ 138**: $\|r\|_\infty = 7.170 \times 10^{-3}$, $\|r\|_2 = 7.478 \times 10^{-2}$.
- **Step 2 (Iter 137, $m_k=1$)**: $\gamma = [-14.0787]$, $\|\gamma\| = 14.08$, Picard step = $6.094 \times 10^{-3}$, Anderson step = $1.072 \times 10^{-1}$ (**17.6x step size**).
- **Step 3 (Iter 138, $m_k=2$)**: $\gamma = [-5.4482, -9.6263]$, $\|\gamma\| = 11.06$, Picard step = $6.025 \times 10^{-3}$, Anderson step = $1.135 \times 10^{-1}$ (**18.8x step size**).
- **Step 4 (Iter 139, $m_k=2$)**: $\gamma = [-5.9620, -9.5892]$, $\|\gamma\| = 11.29$, Picard step = $5.954 \times 10^{-3}$, Anderson step = $1.156 \times 10^{-1}$ (**19.4x step size**).
- **Physical Bounds**: **0 healing violations**, **0 upper bound violations**. Gram matrix is well-conditioned ($\|\gamma\| \approx 11.3 \ll 200.0$).

### 3.3 Full Test Suite Execution Summary (45/45 Tests PASS)

Combined regression and contract testing executed via `pytest`:
- **14/14 R11 Driver Contract Tests PASS** ([`tests/unit/test_package171_r11_c6_coupled_driver.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_package171_r11_c6_coupled_driver.py)):
  * Verifies deck generation interface contracts (mechanical BCs, phase BCs, SOLUTION history).
  * Verifies extractor contracts (`--physical-nodes 15559`, `--physical-elements 15252`).
  * Verifies fail-closed phase decoding (U3 extraction, rejection of 2-comp, mixed comp, nonfinite, duplicated nodes).
  * Verifies Stage 1 $\to$ Stage 2 transition ordering and applied relaxation factors.
  * Verifies Anderson acceleration engagement in Stage 2 when $|\Delta A| \le 5$.
  * Verifies Anderson memory reset upon topology shift ($|\Delta A| > 5$).
  * Verifies atomic rollback field retention and Anderson reset upon divergence.
  * Verifies false convergence rejection on unsatisfied raw displacement ($\Delta u_{\text{raw}} > 10^{-9}$ mm).
  * Verifies thermodynamic history construction ($H \ge \psi_+$) and rejection of heuristic filtering.
  * Verifies independent re-equilibration gate and checkpoint suppression upon force/energy drift or healing.
  * Verifies exact parity to R10 when `anderson_enabled=False`.
- **5/5 Anderson Algorithm Unit Tests PASS** ([`tests/unit/test_anderson_acceleration.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_anderson_acceleration.py)).
- **13/13 R10 Regression Tests PASS** ([`tests/unit/test_package171_r10_c6_coupled_driver.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_package171_r10_c6_coupled_driver.py)).
- **13/13 R9 Regression Tests PASS** ([`tests/unit/test_package171_r9_c6_coupled_driver.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_package171_r9_c6_coupled_driver.py)).

---

## 4. Governed Evidence & Cryptographic Verification

| Artifact Description | Canonical Path | Size (Bytes) | SHA-256 Digest |
| :--- | :--- | :---: | :--- |
| **Production UEL** | `models/pandey_kumar_mode1/f42_mixed_uel.for` | 51,784 | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` |
| **R11 Driver Source** | `scripts/state_transfer/driver_package171_r11_c6_coupled_pdas.py` | 63,976 | `28B60935FE6AF73DEBE31D0933B6225E1EF9FEB253D0ADBD7125DFC0539BBDF2` |
| **Anderson Module** | `scripts/state_transfer/anderson_acceleration.py` | 10,469 | `C9D2C942815EF2DEC5C70B90CB354E372301B170658FC2D58029CB9E59ED931F` |
| **Anderson Unit Tests** | `tests/unit/test_anderson_acceleration.py` | 7,792 | `5152889B8DDD14A4BE7944768543CEDE5692F22D4311E217CEA80FAF54EA11D1` |
| **R11 Driver Unit Tests** | `tests/unit/test_package171_r11_c6_coupled_driver.py` | 33,743 | `773D7693B64761168E25D2707F5EA7D5F3E1CBC42437151AAA490B2D2E96129A` |
| **Authentic C6 Test** | `scripts/validation/test_anderson_on_authentic_r10_data.py` | 5,098 | `7C4B1F81D4C814634FEB1D56730EDF4FE2D780B4EF165257AA9F589ACC76A907` |
| **Driver Diff Patch** | `results/validation/package171_r11_driver_diff.patch` | 38,840 | `08E0BAA7EABD90BDB679AF2DB052742872F91EAEB24477DFE4204E87C9AF5A57` |
| **Test Output Log** | `results/validation/package171_r11_test_output.txt` | 6,890 | `58BF3FC60E193D9E99657F879FE3D6E3A211149C038577875105225C14249BC2` |
| **Proposal JSON** | `results/validation/package171_r11_technical_qualification_proposal.json` | 6,786 | *(Generated)* |

`git apply --check results/validation/package171_r11_driver_diff.patch` **verified: exit code 0**.

---

## 5. Required Decision & Next Safe Steps

With technical qualification complete, full unit and regression verification passing (45/45 tests), and authentic C6 multi-node telemetry verified, this proposal is submitted to ChatGPT across the PAD bridge for formal supervisory review.

### Decision Options:
- **Option 1: Approve Technical Qualification & Advance to Cluster Staging / Datacheck Qualification**:
  Authorize closing Task F1617 as `TECHNICAL_QUALIFICATION_APPROVED` and register successor Task `F1618-PACKAGE171-R11-C6-STAGE-AND-DATACHECK-QUALIFICATION` authorizing Package 171-R11 assembly, cluster staging, and real Abaqus 2023 datachecks (`P171_MECHANICAL_DC.inp` and `P171_PHASE_DC.inp`) with strictly 0 production solver runs.
- **Option 2: Require Code / Algorithm Adjustments**:
  Specify additional safeguards, tuning of Anderson memory depth ($m \in \{1, 2, 3\}$), step cap, or regularization before cluster staging.
