# Authoritative HPC Execution Ledger

**Institution:** TU Bergakademie Freiberg, Institute of Mechanics and Fluid Dynamics (IMFD)  
**Date:** September 4, 2026 (Updated September 10, 2026: Terminal Qualification of 7 HPC Jobs, Full-Interval Gate-6 $2 \times 2$ Factorial Closure, Case 81 Full-Interval Intermediate Branch Qualification, Exact 1.664 TB Integer-Byte Storage Remediation Verified, & Strict Epistemic Discipline)  
**Document:** `05_hpc_execution/execution_notes/AUTHORITATIVE_HPC_EXECUTION_LEDGER.md`

---

## 1. Primary HPC Calculations Ledger

```text
=======================================================================================================================
PBS JOB ID         MODEL / CASE DESCRIPTION          ELEMENTS / NODES        WALLTIME   CPUT       SCIENTIFIC CLASSIFICATION & VERDICT
=======================================================================================================================
1398090.mmaster02  Mode-I Fixed-Mesh Reference       15,192 / 15,522         06h 31m    06h 30m    SCIENTIFICALLY_ACCEPTED
                   (Standard Uniform Crack Band)                                                   (Task 3: F_peak=0.7578 kN, error -0.029%, Exit 0)
-----------------------------------------------------------------------------------------------------------------------
1379893.mmaster02  Mode-I Coarse Pre-Analysis        2,906 / 2,988           00h 04m    00h 04m    QUALIFIED_EXTRACTION_SOURCE
                   (Linear Elastic Pre-Refinement)                                                 (Extracted 3,930-row MISESERI error dataset)
-----------------------------------------------------------------------------------------------------------------------
1398807.mmaster02  Mode-I Blunt Notch Trial          74,261 / 73,806         12h 15m    11h 48m    TECHNICAL_PASS_SCIENTIFIC_FAIL
                   (Exploratory Notch Slit w=1 um)                                                 (Rejected: Artificial notch compliance K0=75.47)
-----------------------------------------------------------------------------------------------------------------------
1398865.mmaster02  Mode-I Sharp Seam Nominal 1%      71,320 / 70,846         10h 45m    10h 20m    TECHNICAL_TERMINATION
                   (Initial 1.0% Production Solve)                                                 (Aborted at default dt_min=1e-9 limit)
-----------------------------------------------------------------------------------------------------------------------
1399632.mmaster02  Mode-I Sharp Seam Nominal 1%      71,320 / 70,846         35h 08m    34h 03m    QUANTITATIVE_REPRODUCTION_FAILED
                   (Full Convergence dt_min=1e-14)                                                 (Over-refinement compliance shift, F_peak=0.4782 kN)
-----------------------------------------------------------------------------------------------------------------------
1403681.mmaster02  Mode-I Fixed Ref Diag A           15,192 / 15,522         06h 46m    06h 45m    SCIENTIFICALLY_ACCEPTED
                   (Fixed Mesh + UEL 5abf77b5...)                                                  (F_peak=0.7578 kN, K0=137.9455 kN/mm, Exit 0)
-----------------------------------------------------------------------------------------------------------------------
1403682.mmaster02  Mode-I Fixed Ref Diag B           15,192 / 15,522         06h 55m    06h 54m    SCIENTIFICALLY_ACCEPTED
                   (Fixed Mesh + UEL c540b5...)                                                    (F_peak=0.7578 kN, K0=137.9455 kN/mm, Exit 0)
=======================================================================================================================
```

> **Node Count Standardization**: Prior references to "71,490 nodes" in intermediate draft tables arose from confusing the preliminary exploratory blunt-notch mesh node count with the zero-gap sharp seam mesh. The exact, authoritative count of the 71,320-element mesh directly extracted from input decks is **70,845 finite element mesh nodes + 1 reference point node (Node 999999) = 70,846 total node definitions**. All prior erroneous 71,490 labels are formally marked as `RETIRED_NODE_COUNT_REPORTING_ERROR`.

---

## 2. Cryptographic Checksums of Primary Input Decks & Routines

