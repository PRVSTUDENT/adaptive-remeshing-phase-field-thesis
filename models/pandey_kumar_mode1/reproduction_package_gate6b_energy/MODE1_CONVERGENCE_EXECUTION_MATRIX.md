# Mode-I Multi-Quantity Convergence Execution Matrix & Candidate Qualification Architecture

**Authoritative Supervisor Pack Reference:** `docs/supervisor_reports/08-10-2026/MA_ModeI_Supervisor_Meeting_Pack_2026-10-08/`  
**Protocol Version:** 2  
**Governing Directive:** *"We need to have understood everything related to the first model before we increase complexity."*  
**Date:** 02 October 2026, 09:55 CEST (Supervisor Meeting: Thursday, 08 October 2026, 10:00)  
**Active Phase:** `MODE1_GATE6B_ENERGY_CONVERGENCE_AND_STEP2_RECONCILIATION_ACTIVE`  
**Task Reference:** `F1147-GATE6B-TEMPORAL-CANDIDATES-PREPARATION-AND-DATACHECKS-20261002` (Revision 16)  
**Classification:** `AUTHORITATIVE_CONVERGENCE_PLAN_AND_HISTORICAL_INVENTORY`

---

## 1. Executive Summary & Governance Principles

This document establishes the **authoritative Mode-I convergence execution matrix**, incorporates a blocking **source-lineage parity audit**, reconciles all asynchronous task evidence (`task-842`, `task-877`, `task-939`, `task-945`, `task-1080`), audits and freezes all convergence criteria against dated project evidence, documents the cluster **Abaqus 2023 Datacheck qualification** for candidate spatial meshes, freezes the comprehensive **Equation-to-Code-to-Output Map** with the **Three-Way Dimensional & Provenance Framework for 2D Out-of-Plane Thickness Normalization** ($1\,\text{kN/mm}^2 = 1\,\text{GPa} = 1000\,\text{MPa} = 1\,\text{J/mm}^3$, Pandey & Kumar 2025 Sec. 4.1 2D formulation with no thickness prescription, $t_{\text{ref}} = 1.0\,\text{mm}$ project normalization convention, companion Solid Section 1.0 secondary corroboration, $\text{kN}\cdot\text{mm} \equiv \text{J} = 1000\,\text{mJ}$), and defines the conditional execution sequence for Gate-6B.

### Core Governance Principles:
1. **Multi-Quantity Evaluation:** Mesh convergence is not determined by initial stiffness $K_0$ or peak force $F_{\max}$ alone. A comprehensive 10-quantity evaluation is enforced across mechanical, energetic, and spatial localization fields:
   $$F(u), K_0, F_{\max}, u_{\text{peak}}, E_{\text{elas}}(u), E_{\text{frac}}(u), W_{\text{ext}}(u), \Delta_{\text{book}}(u), d(x, y=0.5), y_{\text{crack}}$$
2. **Zero Redundant Runs:** High-throughput cluster capability must not be used to submit redundant or dummy simulations. Every job must be independently justified, qualified, and explicitly authorized.
3. **Source-Lineage Provenance & Parity Certification:** User subroutine Fortran hash `C540B54A...` used in historical fixed-mesh jobs (`1406015`--`1406896`) is mathematically audited against authoritative hash `5CD0D2C0...` and production branch `CE8D5EDC...`. All implementations are certified as **`OUTPUT_ONLY_NONINVASIVE`** with 100.000% mathematical and mechanical parity on 15,192-element overlap cases. Historical `C540B54A...` results are preserved and utilized as mechanically equivalent/output-only evidence where the prior source-diff audit proves equivalence.
4. **Documentary Provenance & Criteria Integrity:** A systematic audit against dated project commits and session logs proved that arbitrary numerical tolerance bands (such as $F_{\max} \in [0.735, 0.745]\,\text{kN}$, $\delta_2(F_{\max}) \in (1.5\%, 3.0\%)$, $K_0 \pm 0.50\%$, and fixed $E_{\text{frac}} \pm 3.0\%$) were constructed post-hoc after historical outcomes were already known. They are formally classified as **`POST_HOC_NOT_ADMISSIBLE_AS_PREDECLARED_CRITERIA`** and revoked. The governing spatial criterion is outcome-independent successive-resolution relative error decay (**`TREND_ONLY`**), reporting actual successive differences without newly invented pass/fail bands.
5. **Preflight Datacheck Qualification Confirmed:** Candidate packages $S_2$ (32,130 finite elements) and $S_3$ (41,912 finite elements) passed full Abaqus 2023 / Intel Fortran 2021.13.0 compilation and datacheck preflight on the cluster with **Exit Code 0** (verified in `task-939` and `task-945`).
6. **Conditional Submission Release Gate:** Passing datacheck is necessary but strictly *insufficient* to authorize solver submission. Physical release of $S_2$ and $S_3$ is conditional on the normal completion and authoritative energy qualification of reference Job `1409734.mmaster02`. **ZERO SUBMISSIONS PRIOR TO S1 QUALIFICATION**.
7. **No Automatic Retries:** Candidate Step-2 adaptive mesh (Job `1409585.mmaster02`, 62,057 finite elements) is maintained under `ROOT_CAUSE_CANDIDATE_NOT_YET_RECONCILED` with zero retries permitted.

---

## 2. Reconciled Asynchronous Task Evidence

The asynchronous background tasks executed during the Gate-6B audit were retrieved, examined from raw terminal logs, and verified:

| Task ID | Execution Timestamp (CEST) | Script / Command | Exit Code | Raw Result & Findings | Log SHA-256 Checksum |
| :--- | :---: | :--- | :---: | :--- | :---: |
| **`task-842`** | 2026-10-01 21:36:25 | `uv run --with pytest pytest tests/unit/test_pandey_kumar_step_increment_consistency.py tests/unit/test_pandey_kumar_adaptive_refinement.py tests/unit/test_mode1_adapted_decks_contract.py` | **0** | **15 passed in 0.25s**. Verified step-increment consistency (3/3), adaptive refinement (8/8), and adapted deck contracts (4/4). | `A39BD6C8E5C6C094F60AC0E8245BF20950DCE28C0F40DD8DA7D8D7A2249A2AF8` |
| **`task-877`** | 2026-10-01 21:41:40 | `uv run python search_criteria_provenance.py` | **0** | Git commit scan across repository history. Proved $K_0 \pm 0.5\%$, $\varepsilon_{\text{book}} < 0.12\%$, and crack-path tolerances were formulated post-hoc. | `CD424B418326AB4D6C1995C9EBE481190049652A0911DB86D7D76664FF4573C6` |
| **`task-939`** | 2026-10-01 21:45:05 | `powershell -File Invoke-GuardedSsh.ps1 -RemoteCommand "bash run_s2_datacheck.sh"` | **0** | **Abaqus JOB PK_M1_S2_DC COMPLETED, Exit Code 0**. Intel Fortran 2021.13.0 compiled `uel_` and `umat_` with automatic CPU dispatch. End Analysis Input File Processor with 0 errors. | `83EEEA8D159BBAD4C329C14328FC2B6B7CBB82D0C6065DD6ED84B0DA9EB574E7` |
| **`task-945`** | 2026-10-01 21:45:28 | `powershell -File Invoke-GuardedSsh.ps1 -RemoteCommand "bash run_s3_datacheck.sh"` | **0** | **Abaqus JOB PK_M1_S3_DC COMPLETED, Exit Code 0**. Intel Fortran 2021.13.0 compiled `uel_` and `umat_` with automatic CPU dispatch. End Analysis Input File Processor with 0 errors. | `2D318B6A8C90185B4EE8A3299D52F67E11E96C7B99EC92F3CB681B72E863546A` |
| **`task-1080`** | 2026-10-01 21:52:45 | `uv run --with pytest pytest tests/unit/test_pandey_kumar_step_increment_consistency.py tests/unit/test_pandey_kumar_adaptive_refinement.py tests/unit/test_mode1_adapted_decks_contract.py` | **0** | **15 passed in 0.25s**. Independent confirmation of regression safety. | `A39BD6C8E5C6C094F60AC0E8245BF20950DCE28C0F40DD8DA7D8D7A2249A2AF8` |

---

## 3. Source-Lineage Audit: Fortran Hash Parity Proof

