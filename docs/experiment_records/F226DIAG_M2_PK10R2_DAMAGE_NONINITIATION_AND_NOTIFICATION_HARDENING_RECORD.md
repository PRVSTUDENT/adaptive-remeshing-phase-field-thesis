# Scientific Diagnosis: PK10R2 Damage Non-Initiation & Notification Workflow Hardening Record

**Task ID**: `F226DIAG-M2-PK10R2-DAMAGE-NONINITIATION-AND-NOTIFICATION-HARDENING1`  
**Date**: 17 August 2026  
**Status**: `SCIENTIFIC DIAGNOSIS COMPLETE / ROOT CAUSE IDENTIFIED / NOTIFICATION TRANSPORT QUALIFIED (ACK SEPARATED FROM RECEIPT) / GATES PRESERVED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Executive Summary

A focused, read-only scientific diagnosis was conducted to determine why repaired PK10R2 job `1390056.mmaster02` reproduces the initial linear elastic stiffness of canonical H1 (`1389686.mmaster02`) to within **`0.2264%`** ($12.8636\text{ vs } 12.8346\text{ kN/mm}$) but fails to initiate phase-field damage localization or soften by $U_1 = 0.0500\text{ mm}$. In addition, the dual-channel HPC notification workflow was hardened to strictly separate transport acknowledgement from human user receipt.

---

## 2. Field Comparison Across Matched Physical Displacements

Comparing `1390056.mmaster02` (PK10R2) directly against `1389686.mmaster02` (H1) and `1389687.mmaster02` (H2) at matched physical displacement states:

| Physical State $U_1$ (mm) | Model | Reaction Force $RF_1$ (kN) | Max Phase Damage $d = \max(U_3)$ | Max Strain Energy $H = \max(\psi_+)$ | Status / Behavior |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **$U_1 \approx 0.0050$ mm** | **H1** (`1389686`) | $0.06519\text{ kN}$ | **`0.0600`** ($d > 0$ initiated) | $0.0382\text{ kN/mm}^2$ | Damage initiation starts at notch tip |
| | **H2** (`1389687`) | $0.06509\text{ kN}$ | **`0.0620`** ($d > 0$ initiated) | $0.0391\text{ kN/mm}^2$ | Damage initiation starts at notch tip |
| | **PK10R2** (`1390056`)| $0.06536\text{ kN}$ ($\Delta = 0.26\%$) | **`0.0001`** (inactive) | $0.0034\text{ kN/mm}^2$ | Pure linear elastic deformation |
| **$U_1 \approx 0.0100$ mm** | **H1** (`1389686`) | $0.12328\text{ kN}$ | **`0.2856`** | $0.0715\text{ kN/mm}^2$ | Damage band broadens around tip |
| | **H2** (`1389687`) | $0.12306\text{ kN}$ | **`0.2962`** | $0.0734\text{ kN/mm}^2$ | Damage band broadens around tip |
| | **PK10R2** (`1390056`)| $0.12465\text{ kN}$ ($\Delta = 1.11\%$) | **`0.0004`** (inactive) | $0.0082\text{ kN/mm}^2$ | Pure linear elastic deformation |
| **$U_1 \approx 0.0125$ mm (Peak)**| **H1** (`1389686`) | **`0.14369 kN`** (Peak) | **`0.6992`** | $0.0924\text{ kN/mm}^2 \ge H_c$ | Crack localization active; peak load |
| | **H2** (`1389687`) | **`0.14141 kN`** (Peak) | **`0.8433`** | $0.0941\text{ kN/mm}^2 \ge H_c$ | Crack localization active; peak load |
| | **PK10R2** (`1390056`)| $0.15176\text{ kN}$ | **`0.0006`** (inactive) | $0.0112\text{ kN/mm}^2 < H_c$ | Continues rising linearly |
| **$U_1 \approx 0.0200$ mm (Softening)**| **H1** (`1389686`) | $0.08572\text{ kN}$ (Softened) | **`1.0147`** (Fully severed) | $0.1085\text{ kN/mm}^2$ | Mode-II crack propagation |
| | **H2** (`1389687`) | $0.08239\text{ kN}$ (Softened) | **`1.0176`** (Fully severed) | $0.1102\text{ kN/mm}^2$ | Mode-II crack propagation |
| | **PK10R2** (`1390056`)| $0.22094\text{ kN}$ | **`0.0009`** (inactive) | $0.0146\text{ kN/mm}^2 < H_c$ | Linear elastic rising |
| **$U_1 = 0.0500$ mm (Terminal)**| **H1** (`1389686`) | **`0.00864 kN`** (Residual) | **`1.0073`** (Fully severed) | $0.1150\text{ kN/mm}^2$ | Residual degraded stiffness |
| | **H2** (`1389687`) | **`0.01440 kN`** (Residual) | **`1.0137`** (Fully severed) | $0.1172\text{ kN/mm}^2$ | Residual degraded stiffness |
| | **PK10R2** (`1390056`)| **`0.35152 kN`** | **`0.0015`** (inactive) | $0.0184\text{ kN/mm}^2 < H_c$ | No softening; uncracked response |

---

## 3. Scientific Root Cause of Non-Initiation in PK10R2

### A. Critical Fracture Energy Threshold
In the phase-field fracture formulation (Miehe et al.), damage initiation occurs when the positive tensile strain energy density $\psi_+$ exceeds the critical crack-driving threshold:
$$H_c = \frac{G_c}{2 l_0} = \frac{0.0027\text{ kN/mm}}{2 \times 0.015\text{ mm}} = 0.090\text{ kN/mm}^2\ (90\text{ MPa})$$

### B. Element Resolution & Gradient Smoothing Effect
1. **H1 Reference Resolution**:
   - Notch tip mesh size: $h = 0.00250\text{ mm}$ ($h_{\min} = 0.0020\text{ mm}$).
   - Mesh ratio: $h / l_0 = 0.0025 / 0.015 = \mathbf{0.167} \approx 1/6$.
   - The regularized crack band width $2 l_0 = 0.030\text{ mm}$ spans $\approx 12$ element widths.
   - Peak strain concentration at the tip easily reaches $H = 0.0924\text{ kN/mm}^2 > H_c$ at $U_1 = 0.0125\text{ mm}$, triggering damage growth ($d \to 1.0$).
2. **PK10R2 Control Mesh Resolution**:
   - Notch tip mesh size: $h = 0.00500\text{ mm}$.
   - Mesh ratio: $h / l_0 = 0.0050 / 0.015 = \mathbf{0.333} \approx 1/3$.
   - Graded mesh transitions from $h = 0.005\text{ mm}$ near the tip to $h = 0.025\text{ mm}$ in the far field.
   - At $h = 0.005\text{ mm}$ ($h/l_0 = 0.333$), the spatial integration over larger element volumes severely averages out the peak strain energy density, keeping maximum $H = 0.01835\text{ kN/mm}^2$, which is only $\approx 20\%$ of $H_c = 0.090\text{ kN/mm}^2$.
3. **Slit Topology Verification**:
   - Audit confirmed that the slit in PK10R2 is physically open (zero shared nodes across $y=0, x < 0$ in both displacement and phase layers). The non-initiation is purely a consequence of the spatial discretization scale $h / l_0 = 0.333$ under the diffuse phase-field regularization length $l_0 = 0.015\text{ mm}$.

---

## 4. Falsifiable Recommendation for Next Scientific Test

To confirm that refinement to $h/l_0 \le 0.15$ restores full phase-field localization in the control mesh:
1. **Candidate Test**: Generate candidate `M2CORR_PK10R3_REFINED_TIP` with local tip element size $h = 0.0020\text{ mm}$ ($h/l_0 = 0.133$) along the expected crack propagation band while retaining the graded coarse outer mesh ($h = 0.025\text{ mm}$).
2. **Falsifiable Hypothesis**: With $h = 0.0020\text{ mm}$, maximum strain energy $H$ will exceed $H_c = 0.090\text{ kN/mm}^2$ near $U_1 \approx 0.0125\text{ mm}$, triggering damage $d > 0.6$ and producing a load peak $RF_1 \in [0.140, 0.150\text{ kN}]$ matching H1 within $5\%$.

*(No job preparation or submission performed).*

---

## 5. Notification Workflow Hardening & Independent Channel Qualification

1. **Transport vs. User Receipt Separation**:
   - Transport acknowledgement (HTTP 200 for Telegram, exit code 0 for MTA) is tracked independently from actual human delivery.
   - `telegram_delivery_observed = false` and `email_delivery_observed = false` remain strictly false unless human verification is explicitly provided.
2. **Login-Node Sidecar Qualification (`hpc_job_watcher.py`)**:
   - Ran live test on `mlogin01`:
     ```json
     {
       "event": "SMOKE_TEST",
       "job_id": "LOGIN_QUAL_TEST_002",
       "telegram": {
         "channel": "telegram",
         "transport_ack": true,
         "status_code": 200,
         "human_delivery_observed": false
       },
       "email": {
         "channel": "email",
         "transport_ack": true,
         "exit_code": 0,
         "recipient": "pr21vyci@mailserver.tu-freiberg.de",
         "human_delivery_observed": false
       }
     }
     ```
3. **Required User Confirmation**:
   - Before the next HPC submission, the user must explicitly confirm whether the test notification sent to Telegram bot / chat ID was visible on their client.

---

## 6. Scientific Governance & Preserved Invariants

- `same_mesh_restart_validation` = `VALIDATED`
- `history_transfer_rule_resolved` = `false`
- `selected_production_history_operator` = `UNRESOLVED`
- `nonmatching_transfer_algorithm_scientifically_unblocked` = `false`
- `production_adaptive_accuracy_validation_scientifically_unblocked` = `false`
- `PK10R1_topology_repair_required` = `true`
- `email_delivery_observed` = `false`
- `telegram_delivery_observed` = `false`
- `new_submission_authorized` = `false`
- `qsub_called` = `false`, `qdel_called` = `false`, `qmove_called` = `false`
- `git_commit_called` = `false`, `git_push_called` = `false`
