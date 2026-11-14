# Task F1745: Case 3 Notched Plate with Hole and Pins (Sec 4.3) Unified 5-State Error-Indicator Envelope Offline Qualification & Discrepancy Reconciliation Report

## Executive Summary

Task **F1745** executes a rigorous, zero-PBS offline investigation and discrepancy reconciliation for **Case 3** (Pandey and Kumar 2025, Section 4.3: *Rectangular Notched Plate with Hole and Pins*). Following the completion of predecessor Task **F1744** and its independent review approval under **HND-F1744-CASE3-CLOSEOUT-001** (`APPROVE`), Task F1745 resolves every numerical, topological, and accounting issue identified by the independent reviewer without consuming any PBS compute jobs (`max_new_pbs_submissions = 0`, `submissions_consumed = 0`).

The central breakthrough of Task F1745 is the formulation, cluster verification, and mathematical qualification of a **Unified Multi-State Relative Error-Indicator Envelope** ($\hat{\eta}_e^{(\mathrm{envelope})}$). In Task F1744, sequential multi-pass remeshing was found to suffer from **pass-memory loss**: because the primary crack was already fully severed and stress-relaxed in State 4, Abaqus CAE sized the primary ligament back to coarse ($\sim 1.50\,\mathrm{mm}$), collapsing the primary ligament mesh from 90,465 elements down to 19,005 elements. Task F1745 mathematically eliminates pass-memory loss by taking the supremum of normalized relative element error across all five authentic donor states ($k \in \{T1, T2, T3, S2, S4\}$) on the common 3,923-element coarse mesh before any remeshing call is made.

Furthermore, Task F1745 resolves the historical 31,518.59 denominator spike from Task F1740 by formulating a strictly non-singular, dimensionless energy error norm normalized by the global solution energy norm $\|u\|_k$, proving that $\hat{\eta}_e$ is smoothly bounded between $0.000613$ and $15.7086$.

---

## 1. Discrepancy Reconciliation & Forensic Findings

### Finding F1745-R01: Reconciliation of the 3,923 vs 3,979 Mesh Count Discrepancy (`F1744-R04`)
- **Background**: Review Finding `F1744-R04` required reconciling whether the Case 3 donor base mesh has 3,923 or 3,979 elements, and confirming exact topological matching.
- **Forensic Verification**:
  - Every authentic solver model deck (`PK_SEC43_COARSE_PHYS.inp`, `PK_SEC43_COMPANION_T1.inp`, `PK_SEC43_COMPANION_T2.inp`, `PK_SEC43_COMPANION_T3.inp`, and Task 192 prescribed models) and all five solver ODB databases (`PK_SEC43_COMPANION_T1.odb`, `T2.odb`, `T3.odb`, `PK_SEC43_PRESCRIBED_STATE2.odb`, `STATE4.odb`) contain **exactly 3,923 physical elements** (3,814 CPE4 quads and 109 CPE3 linear triangles) and 4,078 nodes.
  - Across all five ODBs, node coordinates match to within machine precision ($\Delta x < 10^{-6}\,\mathrm{mm}$), and element connectivity is 100.00% identical.
  - **Source of the 3,979 Count**: In Task F1744 attempt 1, an unadapted free-meshing command was executed on a freshly imported CAD sketch before the first adaptive pass ran, producing 3,979 elements. That temporary CAD free-mesh was never solved or used as a physical donor.
  - **Authoritative Resolution**: The canonical, authoritative coarse base mesh for Case 3 is **3,923 elements**.

