# Mode-II History Transfer Literature Provenance & Nonmatching Benchmark Design Audit Record

**Task ID**: `F208AUDIT-M2-HISTORY-TRANSFER-LITERATURE-PROVENANCE-AND-NONMATCHING-BENCHMARK-DESIGN1`  
**Date**: 17 August 2026  
**Status**: `AUDIT COMPLETED / LITERATURE PROVENANCE RECONCILED / PURE BENCHMARK GENERATED / IMPLEMENTATION MATRIX CONSTRUCTED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Executive Summary

A strict offline audit of the literature provenance and benchmark design from Task F207 was performed.

### Key Audit Findings
1. **Literature Provenance**: No cited paper in the project bibliography (Molnár & Gravouil 2017, Msekh et al. 2015, Pandey & Kumar 2025, Diddige et al. 2025) directly prescribes the exact compound operator `CLEMENT_NODAL_RECOVERY_WITH_STRAIN_GUARD` for phase-field history variable $\mathcal{H}$. The operator is classified as **`DERIVED_FROM_MULTIPLE_SUPPORTED_STEPS`** / **`REASONABLE_BUT_NOT_DIRECTLY_SUPPORTED`**.
2. **Bibliographic Corrections**:
   - `Pandey & Kumar`: Published in **2025** (CMES, article TSP_CMES_67858), not 2020. Addresses pre-analysis elastic remeshing via `MISESERI`, not state variable transfer during active fracture.
   - `Diddige, Roth, Kiefer`: Published in **2025** (CMAME), not 2022. Architectural multi-field UEL reference.
3. **UEL Runtime vs Pre-Transfer Strain Guard**:
   - The UEL (`f42_mixed_uel.for`, `f44_mixed_uel_restart_stateinit.for`) naturally executes `H = MAX(SV_H_COMMITTED, PSIP)` on every increment at runtime.
   - Therefore, `pretransfer_strain_guard_required = false`, `UEL_runtime_guard_already_equivalent = true`, and `double_application_risk = false`.
4. **Benchmark Topology Reconciliation**:
   - Proposing `PK10R1 -> PK10R2` as the initial nonmatching benchmark was **`INVALID_AS_FIRST_PURE_NONMATCHING_TRANSFER_BENCHMARK`** because PK10R1 (unslit continuous ligament) and PK10R2 (open physical slit with 26 split stations) have different crack topologies.
5. **Pure Nonmatching Target Deck Generated**:
   - Generated `M2_PURE_NONMATCHING_TARGET_NMA_80x80.inp` (SHA256: `9716e7ce...`) with identical physical domain ($1.0 \times 1.0\text{ mm}$), identical unslit topology, and 6,400 uniform quads ($h = 0.0125\text{ mm}$).

---

## 2. Source-by-Source Literature Provenance Audit

| Source Identity | Year | Relevant Section / Scope | Adaptive Remeshing? | History Field Transfer? | Gauss-to-Node Recovery? | Directly Prescribes Clement/SPR for $\mathcal{H}$? | Direct Support Level |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Molnár & Gravouil** | 2017 | Staggered UEL formulation on Abaqus (FEAD vol. 130) | `false` | `false` | `false` | `false` | `NONE` (Base UEL reference) |
| **Msekh et al.** | 2015 | Abaqus UEL phase-field implementation (CMS vol. 96) | `false` | `false` | `false` | `false` | `NONE` (UEL architecture) |
| **Pandey & Kumar** | 2025 | Pre-analysis adaptive remeshing via `MISESERI` (CMES) | `true` (pre-analysis) | `false` (elastic only) | `true` (built-in SPR for stress) | `false` | `ANALOGOUS` (Mesh generator only) |
| **Diddige, Roth, Kiefer** | 2025 | Multi-field UEL framework (CMAME) | `false` | `false` | `false` | `false` | `NONE` (Architectural reference) |
| **Miehe, Welschinger, Hofacker** | 2010 | Variational phase-field formulation (IJNME vol. 83) | `false` | `false` | `false` | `false` | `THEORETICAL_CONSTITUTIVE` ($\mathcal{H} \ge \psi_+$) |

---

## 3. Nonmatching Benchmark Taxonomy

- **Class NM-A (Pure Nonmatching Remesh)**:
  - Same $1 \times 1\text{ mm}$ geometry, same unslit ligament topology, different discretization (PK10R1 graded $\to$ 80x80 uniform $h=0.0125\text{ mm}$).
  - Purpose: Purely isolates spatial interpolation and history transfer error.
- **Class NM-B (Nonmatching Remesh with Refinement/Coarsening)**:
  - Same geometry and crack topology, locally adapted mesh density.
- **Class NM-C (Topology Change & Discretization Transfer)**:
  - PK10R1 unslit $\to$ PK10R2 open slit. Evaluates combined effect of topology correction and spatial transfer.
- **Class NM-D (Production Online Adaptive Remeshing)**:
  - Multi-increment automated remeshing sequence during crack propagation.

---

## 4. Pure Nonmatching Target Benchmark Candidate (`NM-A`)

- **Deck Name**: `M2_PURE_NONMATCHING_TARGET_NMA_80x80.inp`
- **Location**: `models/generated/mode_ii/benchmark_mesh_candidates/M2_PURE_NONMATCHING_TARGET_NMA_80x80.inp`
- **SHA256**: `9716e7ce570cc644ac463d5a3d17e75fb23cf30ce47674e882ddf22f812fa8db`
- **Mesh Specifications**:
  - Domain: $[-0.5, 0.5] \times [-0.5, 0.5]\text{ mm}$
  - Crack Topology: Unslit continuous ligament along $y=0$ (Identical to PK10R1)
  - Physical Nodes: 6,561 ($81 \times 81$) + 1 RP Node (99999 at $(0.0, 0.5)$) = 6,562 total
  - Physical Quads: 6,400 ($80 \times 80$ uniform, $h = 0.0125\text{ mm}$)
  - Layered Elements: 12,800 (6,400 Phase U1 + 6,400 Mech U2)
  - Boundary Sets: `BOT_NODES`, `TOP_NODES`, `LEFT_NODES`, `RIGHT_NODES`, `RP_NODE`
  - Kinematic Equations: Top surface tied to RP node in $U_1$ via `*EQUATION`
  - Discretization: Genuinely nonmatching with PK10R1 ($h_{\text{local}} = 0.010, h_{\text{global}} = 0.050$).

---

## 5. Implementation Decision Matrix

| Operator Component | Scientific Requirement | Source Support | Mathematical Support | Implementation Choice | Resolved | Blocking Issue |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Source $\mathcal{H}$ Reconstruction** | Quadrature storage $\mathcal{H}(\mathbf{x}_g) \ge 0$ | UEL `f42`/`f44` | Exact Gauss coordinates | Inverse quad shape matrix $M_{GP\to Node}$ | `true` | None |
| **GP-to-Node Recovery** | $C^0$ nodal field | Zienkiewicz/Clement | Local element smoothing | Inverse Gauss extrapolation | `true` | None |
| **Patch Averaging** | Consistent nodal smoothing | Literature (Clement 1975) | Area-weighted vs arithmetic | Area-weighted patch average | `true` | Formulation fixed |
| **Target Interpolation** | Non-negative interpolation | Standard FE | Barycentric / bilinear | Bilinear quad shape functions | `true` | None |
| **Target GP Evaluation** | Quadrature point values | Standard FE | Standard 2x2 Gauss rule | Evaluate shape functions at $(\xi_g, \eta_g)$ | `true` | None |
| **Irreversibility Handling** | $\mathcal{H} \ge 0$ and $\dot{\mathcal{H}} \ge 0$ | Miehe (2010) | Variational lower bound | $\max(0, \mathcal{H}_{\text{proj}})$ | `true` | None |
| **$\psi_+$ Guard** | Constitutive bound | UEL runtime | Idempotent with UEL update | Let UEL evaluate `MAX(H_COMMITTED, PSIP)` at runtime | `true` | Pre-transfer guard unnecessary |
| **Boundary Handling** | No artificial extrapolation | Standard FE | Bounded domain | Nearest valid boundary point projection | `true` | None |
| **Crack-Face Handling** | No cross-slit bleeding | Topology isolation | Duplicate nodes | Separate top/bottom patch partitions | `true` | Required for split meshes |
| **Triangles** | Mixed element recovery | Standard FE | 3-point Gauss rule | Linear triangle shape functions | `true` | 3-point rule formulation |
| **Fallback Behavior** | Robust mapping | Standard CAD/FE | Spatial tolerance | Nearest valid Gauss point within tolerance | `true` | Defined |
