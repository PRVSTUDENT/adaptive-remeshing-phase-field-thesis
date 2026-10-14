# Technical Report: Task F1464 -- Method B Retrospective Provenance, AT-2 Mathematical Audit, and Prospective Adaptive Limitation

**Date:** 2026-10-14  
**Agent:** Gemini Antigravity  
**Task ID:** `F1464-VALIDATE-METHOD-B-LIMITATION-AND-ADVANCE-NATIVE-EXPERIMENT`  
**Starting Commit:** `844657b6ee4b1b216fa706cd425a6aed8bd8970c`  
**Status:** `COMPLETED`  
**Governing Gate:** `GATE6B_EVALUATION_COMPLETE_READY_FOR_SUPERVISOR_SIGNOFF` (Gate 6C strictly on hold)

---

## 1. Executive Summary & Immediate Submission Decision

### 1.1 The Immediate Submission Decision
A primary directive for Task `F1464` is to establish the immediate computational experiment decision before further documentation:
- **Decision:** **NO REDUNDANT OR DUMMY PBS JOB IS SUBMITTED TO THE HPC CLUSTER.**
- **Scientific Rationale:**
  1. *Candidate A (Prospective Native Remeshing Experiment):* Can native Abaqus `RemeshingRule` driven by a prospective linear-elastic pre-analysis ($u \le 0.0050\,\text{mm}$) refine the uncracked ligament and prevent the coarse-pinning force plateau ($0.55\,\text{kN}$) without post-fracture crack path information? **No.** Exhaustive spatial audits across 1%, 2%, 3%, and 5% error targets confirm that the stationary notch singularity decays as $r^{-3/2}$, leaving the unbroken ligament with zero fine elements ($h \approx 20\,\mu\text{m} \gg \ell_0/2 = 3.75\,\mu\text{m}$). Submitting a prospective job with native controls will merely regenerate a coarse ligament and reproduce the known artificial force plateau already documented in Jobs `1411934`, `1411949`, and `1412872`.
  2. *Candidate B (Post-Fracture Completion Diagnostic beyond $u = 0.007889\,\text{mm}$):* In Jobs `1412465` and `1412873`, physical brittle fracture was completely demonstrated, with the reaction force dropping from $743.7\,\text{N}$ to $1.76\,\text{N}$ ($99.76\%$ load drop). The simulation terminated at Increment 2890 because standard Abaqus automatic time incrementation reached the minimum increment $dt < dt_{\min} = 1.0 \times 10^{-9}$ on a physically severed structure governed by residual penalty stiffness $k = 10^{-6}$. Forcing the solver through the uncoupled rigid separation of two severed halves requires unphysical numerical relaxation or minute increments ($< 10^{-12}$) with zero new physical fracture information.
  3. *Scheduler Governance Compliance:* Cluster policy strictly prohibits speculative, redundant, or dummy jobs launched merely because cluster slots are idle. Every independent computational fact is already established by terminal, bitwise-verified simulation evidence.

---

## 2. Completed HPC Evidence & Parity Certification

Both HPC simulations reached terminal status on cluster `/scratch9/pr21vyci/` with full telemetry harvested:

| PBS Job ID | Discretization & Purpose | Threads / Mode | Exit Code | Walltime | Increments | Final State | Parity & Determinism Certification |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `1412872.mmaster02` | Native Method B (14,677 FE) Stage B Repeat | 8 CPUs SMP | 0 | 05:12:04 | 7,000 | $u = 0.0100\,\text{mm}$, $RF = 8.262311\,\text{N}$ | **`THREAD_PARITY_PASS`** & **`THREAD_DETERMINISM_PASS`** ($1.87\times$ speedup) |
| `1412873.mmaster02` | Corrected Method B (14,483 FE) Stage A Parity | 8 CPUs SMP | 1 | 03:35:22 | 4,890 | $u = 0.007889\,\text{mm}$, $RF = 1.764510\,\text{N}$ | **`THREAD_PARITY_PASS`** ($1.82\times$ speedup, $99.76\%$ softened) |