A rigorous diff and mathematical scan between historical subroutine `f42_mixed_uel.for` (SHA-256 `c540b54a2a7ee96a51deee49bdab714ed0fb27344f703f11abf17f76e985b14b`, 704 lines) and authoritative subroutine `f42_mixed_uel.for` (SHA-256 `5cd0d2c015c9ead91c99d7a744156cc86f5b5ea26473bbed7d6e5515fe30fa46`, 901 lines) was performed under Task F1126:

### Key Audit Findings:
1. **Single Production Source Branch (`CE8D5EDC...`):**
   - Corrected Fortran subroutine `f42_mixed_uel.for` (SHA-256 `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`, 907 lines) has been established as the single authoritative source branch across S1, S2, and S3.
   - Verified via strict unified diff against `5CD0D2C0...`: Strictly **0 diff lines** in `SUBROUTINE UEL` and strictly **0 diff lines** in `SUBROUTINE UMAT`.
   - The ONLY substantive modification is the integration of `CALL GETOUTDIR(OUTDIR_STR, L_OUTDIR)` in `UEXTERNALDB` ensuring that `uel_energy_balance.csv` is written to the simulation working directory.
2. **Residual Vector (`RHS`):** Strictly **0 diff lines** across all versions. The element residual equations governing displacement and phase-field equilibrium are bit-for-bit identical.
3. **Tangent Stiffness Matrix (`AMATRX`):** Strictly **0 mathematical differences**. All punch-card line-wrapping rules preserved.
4. **Constitutive Update & Weak Form:** Linear elasticity tensor `D_ELAS`, symmetric strain computation, stress tensor, damage degradation function $g(d) = (1-d)^2 + k$, crack driving source $\psi_0^+$, and phase-field weak form matrices `A_M` and `R_M` are **100.000% identical**.
5. **Functional Additions in `5CD0D2C0...` and `CE8D5EDC...`:**
   - Common storage capacity `N_CAPACITY` expanded from 100,000 to 150,000 nodes to support large meshes up to 150k elements.
   - Internal calculation of element stored elastic strain energy (`E_ELAS_ELEM`) and fracture surface energy (`E_FRAC_ELEM`), logged to Abaqus solver energy accumulators `ENERGY(2)` and `ENERGY(7)`.
   - Populated companion visualizer layer state variables `STATEV(17..20)` for ODB contour plotting of energy densities.
   - File logging to Unit 105 (`uel_energy_balance.csv`) in `UEXTERNALDB` on accepted increments.
6. **15,192-Element Overlap Mechanical Parity:**
   - **Job `1398090`** (Uninstrumented baseline): $K_0 = 137.945520\,\text{kN/mm}$, $F_{\max} = 0.757778\,\text{kN}$, $u(F_{\max}) = 0.005857\,\text{mm}$, $W_{\text{trap}} = 2.359329\,\text{mJ}$.
   - **Job `1406015` / `1406839`** (`C540B54A...`, Visualizer): $K_0 = 137.945520\,\text{kN/mm}$, $F_{\max} = 0.757778\,\text{kN}$, $u(F_{\max}) = 0.005857\,\text{mm}$, $W_{\text{trap}} = 2.359329\,\text{mJ}$ (relative difference: $0.000000\%$).
   - **Job `1409577`** (`5CD0D2C0...`, Energy): $K_0 = 137.945520\,\text{kN/mm}$, $F_{\max} = 0.757778\,\text{kN}$, $u(F_{\max}) = 0.005857\,\text{mm}$, $W_{\text{trap}} = 2.359329\,\text{mJ}$ (relative difference: $0.000000\%$).
   - **Job `1409705`** (`13408A83...`, Energy): $K_0 = 137.945520\,\text{kN/mm}$, $F_{\max} = 0.757778\,\text{kN}$, $u(F_{\max}) = 0.005857\,\text{mm}$, $W_{\text{trap}} = 2.359329\,\text{mJ}$ (relative difference: $0.000000\%$).
7. **Classification:** Confirmed as **`OUTPUT_ONLY_NONINVASIVE`**. All mechanical response quantities ($F(u), K_0, F_{\max}, u_{\text{peak}}, W_{\text{trap}}$), spatial damage profiles $d(x, y=0.5)$, and pre-peak Unit 105 energy balance data from historical runs are physically valid and equivalent to `CE8D5EDC...`.

---

## 4. Table 1: Historical 1-CPU Serial Mode-I Fixed-Mesh Inventory

This inventory audits all historical 1-CPU serial Mode-I fixed-mesh jobs executed on the cluster, explicitly classifying data availability across the **10 canonical project quantities**:
1. $F(u)$ load-displacement response curve
2. $K_0$ initial structural stiffness
3. $F_{\max}$ peak reaction force
4. $u(F_{\max})$ displacement at peak load
5. $E_{\text{elas}}(u)$ stored elastic strain energy
6. $E_{\text{frac}}(u)$ regularized fracture surface energy
7. $W_{\text{ext}}(u)$ external boundary work ($W_{\text{trap}}$)
8. $\Delta_{\text{book}}(u) \equiv E_{\text{model}} - W_{\text{ext}}$ bookkeeping difference
9. $d(x, y=0.5)$ spatial damage profile across the ligament
10. Crack path ($y_{\text{crack}}(x)$ centerline trajectory)