```text
File Name                  Role / Case                   SHA-256 Checksum                                                   Provenance Status
-------------------------------------------------------------------------------------------------------------------------------------------------------
PK_MODE1_STANDARD_PFM.inp  Task-3 Fixed Reference Run    c1773707d2f12fb8bfe1324ac6be47d28d1fd6b06c4c3780cd98e9527fa7ef82  RUNTIME_SOURCE_PROVEN (Job 1398090)
f42_mixed_uel.for          Task-3 Fixed Reference UEL    ed1586d6427a4b1a01d99f7e219891ec7be9fe911e066d9360724942e7d27720  RUNTIME_SOURCE_PROVEN (Job 1398090)
PK_MODE1_PROPOSED_PFM.inp  Task-5 Nominal 1% Adaptive    cb01d04105257099fd248bd713578b5c0499a4f58639996d55238dfb8c9e3bdf  RUNTIME_SOURCE_PROVEN (Job 1399632)
f42_mixed_uel.for          Task-5 Nominal 1% UEL         5abf77b570c67283f082e02d8ba2fd0111db843ad9c4cd3501eb9aaaf149dfdd  RUNTIME_SOURCE_PROVEN (Job 1399632)
```

---

## 3. Reconciled Gate-6 Factorial & Isolation Control Jobs Ledger

Following complete terminal qualification of all 24-hour PBS jobs on September 10, 2026, every job's identity is proven from its actual executed `.inp` deck, Fortran source, and scratch execution path. Every previously conflicting textual label is formally marked as `SUPERSEDED_JOB_ROLE_LABEL_ERROR`.

Physical deck byte inspections confirmed that **UNSYMM is ON across all isolation controls (Cases 72b–75b)**, matching parent Case 61.

> **Case 71b Labeling Reconciliation**: Job `1403813.mmaster02` (`PK_M1_DECOMP_COMPANION_EXT`) is the **71,320-element Case-71b $K_{01}$ companion-only factorial extension** ($70,846$ nodes, $69,443$ quads, $1,877$ tris), **not** a 15k mesh. Its exact submitted deck is `PK_M1_DECOMP_COMPANION_EXT.inp` (SHA-256: `80e723976aa5fc018f9afaca4898d9466b1c7e6d1d4bcc620c7093a801d694af`).

```text
============================================================================================================================================================================================
CANONICAL RECONCILED JOB-ROLE & ISOLATION LEDGER (GATE-6 DECOMPOSITION & ISOLATION CONTROLS)
============================================================================================================================================================================================
PBS ID            Actual Job_Name         Deck SHA (8)  Source SHA (8)  Scientific Case  UNSYMM  Companion Formulation / Scope      Terminal Achieved Disp & K0  Mapping Status
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
1403818.mmaster02 PK_M1_DEC_M_PH_EXT      b1e51a39      5b381dd5        Case 69b (K00)   NO      None (No companion mesh)           u=0.001000 mm, K0=138.021015 FULL_INTERVAL_QUALIFIED
1403819.mmaster02 PK_M1_DEC_UNSYM_EXT     5368458e      5b381dd5        Case 70b (K10)   YES     None (No companion mesh)           u=0.001000 mm, K0=138.021015 FULL_INTERVAL_QUALIFIED
1403813.mmaster02 PK_M1_DEC_COMP_EXT      80e72397      5b381dd5        Case 71b (K01)   NO      71,320 CPE4+CPE3 (*Elastic)        u=0.001000 mm, K0=138.021015 FULL_INTERVAL_QUALIFIED
1403698.mmaster02 PK_M1_FROZEN_INTACT_NOM a396af8f      5b381dd5        Case 61  (K11)   YES     71,320 CPE4+CPE3 (UMAT stub)       u=0.001000 mm, K0=122.599592 FULL_INTERVAL_QUALIFIED
1403825.mmaster02 PK_M1_DEC_Z_EXT         a396af8f      f858d3b6        Case 72b (Twin)  YES     Explicit-zero UMAT (DDSDDE=0)      u=0.001000 mm, K0=122.599592 FULL_INTERVAL_QUALIFIED
1403826.mmaster02 PK_M1_DEC_B_EXT         6955b8f1      f858d3b6        Case 73b (Twin)  YES     Native *ELASTIC (near-zero damp)   u=0.001000 mm, K0=122.599592 FULL_INTERVAL_QUALIFIED
1403827.mmaster02 PK_M1_DEC_4_EXT         0b71415b      f858d3b6        Case 74b (Twin)  YES     Native *ELASTIC, 69,443 CPE4 only  u=0.001000 mm, K0=122.599592 FULL_INTERVAL_QUALIFIED
1403828.mmaster02 PK_M1_DEC_3_EXT         8ee6b6ee      f858d3b6        Case 75b (Twin)  YES     Native *ELASTIC, 1,877 CPE3 only   u=0.001000 mm, K0=122.599592 FULL_INTERVAL_QUALIFIED
1404051.mmaster02 PK_M1_SPARSE_N1_TIP     f6cf15eb      f858d3b6        Case 76 (N1_TIP) YES     1 CPE3 near crack tip (0.49, 0.49) u=0.001000 mm, K0=122.599592 FULL_INTERVAL_QUALIFIED
1404052.mmaster02 PK_M1_SPARSE_N1_FAR     173f565e      f858d3b6        Case 77 (N1_FAR) YES     1 CPE3 far-field (0.026, 0.016)    u=0.001000 mm, K0=122.599592 FULL_INTERVAL_QUALIFIED
1404053.mmaster02 PK_M1_SPARSE_N10_DIST   9cf10f8b      f858d3b6        Case 78 (N10)    YES     10 CPE3 distributed (FPS)          u=0.001000 mm, K0=122.599592 FULL_INTERVAL_QUALIFIED
1404054.mmaster02 PK_M1_SPARSE_N100_DIST  e5666f22      f858d3b6        Case 79 (N100)   YES     100 CPE3 distributed (FPS)         u=0.001000 mm, K0=122.599592 FULL_INTERVAL_QUALIFIED
1404068.mmaster02 PK_M1_FROZ_15K          81291ddc      5b381dd5        Case 80 (15k_AD) YES     15,396 CPE4+CPE3 (Frozen-Intact)   u=0.001000 mm, K0=138.043928 FULL_INTERVAL_QUALIFIED
1404162.mmaster02 PK_M1_FROZ_17K          00cf839c      5b381dd5        Case 81 (17k_AD) YES     17,687 CPE4+CPE3 (Frozen-Intact)   u=0.001000 mm, K0=124.729718 FULL_INTERVAL_QUALIFIED
============================================================================================================================================================================================
```

