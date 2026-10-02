# Submission Record: F128SUB Corrected Virgin Baselines Batch

- **Task ID**: `F128SUB-M2-CORRECTED-VIRGIN-BASELINES-SUBMIT1`
- **Date**: 2026-08-15
- **Agent**: `gemini-antigravity`
- **Authorization**: Explicit human authorization for exactly 2 guarded baseline submissions.
- **Qualified UEL**: `f42_mixed_uel_transactional.for` (`SHA256 = e3b373253069f9b36085ee426568ce002a7f195a4d5356c6c6a5549c97767138`)

---

## 1. Submitted Jobs Overview

| Job Name | PBS Job ID | Status | Mesh Topology | Physical Element Count | Manifest SHA256 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`M2CORR_H2_FULL_U050`** | `1389683.mmaster02` | `RUNNING` | Exact H2 Reference | **33,852** | `fc0cab9b84b53b405eba17a3eea2a68b8cc5703cc1930c6b0fd4b42e5b7093a2` |
| **`M2CORR_PK10R1_CONTINUOUS_U050`** | `1389684.mmaster02` | `QUEUED` | Exact PK10R1 Control | **9,612** | `352cdf03c9f323be5030b42ce0cfba5c0d70eee49be1cce6b510510deadbb793` |

---

## 2. Guarded Submission Checklist (Pre-Flight Verification)

- [x] **Manifest Hash Match**: Verified before submission via guarded wrapper script `guarded_submit_*.sh`.
- [x] **UEL SHA256 Match**: Verified `e3b373253069f9b36085ee426568ce002a7f195a4d5356c6c6a5549c97767138` on cluster before submission.
- [x] **Dual-Channel Notifications**: Sourced `job_notifications.sh`, verified Telegram API connectivity (`api.telegram.org` HTTP 200 OK), issued `notify_submitted` for both jobs.
- [x] **Resource Directives**: `1 CPU / 16 GB / 24:00:00 / entry_imfdfkmq` confirmed in PBS header.
- [x] **Scheduler Boundary**: Maximum 2 submissions executed; maximum 2 simultaneous jobs limit respected; `automatic_retry = false`.

---

## 3. Joint Scientific Review Criteria (Post-Execution Acceptance Criteria)

Upon completion of both baseline jobs, the joint scientific evaluation will assess:

1. **Un-degraded Strain Energy Consistency**:
   - Verify that history variable $H$ at all integration points satisfies $H(\mathbf{x}, t) = \max_{\tau \le t} \psi_+(\boldsymbol{\varepsilon}(\mathbf{x}, \tau))$ without $g(d)$ degradation.
   - Confirm `fraction_POS_M_gt_H = 0.000000` (or within $10^{-4}\text{ kN/mm}^2$ tolerance) across all frames.

2. **Mesh Topology Force Convergence Ratio**:
   - Compute the peak reaction force ratio $\text{Ratio}_{\text{peak}} = RF_{1,\max}(\text{PK10R1}) / RF_{1,\max}(\text{H2})$.
   - Evaluate whether the corrected PK10R1 continuous curve closely matches the corrected uniform H2 curve across all loading stages $U_1 \in [0.00, 0.05]\text{ mm}$.

3. **Phase-Field Residual Norm Equilibrium**:
   - Verify $R_{\text{phase}, L2} \le 10^{-3}\text{ kN}$ at all accepted increments.

4. **Downstream Unblocking Condition**:
   - Restart and nonmatching-remesh validation remain **strictly blocked** until both baselines finish and pass joint scientific review.
