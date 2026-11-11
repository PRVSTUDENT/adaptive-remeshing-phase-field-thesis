# User Guide: Reusable Method A Adaptive-Remeshing Phase-Field Framework

**Document Version:** 1.0.0  
**Date:** 2026-11-11  
**Master Thesis Reference:** Application of Built-in Adaptive Remeshing and Mesh Refinement Features in Abaqus to Fracture Simulations Using Phase-Field User Elements  
**Author:** Gemini Antigravity (Computational Materials Science Research Executor)  
**Research Freeze:** December 13, 2026 | **Final Thesis Submission:** January 13, 2027

---

## 1. Overview & Purpose

The **Method A Adaptive-Remeshing Framework** is an automated, configuration-driven Python framework that interfaces with Abaqus/Standard and Abaqus/CAE to perform indicator-driven spatial mesh adaptation for regularized phase-field fracture mechanics.

Unlike conventional heuristic crack-corridor refinement methods that require manually prescribed geometric bounding boxes or known crack propagation trajectories, this framework:
1. Validates standard 2D continuum coarse finite-element models (`.inp`).
2. Computes the authentic Superconvergent Patch Recovery (SPR) stress jump error indicator (`MISESERI`).
3. Executes native Abaqus CAE `adaptiveRemesh` to generate optimal, continuous locally refined physical meshes.
4. Reconstructs a 3-layer coupled user element architecture (Phase UEL, Mechanical UEL, and Visualizer UMAT).
5. Postprocesses reaction force equilibrium ($-\sum_{N_{\text{BOTTOM}}} RF_{2, j}$), volume-integrated element energies (`SDV17`, `SDV18`), and damage fields ($d \in [0, 1]$).
6. Generates publication-quality 300-DPI vector visualizations and machine-readable validation reports.

---

## 2. Framework Architecture & Modules

The framework is organized into modular, independently testable components under `scripts/method_a_framework/`:

```
scripts/method_a_framework/
├── __init__.py           # Package exports
├── config.py             # Configuration schema, physics bounds, and JSON I/O
├── input_validator.py    # 2D continuum topology validation and mesh quality auditing
├── indicator.py          # SPR stress error extraction and continuous sizing field model
├── deck_builder.py       # 3-layer UEL production deck reconstruction and MPC coupling
├── postprocessor.py      # Bottom-edge equilibrium, energy assembly, and damage validation
├── visualizer.py         # Publication-quality matplotlib graphics (wireframes, F-u, energies)
└── pipeline.py           # Unified end-to-end orchestration entrypoint
```

---

## 3. Supported Input Models & Element Topologies

### Supported Elements:
- **Plane Strain / Plane Stress 2D Elements:** `CPE4`, `CPE4R`, `CPS4`, `CPS4R` (4-node quadrilaterals), `CPE3`, `CPS3` (3-node triangles).
- **Physical Boundary Requirements:**
  - Lower boundary constrained along $y$ (`N_BOTTOM`).
  - Pin constraint preventing rigid horizontal motion (`N_PIN`).
  - Upper boundary coupled kinematically to an independent reference node (`N_RP`) via linear constraint equations (`*EQUATION`).

### Unsupported Elements (Rejected with Diagnostics):
- 3D continuum elements (`C3D8`, `C3D4`, `C3D10`, `C3D20`).
- 1D beam or truss elements (`B21`, `B31`, `T2D2`, `T3D2`).
- Shell or membrane elements (`S4R`, `S3`, `M3D4`).

---

## 4. Configuration Specification

Configuration files are formatted in standard JSON or Python dictionaries. Example:

```json
{
  "benchmark_name": "Five_Hole_Multi_Void_Benchmark",
  "geometry": {
    "plate_width": 1.0,
    "plate_height": 1.0,
    "notch": null,
    "voids": [
      {"name": "h1", "type": "semicircle_left", "x": 0.0, "y": 0.50, "r": 0.10},
      {"name": "h2", "type": "circle", "x": 0.35, "y": 0.45, "r": 0.10},
      {"name": "h3", "type": "circle", "x": 0.60, "y": 0.55, "r": 0.05},
      {"name": "h4", "type": "circle", "x": 0.75, "y": 0.50, "r": 0.075},
      {"name": "h5", "type": "semicircle_right", "x": 1.0, "y": 0.45, "r": 0.075}
    ]
  },
  "material": {
    "E": 210.0,
    "nu": 0.30,
    "Gc": 0.0027,
    "l0": 0.0080,
    "k_residual": 1e-7,
    "constitutive_split": "amor"
  },
  "remeshing": {
    "indicator": "MISESERI",
    "sizing_method": "UNIFORM_ERROR",
    "error_target_pct": 1.85,
    "h_min": 0.001,
    "h_max": 0.020,
    "refinement_factor": 10.0,
    "coarsening_allowed": false
  },
  "loading": {
    "step1_disp": 0.0050,
    "step2_disp": 0.0100,
    "step1_dt": 0.0005,
    "step2_dt": 0.0002,
    "dt_min": 1e-9
  }
}
```

