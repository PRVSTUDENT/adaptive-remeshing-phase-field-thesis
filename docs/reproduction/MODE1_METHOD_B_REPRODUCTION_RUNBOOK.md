# Mode-I Method B Adaptive Remeshing Reproduction Runbook and Successor Specification

- **Document:** `docs/reproduction/MODE1_METHOD_B_REPRODUCTION_RUNBOOK.md`
- **Governing Task:** `F1597-CORRECT-PACKAGE72-STATE-TRANSFER`
- **Configuration Master:** `models/pandey_kumar_mode1/canonical_mode1_method_b_config.json`
- **Status:** **`APPROVED_FOR_REPRODUCTION`**
- **Milestone Anchors:** Architecture Decision (November 13), Thesis Candidate Freeze (December 13)

---

## 1. Executive Summary & Scope

This runbook establishes a self-contained, clean-checkout reproduction contract for the complete Mode-I adaptive remeshing workflow (Method A/B) developed in reproduction of Pandey & Kumar (2025).

### Core Methodological Principles
1. **Primary Deliverable Focus**: The complete, production Mode-I workflow consists of linear-elastic coarse pre-analysis, posteriori stress recovery (MISESERI), automated crack-corridor pre-refinement (Gmsh), dual-element UEL assembly (`f42_mixed_uel.for`), and full fracture propagation to terminal horizon $u = 0.010\,\text{mm}$.
2. **Method C Scoping**: Multi-cycle in-analysis remeshing with nonmatching state transfer (Method C) is an optional successor research extension, not a thesis-completion requirement. Package 89 (`Job 1416539.mmaster02`) serves as a qualified single-step benchmark at crack initiation, but is not required to reproduce the primary Method B results.
3. **Model Scale Separation**: The canonical Mode-I benchmark is a **$1.0 \times 1.0\,\text{mm}$** square plate with initial slit $a_0 = 0.5\,\text{mm}$ at $y = 0.5\,\text{mm}$ (producing peak reaction force $F_{\max} \approx 743.02\,\text{N}$ and initial stiffness $K_0 \approx 137.89\,\text{kN/mm}$). It must not be conflated with the miniature $0.1 \times 0.1\,\text{mm}$ test specimen ($F_{\max} \approx 185.34\,\text{N}$) used in Package 89 state-transfer experimentation.

---

## 2. System Prerequisites & Environment Setup

To ensure clean-checkout portability across workstation and HPC environments, the workflow avoids hardcoded paths, user credentials, or environment-specific aliases.

### 2.1 Software Requirements
| Component | Minimum Version | Recommended Version | Verification Command |
| :--- | :--- | :--- | :--- |
| **Python** | 3.10 | 3.11+ | `python --version` |
| **NumPy / SciPy** | 1.22+ / 1.8+ | Latest stable | `python -c "import numpy, scipy; print('OK')"` |
| **Gmsh** | 4.10 | 4.11+ | `gmsh -version` |
| **Abaqus** | 2022 | 2023 HF4 | `abaqus whereami` |
| **Intel Fortran Compiler**| OneAPI 2023 | Classic / Ifort 2021+ | `ifort -v` or `ifx -v` |
| **PowerShell** | 5.1 (Win) | 7.2+ Core | `$PSVersionTable.PSVersion` |

### 2.2 Environment Variables
Ensure the following variables are defined in your shell or profile:
```bash
# Linux / HPC
export ABAQUS_BAT="abaqus"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Windows PowerShell
$env:ABAQUS_BAT = "abaqus"
$env:PYTHONPATH = "$((Get-Location).Path)"
```

---

## 3. Physical Problem & Discretization Specification

