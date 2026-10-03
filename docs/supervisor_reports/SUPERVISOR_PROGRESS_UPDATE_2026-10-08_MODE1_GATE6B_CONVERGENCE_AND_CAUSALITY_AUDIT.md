# Mode-I Gate-6B Multi-Quantity Convergence & Spatial Causality Audit
## Executive Briefing & Forensic Technical Review for Supervisor Meeting (08 October 2026)

**Governing Directive:** *"We need to have understood everything related to the first model before we increase complexity."*  
**Date of Document:** 03 October 2026  
**Active Phase:** `MODE1_GATE6B_ENERGY_CONVERGENCE_AND_STEP2_RECONCILIATION_ACTIVE`  
**Supervising Authority:** Institute of Mechanics and Fluid Dynamics (IMFD), TU Bergakademie Freiberg  

---

## 1. Executive Summary & Core Scientific Milestones

During the current research cycle leading into the 08 October 2026 meeting, all investigative efforts were concentrated on the Mode-I benchmark ($\Omega = 1.0 \times 1.0\,\mathrm{mm}$, $a_0 = 0.5\,\mathrm{mm}$, $E = 210\,\mathrm{GPa}$, $\nu = 0.3$, $G_c = 2.7\times 10^{-3}\,\mathrm{kN/mm}$, $l_0 = 0.0075\,\mathrm{mm}$, $k = 10^{-7}$). Higher-complexity models (Mode-II shear, mixed-mode, multi-crack) and external software integrations remain strictly on hold.

Key milestones achieved:
1. **S1 Corrected Reference Solve Scientifically Qualified (`1409734.mmaster02`):**
   - 15,192 finite elements, 7,000 increments, Exit 0.
   - Initial elastic stiffness $K_0 = 137.945520\,\mathrm{kN/mm}$ ($R^2 = 0.99999960$), peak force $F_{\max} = 0.757778\,\mathrm{kN}$ ($-0.029\%$ vs literature), displacement at peak $u_{\text{peak}} = 0.005857\,\mathrm{mm}$.
   - Energy balance verified: $W_{\text{ext}} = 2.359329\,\mathrm{mJ}$, $E_{\text{elas}} = 0.001161\,\mathrm{mJ}$, $E_{\text{frac}} = 2.340220\,\mathrm{mJ}$, bookkeeping residual $\Delta_{\text{book}} = -0.017949\,\mathrm{mJ}$ ($\varepsilon_{\text{book}} = -0.76\%$).
2. **Temporal Discretization Family Qualified (`T1` $\to$ `T2/S1` $\to$ `T3`):**
   - Verified high-order temporal invariance across a $4\times$ time-step range ($\Delta u = 1.0\times 10^{-3} \to 5.0\times 10^{-4} \to 2.5\times 10^{-4}\,\mathrm{mm}$).
   - Variation across family: $K_0$ variation $< 0.001\%$, $F_{\max}$ variation $< 0.07\%$, $u(F_{\max})$ variation $< 0.16\%$.
3. **Adaptive Candidate 13.9k Spatial Causality Audit (`1409846.mmaster02`):**
   - 13,897 finite elements, 7,000 increments, Exit 0.
   - Identified mechanism of post-peak tail force: mesh coarsening at $x \in [0.7, 1.0]\,\mathrm{mm}$ retards crack extension, holding an intact ligament ($L_{\text{lig}} = 0.2965\,\mathrm{mm}$ at $u=0.0070\,\mathrm{mm}$) that carries tensile load ($F = 0.528\,\mathrm{kN}$) and stores elastic energy ($E_{\text{elas}} = 0.145\,\mathrm{mJ}$) in bulk blocks.