### 3.1 Interval Completeness & Factorial Classification
- All active jobs have completed to 100% full interval ($2,000 / 2,000$ increments, $u = 0.001000\,\text{mm}$, Exit status 0).
- Authoritative full-interval factorial status:
  * **Factorial Status**: **`FACTORIAL_FULL_INTERVAL_QUALIFIED`**
  * **Cell Status**: **`FACTORIAL_4_OF_4_FULL_INTERVAL_CELLS_QUALIFIED`** (Cases 61, 69b, 70b, 71b fully qualified at $u = 0.001000\,\text{mm}$)
- Verified metrics across the full interval ($u \in [0, 0.001000]\,\text{mm}$, $N=2000$ points, $R^2 = 1.00000000$):
  * $K_{00} = 138.021015\,\text{kN/mm}$ (Case 69b)
  * $K_{10} = 138.021015\,\text{kN/mm}$ (Case 70b)
  * $K_{01} = 138.021015\,\text{kN/mm}$ (Case 71b)
  * $K_{11} = 122.599592\,\text{kN/mm}$ (Case 61)
  * $\Delta K_{\text{int}} = K_{11} - K_{10} - K_{01} + K_{00} = -15.421423\,\text{kN/mm}$ ($-11.173243\%$).

### 3.2 Epistemic Reconciliation of the Fixed-Reference Counterexample
- The fixed-reference deck `PK_MODE1_STANDARD_PFM.inp` contains `*USER ELEMENT, ..., UNSYMM` active on both U1 and U2, and exactly 15,192 co-located companion `CPE4` elements participating in DOFs 1 and 2 assembly.
- In the fixed reference, this configuration produces $K_0 = 137.945520\,\text{kN/mm}$ (no stiffness drop).
- Case 80 ($15,396$ elements, `1404068.mmaster02`): produces $K_0 = 138.043928\,\text{kN/mm}$ ($\Delta K_0 = +0.098408\,\text{kN/mm}$ / $+0.0713\%$, classified as `CLOSE_AGREEMENT_WITH_CANONICAL_REFERENCE`).
- Consequently, `UNSYMM=ON` + companion layer is **NOT** a sufficient condition across arbitrary discretizations.
- Authoritative classifications:
  * `UNSYMM_COMPANION_STIFFNESS_SHIFT_VERIFIED_ONLY_IN_TESTED_71320_ADAPTIVE_MESH_CONTEXT`
  * `FIXED_REFERENCE_IS_COUNTEREXAMPLE_TO_GENERAL_UNSYMM_X_COMPANION_TRIGGER`
  * `INTERNAL_MECHANISM_NOT_YET_ESTABLISHED`

