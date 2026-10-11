# Supervisor Decision Package: Proposed Method B Load-Partitioning Study on Mode-I Benchmark

**Document ID:** `SUPERVISOR_DECISION_METHOD_B_MODE1_LOAD_PARTITIONING`  
**Date:** `2026-10-11`  
**Status:** `PROPOSED / PENDING SUPERVISOR REVIEW & EXPLICIT AUTHORIZATION`  
**Target Milestone:** Supervisor Meeting (Thursday, 22 October 2026, 10:00 AM)  
**Governing Benchmark:** Mode-I Symmetric Tension Crack Propagation ($l_0 = 7.5\,\mu\text{m}$, Frozen Baseline)  
**Author:** Gemini Antigravity  

---

> [!IMPORTANT]
> **GOVERNANCE & EXECUTION DISCLAIMER:**
> This document constitutes a formal scientific study proposal and decision package for supervisor review. **It does NOT authorize any Abaqus solver runs, PBS job submissions, queue modifications, or cluster executions.** All HPC actions remain strictly locked until explicit, recorded human supervisor approval is granted. The frozen Mode-I baseline (tag `v2026.10.08-supervisor-meeting-mode1-freeze`, UEL SHA-256 `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`) remains 100% frozen and untouched.

---

## 1. Executive Summary & Problem Formulation

### 1.1 Limitation of Standard Two-Pass Offline Pre-Refinement (Method A)
In the native Abaqus adaptive remeshing workflow demonstrated in Chapter 4 (Method A):
1. A preliminary coarse finite-element analysis (pre-analysis) is solved across the displacement loading horizon.
2. The Zienkiewicz–Zhu / SPR-based recovery error indicator (`MISESERI` / `MISESAVG`) is computed at selected state frames.
3. Abaqus CAE generates an adapted mesh conforming to the specified error target ($\text{ET} = 2.0\%$).
4. The full phase-field fracture simulation is then executed from $t = 0$ on this fixed adapted discretization.

While Method A achieved a **$2.46\times$ workflow walltime speedup** and **$70.67\%$ element count reduction** on Mode-II with under $1\%$ peak force error, it exhibits a fundamental limitation:
- If the coarse pre-analysis is pushed deep into the softening regime ($u > u_{\text{peak}}$), the coarse discretization experiences localized softening non-convergence, cutback loops, or solver cutoff before providing the full deformation history.
- Conversely, if the coarse pre-analysis is restricted to a single purely elastic increment, it cannot capture stress redistribution or damage-induced rotation of the principal stress field prior to macroscopic crack extension.

### 1.2 The Method B Alternative: Configurable Load Partitioning
**Method B** resolves this limitation without requiring the intrusive complexity of nonmatching state transfer (Method C):
- Rather than executing an unpartitioned coarse solve that risks softening divergence, the pre-analysis loading schedule is divided into **configurable load partitions** up to an initiation fraction $\alpha \in [0.5, 0.9]$ of the expected peak displacement ($u_{\text{part}} = \alpha\,u_{\text{peak}}$).
- By terminating the pre-analysis before severe softening instability while allowing sufficient load for stress-gradient development and early localization, Method B extracts the optimal spatial refinement corridor natively in Abaqus CAE.
- The full fracture analysis is subsequently re-run from $t = 0$ on the adapted discretization, completely bypassing nonmatching state transfer while avoiding coarse-mesh softening non-convergence.

---

## 2. Scientific Objective & Hypotheses

### 2.1 Primary Objective
To establish whether configurable load partitioning (1-step, 2-step, and 4-step schedules) in the coarse pre-analysis can systematically capture the stress recovery error indicator (`MISESERI`) and optimal damage corridor on the Mode-I benchmark prior to softening divergence, maintaining high fracture fidelity while minimizing pre-analysis computational overhead.

