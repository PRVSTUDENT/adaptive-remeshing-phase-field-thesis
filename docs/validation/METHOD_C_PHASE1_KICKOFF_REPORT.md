# Method C Plan — Phase 1 Kickoff: Incremental Adaptive Remeshing Demonstration

**Task ID:** METHOD-C-PHASE1-DEMO-AND-LOOP-SKELETON  
**Date:** 19 November 2026  
**Status:** READY_FOR_SUPERVISORY_CONFIRMATION  
**Research Goal:** METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1  
**Target Milestone:** Supervisor Meeting (Prof. Kiefer & Dr. Roth) on Wednesday, 2 December 2026, 13:00  
**Research Freeze:** 13 December 2026 | **Thesis Submission:** 13 January 2027  

---

## 1. Executive Summary & Supervisor Directive

Following the supervisor meeting on 19 November 2026, the master research priorities have been officially aligned:

1. **Method A Framework (F1852) Accepted & Frozen:** The one-shot adaptive remeshing framework combining native recovered-stress error (MISESERI) and the constructed damage envelope has been thoroughly evaluated and validated on Cases 1, 2, 3, and 5. As stated by the supervisor: *"all the other things are already done at a very good and sufficient quality; do not revisit unless requested."* Method A is formally frozen as a successful baseline.
2. **Method C Formal Mandate:** The primary research goal is now the end-to-end demonstration of **Method C — incremental adaptive remeshing with state and history transfer across advancing load steps** on a single representative Mode-I demonstration benchmark (plate with initial crack and central hole).
3. **Core Demonstration Objective:** Show that the mesh progressively adapts as the load increases, with the crack initiating at the notch tip and advancing toward the hole along the evolving damage field, maintaining mechanical equilibrium and history consistency across transfers.

---

## 2. Proposed Demonstration Benchmark Specification

### 2.1 Geometry
To demonstrate that the advancing crack naturally follows the damage field toward a stress-concentrating void, we propose the following symmetrical Mode-I plate with an initial edge crack and an on-axis circular hole:

- **Domain:** $[0.0, 1.0] \times [0.0, 1.0]\,\text{mm}$ square plate ($\Omega = 1.0 \times 1.0\,\text{mm}$).
- **Initial Crack / Edge Notch:** Horizontal seam notch along $y = 0.5\,\text{mm}$ extending from $x = 0.0$ to $x = 0.5\,\text{mm}$ (initial crack length $a_0 = 0.5\,\text{mm}$, identical to Case 1).
- **Hole Ahead of Crack Tip:** Symmetrical circular hole centered at $(x_c, y_c) = (0.75, 0.50)\,\text{mm}$ with radius $r = 0.10\,\text{mm}$.
- **Ligament Dimensions:**
  - *Inter-feature ligament (notch tip to hole edge):* $x \in [0.50, 0.65]\,\text{mm}$ (width $w_1 = 0.15\,\text{mm}$).
  - *Hole domain:* $x \in [0.65, 0.85]\,\text{mm}$, $y \in [0.40, 0.60]\,\text{mm}$.
  - *Rear ligament (hole edge to right boundary):* $x \in [0.85, 1.00]\,\text{mm}$ (width $w_2 = 0.15\,\text{mm}$).

### 2.2 Boundary Conditions & Loading
- **Bottom Edge ($y = 0.0\,\text{mm}$):** Fully clamped ($u_1 = 0$, $u_2 = 0$).
- **Top Edge ($y = 1.0\,\text{mm}$):** Uniform vertical displacement (`EDGE_PULL`), $u_2 = \Delta(t)$, with horizontal displacement constrained ($u_1 = 0$) or free.
- **Loading Schedule:**
  - *Step 1 (Elastic pre-load):* Ramp to $u_2 = 0.005\,\text{mm}$ (50 increments). Damage remains zero everywhere ($d = 0$).
  - *Step 2 (Incremental fracture loading):* Partitioned into $N_{\text{inc}} = 4\text{--}6$ discrete increments from $u_2 = 0.005\,\text{mm}$ to $u_2 = 0.010\,\text{mm}$. For each increment, the solver advances, evaluates remeshing criteria, adapts the mesh, transfers the state, and continues.

### 2.3 Phase-Field Material Parameters
Consistent with canonical Case 1 parameters and frozen Fortran UEL (`CE8D5EDC`):
- Young's modulus: $E = 210.0\,\text{GPa}$ ($210.0\,\text{kN/mm}^2$)
- Poisson's ratio: $\nu = 0.30$
- Critical fracture energy release rate: $G_c = 0.0027\,\text{kN/mm}$ ($2.7\,\text{N/mm}$)
- Length scale: $l_0 = 0.0075\,\text{mm}$ ($7.5\,\mu\text{m}$)
- Residual stiffness parameter: $k = 1.0 \times 10^{-7}$
- Initial coarse mesh seed: $h_0 \approx 0.020\,\text{mm}$ ($\approx 2,900$ elements, matching Case 1 coarse donor).

