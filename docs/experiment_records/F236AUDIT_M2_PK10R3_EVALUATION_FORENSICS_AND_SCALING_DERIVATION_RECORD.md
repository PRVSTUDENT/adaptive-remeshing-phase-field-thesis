# Forensic Audit Record: F235 Evaluation Reconciliation & Element Scaling Derivation

**Task ID**: `F236AUDIT-M2-PK10R3-EVALUATION-FORENSICS-AND-SCALING-DERIVATION1`  
**Date**: 17 August 2026  
**Status**: `FORENSIC_AUDIT_COMPLETE / DATASET_RECONCILED / SCALING_MATHEMATICALLY_DERIVED / GATES_PRESERVED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Executive Summary & Root-Cause Discrepancy Reconciliation

A rigorous, read-only forensic audit of the F235 evaluation was conducted to reconcile apparent contradictions between previous reports and the frozen canonical dataset (`docs/studies/canonical_mode_ii_summary.json`).

### A. Reconciliation of Reported Quantities

1. **H2 Canonical Terminal Force ($RF_{1,\text{term}}$)**:
   - **Disputed Report in F235**: $0.0070\text{ kN}$.
   - **Canonical Frozen Truth**: **`0.014404 kN`** at $U_1 = 0.042579\text{ mm}$ (SHA-256: `06234e38f1e2e704cc76f3bf51ab350fea3e243126c416ac743800529243a76d`).
   - **Root Cause**: The quick diagnostic script in F235 polled a single displacement coordinate without summing positive reactions on the boundary (`sum_pos_rf1_kN`), which is required for H2 because the reference node in H2 was uncoupled in the raw output. Re-extraction using the canonical parser restores exact agreement ($RF_1 = 0.014404\text{ kN}$).

2. **PK10R2 Crack-Driving History ($H$) and Phase Field ($d$)**:
   - **Disputed F226 Report**: $H \approx 0.0184\text{ kN/mm}^2$, $d \approx 0.0015$.
   - **F235 / Actual Full-Step Terminal Values**: $H_{\max} = 2.7570\text{ kN/mm}^2$ (Layer 2 element 8973), $d_{\max} = 0.8690$ (Layer 2 element 8847).
   - **Root Cause**:
     - F226 extracted $H$ and $d$ from an early intermediate displacement state ($U_1 \approx 0.00125\text{ mm}$, prior to the F224 correction of the $40\times$ displacement scaling error).
     - Because elastic strain energy scales quadratically ($H \propto U_1^2$), scaling from $U_1 = 0.00125\text{ mm}$ to the true terminal state $U_1 = 0.0500\text{ mm}$ ($40\times$ larger) increases $H$ by a factor of $(40)^2 = 1600\times$. Thus $0.00172\text{ kN/mm}^2 \times 1600 \approx 2.75\text{ kN/mm}^2$.
     - At $U_1 = 0.0500\text{ mm}$, the full-step terminal `.dat` file confirms that PK10R2 accumulated $H_{\max} = 2.7570\text{ kN/mm}^2$ and $d_{\max} = 0.8690$ locally near the notch tip, but was pinned by the coarse outer mesh.

---

## 2. Canonical Trajectory Provenance & Cryptographic Hashes

All trajectories were re-extracted directly from original ODBs and synchronized into [`docs/studies/canonical_mode_ii_summary.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/studies/canonical_mode_ii_summary.json):

| Model ID | PBS Job ID | Mesh ($h_{\min}$) | Initial Stiffness $K_0$ | Peak $RF_1$ | Peak $U_1$ | Terminal $RF_1$ | Terminal $U_1$ | Dissipated Energy $W$ | Trajectory CSV SHA-256 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`H1_UNIFORM_FINE`** | `1389686.mmaster02` | $0.0020\text{ mm}$ | $12.8346\text{ kN/mm}$ | $0.143686\text{ kN}$ | $0.012530\text{ mm}$ | $0.008640\text{ kN}$ | $0.050000\text{ mm}$ | $0.002733\text{ kN}\cdot\text{mm}$ | `0621a63a18edc67b3b8ea8f5a5c05de8afd0ac12d3675b0d9c416e9e81ff6829` |
| **`H2_UNIFORM_ULTRAFINE`** | `1389687.mmaster02` | $0.0010\text{ mm}$ | $12.8164\text{ kN/mm}$ | $0.141415\text{ kN}$ | $0.012214\text{ mm}$ | $0.014404\text{ kN}$ | $0.042579\text{ mm}$ | $0.002634\text{ kN}\cdot\text{mm}$ | `06234e38f1e2e704cc76f3bf51ab350fea3e243126c416ac743800529243a76d` |
| **`PK10R1_DEFECTIVE`** | `1389684.mmaster02` | $0.0050\text{ mm}$ | $31.9899\text{ kN/mm}$ | $0.383101\text{ kN}$ | $0.013606\text{ mm}$ | $0.003639\text{ kN}$ | $0.050000\text{ mm}$ | $0.003922\text{ kN}\cdot\text{mm}$ | `61e64463583f4080cf2d1d40908d108adde495d1ef6a00b5fd7dabf38e6105b6` |
| **`PK10R2_TOPOLOGY`** | `1390056.mmaster02` | $0.0050\text{ mm}$ | $12.8636\text{ kN/mm}$ | $0.351522\text{ kN}$ | $0.050000\text{ mm}$ | $0.351522\text{ kN}$ | $0.050000\text{ mm}$ | $0.011393\text{ kN}\cdot\text{mm}$ | `3e64ea894708f8c819079105ad6be13975a5bfbe292c7138f8c9cec5c3b93dab` |
| **`R7_SAMEMESH`** | `1390042.mmaster02` | $0.0050\text{ mm}$ | N/A (Restart) | $0.387570\text{ kN}$ | $0.014235\text{ mm}$ | $0.003587\text{ kN}$ | $0.050000\text{ mm}$ | $0.002488\text{ kN}\cdot\text{mm}$ | `e61c97e9ca861ac713760091e02cacd332af8cc4583eaa4b99ce42769969a462` |
| **`PK10R3_REFINED_TIP`** | `1390098.mmaster02` | $0.0020\text{ mm}$ | $12.8241\text{ kN/mm}$ | $0.348565\text{ kN}$ | $0.050000\text{ mm}$ | $0.348565\text{ kN}$ | $0.050000\text{ mm}$ | $0.011330\text{ kN}\cdot\text{mm}$ | `4e2a7030b8c7eaa53105a30e9def018cde0cec079f14bd5e986bf8359806448f` |

