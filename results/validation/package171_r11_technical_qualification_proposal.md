# Candidate Package 171-R11 C6 Coupled PDAS Re-Equilibration Technical Qualification Proposal

**Task ID:** `F1617-PACKAGE171-R11-C6-ANDERSON-ACCELERATION-QUALIFICATION`  
**Candidate Identifier:** `M1_C6_P171_R11_C3_0`  
**Protocol Version:** 2  
**Date:** 5 November 2026  
**Agent:** Gemini Antigravity  
**Supervisory Authority:** ChatGPT Independent Technical Review (PAD Bridge Handoff `HND-36a95b64ebae` & Directive `HND-52ff442365c2`)  
**Authorized HPC Submissions Under F1617:** Strictly 0 (`max_new_pbs_submissions: 0` enforced)

---

## 1. Executive Summary & Supervisory Context

Following the initial submission of Candidate R11 for supervisor review (`HND-52ff442365c2`), ChatGPT issued a binding directive:
`DECISION: REJECT R11 FOR STAGING — CORRECT AND REQUALIFY THE ANDERSON SAFEGUARDS OFFLINE.`

Four specific blocking deficiencies were identified:
1. **Blocker 1 (Oversized Step vs Catastrophic Rollback Limit)**: Anderson candidates reached $\sim 0.11$, but production driver's catastrophic rollback threshold is $0.05$. Under the uncorrected algorithm, accelerated proposals would trigger catastrophic rollback to Stage 1.
2. **Blocker 2 (Active-Set Topology Memory Reset)**: When $|\Delta A| > 5$, the driver branched to Picard without clearing secant memory, allowing stale differences to survive large constraint changes.
3. **Blocker 3 (Authentic Residual Validation & Fail-Closed Guard)**: Validation script used consecutive endpoint differences rather than intrinsic residual $r_k = d_{\text{PDAS}}(k) - d_k$, lacked transferred $d_0$ bounds, lacked verified GitHub endpoint files, and failed open on missing files.
4. **Blocker 4 (Duplicated Production Algorithm)**: Production driver embedded a duplicate `AndersonAccelerator` class instead of importing the canonical module.

Under Task F1617, all four blockers have been completely remediated and verified through 51/51 passing tests with zero PBS submissions.

---

## 2. Four Blocker Remediations

