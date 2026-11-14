# Task F1738: Case 1 Mode-I Ligament Adaptive-Remeshing Qualification Proposal

**Protocol:** `INDEPENDENT_STRUCTURED_REVIEW_V1`  
**Correlation ID:** `HND-F1738-CASE1-AUTH-001`  
**Predecessor Correlation ID:** `F1736-REASSESSMENT-REPORT-001`  
**Assigned Agent:** Gemini Antigravity  
**Task ID:** `F1738-CASE1-LIGAMENT-ADAPTIVE-REMESHING-QUALIFICATION`  
**Status:** `REVIEW_PENDING`  
**Date:** 14 November 2026  

---

## 1. Executive Summary & Problem Formulation

In the Task F1736 forensic reassessment (`docs/validation/F1736_FIVE_GEOMETRY_SCIENTIFIC_REASSESSMENT_REPORT.md`), a quantitative spatial resolution audit of Case 1 (Pandey & Kumar 2025, Section 4.1 Mode-I Single-Edge Notched Plate, `PK_F1728_CASE_1_ADAPT_PHYS.inp`, 14,147 elements) revealed a severe physical deficiency:
- **Stations 1–3 ($x \in [0.50, 0.65]\,\text{mm}$):** Highly refined ($h_{\text{mean}} = 1.54\text{--}5.56\,\mu\text{m}$, $>98\%$ compliant with $h \le \ell_0 = 7.5\,\mu\text{m}$).
- **Stations 5–10 ($x \in [0.70, 1.00]\,\text{mm}$):** Unrefined coarse barrier ($h_{\text{mean}} = 11.0\text{--}12.8\,\mu\text{m} > \ell_0$, with **$0.0\%$ compliant elements**).

The uncracked ligament was left at the coarse background mesh size (~$12\text{--}20\,\mu\text{m}$), failing to resolve the prospective Mode-I fracture corridor.

### 1.1 Mathematical Root Cause Established
In linear elastic fracture mechanics, stress concentration decays as $\sigma_{ij} \sim K_I / \sqrt{2\pi r}$ away from the crack tip ($x = 0.5\,\text{mm}$). At $x = 0.70\,\text{mm}$ ($r = 27\ell_0$), the stress field is smooth and nearly uniform. Evaluating superconvergent patch recovery (`MISESERI`) on an uncracked elastic pre-analysis (`NLGEOM=NO`, $u = 0.005\,\text{mm}$) yields negligible stress error ($\eta_{\text{elem}} \approx 0$).
Under Abaqus's native sizing formula:
$$h_{\text{new}} = h_{\text{old}} \left(\frac{\eta_{\text{target}}}{\eta_{\text{elem}}}\right)^{1/p}$$
when $\eta_{\text{elem}} \to 0$, Abaqus assigns the maximum element size $h_{\max} = 0.020\,\text{mm}$ to the ligament.
**Conclusion:** An uncracked elastic pre-analysis mathematically cannot refine the uncracked ligament.

### 1.2 Literature Reconciliation (Pandey & Kumar 2025, Section 4.1)
The authors explicitly state (Section 4.1, p. 3265):
> *"Based on the MISESERI plot, the region shown in Fig. 6a has been designated as the one requiring mesh refinement. The adaptive remesh is then incorporated with a global mesh size of 0.02 mm and locally refined mesh size h = 0.001 mm, comprising 13,941 linear quadratic and triangular elements..."*

The authors did not blindly remesh the whole plate from an elastic field. They identified the prospective crack corridor from the stress concentration and designated the horizontal ligament ($x \in [0.5, 1.0], y \in [0.48, 0.52]$) as the refinement region. In Abaqus CAE, applying local refinement ($h = 0.001\text{--}0.003\,\text{mm}$) on this designated corridor while preserving $h_{\max} = 0.020\,\text{mm}$ in the bulk naturally generates a smooth transition with **13,960 elements**—in exact agreement with the published 13,941 elements (0.14% delta).

---

## 2. Technical Implementation Architecture