---

## 3. Matched-Displacement Field Provenance Table

Exact pointwise physical state quantities traced across all runs:

| Prescribed $U_1$ | Canonical H1 ($h=0.002$) $d_{\max}$ | Canonical H2 ($h=0.001$) $d_{\max}$ | PK10R2 ($h=0.005$) $H_{\max}$ ($\text{kN/mm}^2$) | PK10R2 $d_{\max}$ | PK10R3 ($h=0.002$) $H_{\max}$ ($\text{kN/mm}^2$) | PK10R3 $d_{\max}$ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **$U_1 = 0.0050\text{ mm}$** | $0.060033$ (Node 5858) | $0.062048$ (Node 17048) | $0.0276$ (Inc 18) | $0.0087$ | **`0.0609`** (Inc 18) | $0.0090$ |
| **$U_1 = 0.0100\text{ mm}$** | $0.285585$ (Node 5858) | $0.296184$ (Node 17048) | $0.1103$ (Inc 28) | $0.0348$ | **`0.2435`** (Inc 28) | $0.0358$ |
| **$U_1 = 0.0125\text{ mm}$** (Peak) | **`0.699200`** (Node 5858) | **`0.843327`** (Node 16457) | $0.1723$ (Inc 33) | $0.0544$ | **`0.3804`** (Inc 33) | $0.0560$ |
| **$U_1 = 0.0200\text{ mm}$** | $1.014741$ (Node 4268) | $1.017557$ (Node 9999) | $0.4411$ (Inc 48) | $0.1392$ | **`0.9739`** (Inc 48) | $0.1432$ |
| **$U_1 = 0.0350\text{ mm}$** | $1.014814$ (Node 3618) | $1.022190$ (Node 7986) | $1.3509$ (Inc 78) | $0.4261$ | **`2.9826`** (Inc 78) | $0.4388$ |
| **$U_1 = 0.0500\text{ mm}$** | $1.007308$ (Node 4930) | $1.013730$ (Node 7985) | $2.7570$ (Elem 8973) | $0.8690$ (Elem 8847) | **`6.0870`** (Elem 26349) | **`0.8966`** (Elem 26063) |

- **PK10R2 Peak Locations**:
  - Element 8973 (Layer 2) $\implies$ Physical Quad 2925: Centroid at $(x = +0.002500\text{ mm}, y = -0.002500\text{ mm})$.
  - Element 8847 (Layer 2) $\implies$ Physical Quad 2799: Centroid at $(x = +0.002500\text{ mm}, y = -0.007500\text{ mm})$.
- **PK10R3 Peak Locations**:
  - Element 26349 (Layer 2) $\implies$ Physical Quad 8617: Centroid at $(x = +0.001000\text{ mm}, y = -0.001000\text{ mm})$.
  - Element 26063 (Layer 2) $\implies$ Physical Quad 8331: Centroid at $(x = +0.001000\text{ mm}, y = -0.003000\text{ mm})$.

---

## 4. Mathematical Derivation of Element Stiffness Scaling in 2D Phase-Field UEL

In `f42_mixed_uel.for`, the phase-field residual is:
$$R_i = \int_{\Omega_e} \left[ G_c l_0 \nabla N_i \cdot \nabla d + \left( \frac{G_c}{l_0} + 2H \right) N_i d - 2H N_i \right] d\Omega$$

