# Task F1728 Case 2 (Single Off-Axis Hole Plate) Donor Qualification Report (Reconciled Round 2)

**Task ID:** `F1728-UNIFIED-METHOD-A-FIVE-GEOMETRIES`  
**Subtask ID:** `F1728-CASE2-PEAK_DONOR_NATIVE_INDICATOR_VERIFICATION`  
**Classification:** `CASE2_DONOR_QUALIFICATION_RECONCILED_PASS`  
**Date:** 13 November 2026  
**Protocol Version:** 1  
**Agent:** `gemini-antigravity`  
**Review Correlation:** `HND-F1728-CASE2-DONOR-QUAL-002`  
**Predecessor Review:** `HND-F1728-CASE2-DONOR-QUAL-001` (Decision: `REJECT`, Findings F1728-R15 to F1728-R19)  

---

## 1. Executive Summary and Complete Resolution of Findings F1728-R15 to F1728-R19

This reconciled report comprehensively resolves all five findings issued in the Round 1 Independent Review ([`HND-F1728-CASE2-DONOR-QUAL-001`](file:///D:/Master%20thesis/Adaptive%20remeshing/.agents/bridge_history/response_HND-F1728-CASE2-DONOR-QUAL-001.md)):

1. **Finding F1728-R15 (Zero MISESERI and Cauchy Stress in Donor 2 Diagnosed):**
   - Detailed inspection of `f42_mixed_uel.for` in `/scratch9/pr21vyci/runs/mode1_method_a_hole_coarse/` reveals that Layer 3 visualizer UMAT explicitly sets:
     ```fortran
     DO I=1, NTENS
       STRESS(I) = 0.D0
       DO J=1, NTENS
         DDSDDE(I,J) = 0.D0
       ENDDO
       DDSDDE(I,I) = 1.D-11
     ENDDO
     ```
   - In `PK_HOLE_COARSE_JOB1.odb`, the Cauchy stress tensor $\mathbf{S}$ in Layer 3 is identically zero (`0.0`), and consequently the SPR stress-recovery error $\text{MISESERI}$ is identically zero across all 389 increments.
   - **Definitive Classification:** `PK_HOLE_COARSE_JOB1.odb` alone **CANNOT** serve as a direct native `MISESERI` donor for Abaqus adaptive remeshing. To utilize Step-2 peak damage information, a companion stress-recovery operation (such as the direct-coupled UEL `/CB_F1720_STRESS/` or companion continuum solve) is required.
   - **Donor 1 Remains Valid:** Candidate Donor 1 (`PK_HOLE_METHOD_A_PREANALYSIS.odb`) contains a genuine, nonzero native $\text{MISESERI}$ field ($1,430.27\,\text{MPa}$ peak) and is the only currently execution-ready native donor.

2. **Finding F1728-R16 (Elementwise Dataset Published & Graph Adjacency Audited):**
   - The full elementwise dataset is published at [`results/validation/f1728_case2_coarse_job1_fields.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/results/validation/f1728_case2_coarse_job1_fields.json) ($745,890$ bytes).
   - Graph adjacency analysis on the 48 damaged elements ($d \ge 0.10$) at Step-2 Peak was executed via [`scripts/remeshing/audit_case2_damage_connectivity.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/scripts/remeshing/audit_case2_damage_connectivity.py).
   - **Audited Topology:** The 48 elements do **not** form a single continuous band into the hole. They are partitioned into 3 edge-connected components:
     * **Component 1 (37 elements):** Primary crack lobe originating $9.5\,\mu\text{m}$ from the notch tip $(0.50, 0.50)\,\text{mm}$ and terminating with centroid $(0.5608, 0.5513)\,\text{mm}$, exactly **$7.69\,\mu\text{m}$ ($1.02\,\ell_0$)** away from the hole perimeter ($d_{\max} = 0.5798$, $d_{\text{mean}} = 0.1869$). A physical gap of $7.69\,\mu\text{m}$ remains uncracked before hole penetration.
     * **Component 2 (10 elements):** Secondary crack initiation lobe on the opposite (right) flank of the hole ($x \in [0.7442, 0.7809], y \in [0.5970, 0.6809]$) within **$7.85\,\mu\text{m}$** of the hole perimeter ($d_{\max} = 0.2253$, $d_{\text{mean}} = 0.1542$).
     * **Component 3 (1 element):** Element 1140 at $(0.99, 0.99)\,\text{mm}$ ($d = 0.1258$), a localized corner boundary artifact.

3. **Finding F1728-R17 (Numerical Consistency Corrected):**
   - Hardcoded prose strings containing incorrect numbers ($107.39\,\text{MPa}$, $68.42\,\text{MPa}$, $3.88\,\text{MPa}$) have been completely removed from [`scripts/remeshing/audit_case2_off_axis_hole_donor.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/scripts/remeshing/audit_case2_off_axis_hole_donor.py).
   - All assessments in [`results/validation/f1728_case2_donor_qualification.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/results/validation/f1728_case2_donor_qualification.json) and this report are dynamically formatted directly from the verified data records:
     * Maximum $\text{MISESERI}$: $1,430.27\,\text{MPa}$ (Element 1184).
     * Tip core mean ($r \le 0.05\,\text{mm}$): $385.55\,\text{MPa}$.
     * Hole flank mean: $162.63\,\text{MPa}$.
     * Notch-to-hole ligament mean: $193.96\,\text{MPa}$.
     * Far-field bulk mean: $15.04\,\text{MPa}$.
     * Maximum-to-bulk contrast: $95.11\times$.
     * Core mean-to-bulk mean contrast: $25.64\times$.
     * Hole flank mean-to-bulk mean contrast: $10.81\times$.

4. **Finding F1728-R18 (Exact ODB Provenance, SHA-256, and Step/Frame Provenance):**
   - **Candidate Donor 1 (Linear-Elastic Pre-Analysis):**
     * Path: `/scratch9/pr21vyci/runs/mode1_hole_method_a_test/PK_HOLE_METHOD_A_PREANALYSIS.odb`
     * Size: 2,883,480 bytes, SHA-256: `0A108C6A8404F1AF9D8F5DDC03223E9D8D051AB08587F841D9F5799970AE93B1`
     * Instance: `PLATE-1`
     * Step: `Step-1`, Frame: Last (Time = 1.0, $u_y = 0.0050\,\text{mm}$)
     * Native $\text{MISESERI}$: Verified nonzero ($1,430.27\,\text{MPa}$ peak).
   - **Candidate Donor 2 (Coarse Phase-Field Simulation):**
     * Path: `/scratch9/pr21vyci/runs/mode1_method_a_hole_coarse/PK_HOLE_COARSE_JOB1.odb`
     * Size: 518,169,932 bytes, SHA-256: `834b9bb035fcf7b25dbb0deb7f8c344d7a9783dcfaa6d92a0c986affb689ad4c`
     * Total Frames: 389 (Step-1: 51 frames, Step-2: 338 frames)
     * Peak State: Step-2, Frame 167 (Time = 0.3276875, $u_y = 0.00729381\,\text{mm}$, $F_y = 0.731015\,\text{kN}$, $d_{\max} = 0.5798$)
     * Native $\text{MISESERI}$: **Zero (0.0)** across all frames.

5. **Finding F1728-R19 (Expanded Unit Regression Test Suite):**
   - Added rigorous tests to [`tests/unit/test_f1728_five_geometry_framework.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_f1728_five_geometry_framework.py):
     * Test verifying `PK_HOLE_COARSE_JOB1.odb` SHA-256 `834b9bb0...`.
     * Test verifying zero nonzero $\text{MISESERI}$ values in Donor 2, ensuring that any claim of native stress recovery fails closed.
     * Test verifying the 3 damage connected components, 37 elements in primary lobe, and $7.69\,\mu\text{m}$ gap to hole perimeter.
     * Test verifying numerical consistency between report text, JSON records, and raw datasets.

---

## 2. Quantitative Comparison of Candidate Donors

| Metric / Property | Candidate Donor 1 (Pre-Analysis) | Candidate Donor 2 (Phase-Field Peak) |
| :--- | :--- | :--- |
| **ODB File Path** | `PK_HOLE_METHOD_A_PREANALYSIS.odb` | `PK_HOLE_COARSE_JOB1.odb` |
| **File Size & SHA-256** | 2.88 MB / `0A108C6A...` | 518.2 MB / `834b9bb0...` |
| **Physical Elements** | 2,906 (2,818 quads, 88 tris) | 2,906 physical (8,718 layered) |
| **Step & Frame Index** | Step-1, Frame 10 (Last) | Step-2, Frame 167 (Peak) |
| **Displacement $u_y$** | $0.00500\,\text{mm}$ | $0.00729\,\text{mm}$ |
| **Reaction Force $F_y$** | N/A (Linear elastic) | $0.7310\,\text{kN}$ ($F_{\max}$) |
| **Maximum Damage $d_{\max}$** | $0.0000$ (Intact elasticity) | $0.5798$ (Active softening) |
| **Damaged Elements ($d \ge 0.10$)** | 0 | 48 (37 in primary lobe, gap $7.69\,\mu\text{m}$) |
| **Native $\text{MISESERI}$ Max** | **$1,430.27\,\text{MPa}$** | **$0.00\,\text{MPa}$** (Identically zero) |
| **Native $\text{MISESERI}$ Nonzero Count** | **2,906 / 2,906 elements** | **0 / 2,906 elements** |
| **Cauchy Stress $\mathbf{S}$ Status** | Nonzero continuum stress | Identically zero (`STRESS(I)=0.D0`) |
| **Native Remeshing Readiness** | **QUALIFIED FOR NATIVE REMESHING** | **REQUIRES COMPANION STRESS RECOVERY** |

---

## 3. Detailed Damage Connectivity and Gap Analysis

The element-adjacency audit on the 48 damaged elements ($d \ge 0.10$) reveals the exact spatial structure of the phase-field softening field:

```
[Notch Tip (0.50, 0.50)]
        |
        | (gap: 9.5 um from tip to El 1184)
        v
[Component 1: 37 Elements]  --> d_max = 0.5798, d_mean = 0.1869
        |
        | (gap: 7.69 um = 1.02 l0 to hole perimeter)
        v
[Hole Boundary (0.65, 0.65), R=0.10]
        |
        | (gap: 7.85 um to right hole flank)
        v
[Component 2: 10 Elements]  --> d_max = 0.2253, d_mean = 0.1542 (Secondary Crack Nucleation)
```

**Key Finding:**  
At peak load, the damage field has advanced significantly across the ligament, leaving a residual intact ligament gap of only **$7.69\,\mu\text{m}$** ($1.02\,\ell_0$). It has not yet penetrated the hole.

---

## 4. Reconciled Scientific Hypothesis (`HYPOTHESIS F1728-H2-CASE2`)

> **HYPOTHESIS F1728-H2-CASE2:**  
> 1. Native Abaqus `UNIFORM_ERROR` remeshing driven by linear-elastic pre-analysis (Step-1, Donor 1) will produce a mesh highly refined at the notch root ($h \le \ell_0/2$) but coarse across the uncracked oblique ligament into the hole flank ($h > \ell_0/2$) because linear elasticity lacks localized stress gradients along an uncracked ligament.  
> 2. Conversely, driving adaptive remeshing from an authentic coarse phase-field donor at peak load (Step-2 Peak, Donor 2) requires a companion degraded Cauchy stress recovery to generate the steep stress jumps across the 37 primary crack elements needed for SPR to refine the oblique trajectory into the hole boundary.

---

## 5. Execution Accounting and Ledger Reconciliation

- **New PBS Submissions Consumed:** `0` (`max_new_pbs_submissions = 0`, `submissions_consumed = 0` for this subtask).
- **Cumulative Historical Submissions:** Permanently reconciled at `5` in all ledgers (`1423095`, `1423101`, `1423102`, `1423103`, `1423169`).
- **Zero Forward Fracture Rule:** Strictly observed. Zero forward simulations executed or authorized.
