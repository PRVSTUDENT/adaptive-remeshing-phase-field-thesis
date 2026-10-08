# Mode-II Native Adaptive Remeshing Frame Selection and Target Hierarchy Decision

**Date**: `2026-10-08`  
**Status**: `APPROVED / ACTIVE`  
**Governing Gate**: `Gate M2-3 (Native Adaptive Remeshing Reproduction & Forensic Audit)` / `Gate M2-4 (Mode-II Adapted Fracture Simulation)`  
**Author**: Gemini Antigravity  
**Literature Reference**: Pandey, V., & Kumar, S. (2025). *Computer Modeling in Engineering & Sciences*, 144(3), 3255–3283. DOI: [10.32604/cmes.2025.067858](https://doi.org/10.32604/cmes.2025.067858).

---

## 1. Context & Background

In Gate M2-2 and Gate M2-3, the Mode-II coarse pre-analysis (`Job-1_UEL_paper_horizon.odb`, $2{,}960$ physical elements, $3{,}042$ nodes) was executed over the full 2-step loading schedule ($u_x = 0 \to 10\,\mu\text{m}$ in Step-1; $u_x = 10 \to 20\,\mu\text{m}$ in Step-2).

A forensic audit (Tasks F1335–F1340) investigated whether the native adaptive remeshing rule should target the Step-1 final frame ($u_x = 10.0\,\mu\text{m}$) or the Step-2 final frame ($u_x = 20.0\,\mu\text{m}$).

Key forensic findings:
1. **Mathematical Scale-Invariance**: Because the pre-analysis is strictly linear elastic ($d \equiv 0$), both stresses $\mathbf{\sigma}$ and the stress-recovery indicator $\text{MISESERI}$ scale linearly with prescribed displacement $u_x$:
   $$\text{MISESERI}(\mathbf{x}, 20\,\mu\text{m}) = 2 \times \text{MISESERI}(\mathbf{x}, 10\,\mu\text{m})$$
   $$\text{MISESAVG}(20\,\mu\text{m}) = 2 \times \text{MISESAVG}(10\,\mu\text{m})$$
   Consequently, the relative error indicator is **100% bit-for-bit scale-invariant**:
   $$\eta_e = \frac{\text{MISESERI}_e}{\text{MISESAVG}} \equiv \text{constant across all increments}$$
2. **Topological Equivalence**: Native Abaqus CAE `adaptiveRemesh` produces $22{,}530$ elements ($22{,}642$ nodes) from Step-1 and $22{,}405$ elements ($22{,}512$ nodes) from Step-2 at $\text{errorTarget} = 2.0\%$. The difference is only $-125$ elements ($-0.55\%$), confirming topological equivalence and refuting any frame-selection defect hypothesis.
3. **Figure Provenance Alignment**: The publication figure `fig_mode2_et2_mesh_topology_fulldomain.png` was audited and proven to depict the Step-1 mesh ($22{,}530$ FEs), which is also the active mesh solving in production retest Job `1411103.mmaster02`.

---

## 2. Formal Working Project Decision

### Decision 2.1: Primary Working Candidate Frame
- **Primary Candidate Frame**: **Step-2 Final Frame ($u_x = 20.0\,\mu\text{m}$, Frame 2000)** of `Job-1_UEL_paper_horizon.odb`.
- **Scientific Rationale**:
  - Represents the complete physical horizon of the pre-analysis before fracture onset.
  - Aligns with the full 2-step loading schedule specified by Pandey & Kumar (2025).
  - Possesses fully documented element geometry and node coordinates (`m2_3_mesh_elements_step2_et2pct.csv`, `m2_3_mesh_nodes_step2_et2pct.csv`).

### Decision 2.2: Reference / Baseline Audit Frame
- **Comparison Reference Mesh**: **Step-1 Final Frame ($u_x = 10.0\,\mu\text{m}$)** mesh (`M2_3_ADAPTED_RAW_2PCT.inp`, $22{,}530$ FEs, $22{,}642$ nodes).
- **Role**: Serves as the authoritative benchmark mesh for live fracture retest Job `1411103.mmaster02` and provides the historical baseline for cross-frame invariance audits.

### Decision 2.3: Baseline Error Target Hierarchy
- **Standard Baseline Error Target**: $\text{errorTarget} = 2.0\%$ ($\eta_{\text{target}} = 0.02$, $h_{\min} = 0.001\,\text{mm}$, $h_{\max} = 0.020\,\text{mm}$, refinement factor 10, coarsening NOT_ALLOWED).
- **Diagnostic High-Resolution Target**: $\text{errorTarget} = 1.0\%$ ($\eta_{\text{target}} = 0.01$).
  - Purpose: Investigate whether tighter error tolerance extends the high-resolution refinement corridor further along the prospective oblique shear trajectory ($(0.5, 0.5) \to (0.81, 0.0)\,\text{mm}$).
  - Artifacts: `M2_3_ADAPTED_STEP2_RAW_1PCT.inp`, `m2_3_mesh_elements_step2_et1pct.csv`, `m2_3_mesh_nodes_step2_et1pct.csv`, `MODE2_M2_3_STEP2_1PCT_ADAPTED_MESH_MANIFEST.json`.

---

## 3. Implementation and Governance Matrix

| Mesh Designation | Source Frame | Prescribed $u_x$ | Error Target | Finite Elements | Nodes | Governed Role |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `M2_3_ADAPTED_RAW_2PCT` | `Step-1` (Frame 2000) | $10.0\,\mu\text{m}$ | $2.0\%$ | $22{,}530$ | $22{,}642$ | Active Fracture Retest Baseline (Job `1411103.mmaster02`) |
| `M2_3_ADAPTED_STEP2_RAW_2PCT` | `Step-2` (Frame 2000) | $20.0\,\mu\text{m}$ | $2.0\%$ | $22{,}405$ | $22{,}512$ | Primary Mode-II Native Adapted Model Candidate |
| `M2_3_ADAPTED_STEP2_RAW_1PCT` | `Step-2` (Frame 2000) | $20.0\,\mu\text{m}$ | $1.0\%$ | *TBD (Generating)* | *TBD* | High-Resolution Corridor Reach Diagnostic |

---

## 4. Invariance & Preservation Constraints
1. **Mode-I Baseline Freeze**: Tag `v2026.10.08-supervisor-meeting-mode1-freeze` and Fortran UEL hash `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` remain strictly untouched.
2. **Active Cluster Retest**: PBS Job `1411103.mmaster02` ($22{,}530$ FEs) remains undisturbed in `normal_imfdfkmq`.
3. **Execution Guardrails**: Guarded SSH wrapper `Invoke-GuardedSsh.ps1` used for all remote operations; 100% scratch directory compliance on HPC.
