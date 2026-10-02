# Supervisor Decision Note: Mode-I Resolution Extension & Gate-6 Requalification Audit

**Date:** 2026-09-12  
**Target Milestone:** Post-Handoff Mode-I Resolution Extension  
**HPC Platform:** TU Bergakademie Freiberg Cluster (`normal_imfdfkmq` / `entry_imfdfkmq`)  
**Active Scientific Status:** `CORRECTED_HIGH_BRANCH_ADAPTIVE_REPRODUCTION_PARTIALLY_QUALIFIED`  

---

## 1. Executive Summary of Audited Evidence

A rigorous raw-data verification and ODB field audit has established the following verified scientific facts:

1. **Priority Question A (Stiffness Anomaly Causal Closure):**
   * **Root Cause:** Silent Abaqus input pre-processor (`pre`) truncation of overlong single-line `*NSET` records exceeding standard line-length limits dropped 92.4% of top boundary nodes (194/210) and 89.3% of bottom boundary nodes (134/150).
   * **Kinematic Consequence:** Dropped nodes were omitted from constraint equations, causing boundary lift ($u_2$ up to $0.286\ \mu\text{m}$) and drift ($u_1$ up to $0.062\ \mu\text{m}$), which artificially softened the specimen ($K_0 \approx 122.60\text{ kN/mm}$).
   * **Restoration:** Multi-line wrapping ($\le 16$ node entries per line) restored 100% constraint enforcement, strictly eliminating boundary drift/lift ($0.0000\text{ mm}$ everywhere) and recovering stiffness to $K_0 = 138.021015\text{ kN/mm}$ ($+0.0547\%$ vs fixed reference anchor $137.945520\text{ kN/mm}$).
   * **Status:** `CAUSAL_CLOSURE_VERIFIED_BOUNDARY_SET_LINE_FORMATTING`
   * **Hypothesis Retirement:** Earlier hypotheses attributing stiffness loss to intrinsic `UNSYMM=YES` $\times$ companion element coupling are formally retired as confounded, while preserving their historical raw data.

2. **Gate-6 Full-Fracture Requalification Audit (Job 1404454.mmaster02 / 1404306.mmaster02 vs Fixed Reference 1398090.mmaster02):**
   * **Model:** Line-wrapped nominal 1% 71,320-element model (`PK_M1_NOM1_FIELD_QUAL`), running serial ($1\text{ CPU}$) under Abaqus 2023.
   * **Terminal Telemetry (from `.sta` and `.msg`):** Completed 3,804 increments (Step 1: 2,000, Step 2: 1,784), ending at $u = 0.00677407\text{ mm}$ where Abaqus time increment cutback limit was reached ($dt < 10^{-14}$ at Increment 1784 Attempt 4). Walltime: $18:34:50$, CPU time: $18:31:40$.
   * **Failure Classification:** Strictly **deep-post-peak nonlinear convergence failure / minimum-increment exhaustion**, NOT PBS walltime termination.
   * **Direct Raw-Curve Metrics ($0 \le u \le 0.00677407\text{ mm}$):**
     * Initial stiffness: $K_0 = 137.820804\text{ kN/mm}$ ($\mathbf{-0.0904\%}$ vs reference anchor $137.945520\text{ kN/mm}$, $N=400$, $R^2 = 0.99999960$).
     * Peak force: $F_{\max} = 0.745325\text{ kN}$ at $u = 0.005750\text{ mm}$ ($\mathbf{-1.643\%}$ vs reference $0.757778\text{ kN}$ at $u = 0.005857\text{ mm}$).
     * Pre-peak RMS error ($0 \le u \le 0.005750\text{ mm}$): $\mathbf{0.000625\text{ kN}}$ ($0.625\text{ N}$, $0.082\%$ of peak load).
     * Common-interval full RMS error ($0 \le u \le 0.00677407\text{ mm}$): $\mathbf{0.160501\text{ kN}}$ ($160.501\text{ N}$, $\mathbf{21.18\%}$ of peak load; continuous $L_2 = 119.749\text{ N}$, $15.80\%$).
     * External work $\int F\,du$: $W_{\text{ext}} = 2.572602\text{ mJ}$ vs $W_{\text{ref,common}} = 2.358288\text{ mJ}$ ($\Delta W_{\text{ext}} = \mathbf{+9.088\%}$).
     * Cutoff reaction force: $F_{\text{adapt}} = 0.184465\text{ kN}$ vs $F_{\text{ref}} = 0.000454\text{ kN}$.
   * **Field Output Finding:** ODB field outputs in `PK_M1_NOM1_FIELD_QUAL.odb` contain only nodal displacement and reaction force (`['RF', 'U']`). Scalar damage SDV14 was omitted because `*ELEMENT OUTPUT` targeted the UEL layer. Crack localization and regularization profiles in Figure 4 are preserved from the verified reference model `fixture_h0015` and earlier companion-enabled runs. Direct raw damage profile-difference norms for 1404454 are unavailable in the ODB.
   * **Status:** `CORRECTED_HIGH_BRANCH_ADAPTIVE_REPRODUCTION_PARTIALLY_QUALIFIED`