### Remediation of Blocker 1: Step Norm Cap & Safe Picard Fallback
- **Preserved Qualified Catastrophic Threshold**: The production driver retains $0.05$ as the hard catastrophic rollback threshold.
- **Explicit Safety Margin**: `max_step_cap` is set to $0.045$ in both `AndersonAccelerator` and driver, establishing a $0.005$ safety margin below the $0.05$ catastrophic threshold.
- **Safe Fallback**: When an accelerated candidate proposes a step $\|d_{\text{cand}} - d_k\|_\infty > 0.045$, the accelerator rejects it (`reason='oversized_step'`), falls back to the safe damped Picard step ($\|d_{\text{Picard}} - d_k\|_\infty \le 0.045$), and prevents triggering the driver's catastrophic rollback guard.
- **Telemetry Disambiguation**: Telemetry now explicitly logs `anderson_proposed_step`, `anderson_accepted_step`, and `anderson_picard_step`.
- **Regression Tests**: Verified in [`tests/unit/test_anderson_acceleration.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_anderson_acceleration.py#L206) and driver test [`test_production_path_oversized_step_rejected_with_safe_fallback`](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_package171_r11_c6_coupled_driver.py#L716).

### Remediation of Blocker 2: Active-Set Topology Memory Reset
- **Enforced Topology Flush**: In [`driver_package171_r11_c6_coupled_pdas.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/scripts/state_transfer/driver_package171_r11_c6_coupled_pdas.py#L773), whenever active-set symmetric difference exceeds threshold ($|\Delta A| > 5$) or when $\text{stage} \ne 2$, `self.accelerator.reset()` is invoked immediately, flushing all secant vectors ($\Delta D, \Delta R$).
- **Lifecycle Sequence Verified**: Tested and verified the complete sequence: `acceleration active -> topology change -> memory cleared -> new history accumulated -> acceleration resumed` ([`test_production_path_topology_reset_and_reentry_sequence`](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_package171_r11_c6_coupled_driver.py#L761)).

### Remediation of Blocker 3: Authentic Intrinsic Residual Replay & Fail-Closed Guard
- **Intrinsic Residual Equivalence**: Reconstructed exact same-iteration raw PDAS vectors:
  $$d_{\text{PDAS}}(k) = d_k + \frac{d_{k+1} - d_k}{\omega_d} \quad (\omega_d = 0.85)$$
  $$r_k = d_{\text{PDAS}}(k) - d_k = \frac{d_{k+1} - d_k}{\omega_d}$$
- **Authentic Lower Bounds**: Loaded transferred lower bounds $d_0$ across all 15,559 nodes from `models/pandey_kumar_mode1/171_c6_package171_r10_c3_0_adaptive_reequilibration/nodal_phase_field_initial.csv`.
- **Governed GitHub Evidence**: Committed authentic endpoint files `endpoint_o136.json` through `endpoint_o140.json` (Job 1420261) to the repository.
- **Fail-Closed Guards**: Missing files immediately raise `FileNotFoundError` (verified by unit test [`test_missing_authentic_evidence_fails_closed`](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_package171_r11_c6_coupled_driver.py#L860)).
- **Illustrative Classification**: Script explicitly classified as an illustrative offline fixed-point study on C6 mesh geometry. Replay demonstrates that oversized proposed steps ($0.113 - 0.120 > 0.045$) are safely rejected and fall back to Picard ($0.0071 \le 0.045$), with zero healing violations ($d \ge d_0$) and zero upper bound violations ($d \le 1.0$) across all 15,559 nodes.

### Remediation of Blocker 4: Single Canonical Algorithm
- **Eliminated Code Duplication**: Removed the duplicate inline `AndersonAccelerator` class from `driver_package171_r11_c6_coupled_pdas.py`.
- **Shared Canonical Module**: Both the production driver and all unit test suites import from `scripts.state_transfer.anderson_acceleration`.
- **Comprehensive Parity**: Verified exact parity to R10 when `anderson_enabled=False` across multi-iteration production solves ([`test_production_path_exact_equivalence_to_r10_when_anderson_disabled`](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_package171_r11_c6_coupled_driver.py#L639)).

---

## 3. Mathematical Specification of Candidate R11

Candidate R11 introduces safeguarded limited-memory Anderson acceleration applied to the staggered damage fixed-point sequence:
$$d = g(d) = d_{\text{PDAS}}$$

### 3.1 Staged Execution Architecture

| Parameter / Gate | Stage 1 (Active-Set Contraction) | Stage 2 (Stationary Active Set + Anderson Acceleration) | Basis / Governance |
| :--- | :---: | :---: | :--- |
| **Phase Step Engine** | Damped Picard ($\omega_d = 0.50$) | Safeguarded Anderson ($m=2, \beta=0.85, \text{cap}=0.045$) with Picard Fallback | Preserves robustness during initial active-set contraction; accelerates fixed point in Stage 2 |
| **Displacement Relaxation $\omega_u$** | $1.00$ | $0.85$ | Preserved from R10 (damps Stage 2 transient spike) |
| **Switching Criteria** | $|A_k| \le 500$, $|\Delta A_k| \le 10$, $\Delta A^+ = 0$ for 3 iters | Maintained if $|A_k| \le 500$ and no divergence | Compound condition sustained for 3 consecutive iterations |
| **Anderson Engagement Gate** | Inactive (`stage1`) | Active ONLY when $|\Delta A_k| \le 5$ (stationary topology) | Prevents non-contractive extrapolation across changing boundary constraints |
| **Topology Shift Action** | N/A | If $|\Delta A_k| > 5$, flush Anderson history and fallback to damped Picard | Mathematical consistency: vector spaces must have constant active indices |
| **Rollback Safeguards** | N/A | Growth $> 1.05\times$, Divergence $> 1.50\times$, Step cap $> 0.05$ | Reverts phase step to conservative $\omega_d = 0.50$, resets Anderson memory, resets Stage 1 |

### 3.2 Anderson Formulation & Safeguard Hierarchy

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
3. **Oversized Step Rejection Safeguard**: $\|d_{\text{cand}} - d_k\|_\infty \le 0.045$. If proposed step exceeds $0.045$, fall back safely to damped Picard ($\le 0.045$), preserving safety margin below the $0.05$ catastrophic rollback threshold.
4. **Conditioning Safeguard**: If $\|\gamma\|_2 > 200.0$ or the small linear system is singular ($\det \approx 0$), fallback to damped Picard step.
5. **Topology Reset Safeguard**: Immediate memory flush upon $|\Delta A| > 5$ or $\text{stage} \ne 2$.

---

## 4. Full Test Suite Execution Summary (51/51 Tests PASS)

Combined regression and contract testing executed via `pytest`:
- **18/18 R11 Driver Contract Tests PASS** ([`tests/unit/test_package171_r11_c6_coupled_driver.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_package171_r11_c6_coupled_driver.py)):
  * Verifies deck generation interface contracts (mechanical BCs, phase BCs, SOLUTION history).
  * Verifies extractor contracts (`--physical-nodes 15559`, `--physical-elements 15252`).
  * Verifies fail-closed phase decoding (U3 extraction, rejection of 2-comp, mixed comp, nonfinite, duplicated nodes).
  * Verifies Stage 1 $\to$ Stage 2 transition ordering and applied relaxation factors.
  * Verifies Anderson acceleration engagement in Stage 2 when $|\Delta A| \le 5$.
  * Verifies Anderson memory reset upon topology shift ($|\Delta A| > 5$) and re-entry sequence.
  * Verifies oversized Anderson step rejection ($> 0.045$) with safe Picard fallback preventing catastrophic rollback ($< 0.05$).
  * Verifies atomic rollback field retention and Anderson reset upon divergence.
  * Verifies false convergence rejection on unsatisfied raw displacement ($\Delta u_{\text{raw}} > 10^{-9}$ mm).
  * Verifies thermodynamic history construction ($H \ge \psi_+$) and rejection of heuristic filtering.
  * Verifies independent re-equilibration gate and checkpoint suppression upon force/energy drift or healing.
  * Verifies exact parity to R10 when `anderson_enabled=False`.
  * Verifies missing authentic evidence fails closed with `FileNotFoundError`.
  * Verifies intrinsic residual construction $r_k = d_{\text{PDAS}} - d_k$.
- **6/6 Anderson Algorithm Unit Tests PASS** ([`tests/unit/test_anderson_acceleration.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_anderson_acceleration.py)):
  * Small system solver accuracy (1x1, 2x2, 3x3).
  * Physical projection bounds ($d \in [d_0, 1.0]$).
  * Active set change memory reset.
  * Convergence acceleration on mock slow-contracting problem ($\rho = 0.985$, 2.34x speedup).
  * Gamma cap and ill-conditioning fallback.
  * Oversized step rejection with safe Picard fallback.
- **13/13 R10 Regression Tests PASS** ([`tests/unit/test_package171_r10_c6_coupled_driver.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_package171_r10_c6_coupled_driver.py)).
- **13/13 R9 Regression Tests PASS** ([`tests/unit/test_package171_r9_c6_coupled_driver.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_package171_r9_c6_coupled_driver.py)).
- **1/1 Authentic C6 Replay PASS** ([`scripts/validation/test_anderson_on_authentic_r10_data.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/scripts/validation/test_anderson_on_authentic_r10_data.py)).

---

## 5. Governed Evidence & Cryptographic Verification

| Artifact Description | Canonical Path | Size (Bytes) | SHA-256 Digest |
| :--- | :--- | :---: | :--- |
| **Production UEL** | `models/pandey_kumar_mode1/f42_mixed_uel.for` | 51,784 | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` |
| **R11 Driver Source** | `scripts/state_transfer/driver_package171_r11_c6_coupled_pdas.py` | 57,529 | `0B3E47ADF1C6F619A83EEC817041D523BFDEA783C87E600DB5B3F74E124A0BDA` |
| **Anderson Module** | `scripts/state_transfer/anderson_acceleration.py` | 12,046 | `57D004E81F97B504FD185C22AF1EB1F9176A9BEFBB6D485B0D1056AE4A44A3EE` |
| **Anderson Unit Tests** | `tests/unit/test_anderson_acceleration.py` | 9,350 | `3F26025B9C9BB233657A6E46AAF4A16A7DF53D7CBDF3E8AE64015920015A1C7F` |
| **R11 Driver Unit Tests** | `tests/unit/test_package171_r11_c6_coupled_driver.py` | 41,684 | `D4D87C43F5BF29EBB0942F5D228BED9B71CD1D1DE4F0858FD4CF3B1FAB974352` |
| **Authentic C6 Test** | `scripts/validation/test_anderson_on_authentic_r10_data.py` | 6,261 | `CCADBDF7E8117DEC48FFA53E461B881309AD337273163D0834F41836F680D00E` |
| **Driver Diff Patch** | `results/validation/package171_r11_driver_diff.patch` | 33,135 | `89C5FC094CFF23931BD3A070282738FD61B15C9DC3B288F55611556259F3E608` |
| **Test Output Log** | `results/validation/package171_r11_test_output.txt` | 15,474 | `40C93D28B483434484F8E1EF315D8884C8AFCFF7F0B30BD20BBD7C53B2E60C56` |
| **Endpoint Outer 136** | `models/pandey_kumar_mode1/171_c6_package171_r10_c3_0_adaptive_reequilibration/evidence/1420261.mmaster02/endpoint_o136.json` | 1,185,198 | `093F0678A377CDD27D773AC057DDFAC359B716167524AAA5B03FF0E2B966F032` |
| **Endpoint Outer 137** | `models/pandey_kumar_mode1/171_c6_package171_r10_c3_0_adaptive_reequilibration/evidence/1420261.mmaster02/endpoint_o137.json` | 1,185,213 | `CF7AD99A73CA9A50BE433F4634B106EAFDE56B34805FDD424413F441734D7C44` |
| **Endpoint Outer 138** | `models/pandey_kumar_mode1/171_c6_package171_r10_c3_0_adaptive_reequilibration/evidence/1420261.mmaster02/endpoint_o138.json` | 1,185,189 | `DEDA944D06AF692A7D47EBD0281C06A2C2B4051928E4828620D1A453F2FB3C9D` |
| **Endpoint Outer 139** | `models/pandey_kumar_mode1/171_c6_package171_r10_c3_0_adaptive_reequilibration/evidence/1420261.mmaster02/endpoint_o139.json` | 1,185,131 | `990124A6A6427E2788C04FA0A254F23200D6D9C4F2D5D3167C388D6295D3894F` |
| **Endpoint Outer 140** | `models/pandey_kumar_mode1/171_c6_package171_r10_c3_0_adaptive_reequilibration/evidence/1420261.mmaster02/endpoint_o140.json` | 1,185,209 | `B96331D134E6A7CCD054D2A59D41FF93A39BDFACB6545C455AD274D1D5731EF0` |

`git apply --check results/validation/package171_r11_driver_diff.patch` **verified: exit code 0**.

---

## 6. Required Decision & Next Safe Steps

With technical qualification complete, all four blockers resolved, 51/51 tests passing, authentic C6 telemetry verified, and zero PBS submissions maintained, this revised proposal is submitted to ChatGPT across the PAD bridge for formal supervisory re-review.

### Decision Options:
- **Option 1: Approve Technical Qualification & Advance to Cluster Staging / Datacheck Qualification**:
  Authorize closing Task F1617 as `TECHNICAL_QUALIFICATION_APPROVED` and register successor Task `F1618-PACKAGE171-R11-C6-STAGE-AND-DATACHECK-QUALIFICATION` authorizing Package 171-R11 assembly, cluster staging, and real Abaqus 2023 datachecks (`P171_MECHANICAL_DC.inp` and `P171_PHASE_DC.inp`) with strictly 0 production solver runs.
- **Option 2: Require Code / Algorithm Adjustments**:
  Specify additional safeguards, tuning of Anderson memory depth ($m \in \{1, 2, 3\}$), step cap, or regularization before cluster staging.