| Case ID & Mesh Name | Element Count & Type | $h_{\text{corridor}}$ [$\mu\text{m}$] | $h/l_0$ | Time Step Schedule | PBS Job ID | Exit Status | User Subroutine Hash & Source Lineage Classification | Mechanical Availability ($F(u), K_0, F_{\max}, u_{\text{peak}}, W_{\text{ext}}$) | Energetic Availability ($E_{\text{elas}}, E_{\text{frac}}, \Delta_{\text{book}}$) | Spatial Availability ($d(x), y_{\text{crack}}$) | Historical Findings & Provenance Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **$S_1$ Corrected Ref**<br>`PK_M1_REF15K_ENERGY` | 15,192<br>CPE4 | $3.00$ | $0.400$ | Nominal $1\times$<br>(7,000 incs) | `1409734`<br>(Prior: `1409705`, `1398090`) | `R` (Running)<br>(1409705: Exit 0) | FOR: `CE8D5EDC...`<br>`CORRECTED_GETOUTDIR_PRODUCTION` | **AVAILABLE**<br>Full horizon ($u=10\,\mu\text{m}$) | **AVAILABLE**<br>Live CSV + All_elem SDV17-20 | **AVAILABLE**<br>Live ODB + SDV1-20 | Active 1-CPU replacement solve `1409734.mmaster02` on `mnode097/0`. Prior Job 1409705 verified 100.000% mechanical parity with companion index mapping diagnosed. |
| **$S_1$ Visualizer**<br>`PK_M1_FIX_H0030_VIS` | 15,192<br>CPE4 | $3.00$ | $0.400$ | Nominal $1\times$<br>(7,000 incs) | `1406015`<br>`1406839` | Exit 0<br>(0 cutbacks) | FOR: `C540B54A...`<br>`OUTPUT_ONLY_NONINVASIVE` | **AVAILABLE**<br>Full horizon | **AVAILABLE**<br>Via Unit 105 CSV & companion SDVs | **AVAILABLE**<br>Full horizon ($u=10\,\mu\text{m}$) | Full energy & spatial recovery: $K_0=137.95\,\text{kN/mm}$, $F_{\max}=0.7578\,\text{kN}$, pre-peak $|\Delta_{\text{book}}| < 0.008\%$. |
| **$S_2$ Fine**<br>`PK_M1_FIX_H0020_VIS` | 32,130<br>CPE4 | $2.00$ | $0.267$ | Nominal $1\times$<br>(6,000 incs) | `1406016` | Cutback at $u=6.82\,\mu\text{m}$ | FOR: `C540B54A...`<br>`OUTPUT_ONLY_NONINVASIVE` | **AVAILABLE**<br>Up to $u=6.82\,\mu\text{m}$ | **AVAILABLE**<br>Up to $u=6.20\,\mu\text{m}$ (Unit 105) | **AVAILABLE**<br>Up to $u=6.82\,\mu\text{m}$ | $K_0=137.89\,\text{kN/mm}$ ($-0.04\%$), $F_{\max}=0.7412\,\text{kN}$ ($-2.19\%$). Pre-peak energy matched to reference. |
| **$S_3$ Finer**<br>`PK_M1_FIX_H0015_VIS` | 41,912<br>CPE4 | $1.50$ | $0.200$ | Nominal $1\times$<br>(6,000 incs) | `1406017` | Cutback at $u=7.84\,\mu\text{m}$ | FOR: `C540B54A...`<br>`OUTPUT_ONLY_NONINVASIVE` | **AVAILABLE**<br>Up to $u=7.84\,\mu\text{m}$ | **AVAILABLE**<br>Up to $u=6.20\,\mu\text{m}$ (Unit 105) | **AVAILABLE**<br>Up to $u=7.84\,\mu\text{m}$ | $K_0=137.86\,\text{kN/mm}$ ($-0.06\%$), $F_{\max}=0.7322\,\text{kN}$ ($-3.38\%$). Pre-peak energy matched to reference. |
| **$S_4$ Very Fine**<br>`PK_M1_S4_H00125` | 51,408<br>CPE4 | $1.25$ | $0.167$ | Nominal $1\times$<br>(6,000 incs) | `1406018` | Cutback at $u=7.21\,\mu\text{m}$ | FOR: `C540B54A...`<br>`OUTPUT_ONLY_NONINVASIVE` | **AVAILABLE**<br>Up to $u=7.21\,\mu\text{m}$ | **AVAILABLE**<br>Up to $u=6.20\,\mu\text{m}$ (Unit 105) | **AVAILABLE**<br>Up to $u=7.21\,\mu\text{m}$ | $K_0=137.84\,\text{kN/mm}$ ($-0.08\%$), $F_{\max}=0.7290\,\text{kN}$ ($-3.80\%$). Pre-peak $E_{\text{frac}}$ within $1.56\%$ of $S_1$. |
| **$S_5$ Ultra Fine**<br>`PK_M1_S5_H00100` | 69,384<br>CPE4 | $1.00$ | $0.133$ | Nominal $1\times$<br>(6,000 incs) | `1406019` | Cutback at $u=9.58\,\mu\text{m}$ | FOR: `C540B54A...`<br>`OUTPUT_ONLY_NONINVASIVE` | **AVAILABLE**<br>Up to $u=9.58\,\mu\text{m}$ | **AVAILABLE**<br>Up to $u=6.20\,\mu\text{m}$ (Unit 105) | **AVAILABLE**<br>Up to $u=9.58\,\mu\text{m}$ | $K_0=137.82\,\text{kN/mm}$ ($-0.09\%$), $F_{\max}=0.7255\,\text{kN}$ ($-4.26\%$). Traversed $95.8\%$ of displacement horizon. |
| **$T_1$ Coarse Time**<br>`PK_M1_T1_COARSE` | 15,192<br>CPE4 | $3.00$ | $0.400$ | Coarse $2\times$<br>(3,500 incs) | `1406020` | Exit 0<br>(0 cutbacks) | FOR: `C540B54A...`<br>`OUTPUT_ONLY_NONINVASIVE` | **AVAILABLE**<br>Full horizon ($u=10\,\mu\text{m}$) | **AVAILABLE**<br>Full horizon ($u=10\,\mu\text{m}$) | **AVAILABLE**<br>Full horizon ($u=10\,\mu\text{m}$) | $K_0=137.95\,\text{kN/mm}$, $F_{\max}=0.7581\,\text{kN}$ ($+0.05\%$), $W_{\text{trap}}=2.4101\,\text{mJ}$. Proves mechanical temporal stability. |
| **$T_2$ Nominal Time**<br>`PK_M1_T2_NOMINAL` | 15,192<br>CPE4 | $3.00$ | $0.400$ | Nominal $1\times$<br>(7,000 incs) | `1406021` | Exit 0<br>(0 cutbacks) | FOR: `C540B54A...`<br>`OUTPUT_ONLY_NONINVASIVE` | **AVAILABLE**<br>Full horizon ($u=10\,\mu\text{m}$) | **AVAILABLE**<br>Full horizon ($u=10\,\mu\text{m}$) | **AVAILABLE**<br>Full horizon ($u=10\,\mu\text{m}$) | $K_0=137.95\,\text{kN/mm}$, $F_{\max}=0.7578\,\text{kN}$, $W_{\text{trap}}=2.3593\,\text{mJ}$. Baseline temporal anchor. |
| **$T_3$ Fine Time**<br>`PK_M1_T3_FINE` | 15,192<br>CPE4 | $3.00$ | $0.400$ | Fine $0.5\times$<br>(14,000 incs) | `1406317` | Exit 0<br>(0 cutbacks) | FOR: `C540B54A...`<br>`OUTPUT_ONLY_NONINVASIVE` | **AVAILABLE**<br>Full horizon ($u=10\,\mu\text{m}$) | **AVAILABLE**<br>Full horizon ($u=10\,\mu\text{m}$) | **AVAILABLE**<br>Full horizon ($u=10\,\mu\text{m}$) | $K_0=137.95\,\text{kN/mm}$, $F_{\max}=0.7576\,\text{kN}$ ($-0.02\%$), $W_{\text{trap}}=2.3319\,\text{mJ}$. Completed all 10,022 Step-2 incs. |
| **$L_1$ Length-Scale**<br>`PK_M1_L0_0750` | 41,912<br>CPE4 | $1.50$ | $0.200$ | Nominal $1\times$<br>($l_0 = 7.5\,\mu\text{m}$) | `1406017` | Cutback at $u=7.84\,\mu\text{m}$ | FOR: `C540B54A...`<br>`OUTPUT_ONLY_NONINVASIVE` | **AVAILABLE**<br>Up to $u=7.84\,\mu\text{m}$ | **AVAILABLE**<br>Up to $u=6.20\,\mu\text{m}$ (Unit 105) | **AVAILABLE**<br>Up to $u=7.84\,\mu\text{m}$ | $K_0=137.86\,\text{kN/mm}$, $F_{\max}=0.7322\,\text{kN}$, $u_{\text{peak}}=5.633\,\mu\text{m}$. Standard physical baseline. |
| **$L_2$ Length-Scale**<br>`PK_M1_L0_1125` | 41,912<br>CPE4 | $1.50$ | $0.133$ | Nominal $1\times$<br>($l_0 = 11.25\,\mu\text{m}$) | `1406895` | Cutback at $u=7.80\,\mu\text{m}$ | FOR: `C540B54A...`<br>`OUTPUT_ONLY_NONINVASIVE` | **AVAILABLE**<br>Up to $u=7.80\,\mu\text{m}$ | **AVAILABLE**<br>Up to $u=6.20\,\mu\text{m}$ (Unit 105) | **AVAILABLE**<br>Up to $u=7.80\,\mu\text{m}$ | $K_0=137.77\,\text{kN/mm}$ ($-0.07\%$), $F_{\max}=0.7084\,\text{kN}$ ($-3.25\%$), $u_{\text{peak}}=5.590\,\mu\text{m}$. Length-scale sensitive. |
| **$L_3$ Length-Scale**<br>`PK_M1_L0_1500` | 41,912<br>CPE4 | $1.50$ | $0.100$ | Nominal $1\times$<br>($l_0 = 15.0\,\mu\text{m}$) | `1406896` | Cutback at $u=7.65\,\mu\text{m}$ | FOR: `C540B54A...`<br>`OUTPUT_ONLY_NONINVASIVE` | **AVAILABLE**<br>Up to $u=7.65\,\mu\text{m}$ | **AVAILABLE**<br>Up to $u=6.20\,\mu\text{m}$ (Unit 105) | **AVAILABLE**<br>Up to $u=7.65\,\mu\text{m}$ | $K_0=137.68\,\text{kN/mm}$ ($-0.13\%$), $F_{\max}=0.6895\,\text{kN}$ ($-5.83\%$), $u_{\text{peak}}=5.579\,\mu\text{m}$. Length-scale sensitive. |

---

## 5. Documentary Provenance Audit & Convergence Criteria Freezing

A systematic audit was conducted across repository commit logs and session reports to evaluate every claimed acceptance criterion against dated pre-result evidence:

### 5.1. Classification of Disqualified Numerical Bands (`POST_HOC_NOT_ADMISSIBLE_AS_PREDECLARED_CRITERIA`)