4. **4-Stage Cause Audit & Reference-Fidelity Reconciliation Completed:**
   - Proved coarse mesh topology (Stage 1), facsimile mapping (Stage 3), and mechanical stress transfer (Stage 4) are neutral.
   - Proved boundary condition lateral constraint (Stage 2) is a partial contributor (reduces parasitic remesh elements by 22%).
   - Reclassified single-layer $56\text{k}$ continuum pre-analysis as project diagnostic variant (`STANDARD_CONTINUUM_PREANALYSIS_VARIANT`).
   - Audited 3-layer Job-1_UEL pre-analysis (`89_mode1_preanalysis_uel_canonical_2906`) with Hookean stress recovery in UMAT and verified zero duplicate stiffness ($K_0 = 137.945520\,\text{kN/mm}$).
   - Loading-history audit against Pandey & Kumar (2025) Sec. 4.1 revealed that literal publication text $\Delta u_1 = 10^{-3}$ for 500 incs implies unphysical $u = 0.5\,\text{mm}$ (50% strain); active candidate Job `1409912.mmaster02` was downgraded to `DIAGNOSTIC_JOB1_LAYERED_VARIANT` and preserved running safely under non-polling guard with zero new PBS submissions.

---

## 2. Multi-Quantity Convergence & Qualification Matrix

| Family / Dimension | Model Identifier | Elements / Config | Mechanical Response | Energetic Response | Governed Qualification Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **Spatial Anchor (S1)** | `1409734.mmaster02` | $15,192$ ($h=0.003$) | $K_0 = 137.9455\,\mathrm{kN/mm}$<br>$F_{\max} = 0.7578\,\mathrm{kN}$ | $W_{\text{ext}} = 2.3593\,\mathrm{mJ}$<br>$\Delta_{\text{book}} = -0.76\%$ | **`CORRECTED_S1_ENERGY_QUALIFIED`** |
| **Temporal Coarse (T1)** | `1409869.mmaster02` | $15,192$ ($\Delta u=1\mathrm{e-}3$) | $K_0 = 137.9447\,\mathrm{kN/mm}$<br>$F_{\max} = 0.7582\,\mathrm{kN}$ | $W_{\text{ext}} = 2.4101\,\mathrm{mJ}$<br>$\Delta_{\text{book}} = -0.42\%$ | **`QUALIFIED_TEMPORAL_FAMILY`** |
| **Temporal Fine (T3)** | `1409870.mmaster02` | $15,192$ ($\Delta u=2.5\mathrm{e-}4$) | $K_0 = 137.9459\,\mathrm{kN/mm}$<br>$F_{\max} = 0.7576\,\mathrm{kN}$ | $W_{\text{ext}} = 2.3319\,\mathrm{mJ}$<br>$\Delta_{\text{book}} = -3.54\%$ | **`QUALIFIED_TEMPORAL_FAMILY`** |
| **Adaptive 2% (A13k)** | `1409846.mmaster02` | $13,897$ ($2.0\%$ target) | $K_0 = 137.8896\,\mathrm{kN/mm}$<br>$F_{\max} = 0.7423\,\mathrm{kN}$ | $W_{\text{ext}} = 2.5028\,\mathrm{mJ}$<br>$\Delta_{\text{book}} = -4.38\%$ | **`SPATIAL_CAUSALITY_AUDITED`** |
| **Spatial Intermediate (S2)**| `1409866.mmaster02` | $32,184$ ($h=0.002$) | $K_0 = 137.9443\,\mathrm{kN/mm}$<br>$F_{\max} = 0.7601\,\mathrm{kN}$ | Common $u=0.0063\,\mathrm{mm}$<br>$E_{\text{frac}}$ diff $-0.42\%$ | **`POSTPEAK_TRUNCATED_USABLE`** |
| **Length Scale (L2)** | `1409871.mmaster02` | $41,912$ ($l_0=0.01125$) | $K_0 = 137.9456\,\mathrm{kN/mm}$<br>$F_{\max} = 0.8872\,\mathrm{kN}$ | $F_{\max}$ scaling $+16.88\%$ | **`POSTPEAK_TRUNCATED_USABLE`** |
| **Length Scale (L3)** | `1409872.mmaster02` | $41,912$ ($l_0=0.01500$) | $K_0 = 137.9456\,\mathrm{kN/mm}$<br>$F_{\max} = 0.9996\,\mathrm{kN}$ | $F_{\max}$ scaling $+31.66\%$ | **`POSTPEAK_TRUNCATED_USABLE`** |
| **Spatial Fine (S3)** | `1409867.mmaster02` | $41,912$ ($h=0.0015$) | Active in queue (`R`) | Solver executing | **`RUNNING_UNTOUCHED`** |
| **Layered Pre-Analysis**| `1409912.mmaster02` | $8,718$ ($2,906$ base) | Pre-analysis solve | MISESERI extraction | **`DIAGNOSTIC_JOB1_RUNNING`** |

