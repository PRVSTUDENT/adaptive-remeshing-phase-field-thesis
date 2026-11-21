# Method C Case 3: Single-Job Multi-Cycle Adaptive Remeshing Framework Package Report

- **Task ID:** `METHOD-C-CASE3-SINGLE-JOB-FRAMEWORK-BUILD-AND-TEST`
- **Goal ID:** `METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1`
- **Correlation ID:** `HND-METHOD-C-CASE3-FRAMEWORK-TEST-001`
- **Predecessor Correlation ID:** `HND-METHOD-C-CASE3-FRAMEWORK-PREP-001` (reviewed at 2026-11-21T09:16:45Z)
- **Author:** Gemini Antigravity
- **Date:** 2026-11-21
- **Status:** COMPLETED_READY_FOR_INDEPENDENT_REVIEW
- **Cumulative PBS Submissions:** **67** (0 new jobs consumed during framework build; 1 PBS job authorized for test run, cumulative 67 $\to$ 68)

---

## 1. Executive Summary

This package delivers the revised and fully executable **Single-Job Multi-Cycle Adaptive Remeshing Framework** for Method C Case 3 (Pandey & Kumar 2025 Section 4.3: Mode-I cracked plate with central void and pin loading).

Incorporating the directives from independent review `HND-METHOD-C-CASE3-FRAMEWORK-PREP-001`, the framework completely supersedes the earlier static 5-cycle design with a dynamic, user-configurable, equal-load-division architecture:
1. **User-Specifiable Granularity & Equal Load Division (`GAP-FW-01`):** The number of adaptive steps is parameterised as `n_adaptive_steps` (default 4), exposed via CLI (`--n-adaptive-steps N`), manifest, and PBS script. Displacement is advanced in equal increments (`load_increment_mm`, default $0.0100\,\text{mm}$). The arbitrary $1.5000\,\text{mm}$ displacement cap has been completely removed.
2. **Crack-Completion Termination Criteria (`GAP-FW-01`):** The orchestrator loops dynamically (adding successive equal load increments) until physical crack completion is detected:
   - *Criterion A:* Terminal crack tip $x_{\text{tip}} \ge 64.0\,\text{mm}$ (right boundary of the $65.0\,\text{mm}$ plate), OR
   - *Criterion B:* Structural reaction force $RF_2 < 0.05 \times RF_{2,\text{peak}}$ (plate severed, $>95\%$ load capacity lost),
   with the 72-hour walltime allocation serving as the outer operational bound.
3. **Executable In-Allocation Orchestrator (`GAP-FW-02`):** The orchestrator `scripts/remeshing/case3_single_job_orchestrator.py` implements both the dry-run planning/verification path and the complete in-allocation execution loop (Abaqus solver invocation, `.sta` parsing, cutback floor detection, state and history transfer with `convex_clamp`, 3-layer deck assembly, fixed-load re-equilibration, and load advance).
4. **Authentic Record Reconciliation (`GAP-FW-03`):** All forensic figures have been corrected against committed repository records: Step 1 converged in 1 increment / 2 Newton iterations with force continuity $-0.9501\%$ (Job 5) and $-0.2897\%$ (Job 4); Job 5 Increment-12 failing nodes are 19880, 20110, 43706, 19975, 4328 at $x \in [14.3733, 14.6996]\,\text{mm}$ ahead of the tip; max terminal $u_2 = 0.057595\,\text{mm}$; initial coarse mesh has 4,671 physical elements (14,013 layered elements); Job 5 has 64,653 elements and 64,106 physical nodes.
5. **Physical Mesh Generated & Audited (`NOTE-FW-02`):** The minimized corridor physical mesh `PK_METHOD_C_CASE3_ADAPTIVE_PHYS.inp` has been generated via Abaqus CAE and committed: exactly 24,832 physical elements (24,738 nodes, $97.41\%$ quad fraction), representing a measured $61.6\%$ element reduction vs Job 5 ($64,653$ elements).
6. **Package Notification Script (`NOTE-FW-03`):** Committed `job_notifications.sh` directly into the package directory `models/pandey_kumar_mode1/290_method_c_case3/`.
7. **Bitwise Physics Preservation:** Frozen UEL `f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`) preserved bitwise.