### 3.3 Authoritative Canonical V2 Extraction (Cases 72b–75b)
- **Authoritative Extractor**: `canonical_gate6_extractor.py` (SHA-256: `EB04E132EA97BD77C77636F2833780317E4295292F07A5DA6B19DA63A74E82B7`).
- **Interval**: Full terminal interval $0 \le u \le 0.001000\,\text{mm}$ ($N=2,000$ points).
- **Exact Results**:
  * Case 72b (`1403825`): $K_0 = 122.599592\,\text{kN/mm}$, $b = 3.637979\times 10^{-12}\,\text{kN}$, $R^2 = 1.00000000$
  * Case 73b (`1403826`): $K_0 = 122.599592\,\text{kN/mm}$, $b = 3.637979\times 10^{-12}\,\text{kN}$, $R^2 = 1.00000000$
  * Case 74b (`1403827`): $K_0 = 122.599592\,\text{kN/mm}$, $b = 3.637979\times 10^{-12}\,\text{kN}$, $R^2 = 1.00000000$
  * Case 75b (`1403828`): $K_0 = 122.599592\,\text{kN/mm}$, $b = 3.637979\times 10^{-12}\,\text{kN}$, $R^2 = 1.00000000$
- **Epistemic Rectification**:
  * Cases 74b and 75b vary only the companion layer (`CPE4` vs `CPE3`), while retaining the underlying mixed quad/tri UEL mesh ($69,443$ quads + $1,877$ tris).
  * Consequently, they rule out companion element family as the driver (`COMPANION_CPE3_VS_CPE4_FAMILY_NOT_REQUIRED_FOR_LOW_EARLY_STIFFNESS`).
  * They do **NOT** isolate the underlying mixed mesh context (`UNDERLYING_MIXED_QUAD_TRI_MESH_CONTEXT_NOT_YET_ISOLATED`), nor establish the internal matrix solver mechanism (`INTERNAL_MECHANISM_NOT_YET_ESTABLISHED`).

### 3.4 Case 80 Intermediate Adaptive Full-Interval Qualification
- **Job Provenance**: PBS ID `1404068.mmaster02` (Exit status 0, walltime 03h 09m 45s).
- **Canonical V2 Quantitative Metrics ($N = 2,000$ points, $0 \le u \le 0.001000\,\text{mm}$)**:
  * Full Interval: `FROZEN_K0` = $\mathbf{138.043928\,\text{kN/mm}}$, $b = 2.507960\times 10^{-12}\,\text{kN}$, $R^2 = 1.00000000$.
  * Final Endpoint: $u_{\max} = 0.001000\,\text{mm}$, $RF_2(u_{\max}) = 0.13804393\,\text{kN}$.
  * External Work Integral: $W = 6.902196\times 10^{-5}\,\text{kN}\cdot\text{mm}$ ($69.021964\,\mu\text{J}$).
- **Classification**: Confirmed **`CASE80_15396_CONTROLLED_MESH_HIGH_STIFFNESS_BRANCH`** and **`MESH_CONTEXT_FACTOR_ISOLATION_VERIFIED`**.

### 3.5 Case 81 Diagnostic Full-Interval Qualification (`1404162.mmaster02`)
- **Job Provenance**: PBS ID `1404162.mmaster02` (Exit status 0, walltime 02h 54m 51s, host `mnode097`).
- **Factor Isolation**: Input deck `PK_M1_FROZEN_INTACT_17K.inp` constructed under `MESH17687_FACTOR_ISOLATION_VERIFIED` ($17,687$ elements: $17,196$ quads + $491$ tris, $17,688$ nodes).
- **Canonical V2 Quantitative Metrics ($N = 2,000$ points, $0 \le u \le 0.001000\,\text{mm}$)**:
  * Full Interval Initial Fitted $K_0$: $\mathbf{124.729718\,\text{kN/mm}}$ ($R^2 = 1.00000000, b = 3.637979 \times 10^{-12}\,\text{kN}$).
  * Final Endpoint: $u_{\max} = 0.001000\,\text{mm}$, $RF_2(u_{\max}) = 0.12472972\,\text{kN}$.
  * External Work Integral: $W = 6.236486\times 10^{-5}\,\text{kN}\cdot\text{mm}$ ($62.364859\,\mu\text{J}$).
