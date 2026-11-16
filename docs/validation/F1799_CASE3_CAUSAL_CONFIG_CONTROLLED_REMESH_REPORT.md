# Task F1799 Evidentiary Report: Case 3 Causal Configuration & Physical-Donor Controlled Remeshing

## 1. Executive Summary & Governance Metadata

| Attribute | Specification / Verification Value |
| :--- | :--- |
| **Task ID** | `F1799-CASE3-CAUSAL-CONFIG-AND-PHYSICAL-DONOR-CONTROLLED-REMESH` |
| **Predecessor Review** | `HND-F1798-CASE3-NATIVE-REMESH-001` (Decision: `REJECT`, Action: `CONTINUE`) |
| **Correlation ID** | `HND-F1799-CASE3-CONTROLLED-REMESH-001` |
| **Parent Commit** | `a34d7ff9a` |
| **Shared Implementation** | `scripts/remeshing/reusable_2d_adaptive_framework.py` |
| **Framework SHA-256** | `99EC77D2433EB5048DC9B4D70E5EA3B8468073C3BCEA342B7BFE139234700E6D` |
| **Production Fortran UEL** | `models/pandey_kumar_mode1/f42_mixed_uel.for` |
| **Frozen UEL SHA-256** | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` |
| **Cumulative PBS Submissions**| **35** (strictly preserved, exactly 0 new jobs submitted) |
| **Master Goal Status** | **`OPEN`** (Persistent loop active; `<!-- GOAL_COMPLETE -->` strictly withheld) |

---

## 2. Supervisor Directives from Task F1798 & Exact Resolutions

In the independent scientific review for Task F1798 (`HND-F1798-CASE3-NATIVE-REMESH-001`), the reviewer independently verified the generated physical mesh (`PK_F1798_CASE_3_ADAPT_PHYS.inp`, 1,934,333 bytes, SHA-256 `C3B84ECA...`, body hash `13B6770F...`, 26,891 elements, 97.23% quads, positive Jacobians, max AR 2.706), but identified specific configuration schema and documentary defects requiring immediate bounded correction in Task F1799:

### 2.1 Causal Configuration Schema Defect Resolution
* **Defect Identified:** In Task F1798, `causal_mode=true`, `max_frame_index=1`, and `max_frame_time=1.0` were placed at the JSON root of `configs/remeshing/f1798_case3_native_miseseri.json`. However, `AdaptiveConfig` in `scripts/remeshing/reusable_2d_adaptive_framework.py` parses these fields from `indicator_options`. Consequently, `cfg.causal_mode` parsed as `False`, `cfg.max_frame_index` as `None`, and `cfg.max_frame_time` as `None`.
* **Resolution Applied in F1799:**
  1. Authored `configs/remeshing/f1799_case3_native_miseseri.json` with `causal_mode: true`, `max_frame_index: 1`, and `max_frame_time: 1.0` inside `indicator_options` (as well as at root).
  2. Implemented explicit fail-closed runtime assertions in `scripts/remeshing/run_f1799_case3_controlled_remesh.py`:
     ```python
     assert cfg.causal_mode is True, "FAIL_CLOSED: cfg.causal_mode must be True!"
     assert cfg.max_frame_index == 1, "FAIL_CLOSED: cfg.max_frame_index must be 1!"
     assert cfg.max_frame_time == 1.0, "FAIL_CLOSED: cfg.max_frame_time must be 1.0!"
     ```
  3. Verified that `AbaqusNativeRemeshingEngine.execute_native_remesh()` executes with `c_mode = True`, successfully validating that `step_obj.frames` contains exactly 2 frames (index 0 and 1) and that no unconstrained future frames exist in the donor.

### 2.2 Material Unit Discrepancy Reconciliation
* **Defect Identified:** `PK_SEC43_COARSE_RECOVERY.inp` specifies $E = 210.0$ (in $\text{kN/mm}^2$ = GPa), whereas configuration JSON specifies $E = 210000.0$ MPa. The review directed explicit documentation and reconciliation without silently choosing one.
* **Resolution Applied in F1799:**
  1. **Governing Unit System:** The Case 3 production model (`PK_SEC43_COARSE_JOB1.inp` lines 15849-15856) adopts the standard structural SI-derived unit system:
     $$\text{Length: mm}, \quad \text{Force: kN}, \quad \text{Stress: } \frac{\text{kN}}{\text{mm}^2} \equiv \text{GPa}, \quad \text{Energy: kN}\cdot\text{mm} \equiv \text{J}$$
     In this system, $E = 210.0\text{ kN/mm}^2$ (= 210 GPa = 210,000 MPa), $G_c = 0.00228\text{ kN/mm}$ (= 2.28 N/mm), and $\ell_0 = 0.285\text{ mm}$.
  2. **Mathematical Scale-Invariance Proof:** In linear elasticity without geometric nonlinearity (`NLGEOM=NO`), the displacement vector scales linearly with applied loads, and the stress tensor scales linearly with Young's modulus $E$:
     $$\boldsymbol{\sigma}(\mathbf{x}) = E \cdot \tilde{\boldsymbol{\sigma}}(\mathbf{x})$$
     Abaqus computes the elemental recovered stress error $\Vert \mathbf{e}_\sigma \Vert_{L_2}$ and the average stress $\Vert \bar{\boldsymbol{\sigma}} \Vert_{L_2}$. Both quantities scale linearly with $E$:
     $$\Vert \mathbf{e}_\sigma \Vert = E \cdot \Vert \tilde{\mathbf{e}}_\sigma \Vert, \qquad \Vert \bar{\boldsymbol{\sigma}} \Vert = E \cdot \Vert \tilde{\bar{\boldsymbol{\sigma}}} \Vert$$
     The relative error indicator $\eta_R$ defined by Zienkiewicz-Zhu / Abaqus `MISESERI`:
     $$\eta_R(\mathbf{x}) = \frac{\Vert \mathbf{e}_\sigma \Vert}{\Vert \bar{\boldsymbol{\sigma}} \Vert + \Vert \mathbf{e}_\sigma \Vert} = \frac{E \cdot \Vert \tilde{\mathbf{e}}_\sigma \Vert}{E \cdot \left(\Vert \tilde{\bar{\boldsymbol{\sigma}}} \Vert + \Vert \tilde{\mathbf{e}}_\sigma \Vert\right)} = \frac{\Vert \tilde{\mathbf{e}}_\sigma \Vert}{\Vert \tilde{\bar{\boldsymbol{\sigma}}} \Vert + \Vert \tilde{\mathbf{e}}_\sigma \Vert}$$
     The scalar factor $E$ cancels identically. Hence, whether $E$ is entered as $210.0\text{ kN/mm}^2$ or $210,000\text{ MPa}$, the normalized relative error distribution $\eta_R(\mathbf{x})$ and the resulting element size distribution $h(\mathbf{x}) = h_0 (\eta_{\text{target}}/\eta_R)^{1/p}$ are bitwise invariant.

### 2.3 Physical Displacement Chronology Resolution
* **Defect Identified:** Investigate whether $u_y = 1.46\text{ mm}$ genuinely precedes fracture initiation or corresponds to late propagation.
* **Resolution Applied in F1799:**
  1. **Provenance:** Tracing `scripts/remeshing/execute_f1688_sec43_recovery.py` line 159 reveals that $u_y = 1.46\text{ mm}$ was chosen to match Pandey & Kumar (2025) Fig. 16 State $u_{s4} = 1.46\text{ mm}$.
  2. **Chronology:** In Pandey & Kumar (2025), $u_{s4} = 1.46\text{ mm}$ is **late secondary crack propagation** near final structural failure (simulation terminates at $u = 1.50\text{ mm}$). In the coupled phase-field model (`PK_SEC43_COARSE_JOB1.inp`), crack initiation begins at $u_y \approx 0.10\text{ mm}$ (State 1 in `f1698_sec43_five_state_recovery_analysis.json`).
  3. **Linear Scale-Invariance:** Crucially, `PK_SEC43_COARSE_RECOVERY.inp` is a **pure linear-elastic static solve** (`*STATIC`, `NLGEOM=NO`) without phase-field damage coupling. In uncracked linear elasticity, stress scales strictly proportionally with applied displacement:
     $$\boldsymbol{\sigma}(\mathbf{x}; u_y = 1.46) = \frac{1.46}{0.10} \cdot \boldsymbol{\sigma}(\mathbf{x}; u_y = 0.10)$$
     Because scalar multipliers cancel identically in the dimensionless relative error $\eta_R$, a linear recovery solve conducted at $u_y = 0.10\text{ mm}$ produces the identical spatial error distribution and identical adapted mesh as one conducted at $u_y = 1.46\text{ mm}$.
  4. **Key Scientific Insight:** This scale-invariance explains why a single-pass initial-state linear recovery solve *cannot* anticipate downstream secondary cracking: in linear elasticity without damage, the stress concentration remains localized strictly at the sharp notch tip $(10, 70)$, while the secondary ligament between the central hole and the outer boundary is smooth and non-singular.

### 2.4 Execution Journal Preservation
* **Resolution Applied in F1799:** Preserved both `abaqus.rpy` (3,327 bytes) and `abaqus_cae_execution.log` (573 bytes) directly in `models/pandey_kumar_mode1/249_f1799_case3_controlled_remesh/`, providing independent execution evidence that `GATE_01` executed with Exit 0.

### 2.5 Audit Receipt Corner Angles
* **Resolution Applied in F1799:** The audit receipt `PK_F1799_CASE3_CONTROLLED_REMESH_RECEIPT.json` now explicitly includes `min_corner_angle_deg` ($27.05^\circ$) and `max_corner_angle_deg` ($138.19^\circ$), verifying healthy element shapes without corner collapse.

---

## 3. Physical Donor Qualification Audit

The donor ODB was qualified in `PK_F1799_CASE3_DONOR_QUALIFICATION_RECEIPT.json`:

```json
{
  "task_id": "F1799-CASE3-CAUSAL-CONFIG-AND-PHYSICAL-DONOR-CONTROLLED-REMESH",
  "donor_file": "PK_SEC43_COARSE_RECOVERY.odb",
  "donor_path": "models/pandey_kumar_mode1/188_pk_sec43_hole_plate/PK_SEC43_COARSE_RECOVERY.odb",
  "donor_sha256": "BDCC74908A7F85186E6CE4165851AB2061969BCEF84E370C41F5DEF63597E3F4",
  "donor_size_bytes": 1498400,
  "mesh_topology": {
    "num_nodes": 4040,
    "num_elements": 3923,
    "element_types": ["CPE3", "CPE4"]
  },
  "step_name": "RECOVERY_STEP",
  "step_procedure": "*STATIC",
  "frame_index": 1,
  "frame_time": 1.0,
  "total_frames_in_step": 2,
  "is_causal_preanalysis": true,
  "causal_verification": {
    "causal_mode": true,
    "max_frame_index": 1,
    "max_frame_time": 1.0,
    "donor_frames_count": 2,
    "temporal_horizon_enforced": true
  },
  "indicator_field": "MISESERI",
  "normalization_field": "MISESAVG",
  "num_elements_with_indicator": 3923,
  "miseseri_stats": {
    "min_mpa": 0.00053513,
    "max_mpa": 5.19831657,
    "mean_mpa": 0.05985284,
    "median_mpa": 0.03034505,
    "p90_mpa": 0.12277275,
    "p99_mpa": 0.48030719,
    "nonzero_count": 3923
  },
  "misesavg_stats": {
    "min_mpa": 0.00101920,
    "max_mpa": 12.56767082,
    "mean_mpa": 1.62892294
  },
  "qualification_status": "QUALIFIED_AUTHENTIC_INITIAL_STATE_NATIVE_DONOR"
}
```

---

## 4. Controlled Mesh Quality & Spatial Resolution Audit

### 4.1 Physical Mesh Invariants & Topology
* **Filename:** `PK_F1799_CASE_3_ADAPT_PHYS.inp`
* **File Size:** 1,934,333 bytes
* **File SHA-256:** `C3B84ECAFEB93498EF7880006629FBDDEEA2B1D2744D8E393D57349CECC4B5C0`
* **Mesh Body SHA-256:** `13B6770FC30025CBB1D2CC5ACC1D50F98CE6D5F58F5300BB70158A39E232F7B6`
* **Total Nodes:** 26,961
* **Total Physical Elements:** 26,891
* **Quad Elements (CPE4):** 26,145 (**97.23%**)
* **Triangular Elements (CPE3):** 746 (**2.77%**)
* **Minimum Signed Jacobian:** $+7.9700 \times 10^{-4}$ (**Zero non-positive Jacobians**)
* **Aspect Ratio:** Median = 1.232, Maximum = 2.706 (**0 violations $> 4.0$**)
* **Corner Angles:** Minimum = $27.05^\circ$, Maximum = $138.19^\circ$

### 4.2 Spatial Resolution Across Critical and Far-Field Zones
Given material length scale $\ell_0 = 0.285\text{ mm}$ and target $\ell_0/2 = 0.1425\text{ mm}$:

| Zone | Geometry Bounds | Element Count | Mean $h$ (mm) | Min $h$ (mm) | Max $h$ (mm) | $\% \le \ell_0$ | $\% \le \ell_0/2$ |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Primary Corridor** | Notch tip to central hole ($x \in [10, 36.5], y \in [45, 75]$) | 5,888 | 2.320 | 0.0430 | 6.735 | 3.33% | 1.27% |
| **Secondary Corridor** | Central hole to boundary ($x \in [46.5, 65], y \in [40, 62]$) | 890 | 3.742 | 0.2014 | 7.344 | 0.67% | 0.00% |
| **Far-Field Background** | Plate ends ($y \le 15$ or $y \ge 105$) | 2,074 | 4.094 | 0.0549 | 10.533 | 0.82% | 0.19% |

* **Far-to-Core Coarsening Ratio:**
  $$\frac{\bar{h}_{\text{far-field}}}{\bar{h}_{\text{primary}}} = \frac{4.094\text{ mm}}{2.320\text{ mm}} = 1.76\times$$

---

## 5. Direct Comparative Evaluation Against Baselines

| Metric | Task F1799 (Current) | Task F1798 (Predecessor) | F1741 (Explosion) | F1780 (Multi-State) | Literature Target |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Total Elements** | **26,891** | 26,891 | 28,933 | 10,064 | 12,168 |
| **Quad Fraction** | **97.23%** | 97.23% | 98.65% | 96.94% | ~95% |
| **Min Signed det(J)**| **+7.97e-4** | +7.97e-4 | +1.12e-4 | +4.56e-4 | $> 0$ |
| **Max Aspect Ratio** | **2.706** | 2.706 | 3.120 | 2.854 | $\le 4.0$ |
| **Corner Angles** | **[27.05°, 138.19°]**| [27.05°, 138.19°]* | Not recorded | [25.1°, 141.2°] | N/A |
| **Primary $\% \le \ell_0$** | **3.33%** | 3.33% | 88.4% | 94.2% | $> 90\%$ |
| **Secondary $\% \le \ell_0$**| **0.67%** | 0.67% | 72.1% | 86.5% | $> 80\%$ |
| **Far-to-Core Coarsen**| **1.76x** | 1.76x | 1.84x | 2.45x | $\ge 2.0\times$ |
| **Delta vs F1798** | **0 (100.0% parity)** | Reference | -2,042 | +16,827 | +14,723 |
| **Delta vs Literature**| **+14,723 (+121.0%)** | +14,723 | +16,765 | -2,104 | Reference |

*\*Recorded in audit but omitted from receipt in F1798; now fully reconciled.*

---

## 6. Quality Gates Assessment

All seven quality gates were evaluated under the strict predeclared criteria:

```json
"quality_gates": {
  "GATE_01_NATIVE_EXECUTION_EXIT_0": "PASS",
  "GATE_02_QUAD_FRACTION_GE_90_PCT": "PASS",
  "GATE_03_ZERO_NEGATIVE_JACOBIANS": "PASS",
  "GATE_04_ASPECT_RATIO_LE_4": "PASS",
  "GATE_05_PRIMARY_CORRIDOR_RESOLUTION": "FAIL",
  "GATE_06_FAR_FIELD_COARSENING": "FAIL",
  "GATE_07_EFFICIENCY_VS_HISTORICAL_EXPLOSION": "FAIL"
}
```

### Authentic Scientific Interpretation of Failed Gates
* **GATE_05 (Primary Corridor Resolution = 3.33% vs 90.0%):** Under single-pass initial linear elasticity, the stress concentration is localized strictly within a microscopic radius ($\sim 0.1\text{ mm}$) at the notch tip. The remainder of the primary ligament carries modest nominal stress and negligible recovered gradient error, leaving 96.67% of the corridor unrefined.
* **GATE_06 (Far-Field Coarsening = 1.76x vs 2.0x):** Sizing transition from the notch tip to the plate boundaries achieves 1.76x coarsening, slightly below the 2.0x threshold due to free-meshing graded sizing transitions around the three holes.
* **GATE_07 (Efficiency vs Historical Explosion = 26,891 vs 20,000):** Element count exceeds 20,000 because Abaqus CAE generates fine transition elements around the three circular cutouts to satisfy geometric curvature seeding.

**Governing Discipline:** These failed gates represent authentic physical limitations of single-pass linear-elastic pre-analysis remeshing. They are retained as `FAIL` and not artificially modified or suppressed.

---

## 7. Conclusions & Next Action

Task F1799 successfully resolves all supervisory directives from Task F1798:
1. Validates the causal configuration schema with active runtime assertions.
2. Reconciles the material unit system with mathematical scale-invariance proof.
3. Resolves the displacement chronology between Pandey & Kumar reference states and linear elasticity.
4. Commits CAE execution journals demonstrating Exit 0 independently.
5. Reconciles corner angle distribution in the audit receipt.
6. Strictly preserves cumulative PBS count at 35 (0 new jobs consumed) and maintains `MASTER_GOAL_STATUS = OPEN`.

Ready for independent scientific review under correlation ID `HND-F1799-CASE3-CONTROLLED-REMESH-001`.