| Claimed Criterion | Claimed Band | Earliest Documentary Appearance | Historical Provenance & Root Cause | Formal Classification | Governed Action & Scientific Ruling |
| :--- | :---: | :---: | :--- | :---: | :--- |
| **Initial Stiffness $K_0$** | $\pm 0.50\%$ ($[137.25, 138.63]\,\text{kN/mm}$) | 2026-10-01 (Task F1125/F1126) | Canonical value $137.945520\,\text{kN/mm}$ was fitted from Job `1398090` ($u \le 0.0010\,\text{mm}, N=400$). The $\pm 0.50\%$ window was constructed retroactively today. | **`POST_HOC_NOT_ADMISSIBLE_AS_PREDECLARED_CRITERIA`** | **Disqualified as an a priori threshold.** Reclassified under **`TREND_ONLY`** as global structural compliance invariance: global elasticity is governed by far-field geometry and boundary conditions, requiring $K_0$ variation across local refinements to remain $< 0.10\%$. Report actual successive differences directly. |
| **Pre-Peak Bookkeeping Bound $\varepsilon_{\text{book}}$** | $< 0.12\%$ | 2026-08-10 (Session F43STATE) | Originally introduced as an energy conservation tolerance for Mode-II state transfer restarts. Adopted in Mode-I on 2026-10-01 after observing the 64-element mini-model error ($0.0988\%$). | **`POST_HOC_NOT_ADMISSIBLE_AS_PREDECLARED_CRITERIA`** | **Disqualified as an a priori threshold for spatial convergence.** Reclassified under **`TREND_ONLY`**: pre-peak energy identity $E_{\text{model}}(u) \equiv W_{\text{ext}}(u)$ is monitored continuously, reporting signed $\Delta_{\text{book}}(u)$ and relative error without artificial ceilings. |
| **$S_2$ Peak Force Interval** | $F_{\max} \in [0.735, 0.745]\,\text{kN}$ | 2026-10-01 (Task F1125) | Fabricated directly around historical run `1406016` ($S_2$, $F_{\max} = 0.7412\,\text{kN}$). | **`POST_HOC_NOT_ADMISSIBLE_AS_PREDECLARED_CRITERIA`** | **Revoked and completely removed.** Narrow numerical tolerance intervals constructed around previously computed outcomes violate scientific integrity. |
| **$S_3$ Peak Force Interval** | $F_{\max} \in [0.728, 0.738]\,\text{kN}$ | 2026-10-01 (Task F1125) | Fabricated directly around historical run `1406017` ($S_3$, $F_{\max} = 0.7322\,\text{kN}$). | **`POST_HOC_NOT_ADMISSIBLE_AS_PREDECLARED_CRITERIA`** | **Revoked and completely removed.** Narrow numerical tolerance intervals constructed around previously computed outcomes violate scientific integrity. |
| **$S_2$ Relative Drop Interval** | $\delta_2(F_{\max}) \in (1.5\%, 3.0\%)$ | 2026-10-01 (Task F1126) | Reconstructed directly from known historical drop ($2.19\%$). | **`POST_HOC_NOT_ADMISSIBLE_AS_PREDECLARED_CRITERIA`** | **Revoked and completely removed.** |
| **Fixed $E_{\text{frac}}$ Percentage Band** | $\pm 3.0\%$ of $S_1$ at $u=6.2\,\mu\text{m}$ | 2026-10-01 (Task F1125) | Reconstructed around known historical value ($2.375\,\text{mJ}$ vs $2.339\,\text{mJ}$, $1.56\%$). | **`POST_HOC_NOT_ADMISSIBLE_AS_PREDECLARED_CRITERIA`** | **Revoked and completely removed.** Replaced by outcome-independent successive-resolution convergence towards $G_c \cdot a$. |

### 5.2. Preserved Physical Expectation (`TREND_ONLY` / Domain Symmetry)
- **Crack Path Centerline Trajectory $y_{\text{crack}}$:** Mode-I symmetry on a homogeneous square domain requires planar horizontal crack propagation along $y = 0.500\,\text{mm}$ without unphysical branching or secondary cracks ($d < 0.20$ outside $|y - 0.5| > 0.05\,\text{mm}$). Classified as **`TREND_ONLY` / Domain Symmetry**.

### 5.3. Frozen Spatial Convergence Evaluation Formulation (`TREND_ONLY`)
Because exact closed-form analytical solutions for localized phase-field fracture on finite notched domains do not exist, spatial convergence across $S_1 \to S_2 \to S_3 \to S_4 \to S_5$ is evaluated using **outcome-independent successive-resolution comparison** across identical matched displacement evaluation points ($u \in \{0.0010, 0.0050, 0.005857, 0.0060, 0.0062, 0.0065, 0.0070, 0.0100\}\,\text{mm}$):

$$\text{For every canonical quantity } \phi \in \{F(u), K_0, F_{\max}, u_{\text{peak}}, E_{\text{elas}}(u), E_{\text{frac}}(u), W_{\text{ext}}(u), \Delta_{\text{book}}(u), d(x, y=0.5), y_{\text{crack}}\}:$$

$$\delta_n(\phi) \equiv \frac{|\phi^{(S_n)} - \phi^{(S_{n-1})}|}{\max(|\phi^{(S_{n-1})}|, 10^{-12})}$$

The successive normalized differences $\delta_n(\phi)$ are reported directly as quantitative measures of resolution sensitivity without imposing newly invented pass/fail bands:
1. **Initial Structural Stiffness Invariance:** Monitored via $\delta_n(K_0)$ to verify that local crack-corridor refinement does not alter global elastic specimen compliance ($< 0.10\%$).
2. **Monotonic Peak Force Reduction:** Monitored via $F_{\max}^{(S_1)} > F_{\max}^{(S_2)} > F_{\max}^{(S_3)} > \dots$ as resolving the steep crack-tip strain gradient relieves artificial mesh-pinning.
3. **Successive Error Decay:** Monitored via $\delta_{n}(F_{\max}) < \delta_{n-1}(F_{\max})$, confirming asymptotic approach to the continuum spatial limit.
4. **Peak Displacement Advance:** Monitored via $u(F_{\max})^{(S_n)} \le u(F_{\max})^{(S_{n-1})}$.
5. **Regularized Surface Energy Evolution:** Monitored via successive difference $\delta_n(E_{\text{frac}})$ at matched post-peak displacement points.
6. **Planar Symmetry Trajectory:** Monitored via crack path centerline deviation $|y_{\text{crack}} - 0.500\,\text{mm}|$ and diffuse half-width.

---

## 6. Candidate Package Verification & Abaqus Datacheck Evidence

Both candidate packages ($S_2$ and $S_3$) were transferred to the cluster, cryptographically verified, and subjected to complete **Abaqus 2023 / Intel Fortran 2021.13.0 Datachecks** on the cluster compute environment:

### Package A: Spatial Candidate $S_2$ (32,130 Finite Elements)
* **Directory:** `models/pandey_kumar_mode1/12_fixed_convergence_h0020/`
* **Input Deck:** `PK_MODE1_FIX_H0020_ENERGY.inp` (SHA-256: `9A5C3BD7EA9AF8CD38715FAC9FB062B1590766B7A7CF3A800D2F8C9E95C3767F`, 4,256,089 bytes)
* **User Subroutine:** `f42_mixed_uel.for` (SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`, 29,722 bytes)
* **PBS Scripts:**
  - `submit_solver.pbs` (Job Name: `PK_M1_S2_ENERGY`, 1-CPU serial, 32GB, 48h, normal queue, dual notification traps, SHA-256: `1B42064AC207B034FE06CC2C40D6BDC116AE66FE2028EFCD42E1CB3C7FBD9B5B`)
  - `submit_datacheck.pbs` (Job Name: `PK_M1_S2_DC`, 1-CPU serial, 16GB, 1h, entry queue, SHA-256: `AF505FA5AC5C04E094837A35CD6ADA76ADEEFD5BD5FAB180A89FBCB5D0DC6366`)
* **Cluster Datacheck Execution Evidence (`task-939`):**
  - Compiler: Intel Fortran Classic `2021.13.0 Build 20240602_000000` (subroutines `uel_` and `umat_` targeted for automatic CPU dispatch).
  - Linker: GNU ld `2.30-128.el8_10` (clean link, 0 unresolved symbols).
  - Abaqus Preprocessor: `End Analysis Input File Processor` (0 card length violations, 32,130 elements, 32,613 nodes).
  - Standard Datacheck: `Abaqus JOB PK_M1_S2_DC COMPLETED`, **Exit Code: 0**.
* **Governance Status:** **`DATACHECK_PASSED_READY_AFTER_CORRECTED_S1_ENERGY_QUALIFICATION` (ZERO SUBMISSIONS PRIOR TO S1 QUALIFICATION)**.

### Package B: Spatial Candidate $S_3$ (41,912 Finite Elements)
* **Directory:** `models/pandey_kumar_mode1/13_fixed_convergence_h0015/`
* **Input Deck:** `PK_MODE1_FIX_H0015_ENERGY.inp` (SHA-256: `1500ECA5028660045789AF04AD3112E26CA76BBF7BFAC6437A42008A4307408F`, 5,621,225 bytes)
* **User Subroutine:** `f42_mixed_uel.for` (SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`, 29,722 bytes)
* **PBS Scripts:**
  - `submit_solver.pbs` (Job Name: `PK_M1_S3_ENERGY`, 1-CPU serial, 32GB, 48h, normal queue, dual notification traps, SHA-256: `98DD9AC943F4A4A6A99F7F29BCB41BEABE360F1B9D1D299D8688AD3ACAD6FF63`)
  - `submit_datacheck.pbs` (Job Name: `PK_M1_S3_DC`, 1-CPU serial, 16GB, 1h, entry queue, SHA-256: `75AF7059759348A76A25D21A4261C4A213EF3FA88A4D7EF17BF008B39B36D5AC`)