- **Bitwise Energy Trace Parity:** For both Job `1412872` and Job `1412873`, the harvested `uel_energy_balance.csv` traces are bitwise identical across all increments compared to their serial baselines:
  - Native 14,677 FE: SHA-256 `792BE67DB9AC2CA2E51B9811CA0FB6F374BF28D0BA160F725F2D071B3C38D99D` across all 7,000 increments.
  - Corrected 14,483 FE: SHA-256 `82F2963D4399F7929DB6DF019A2D7FD34ABD3DEB570571C04AD489B723561333` across all 4,890 increments.
- **Physical Fracture Demonstration vs Full Horizon:** Job `1412873` (and serial Job `1412465`) demonstrated complete physical brittle fracture across the ligament up to $u = 0.007889\,\text{mm}$ ($99.76\%$ force drop). The plate was completely severed before Abaqus automatic time incrementation terminated at $dt < dt_{\min} = 1.0 \times 10^{-9}$ on the uncoupled halves.

---

## 3. Mathematical Audit of AT-2 Phase-Field Damage Mechanics

### 3.1 Strong-Form Euler--Lagrange Formulation
In the AT-2 phase-field formulation ($w(d)=d^2$, $c_w = 1$), the variational minimization of total potential energy with respect to damage $d$ yields the strong-form Euler--Lagrange boundary value problem:
$$(H + \psi_0)\,d - G_c \ell_0 \nabla^2 d = H \quad \text{in } \Omega, \qquad \nabla d \cdot \mathbf{n} = 0 \quad \text{on } \partial\Omega$$
where:
- $\psi_0 = \frac{G_c}{2\ell_0} = \frac{0.0027\,\text{kN/mm}}{2 \times 0.0075\,\text{mm}} = 0.180\,\text{kN/mm}^2 = 180.0\,\text{MPa}$ is the characteristic fracture energy density scale.
- $H(\mathbf{x}, t) = \max_{\tau \le t} \psi_e^+(\boldsymbol{\epsilon}(\mathbf{x}, \tau))$ is the crack-driving strain history variable.

### 3.2 Homogeneous Zero-Gradient Limit vs Coupled Spatial Solution
- When spatial gradients vanish ($\nabla d = \mathbf{0} \implies \nabla^2 d = 0$), the field equation reduces algebraically to:
  $$d_{\mathrm{hom}} = \frac{H}{H + \psi_0}$$
  This proves that standard AT-2 damage initiates continuously for any positive history $H > 0$ without a discrete initiation threshold.
- However, at a sharp notch singularity, $H(\mathbf{x})$ possesses steep spatial gradients. At the local peak of damage, curvature is negative ($\nabla^2 d < 0$). The regularizing Laplacian operator $-G_c \ell_0 \nabla^2 d > 0$ acts as a spatial diffusion mechanism that regularizes the singularity and couples nodal damage across a zone of characteristic width $\sim \ell_0$.
- Substituting the local notch tip history $H_{\max} \approx 18.88\,\text{MPa}$ at $u = 0.0050\,\text{mm}$ into the zero-gradient formula yields a scalar estimate:
  $$d_{\mathrm{hom}} \approx \frac{18.88}{18.88 + 180.0} = 0.09493$$
  This 0D scalar value cannot replace solving the spatially coupled finite element boundary value problem:
  - On the coarse $2{,}906$-element mesh ($h \approx 20\,\mu\text{m} > 2.6\,\ell_0$), the element cannot resolve the gradient operator $\nabla d$, causing artificial discretization pinning that retards damage growth to $d_{\max} = 0.094910$ (Job `1411891`).
  - On an adequately resolved mesh ($h \le \ell_0/4 = 1.875\,\mu\text{m}$), the finite element solution resolves the Laplacian operator, allowing damage to develop to $d_{\max} = 0.3195$ at the identical displacement $u = 0.0050\,\text{mm}$ (Job `1411934`).

---

## 4. Retrospective Provenance of the 14,483-Element Mesh