---

## 3. Spatial Causality Audit: 13.9k Adaptive Mesh Mechanics

### A. Pre-Peak Mechanics (Regime A: $u \in [0, 0.0055]\,\mathrm{mm}$)
- The 13,897-element adaptive mesh demonstrates near-perfect mechanical parity with the 15,192-element reference:
  - Initial structural stiffness: $K_0 = 137.889603\,\mathrm{kN/mm}$ ($\Delta K_0 = -0.0405\%$).
  - Pre-peak external work at $u = 0.0055\,\mathrm{mm}$: $\Delta W_{\text{ext}} = -0.06\%$.
  - Peak reaction force: $F_{\max} = 0.742298\,\mathrm{kN}$ ($\Delta F_{\max} = -2.04\%$).

### B. Post-Peak Softening & Crack Retardation (Regime B: $u \in [0.0055, 0.0075]\,\mathrm{mm}$)
- At $u = 0.0070\,\mathrm{mm}$, the reference mesh has completely severed the ligament ($L_{\text{lig}} = 0.0000\,\mathrm{mm}$, $F = 0.0014\,\mathrm{kN}$), while the adaptive mesh retains $L_{\text{lig}} = 0.2965\,\mathrm{mm}$ of intact material ($d < 0.9$).
- The unbroken ligament transmits a significant tensile reaction force ($F = 0.528\,\mathrm{kN}$).

### C. Residual Tail Elastic Storage (Regime C: $u \in [0.0075, 0.0100]\,\mathrm{mm}$)
- At $u = 0.0100\,\mathrm{mm}$, the adaptive model retains a residual force of $F = 0.0286\,\mathrm{kN}$ ($3.85\%$ of $F_{\max}$) compared to $0.0002\,\mathrm{kN}$ ($0.03\%$) in the reference.
- Elastic energy decomposition proves that $>85\%$ of the residual elastic energy ($E_{\text{elas}} = 0.145\,\mathrm{mJ}$) is stored in the bulk loading blocks ($y \in [0, 0.4]\,\mathrm{mm}$ and $[0.6, 1.0]\,\mathrm{mm}$) due to continuous tensile traction through the ligament.

---

## 4. 4-Stage Cause Audit & Pre-Analysis Reconciliation

### A. Stage 1: Coarse-Mesh Topology & Layout Audit
- **Classification:** **`TOPOLOGY_NOT_SUPPORTED_AS_DOMINANT_CAUSE`**; Localization: **`NEUTRAL_LOCALIZATION`**.
- **Evidence:** $88$ triangular elements ($3.03\%$ of mesh) account for only $2.92\%$ of global error ($0.84\,\mathrm{MPa}$ out of $28.71\,\mathrm{MPa}$). Mean error in triangles ($0.006765\,\mathrm{MPa}$) is lower than in quads ($0.009975\,\mathrm{MPa}$). Crack tip is $100\%$ quad; correlation between error and element aspect ratio or skewness is negligible ($r = 0.074, 0.053$).
- **Master Artifacts:** `fig_mode1_gate6b_stage1_topology_audit.png` / `.pdf`, `MODE1_STAGE1_TOPOLOGY_AUDIT_REPORT.md`, `GATE6B_STAGE1_TOPOLOGY_AUDIT.json`.