### 2.2 Testable Hypotheses
1. **Hypothesis H1 (Linear Scale Invariance in Elastic Sub-Steps):**
   Within the linear elastic regime ($d \approx 0$), the relative normalized error indicator $\eta_e = \text{MISESERI}_e / \text{MISESAVG}$ is scale-invariant with respect to load magnitude; partitioning does not alter mesh topology in the elastic regime.
2. **Hypothesis H2 (Pre-Peak Localization Capture):**
   A 2-step or 4-step partitioned pre-analysis terminating at $\alpha = 0.85\,u_{\text{peak}}$ captures incipient stress gradients and localized strain concentrations that rotate or sharpen the refinement corridor compared to a low-load elastic frame ($\alpha = 0.50$), without triggering coarse-mesh softening cutbacks.
3. **Hypothesis H3 (Parity with High-Density References):**
   A Method B adapted mesh generated from an optimal partition ($\alpha \approx 0.85$) reproduces the peak force $F_{\max}$, initial stiffness $K_0$, and crack propagation trajectory of the frozen Mode-I uniform reference within $\le 1.0\%$ relative error, while reducing element count by $\ge 60\%$.

---

## 3. Controlled Experimental Matrix & Study Design

The proposed study evaluates three load-partitioning configurations against the authoritative Mode-I uniform fine reference:

| Configuration ID | Pre-Analysis Loading Schedule | Load Steps ($N$) | Step Cutoff Fractions ($\alpha = u/u_{\text{peak}}$) | Terminal Pre-Analysis State | Target Remesh Role |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **M1-MB-1S** (1-Step Baseline) | Single monotonic step | 1 | $\alpha_1 = 0.50$ (Strict Elastic) | Pure elastic stress field | Baseline elastic corridor |
| **M1-MB-2S** (2-Step Partition) | Two-stage loading | 2 | $\alpha_1 = 0.50$, $\alpha_2 = 0.85$ (Early Localization) | Incipient localization | Primary candidate |
| **M1-MB-4S** (4-Step Partition) | Four-stage loading | 4 | $\alpha_1 = 0.25$, $\alpha_2 = 0.50$, $\alpha_3 = 0.75$, $\alpha_4 = 0.90$ | Pre-peak threshold | High-resolution sensitivity |
| **M1-REF-UNIF** (Reference Anchor) | Continuous solve | 1 | Full horizon ($u = 1.0 \times 10^{-2}\,\text{mm}$) | Terminal fracture | Authoritative benchmark |

### 3.1 Invariant Parameters & Numerical Controls
To guarantee strict like-for-like comparability:
- **Specimen Geometry:** $1.0\,\text{mm} \times 1.0\,\text{mm}$ square plate with horizontal edge crack of length $a_0 = 0.5\,\text{mm}$ at mid-height ($y = 0.5\,\text{mm}$).
- **Material Parameters:**
  - Young's modulus: $E = 210.0\,\text{kN/mm}^2 = 210\,\text{GPa}$
  - Poisson's ratio: $\nu = 0.30$
  - Fracture energy: $G_c = 2.7 \times 10^{-3}\,\text{kN/mm} = 2.7\,\text{kJ/m}^2$
  - Regularization length scale: $l_0 = 0.0075\,\text{mm} = 7.5\,\mu\text{m}$