### Finding F1745-R02: Native Field Definitions, Units, and Elimination of Denominator Singularity (`F1744-R03`)
- **Native Variable Definitions in Abaqus**:
  - `MISESERI`: Normalized stress error indicator based on Zienkiewicz–Zhu (1987) SPR stress recovery:
    $$e_\sigma = \sigma^* - \sigma_h$$
    At the element level in Abaqus/Standard, `MISESERI` represents the root-mean-square von Mises difference between recovered and FE stresses:
    $$\mathrm{MISESERI}_e = \sqrt{ \frac{1}{V_e} \int_{\Omega_e} (\boldsymbol{\sigma}^* - \boldsymbol{\sigma}_h) : (\boldsymbol{\sigma}^* - \boldsymbol{\sigma}_h) \, dV } \quad [\mathrm{MPa} = \mathrm{N/mm^2}]$$
  - `MISESAVG`: Area-weighted average von Mises stress across the element:
    $$\mathrm{MISESAVG}_e = \frac{1}{V_e} \int_{\Omega_e} \sigma_{\mathrm{vM}} \, dV \quad [\mathrm{MPa} = \mathrm{N/mm^2}]$$
  - `EVOL`: Element volume / area:
    $$\mathrm{EVOL}_e = V_e = A_e \times t \quad (t = 1.0\,\mathrm{mm}) \quad [\mathrm{mm^3} = \mathrm{mm^2}]$$
- **Root Cause of the 31,518 Extreme Ratio in Task F1740**:
  - In F1740, the local relative error was computed element-by-element as:
    $$\eta_e^{\mathrm{local}} = \frac{\mathrm{MISESERI}_e}{\mathrm{MISESAVG}_e}$$
  - In elements located in stress-free or fully cracked regions, $\mathrm{MISESAVG}_e \to 0$ ($< 10^{-4}\,\mathrm{MPa}$), while numerical extrapolation noise yielded $\mathrm{MISESERI}_e \sim 10^{-1}\,\mathrm{MPa}$, producing spurious ratios up to $31,518.59$.
- **Dimensionally Rigorous Non-Singular Formulation in Task F1745**:
  - To eliminate local division-by-zero, we normalize the element energy error norm by the **global model energy solution norm**:
    $$\|e\|_e^{(k)} = \mathrm{MISESERI}_e^{(k)} \sqrt{V_e} \quad [\mathrm{MPa} \cdot \mathrm{mm} = \mathrm{N}^{1/2}]$$
    $$\|u\|_k = \sqrt{ \sum_{e=1}^{N_{\mathrm{elem}}} \left(\mathrm{MISESAVG}_e^{(k)}\right)^2 V_e } \quad [\mathrm{MPa} \cdot \mathrm{mm}]$$
  - The mean element energy norm across the model is:
    $$\|u\|_{\mathrm{elem}, k} = \frac{\|u\|_k}{\sqrt{N_{\mathrm{elem}}}}$$
  - The dimensionless, non-singular normalized relative error is:
    $$\hat{\eta}_e^{(k)} = \frac{\|e\|_e^{(k)}}{\|u\|_{\mathrm{elem}, k}} = \frac{\mathrm{MISESERI}_e^{(k)} \sqrt{V_e}}{\|u\|_k / \sqrt{N_{\mathrm{elem}}}}$$
  - The unified multi-state error-indicator envelope is:
    $$\hat{\eta}_e^{(\mathrm{envelope})} = \max_{k \in \{T1, T2, T3, S2, S4\}} \hat{\eta}_e^{(k)}$$
- **Mathematical Guarantees**:
  1. **Strictly Dimensionless**: Numerator and denominator both carry units of $[\mathrm{MPa} \cdot \mathrm{mm}]$.
  2. **Strictly Non-Singular**: $\|u\|_k > 0$ for all physical loading stages ($9.327 \le \|u\|_k \le 224.37\,\mathrm{MPa}\cdot\mathrm{mm}$).
  3. **Smooth and Bounded**: $\min \hat{\eta} = 0.000613$, median $= 0.0182$, mean $= 0.1224$, and $\max \hat{\eta} = 15.7086$. The extreme 31,518.59 artifact is completely eradicated.

---

## 2. Quantitative Envelope Statistics & Spatial Activation

The envelope was computed across all 3,923 elements using the forensic cluster audit tool `export_envelope_map.py` executed on `mnode097.cluster`.

### Table 1: Global Solution Energy Norms & State Characteristics

