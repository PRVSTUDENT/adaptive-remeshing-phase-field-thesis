# Task F1808: Four-Case Native-MISESERI Reproducibility Investigation and Regression Audit (Cases 1, 2, 3, 5)

**Document ID:** `docs/validation/F1808_FOUR_CASE_NATIVE_MISESERI_REPRODUCIBILITY_REPORT.md`  
**Governing Task ID:** `F1808-FOUR-CASE-NATIVE-MISESERI-REPRODUCIBILITY-AND-REGRESSION`  
**Predecessor Task:** `F1807-FOUR-CASE-NATIVE-MISESERI-REGRESSION-AND-QUALITY-EVALUATION` (`REJECT / CONTINUE`)  
**Bridge Review Handoff ID:** `HND-F1808-FOUR-CASE-REPRODUCIBILITY-001`  
**Protocol:** `INDEPENDENT_STRUCTURED_REVIEW_V1`  
**Master Continuation Goal Status:** `OPEN` (Mandatory Invariant)  
**Date:** 16 November 2026  
**Classification:** ADAPTIVE REMESHING RESEARCH ONLY  

---

## 1. Executive Summary & Review Mandate

Following supervisory review directive `HND-F1807-FOUR-CASE-REGRESSION-001` (`DECISION: REJECT`, `ACTION: CONTINUE`, `MASTER_GOAL_STATUS: OPEN`), Task F1808 executes a controlled reproducibility investigation and regression audit across all four canonical registered benchmarks:
- **Case 1:** Mode-I Edge-Cracked Plate ($1.0 \times 1.0\,\text{mm}$, $\ell_0 = 7.5\,\mu\text{m}$, literature target 13,941 elements)
- **Case 2:** Mode-I Plate with an Off-Axis Hole ($1.0 \times 1.0\,\text{mm}$, $\ell_0 = 7.5\,\mu\text{m}$, F1806 baseline 22,924 elements at $\eta_R = 1.8\%$)
- **Case 3:** Notched Plate with Central Hole and Pins ($65 \times 120\,\text{mm}$, $\ell_0 = 0.285\,\text{mm}$, State 2 degraded-elastic recovery donor)
- **Case 5:** Square Plate with Seven Holes ($1.0 \times 1.0\,\text{mm}$, $\ell_0 = 8.0\,\mu\text{m}$, Table 6 literature target 15,714 elements)

### Primary Scientific Questions Addressed

1. **Root-Cause Analysis of Case 2 Discrepancy:** Why did F1807 produce 22,656 elements while F1806 produced 22,924 elements under the reportedly identical post-breach donor and 1.8% target?
   - *Finding:* Systematic audit revealed that the F1807 configuration contained an input deck error: `geometry.notch_length = 0.4` mm instead of `0.5` mm. The 0.1 mm shorter initial notch altered the domain polygon boundaries, edge partitioning, and advancing-front propagation across the authentic donor field.
   - *Proof of Determinism:* Restoring `notch_length = 0.5` in F1808 produced **EXACTLY 22,924 elements** (22,346 quads, 578 tris), with a **100.000% bitwise identical body hash** (`35178C924EB5652DD57991AAD34C4CCB436D5C6F6F132E3704B7D9AFF2F1955A`) matching F1806. The framework is completely deterministic.
2. **Fresh, Authenticated Same-Revision Generation Evidence:**
   - Designed and executed `scripts/remeshing/run_f1808_master.py` with isolated per-case subprocesses (`run_f1808_single_case.py`), eliminating cross-case memory, journal, or seed retention.
   - Preserved individual native Abaqus execution journals (`case_1_abaqus.rpy`, `case_2_abaqus.rpy`, `case_3_abaqus.rpy`, `case_5_abaqus.rpy`) and per-case receipts.
3. **Rigorous Quality Matrix & Scientific Gate Discipline:**
   - All standard Gates 01–07 evaluated and confirmed `PASS` across all four benchmarks (all quad fractions $\ge 97.0\%$, zero nonpositive Jacobians, all max aspect ratios $\le 3.862 \le 4.0$, corner angles within $[25.4^\circ, 146.8^\circ]$, coarsening ratios $\ge 2.10\times \ge 2.0\times$, all element counts $\le 26,746 \le 30,000$).
   - Case 2 outer distal scientific gate is strictly retained as **`FAIL`** (combined outer ligament $h \le \ell_0/2$ coverage is $28.02\% < 50.0\%$).
   - Case 3 secondary corridor scientific gate is strictly retained as **`INCOMPLETE_RESOLUTION`** ($58.32\% \le \ell_0$, with local $h_{\min} = 0.0738\,\text{mm} \ll \ell_0/2$ distinguished from complete active corridor resolution).
