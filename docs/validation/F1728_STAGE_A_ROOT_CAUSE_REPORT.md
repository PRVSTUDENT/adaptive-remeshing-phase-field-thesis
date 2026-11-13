# F1728 Stage A Root-Cause Investigation Report: Comprehensive Diagnosis of Method A Donor Fields, State Timing, and Framework Architecture Across Five Geometries

**Protocol:** INDEPENDENT_STRUCTURED_REVIEW_V1  
**Task ID:** `F1728-UNIFIED-METHOD-A-FIVE-GEOMETRIES`  
**Milestone:** `STAGE_A_ROOT_CAUSE_INVESTIGATION`  
**Date:** 13 November 2026  
**Agent:** Gemini Antigravity (PRV_ADAPTIVE_REMESHING)  
**Status:** `STAGE_A_COMPLETE`  
**Governing Mandate:** Mandatory Root-Cause Investigation before new HPC experiments. Formal recording of user visual rejection of F1727 historical baseline meshes.

---

## 1. Executive Summary & Problem Statement

Task F1727 attempted to extend Method A adaptive remeshing across three geometries (Models A, B, and C). However, the resulting meshes failed user visual review because:
1. The staged adapted physical meshes in F1727 were identical copies of historical project files rather than fresh meshes generated through a unified pipeline.
2. In Model A (Section 4.3), refinement localized solely at the notch root ($h \le 0.143\,\text{mm}$), leaving the secondary ligament between the central hole and the right free boundary completely unrefined ($h \approx 1.5\,\text{mm}$).
3. The reusable framework (`scripts/remeshing/reusable_2d_adaptive_framework.py`) supported configuration parsing, geometry containment, quality audits, and production-deck assembly, but lacked a native Abaqus `RemeshingRule` / `adaptiveRemesh()` execution backend, forcing past studies to rely on ad-hoc, case-specific scripts.

This Stage A investigation performs an exhaustive, evidence-backed audit across all three root-cause tracks mandated by the research directive:
- **Track A:** Donor field, stress formulation, and superconvergent patch recovery (SPR) implementation.
- **Track B:** Donor-state timing and the physical mechanisms governing single-corridor vs. multi-corridor refinement.
- **Track C:** Software architecture and engine unification across all five benchmark cases.

---

## 2. Track A: Donor Field & Stress-Recovery Implementation Audit

### 2.1 The Native Abaqus MISESERI Formulation
In Abaqus/Standard, the error indicator `MISESERI` represents the equivalent Mises stress discretization error derived from the Zienkiewicz–Zhu (1987) superconvergent patch recovery (SPR) technique:
$$e_{\sigma} = \sqrt{\frac{3}{2} (\mathbf{s}^* - \mathbf{s}) : (\mathbf{s}^* - \mathbf{s})}$$
where $\mathbf{s}^*$ is the continuous polynomial stress deviator fitted across nodal patches, and $\mathbf{s}$ is the raw integration-point Cauchy stress deviator.

The relative error normalized by the domain-averaged stress is:
$$\eta_e = \frac{e_{\sigma}}{\sigma_{\mathrm{avg}}}, \quad \text{where } \sigma_{\mathrm{avg}} = \sqrt{\frac{1}{V} \int_V \sigma_{\mathrm{Mises}}^2 \, \mathrm{d}V}$$

Under Abaqus `UNIFORM_ERROR` sizing:
$$h_{\mathrm{new}} = h_{\mathrm{old}} \left( \frac{e_{\mathrm{target}}}{\eta_e} \right)^{1/p}$$
where $p \approx 1$ for linear elements.

### 2.2 UEL-to-UMAT Stress Transfer and Overlay Scaling Invariance
A critical finding from Tasks F1718–F1720 is the overlay mechanical neutrality paradox:
- In the 3-layer Method A architecture, Layer 1 (Phase Field) and Layer 2 (Displacement) solve the coupled problem via the user element subroutine `f42_mixed_uel.for`.
- Layer 3 consists of companion standard continuum elements (`CPE4`/`CPE3`) with material `DUMMY_MAT` executing a companion user material (`UMAT`) to receive Cauchy stresses via a shared Fortran `COMMON` block (`CB_F1720_STRESS`).
- To prevent Layer 3 from artificially doubling the structural reaction force ($RF$), the companion dummy Young's modulus must be scaled by $s \approx 10^{-11} / E_0 \approx 4.7619 \times 10^{-14}$.
- **Mathematical Invariance Proof:** Because both raw stress error $e_{\sigma}$ and domain-average stress $\sigma_{\mathrm{avg}}$ scale linearly with $s$, the relative error $\eta_e = e_{\sigma} / \sigma_{\mathrm{avg}}$ is mathematically and numerically scale-invariant ($|\Delta \eta| \le 2.94 \times 10^{-5}\%$, audited in Task F1718).
- This explains why published Figure 25(a) displays an apparent numerical legend scale of $10^{-12} \sim 10^{-19}\,\mathrm{MPa}$: it reflects the unscaled dummy modulus overlay in Abaqus, while the resulting mesh sizing $h_{\mathrm{new}}$ is completely unaffected.