- **User Subroutine:** Authoritative Mode-I `f42_mixed_uel.for` (SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`).
- **Adaptation Engine:** Native Abaqus CAE `adaptiveRemesh` with error target $\text{ET} = 2.0\%$, SPR error indicator, quad-dominated element generation.
- **Fracture Analysis Execution:** Monotonic vertical displacement $u_y = 1.0 \times 10^{-2}\,\text{mm}$ applied to top boundary; bottom boundary fixed ($u_y = 0$).

---

## 4. Quantitative Acceptance Criteria

For Method B to be scientifically qualified on Mode-I, the candidate adapted simulation must satisfy all of the following criteria:

1. **Global Force-Displacement Parity:**
   - Peak load discrepancy relative to uniform reference: $|\Delta F_{\max}| / F_{\max,\text{ref}} \le 1.0\%$.
   - Initial elastic stiffness discrepancy: $|\Delta K_0| / K_0,\text{ref} \le 0.5\%$.
   - Pre-peak load-displacement root-mean-square error: $\text{NRMSE}_{\text{pre}} \le 1.0\%$.
2. **Fracture Trajectory & Damage Localization:**
   - Crack initiation point within $1.0\,h_{\min}$ of notch tip.
   - Crack path collinearity: path deviation angle $|\Delta \theta| \le 1.0^\circ$ (pure Mode-I horizontal propagation along $y = 0.5\,\text{mm}$).
   - Complete ligament damage coverage ($d \ge 0.95$ across the entire fracture ligament).
3. **Discretization & Computational Efficiency:**
   - Finite element count reduction: $\ge 50\%$ compared to uniform fine mesh.
   - Refinement confinement: fine elements ($h \le l_0/2 = 3.75\,\mu\text{m}$) strictly confined to the crack corridor; coarse sizing ($h \ge 2\,l_0$) preserved in far field.
   - Workflow walltime speedup: $\ge 2.0\times$ (including pre-analysis, CAE remesh, and adapted solve).
4. **Pre-Analysis Convergence Robustness:**
   - Pre-analysis solve completed with zero cutback failures, zero line-search divergences, and exit code 0.

---

## 5. Computational Budget & HPC Specification

If authorized by the supervisor, the proposed study will execute within the following verified HPC environment:
- **Cluster:** TU Bergakademie Freiberg HPC Cluster (`normal_imfdfkmq` queue).
- **Execution Mode:** Single-rank shared-memory SMP (1 CPU serial authoritative anchor; 8-thread SMP qualification).
- **Resource Request per Job:** 1 node, 1 to 8 CPUs, 16 GB RAM, walltime limit 4:00:00 (expected runtime $\le 45$ minutes per job).
- **Total Study Budget:** Maximum 6 jobs (3 coarse pre-analyses + 3 adapted fracture solves), total CPU hours $\le 24$ CPU-hours.
- **Notification Integration:** Dual-channel PBS email (`#PBS -m abe`) and Telegram notification traps.

---

## 6. Supervisor Review & Decision Checkpoints

The supervisor is requested to review and decide on the following three actionable gates during the 22 October 2026 meeting:

| Checkpoint ID | Decision Item | Recommended Action | Supervisor Decision |
| :---: | :--- | :--- | :---: |
| **CP-1** | **Scope Authorization:** Approve Method B load-partitioning study on Mode-I as a formal thesis contribution. | **APPROVE** (expands thesis from single-pass Method A to robust load-partitioned adaptive remeshing). | `[ ] APPROVED  [ ] DEFERRED  [ ] REJECTED` |
| **CP-2** | **Partitioning Schedule:** Adopt 2-step schedule ($\alpha = 0.50, 0.85$) as primary candidate and 4-step as sensitivity check. | **APPROVE** (balances localization capture against pre-analysis solve cost). | `[ ] APPROVED  [ ] MODIFIED  [ ] REJECTED` |
| **CP-3** | **HPC Execution Clearance:** Authorize staged execution of the 6-job Mode-I test batch following meeting. | **DEFER EXECUTION** until post-meeting minute sign-off; keep all cluster submission gates locked. | `[ ] APPROVED  [ ] PENDING MINUTES` |

---

## 7. Archival & Traceability

- **Parent Methodology:** Thesis Chapter 4, Section 4.5 ("Future Methodological Directions: Methods B and C").
- **Reference Tag:** `docs/decisions/SUPERVISOR_DECISION_METHOD_B_MODE1_LOAD_PARTITIONING.md`
- **Related Records:**
  - `project_coordination/CURRENT_STATE.md`
  - `project_coordination/TASK_LEDGER.csv` (Task `F1404`)
  - `project_coordination/ARTIFACT_REGISTRY.csv`
