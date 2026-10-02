# Scientific Audit: Phase-Field UEL Mathematics, Local Crack-Tip Field Provenance & Persistent Notification Qualification

**Task ID**: `F227AUDIT-M2-PHASEFIELD-UEL-MATHEMATICS-AND-NOTIFICATION-PERSISTENCE1`  
**Date**: 17 August 2026  
**Status**: `SOURCE MATHEMATICS AUDITED / INITIATION THRESHOLD CLAIM CORRECTED / LOCAL GAUSS PROVENANCE QUANTIFIED / NOTIFICATION PERSISTENCE QUALIFIED / GATES PRESERVED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Executive Summary

This task conducted a line-by-line mathematical audit of the Fortran source code `f42_mixed_uel.for` across H1 (`1389686.mmaster02`), H2 (`1389687.mmaster02`), and PK10R2 (`1390056.mmaster02`). The audit:
1. **Refuted the artificial initiation threshold claim**: Verified that the implemented weak form contains no discrete step threshold $H_c$, but rather a smooth continuous algebraic response where $H_0 = \frac{G_c}{2 l_0} = 0.090\text{ kN/mm}^2$ is the half-damage characteristic scale ($d = 0.50$).
2. **Quantified the local crack-tip discretization effect**: Discovered that due to $h = 0.0050\text{ mm}$ ($h/l_0 = 0.333$) in PK10R2 vs $h = 0.0025\text{ mm}$ ($h/l_0 = 0.167$) in H1, the nearest Gauss integration point in PK10R2 is located at $r = 0.001494\text{ mm}$ ($2.00\times$ further from the singular tip than H1's $r = 0.000747\text{ mm}$), and the element area is $4.00\times$ larger, resulting in severe volume averaging of the singular strain gradient.
3. **Removed unscientific acceptance criteria**: Struck the 5% tolerance claim and framed the next refined-tip mesh strictly as a falsifiable diagnostic comparison against canonical H1/H2 trajectories.
4. **Qualified the persistent login-node notification sidecar**: Verified detached daemon operation and state tracking via `qstat -x`, strictly maintaining `telegram_delivery_observed = false` and `email_delivery_observed = false` pending user verification.

---

## 2. Line-by-Line UEL Mathematical Audit (`f42_mixed_uel.for`)

### A. Phase-Field Variational Formulation (JTYPE = 1)
Inspecting lines 162–188 of `f42_mixed_uel.for`:
- Shape function derivatives: $\mathbf{B}_{\text{phase}} = \nabla \mathbf{N}$.
- Weak form tangent matrix:
  $$\mathbf{K}_{\text{phase}} = \int_{\Omega_e} \left[ G_c l_0 \mathbf{B}^T \mathbf{B} + \left( \frac{G_c}{l_0} + 2 H \right) \mathbf{N}^T \mathbf{N} \right] d\Omega$$
- Right-hand side residual:
  $$\mathbf{R}_{\text{phase}} = \int_{\Omega_e} 2 H \mathbf{N}^T d\Omega - \mathbf{K}_{\text{phase}} \mathbf{d}$$
- Homogeneous / Local Strong Form:
  $$- G_c l_0 \nabla^2 d + \left( \frac{G_c}{l_0} + 2 H \right) d = 2 H \implies d = \frac{2 H}{\frac{G_c}{l_0} + 2 H} = \frac{1}{1 + \frac{G_c}{2 l_0 H}}$$

**Mathematical Finding**:
- The expression $H_0 = \frac{G_c}{2 l_0}$ ($0.090\text{ kN/mm}^2$ for $G_c = 0.0027\text{ kN/mm}, l_0 = 0.015\text{ mm}$) is the **half-damage scale** ($d(H_0) = 0.50$), NOT a discrete Heaviside threshold.
- For any $H > 0$, damage evolves continuously:
  - At $H = 0.010\text{ kN/mm}^2$: $d = \frac{2(0.010)}{0.180 + 2(0.010)} = \frac{0.020}{0.200} = \mathbf{0.100}$, yielding degradation $g(d) = (1-0.10)^2 = 0.81$.
  - At $H = 0.0018\text{ kN/mm}^2$ (as in PK10R2): $d = \frac{0.0036}{0.1836} = \mathbf{0.0196}$, yielding $g(d) \approx (0.98)^2 \approx 0.96$ (imperceptible global softening).

### B. Mechanical Degradation & History Update (JTYPE = 2)
Inspecting lines 313–349 of `f42_mixed_uel.for`:
- Tensile strain energy:
  $$\psi_+ = \text{POS\_M} = \frac{1}{2} \lambda \langle \text{tr} \boldsymbol{\varepsilon} \rangle_+^2 + \mu \left( \varepsilon_{11}^2 + \varepsilon_{22}^2 + 2 \varepsilon_{12}^2 \right)$$
- History variable (strictly monotonic / irreversible):
  $$H(t) = \max_{\tau \le t} \psi_+(\tau)$$
- Stress degradation:
  $$\boldsymbol{\sigma} = \left[ (1 - d)^2 + k_{\text{res}} \right] \frac{\partial \psi_+}{\partial \boldsymbol{\varepsilon}} + \frac{\partial \psi_-}{\partial \boldsymbol{\varepsilon}}, \quad k_{\text{res}} = 1.0 \times 10^{-7}$$

---

## 3. Local Crack-Tip Field Provenance & Discretization Analysis

A rigorous extraction of node coordinates, Gauss integration points, and local field tensors near the notch tip $(0,0)$ revealed:

| Metric / Attribute | Canonical H1 Reference (`1389686`) | PK10R2 Control Mesh (`1390056`) | Ratio / Difference |
| :--- | :--- | :--- | :--- |
| **Notch Tip Element Size ($h$)** | $0.00250\text{ mm}$ ($h_{\min} = 0.0020\text{ mm}$) | $0.00500\text{ mm}$ | **`2.00x coarser`** |
| **Regularization Ratio ($h / l_0$)** | $0.0025 / 0.015 = \mathbf{0.167} \approx 1/6$ | $0.0050 / 0.015 = \mathbf{0.333} \approx 1/3$ | **`2.00x under-resolved`** |
| **Nearest Gauss Point to Tip ($r_{\min}$)**| **`0.000747 mm`** | **`0.001494 mm`** | **`2.00x further from singularity`** |
| **Gauss Point Coordinates (GP 1)** | $(0.000528, 0.000528)\text{ mm}$ | $(0.001057, 0.001057)\text{ mm}$ | Physical location offset |
| **Element Quadrilateral Area ($h^2$)** | $6.25 \times 10^{-6}\text{ mm}^2$ | $2.50 \times 10^{-5}\text{ mm}^2$ | **`4.00x volume averaging`** |
| **Slit Shared Nodes across $y=0$** | $0$ (Physically open) | $0$ (Physically open) | Identical topology |
| **Jacobian Determinant ($\det \mathbf{J}$)** | $> 0$ (Positive everywhere) | $> 0$ (Positive everywhere) | Identical regularity |
| **Phase DOF Boundary Condition** | Free (Neumann $\nabla d \cdot \mathbf{n} = 0$) | Free (Neumann $\nabla d \cdot \mathbf{n} = 0$) | Identical BCs |
| **Displacement Coupling** | Rigid $U_1$ via `*EQUATION` | Rigid $U_1$ via `*EQUATION` | Identical BCs |

### Theoretical Provenance Conclusion
In linear elastic fracture mechanics under pure Mode-II shear, the singular strain field scales as $\gamma(r) \sim \frac{K_{II}}{\sqrt{2 \pi r}}$, so the strain energy density scales as $\psi_+(r) \sim \frac{1}{r}$. 
1. In PK10R2, the nearest sampling point is $2\times$ further from the notch singularity ($r = 1.494\ \mu\text{m}$ vs $0.747\ \mu\text{m}$).
2. The bilinear interpolation over a $4\times$ larger element area smooths the steep strain gradient.
3. Consequently, at $U_1 = 0.0125\text{ mm}$, maximum sampled $\psi_+$ is only $0.0112\text{ kN/mm}^2$ in PK10R2 (yielding $d \approx 0.0006$), compared to $0.0924\text{ kN/mm}^2$ in H1 (yielding $d = 0.6992$).

---

## 4. Falsifiable Scientific Test Definition

- **Refined Diagnostic Candidate**: `M2CORR_PK10R3_REFINED_TIP`
  - Mesh: Local refinement to $h = 0.0020\text{ mm}$ ($h/l_0 = 0.133 \le 0.15$) along the expected crack band $(x \in [0.0, 0.5], y \in [-0.05, 0.05])$, while preserving the graded outer mesh ($h = 0.025\text{ mm}$).
  - Scientific Test: Directly compare extracted $RF_1 - U_1$ trajectory, $d(x,y)$, and $H(x,y)$ against canonical H1/H2.
  - Falsifiable Hypothesis: If local refinement to $h = 0.0020\text{ mm}$ places Gauss points within $r \le 0.0006\text{ mm}$ of the tip and reduces volume averaging by $6.25\times$, local strain energy will reach $H \approx 0.09\text{ kN/mm}^2$, producing damage localization ($d > 0.5$) and load peak/softening. If it fails, non-initiation must be attributed to an undiscovered formulation inconsistency rather than spatial discretization.
- *(No job was prepared or submitted).*

---

## 5. Notification Sidecar Persistence & Qualification

1. **Persistence & Detached Operation**:
   - `scripts/hpc/notifications/hpc_job_watcher.py` supports background/daemon mode with PID tracking and polling of `qstat -x <JOB_ID>`.
   - Dispatches SUBMITTED, STARTED, COMPLETED, FAILED, and TERMINATED lifecycle notifications from the network-capable login node (`mlogin01`).
2. **Live Non-Submitting Qualification**:
   ```json
   {
     "event": "PERSISTENT_QUAL_TEST",
     "job_id": "LOGIN_PERSIST_TEST_003",
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
3. **Delivery Invariants**:
   - `telegram_delivery_observed = false`
   - `email_delivery_observed = false`
   - (Awaiting human client verification before future submissions).

---

## 6. Scientific Governance & Preserved Invariants

```text
same_mesh_restart_validation = VALIDATED
history_transfer_rule_resolved = false
selected_production_history_operator = UNRESOLVED
nonmatching_transfer_algorithm_scientifically_unblocked = false
production_adaptive_accuracy_validation_scientifically_unblocked = false
PK10R1_topology_repair_required = true
email_delivery_observed = false
telegram_delivery_observed = false
```

```text
new_submission_authorized = false
qsub_called = false
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```