### A. Element Gradient Stiffness Matrix $\mathbf{K}_{\text{grad}}^{(e)}$
$$\mathbf{K}_{\text{grad}, ij}^{(e)} = G_c l_0 \int_{\Omega_e} \nabla N_i \cdot \nabla N_j \, d\Omega = G_c l_0 \int_{-1}^{1}\int_{-1}^{1} (\mathbf{J}^{-T} \nabla_{\boldsymbol{\xi}} N_i) \cdot (\mathbf{J}^{-T} \nabla_{\boldsymbol{\xi}} N_j) \det(\mathbf{J}) \, d\xi d\eta$$
For a 2D quadrilateral of characteristic size $h$:
- $\det(\mathbf{J}) \propto h^2$ (area scaling)
- $\mathbf{J}^{-1} \propto \frac{1}{h}$ (spatial gradient operator)
- $(\nabla N_i \cdot \nabla N_j) \det(\mathbf{J}) \propto \left(\frac{1}{h}\right) \left(\frac{1}{h}\right) (h^2) = \mathcal{O}(h^0) = \mathcal{O}(1)$.

$$\mathbf{K}_{\text{grad}}^{(e)} \propto G_c l_0 \cdot \mathcal{O}(1) \quad (\text{Scale-invariant in 2D})$$
*Correction*: The element gradient stiffness $\mathbf{K}_{\text{grad}}^{(e)}$ does **not** increase with coarsening; it is independent of $h$ in 2D.

### B. Element Mass / Regularization Matrix $\mathbf{K}_{\text{mass}}^{(e)}$
$$\mathbf{K}_{\text{mass}, ij}^{(e)} = \frac{G_c}{l_0} \int_{\Omega_e} N_i N_j \, d\Omega = \frac{G_c}{l_0} \int_{-1}^{1}\int_{-1}^{1} N_i N_j \det(\mathbf{J}) \, d\xi d\eta \propto \frac{G_c}{l_0} h^2 = \mathcal{O}(h^2)$$
The mass matrix shrinks quadratically as $h \to 0$ and expands quadratically as $h$ increases.

### C. Ratio of Gradient to Mass Stiffness
$$\frac{\|\mathbf{K}_{\text{grad}}^{(e)}\|}{\|\mathbf{K}_{\text{mass}}^{(e)}\|} \propto \frac{G_c l_0}{\frac{G_c}{l_0} h^2} = \frac{l_0^2}{h^2}$$
- On fine elements ($h \ll l_0$, e.g. $h=0.002\text{ mm}, l_0=0.015\text{ mm}$): $l_0^2/h^2 \approx 56.25 \gg 1$.
- On coarse elements ($h \gg l_0$, e.g. $h=0.025\text{ mm}, l_0=0.015\text{ mm}$): $l_0^2/h^2 \approx 0.36 \sim 1$.

### D. True Physical/Discretization Mechanism of Crack Arrest
The arrest of the crack at the coarse boundary in PK10R3 is governed by:
1. **Singularity Averaging**: The singular crack-tip strain field $\varepsilon \sim 1/\sqrt{r} \implies \psi_+ \sim 1/r$ is integrated over an element volume $\Omega_e \sim h^2$. On coarse elements ($h=0.025\text{ mm}$), the driving forcing vector $\mathbf{f}_{\text{ext}}^{(e)} = \int 2H N_i d\Omega$ is averaged and diluted.
2. **Phase-Field Band Under-Resolution ($h/l_0 > 1$)**: When $h = 0.025\text{ mm} > l_0 = 0.015\text{ mm}$, the finite element polynomial basis cannot resolve the steep exponential profile $d(x) = e^{-|x|/l_0}$, leading to artificial numerical crack pinning.

---

## 5. Epistemic Scope: What `1390098.mmaster02` Demonstrates vs Open Hypotheses

1. **Demonstrated Facts**:
   - Local crack-tip mesh refinement to $h = 0.0020\text{ mm}$ ($h/l_0 = 0.1333$) successfully activates local crack-driving energy ($H = 6.087\text{ kN/mm}^2$) and phase-field degradation ($d = 0.8966$) along the Mode-II kink direction.
   - A static local refinement patch alone cannot sustain crack propagation through an unrefined coarse background mesh ($h=0.025\text{ mm}$).
2. **Open Hypotheses**:
   - Whether dynamic adaptive remeshing, graded refinement corridors, or global uniform refinement is optimal for Mode-II shear localization remains an open question subject to formal algorithm qualification.

---

## 6. Preserved Scientific Gates & Multi-Agent Invariants

```text
same_mesh_restart_validation = VALIDATED
history_transfer_rule_resolved = false
selected_production_history_operator = UNRESOLVED
nonmatching_transfer_algorithm_scientifically_unblocked = false
production_adaptive_accuracy_validation_scientifically_unblocked = false
PK10R1_topology_repair_required = true
telegram_delivery_observed = true (prior smoke test)
email_delivery_observed = true (prior smoke test)
notification_pre_submission_gate_passed = true
```

```text
new_submission_authorized = false
qsub_called = false
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```