### 2.3 Verification Against Published Error Contours
Comparing actual computed Abaqus `MISESERI` fields against Pandey & Kumar (2025):
- **Case 1 (Section 4.1, Fig. 6a):** Crack-tip stress singularity generates sharp circular error contours centered on $(0.5, 0.5)\,\mathrm{mm}$, decaying smoothly into the bulk.
- **Case 4 (Section 4.5, Fig. 25a):** Error peaks concentrate in narrow ligaments between adjacent circular voids.
- **Case 5 (Section 4.6, Fig. 25b):** Upper row of holes carries intense error concentrations bridging $h_1 \to h_4 \to h_2 \to h_5 \to h_3$, while lower holes $h_6$ and $h_7$ are stress-shielded.
- **Case 3 (Section 4.3, Fig. 15b):** Crucially, the published figure displays narrow indicator bands on **BOTH** sides of the central hole:
  1. Primary band connecting the notch root $(10, 70)$ to the central hole $(36.5, 51)$.
  2. Secondary band connecting the right flank of the central hole $(46.5, 51)$ to the right specimen boundary $(65, 51)$.

---

## 3. Track B: Donor-State Timing & The Multi-Corridor Refinement Mechanism

### 3.1 Why Model A Failed in Tasks F1688 and F1727
In Tasks F1688 and F1727, the donor ODB used for Section 4.3 was `PK_SEC43_COARSE_RECOVERY.odb`, extracted from an elastic, uncracked pre-analysis step.

The physical mechanics of an elastic uncracked notched plate:
1. The sharp notch root ($a = 10\,\mathrm{mm}, w = 0.4\,\mathrm{mm}$) introduces an elastic stress concentration factor $K_t \gg 1$, producing a localized Mises stress peak of $5.1983\,\mathrm{MPa}$.
2. In contrast, the ligament between the smooth circular void ($R = 10\,\mathrm{mm}$) and the right free boundary experiences only a mild Kirsch-type stress perturbation with very low spatial stress gradients ($|\nabla \sigma| \approx 0$).
3. Because SPR error $e_{\sigma}$ is proportional to the second derivatives of displacement (stress gradients), $e_{\sigma}$ along the secondary ligament is negligible.
4. Consequently, Abaqus `UNIFORM_ERROR` sizing allocates fine elements ($h \approx 0.143\,\mathrm{mm}$) exclusively at the notch root, while assigning the maximum allowed element size ($h \approx 1.5\,\mathrm{mm}$) to the secondary ligament.

### 3.2 How Pandey & Kumar Obtained Figure 15(b)
Pandey & Kumar (2025) Section 4.3 did NOT use a purely linear-elastic uncracked donor state for Figure 15(b).

In phase-field brittle fracture:
- As the specimen is pulled, damage $d$ initiates at the notch root and propagates toward the central void.
- When the primary crack penetrates the central void, the load path is severed on the left side of the void.
- To maintain static equilibrium, the tensile load is transferred entirely across the remaining ligament between the central hole and the right free edge.
- This creates severe stress concentration and steep stress gradients on the right flank of the hole, producing a high `MISESERI` signal along the secondary corridor.

### 3.3 Historical Verification in Task F1703
In Task F1703, our project previously demonstrated this exact physical mechanism:
- When a donor state with damage progression was used (`PK_SEC43_F1703_SECONDARY_COMPLETE_ADAPT.inp`, $10{,}065$ elements), the resulting native adapted mesh resolved **BOTH** corridors:
  - Primary corridor: $h \le 0.143\,\mathrm{mm}$ ($100\%$ compliance with $\le \ell_0/2$).
  - Secondary corridor: $h \le 0.051\,\mathrm{mm}$ across the entire $18.56\,\mathrm{mm}$ ligament to the right edge.
- **Actionable Conclusion:** To capture both fracture corridors in Case 3 without artificial crack-path priors, the coarse donor simulation must be executed past initial damage localization until stress redistribution transfers across the central void into the secondary ligament.