---

## 2. Dynamic Equal-Load-Division Architecture

The single-job orchestrator manages the entire propagation sequence inside **one PBS allocation** on compute-node local scratch:

```
+---------------------------------------------------------------------------------------------------+
| SINGLE PBS ALLOCATION (16 CPUs SMP, 48 GB RAM, 72 h Walltime, Scratch9)                           |
|                                                                                                   |
|  [Cycle 0: Initial Coarse Solve]                                                                  |
|    - Coarse mesh (4,671 physical elements, 14,013 layered)                                        |
|    - Solve to onset load u2 = 0.0500 mm (RF2 = 3.9288 kN)                                         |
|         |                                                                                         |
|         v                                                                                         |
|  [Adaptive Remeshing Loop: k = 1, 2, ..., until completion]                                       |
|    - Check Completion: is x_tip >= 64.0 mm OR RF2 < 5% of peak RF2?                               |
|        YES -> Terminate and emit final completion receipt                                         |
|        NO  -> Proceed with Cycle k                                                                |
|    - Remesh: Minimized corridor box x in [8.5, 20.0], y in [60.0, 77.0] mm (24,832 elements)     |
|    - Transfer: Nodal (u, d) and GP history H with convex_clamp (H >= 0, 0 <= d <= 1)              |
|    - Assemble: 3-layer coupled deck (Step 1 hold at donor u2, Step 2 advance by load_increment_mm)|
|    - Solve: Abaqus 2023 with 16 CPUs interactive, dt_min = 1e-14, line search                     |
|    - Sta Monitor: If dt < dt_min (1e-14), stop cycle gracefully, extract last converged increment |
|    - Gates: Check |Delta RF2| <= 5.0%, Gamma continuity, non-healing d_max >= d_trans - 1e-4      |
|    - Advance: Set donor state from terminal converged increment, k = k + 1                        |
+---------------------------------------------------------------------------------------------------+
```

### Granularity and Dynamic Schedule

| Parameter | Identifier | Value / Behavior | Source / Justification |
| :--- | :--- | :--- | :--- |
| **Adaptive Step Granularity** | `n_adaptive_steps` | User-settable (default: `4`) | Configures planned remeshes per pass; not a hard cap |
| **Equal Load Increment** | `load_increment_mm` | Default: `0.0100 mm` | Sized at roughly $2\times$ largest observed advance ($0.0061\,\text{mm}$) |
| **Onset Displacement** | `coarse_u2_mm` | `0.0500 mm` | Initial elastic pre-cracking onset |
| **Displacement Cap** | Final $u_2$ limit | **NONE** | Uncapped; loops dynamically until complete severance |
| **Completion Criterion A** | Crack tip position | $x_{\text{tip}} \ge 64.0\,\text{mm}$ | Full propagation to right plate edge ($W = 65.0\,\text{mm}$) |
| **Completion Criterion B** | Load severance drop | $RF_2 < 0.05 \times RF_{2,\text{peak}}$ | Complete structural failure ($>95\%$ load release) |

---

## 3. Forensic Findings from Jobs 4 and 5 Corrected Against Committed Records

In compliance with `GAP-FW-03`, all statements regarding prior jobs are strictly aligned with committed repository records:

1. **Step-1 Re-Equilibration Convergence:**
   - In Job 4: Step 1 converged in **1 increment and 2 Newton iterations**, achieving force continuity $\Delta RF_2 = -0.2897\%$ ($3.9361\,\text{kN}$ vs donor $3.9475\,\text{kN}$, within $\le 5.0\%$).
   - In Job 5: Step 1 converged in **1 increment and 2 Newton iterations**, achieving force continuity $\Delta RF_2 = -0.9501\%$ ($3.8692\,\text{kN}$ vs donor $3.9064\,\text{kN}$, within $\le 5.0\%$).