- **Formal Epistemic Classifications**:
  * **`CASE81_17687_FULL_INTERVAL_QUALIFIED`**
  * **`CASE81_INTERMEDIATE_BRANCH_VERIFIED_IN_TESTED_17687_MESH_CONTEXT`**
  * **`CONFIRMED_INTERMEDIATE_BRANCH_DISTINCT_FROM_BOTH_122_AND_138`**

---

## 4. Storage Remediation Status

- **PBS Offload Worker Job**: `1403851.mmaster02` (`HOME_OFFLOAD_M1_CONT`, host `mnode097`, Exit status `0`, Completed).
- **Exact Integer-Byte Storage Reconciliation**:
  * Total Verified Files: **10 / 10 targets**.
  * Exact Reclaimed Storage: **$1{,}664{,}172{,}974{,}560\,\text{bytes}$**.
  * Decimal TB: **$1.664172974560\,\text{TB}$**.
  * Binary TiB: **$1.513556503196\,\text{TiB}$**.
  * Error Classifications:
    - Prior interim 9-file total ($1,476,830,402,528\,\text{bytes}$) marked `RETIRED_STORAGE_TOTAL_REPORTING_ERROR`.
    - Prior approximate rounded representation ("1.446 TB") marked `RETIRED_ROUNDED_STORAGE_TOTAL_ERROR`.
- **Remaining `/home/pr21vyci` Footprint Verification**:
  * Allocated Block Size (`du -sh`): **$951\,\text{GB}$** ($996{,}201{,}076\,\text{KB}$ allocated on NFS mount `mnfs:/home`).
  * Free Space Available: $> 6.4\,\text{TB}$ ($69\%$ filesystem utilization).
  * Storage footprint successfully reduced below the $1\,\text{TB}$ threshold.
- **Threshold Check & Notification Epistemology Audit**:
  * Classification: `OFFLOAD_GT_1TB_VERIFIED` (Threshold $> 1.0\,\text{TB}$ strictly satisfied).
  * Transmission Timestamp (UTC): `2026-09-09T16:21:22.409884+00:00`.
  * Channel: Established Telegram Bot Dispatcher (`api.telegram.org/bot.../sendMessage`).
  * Message ID: `1115` (`chat_id`: `5438966389`, `success`: `true`).
  * Endpoint Audit Result: `chat_id: 5438966389` is the user's personal project notification endpoint configured in `~/.config/hpc-notify/telegram.env`, not the official URZ/HPC helpdesk ticket system.
  * Formal Classifications:
    - `USER_TELEGRAM_STORAGE_NOTICE_SENT` (Message ID: `1115`)
    - `HPC_SUPPORT_NOTICE_NOT_YET_SENT`
    - `HPC_SUPPORT_RECIPIENT_UNRESOLVED`

---

## 5. Definitive Evidence Hierarchy

- **VERIFIED**:
  1. Fixed-reference source-lineage parity (Jobs 1398090, 1403681, 1403682 produce bitwise identical curves, $L_2 = 0.0\,\text{kN}$, $K_0=137.945520\,\text{kN/mm}$).
  2. Fixed-reference counterexample: Deck `PK_MODE1_STANDARD_PFM.inp` contains UNSYMM=ON and 15,192 co-located companion elements, yet exhibits no compliance drop ($K_0 = 137.945520\,\text{kN/mm}$).
  3. Adaptive continuum elastic parity: Job `1403684` yields $K_0 = 137.973464\,\text{kN/mm}$ (within $0.125\%$ of fixed reference).
  4. Full-interval UNSYMM $\times$ companion interaction: On the full terminal interval ($u \le 0.001000\,\text{mm}$), the low stiffness ($122.60\,\text{kN/mm}$) appears only when UNSYMM is coupled with companion elements on the tested 71,320-element mesh ($\Delta K_{\text{int}} = -15.421423\,\text{kN/mm}$, $-11.173243\%$).
  5. Full-interval isolation-control invariance across Cases 72b–75b ($K_0 = 122.599592\,\text{kN/mm}$, $0.000000\%$ difference, $N=2000$).
  6. Case 80 intermediate adaptive full-interval qualification ($15,396$ elements, $u \le 0.001000\,\text{mm}$, $N=2000$): confirms high-stiffness branch (`FROZEN_K0` = $138.043928\,\text{kN/mm}$, $R^2 = 1.00000000$, final RF = $0.13804393\,\text{kN}$).
  7. Case 81 intermediate adaptive full-interval qualification ($17,687$ elements, $u \le 0.001000\,\text{mm}$, $N=2000$): linear fit $K_0 = \mathbf{124.729718\,\text{kN/mm}}$ ($R^2 = 1.00000000$, `CASE81_INTERMEDIATE_BRANCH_VERIFIED_IN_TESTED_17687_MESH_CONTEXT`).
  8. Reclaimed exact $1{,}664{,}172{,}974{,}560\,\text{bytes}$ ($1.664173\,\text{TB}$ / $1.513557\,\text{TiB}$) via cryptographic verification and symlinking; personal Telegram notice transmitted (`USER_TELEGRAM_STORAGE_NOTICE_SENT`).