### Pre-configured Benchmark Templates:
The framework repository supplies ready-to-use, fully validated configuration files under `configs/method_a/`:
1. `mode1_benchmark.json`: Primary Benchmark 1 (Mode-I $1.0 \times 1.0\,\text{mm}$ single-edge notched square plate, $\ell_0 = 0.0075\,\text{mm}$, 14,933 physical elements, mixed UEL split).
2. `five_hole_benchmark.json`: Primary Benchmark 2 (Five-hole multi-void tension specimen, $\ell_0 = 0.0080\,\text{mm}$, 13,034 physical elements, Amor split UEL).
3. `off_axis_hole_benchmark.json`: Benchmark 3 (Mode-I plate with off-axis circular hole at $(0.65, 0.65)\,\text{mm}$, $R = 0.10\,\text{mm}$, Candidate E10, 9,164 physical elements, mixed UEL split).

---

## 5. End-to-End Workflow & Command-Line Usage

### Step 1: Preprocessing & Deck Reconstruction
Run the pipeline to validate the coarse deck, audit the adapted physical mesh, and generate the 3-layer production deck:

```python
from scripts.method_a_framework.pipeline import MethodAFrameworkPipeline

pipeline = MethodAFrameworkPipeline("configs/method_a/five_hole_benchmark.json")

pipeline.run_preprocessing_and_deck_generation(
    coarse_inp_path="models/.../PK_F1714_JOB1_COARSE.inp",
    adapted_phys_inp_path="models/.../PK_F1714_JOB2_ADAPTED_PHYS.inp",
    output_prod_inp_path="models/.../PK_F1714_JOB2_ADAPTED_PROD.inp"
)
```

### Step 2: Postprocessing & Scientific Validation
Once the Abaqus simulation completes, extract the authentic reaction forces, energies, and damage fields:

```python
# Process extracted telemetry dictionary or JSON output:
validation_summary = pipeline.run_postprocessing_and_validation(
    raw_telemetry_or_json="results/.../f1714_five_hole_telemetry.json",
    out_report_json="results/.../f1714_validation_report.json"
)
```

---

## 6. Mathematical & Thermodynamic Principles

1. **Reaction Force Recovery via Global Equilibrium:**
   $$\sum F_y = 0 \implies F_{\text{tensile}}(t) = -\sum_{j \in \text{N\_BOTTOM}} RF_{2, j}(t)$$
   Guarantees finite, non-zero reaction load without relying on reference node printouts.

2. **Volume-Integrated Domain Energies:**
   In the visualizer layer, `STATEV(17)` ($E_{\text{frac}}$) and `STATEV(18)` ($E_{\text{elas}}$) are volume-integrated at element level:
   $$E_{\text{elas}} = \int_{\Omega_e} \psi_e \, d\Omega = \sum \text{CJAC} \cdot \psi_{e, \text{pt}}$$
   Summing across all $N_{\text{phys}}$ active elements strictly yields the exact global thermodynamic energy balance in Joules ($\text{kN}\cdot\text{mm}$).

3. **Continuous Spatial Resolution:**
   Enforces $h_{\min} \le \ell_0 / 2$ to ensure that the finite-element discretization fully resolves regularized diffuse damage gradients.

---

## 7. Multi-Benchmark Verification & Computational-Cost Synthesis

The framework has been benchmarked across four distinct structural fracture problems:

| Benchmark Configuration | Physical Elements | Layered Elements | Element Parity vs Target | Runtime / Speedup | Key Fracture Behavior Verified |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Benchmark 1: Mode-I Notch** (Pandey & Kumar 2025, Sec. 4.1) | 14,933 | 44,799 | $+7.1\%$ vs 13,941 | Step 1 Exit 0 (2,000 incs) | Autonomous notch-tip stress concentration localization |
| **Benchmark 2: Five-Hole Multi-Void** (Pandey & Kumar 2025, Sec. 4.5) | 13,034 | 39,102 | $+0.70\%$ vs 12,944 | 6,051 incs / 8h walltime | 4 inter-hole ligament stress concentrations resolved |
| **Benchmark 3: Off-Axis Hole E10** (Master Thesis Candidate E10) | 9,164 | 27,492 | N/A (Candidate E10) | 32 min ($2.05\times$ speedup) | Primary hole arrest + secondary snap-through to free edge |
| **Section 4.3 Staggered Benchmark** (Pandey & Kumar 2025, Sec. 4.3) | 10,065 | 30,195 | $-3.96\%$ vs 10,480 | 121.9 min ($2.42\times$ speedup) | Notch initiation, void penetration, secondary reloading & severance |

Complete validation details and forensic telemetry are available in:
- `docs/validation/F1714_FIVE_HOLE_BENCHMARK_REPORT.md`
- `docs/validation/F1709_JOB2_REPRODUCTION_REPORT.md`
- `docs/validation/F1710_AUTHENTIC_ADAPTIVE_MESH_REPORT.md`