* **Cluster Datacheck Execution Evidence (`task-945`):**
  - Compiler: Intel Fortran Classic `2021.13.0 Build 20240602_000000` (subroutines `uel_` and `umat_` targeted for automatic CPU dispatch).
  - Linker: GNU ld `2.30-128.el8_10` (clean link, 0 unresolved symbols).
  - Abaqus Preprocessor: `End Analysis Input File Processor` (0 card length violations, 41,912 elements, 42,364 nodes).
  - Standard Datacheck: `Abaqus JOB PK_M1_S3_DC COMPLETED`, **Exit Code: 0**.
* **Governance Status:** **`DATACHECK_PASSED_READY_AFTER_CORRECTED_S1_ENERGY_QUALIFICATION` (ZERO SUBMISSIONS PRIOR TO S1 QUALIFICATION)**.

---

## 7. Execution Protocol & Explicit List of Necessary Solver Jobs

### 1. Actively Solving on Cluster (1 Job):
- **Job `1409734.mmaster02` (`PK_M1_REF15K_ENERGY`)**: 15,192 finite elements, 1-CPU serial, normal queue (`mnode097/0`).
- **Telemetry Snapshot:**
  * State: `R` (Running) on `mnode097/0` in queue `normal_imfdfkmq`.
  * Time Use: `01:36:24` (CPU time at guarded snapshot 2026-10-02 09:31:41 CEST).
  * Input Deck: `PK_MODE1_REF15K_ENERGY.inp` (SHA-256 `EC560A4C...`) with `*User Material, constants=3` specifying $N_{\text{phys}}=15192.0$.
  * User Subroutine: `f42_mixed_uel.for` (SHA-256 `CE8D5EDC...`) with `CALL GETOUTDIR` generating working-dir `uel_energy_balance.csv`.
  * Live CSV and ODB updating actively.
- **Protocol:** Preserved completely undisturbed on compute node with strict non-polling invariant enforced.

### 2. Truly Necessary Future Solver Runs (Strictly 2 Candidate Jobs):
- **Candidate $S_2$ (`PK_M1_S2_ENERGY`)**: 32,130 finite elements ($h = 2.0\,\mu\text{m}$, $h/l_0 = 0.267$).
  * Scientific Justification: Historical run `1406016` lacked companion ODB energy fields (`SDV17-20`) and experienced solver cutback at $u = 6.82\,\mu\text{m}$. Datacheck passed (Exit 0, `task-939`).
- **Candidate $S_3$ (`PK_M1_S3_ENERGY`)**: 41,912 finite elements ($h = 1.5\,\mu\text{m}$, $h/l_0 = 0.200$).
  * Scientific Justification: Historical run `1406017` lacked companion ODB energy fields (`SDV17-20`) and cut back at $u = 7.84\,\mu\text{m}$. Datacheck passed (Exit 0, `task-945`).