### 3.1 Specimen Geometry & Boundary Conditions
- **Domain**: Square plate $\Omega = [0, 1.0]\,\text{mm} \times [0, 1.0]\,\text{mm}$, thickness $t = 1.0\,\text{mm}$.
- **Crack Geometry**: Initial horizontal slit along $y = 0.5\,\text{mm}$ extending from $x = 0.0\,\text{mm}$ to $x = 0.5\,\text{mm}$.
- **Flank Representation**: Opposing slit flanks are discretized with duplicate, coincident node pairs at $y = 0.5\,\text{mm}$ ($x \le 0.5\,\text{mm}$) with detached topology to model traction-free slit surfaces.
- **Boundary Sets**:
  - `N_BOTTOM` ($y = 0.0\,\text{mm}$): Displacement constraint $u_y = 0.0$.
  - `N_BOTTOM_PIN` ($x = 0.0, y = 0.0\,\text{mm}$): Rigid translation pin $u_x = 0.0$.
  - `N_TOP` ($y = 1.0\,\text{mm}$): Kinematically coupled to reference node `N_RP`.
  - `N_RP`: Monotonic displacement boundary condition $u_y(t) = 0.010\,\text{mm}$.

### 3.2 Material Parameters (AT2 Brittle Phase-Field Formulation)
- Young's modulus: $E = 210.0\,\text{GPa} = 210.0\,\text{kN/mm}^2$
- Poisson's ratio: $\nu = 0.3$
- Critical fracture energy release rate: $G_c = 2.7\,\text{N/mm} = 0.0027\,\text{kN/mm}$
- Phase-field regularization length scale: $\ell_0 = 0.0075\,\text{mm} = 7.5\,\mu\text{m}$
- Degradation function: $g(d) = (1-d)^2 + k_{\text{res}}$ with $k_{\text{res}} = 10^{-7}$
- Strain energy decomposition: Spectral split (Miehe et al.)

### 3.3 Mesh Discretization Hierarchy & Resolution
1. **Coarse Pre-Analysis Mesh (`PK_M1_JOB1_UEL_2906.inp`)**:
   - Elements: 2,906 quad elements.
   - Nodes: 2,989 physical nodes.
   - Solver DOFs: $8,969$ active equations ($3 \times 2,989 + 2$ reference DOFs).
   - Degree-of-Freedom Reduction: **$80.74\%$ reduction** compared to S1 reference ($46,568$ DOFs).
2. **Adapted Fracture Mesh (`M1_MB_NATIVE_FINAL_1S.inp`)**:
   - Elements: 14,677 quad elements.
   - Nodes: 14,647 physical nodes.
   - Solver DOFs: $43,943$ active equations.
   - Crack-tip element size: $h_{\min} = 1.15\,\mu\text{m}$ ($h / \ell_0 \approx 0.153$).
   - Refinement Corridor: $y \in [0.48, 0.52]\,\text{mm}$ across $x \in [0.45, 1.0]\,\text{mm}$.
   - Linear Resolution Ratio: $1.50\,\mu\text{m} / 1.15\,\mu\text{m} = \mathbf{1.304\times}$ finer linear resolution than reference S1.
   - DOF Savings: $5.64\%$ fewer DOFs than reference S1 while providing $1.304\times$ finer crack-tip resolution; $>98.5\%$ fewer DOFs compared to a hypothetical uniform $1\,\mu\text{m}$ mesh ($>3\times 10^6$ DOFs, theoretical baseline).
3. **Reference Discretization (`PK_MODE1_REF15K_ENERGY.inp`)**:
   - Elements: 15,192 quad elements.
   - Nodes: 15,522 physical nodes.
   - Solver DOFs: $46,568$ active equations.
   - Crack-tip element size: $h_{\min} = 1.50\,\mu\text{m}$.

---

## 4. Execution Tiers: Reproduction Procedures

Reproduction is structured into three distinct operational tiers to suit varying computing constraints.

### 4.1 TIER 1: Archived Evidence Replay (Zero Abaqus / HPC Required)
- **Target Audience**: Researchers, peer reviewers, and automated CI pipelines without access to proprietary Abaqus licenses or cluster resources.
- **Execution Time**: $< 5$ seconds.
- **Prerequisites**: Python 3.10+ standard library.
- **Procedure**:
  ```bash
  python scripts/validation/verify_mode1_reproduction_contract.py
  ```