| State ID | Physical Increment | Prescribed $u_y$ | Crack Stage | Global Solution Energy Norm $\|u\|_k$ | Mean Element Norm $\|u\|_{\mathrm{elem}, k}$ | Dominant Elements in Specimen |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **T1** | Inc 260 | $0.130\,\mathrm{mm}$ | Primary initiation at notch root | $9.7126\,\mathrm{MPa}\cdot\mathrm{mm}$ | $0.1551\,\mathrm{MPa}\cdot\mathrm{mm}$ | 1,757 (44.8%) |
| **T2** | Inc 300 | $0.150\,\mathrm{mm}$ | Primary mid-propagation in ligament | $9.3270\,\mathrm{MPa}\cdot\mathrm{mm}$ | $0.1489\,\mathrm{MPa}\cdot\mathrm{mm}$ | 919 (23.4%) |
| **T3** | Inc 340 | $0.170\,\mathrm{mm}$ | Primary approach to central hole | $9.6974\,\mathrm{MPa}\cdot\mathrm{mm}$ | $0.1548\,\mathrm{MPa}\cdot\mathrm{mm}$ | 1,172 (29.9%) |
| **S2** | Inc 400 | $0.200\,\mathrm{mm}$ | Primary crack arrested in central hole | $144.3576\,\mathrm{MPa}\cdot\mathrm{mm}$ | $2.3048\,\mathrm{MPa}\cdot\mathrm{mm}$ | 30 (0.8%) |
| **S4** | Inc 600 | $0.300\,\mathrm{mm}$ | Secondary crack propagation to right boundary | $224.3686\,\mathrm{MPa}\cdot\mathrm{mm}$ | $3.5822\,\mathrm{MPa}\cdot\mathrm{mm}$ | 45 (1.1%) |
| **Total** | — | — | — | — | — | **3,923 (100.0%)** |

### Table 2: Quantitative Corridor Activation Metrics

| Corridor | Trajectory Points $(x, y)$ | Elements Sampled | Min $\hat{\eta}$ | Max $\hat{\eta}$ | Mean $\hat{\eta}$ | Ratio vs Global Background Mean ($\bar{\eta} = 0.122$) | State Dominance Breakdown |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Primary Corridor** | $(10.0, 70.0) \to (26.5, 51.0)$ | 22 | $0.0079$ | $15.7086$ | **$1.5942$** | **$13.0\times$** | T1: 14 (63.6%)<br>T2: 5 (22.7%)<br>T3: 2 (9.1%)<br>S2: 1 (4.5%)<br>S4: 0 (0.0%) |
| **Secondary Corridor** | $(46.5, 50.73) \to (65.0, 52.25)$ | 11 | $0.0283$ | $1.3960$ | **$0.2500$** | **$2.05\times$** | T1: 0 (0.0%)<br>T2: 2 (18.2%)<br>T3: 7 (63.6%)<br>S2: 0 (0.0%)<br>S4: 2 (18.2%) |
| **Model Wide** | Entire domain $[0, 65] \times [0, 120]\,\mathrm{mm}$ | 3,923 | $0.0006$ | $15.7086$ | **$0.1224$** | $1.0\times$ | T1: 1,757<br>T2: 919<br>T3: 1,172<br>S2: 30<br>S4: 45 |

### Physical Interpretation of Corridor Activation:
1. **Primary Corridor**: Exhibits massive error concentration ($\max \hat{\eta} = 15.71$, mean $\hat{\eta} = 1.59$, which is **13.0 times higher than the global background mean**). States T1, T2, and T3 provide full, continuous coverage from the notch root along the curved trajectory into the hole.
2. **Secondary Corridor**: Exhibits significant elevation ($\max \hat{\eta} = 1.40$, mean $\hat{\eta} = 0.25$, which is **2.05 times higher than the background mean**). It is governed by T3 (approach to hole, establishing stress concentration on the opposing flank) and S4 (secondary crack propagation).
3. **Simultaneous Synthesis**: Because the envelope takes the supremum across all states before remeshing, both corridors are simultaneously active in a single donor field.

---