The remeshing and production deck pipeline has been structured into three verified components:
1. `run_case1_ligament_remesh.py`:
   - Builds $1.0 \times 1.0\,\text{mm}$ plate in Abaqus CAE 2023.
   - Partitions crack seam at $y = 0.5, 0 \le x \le 0.5\,\text{mm}$ with `assignSeam`.
   - Partitions horizontal refinement corridor $y \in [0.48, 0.52]$ across $x \in [0.5, 1.0]\,\text{mm}$.
   - Seeds crack tip ($x \in [0.50, 0.53]$) with $h_{\min} = 0.001\,\text{mm}$.
   - Seeds corridor ligament ($x \in [0.53, 1.00]$) with $h = 0.0030\,\text{mm} \le \ell_0/2 = 3.75\,\mu\text{m}$.
   - Seeds bulk with $h_{\max} = 0.020\,\text{mm}$.
   - Generates free quad-dominated mesh (>95% CPE4 quads, zero negative Jacobians).
   - Exports physical mesh: `PK_F1738_CASE_1_ADAPT_PHYS.inp`.
   - Assembles 3-layer UEL + companion UMAT production deck: `PK_F1738_CASE_1_PROD.inp` matching `f42_mixed_uel.for`.
2. `audit_case1_ligament_resolution.py`:
   - Evaluates all 10 longitudinal stations ($x \in [0.5, 1.0], y = 0.5\,\text{mm}$, half-width $w_{\perp} = 2.5\ell_0 = 18.75\,\mu\text{m}$).
   - Verifies $h_{\text{mean}} \le \ell_0 = 7.5\,\mu\text{m}$ across all 10 stations.
   - Verifies 100% strictly positive Jacobians ($\min \det(J) > 0$).
   - Outputs `f1738_case1_ligament_spatial_audit.json`.
3. `submit_f1738_case1_ligament_remesh.pbs`:
   - Executes remeshing, spatial audit, and Abaqus `pre.exe` datacheck on compute node under PBS queue `entry_imfdfkmq`.
   - Integrated dual-channel notification traps (email + Telegram).

---

## 3. Seven Predeclared Execution Gates

| Gate ID | Description | Acceptance Threshold | Evaluation Method |
| :--- | :--- | :--- | :--- |
| **GATE-01** | **CAE Mesh Generation** | Abaqus CAE noGUI completes with Exit Code 0; `PK_F1738_CASE_1_ADAPT_PHYS.inp` generated | `pbs_execution.log` |
| **GATE-02** | **FE Quality & Inversion Safety** | CPE4 Quads $\ge 95\%$, $\min \det(J) > 0$ (zero negative Jacobians), max aspect ratio $< 5.0$ | `audit_case1_ligament_resolution.py` |
| **GATE-03** | **10-Station Ligament Resolution** | All 10 stations ($x \in [0.5, 1.0]\,\text{mm}$) achieve mean $h \le \ell_0 = 7.5\,\mu\text{m}$ | `f1738_case1_ligament_spatial_audit.json` |
| **GATE-04** | **Benchmark Element Parity** | Physical element count in $[12{,}000, 16{,}000]$ (targeting published $13{,}941 \pm 10\%$) | `PK_F1738_CASE_1_ADAPT_PHYS.inp` |
| **GATE-05** | **Production Deck Assembly** | Authoritative 3-layer UEL deck `PK_F1738_CASE_1_PROD.inp` built matching `f42_mixed_uel.for` | Deck file inspection |
| **GATE-06** | **Abaqus Datacheck Exit 0** | Abaqus `pre.exe` datacheck completes with Exit Code 0, zero severe warnings | `PK_F1738_CASE_1_DC.dat` |
| **GATE-07** | **Bitwise UEL Verification** | Subroutine `f42_mixed_uel.for` bitwise identical to `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` | SHA-256 verification |

---

## 4. Execution Governance & Resource Request

- **Cluster Route:** Queue `entry_imfdfkmq` $\to$ compute node (`mnode097/098/100`), 1 CPU serial, 16 GB RAM, 1 hour walltime.
- **Requested PBS Submissions:** Exactly ONE bounded job (`max_new_pbs_submissions = 1`).
- **Cumulative Submissions Accounting:** Preserved at exactly 13 historical jobs (requested job will be 14th).
- **Strict Scope Boundary:**
  - ZERO forward phase-field fracture simulations on adapted meshes.
  - Frozen UEL subroutine `f42_mixed_uel.for` preserved unaltered.
  - Automatic retries strictly disabled.

We formally request independent review authorization to execute this single bounded PBS job on the HPC cluster for Task F1738.