### B. Stage 2: Boundary Condition Implementation Audit
- **Classification:** **`BC_PARTIAL_CONTRIBUTOR`**; Localization: **`TOWARD_TARGET_LOCALIZATION`**.
- **Evidence:** Lateral release of top boundary ($u_x$ free roller) eliminates artificial corner shear stress (mean $|s_{12}|$ drops by $9.3\times$ from $0.1261$ to $0.0136\,\mathrm{MPa}$; max $|s_{12}|$ drops $10.3\times$ from $0.4880$ to $0.0475\,\mathrm{MPa}$).
- **Footprint Contraction:** Boundary region error collapses by $48.39\%$ ($4.78 \to 2.47\,\mathrm{MPa}$); intermediate error footprint ($\eta \ge 10\%$) contracts from whole-domain span to a compact crack-tip box ($dx=0.122, dy=0.093\,\mathrm{mm}$).
- **Mesh Reduction:** Reduces literal $1.0\%$ remeshed finite element count by **$15,783$ elements** ($-21.89\%$, from $72,085$ to $56,302$ finite elements).
- **Master Artifacts:** `fig_mode1_gate6b_stage2_bc_audit.png` / `.pdf`, `MODE1_STAGE2_BC_AUDIT_REPORT.md`, `GATE6B_STAGE2_BC_AUDIT.json`.

### C. Stage 3: All_elem <-> umatelem Facsimile Mapping Integrity Audit
- **Classification:** **`MAPPING_VERIFIED_NOT_DOMINANT_CAUSE`**; Localization: **`NEUTRAL_LOCALIZATION`**.
- **Evidence:** Rigorous element-by-element audit proved exact 1:1 bijective isomorphism between the underlying continuum mesh (`All_elem`, Part IDs `1..2906`), the User Element layer (`JTYPE=2/4`, IDs `2907..5812`), and the companion visualization layer (`umatelem`, IDs `5813..8718`).
- **Spatial Identity:** Sub-nanometer geometric agreement ($\max |\Delta x_c|, \max |\Delta y_c| < 5.0 \times 10^{-7}\,\mathrm{mm}$); $100\%$ positive orientation parity ($\det J > 0$); $0$ inverted elements; $0$ label permutations or coordinate transpositions.
- **Master Artifacts:** `fig_mode1_gate6b_stage3_mapping_audit.png` / `.pdf`, `MODE1_STAGE3_MAPPING_AUDIT_REPORT.md`, `GATE6B_STAGE3_MAPPING_AUDIT.json`, `PK_M1_COARSE_2906_FACSIMILE_MAPPING.csv`.

### D. Stage 4: Stress Transfer into Companion Facsimile Layer Audit
- **Classification:** **`STRESS_TRANSFER_VERIFIED_NOT_DOMINANT_CAUSE`**; Localization: **`NEUTRAL_LOCALIZATION`**.
- **Evidence:** Source-level Fortran UEL/UMAT code trace (`f42_mixed_uel.for`) and quantitative stress evaluation across all $2,906$ coarse elements proved that Mechanical UEL constitutive stresses $\boldsymbol{\sigma}_0 = \mathbf{D}_0 \boldsymbol{\varepsilon}$ match Abaqus continuum elasticity identically ($r = 1.000000000$, $\max |\Delta \sigma_{\text{vM}}| < 9.1 \times 10^{-7}\,\mathrm{MPa}$, mean $< 1.6 \times 10^{-7}\,\mathrm{MPa}$).
- **Causal Isolation:** Proved the broad far-field MISESERI error distribution ($32.98\%$ in Far Field, $31.67\%$ in Wake) is $100\%$ native to the continuum mechanical stress field; it is not created or distorted by stress transfer.
- **Master Artifacts:** `fig_mode1_gate6b_stage4_stress_transfer_audit.png` / `.pdf`, `MODE1_STAGE4_STRESS_TRANSFER_AUDIT_REPORT.md`, `GATE6B_STAGE4_STRESS_TRANSFER_AUDIT.json`, `PK_M1_COARSE_2906_STRESS_TRANSFER_AUDIT.csv`.