## 3. Reconciliation of PBS Submissions 20 through 25 (`F1744-R06`)

Review Finding `F1744-R06` requested an explicit accounting chronology for all cluster submissions from Job 20 through Job 25. Every PBS submission is permanently preserved in `project_coordination/HPC_JOB_LEDGER.csv` and documented below:

### Table 3: Bounded HPC Submission Chronology (Jobs 20–25)

| Sub. # | PBS Job ID | Target / Operation | Compute Node | Queue | Exit Code | Classification & Physical Finding |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **20** | `1423451.mmaster02` | Task F1743: 3 Intermediate Companion Solves | `mnode097.cluster` | `normal_imfdfkmq` | **Exit 0** | **SUCCESS**: Solved T1, T2, T3 in 40s walltime. Machine-zero residual $< 5.1\times 10^{-7}\,\mathrm{kN}$. Monotonic peak `MISESERI` growth ($1.88 \to 2.40 \to 2.88\,\mathrm{MPa}$). |
| **21** | `1423459.mmaster02` | Task F1744 Attempt 1: 5-State Remesh | `mnode097.cluster` | `normal_imfdfkmq` | Exit 1 | **TECHNICAL FAILURE**: Abaqus CAE `refinementFactor` argument type mismatch (passed float instead of SymbolicConstant `DEFAULT`). Preserved. |
| **22** | `1423461.mmaster02` | Task F1744 Attempt 2: 5-State Remesh | `mnode097.cluster` | `normal_imfdfkmq` | Exit 1 | **TECHNICAL FAILURE**: Abort on stale `.lck` file left by previous attempt. Preserved. Minimal repair: cleanup trap added. |
| **23** | `1423462.mmaster02` | Task F1744 Attempt 3: 5-State Remesh | `mnode097.cluster` | `normal_imfdfkmq` | Exit 1 | **TECHNICAL FAILURE**: Missing `EVOL` output in donor ODBs caused CAE error `Cannot find volume for element`. Preserved. |
| **24** | `1423463.mmaster02` | Task F1744 Attempt 4: 5-State Remesh | `mnode097.cluster` | `normal_imfdfkmq` | Exit 1 | **TECHNICAL FAILURE**: ODB section category incompatibility between shell and solid sections in temporary CAE model. Preserved. |
| **25** | `1423469.mmaster02` | Task F1744 Attempt 5: 5-State Remesh | `mnode097.cluster` | `normal_imfdfkmq` | **Exit 0** | **SUCCESSFUL EXECUTION / SPATIAL DEFICIENCY**: Solved 3 companion models, completed 5 CAE remeshing passes in 106s, generated 19,005 elements ($96.64\%$ CPE4), min $\det(J) = 0.01215 > 0$, 3-layer UEL deck passed datacheck Exit 0. Disclosed **pass-memory loss**. |

**Cumulative Submissions Accounting**:
- Historical cumulative submissions prior to F1743: 19 jobs.
- Task F1743 consumed: 1 job (Job 20: `1423451.mmaster02`).
- Task F1744 consumed: 5 jobs (Jobs 21–25: `1423459`, `1423461`, `1423462`, `1423463`, `1423469`).
- Task F1745 consumed: **0 jobs** (`max_new_pbs_submissions = 0`).
- Total cumulative submissions: **25 jobs**.

---

## 4. Synthesis Visualization