- **INFERRED BUT NOT PROVEN**:
  1. Mesh context transition: Stiffness drop scales non-linearly with refinement between 15k and 71k elements (`FROZEN_FORMULATION_RESPONSE_DIFFERS_BETWEEN_TESTED_MESH_CONTEXTS`, `DESCRIPTIVE_ASSOCIATION_NOT_CAUSAL_PROOF`).
- **UNRESOLVED**:
  1. Internal Abaqus assembly mechanism: Exact equation solver routine causing non-symmetric companion coupling on graded meshes remains `INTERNAL_MECHANISM_NOT_YET_ESTABLISHED`.
  2. Cause of 1.0% adaptive over-refinement ($71,320$ elements vs literature $\sim 13,941$) (`GATE5_UNRESOLVED_DUE_TO_INSUFFICIENT_PUBLISHED_REMESHING_DETAILS`).
  3. Official URZ/HPC support email/ticket endpoint (`HPC_SUPPORT_RECIPIENT_UNRESOLVED`).
- **Project Scope Restriction**: Mode-II and State Transfer remain strictly PAUSED.

---

## 6. Post-Handoff Mode-I Resolution Extension & General Abaqus Parser Rule Verification

### 6.1 Extraction Job Provenance Reconciliation
- **Job 1404307.mmaster02** (`SETS_EXTRACT`, Exit status `1`, walltime 03m 18s): Preliminary ODB extraction attempt; script encountered node iteration type error on un-nested node sequences.
- **Job 1404311.mmaster02** (`SETS_EXTRACT`, Exit status `1`, walltime 00m 01s): Interim extraction attempt; failed with `TypeError: 'OdbMeshNode' object is not iterable` at line 42.
- **Job 1404312.mmaster02** (`SETS_EXTRACT`, Exit status `0`, walltime 00m 04s, host `mnode097`):
  * **Authoritative Production Extraction Job**: Successfully extracted parsed nodeSet memberships across all 5 benchmark ODBs and full 150-node bottom-edge displacement/reaction-force profiles.
  * Script: `extract_boundary_sets_and_displacement_profile.py` (SHA-256: `023de18fd622f3d8f2aeb77dd57ba3aceb977ce00a27ae5576bf84709e18bd6c`).
  * Produced Artifacts: `/scratch9/pr21vyci/test_wrapped_case61/parsed_nsets_audit.json`, `/scratch9/pr21vyci/test_wrapped_case61/bottom_edge_comparison.json`, `/scratch9/pr21vyci/test_wrapped_case61/boundary_sets_extraction.log`.
  * Verified ODB Memberships:
    - Case 61 (Defective Frozen Nom1): `N_BOTTOM` = 16 (Nodes 1..16), `N_TOP` = 16 (Nodes 73..88), `N_PIN` = 1.
    - Case 76 (Defective Sparse N1 Tip): `N_BOTTOM` = 16, `N_TOP` = 16, `N_PIN` = 1.
    - Job 1399632 (Defective Full Fracture): `N_BOTTOM` = 16, `N_TOP` = 16, `N_PIN` = 1.
    - Job 1404261 (Corrected Wrapped Sparse): `N_BOTTOM` = 150, `N_TOP` = 210, `N_PIN` = 1.
    - Job 1404262 (Corrected Wrapped Frozen Nom1): `N_BOTTOM` = 150, `N_TOP` = 210, `N_PIN` = 1.