3. **First-Divergence Location & Source Audit (Job 1398090 vs Job 1404454):**
   * **Exact Crossing Identification ($N = 3,786$ points):**
     - $0 \le u \le 0.0050\text{ mm}$: Parity strictly qualified ($|\Delta F| \le 0.69\text{ N}$, relative error $\le 0.10\%$, $K_0 = 137.82\text{ kN/mm}$, $-0.0904\%$).
     - First $1\text{ N}$ crossing: at $u = \mathbf{0.005533\text{ mm}}$ ($-1.00\text{ N}$, $0.14\%$ relative discrepancy).
     - Peak: Adaptive reaches $F_{\max} = 0.7453\text{ kN}$ at $u = 0.005750\text{ mm}$; Reference reaches $F_{\max} = 0.7578\text{ kN}$ at $u = 0.005857\text{ mm}$ ($\Delta F_{\max} = -1.643\%$).
     - Post-peak: Discrepancy accelerates rapidly ($|\Delta F| = 51\text{ N}$ at $0.005769\text{ mm}$; $|\Delta F| = 105\text{ N}$ at $0.005778\text{ mm}$; full RMS error $= 21.18\%$). Reference drops to $0.00045\text{ kN}$, while adaptive forms an artificial plateau at $0.1845\text{ kN}$.
   * **Audit & Epistemic Downgrade of 12-Factor Matrix (`gate6_one_factor_matrix.json` & `gate6_postpeak_mesh_hypothesis_audit.json`):**
     - Governing UEL formulation, plate geometry, constitutive parameters ($E, \nu, G_c, l_0, \kappa$), boundary kinematics, and nominal loading rate ($1.0\times 10^{-6}\text{ mm/inc}$) are verified identical.
     - **Phase-Field DOF Identification:** Abaqus deck syntax (`*USER ELEMENT, TYPE=U1 ... \n 3`) mathematically and unambiguously confirms that DOF 3 is the scalar phase-field order parameter $d$. Therefore, the solver divergence reported at Node 61805 ($(0.940192, 0.509091)\text{ mm}$) in DOF 3 represents phase-field Newton-Raphson divergence.
     - **Failure Location Mesh Resolution Audit:** An exact geometric audit of elements incident to Node 61805 revealed $h \approx 0.0048\text{--}0.0052\text{ mm}$ ($h/l_0 \approx 0.64\text{--}0.70$), which is strictly $< 1.0$. Coarsening with $h/l_0 > 1.0$ (up to $1.04$) is localized around $x \in [0.85, 0.90]\text{ mm}$.
     - **Epistemic Classification of Mesh Coarsening:** Downgraded from "Primary Cause" to **`SUPPORTED_ASSOCIATION_NOT_CAUSAL`**. Spatial coincidence between downstream coarsening ($h/l_0$ rising from $0.235$ at tip to $\sim 0.67\text{--}0.88$ downstream) and Newton-Raphson failure at Node 61805 is a supported association, but does not constitute causal proof.
   * **Companion Visualization & SDV ODB Output Resolution:**
     - Co-located companion mesh (`CPE4`/`CPE3`, 71,320 elements) connected via verified state-transfer UMAT bridge (`DDSDDE = 1.D-11`, zero stress).
     - Diagnostic solver job `1404931.mmaster02` (`PK_M1_NOM1_SDV_TRUNC`) and companion `1404933.mmaster02` (`PK_M1_NOM1_STRICT_0062`) are actively executing on `mnode098` and remain untouched.