- **Verification Performed**:
  - Bitwise SHA-256 validation of frozen UEL `f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`).
  - Validation of input deck geometry, node coordinates, and slit-flank node pairs.
  - Replay of archived solver output (`M1_MB_NATIVE_14K_TERMINAL_EVALUATION.json` and `PK_MODE1_REF15K_ENERGY.inp`).
  - Exact computation and assertion of all 10 release acceptance gates.

### 4.2 TIER 2: Local Preflight & Syntax Datacheck
- **Target Audience**: Researchers preparing a local modification or validating input decks prior to cluster submission.
- **Execution Time**: $< 60$ seconds.
- **Prerequisites**: Local Abaqus 2022+ with Fortran compiler.
- **Procedure**:
  ```bash
  abaqus job=M1_MB_NATIVE_PREFLIGHT \
         input=models/pandey_kumar_mode1/38_method_b_native_final_14k/M1_MB_NATIVE_FINAL_1S.inp \
         user=models/pandey_kumar_mode1/reproduction_package_gate6b_energy/f42_mixed_uel.for \
         datacheck interactive
  ```
- **Acceptance Criteria**:
  - `M1_MB_NATIVE_PREFLIGHT.log` terminates with `THE ANALYSIS HAS COMPLETED SUCCESSFULLY`.
  - Zero syntax errors, zero missing node sets, zero unmapped user element types.

### 4.3 TIER 3: Full Production HPC Execution
- **Target Audience**: Researchers performing an independent end-to-end recalculation on high-performance computing infrastructure.
- **Execution Time**: $\sim 3.5$ hours (8-thread SMP) or $\sim 6.5$ hours (1-CPU serial).
- **HPC Resource Configuration**:
  - Resource allocation: 1 chunk / 1 node, 8 CPU cores (`select=1:ncpus=8:mpiprocs=1:ompthreads=8`).
  - Memory: $16\,\text{GB}$ RAM (`mem=16gb`).
  - Walltime: $08:00:00$ (`walltime=08:00:00`).
  - Execution mode: Single-rank shared-memory SMP (`f42_mixed_uel.for` is not qualified for multi-rank distributed MPI).
- **Execution Command via Guarded Controller**:
  ```powershell
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/hpc/Invoke-Mode1Execution.ps1 `
      -ManifestPath "models/pandey_kumar_mode1/38_method_b_native_final_14k/PACKAGE_MANIFEST.json"
  ```
- **Dual-Channel Notification**:
  - PBS mail alerts: `#PBS -m abe` directed to configured user email.
  - Telegram webhook: Triggered on submission, job start, and terminal exit via `job_notifications.sh`.

---

## 5. Computational Performance & Timing Accounting

To maintain rigorous scientific accuracy, execution timings are explicitly categorized as measured solver walltime vs estimated workstation preprocessing:

| Phase | Description | Measured / Estimated | Duration (s) | Duration (Formatted) |
| :--- | :--- | :--- | :--- | :--- |
| **Pre-Analysis** | Coarse elastic solve (2,906 quads) | Workstation Benchmark Estimate | $8.0\,\text{s}$ | $00:00:08$ |
| **Error Recovery** | MISESERI stress recovery & sizing field | Workstation Benchmark Estimate | $4.0\,\text{s}$ | $00:00:04$ |
| **Remeshing** | Gmsh graded crack-corridor mesh | Workstation Benchmark Estimate | $25.0\,\text{s}$ | $00:00:25$ |
| **State Transfer** | Method B (zero transfer required) | Exact / Methodological | $0.0\,\text{s}$ | $00:00:00$ |
| **Solver (8-Thread SMP)** | Job 1412873 full fracture propagation | **Exact Measured PBS Walltime** | $\mathbf{12,920\,\text{s}}$ | $\mathbf{03:35:20}$ |
| **Solver (1-CPU Serial)** | Job 1412872 full fracture propagation | **Exact Measured PBS Walltime** | $\mathbf{23,498\,\text{s}}$ | $\mathbf{06:31:38}$ |
| **Post-Processing** | Reaction force & energy extraction | Workstation Benchmark Estimate | $15.0\,\text{s}$ | $00:00:15$ |

