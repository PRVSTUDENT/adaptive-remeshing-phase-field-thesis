# Task F1728 Case 2 (Single Off-Axis Hole Plate) Donor Qualification Report (Reconciled Round 3)

**Task ID:** `F1728-UNIFIED-METHOD-A-FIVE-GEOMETRIES`  
**Subtask ID:** `F1728-CASE2-BOUNDARY_CONTACT_AND_INDICATOR_STATISTICS_CORRECTION`  
**Classification:** `CASE2_DONOR_QUALIFICATION_RECONCILED_PASS`  
**Date:** 13 November 2026  
**Protocol Version:** 1  
**Agent:** `gemini-antigravity`  
**Review Correlation:** `HND-F1728-CASE2-DONOR-QUAL-003`  
**Predecessor Reviews:** `HND-F1728-CASE2-DONOR-QUAL-001` (REJECT), `HND-F1728-CASE2-DONOR-QUAL-002` (REJECT, Findings F1728-R20 and F1728-R21)  

---

## 1. Executive Summary and Resolution of Review Findings F1728-R20 & F1728-R21

This reconciled report incorporates the decisive corrections mandated by the Independent Scientific Reviewer in [`HND-F1728-CASE2-DONOR-QUAL-002`](file:///D:/Master%20thesis/Adaptive%20remeshing/.agents/bridge_history/response_HND-F1728-CASE2-DONOR-QUAL-002.md):

1. **Resolution of Finding F1728-R20 (Physical Boundary Contact vs. Centroid Clearance):**
   - **Correction of Gap Interpretation:** The previously reported $7.69\,\mu\text{m}$ ($1.02\,\ell_0$) metric was a **centroid-to-boundary distance** from Element 13 $(0.5608, 0.5513)\,\text{mm}$ to the circular hole boundary, **not** an intact physical gap.
   - **Empirical Boundary Contact Verification:** Direct polygon-level vertex and element-connectivity analysis on the authentic coarse mesh ([`PK_HOLE_COARSE_PHYS.inp`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_COARSE_PHYS.inp)) confirms that **six elements** belonging to the 37-element primary damage component ($d \ge 0.10$) have nodes lying directly on the circular hole boundary ($r = 0.10\,\text{mm}$):
     * **Element 151:** Boundary nodes `[7, 638]`, coordinates `[(0.5626, 0.6015), (0.5546, 0.6201)]`, $d = 0.1292$
     * **Element 152:** Boundary node `[637]`, coordinates `[(0.5505, 0.6399)]`, $d = 0.1172$
     * **Element 153:** Boundary nodes `[6, 637]`, coordinates `[(0.5505, 0.6601), (0.5505, 0.6399)]`, $d = 0.1245$
     * **Element 687:** Boundary nodes `[638, 637]`, coordinates `[(0.5546, 0.6201), (0.5505, 0.6399)]`, $d = 0.2439$
     * **Element 734:** Boundary nodes `[6, 636]`, coordinates `[(0.5505, 0.6601), (0.5546, 0.6799)]`, $d = 0.1486$
     * **Element 1088:** Boundary nodes `[7, 639]`, coordinates `[(0.5626, 0.6015), (0.5741, 0.5849)]`, $d = 0.1009$
   - **Physical Polygon Clearance:** The true physical polygon-to-boundary clearance is **$0.0000\,\text{mm}$**; the primary softening damage lobe physically reaches and touches the hole boundary at peak load.
   - **Distinction from Full Crack Rupture:** Physical boundary contact by diffuse softening ($d \in [0.10, 0.58]$) must not be conflated with full macroscopic crack penetration: at Step-2 Peak ($u_y = 0.00729\,\text{mm}$), $d_{\max} = 0.5798$, and there are **zero elements satisfying $d \ge 0.90$** in the entire specimen.
   - **Secondary Flank Contact:** The 10-element secondary crack initiation lobe on the opposite right hole flank also physically contacts the boundary across six elements (`[241, 243, 245, 497, 498, 1379]`, polygon clearance $0.0\,\mu\text{m}$, centroid clearance $7.85\,\mu\text{m}$).

2. **Resolution of Finding F1728-R21 (Mutually Exclusive Disjoint Spatial Error Segmentation):**
   - Corrected the pre-analysis indicator segmentation to establish a strict, mutually exclusive partition across all 2,906 physical elements:
     * **Notch Tip Core ($r \le 0.05\,\text{mm}$):** 23 elements, mean $385.55\,\text{MPa}$, max $1,430.27\,\text{MPa}$ ($25.64\times$ bulk).
     * **Hole Flank Boundary (Disjoint):** 36 elements, mean $162.63\,\text{MPa}$, max $301.26\,\text{MPa}$ ($10.81\times$ bulk).
     * **Notch-Excluded Ligament Corridor (Disjoint):** 39 elements, mean $118.79\,\text{MPa}$, max $263.98\,\text{MPa}$ ($7.90\times$ bulk).
     * **Far-Field Bulk Domain (Disjoint):** 2,808 elements, mean $15.04\,\text{MPa}$, max $230.27\,\text{MPa}$ (anchor).
     * **Partition Total:** $23 + 36 + 39 + 2,808 = 2,906$ elements (100% disjoint, 0 overlaps, 0 omissions).
   - **Auxiliary Overlapping Mask:** An inclusive ligament corridor containing the notch tip singularity contains 60 elements with mean $193.96\,\text{MPa}$ and max $1,430.27\,\text{MPa}$.
   - **Scientific Impact:** Disjoint analysis isolates the true uncracked ligament stress state: the notch-excluded ligament mean error is $118.79\,\text{MPa}$ ($7.90\times$ bulk), more than $3\times$ lower than the notch tip core ($385.55\,\text{MPa}$). Linear-elastic pre-analysis will thus refine the notch tip but starve the uncracked ligament.

3. **Preservation of Accepted Progress:**
   - The source-level root cause of zero stress in `PK_HOLE_COARSE_JOB1.odb` remains established: `f42_mixed_uel.for` Layer 3 visualizer sets `STRESS(I) = 0.D0` and dummy stiffness `DDSDDE(I,I) = 1.D-11`. `PK_HOLE_COARSE_JOB1.odb` alone cannot natively drive remeshing without companion stress recovery.
   - Candidate Donor 1 (`PK_HOLE_METHOD_A_PREANALYSIS.odb`) remains the only currently qualified native $\text{MISESERI}$ donor ($1,430.27\,\text{MPa}$ peak).
   - Exact Step-2 peak provenance is preserved: Frame 167, Step Time 0.327688, $u_y = 0.00729381\,\text{mm}$, $F_{\max} = 0.731015\,\text{kN}$, ODB SHA-256 `834b9bb0...`.

---

## 2. Quantitative Donor Comparison Matrix

| Property / Metric | Candidate Donor 1 (Linear-Elastic Pre-Analysis) | Candidate Donor 2 (Coarse Phase-Field Peak) |
| :--- | :--- | :--- |
| **Source ODB Path** | `PK_HOLE_METHOD_A_PREANALYSIS.odb` | `PK_HOLE_COARSE_JOB1.odb` |
| **File Size & SHA-256** | 2.88 MB / `0A108C6A8404...` | 518.2 MB / `834b9bb035fc...` |
| **Physical Elements** | 2,906 (2,818 quads, 88 tris) | 2,906 physical (8,718 layered) |
| **Step & Frame Index** | Step-1, Frame 10 (Last converged, $t=1.0$) | Step-2, Frame 167 (Peak load state, $t=0.3277$) |
| **Top Displacement $u_y$** | $0.00500\,\text{mm}$ | $0.00729381\,\text{mm}$ |
| **Tensile Reaction Force $F_y$** | N/A (Linear elastic overlay) | $0.731015\,\text{kN}$ ($F_{\max}$) |
| **Maximum Damage $d_{\max}$** | $0.0000$ (Intact elasticity) | $0.579752$ (Active phase-field softening) |
| **Damaged Elements ($d \ge 0.10$)** | 0 | 48 elements (37 primary lobe, 10 secondary, 1 corner) |
| **Fully Broken Elements ($d \ge 0.90$)** | 0 | **0 elements** (No macroscopic crack severance) |
| **Physical Hole Boundary Contact** | N/A (Continuous geometry) | **YES** (6 elements possess boundary nodes, clearance $0.0\,\mu\text{m}$) |
| **Nearest Centroid Clearance** | N/A | $7.69\,\mu\text{m}$ ($1.02\,\ell_0$) [Centroid metric only] |
| **Native $\text{MISESERI}$ Max** | **$1,430.27\,\text{MPa}$** | **$0.00\,\text{MPa}$** (Identically zero across all increments) |
| **Native $\text{MISESERI}$ Nonzero Count** | **2,906 / 2,906 elements** | **0 / 2,906 elements** |
| **Cauchy Stress $\mathbf{S}$ Status** | Nonzero continuum stress tensor | Zeroed out by visualizer UMAT (`STRESS(I)=0.D0`) |
| **Native Remeshing Readiness** | **QUALIFIED FOR NATIVE REMESHING** | **REQUIRES COMPANION STRESS RECOVERY** |

---

## 3. Disjoint Spatial Error Segmentation (Donor 1)

All 2,906 physical elements are partitioned into mutually exclusive disjoint regions:

| Region Definition | Element Count | Mean $\text{MISESERI}$ [MPa] | Max $\text{MISESERI}$ [MPa] | Contrast vs. Bulk Mean |
| :--- | :--- | :--- | :--- | :--- |
| **Notch Tip Core ($r \le 0.05\,\text{mm}$)** | 23 | **385.55** | **1,430.27** | **$25.64\times$** |
| **Hole Flank Vicinity (Disjoint)** | 36 | **162.63** | 301.26 | **$10.81\times$** |
| **Notch-Excluded Ligament (Disjoint)** | 39 | **118.79** | 263.98 | **$7.90\times$** |
| **Far-Field Bulk Domain (Disjoint)** | 2,808 | **15.04** | 230.27 | **$1.00\times$ (Anchor)** |
| **Total Disjoint Domain** | **2,906** | **21.19** (Median: 8.54) | **1,430.27** | — |
| *Auxiliary: Inclusive Ligament Corridor* | *60* | *193.96* | *1,430.27* | *$12.90\times$* |

---

## 4. Damage Topology and Physical Boundary Contact Audit (Donor 2)

```
[Notch Tip (0.50, 0.50)]
        |
        | (Centroid distance: 9.5 um from tip to Element 1184)
        v
[Component 1: 37 Elements]  --> d_max = 0.5798, d_mean = 0.1869, d >= 0.90 count = 0
        |
        | PHYSICAL ELEMENT-LEVEL CONTACT: Polygon clearance = 0.0000 mm
        | Six elements (151, 152, 153, 687, 734, 1088) share boundary nodes 6, 7, 636, 637, 638, 639
        | (Nearest centroid clearance to boundary: 7.69 um = 1.02 l0)
        v
[Circular Hole Boundary (0.65, 0.65), R = 0.10 mm]
        ^
        | PHYSICAL ELEMENT-LEVEL CONTACT: Polygon clearance = 0.0000 mm
        | Six elements (241, 243, 245, 497, 498, 1379) share boundary nodes 1, 12, 13, 628, 644, 645
        | (Nearest centroid clearance to boundary: 7.85 um)
        |
[Component 2: 10 Elements]  --> d_max = 0.2253, d_mean = 0.1542, Secondary Flank Nucleation
```

**Key Topological Findings:**
1. **Physical Boundary Contact:** The primary softening component ($d \ge 0.10$) does not stop short of the hole; it physically reaches the circular void perimeter across six elements (`[151, 152, 153, 687, 734, 1088]`).
2. **Absence of Crack Rupture:** Because $d_{\max} = 0.5798 < 0.90$ across all 2,906 elements, this contact is diffuse phase-field softening, not fully separated crack severance.
3. **Secondary Initiation:** Secondary softening initiates concurrently on the opposite flank, also contacting the perimeter across six elements.
4. **Isolated Artifact:** Component 3 consists of a single element (1140) at the remote corner $(0.99, 0.99)\,\text{mm}$ ($d = 0.1258$, polygon clearance $0.3666\,\text{mm}$), far from the fracture path.

---

## 5. Reconciled Falsifiable Scientific Hypothesis (`HYPOTHESIS F1728-H2-CASE2`)

> **HYPOTHESIS F1728-H2-CASE2:**  
> 1. Native Abaqus `UNIFORM_ERROR` remeshing driven strictly by linear-elastic pre-analysis (Step-1, Donor 1) will produce a mesh highly refined at the singular notch root ($h \le \ell_0/2 = 3.75\,\mu\text{m}$) but coarse across the uncracked oblique ligament into the hole flank ($h > \ell_0/2$) because linear elasticity lacks localized stress gradients away from the notch tip ($385.55\,\text{MPa}$ core vs. $118.79\,\text{MPa}$ ligament).  
> 2. Conversely, driving adaptive remeshing from an authentic coarse phase-field donor state at peak load (Step-2 Peak, Donor 2) requires a companion degraded Cauchy stress recovery operation to generate the physical inter-element stress jumps needed for SPR to refine $h \le \ell_0/2$ continuously across the primary crack lobe into the circular hole boundary.

---

## 6. Execution Accounting and Governance Boundary

- **Submissions Consumed in Subtask:** `0` (`max_new_pbs_submissions = 0`, `submissions_consumed = 0`).
- **Cumulative Project Submissions:** Permanently reconciled at `5` in all ledgers (`1423095`, `1423101`, `1423102`, `1423103`, `1423169`).
- **Zero Forward Fracture Rule:** Strictly observed. Zero forward fracture propagation simulations executed or proposed.
- **Zero Local Abaqus Executions:** All audits performed offline on committed datasets without local CAE or solver binaries.