### 6.2 Controlled Abaqus 2023 Parser Limit Verification (Job 1404318.mmaster02)
- **Job Provenance**: PBS ID `1404318.mmaster02` (`PARSER_TEST`, host `mnode097`, queue `entry_imfdfkmq` -> `normal_imfdfkmq`, Exit status `0`, completed 2026-09-10T10:35:14+02:00).
- **Controlled Test Design**: Minimal dummy model retaining 30 nodes via 30 1-node MASS elements (no UEL, no phase field, no remeshing):
  * `SET_20_ITEMS_SHORT`: 20 items on 1 line (<80 characters, >16 items). Result: Exactly 16 nodes parsed (1..16). Nodes 17..20 deleted by `pre`. Emitted compiler warning: `One or more data lines contain more than 16 items... The extra items are deleted.`
  * `SET_10_ITEMS_120_CHARS`: 10 items on 1 line padded to 120 characters (>80 chars, <=16 items). Result: All 10 nodes parsed (0 warnings).
  * `SET_10_ITEMS_300_CHARS`: 10 items on 1 line padded to 300 characters (>256 chars, <=16 items). Result: All 10 nodes parsed (`Line #40 has been truncated` at column 256).
  * `SET_30_ITEMS_UNWRAPPED`: 30 items on 1 line (~150 chars, >16 items). Result: Exactly 16 nodes parsed (1..16). Nodes 17..30 deleted by `pre`.
  * `SET_30_ITEMS_WRAPPED`: 30 items wrapped at 16 per line (Line 1: 16 items, Line 2: 14 items). Result: All 30 nodes parsed (1..30) with 0 warnings.
- **Formal General Conclusion**: Promoted from deck-specific observation to **`GENERAL_ABAQUS_NSET_16_ENTRY_PARSER_TRUNCATION_RULE_VERIFIED`**.

### 6.3 Full-Fracture Requalification Solver Status (Job 1404306.mmaster02)
- **Job Provenance**: PBS ID `1404306.mmaster02` (`PK_M1_NOM1_SOLVE`, queue `normal_imfdfkmq`, compute node `mnode097.cluster`).
- **Pre-Submission Datacheck**: Job `1404302.mmaster02` (Exit status `0`, 0 truncation warnings, 150 bottom nodes parsed, 210 top nodes parsed).
- **Execution Architecture**: Single-rank serial, 1 CPU, 32 GB RAM, walltime limit 336:00:00.
- **Active Telemetry**: Increment 336+ reached ($u = 0.000840\,\text{mm}$), solving cleanly with 3 equilibrium iterations per increment, 0 cutbacks.
- **Initial Stiffness**: $K_0 = \mathbf{138.02102\,\text{kN/mm}}$ confirmed on Increments 1 to 8. Left completely undisturbed on `mnode097`.

### 6.4 Priority B Primary-Source Literature Audit & Area/Density Balance
- **Publication Context Classification**:
  * Listing 1: `GENERIC_METHOD_LISTING` (Python template specifying `errorTarget=1.0`).
  * Section 4.1 (Reported ~13,941-element Mode-I mesh): `SAME_MODE1_REPORTED_MESH_CONTEXT` (`errorTarget` is unstated in the text; specifies $h_{\max} = 0.02\,\text{mm}$, $h_{\min} = 0.001\,\text{mm}$, initial pre-analysis load $\Delta u_1 = 10^{-3}$ for 500 incs, $\Delta u_2 = 5 \times 10^{-4}$ for 1000 incs).
  * Section 4.1.1 & 4.1.2: `DIFFERENT_SECTION_OR_CASE` ($l_0 = 0.01\,\text{mm}$ sensitivity study; `errorTarget=5` selected from $\{2, 5, 10, 20\}$).
  * Section 4.4: `DIFFERENT_SECTION_OR_CASE` (L-shaped panel; `errorTarget=3.5`).
- **Region-Wise Area/Density Balance ($71,320$ vs $15,396$ finite elements)**:
  * Crack-tip region ($r \le 0.05\,\text{mm}$): Area = $0.007786\,\text{mm}^2$ ($0.78\%$ of domain). Surplus = **$335\text{ elements}$** ($0.61\%$ of total surplus). $h_{\text{eff}} = 1.848\,\mu\text{m}$ vs $2.001\,\mu\text{m}$ ($7.6\%$ delta).
  * Notch/corridor region ($|y - 0.5| < 0.20\,\text{mm}$, $r > 0.05\,\text{mm}$): Area = $0.3888\,\text{mm}^2$ ($38.9\%$ of domain). Surplus = **$26,459\text{ elements}$** ($48.57\%$). Density multiplier = $4.652\times$ (scaling prediction $(7.324/3.396)^2 = 4.651\times$, residual discrepancy $0.02\%$).
  * Far-field bulk ($|y - 0.5| \ge 0.20\,\text{mm}$): Area = $0.5954\,\text{mm}^2$ ($59.5\%$ of domain). Surplus = **$27,686\text{ elements}$** ($50.82\%$). Density multiplier = $5.798\times$ (scaling prediction $(10.158/4.219)^2 = 5.797\times$, residual discrepancy $0.02\%$).
  * Master Classification: **`OUR_1PCT_SURPLUS_ELEMENTS_ARE_PREDOMINANTLY_FAR_FIELD_RELATIVE_TO_OUR_2PCT_MESH`** ($99.39\%$ of surplus elements reside in non-critical corridor and bulk).