2. **Increment-12 Residual Rebound Mechanism:**
   - Forensics of `PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5.msg` demonstrate that steep cohesive damage gradients triggered residual rebounds at nodes **$0.19$ to $0.61\,\text{mm}$ ahead of the terminal tip** ($x_{\text{tip}} = 14.1848\,\text{mm}$):
     * Node 19880 at $(14.5816, 69.8305)\,\text{mm}$
     * Node 20110 at $(14.6996, 69.5430)\,\text{mm}$
     * Node 43706 at $(14.4851, 69.5527)\,\text{mm}$
     * Node 19975 at $(14.4759, 69.7949)\,\text{mm}$
     * Node 4328 at $(14.3733, 69.7467)\,\text{mm}$
   - Residual forces rebounded from $\sim 10^{-4}$ up to $+3.64 \times 10^{-3}\,\text{kN}$, forcing repeated cutbacks down to $\Delta t = 6.99 \times 10^{-14}$ and hitting the $\Delta t_{\min} = 10^{-14}$ floor at attempt 5.
3. **Displacement Limits Reached:**
   - Job 4 terminal displacement: $u_2 = 0.056835\,\text{mm}$ (Increment 11).
   - Job 5 terminal displacement: $u_2 = 0.057595\,\text{mm}$ (Increment 11).
4. **Mesh Discretization Totals:**
   - Initial Coarse Mesh: **4,671 physical elements** ($14,013$ layered elements, $4,813$ physical nodes).
   - Job 5 Mesh: **64,653 physical elements** ($193,959$ layered elements, $64,106$ physical nodes, $64,107$ with `N_RP`).
   - Minimized Corridor Physical Mesh: **24,832 physical elements** ($74,496$ layered elements, $24,738$ nodes).
   - Element count reduction: $(64,653 - 24,832) / 64,653 = \mathbf{61.59\%}$ reduction in physical elements, substantially reducing system matrix dimensions and memory footprint.

---

## 4. Minimized Refinement Corridor Geometry & Mesh Audit

The physical mesh `PK_METHOD_C_CASE3_ADAPTIVE_PHYS.inp` was generated using Abaqus CAE with the minimized corridor box:

### Corridor Dimensions
- **Corridor Box:** $x \in [8.5, 20.0]\,\text{mm}$, $y \in [60.0, 77.0]\,\text{mm}$
- **Width:** $11.5\,\text{mm}$, **Height:** $17.0\,\text{mm}$, **Area:** $195.5\,\text{mm}^2$
- **Area Reduction:** $(885.0 - 195.5) / 885.0 = \mathbf{77.9\%}$ reduction vs broad corridor ($885.0\,\text{mm}^2$).

### Measured Mesh Audit Metrics
- Total Nodes: **24,738**
- Total Elements: **24,832**
- Quad Elements: **24,189** ($97.41\%$)
- Triangle Elements: **643** ($2.59\%$)
- **Gate 01 (Jacobian):** Strictly positive ($\min(\det(J)) > 0$, PASS).
- **Gate 02 (Quad Fraction):** $97.41\% \ge 85.0\%$ (PASS).
- **Gate 03 (Aspect Ratio):** Mean aspect ratio $1.26 \le 2.5$, maximum $3.88 \le 4.0$ (PASS).
- **Gate 04 (Element Sizing):** Refined corridor $h_{\text{ref}} = 0.140\,\text{mm} < l_0 / 2 = 0.1425\,\text{mm}$ ($l_0 = 0.285\,\text{mm}$, PASS).

---

## 5. Physical Convergence & State Integrity Gates

1. **Fixed-Load Force Continuity Gate:**
   $$\left|\frac{RF_{2}^{\text{receiver, Step 1}} - RF_{2}^{\text{donor, terminal}}}{RF_{2}^{\text{donor, terminal}}}\right| \times 100\% \le 5.0\%$$
2. **Fracture Energy Continuity Gate ($G_c$-Normalized):**
   $$\Gamma = \frac{E_{\text{frac}}}{G_c}$$
   Evaluates fracture surface area continuity. For standard transitions with identical $G_c$, $|\Delta E_{\text{frac}}| \le 5.0\%$. When material parameter changes are disclosed, normalized crack surface area $\Gamma$ is verified monotonic.