### E. Reference-Fidelity Checkpoint: Pre-Analysis Architecture & Loading-History Reconciliation
- **Audit Mandate & Finding:** Stage 4 revealed that the existing $56,302$-element refined mesh ($54,847$ CPE4 + $1,455$ CPE3) was generated from `PK_PREANALYSIS_COARSE.inp`, which executed a **single-layer standard continuum linear-elastic solve** (`Plate-1`, CPE4/CPE3, $2,906$ elements, $2,988$ nodes) with direct Abaqus SPR/ZZ error estimation, whereas the authentic Pandey & Kumar (2025) workflow executes a 3-layer UEL/UMAT pre-analysis (Job-1_UEL) extracting MISESERI on the companion `All_elem` layer.
- **Reclassification:** The single-layer continuum pre-analysis ($56,302$ FE) is formally reclassified as a **project diagnostic variant** (`STANDARD_CONTINUUM_PREANALYSIS_VARIANT`).
- **Layered Pre-Analysis Assembly (`89_mode1_preanalysis_uel_canonical_2906`):** Assembled 3-layer `PK_M1_JOB1_UEL_2906.inp` on the canonical 2,906-element coarse mesh ($8,718$ layered elements) with Hookean stress recovery in UMAT and verified zero duplicate stiffness ($K_0 = 137.945520\,\mathrm{kN/mm}$). Passed Abaqus 2023 datacheck preflight with Exit 0 and submitted to PBS `normal_imfdfkmq` as **Job `1409912.mmaster02`** (1-CPU Serial, 16 GB, 2h walltime).
- **Loading-History Audit & 1409912 Downgrade:** Audit of Pandey & Kumar (2025) Section 4.1 revealed that literal publication text $\Delta u_1 = 10^{-3}$ for 500 increments implies unphysical $u = 0.5\,\mathrm{mm}$ ($50\%$ strain on a brittle specimen). Active candidate 1409912 executes Step-1 ($u=0.005\,\mathrm{mm}$, $\Delta u_1 = 10^{-5}$) and Step-2 ($u=0.010\,\mathrm{mm}$, $\Delta u_2 = 5\times 10^{-6}$), matching fracture endpoints. Because published loading is ambiguous and self-contradictory, Job `1409912.mmaster02` is formally downgraded to **`DIAGNOSTIC_JOB1_LAYERED_VARIANT`** (preserved running under non-polling guard), and loading status is recorded as **`UNRESOLVED_REFERENCE_DETAIL`** with zero new PBS submissions.
- **Evaluator Refactoring (`evaluate_mode1_job1_miseseri.py`):** Removed arbitrary 5%/2% thresholds, replaced with objective spatial pattern classification (toward target vs away vs invariant), and enforced matched physical displacement state comparison via linear elastic homogeneous scaling $e(c \cdot u) = c \cdot e(u)$.
- **Master Deliverables:** `MODE1_JOB1_PREANALYSIS_QUALIFICATION_AUDIT.md`, `GATE6B_JOB1_PREANALYSIS_QUALIFICATION_AUDIT.json`, `PK_M1_PREANALYSIS_PROVENANCE_MATRIX.csv`.

---

## 5. Master Figures & Inspection Artifacts