### 3. Audited Conditional Submission Release Gate (`handle_job_1409705_terminal_qualification.py`):
Submission of $S_2$ and $S_3$ is governed by the audited one-shot terminal handler ([`scripts/validation/handle_job_1409705_terminal_qualification.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/scripts/validation/handle_job_1409705_terminal_qualification.py)), which is fully qualified across 25 unit test scenarios and 9 dryrun scenarios (**`TERMINAL_RELEASE_HANDLER_QUALIFIED`**, 25/25 unit tests passed in `tests/unit/test_handle_job_1409705_terminal_qualification.py`; full Mode-I regression 77/77 passed across 7 suites).

**A. Mandatory S1 Pre-Release Prerequisites (All 12 Boolean Implementation Checks):**
1. **Scheduler State:** Terminal (`terminal_scheduler_state`: completed and cleared from queue). Non-polling guard exits 0 (`STILL_RUNNING_NOOP`) while active.
2. **Abaqus Exit Code:** Clean solver exit (`solver_exit_0`: Exit 0 confirmed in `.log` and `.sta`).
3. **Displacement Horizon:** Prescribed loading endpoint reached (`final_target_displacement_reached`: consistency verified from completed two-step loading schedule and displacement-BC mapping to $u = 0.010000\,\text{mm}$, reporting extracted $u_{\text{final}}$ and numerical difference from $0.010000\,\text{mm}$ without an invented pass/fail numerical tolerance band).
4. **Step/Increment Horizon:** Two-step schedule completed (`expected_step_completed`: Step 1 = 2,000 incs / $t=1.0\,\text{s}$, Step 2 = 5,000 incs / $t=1.0\,\text{s}$, Total = 7,000 incs, rejecting incorrect 7,000-inc Step-2 assumptions).
5. **Diagnostic Integrity:** Scan of `.msg` confirms zero fatal defects (`no_fatal_solver_diagnostics`: zero fatal errors, zero zero-pivots, zero numerical singularities, zero cutback exhaustion; nonfatal softening negative-eigenvalue warnings recorded as transparent physical diagnostics without categorical blocking).
6. **Mechanically Valid $F-u$ History:** Complete, finite, monotonic $F-u$ trajectory (`mechanically_valid_f_u`: $K_0 > 0$, $F_{\max} > 0$, $u_{\text{peak}} \in (0, u_{\text{final}})$, and post-peak softening $F_{\text{final}} < F_{\max}$, zero NaNs/Infs).
7. **Mechanical Parity Extraction:** Extraction and signed difference reporting (`mechanical_parity_extraction`: $K_0, F_{\max}, u_{\text{peak}}, F_{\text{final}}, W_{\text{ext}}$ differences reported vs canonical reference without newly invented hard percentage gates).
8. **Companion Energy Output:** Full presence of `SDV17-20` state variables (`presence_of_sdv17_20` on companion Layer 3 `All_elem`).
9. **Single-Value Deduplication:** Unique element reduction (`single_value_deduplication`: 15,192 elements) preventing $4\times$ CPE4 overcounting.
10. **Units & Sign Conventions:** Formulation-specific energy units (`units_and_sign_conventions`: $1\,\text{kN}\cdot\text{mm} = 1\,\text{J} = 1000\,\text{mJ}$), non-negative strain/fracture integrands ($E_{\text{elas}} \ge 0, E_{\text{frac}} \ge 0$), and normalized external work handling ($W_{\text{ext}} = |W_{\text{raw}}|$).
11. **Cross-Channel Parity:** Frame matching and element reduction reconciliation (`cross_channel_reconciliation`: exact-frame ODB vs Unit 105 `uel_energy_balance.csv` agreement).
12. **Extractor Provenance:** Valid extractor execution and structure (`no_extractor_provenance_defect`).

**B. Bookkeeping Error Governance (No Hard Ceiling):**
- In accordance with the documentary criteria audit, numerical bookkeeping thresholds (such as $\varepsilon_{\text{book}} < 1.0\%$) were not predeclared and are **strictly disqualified as pass/fail gates**.
- The handler calculates and reports the trajectory residual ($\Delta_{\text{book}}$, $\text{RelDiff}_{\text{signed}}$, $\varepsilon_{\text{book}}$) for scientific transparency without blocking release on a post-hoc value.

**C. Idempotency & Duplicate Submission Safety:**
- Checks `HPC_JOB_LEDGER.csv`, live `qstat`, and persistent record (`GATE6B_S2_S3_RELEASE_RECORD.json`) before any `qsub`.
- If both $S_2$ and $S_3$ are already submitted: exits cleanly with `ALREADY_RELEASED_NOOP`.
- If $S_2$ was submitted and $S_3$ was not: submits ONLY $S_3$ (never resubmits $S_2$).
- If $S_3$ was submitted and $S_2$ was not: submits ONLY $S_2$ (never resubmits $S_3$).
- Immediately records exact PBS Job ID after each successful submission.
- If $S_2$ succeeds and $S_3$ fails: preserves $S_2$ ID and classifies as `PARTIAL_SUBMISSION_REQUIRES_RECONCILIATION` without automatic retry.

**D. Dual-Channel Notification Integration:**
- Submissions dispatch dual-channel notifications (email via `#PBS -m abe` and Telegram via `notify_submitted`).
- Notification errors are caught and logged without obscuring or invalidating the captured PBS Job ID.
- Execution mode: strictly 1-CPU serial using `f42_mixed_uel.for` (single-rank shared-memory threading).

---

## 8. Epistemological Classifications & Project Bounds

1. **`CONVERGED / STABLE` Quantities:**
   - Initial elastic stiffness $K_0$: Variation $< 0.09\%$ across spatial meshes, $< 0.001\%$ across time steps, $0.13\%$ across length scales.
   - Crack propagation direction: Strictly planar horizontal advance along symmetry line $y = 0.50\,\text{mm}$ across all valid models.
2. **`MESH-SENSITIVE` Quantities:**
   - Peak tensile load $F_{\max}$: Decreases monotonically by $4.26\%$ from $0.7578 \to 0.7255\,\text{kN}$ across $h/l_0 \in [0.133, 0.400]$.
   - Peak displacement $u(F_{\max})$: Advances monotonically by $4.81\%$ ($5.857 \to 5.575\,\mu\text{m}$).
   - Fracture localization band width: Diffuse half-width remains resolution-limited ($\sim 10\text{--}15\,\mu\text{m}$).
3. **`LENGTH-SCALE SENSITIVE` Quantities:**
   - Peak tensile load $F_{\max}$: Decreases by $5.83\%$ across $l_0 \in [7.5, 15.0]\,\mu\text{m}$ at fixed mesh resolution ($h = 1.5\,\mu\text{m}$).
4. **`ROOT_CAUSE_CANDIDATE_NOT_YET_RECONCILED`:**
   - Terminal breakthrough nonconvergence in Step-2 adaptive mesh: Numerical interaction between steep physical softening and $dt_{\min} = 10^{-8}\,\text{s}$ during final ligament separation ($x > 0.94\,\text{mm}$). Zero replacement runs authorized.
5. **`GLOBAL_ENERGY_IDENTITY — NOT_YET_CLOSED`:**
   - Post-peak work-energy bookkeeping residual represents an observational balance quantity rather than a proven conservation identity.

---

## 9. Gate-6B Lightweight Reproduction Package Architecture & Deliverables

In compliance with supervisor directives requiring lightweight, reproducible `.inp`, `.for`, `.py`, and `commands.txt` deliverables rather than multi-gigabyte binary `.odb` transfers, the authoritative Gate-6B reproduction package is established at:
`models/pandey_kumar_mode1/reproduction_package_gate6b_energy/`

### A. Architectural Properties:
1. **Three-Layer Co-Located Architecture & Companion Index Mapping ($\text{PHYSIDX}$):**
   - Layer 1: Phase-field mixed UEL elements ($\text{NOEL} \in [1, N_{\text{phys}}]$).
   - Layer 2: Mechanical continuum elements ($\text{NOEL} \in [N_{\text{phys}}+1, 2N_{\text{phys}}]$).
   - Layer 3: Companion visualizer elements ($\text{NOEL} \in [2N_{\text{phys}}+1, 3N_{\text{phys}}]$) with low visualizer stiffness $E_{\text{comp}} = 10^{-11}\,\text{GPa}$.
   - Companion physical index evaluated via:
     $$\text{PHYSIDX} = \text{NOEL} - 2 N_{\text{phys}}$$
     mapping companion labels $2N_{\text{phys}}+1, \dots, 3N_{\text{phys}}$ to physical finite-element indices $1, \dots, N_{\text{phys}}$.
   - Input decks define mesh-specific $N_{\text{phys}}$ under `*User Material, constants=3`:
     - $S_1$ Reference (15,192 elements): $E=210.0, \nu=0.3, N_{\text{phys}}=15192.0$.
     - $S_2$ Candidate (32,130 elements): $E=210.0, \nu=0.3, N_{\text{phys}}=32130.0$.
     - $S_3$ Candidate (41,912 elements): $E=210.0, \nu=0.3, N_{\text{phys}}=41912.0$.
2. **Layer-3 Companion State Variable Assignments (`SDV17-20`):**
   - Companion visualization elements output internal energy quantities mapped directly in `SUBROUTINE UMAT`:
     - `SDV17`: Element-integrated phase-field / fracture surface energy $E_{\text{frac}}$ (`SV_E_FRAC(PHYSIDX)`, units: $\text{kN}\cdot\text{mm} \equiv \text{J} = 1000\,\text{mJ}$).
     - `SDV18`: Element-integrated elastic strain energy $E_{\text{elas}}$ (`SV_E_ELAS(PHYSIDX)`, units: $\text{kN}\cdot\text{mm} \equiv \text{J} = 1000\,\text{mJ}$).
     - `SDV19`: Local volumetric fracture-surface energy density $\psi_f$ (`SV_PSI_F(PHYSIDX)`, units: $\text{kN/mm}^2 \equiv \text{GPa} = 1000\,\text{MPa} \equiv \text{J/mm}^3 = 10^3\,\text{mJ/mm}^3$; point field variable, never directly summed).
     - `SDV20`: Local volumetric elastic strain energy density $\psi_e$ (`SV_PSI_E(PHYSIDX)`, units: $\text{kN/mm}^2 \equiv \text{GPa} = 1000\,\text{MPa} \equiv \text{J/mm}^3 = 10^3\,\text{mJ/mm}^3$; point field variable, never directly summed).
   - Single-IP extraction (`IP1` only) or centroid deduplication prevents $4\times$ overcounting of 4-point Gauss integration data.
3. **Three-Way Dimensional & Provenance Framework for 2D Out-of-Plane Thickness ($t = 1.0\,\text{mm}$):**
   - **Literature Formulation (Pandey & Kumar, 2025, Section 4.1)**: Section 4.1 (pages 3264–3265) formulates the Mode-I benchmark strictly as a 2D problem without prescribing an out-of-plane thickness $t$ (unlike Section 4.4 which explicitly specifies $t = 100\,\text{mm}$ for the L-panel). Statements attributing $t = 1.0\,\text{mm}$ to literature prescription are strictly rejected as unsupported by the primary source.
   - **Tier 1 (Native 2D UEL Assembly)**: In `f42_mixed_uel.for`, all quadratures evaluate pure 2D area integrals $\int_A \cdot \, dA$ with area differential $\text{CJAC} = \det(J) \cdot \text{WT} \sim \text{mm}^2$. The internal mechanical residual is force per unit thickness: $F_{\text{int}} = \int_A B^T \sigma \, dA \sim \text{mm}^2 \cdot (1/\text{mm}) \cdot (\text{kN/mm}^2) = \text{kN/mm}$. Tangent stiffness is stiffness per unit thickness: $K = \int_A B^T D B \, dA \sim \text{kN/mm}^2$. Energy quadrature is energy per unit thickness: $E = \int_A \psi \, dA \sim \text{mm}^2 \cdot (\text{kN/mm}^2) = \text{kN} \equiv \text{J/mm}$. Both integrals share identical area quadrature without explicit thickness factors in Fortran, proving 100% internal mutual dimensional parity at Tier 1 ($[F_{\text{int}}] \equiv [E_{\text{elem}}] \equiv [M L^1 T^{-2}]$).
   - **Tier 2 (Project Implementation Normalization Convention $t_{\text{ref}} = 1.0\,\text{mm}$)**: Adopting the standard benchmark out-of-plane slice thickness $t_{\text{ref}} = 1.0\,\text{mm}$ restores resultant physical tensile force $F = F_{\text{int}} \cdot 1.0\,\text{mm} \sim \text{kN}$ and total scalar energy $E_{\text{model}} = E \cdot 1.0\,\text{mm} \sim \text{kN}\cdot\text{mm} \equiv \text{J} = 1000\,\text{mJ}$, directly matching external work $W_{\text{ext}} = \int F \, du$ ($\text{kN}\cdot\text{mm} \equiv \text{J}$).
   - **Epistemological Status of Companion `*Solid Section ... 1.0`**: The companion card `*Solid Section, elset=All_elem, material=DUMMY_MAT` with explicit `1.0` thickness represents project-level secondary corroborating evidence that the visualization layer adopts the same 1-mm slice convention; it is strictly rejected as proof of a literature thickness prescription or UEL dimensionality.
   - **Historical Reference Anchor Contextualized**: Initial stiffness $K_0 = 137.945520\,\text{kN/mm}$ is structural stiffness for the 1-mm slice (or $137.945520\,\text{kN/mm}^2$ per unit thickness), and peak force $F_{\max} = 0.757778\,\text{kN}$ is resultant peak force for the 1-mm slice (or $0.757778\,\text{kN/mm}$ per unit thickness).
4. **Persistent Working Directory CSV Output (`GETOUTDIR`):**
   - `SUBROUTINE UEXTERNALDB` constructs the exact working directory path via standard Abaqus utility `CALL GETOUTDIR(OUTDIR_STR, L_OUTDIR)` and generates `uel_energy_balance.csv` without file loss.
5. **100.000% Mathematical Invariance:**
   - Line-by-line diff audits confirm 0 changes to `RHS`, `AMATRX`, elasticity tensors, phase-field degradation $g(d)$, history update $\mathcal{H}$, and energy definitions between `CE8D5EDC...` and baseline `5CD0D2C0...`.

### B. Reproduction Package Manifest (SHA-256 Checksums):

| File Name | Description | Size (Bytes) | SHA-256 Checksum |
| :--- | :--- | :---: | :--- |
| `PK_MODE1_REF15K_ENERGY.inp` | Candidate $S_1$ 15,192-element energy reference deck ($N_{\text{phys}}=15192.0$) | 1,941,184 | `EC560A4C265730647B43DAB125D166EBC57CAC285D574D38222A498A967535D9` |
| `PK_MODE1_FIX_H0020_ENERGY.inp` | Candidate $S_2$ 32,130-element energy input deck ($N_{\text{phys}}=32130.0$) | 4,256,089 | `9A5C3BD7EA9AF8CD38715FAC9FB062B1590766B7A7CF3A800D2F8C9E95C3767F` |
| `PK_MODE1_FIX_H0015_ENERGY.inp` | Candidate $S_3$ 41,912-element energy input deck ($N_{\text{phys}}=41912.0$) | 5,621,225 | `1500ECA5028660045789AF04AD3112E26CA76BBF7BFAC6437A42008A4307408F` |
| `f42_mixed_uel.for` | Single Gate-6B production Fortran source with `CALL GETOUTDIR` | 29,722 | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` |
| `extract_authoritative_mode1_energy_complete.py` | Complete Mode-I energy extraction pipeline with flexible `--job-id` | 14,703 | `9270C0F2DC77F84799E2B6435E2D5BCB4FF693204A08EF76BD815D6414332E8A` |
| `handle_job_1409705_terminal_qualification.py` | 12-rule evidence-based qualification handler (Job 1409734 target) | 67,929 | `6F5FF44E218FEAF6F200827AF6E48C27AB77980E3CFD99C558521C45091326F7` |
| `spatial_convergence_pipeline.py` | Multi-quantity spatial convergence postprocessing pipeline | 17,318 | `CC413266FF7E97523756918C1933CF4F945E75CB7CABA082A2DDAF4CD0A18E2D` |
| `submit_s1_ref15k_energy.pbs` | PBS execution script for Candidate $S_1$ (1-CPU serial, `entry_imfdfkmq`) | 1,202 | `C26427E54FC1D91D53BE7C98FFBA0DCCDD2A241EC3C047860050C0A4DB676E1C` |
| `submit_s2_h0020_energy.pbs` | PBS execution script for Candidate $S_2$ (1-CPU serial, `entry_imfdfkmq`) | 1,173 | `207623D697D7F469BD27E7F75867B4C74CF27793A76F2B2DADE96801A366702E` |
| `submit_s3_h0015_energy.pbs` | PBS execution script for Candidate $S_3$ (1-CPU serial, `entry_imfdfkmq`) | 1,173 | `3595AAB6DF979B1AFEFB79A5217A81C3B1937A51877D65AEF0280C593CFD6CC6` |
| `commands.txt` | Complete step-by-step verified cluster commands | 5,594 | `60A7CD83CD46BE4181BBC3233A653A9F7ABA0A1ECDB8207ACAE8659C5B08E975` |
| `README.md` | Comprehensive architectural documentation & user guide | 16,020 | `CB0E9F05FF861720EA12894634DAFFD887A711355A4E53199803DD0285DB835E` |
| `verify_reproduction_package.py` | Automated self-checking verification script (18/18 checks pass, Exit 0) | 11,281 | `34353B977FE8FA212EE75077381DD4AA7AAB4A5EBB1FB03D485A2D839077FDAD` |
| `MODE1_ENERGY_EQUATION_CODE_OUTPUT_MAP.md` | Authoritative Equation-to-Code-to-Output Map & Bookkeeping Specification | 30,340 | `F1CF6571AC3E21974491B13A99E0D7B402C6E6D92A2A452D2885926A9E3B6522` |

### C. Self-Checking Verification Result:
Executing `python3 verify_reproduction_package.py` in the package root verifies all 18 checks with **100.0% Exit 0 Pass**:
- Check 1: 4/4 Core SHA-256 hashes verified bit-for-bit.
- Check 2: Fortran subroutines UEL, UMAT, UEXTERNALDB, exact mapping `PHYSIDX = NOEL - 2*NPHYS`, and `CALL GETOUTDIR` verified.
- Check 3: 3/3 input decks verified for `*User Material, constants=3` ($N_{\text{phys}}$), `*Depvar 20`, and companion `SDV17-20` output.
- Check 4: 9/9 supporting scripts, execution wrappers, and documentation (including `MODE1_ENERGY_EQUATION_CODE_OUTPUT_MAP.md`) verified present.
- Check 5: Dimensional units and Three-Way thickness provenance consistency verified across literature formulation (Pandey & Kumar 2025 Sec. 4.1 2D formulation with no thickness prescription), Tier 1 Fortran source (`CJAC` area quadrature with 0 thickness factors), Tier 2 project convention ($t_{\text{ref}}=1.0\,\text{mm}$ restoring $\text{kN}$ and $\text{J}$), decks (`*Solid Section ... 1.0` secondary corroboration), map, unit tests, and qualification handler.

---


---

## 9. Gate-6B Temporal Discretization Convergence Candidates ($T_1, T_2, T_3$)

In accordance with Task `F1147`, the temporal-convergence candidates have been formally structured into standalone, auditable model packages, instrumented with the qualified Gate-6B energy output architecture, synchronized with the cluster, and verified via Abaqus 2023 / Intel Fortran 2021.13.0 Datacheck preflight with **100% Exit Code 0**:

### A. Candidate Temporal Packages & Specifications:
1. **$T_1$ Coarse Time ($2\times$ nominal $dt$)**:
   - Package: `models/pandey_kumar_mode1/17_temporal_convergence_t1_coarse/`
   - Input Deck: `PK_MODE1_T1_COARSE_ENERGY.inp` (SHA-256: `33183ADA17DA6712F93DA5648D1D4C9B41C27398DA472EE6619E0839E96ACCFF`)
   - Step 1: $dt = 1.0\times 10^{-3}\,\text{s}$ (1,000 incs), Step 2: $dt = 4.0\times 10^{-4}\,\text{s}$ (2,500 incs), Total: **3,500 increments**.
   - Datacheck Result: **Abaqus JOB PK_MODE1_T1_COARSE_ENERGY COMPLETED, Exit Code 0** (0 preprocessor errors).
   - Status: `DATACHECK_PASSED_READY_AFTER_CORRECTED_S1_ENERGY_QUALIFICATION` (Strictly Unsubmitted, `authorized: false`).
2. **$T_2$ Nominal Time ($1\times$ nominal $dt$, matching $S_1$)**:
   - Package: `models/pandey_kumar_mode1/18_temporal_convergence_t2_nominal/`
   - Input Deck: `PK_MODE1_T2_NOMINAL_ENERGY.inp` (SHA-256: `4A0302C60FB47D59FF024BCD40EBADC4B2F036FE155F1C632F6D8874665CD6F1`)
   - Step 1: $dt = 5.0\times 10^{-4}\,\text{s}$ (2,000 incs), Step 2: $dt = 2.0\times 10^{-4}\,\text{s}$ (5,000 incs), Total: **7,000 increments**.
   - Datacheck Result: **Abaqus JOB PK_MODE1_T2_NOMINAL_ENERGY COMPLETED, Exit Code 0** (0 preprocessor errors).
   - Status: `DATACHECK_PASSED_READY_AFTER_CORRECTED_S1_ENERGY_QUALIFICATION` (Strictly Unsubmitted, `authorized: false`).
3. **$T_3$ Fine Time ($0.5\times$ nominal $dt$)**:
   - Package: `models/pandey_kumar_mode1/19_temporal_convergence_t3_fine/`
   - Input Deck: `PK_MODE1_T3_FINE_ENERGY.inp` (SHA-256: `72D6CC5176326BFAB60FB9B23AFBE4AD6882A0ABC030465BAF10A5DC2A19519C`)
   - Step 1: $dt = 2.5\times 10^{-4}\,\text{s}$ (4,000 incs), Step 2: $dt = 1.0\times 10^{-4}\,\text{s}$ (10,000 incs), Total: **14,000 increments**.
   - Datacheck Result: **Abaqus JOB PK_MODE1_T3_FINE_ENERGY COMPLETED, Exit Code 0** (0 preprocessor errors).
   - Status: `DATACHECK_PASSED_READY_AFTER_CORRECTED_S1_ENERGY_QUALIFICATION` (Strictly Unsubmitted, `authorized: false`).

### B. Common Frozen Architecture Across $T_1, T_2, T_3$:
- **Mesh Topology**: Identical 15,192 physical elements (15,192 phase UEL, 15,192 displacement UEL, 15,192 companion CPE4), 15,521 nodes, $h = 0.0030\,\text{mm}$.
- **Fortran Subroutine**: Production `f42_mixed_uel.for` (SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`).
- **Material Constants**: $E = 210.0\,\text{kN/mm}^2$, $\nu = 0.3$, $N_{\text{phys}} = 15192.0$ in `*User Material, constants=3`.
- **Phase-Field Constants**: $G_c = 0.0027\,\text{kN/mm}$, $l_0 = 0.0075\,\text{mm}$, $k = 1.0\times 10^{-7}$.
- **Boundary Conditions & Coupling**: $u_y=0$ on `N_BOTTOM`, $u_x=0$ on `N_PIN`, $u_x=0$ on `N_TOP`, top edge rigid tie to RP (Node 999999), $u_{\text{final}} = 0.0100\,\text{mm}$.
- **Energy Instrumentation**: `*Depvar 20`, `*Element Output, elset=All_elem` (`SDV17-20`), `uel_energy_balance.csv` written via `CALL GETOUTDIR`.
- **Evaluation Pipeline**: `scripts/validation/temporal_convergence_pipeline.py` enforcing strict matched-displacement interpolation with ZERO extrapolation.

## 10. Equation-to-Code-to-Output Map Specification

The definitive mathematical formulations, state-variable storage assignments, ODB/CSV data channels, unit systems, and reduction rules are codified in [`MODE1_ENERGY_EQUATION_CODE_OUTPUT_MAP.md`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/supervisor_reports/08-10-2026/MA_ModeI_Supervisor_Meeting_Pack_2026-10-08/MODE1_ENERGY_EQUATION_CODE_OUTPUT_MAP.md).

### Summary Table of Canonical Energetic Quantities:

| Quantity | Mathematical Definition | Subroutine & Line | Companion SDV | Global CSV Column | Physical Dimension | Reduction / Deduplication Rule |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **Fracture Surface Energy** ($E_{\text{frac}}$) | $\int_\Omega G_c \left[ \frac{d^2}{2l_0} + \frac{l_0}{2}\|\nabla d\|^2 \right] d\Omega$ | `f42_mixed_uel.for`<br>Lines 357–373, 645–659 | `SDV17` | `E_fracture_kNmm` | Native Tier 1: $\text{J/mm} \equiv \text{kN}$<br>Benchmark Slice: $\text{kN}\cdot\text{mm} \equiv \text{J} = 10^3\,\text{mJ}$ | Single-IP1 or unique element deduplication ($\sum_{e=1}^{N_{\text{phys}}} E_{\text{frac}, e}$) |
| **Elastic Strain Energy** ($E_{\text{elas}}$) | $\int_\Omega \frac{1}{2} g(d) \boldsymbol{\varepsilon} : \mathbf{C} : \boldsymbol{\varepsilon} \, d\Omega$ | `f42_mixed_uel.for`<br>Lines 534–549, 806–816 | `SDV18` | `E_elastic_kNmm` | Native Tier 1: $\text{J/mm} \equiv \text{kN}$<br>Benchmark Slice: $\text{kN}\cdot\text{mm} \equiv \text{J} = 10^3\,\text{mJ}$ | Single-IP1 or unique element deduplication ($\sum_{e=1}^{N_{\text{phys}}} E_{\text{elas}, e}$) |
| **Fracture Energy Density** ($\psi_f$) | $G_c \left[ \frac{d^2}{2l_0} + \frac{l_0}{2}\|\nabla d\|^2 \right]$ | `f42_mixed_uel.for`<br>Lines 375, 661 | `SDV19` | *(Not in global CSV)* | $\text{kN/mm}^2 \equiv \text{GPa} = 1000\,\text{MPa} \equiv \text{J/mm}^3 = 10^3\,\text{mJ/mm}^3$ | Pointwise field variable; **NEVER SUM DIRECTLY** |
| **Elastic Energy Density** ($\psi_e$) | $\frac{1}{2} g(d) \boldsymbol{\varepsilon} : \mathbf{C} : \boldsymbol{\varepsilon}$ | `f42_mixed_uel.for`<br>Lines 551, 818 | `SDV20` | *(Not in global CSV)* | $\text{kN/mm}^2 \equiv \text{GPa} = 1000\,\text{MPa} \equiv \text{J/mm}^3 = 10^3\,\text{mJ/mm}^3$ | Pointwise field variable; **NEVER SUM DIRECTLY** |
| **Total Internal Energy** ($E_{\text{model}}$) | $E_{\text{elas}} + E_{\text{frac}}$ | `UEXTERNALDB`<br>Line 137 | Derived: `17+18` | `E_total_kNmm` | Native Tier 1: $\text{J/mm} \equiv \text{kN}$<br>Benchmark Slice: $\text{kN}\cdot\text{mm} \equiv \text{J} = 10^3\,\text{mJ}$ | Global sum over $1 \dots N_{\text{phys}}$ |
| **External Work** ($W_{\text{ext}}$) | $\int_0^u -\text{RF2}_{\text{RP}} \, du$ | Extractor script<br>Lines 124–130 | History at RP | Derived in postproc | $\text{kN}\cdot\text{mm} \equiv \text{J} = 10^3\,\text{mJ}$ | Composite trapezoidal integration over time history |
| **Bookkeeping Residual** ($\Delta_{\text{book}}$) | $E_{\text{model}} - W_{\text{ext}}$ | Extractor script<br>Line 167 | Diagnostic | Diagnostic in postproc | $\text{kN}\cdot\text{mm} \equiv \text{J} = 10^3\,\text{mJ}$ | Point-by-point trajectory subtraction |

### Offline Unit Regression Status:
- Unit test suite [`tests/unit/test_mode1_energy_equation_code_map.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_mode1_energy_equation_code_map.py): **19 / 19 passed in 0.27s (100% Exit 0)** (incorporating `test_rejects_unsupported_claim_that_pandey_kumar_prescribes_thickness`).
- Terminal handler test suite [`tests/unit/test_handle_job_1409705_terminal_qualification.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_handle_job_1409705_terminal_qualification.py): **25 / 25 passed in 1.80s (100% Exit 0)**.
- Full Mode-I regression suite: **77 / 77 passed in 2.25s (100% Exit 0)** across all 7 test files.
- Reproduction package self-check: **18 / 18 checks passed (100% Exit 0)**.