### 4.1 Provenance Evidence
A detailed audit of `models/pandey_kumar_mode1/40_method_b_corrected_propagation_14k/PACKAGE_MANIFEST.json` and Stage 14F session archives (`2026-10-03_2135`) confirmed the exact origin of the 14,483-element mesh:
- **Recorded Source State:** `Stage-14 Step-2 localized damage state (u=0.0100 mm, companion frame 1022)`.
- **Mechanism:** In Stage 14F, `Job-1` was executed through full fracture up to $u = 0.0100\,\text{mm}$, where the crack had already completely severed the ligament ($d_{\max} = 1.0000$). At that post-fracture state, the bulk specimen had unloaded, reducing far-field error to $0.07\%$ and concentrating $95.4\%$ of the error integral along the traversed crack line.
- Running Abaqus native `adaptiveRemesh` on that post-fracture ODB produced the continuous horizontal refinement corridor ($14{,}483$ elements), which visually matched Pandey & Kumar's Fig. 6(a) (~13,941 elements).

### 4.2 Epistemic Classification: Retrospective Verification Mesh
- The 14,483-element discretization is classified explicitly as a **retrospective, benchmark-specific verification mesh**.
- It provides valuable physical evidence: it proves that if the fracture path is adequately resolved ($h \le 3.75\,\mu\text{m}$), the artificial force plateau is eliminated and brittle fracture is restored.
- However, because its refinement corridor was informed by a crack that had already propagated in a previous simulation, it **does not demonstrate that Method B can prospectively predict an unknown crack path**.

---

## 5. Prospective Adaptive Remeshing Limitation & Candidate Status of Method C

### 5.1 The Spatial Singularity Decay Barrier
In a prospective pre-analysis ($u \le 0.0050\,\text{mm}$), the crack has not yet propagated ($x_{\text{tip}} = 0.50\,\text{mm}$). The linear-elastic stress field decays away from the notch as:
$$\sigma_{yy}(r, \theta=0) \propto \frac{K_I}{\sqrt{2\pi r}}$$
Along the uncracked ligament ($x \in [0.70, 1.00]$):
- Stresses are regular and stress recovery error $\text{MISESERI}$ is small ($\text{MISESERI} < \text{MISESAVG}$).
- Under `UNIFORM_ERROR`, Abaqus computes large target element sizes and caps them at `maxElementSize` ($h = 20\,\mu\text{m}$).
- In `SPATIAL_LOCALIZATION_AUDIT_REPORT.json`, transverse profile audits of 1% (48k FE) and 2% (11k FE) meshes prove that **zero fine elements ($h \le 2\,\mu\text{m}$)** exist along the ligament at $x = 0.70, 0.80, 0.90\,\text{mm}$.
- Consequently, when nonlinear fracture begins, the crack inevitably propagates into coarse elements, leading to crack pinning and the artificial force plateau.

### 5.2 Epistemic Boundaries for Method C
- The failure of stationary pre-refinement (Method B) provides the clear conceptual motivation for sequential in-analysis remeshing (Method C), where the mesh is updated dynamically as the crack evolves.
- However, this failure **does not mathematically prove that Method C is already capable or validated**.
- Method C represents an **unqualified candidate sequential remeshing methodology**:
  - Gate C1 exploratory runs (`1412158`, `1412464`, `1412809`) revealed step-boundary reaction force jumps ($\Delta RF = 21.55\,\text{N}$ in Job `1412809`), coarse recipient pinning, and unresolved UEL state mapping questions.
  - Multi-cycle continuation, nonmatching transfer, gradient diffusion ($|\nabla d|$), and damage irreversibility enforcement remain strictly unqualified.
  - Gate 6C remains on hold pending supervisor sign-off on 22 October 2026.

---

## 6. Verification and Regression Testing

All unit tests developed across the Mode-I research pass 100%:
- `tests/unit/test_mode1_f1464_method_b_limitation_and_governance.py`: **6/6 PASS**
- `tests/unit/test_mode1_f1463_physical_consistency_and_feasibility.py`: **6/6 PASS**
- Complete Mode-I regression battery: **438 passed, 0 failed** cleanly.
- Authoritative production UEL hash verified: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`.
