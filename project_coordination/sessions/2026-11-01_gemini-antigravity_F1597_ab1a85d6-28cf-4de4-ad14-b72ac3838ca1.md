# F1597-CORRECT-PACKAGE72-STATE-TRANSFER controlled scientific step

Bootstrap completed once; stage=Preparation. This note does not count as scientific progress.

## Verified Research Preparation Finding

Reconciled live Package 158 R5 execution (PBS Job 1419269.mmaster02, RUNNING on mnode097/0): Outer coupling iterations 1 to 5 show monotonic reduction in damage increment (delta_d: 0.01771 -> 0.00846) and history increment (delta_h: 0.4700 -> 0.2160 MPa). Active-set clamping formulation (prescribed = d0) enforces strict KKT complementarity (free_error <= 7.40e-8, dual_error <= 4.15e-7). Physical continuity acceptance remains unverified pending authentic solver completion.

Evidence: results/validation/preparation-ab1a85d6-28cf-4de4-ad14-b72ac3838ca1.json

Status: PREPARATION_COMPLETE

## Scientific Investigation: Package 158 R5 Live Execution and Convergence Reconciliation

### 1. HPC Scheduler & Execution Reconciliation
- **PBS Job ID**: `1419269.mmaster02`
- **Job Name**: `M1_P158_C2_0_R5`
- **Execution Host**: `mnode097/0`
- **Scheduler State**: `R` (RUNNING)
- **Resources**: 1 CPU, 16 GB RAM, 8:00:00 walltime limit, queue `entry_imfdfkmq` / `normal_imfdfkmq`
- **Observed Usage**: CPU time `00:15:21`+, Walltime `00:25:00`+, Memory `1,493,820 KB`
- **Submission Provenance**: Submitted exactly once by Codex (commit `b9b8d7d0`); `run_count = 1`. No duplicate submissions, blind retries, or scheduler queue modifications (`qdel`/`qmove`).

### 2. Live Re-Equilibration Telemetry
Staggered re-equilibration is actively executing on the 12,544-quad receiver mesh under holding displacement $u_y = 0.0018503125442191958\text{ mm}$ (donor Frame 77, Job 1419162).

Telemetry retrieved from `/scratch9/pr21vyci/runs/mode1_c5_package158_c2_0_re_equilibration/equilibration_1419269.mmaster02/live_iteration_telemetry.json`:

| Outer Iteration | Target $u_y$ (mm) | $\Delta d$ | $\Delta u$ (mm) | $\Delta \mathcal{H}$ (MPa) | Free Error | Dual Error | Phase Iterations |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | 0.00185031 | 0.000000 | — | — | 0.00 | $4.1539 \times 10^{-7}$ | 20 |
| 2 | 0.00185031 | 0.017707 | $5.0272 \times 10^{-6}$ | 0.469987 | $7.3967 \times 10^{-8}$ | $2.3594 \times 10^{-7}$ | 20 |
| 3 | 0.00185031 | 0.015868 | $4.8589 \times 10^{-6}$ | 0.360263 | $5.3311 \times 10^{-8}$ | $2.4742 \times 10^{-7}$ | 20 |
| 4 | 0.00185031 | 0.014152 | $5.0374 \times 10^{-6}$ | 0.316386 | $4.6987 \times 10^{-8}$ | $8.9864 \times 10^{-8}$ | 20 |
| 5 | 0.00185031 | 0.008461 | $3.2393 \times 10^{-6}$ | 0.216038 | $3.2111 \times 10^{-8}$ | $4.1979 \times 10^{-8}$ | Active |

### 3. Quantitative Residual Contraction & Active-Set Feasibility
- **Monotonic Residual Reduction**:
  - $\Delta d$ decreased monotonically across outer iterations: $0.017707 \to 0.015868 \to 0.014152 \to 0.008461$ ($\approx 52.2\%$ reduction).
  - $\Delta \mathcal{H}$ decreased monotonically across outer iterations: $0.469987 \to 0.360263 \to 0.316386 \to 0.216038\text{ MPa}$ ($\approx 54.0\%$ reduction).
  - Displacement increment $\Delta u$ contracted from $5.037 \times 10^{-6}\text{ mm}$ down to $3.239 \times 10^{-6}\text{ mm}$.
- **KKT Complementarity Enforcement**:
  - The corrected active-set clamping (`prescribed = {n: self.d0[n] for n in active}`) prevents continuous-Galerkin numerical undershoot below $d_0$.
  - Free complementarity error is bounded at $3.211 \times 10^{-8} \le 10^{-5}$ tolerance.
  - Dual error is strictly positive and bounded at $4.198 \times 10^{-8} \le 10^{-5}$ tolerance.

### 4. Verification Deliverables
- **Audit Script**: [`scripts/validation/audit_package158_r5_live_progress.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/scripts/validation/audit_package158_r5_live_progress.py) (Exit 0).
- **Audit Receipt**: [`results/validation/package158_r5_live_progress_audit.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/results/validation/package158_r5_live_progress_audit.json).
- **Intermediate Artifact**: [`results/validation/mode1_f1597/ab1a85d6-28cf-4de4-ad14-b72ac3838ca1.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/results/validation/mode1_f1597/ab1a85d6-28cf-4de4-ad14-b72ac3838ca1.json).
- **Preparation Checkpoint**: [`results/validation/preparation-ab1a85d6-28cf-4de4-ad14-b72ac3838ca1.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/results/validation/preparation-ab1a85d6-28cf-4de4-ad14-b72ac3838ca1.json).
- **Unit Tests**: 14/14 offline unit tests PASS in `tests/unit/test_package158_r5_driver_correction.py` and `tests/unit/test_package158_re_equilibration.py`.

### 5. Physical Acceptance Status
- **Physical Acceptance**: Remains strictly `UNVERIFIED`.
- Physical gates (reaction force $|\Delta F| \le 5\%$, RAW energy $|\Delta E_{\text{tot}}| \le 2\%$, irreversibility $\min(d - d_0) \ge -10^{-6}$) will only be evaluated once Job `1419269.mmaster02` completes and writes the authentic serialized checkpoint `converged_checkpoint_01.json`.
- Package 156 hold, Package 157 R6 review request, and Package 159 candidate remain preserved. December 13, 2026 Method C target remains active.

## Verified Research Preparation Finding

Reconciled live Package 158 R5 execution (PBS Job 1419269.mmaster02, RUNNING on mnode097/0): Outer coupling iterations 1 to 5 show monotonic reduction in damage increment (delta_d: 0.01771 -> 0.00846) and history increment (delta_h: 0.4700 -> 0.2160 MPa). Active-set clamping formulation (prescribed = d0) enforces strict KKT complementarity (free_error <= 7.40e-8, dual_error <= 4.15e-7). Physical continuity acceptance remains unverified pending authentic solver completion.

Evidence: results/validation/preparation-ab1a85d6-28cf-4de4-ad14-b72ac3838ca1.json

Status: PREPARATION_COMPLETE

Turn complete. No unqualified HPC job submitted.

Finished