4. **Inspectable Image and Artifact Package:**
   - 12 diagnostic PNG figures (full mesh, close-up, and $h/\ell_0$ map for every case) archived in `models/pandey_kumar_mode1/258_f1808_four_case_reproducibility/figures/`.
   - 4-panel publication synthesis figure generated at `results/figures/fig_f1808_four_benchmark_regression_synthesis.png` (and `.pdf`).

---

## 2. Invariant Governance & Code Provenance

| Parameter / Invariant | Required Canonical State | Task F1808 Verified State | Compliance Status |
| :--- | :--- | :--- | :--- |
| **Production Fortran UEL** | `f42_mixed_uel.for` (`CE8D5EDC...`) | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` | **BITWISE MATCH (PASS)** |
| **Shared Adaptive Framework** | `reusable_2d_adaptive_framework.py` (`99EC77D2...`) | `99EC77D2433EB5048DC9B4D70E5EA3B8468073C3BCEA342B7BFE139234700E6D` | **BITWISE MATCH (PASS)** |
| **Cumulative PBS Submissions** | Exactly 35 submissions preserved | 35 cumulative (0 new jobs consumed) | **PASS** |
| **New HPC Jobs Permitted** | Exactly 0 new jobs | 0 new jobs consumed | **PASS** |
| **Active Benchmark Set** | Cases 1, 2, 3, 5 (Case 4 historical) | Cases 1, 2, 3, 5 executed | **PASS** |
| **Master Continuation Goal** | `MASTER_GOAL_STATUS = OPEN` | `MASTER_GOAL_STATUS = OPEN` | **INVARIANT PRESERVED** |

---

## 3. Root-Cause Analysis: Case 2 Discrepancy (F1806 vs F1807 vs F1808)

The supervisory reviewer specifically requested:
> *"Audit F1806 versus F1807 Case 2 configurations, donor identity, sizing bounds, refinement factor, remeshing rules, Abaqus meshing settings and execution provenance. Reproduce the Case 2 mesh from the registered donor with the frozen shared framework, identify the cause of any mesh difference and quantify its effect on outer-ligament resolution and coarsening."*

### A. Systematic Comparative Audit

| Parameter / Option | F1806 Baseline | F1807 Regression | F1808 Reconciled | Audit Assessment |
| :--- | :--- | :--- | :--- | :--- |
| **Configuration Path** | `configs/remeshing/f1806_case2_native_miseseri.json` | `configs/remeshing/f1807_case2_native_miseseri.json` | `configs/remeshing/f1808_case2_native_miseseri.json` | Reconciled |
| **Initial Notch Length ($a$)** | **`0.50 mm`** | **`0.40 mm` (ERROR)** | **`0.50 mm`** | **ROOT CAUSE IDENTIFIED** |
| **Notch Y-Coordinate** | $0.50\,\text{mm}$ | $0.50\,\text{mm}$ | $0.50\,\text{mm}$ | Identical |
| **Notch Slit Opening** | $0.001\,\text{mm}$ | $0.001\,\text{mm}$ | $0.001\,\text{mm}$ | Identical |
| **Off-Axis Hole Center & Radius** | $(0.65, 0.65)\,\text{mm}, r = 0.10\,\text{mm}$ | $(0.65, 0.65)\,\text{mm}, r = 0.10\,\text{mm}$ | $(0.65, 0.65)\,\text{mm}, r = 0.10\,\text{mm}$ | Identical |
| **Ligament Width (Tip to Hole)** | **$0.05\,\text{mm}$ ($x \in [0.50, 0.55]$)** | **$0.15\,\text{mm}$ ($x \in [0.40, 0.55]$)** | **$0.05\,\text{mm}$ ($x \in [0.50, 0.55]$)** | Altered domain in F1807 |
| **Donor ODB Path** | `PK_HOLE_STATE_POSTBREACH_RECOVERY.odb` | `PK_HOLE_STATE_POSTBREACH_RECOVERY.odb` | `PK_HOLE_STATE_POSTBREACH_RECOVERY.odb` | Identical |
| **Donor SHA-256** | `35E9DC19...` (7,417,896 bytes) | `35E9DC19...` (7,417,896 bytes) | `35E9DC19...` (7,417,896 bytes) | Bitwise identical donor |
| **Error Target ($\eta_R$)** | $1.8\%$ | $1.8\%$ | $1.8\%$ | Identical |
| **Sizing Bounds ($h_{\min}, h_{\max}$)** | $[0.0015, 0.020]\,\text{mm}$ | $[0.0015, 0.020]\,\text{mm}$ | $[0.0015, 0.020]\,\text{mm}$ | Identical |
| **Refinement Factor** | 10 | 10 | 10 | Identical |
| **Sizing Method & Indicator** | `UNIFORM_ERROR`, `MISESERI` | `UNIFORM_ERROR`, `MISESERI` | `UNIFORM_ERROR`, `MISESERI` | Identical |
| **Total Physical Elements** | **22,924** | **22,656 (-268)** | **22,924 (+0)** | **100.000% EXACT MATCH** |
| **Physical Mesh Body SHA-256** | `35178C924EB...` | `378F78BD...` | `35178C924EB...` | **100.000% BITWISE MATCH** |

### B. Mathematical & Geometric Mechanism of the Defect

In `reusable_2d_adaptive_framework.py`, the `OffAxisHoleMode1Adapter.get_outer_polygon_points()` method constructs the CAD part boundary from `config.notch_a`:
```python
    def get_outer_polygon_points(self):
        w = self.config.notch_w
        return [
            (0.0, 0.0),
            (self.config.plate_w, 0.0),
            (self.config.plate_w, self.config.plate_h),
            (0.0, self.config.plate_h),
            (0.0, self.config.notch_y + w),
            (self.config.notch_a, self.config.notch_y + w),
            (self.config.notch_a, self.config.notch_y - w),
            (0.0, self.config.notch_y - w)
        ]