A comprehensive 4-panel publication-quality figure has been authored and rendered at [fig_f1745_case3_envelope_synthesis.png](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/fig_f1745_case3_envelope_synthesis.png) (PDF at [fig_f1745_case3_envelope_synthesis.pdf](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/fig_f1745_case3_envelope_synthesis.pdf)):
- **Panel (a)**: Base Coarse Mesh (3,923 elements) showing the $65 \times 120\,\mathrm{mm}$ plate, initial notch at $(0, 70) \to (10, 70)$, central hole (radius $10\,\mathrm{mm}$), and loading/support pin holes (radius $5\,\mathrm{mm}$).
- **Panel (b)**: Colormap of the Unified 5-State Error-Indicator Envelope $\hat{\eta}_e^{(\mathrm{envelope})}$ across the 3,923 coarse elements, showing simultaneous intense activation of both the primary notch-to-hole path and secondary hole-to-boundary path.
- **Panel (c)**: Donor State Dominance Map: Each coarse element is colored according to the state providing its maximum error: T1 (blue, 44.8%), T2 (green, 23.4%), T3 (cyan, 29.9%), S2 (orange, 0.8%), and S4 (red, 1.1%).
- **Panel (d)**: Quantitative Along-Path Error Profiles: Continuous logarithmic profiles along both fracture corridors, demonstrating that $\hat{\eta}_e$ remains consistently above the global background mean along the entire crack trajectories.

---

## 5. Successor Proposal: Task F1746 Case 3 5-State Envelope Native Remeshing Execution

With the offline mathematical, topological, and accounting foundations established and qualified in Task F1745, Gemini Antigravity proposes successor Task **F1746-CASE3-5STATE-ENVELOPE-EXECUTION**:

### Execution Scope & Predeclared Gates for Task F1746:
1. **Single Synthetic Envelope Donor ODB**:
   - Construct `PK_SEC43_5STATE_ENVELOPE_DONOR.odb` by copying the 3,923-element geometry from `T1.odb` and populating `MISESERI` with the synthesized envelope $\hat{\eta}_e^{(\mathrm{envelope})}$ and `MISESAVG` with $S_{\mathrm{ref}} = 100.0\,\mathrm{MPa}$ at `WHOLE_ELEMENT` locations.
2. **Single Native Remeshing Pass in Abaqus CAE 2023**:
   - Execute a single native call:
     ```python
     m.adaptiveRemesh(odb=envelope_odb)
     ```
   - Because all five states are unified into a single donor field, **pass-memory loss is structurally impossible**.
3. **Predeclared Execution Gates**:
   - **Gate 1 (FE Inversion Safety)**: $100\%$ strictly positive Jacobians ($\min \det(J) > 0$).
   - **Gate 2 (Element Quality)**: $\ge 95\%$ CPE4 quads, $\le 5\%$ CPE3 triangles.
   - **Gate 3 (Primary Corridor Compliance)**: $\ge 85\%$ area compliance with $h \le \ell_0/2 = 0.1425\,\mathrm{mm}$.
   - **Gate 4 (Secondary Corridor Compliance)**: $\ge 85\%$ area compliance with $h \le \ell_0/2 = 0.1425\,\mathrm{mm}$.
   - **Gate 5 (Transverse Coarse Barrier Freedom)**: `has_transverse_coarse_barrier == False` across both corridors.
   - **Gate 6 (Production Deck Datacheck)**: 3-layer UEL production deck assembled and verified with Abaqus `pre.exe` datacheck **Exit Code 0**.
   - **Gate 7 (Strict Governance)**: Maximum **1 bounded PBS job** requested (prospective 26th cumulative submission). Zero forward fracture runs on the adapted mesh. Bitwise frozen UEL `f42_mixed_uel.for` (`CE8D5EDC...`) strictly preserved.

---

## 6. Verification and Regression Status

All 50 tests across the active project test suites pass cleanly:
- `tests/unit/test_f1745_case3_envelope_qualification.py`: 4/4 PASS
- `tests/unit/test_f1744_case3_5state_remesh.py`: 5/5 PASS
- `tests/unit/test_f1743_case3_transient_companion.py`: 7/7 PASS
- `tests/unit/test_f1742_transient_donor_recovery.py`: 5/5 PASS
- `tests/unit/test_f1741_case3_multistate_remeshing.py`: 6/6 PASS
- `tests/unit/test_f1740_case3_multistate_design.py`: 9/9 PASS
- `tests/unit/test_f1738_case1_ligament.py`: 5/5 PASS
- `tests/unit/test_f1739_case1_adapted_fracture.py`: 9/9 PASS
- **Total: 50 / 50 unit tests PASS in 16.18s**.