3. **Zero-Healing Gate:**
   $$d_{\max}^{\text{terminal}} \ge d_{\max}^{\text{transferred}} - 1.0 \times 10^{-4}$$
   Guarantees that phase-field damage remains irreversible across mesh transfers.
4. **Dynamic Terminal Frame Labelling:**
   Terminal frames are dynamically identified from `.sta` records filtering unconverged attempts (e.g. `Increment 11 (terminal converged state)`).

---

## 6. HPC Batch Configuration & Notification Integration

- **Submission Script:** `models/pandey_kumar_mode1/290_method_c_case3/submit_case3_single_job_framework.pbs`
- **Resource Directives:**
  - Nodes: `select=1:ncpus=16:mpiprocs=1:ompthreads=16:mem=48gb`
  - Walltime: `72:00:00`
  - Queue: `entry_imfdfkmq` / `normal_imfdfkmq`
  - Execution Scratch: `/scratch9/pr21vyci/runs/mode1_290_method_c_case3_single_job`
- **Dual-Channel Notifications (`NOTE-FW-03`):**
  - PBS Email: `#PBS -m abe -M pr21vyci@mailserver.tu-freiberg.de`
  - Package Script: `models/pandey_kumar_mode1/290_method_c_case3/job_notifications.sh` committed into the package directory and sourced directly.
  - Shell Traps: automated `notify_start` and terminal exit traps installed.
- **Orchestrator Invocation:**
  ```bash
  python3 "${RUN_DIR}/case3_single_job_orchestrator.py" \
      --run-dir "${RUN_DIR}" \
      --n-adaptive-steps 4 \
      --load-increment-mm 0.01 \
      --coarse-u2-mm 0.05 \
      --cpus 16
  ```

---

## 7. Verification Test Suite Results

The offline unit test suite `tests/unit/test_method_c_case3_framework_package.py` was revised to validate:
1. Frozen UEL SHA-256 bitwise integrity (`CE8D5EDC...`).
2. Orchestrator parameterization (`n_adaptive_steps`, `load_increment_mm`, equal load division, no 1.5 mm cap).
3. Crack completion logic ($x_{\text{tip}} \ge 64.0\,\text{mm}$ or $RF_2 < 5\%$).
4. Minimized corridor geometry ($195.5\,\text{mm}^2$, $h_{\text{ref}} \le l_0/2$).
5. Cutback floor detection and terminal converged frame parsing from `.sta`.
6. Gate evaluation with authentic Job-5 RF2 values ($3.9063646 \to 3.8692487\,\text{kN}$, `NOTE-FW-01`).
7. PBS script directives and execution path invocation.
8. Manifest schema and accounting integrity.
9. Notification script existence in package directory (`NOTE-FW-03`).

---

## 8. Summary of Package Deliverables

| File Path | Description |
| :--- | :--- |
| `scripts/remeshing/case3_single_job_orchestrator.py` | In-allocation orchestrator implementing execution loop, equal load division, and completion criteria |
| `scripts/remeshing/generate_case3_adaptive_corridor_mesh.py` | Corridor partition spec, geometric audit, and Abaqus CAE mesh generator |
| `models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_ADAPTIVE_PHYS.inp` | Generated physical mesh: 24,832 physical elements, 24,738 nodes, 97.41% quad |
| `models/pandey_kumar_mode1/290_method_c_case3/METHOD_C_CASE3_FRAMEWORK_MANIFEST.json` | Configuration manifest with parameterised steps, equal load division, and completion bounds |
| `models/pandey_kumar_mode1/290_method_c_case3/submit_case3_single_job_framework.pbs` | 16-CPU, 48-GB, 72-hour PBS batch script invoking live orchestrator |
| `models/pandey_kumar_mode1/290_method_c_case3/job_notifications.sh` | Committed package dual-channel notification integration script |
| `tests/unit/test_method_c_case3_framework_package.py` | Offline unit test suite covering all specifications |
| `docs/validation/METHOD_C_CASE3_FRAMEWORK_PACKAGE_REPORT.md` | This revised checkpoint report |