```
1. When `notch_a = 0.4` in F1807, the slit vertices were placed at $(0.4, 0.501)$ and $(0.4, 0.499)$. The solid unnotched ligament between the slit tip and the hole (left boundary $x = 0.55$) was $0.15\,\text{mm}$ wide—three times wider than the authentic $0.05\,\text{mm}$ ligament.
2. In contrast, the donor ODB `PK_HOLE_STATE_POSTBREACH_RECOVERY.odb` was solved on a mesh where the slit ended at $x = 0.50\,\text{mm}$.
3. When Abaqus CAE executed `adaptiveRemesh()`, it mapped the stress recovery error from the $a = 0.50\,\text{mm}$ donor onto the altered $a = 0.40\,\text{mm}$ geometry. Because the geometric boundary edges, partitioning lines, and seed positions were displaced, the advancing front produced 22,656 elements.
4. When `notch_length = 0.50` is correctly specified in F1808, Abaqus CAE reproduces the F1806 baseline with **100.000% mathematical bitwise fidelity** (22,924 elements, 22,346 quads, 578 tris, body SHA `35178C924EB5652DD57991AAD34C4CCB436D5C6F6F132E3704B7D9AFF2F1955A`).

### C. Impact on Distal Sizing and Outer-Ligament Resolution

Reconciling the configuration restores the exact F1806 spatial distribution metrics:
- Broad distal fine coverage ($h \le \ell_0/2$ in $x \in [0.75, 1.00]$, $y \in [0.55, 0.75]$): **$89.41\%$** (6,581 elements, compared to $88.70\%$ in F1807).
- Outermost boundary band $x \in [0.95, 1.00]$: achieves $h_{\min} = 2.14\,\mu\text{m} \le 3.75\,\mu\text{m}$ ($0.285\,\ell_0$) and $3.21\%$ fine coverage.
- Combined outer ligament ($x \in [0.90, 1.00]$): **$28.02\%$** (878 elements, compared to $25.69\%$ in F1807).
- Coarsening ratio: **$2.10\times \ge 2.0\times$** ($h_{\text{far}} = 5.22\,\mu\text{m}$ vs $h_{\text{core}} = 2.49\,\mu\text{m}$).
- **Scientific Gate Decision:** Retained as **`FAIL`** ($28.02\% < 50.0\%$), confirming that single-pass static recovery cannot force complete resolution through the outer traction-free boundary without sequential Method A.2 multi-state recovery.

---

## 4. Four-Benchmark Isolated Execution Architecture & Provenance

To guarantee that no Abaqus CAE session state, journal commands, or memory leaks cross benchmark boundaries, Task F1808 implemented a two-tier execution runner:
1. `scripts/remeshing/run_f1808_single_case.py`: A dedicated script executed via `abaqus cae noGUI=... -- <case_id>`. It operates on a single benchmark, creates a fresh MDB model, executes `adaptiveRemesh()`, generates `PK_F1808_CASE_<N>_ADAPT_PHYS.inp`, audits quality, writes `PK_F1808_CASE_<N>_RECEIPT.json`, and archives `case_<N>_abaqus.rpy`.
2. `scripts/remeshing/run_f1808_master.py`: Orchestrates the four individual CAE invocations sequentially, confirms process termination (Exit code 0), validates per-case receipts, and compiles the master four-case receipt `PK_F1808_FOUR_CASE_REPRODUCIBILITY_RECEIPT.json`.

### Input-Output Provenance & Checksums

| Benchmark | Configuration File | Donor ODB Path | Donor SHA-256 | Output Physical Mesh | Physical Mesh Size & Body SHA-256 | Archived CAE Journal |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Case 1** | `configs/remeshing/f1808_case1_native_miseseri.json` | `models/.../257_f1807_four_case_regression/case1/PK_F1807_CASE1_COARSE_DONOR.odb` | `DF246BEA9AD9AD5DD650073156322C6C2213B1B3A26C2C66ECE11D1691E9DCF0` | `models/.../258_f1808_four_case_reproducibility/case1/PK_F1808_CASE_1_ADAPT_PHYS.inp` | 1,011,306 bytes<br>`EAA671FBECC8E1AE759BF3EE5A54AC8BE90F354B087483CD8B513A85DF85F277` | `case_1_abaqus.rpy` |
| **Case 2** | `configs/remeshing/f1808_case2_native_miseseri.json` | `models/.../254_f1804_case2_distal_recovery/PK_HOLE_STATE_POSTBREACH_RECOVERY.odb` | `35E9DC19B1E0A4F5EE5FB3547C9C71004D8882DC50F729C8A8F4CA8A4D50A959` | `models/.../258_f1808_four_case_reproducibility/case2/PK_F1808_CASE_2_ADAPT_PHYS.inp` | 1,649,195 bytes<br>`35178C924EB5652DD57991AAD34C4CCB436D5C6F6F132E3704B7D9AFF2F1955A` | `case_2_abaqus.rpy` |
| **Case 3** | `configs/remeshing/f1808_case3_native_miseseri.json` | `models/.../253_f1803_case3_accurate_recovery/SEC43_STATE2_HIGH_FIDELITY_RECOVERY.odb` | `965136FD7AE637EFF44DEEDF4D152817037CF3C05656D9D1B6006377038362BB` | `models/.../258_f1808_four_case_reproducibility/case3/PK_F1808_CASE_3_ADAPT_PHYS.inp` | 1,925,795 bytes<br>`46024F3241F0C6C8B7BC1D051D52D1E00F53EFDABF3FFFB9160FD7E937912B9C` | `case_3_abaqus.rpy` |
| **Case 5** | `configs/remeshing/f1808_case5_native_miseseri.json` | `models/.../218_f1726_seven_hole_study/PK_F1726_SEVEN_HOLE_COARSE.odb` | `CB673713FDE31593AE452A21BC05BFFC140BCCCE71F1D43D601EE17B43802B0E` | `models/.../258_f1808_four_case_reproducibility/case5/PK_F1808_CASE_5_ADAPT_PHYS.inp` | 1,127,961 bytes<br>`78009AAEE4FE732C0FA56F2DE5487C1717E82E245B4CAF32C3B9CE19AB2B4065` | `case_5_abaqus.rpy` |

---

## 5. Comprehensive Numerical Quality Matrix (Cases 1, 2, 3, 5)

| Metric / Attribute | Case 1 (Mode-I Crack) | Case 2 (Off-Axis Hole) | Case 3 (Hole & Pins) | Case 5 (Seven Holes) | Canonical Gate Threshold |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Physical Nodes ($N$)** | 14,058 | 22,963 | 26,856 | 15,881 | — |
| **Total Physical Elements ($E$)** | **14,087** | **22,924** | **26,746** | **15,466** | $\le 30,000$ (Gate 07: PASS) |
| **Quadrilateral Elements ($E_{\text{quad}}$)** | 13,667 | 22,346 | 26,048 | 15,141 | — |
| **Triangular Elements ($E_{\text{tri}}$)** | 420 | 578 | 698 | 325 | — |
| **Quadrilateral Fraction** | **$97.02\%$** | **$97.48\%$** | **$97.39\%$** | **$97.90\%$** | $\ge 90.0\%$ (Gate 02: PASS) |
| **Triangular Fraction** | $2.98\%$ | $2.52\%$ | $2.61\%$ | $2.10\%$ | $\le 10.0\%$ |
| **Minimum Signed Jacobian ($\det J_{\min}$)**| **$2.48 \times 10^{-7}$** | **$2.87 \times 10^{-7}$** | **$7.65 \times 10^{-4}$** | **$3.92 \times 10^{-7}$** | $> 0.0$ (Gate 01: PASS) |
| **Nonpositive Jacobians** | **0** | **0** | **0** | **0** | Exactly 0 (Gate 01: PASS) |
| **Maximum Aspect Ratio ($AR_{\max}$)** | **2.640** | **2.500** | **3.862** | **2.374** | $\le 4.00$ (Gate 03: PASS) |
| **Median Aspect Ratio ($AR_{\text{med}}$)**| 1.221 | 1.210 | 1.246 | 1.205 | — |
| **Corner Angle Range ($\theta_{\min}, \theta_{\max}$)**| $[31.19^\circ, 137.82^\circ]$ | $[31.37^\circ, 138.48^\circ]$ | $[25.40^\circ, 146.81^\circ]$ | $[29.82^\circ, 139.67^\circ]$ | $[20^\circ, 160^\circ]$ (Gate 04: PASS) |
| **Minimum Element Size ($h_{\min}$)** | $0.706\,\mu\text{m}$ ($0.094\,\ell_0$) | $0.768\,\mu\text{m}$ ($0.102\,\ell_0$) | $0.0470\,\text{mm}$ ($0.165\,\ell_0$) | $0.979\,\mu\text{m}$ ($0.122\,\ell_0$) | $\le 0.50\,\ell_0$ (Gate 05: PASS) |
| **Mean Process-Zone Size ($h_{\text{core}}$)**| $2.925\,\mu\text{m}$ | $2.485\,\mu\text{m}$ | $0.1709\,\text{mm}$ | $3.363\,\mu\text{m}$ | — |
| **Mean Far-Field Size ($h_{\text{far}}$)** | $7.435\,\mu\text{m}$ | $5.222\,\mu\text{m}$ | $0.4237\,\text{mm}$ | $7.120\,\mu\text{m}$ | — |
| **Far-to-Core Coarsening Ratio** | **$2.54\times$** | **$2.10\times$** | **$2.48\times$** | **$2.12\times$** | $\ge 2.00\times$ (Gate 06: PASS) |
| **Literature Target Element Count** | 13,941 | 23,618 | 12,168 | 15,714 | Reference only |
| **Discretization Parity vs Literature**| $+1.05\%$ | $-2.94\%$ | $+119.8\%$ (High-Fidelity) | $-1.58\%$ | Literature comparison |

---

## 6. Scientific Gate Assessment & Corridor Resolution

### Case 1: Mode-I Edge-Cracked Plate
- **Ligament Elements ($x \in [0.5, 1.0], y \in [0.48, 0.52]$):** 918 elements.
  - $h \le \ell_0$: $89.32\%$
  - $h \le \ell_0/2$: $79.85\%$
- **Proximal Crack Tip Elements ($x \in [0.50, 0.55]$):** 628 elements.
  - $h \le \ell_0/2$: **$100.00\%$** (Full physical resolution at initiation tip).
- **Decision:** **`SCIENTIFIC_GATE_TIP = PASS`**.

### Case 2: Plate with Off-Axis Hole
- **Broad Distal Region ($x \in [0.75, 1.00], y \in [0.55, 0.75]$):** 6,581 elements.
  - $h \le \ell_0$: $99.98\%$
  - $h \le \ell_0/2$: **$89.41\%$** (Sub-half-length scale resolution across distal zone).
- **Spatial Binning along Distal Ligament:**
  - Bin 1 ($x \in [0.75, 0.80]$): 2,402 elements, $100.00\% \le \ell_0/2$, $h_{\min} = 0.768\,\mu\text{m}$
  - Bin 2 ($x \in [0.80, 0.85]$): 1,956 elements, $99.03\% \le \ell_0/2$, $h_{\min} = 0.784\,\mu\text{m}$
  - Bin 3 ($x \in [0.85, 0.90]$): 1,345 elements, $96.58\% \le \ell_0/2$, $h_{\min} = 0.936\,\mu\text{m}$
  - Bin 4 ($x \in [0.90, 0.95]$): 566 elements, $41.70\% \le \ell_0/2$, $h_{\min} = 1.717\,\mu\text{m}$
  - Bin 5 ($x \in [0.95, 1.00]$): 312 elements, $3.21\% \le \ell_0/2$, $h_{\min} = 2.140\,\mu\text{m} \le 3.75\,\mu\text{m}$
- **Combined Outer Ligament ($x \in [0.90, 1.00]$):** 878 elements.
  - $h \le \ell_0/2$: **$28.02\%$** (Below the declared $50.0\%$ threshold).
- **Decision:** **`SCIENTIFIC_GATE_OUTER_DISTAL = FAIL`** (Retained without exception).

### Case 3: Notched Plate with Hole and Pins
- **Primary Corridor ($x \in [10.0, 36.5], y \in [45.0, 75.0]$):** 859 elements.
  - $h \le \ell_0$: $0.47\%$ (Coarsened because primary crack has already breached into central hole in State 2 donor).
- **Secondary Corridor ($x \in [36.5, 65.0], y \in [45.0, 65.0]$):** 4,410 elements.
  - $h \le \ell_0$: **$58.32\%$** (Secondary path is captured by recovered stress gradient).
  - $h \le \ell_0/2$: $2.38\%$
  - Minimum element size: **$h_{\min} = 0.0738\,\text{mm} \ll \ell_0/2 = 0.1425\,\text{mm}$**.
- **Scientific Clarification on Local vs Corridor Resolution:** In agreement with supervisory instructions, local minimum element size $h_{\min} < \ell_0/2$ does **NOT** prove complete phase-field corridor resolution. While the crack initiation site at the hole perimeter reaches $0.0738\,\text{mm}$, only $58.32\%$ of the broad active corridor satisfies $h \le \ell_0$.
- **Decision:** **`SCIENTIFIC_GATE_SECONDARY_CORRIDOR = INCOMPLETE_RESOLUTION`** (Retained without exception).

### Case 5: Square Plate with Seven Holes
- **Upper Inter-Hole Corridor ($x \in [0.15, 0.85], y \in [0.45, 0.65]$):** 5,295 elements.
  - $h \le \ell_0$: **$99.04\%$**
- **Lower Inter-Hole Corridor ($x \in [0.15, 0.85], y \in [0.30, 0.45]$):** 2,735 elements.
  - $h \le \ell_0$: **$94.26\%$**
- **Decision:** **`SCIENTIFIC_GATE_INTER_HOLE = PASS`**.

---

## 7. Inspectable Artifact Registry

### A. Four-Panel Publication Synthesis Figure
- **PNG (300 DPI):** [fig_f1808_four_benchmark_regression_synthesis.png](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/fig_f1808_four_benchmark_regression_synthesis.png) (802,136 bytes)
- **Vector PDF:** [fig_f1808_four_benchmark_regression_synthesis.pdf](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/fig_f1808_four_benchmark_regression_synthesis.pdf) (51,318 bytes)

### B. Individual Benchmark Diagnostic Image Set
All 12 diagnostic PNG files are rendered at 300 DPI and archived under `models/pandey_kumar_mode1/258_f1808_four_case_reproducibility/figures/`:
1. **Case 1 (Mode-I Crack):**
   - Full Mesh: [case_1_mesh_full.png](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/258_f1808_four_case_reproducibility/figures/case_1_mesh_full.png) (2,637,462 bytes)
   - Sizing Map ($h/\ell_0$): [case_1_h_over_l0.png](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/258_f1808_four_case_reproducibility/figures/case_1_h_over_l0.png) (1,919,778 bytes)
   - Critical Region Close-Up: [case_1_mesh_closeup.png](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/258_f1808_four_case_reproducibility/figures/case_1_mesh_closeup.png) (1,982,474 bytes)
2. **Case 2 (Off-Axis Hole):**
   - Full Mesh: [case_2_mesh_full.png](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/258_f1808_four_case_reproducibility/figures/case_2_mesh_full.png) (2,878,474 bytes)
   - Sizing Map ($h/\ell_0$): [case_2_h_over_l0.png](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/258_f1808_four_case_reproducibility/figures/case_2_h_over_l0.png) (2,154,633 bytes)
   - Distal Corridor Close-Up: [case_2_mesh_closeup.png](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/258_f1808_four_case_reproducibility/figures/case_2_mesh_closeup.png) (2,831,014 bytes)
3. **Case 3 (Hole & Pins):**
   - Full Mesh: [case_3_mesh_full.png](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/258_f1808_four_case_reproducibility/figures/case_3_mesh_full.png) (2,345,518 bytes)
   - Sizing Map ($h/\ell_0$): [case_3_h_over_l0.png](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/258_f1808_four_case_reproducibility/figures/case_3_h_over_l0.png) (1,712,374 bytes)
   - Double-Corridor Close-Up: [case_3_mesh_closeup.png](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/258_f1808_four_case_reproducibility/figures/case_3_mesh_closeup.png) (2,580,751 bytes)
4. **Case 5 (Seven Holes):**
   - Full Mesh: [case_5_mesh_full.png](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/258_f1808_four_case_reproducibility/figures/case_5_mesh_full.png) (2,506,413 bytes)
   - Sizing Map ($h/\ell_0$): [case_5_h_over_l0.png](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/258_f1808_four_case_reproducibility/figures/case_5_h_over_l0.png) (1,855,730 bytes)
   - Inter-Hole Close-Up: [case_5_mesh_closeup.png](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/258_f1808_four_case_reproducibility/figures/case_5_mesh_closeup.png) (2,392,841 bytes)

### C. Physical Meshes, Execution Journals & Receipts
- Master Four-Case Receipt: [PK_F1808_FOUR_CASE_REPRODUCIBILITY_RECEIPT.json](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/258_f1808_four_case_reproducibility/PK_F1808_FOUR_CASE_REPRODUCIBILITY_RECEIPT.json)
- Case 1 Physical Mesh: [PK_F1808_CASE_1_ADAPT_PHYS.inp](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/258_f1808_four_case_reproducibility/case1/PK_F1808_CASE_1_ADAPT_PHYS.inp)
- Case 2 Physical Mesh: [PK_F1808_CASE_2_ADAPT_PHYS.inp](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/258_f1808_four_case_reproducibility/case2/PK_F1808_CASE_2_ADAPT_PHYS.inp)
- Case 3 Physical Mesh: [PK_F1808_CASE_3_ADAPT_PHYS.inp](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/258_f1808_four_case_reproducibility/case3/PK_F1808_CASE_3_ADAPT_PHYS.inp)
- Case 5 Physical Mesh: [PK_F1808_CASE_5_ADAPT_PHYS.inp](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/258_f1808_four_case_reproducibility/case5/PK_F1808_CASE_5_ADAPT_PHYS.inp)

---

## 8. Unit Testing and Regression Verification

The dedicated test suite `tests/unit/test_f1808_four_case_reproducibility.py` validates all aspects of this task:
- `TestF1808GovernanceInvariants`: Bitwise UEL and framework invariance, 35 cumulative PBS submissions, 0 new jobs, `MASTER_GOAL_STATUS = OPEN` (3/3 PASS).
- `TestF1808Case2ReproducibilityRootCause`: Configuration audit, notch length reconciliation, 22,924 element parity, and bitwise body match against F1806 (2/2 PASS).
- `TestF1808FourCaseMeshQualityGates`: All standard Gates 01–07 across all four benchmarks (1/1 PASS).
- `TestF1808ScientificAssessments`: Scientific gates for Cases 1, 2, 3, and 5 (4/4 PASS).
- `TestF1808InspectableArtifacts`: Physical meshes, execution journals, and diagnostic figures (3/3 PASS).

**Full Active Test Suite:** `60/60 PASSED in 2.83s` (across `test_f1800` through `test_f1808`).