---

## 4. Track C: Software Architecture & Engine Unification

### 4.1 Identified Architectural Defect
Prior to Task F1728, the software architecture was fragmented across multiple disconnected scripts:
- `execute_method_a_sec43_remesh.py` (Case 3 hard-coded CAD and sizing)
- `execute_f1719_native_remesh.py` (Case 4 hard-coded five-hole CAD)
- `run_seven_hole_adaptive_study.py` (Case 5 hard-coded seven-hole CAD)
- `execute_method_a_native_remesh.py` (Case 2 hard-coded single-hole CAD)
- `assemble_f1727_three_geometries.py` (Copied historical INPs rather than remeshing)
- `reusable_2d_adaptive_framework.py` (Contained geometry adapters and audit engines, but NO native remeshing execution method!)

### 4.2 Unified Engine Architecture (Stage B Roadmap)
To eliminate this defect permanently, `scripts/remeshing/reusable_2d_adaptive_framework.py` must be upgraded to provide one unified, configuration-driven native remeshing engine:

```python
def run_method_a_case(case_config, authentic_donor_odb, output_directory, abaqus_model_name=None):
    """
    Unified native Abaqus Method A execution engine:
    1. Validates configuration and geometry parameters.
    2. Builds native CAD part and instances via geometry adapter.
    3. Seeds coarse background mesh and sets up step definitions.
    4. Opens authentic donor ODB and verifies field availability (MISESERI).
    5. Creates native Abaqus RemeshingRule with UNIFORM_ERROR.
    6. Executes model.adaptiveRemesh(odb=donor_odb).
    7. Exports adapted physical mesh (.inp).
    8. Performs independent finite-element quality and resolution audits.
    9. Assembles 3-layer UEL/UMAT production deck.
    10. Generates publication-quality figures and JSON receipts.
    """
```

---

## 5. Summary of Case-Specific Baseline Audit

| Case ID | Benchmark Geometry | Length Scale $\ell_0$ | Coarse $h$ | Published Adapted Mesh | Dominant Failure Mode in Past Runs | Resolution Strategy for F1728 |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| **Case 1** | Mode-I Edge Crack ($1 \times 1\,\text{mm}$) | $0.0075\,\text{mm}$ | $0.020\,\text{mm}$ | $13{,}941$ elements | Relied on copied historical mesh (`PK_F1713`) | Execute unified engine on authentic Mode-I ODB |
| **Case 2** | Thesis Single Hole ($1 \times 1\,\text{mm}$) | $0.0075\,\text{mm}$ | $0.020\,\text{mm}$ | Internal reference | Relied on copied historical mesh (`PK_HOLE_SEL_E08`) | Execute unified engine on `PK_HOLE_METHOD_A_PREANALYSIS.odb` |
| **Case 3** | Notched Plate with Pins ($65 \times 120\,\text{mm}$) | $0.285\,\text{mm}$ | $1.50\,\text{mm}$ | $\sim 13{,}785$ elements | Secondary corridor unrefined due to uncracked elastic donor | Use damage-localized donor state to activate secondary ligament |
| **Case 4** | Five-Hole Plate ($1 \times 1\,\text{mm}$) | $0.008\,\text{mm}$ | $0.020\,\text{mm}$ | $12{,}944$ elements | Hard-coded standalone script (`execute_f1719`) | Ingest into unified engine with Table 5 hole definitions |
| **Case 5** | Seven-Hole Plate ($1 \times 1\,\text{mm}$) | $0.008\,\text{mm}$ | $0.020\,\text{mm}$ | $15{,}714$ elements | Hard-coded standalone script (`run_seven_hole`) | Ingest into unified engine with Table 6 hole definitions |

---

## 6. Actionable Next Steps (Transition to Stage B)

1. **Implement Unified Remeshing Engine:** Extend `scripts/remeshing/reusable_2d_adaptive_framework.py` with `AbaqusNativeRemeshingEngine` and `run_method_a_case`.
2. **Create Five Case Configurations:** Ensure all five cases have standardized, validated JSON definitions in `configs/remeshing/`.
3. **Build Five-Case Offline Regression Suite:** Create `tests/unit/test_f1728_five_geometry_framework.py` checking geometry, boundary conditions, remeshing rule construction, and mesh audit compliance.
4. **Prepare HPC Execution Pilot:** Stage Case 1 on the HPC cluster for initial qualification under a finite PBS budget.

Stage A Root-Cause Investigation is formally complete and registered.