4. **Priority Question B (Remesh Count Discrepancy & Primary-Source Linkage):**
   * **Primary Publication Cardinality Semantics**:
     - **13,941 Elements**: Explicitly published in Section 4.1 (p. 3265, line 1027) as the total finite element count ($N_{el}$) of the nominal Mode-I benchmark single-pass adapted mesh.
     - **14,804 Elements**: Published in Section 3.3, Listing 2 (p. 3263) as the cardinality of element set `umatelem` / `All_elem` ($29,609 \dots 44,412$) and node set `All_elem` ($1 \dots 14,731$). Represents a separate illustrative 3-layer UEL+UMAT deck code snippet ($\Delta N_{el} = +863$ elements, $+6.19\%$ vs 13,941) whose exact relation to the Section 4.1 mesh is unresolved.
     - **26,282 Elements**: Published in Section 4.1 (p. 3264) as the non-adaptive conventional reference mesh with a pre-refined band ($h = 0.003\,\text{mm}$).
     - **6,382 Elements**: Published in Section 4.1.1, Table 1 (p. 3268) as the adapted count for the coarse mesh size sensitivity study ($h_{\text{cms}} = 0.02\,\text{mm}, l_0 = 0.01\,\text{mm}, \text{errorTarget} = 5.0$).
   * **Listing 1 Linkage Contradiction**:
     - Listing 1 hard-codes `errorTarget = 1.0` inside `create_remeshing_rule_assembly_instance`, and Section 4.1 invokes this workflow with $h_{\min}=0.001\,\text{mm}$ and $h_{\max}=0.020\,\text{mm}$ without an override.
     - In controlled Abaqus CAE execution, this exact published workflow yields 71,320 elements across Abaqus 2021, 2022, and 2023 on Linux, creating a direct reproducibility contradiction (`PUBLICATION_LINKAGE_AMBIGUOUS`).
   * **Mesh Decomposition Provenance Reconciliation**:
     - The canonical production 71,320-element mesh contains exactly **69,443 CPE4 + 1,877 CPE3 = 71,320 continuum finite elements** (and 70,845 mesh nodes before the RP).
     - Physical `.inp` files generated by Abaqus CAE in 2021, 2022, and 2023 contain exactly **69,443 CPE4 + 1,877 CPE3 = 71,320 elements**.
   * **Raw Artifact Audit of Exact Twin Jobs across Linux Releases (1404373 & 1404968)**:
     - Abaqus 2021.HF26, 2022 GA, and 2023.HF4 produced 100.000% topologically and geometrically identical adapted meshes with identical substantive deck content (normalized node hash `116f2e20...`, normalized elem hash `30776764...`, all 142,268 substantive lines identical).
     - Line-by-line diff confirms that the ONLY differences between generated `.inp` files are the header comment lines (`** Generated by: Abaqus/CAE ...`).
   * **Abaqus 2024 GA Windows Execution**:
     - Running the exact canonical CPE4 pre-analysis and remeshing under Abaqus 2024 GA on Windows (`win_b64`) produced **71,904 continuum elements** (69,983 CPE4 + 1,921 CPE3, 71,408 mesh nodes, adapted deck SHA-256 `66e93e1aa24b10ebd43151f0e5e63f9f49ff3ebaad81dfbe12d73f8c5f6115ac`).
     - Classified as `RELEASE_PLUS_PLATFORM_CONFOUNDED` (+584 elements, +0.82% vs Linux 71,320).
   * **Current Epistemic Status**:
     - Release status: **`CANONICAL_CPE4_RELEASE_2021_2022_2023_INVARIANCE_VERIFIED`**
     - Overall Gate 5 status: **`UNRESOLVED_WITH_PUBLICATION_INFORMATION_MISSING`**
   * **The 4 Irreducible Missing Literature Facts**:
     1. Workflow linkage & effective `errorTarget` for Section 4.1 Mode-I benchmark (`PUBLICATION_LINKAGE_AMBIGUOUS`).
     2. Free meshing algorithm (`ADVANCING_FRONT` vs `MEDIAL_AXIS`) and part seed curvature controls (`PLAUSIBLE_UNTESTED_FACTOR`).
     3. Initial coarse mesh element and node counts before remeshing (`PLAUSIBLE_UNTESTED_FACTOR`).
     4. Host Abaqus release year/hotfix and operating system platform (omitted from text).
   * A refined 4-point technical inquiry draft is preserved in the repository and remains strictly **unsent** pending explicit human approval.