---

## 3. Method C Incremental Loop Architecture

For each load increment $k = 1, 2, \dots$:

```
                   +----------------------------------+
                   |  1. Solve on current mesh M_k    |
                   |     at current load increment u_k|
                   +-----------------+----------------+
                                     |
                                     v
                   +----------------------------------+
                   |  2. Extract observables:         |
                   |     - max(d) per element         |
                   |     - MISESERI recovered error   |
                   +-----------------+----------------+
                                     |
                                     v
                   +----------------------------------+
                   |  3. Adaptation decision:         |
                   |     - If max(d) >= 0.5: envelope |
                   |     - Else: native MISESERI      |
                   +-----------------+----------------+
                                     |
                      (Remesh triggered? Yes)
                                     |
                                     v
                   +----------------------------------+
                   |  4. Generate adapted mesh M_{k+1}|
                   |     via F1852 driver selection   |
                   +-----------------+----------------+
                                     |
                                     v
                   +----------------------------------+
                   |  5. State & History Transfer:    |
                   |     u, d, alpha/H from M_k       |
                   |     to recipient M_{k+1}         |
                   +-----------------+----------------+
                                     |
                                     v
                   +----------------------------------+
                   |  6. Re-equilibration solve at    |
                   |     fixed load u_k on M_{k+1}    |
                   +-----------------+----------------+
                                     |
                                     v
                   +----------------------------------+
                   |  7. Advance load to u_{k+1}      |
                   +----------------------------------+
```

---

## 4. Key Outstanding Challenges & Diagnostic Plan

### 4.1 Prior Working Transfer (C4 -> C5 Baseline)
Fixed-load nonmatching transfer was successfully demonstrated in Job 1419269 (Package 160):
- Mesh transition: $7,056 \to 12,544$ elements.
- Re-equilibration at fixed displacement $u_2 = 1.8503\,\mu\text{m}$ achieved after 69 outer iterations.
- Mechanical fidelity: Reaction force discrepancy $\Delta F = -1.33\%$, total energy discrepancy $\Delta E = +0.16\%$.
- Irreversibility: Zero damage healing observed ($\Delta d \ge 0$).

### 4.2 The C5 -> C6 Re-equilibration Blocker (Package 171)
In Package 171 ($12,996 \to 15,252$ elements), the fixed-load re-equilibration failed to converge within standard Newton tolerance.
- **Leading Hypothesis:** Gauss-point history smoothing. When transferring history field $\mathcal{H}$ from the donor to the receiver, element-averaging the donor Gauss points before mapping to the receiver's Gauss points artificially flattens steep gradients at the crack tip. The recipient elements experience an artificial drop in peak history, causing localized stress redistribution that destabilizes equilibrium iterations.
- **Phase 2 Remedy:** Implement true point-to-point isoparametric Gauss-point interpolation with local projection or bounding, ensuring that peak crack-tip history is preserved exactly without artificial smoothing.

---

## 5. Work Breakdown & Milestone Timeline

| Phase | Time Window | Deliverables | Status |
| :--- | :--- | :--- | :---: |
| **Phase 1** | 19–21 Nov | Demo geometry confirmation; coarse donor mesh generation; Job-1 baseline solve; orchestration loop skeleton. | **ACTIVE** |
| **Phase 2** | 21–25 Nov | Reproduce and resolve C5 $\to$ C6 re-equilibration blocker; validate clean re-equilibration with force/energy error $\le 2\%$. | SCHEDULED |
| **Phase 3** | 25–28 Nov | Forward propagation after transfer; end-to-end multi-increment execution showing crack path heading toward hole. | SCHEDULED |
| **Phase 4** | 28 Nov – 1 Dec | Production outputs for supervisor meeting: animations (mesh + damage), load-displacement curves, crack evolution plots, meeting presentation. | SCHEDULED |
| **Meeting** | 2 Dec 13:00 | Formal review with Prof. Kiefer & Dr. Roth. | SCHEDULED |
| **Freeze** | 13 Dec 2026 | Research freeze across all thesis codes and data. | LOCKED |
| **Submission**| 13 Jan 2027 | Final Master Thesis Submission. | LOCKED |

---

## 6. Verification & Governance Invariants

- **Bitwise Frozen Subroutine:** `f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`) preserved unchanged.
- **Native Stress Interface:** `f42_native_miseseri_interface_v1.for` (`E5C98B6F601B1CD586571F8E24F357D15ABBD1C5D5487B52903BA249734279B2`) preserved unchanged.
- **F1852 Remeshing Engine:** Reused directly for all mesh generation steps.
- **HPC Job Budget:** Phase 1 involves only coarse offline mesh generation and loop skeleton preparation (0 new PBS jobs consumed at kickoff; submissions strictly governed).