### 6.5 Abaqus Software Release Sensitivity Audit (Gate 5 / Task 4)
- **Anti-Deviation Card**: `docs/cards/ANTI_DEVIATION_CARD_GATE5_ABAQUS_2022_VS_2023.md`.
- **Installed HPC Cluster Releases**:
  * Abaqus 2023: Build `2022_09_28-20.11.55 183150` (Site ID `200000000053187`).
  * Abaqus 2022: Build `2021_09_15-19.57.30 176069` (Site ID `200000000053187`).
  * Abaqus 2021: Build `2024_06_17-08.41.59 168613` (Site ID `200000000053187`).
- **Cluster Jobs Executed**:
  1. **Job 1404363.mmaster02** (`ABQ_VER_INV`, compute node `mnode097`, queue `normal_imfdfkmq` via `entry_imfdfkmq`, Exit `0`). Captured exact command line executables and build strings.
  2. **Job 1404364.mmaster02** (`ABQ22_REMESH`, compute node `mnode097`, Abaqus 2022, Exit `0`, walltime 47s).
     - Coarse pre-analysis datacheck: PASSED cleanly (Exit 0).
     - Native remeshing at `errorTarget = 1.0%`: Generated **58,679 finite elements** (57,102 quads, 1,577 tris) and 58,316 nodes.
     - Ratio to published (13,941): **$4.209\times$** ($+321\%$).
     - Output Deck SHA-256: `58b6eb0142fbf855b73e74f38233eddcdcec48e8a52f21e709855f1a0f4474fd`.
  3. **Job 1404365.mmaster02** (`ABQ22_2PCT`, compute node `mnode097`, Abaqus 2022, Exit `0`, walltime 39s).
     - Native remeshing at `errorTarget = 2.0%`: Generated **15,396 finite elements** (14,963 quads, 433 tris) and 15,414 nodes.
     - Ratio to published (13,941): **$1.104\times$** ($+10.4\%$).
     - Output Deck SHA-256: `1b9dcb340b20c3b28ff854f6cce8f6ab2d52d1b8ceb97a58c312493a2beec9e2`.
- **Topological Comparison & Release Identity Check**:
  * Between Abaqus 2022 and 2023 at `errorTarget = 2.0%`:
    - Maximum Node Coordinate Difference: $\mathbf{0.00 \times 10^0\,\text{mm}}$ across all 15,414 nodes.
    - Element Connectivity Differences: $\mathbf{0}$ across all 15,396 elements.
    - Verdict: **`EXACT_IDENTICAL`**.
  * Between Abaqus 2022 and 2023 at `errorTarget = 1.0%`:
    - Both releases produce dense fine meshes in the 58k–71k regime (2022: 58,679 elems; 2023: 71,320 elems).
    - Neither release produces anything near 13,941 elements.
- **Falsification Verdict**:
  * Promoted to **`ABAQUS_RELEASE_DEPENDENCE_RULED_OUT_FOR_2022_VS_2023`**.
  * Confirms that Dassault's adaptive remeshing engine is structurally invariant across 2022 and 2023; the 13,941 discrepancy is not explained by software release.

- **Epistemic Classifications Retained**:
  * `PRIORITY_A_ROOT_CAUSE_VERIFIED_AT_BOUNDARY_SET_AND_FROZEN_RESPONSE_LEVEL`
  * `PRIORITY_A_FULL_FRACTURE_REQUALIFICATION_RUNNING`
  * `ELEMENT_COUNT_PROXIMITY_NOT_PARAMETER_IDENTITY`
  * `LITERATURE_EFFECTIVE_ERROR_TARGET_NOT_ESTABLISHED`
  * `GATE5_REPRODUCTION_DISCREPANCY_RESOLUTION_ACTIVE`
  * `ABAQUS_RELEASE_DEPENDENCE_RULED_OUT_FOR_2022_VS_2023`
  * `FACTORIAL_UNSYMM_X_COMPANION_CAUSAL_INTERACTION` -> **`RETRACTED`**