### Speedup and Overhead Findings
- **Measured Solver Speedup**: $S_{\text{solver}} = 23,498\,\text{s} / 12,920\,\text{s} = \mathbf{1.8187\times}$ ($\ge 1.5\times$ target, PASS).
- **Full-Workflow Estimated Speedup**: $S_{\text{workflow}} = 23,550\,\text{s} / 12,972\,\text{s} = \mathbf{1.8154\times}$ ($\ge 1.5\times$ target, PASS).
- **Total Offline Pre-Refinement Overhead**: $(8 + 4 + 25)\,\text{s} = 37.0\,\text{s}$ ($0.285\%$ of total runtime), demonstrating that adaptive pre-refinement overhead is completely negligible.

---

## 6. Primary Acceptance Gates & Tolerances

Every reproduction attempt must evaluate the following ten quantitative acceptance criteria against the recorded baselines:

```
+---------------------------------------------------------------------------------------------------+
| GATE                               | METRIC DESCRIPTION           | TOLERANCE      | MEASURED     |
+------------------------------------+------------------------------+----------------+--------------+
| 1. Elastic Stiffness (K0)          | Parity vs reference S1       | <= 0.05%       | -0.0389%     |
| 2. Peak Reaction Force (Fmax)      | Parity vs reference S1       | <= 2.0%        | -1.947%      |
| 3. Peak Displacement (u_peak)      | Parity vs reference S1       | <= 2.5%        | -2.220%      |
| 4. Coarse Screening DOF Savings    | Reduction vs reference S1    | >= 70.0%       | 80.74%       |
| 5. Adapted vs Uniform 1um Savings  | Reduction vs uniform 1um     | >= 90.0%       | 98.54% (hyp) |
| 6. Loading Partition Invariance    | Pre-analysis 1S/2S/4S diff   | 0.0 max diff   | 0.0          |
| 7. SMP Parallel Speedup            | 8-thread vs 1-CPU serial     | >= 1.5x        | 1.8187x      |
| 8. UEL Hash Integrity              | Bitwise SHA-256 match        | Exact Match    | 100% Match   |
| 9. State Transfer PoC (Pkg 89)     | Force continuity at init     | <= 5.0%        | +2.266%      |
| 10. Architecture Contract          | 5-Layer decoupled framework  | Formally Spec. | PASS         |
+---------------------------------------------------------------------------------------------------+
```

---

## 7. Extensible 5-Layer Successor Architecture

To enable future researchers to extend the verified 2D Mode-I implementation to Mode-II mixed mode, 3D geometries, dynamic fracture, or alternative constitutive models, the framework is architected into five decoupled layers.

### 7.1 Layer Definitions & Maturity Status
```
[ Layer 1: Problem Definition & Topology ]           -> Status: IMPLEMENTED (2D Mode-I) / DESIGN ONLY (3D/Mode-II)
[ Layer 2: Discretization & Adaptation Engine ]       -> Status: IMPLEMENTED (Gmsh Quad) / PROTOTYPE (Corridor Sizing)
[ Layer 3: Constitutive & Subroutine Schema ]         -> Status: IMPLEMENTED (AT2 Dual-UEL) / PROTOTYPE (Single-Process Re-equil)
[ Layer 4: Thermodynamic State Transfer Engine ]     -> Status: IMPLEMENTED (Single-Step Pkg 89) / FUTURE WORK (Multi-Cycle)
[ Layer 5: Multi-Stage Re-equilibration Solver ]      -> Status: IMPLEMENTED (4-Step Sequential) / FUTURE WORK (Automated Driver)
```