---

## 2. Supervisor Recommendation & Decisions

We recommend that the supervisor:

1. **Accept Gate 6 Classification as `CORRECTED_HIGH_BRANCH_ADAPTIVE_REPRODUCTION_PARTIALLY_QUALIFIED`:**
   * Recognize that the pre-peak mechanical response of the nominal 1% 71,320-element model is strictly qualified ($\Delta K_0 = -0.09\%$, $\Delta F_{\max} = -1.64\%$, pre-peak RMS error = $0.08\%$).
   * Acknowledge the two material boundaries that prevent full qualification: (a) post-peak trajectory divergence on the common interval (RMS error $21.18\%$) culminating in solver minimum-increment exhaustion ($dt < 10^{-14}$) at $u = 0.006774\text{ mm}$ before complete crack separation; and (b) omission of scalar damage SDV14 in `1404454.odb`.
   * Formally retire the defective low branch ($\approx 122.38\text{–}122.60\text{ kN/mm}$) as an input formatting defect, while preserving its raw experimental data.

2. **Accept Priority Question B as an External Information Boundary:**
   * Maintain Priority Question B release comparison as `CANONICAL_CPE4_RELEASE_2021_2022_2023_INVARIANCE_VERIFIED` and broader status as `UNRESOLVED_WITH_PUBLICATION_INFORMATION_MISSING`.
   * Do not tune `errorTarget` or mesh controls artificially.
   * Decide whether to authorize transmission of the prepared 4-point author inquiry (`docs/supervisor_reports/PRIORITY_B_REPRODUCIBILITY_MATRIX_AND_AUTHOR_QUERY.md`) to Dr. Pandey and Prof. Kumar, or conclude the Mode-I investigation at this documented software/literature boundary.

---

## 3. Supporting Evidence & Cryptographic Hashes

* **Raw Curve Hashes:**
  * Adaptive Curve (`PK_M1_NOM1_FQ_raw_Fu.csv`): `e40eb63a529f1d99f54b9d60fafd178bd8c566d190386f0967aa1434c3ba9a96`
  * Reference Curve (`curve_standard_1398090.csv`): `780d05d39532e778802cdd8503cdd0df25568e412c3d4a51c50f4e001febede6`
* **Canonical CPE4 Input Decks & Meshes (71,320 Elements = 69,443 CPE4 + 1,877 CPE3):**
  * Coarse `CPE4` Pre-Analysis Deck (`JOB1_CPE4_1PCT.inp`): `53ddde8298225c134586450035b3c0af0e8280069d88ae8335e3b1e9ad0502a8`
  * 2021 Adapted `CPE4` Deck (`JOB2_REFINED_CPE4_1PCT.inp`): `190e63a1a49550b86a6a0de486e055c7f76ad7ea44017b96d2a26d863ca42c42`
  * 2022 Adapted `CPE4` Deck (`JOB2_REFINED_CPE4_1PCT.inp`): `ef57beefc19e82cc88548f982646917031e40ada9a03af6a373d3c292ddddb3d`
  * 2023 Adapted `CPE4` Deck (`JOB2_REFINED_CPE4_1PCT.inp`): `c2bb3f62ae1181740a6c67d0c65b042855b2ecaea35d3a98526e3caf718e2afa`
  * 2024 Adapted `CPE4` Deck (Windows): `66e93e1aa24b10ebd43151f0e5e63f9f49ff3ebaad81dfbe12d73f8c5f6115ac`