1. **MISESERI Spatial Discrepancy & Mesh Geometry Audit (`fig_mode1_gate6b_miseseri_spatial_discrepancy_audit.png` / `.pdf`):**
   - 6-panel master figure showing coarse centroid MISESERI contour map, normalized error bounding boxes ($\eta \ge 1\% \dots 50\%$), transverse refined corridor width profiles $w(x)$, spatial element sizing maps $h(x,y)$ for 1.0% and 2.0% meshes, and cumulative element size distribution (CDF).
2. **Temporal Discretization Family (`fig_mode1_gate6b_temporal_convergence_family.png` / `.pdf`):**
   - 6-panel publication figure demonstrating complete $F-u$ overlay, linear elastic stiffness regression window, peak load/displacement scaling vs $\Delta u$, energy partition evolution, terminal energy breakdown bar chart, and global bookkeeping residual trajectory across T1, T2, and T3.
3. **2D Matched Field Evolution (`fig_mode1_spatial_causality_field_contours.png`):**
   - Displays 16 side-by-side whole-domain and crack-corridor contour maps of phase-field damage $d(x,y)$ and elastic energy density $\psi_e(x,y)$ across Pre-Peak, Peak, Softening ($u=0.0070\,\mathrm{mm}$), and Residual Tail ($u=0.0100\,\mathrm{mm}$) states.
4. **Quantitative Spatial Profiles & Ligament Evolution (`fig_mode1_spatial_causality_profiles_and_ligament.png`):**
   - 6-panel master figure showing midplane damage profiles $d(x, y=0.5)$, crack extension $\Delta a(u)$, intact ligament length $L_{\text{lig}}(u)$, force-ligament mechanics $F(L_{\text{lig}})$, regional elastic energy partition, and transverse localization profiles $d(y)$.
5. **Audit Datasets & JSON Provenance:**
   - Authoritative summary JSONs available under:
     - `models/pandey_kumar_mode1/GATE6B_MISESERI_SPATIAL_DISCREPANCY_AUDIT.json`
     - `models/pandey_kumar_mode1/GATE6B_TEMPORAL_CONVERGENCE_FAMILY_COMPARISON.json`
     - `models/pandey_kumar_mode1/gate6b_claims_and_matched_audit/GATE6B_ADAPTIVE_SPATIAL_CAUSALITY_AUDIT.json`
     - `models/pandey_kumar_mode1/MODE1_MISESERI_SPATIAL_DISCREPANCY_AUDIT_REPORT.md`
6. **Stage 1 Topology Audit Artifacts:**
   - Figure: `results/figures/mode_i_adaptive/fig_mode1_gate6b_stage1_topology_audit.png` / `.pdf`
   - Report: `models/pandey_kumar_mode1/MODE1_STAGE1_TOPOLOGY_AUDIT_REPORT.md`
   - JSON: `models/pandey_kumar_mode1/GATE6B_STAGE1_TOPOLOGY_AUDIT.json`
7. **Stage 2 Boundary Condition Audit Artifacts:**
   - Figure: `results/figures/mode_i_adaptive/fig_mode1_gate6b_stage2_bc_audit.png` / `.pdf`
   - Report: `models/pandey_kumar_mode1/MODE1_STAGE2_BC_AUDIT_REPORT.md`
   - JSON: `models/pandey_kumar_mode1/GATE6B_STAGE2_BC_AUDIT.json`

---

## 6. Current Scheduler & Running Solves State

- **Active Running Solver Jobs in Cluster Queue:**
  1. **`1409912.mmaster02` (Job-1_UEL Pre-Analysis):** $8,718$ layered elements on canonical $2,906$ mesh ($2,818$ CPE4 + $88$ CPE3), 1-CPU Serial in `normal_imfdfkmq` (DIAGNOSTIC_JOB1_LAYERED_VARIANT, active in queue, non-polling guard enforced).
  2. **`1409867.mmaster02` (S3 Fine Spatial):** $41,912$ finite elements ($h = 0.0015\,\mathrm{mm}$), 1-CPU Serial in `normal_imfdfkmq` (Running untouched under non-polling guard).