1. **Layer 1: Problem Definition & Topology**
   - *Implemented*: Parametric square domain with horizontal sharp slit at $y = 0.5\,\text{mm}$; duplicate slit-flank node pairs; spectral AT2 linear-elastic brittle constitutive law ($E = 210\,\text{GPa}$, $\ell_0 = 7.5\,\mu\text{m}$, $G_c = 2.7\,\text{N/mm}$).
   - *Design Only*: Curved crack path geometries; mixed-mode shear boundary conditions; 3D planar crack surfaces.
2. **Layer 2: Discretization & Adaptation Engine**
   - *Implemented*: Coarse quad pre-analysis mesher; Zienkiewicz–Zhu / MISESERI stress error recovery; conforming Gmsh crack-corridor refinement.
   - *Prototype*: Automatic bounding box detection from damage threshold contours.
   - *Limitation*: Prescribed corridor bounding box ($y \in [0.48, 0.52]\,\text{mm}$); arbitrary curving crack path independence is NOT claimed.
3. **Layer 3: Constitutive & Subroutine Schema**
   - *Implemented*: Dual-element user subroutine `f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`); active DOFs 1,2 on JTYPE 2 (mechanics), active DOF 3 on JTYPE 1 (phase field); 18 state variables per element; independent internal energy balance accounting.
   - *Prototype*: Single-process persistence across sequential analysis steps.
4. **Layer 4: Thermodynamic State Transfer Engine**
   - *Implemented*: Slit-flank-aware spatial interpolation ($k\text{-d}$ tree with topological boundary partition); physical damage clamping $0 \le d \le 1$; point-wise history monotonicity $\mathcal{H}_B \ge \mathcal{H}_A$ ensuring zero physical healing. Verified in Package 89 (`1416539.mmaster02`).
   - *Future Work*: Automated transfer across multiple nonmatching remeshing cycles throughout the post-peak softening tail.
5. **Layer 5: Multi-Stage Re-equilibration Solver**
   - *Implemented*: Validated 4-stage re-equilibration sequence (Dirichlet State Injection $\to$ Frozen-Damage Mechanical Relaxation $\to$ Staggered Phase Subproblem $\to$ Forward Continuation).
   - *Future Work*: Fully automated external driver linking solve $\to$ error estimate $\to$ remesh $\to$ transfer $\to$ continue without manual deck generation.

---

## 8. Reproducibility Stopping Rule & Successor Handoff

### 8.1 Stopping Rule
The Mode-I reproduction package is formally declared **COMPLETE and FROZEN** when:
1. `canonical_mode1_method_b_config.json` is validated by automated regression test `test_mode1_clean_checkout_reproduction.py` passing 100% on a clean workspace.
2. All 10 acceptance gates pass within their pre-declared physical tolerances.
3. Raw numerical evidence (DAT, ODB, MSG, JSON receipts) remains bitwise verified and archived.
4. No further solver runs or input deck modifications are required for Mode-I thesis defense.

### 8.2 Successor Handoff & Highest-Priority Obstacle
- **Highest-Priority Obstacle for Successor**: Extending from the verified single-step transfer proof-of-concept (Package 89) to automated multi-cycle Method C adaptive remeshing across the deep post-peak softening tail ($u > 0.005\,\text{mm}$).
- **Technical Barrier Identified**: In the deep softening regime ($d > 0.8$), damage diffusion across nonmatching discretizations causes a small localized compliance perturbation, which under displacement control can trigger instantaneous cutbacks if the phase field is freed without the 4-stage staggered re-equilibration protocol developed in Package 89.
- **Recommended Successor Action**: Re-use the verified Layer 5 4-stage protocol within an automated Python loop driving Gmsh and Abaqus sequentially, preserving `f42_mixed_uel.for` bitwise unchanged.
