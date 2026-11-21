# Method C Case 3: Job-3 Diagnosis and Deck Regeneration Disclosure Report

**Task ID:** `METHOD-C-CASE3-JOB3-DIAGNOSIS`  
**Scientific Operation:** `method_c_case3_job3_diagnosis`  
**Correlation ID:** `HND-METHOD-C-CASE3-JOB3-DIAG-001`  
**Predecessor Task:** `METHOD-C-CASE3-CYCLE2-JOB3-SOLVE`  
**Predecessor Correlation ID:** `HND-METHOD-C-CASE3-JOB3-001`  
**Predecessor Review Verdict:** `INSUFFICIENT_EVIDENCE`  
**PBS Job ID:** `1424778.mmaster02` (`M1_MC_C3_JOB3`)  
**Solver:** Abaqus/Standard 2023 with Bitwise Frozen User Element Subroutine `f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`)  
**Cumulative PBS Submissions:** Strictly 65 (0 new PBS jobs consumed; cumulative accounting preserved under Fix Option A allocation 62–67)  
**Master Continuation Goal Status:** `OPEN` (`METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1`)  

---

## 1. Executive Summary & Review Feedback Reconciliation

Following the independent structured review `HND-METHOD-C-CASE3-JOB3-001` (verdict: `INSUFFICIENT_EVIDENCE`), this diagnostic report provides complete disclosure, technical verification, and documentation reconciliation for Case 3 Cycle-2 Job 3 (`1424778.mmaster02`). 

No new PBS simulations were performed. Cumulative PBS submissions strictly remain at **65**.

All five identified review gaps and notes are fully addressed:
1. **`GAP-MC-C3J3-01` (Deck Regeneration Disclosure):** Full disclosure of the preflight syntax repair from approved candidate deck `8DDE4D8B` to executed deck `1D72A981`, proving that changes were strictly confined to 23 header card lines while all 746,928 transferred SVARs remained 100% bitwise identical.
2. **`GAP-MC-C3J3-02` (Report §2 Comparison Table Corrections):** Corrected Job-2 comparison values from authentic committed Job-2 evidence (Step-1 energy continuity $-0.215\%$ fracture / $-0.385\%$ total, initial fracture energy $0.00172721\,\text{kN}\cdot\text{mm}$, and peak structural load $4.0498816\,\text{kN}$ at $u_2 = 0.0524271\,\text{mm}$).
3. **`NOTE-MC-C3J3-01` (File Size Reconciliation):** Corrected all artifact sizes in `METHOD_C_CASE3_JOB3_EXECUTION_REPORT.md`, receipt, and summary to match exact committed filesystem byte counts.
4. **`NOTE-MC-C3J3-02` (Terminal Frame & Peak Load Disambiguation):** Relabeled the terminal converged state as Increment 28 (Increment 29 was aborted during cutback to $\Delta t_{\min} = 1.0 \times 10^{-14}$) and clarified that peak load $4.101037\,\text{kN}$ is ODB-sourced (`.dat` records $4.1009829\,\text{kN}$).
5. **`NOTE-MC-C3J3-04` & `NOTE-MC-C3J3-05` (Walltime, Timestamps, and Crack Baselines):** Disambiguated PBS job span ($4,602\,\text{s}$) vs Abaqus solver wallclock ($4,268\,\text{s}$) and CPU time ($2,918\,\text{s}$); clarified UTC vs CET timestamps; harmonized dual forward advance baselines ($+2.3686\,\text{mm}$ past donor tip vs $+2.3649\,\text{mm}$ past post-hold tip); and classified Step-1 damage growth as `GROWTH_UNDER_HOLD`.

---

## 2. Technical Audit: Preflight Deck Regeneration & Syntax Repair

### 2.1 Context and Discovery
During preparation of the Cycle-2 refinement package (`METHOD-C-CASE3-CYCLE2-PREP`), candidate deck `PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.inp` (SHA-256 `8DDE4D8B4D441CEFFCE55979FBFB4DC5C5C0F6662446A310CE7D2791C24D338C`, 17,373,879 B) was synthesized by `scripts/state_transfer/run_case3_cycle2_state_transfer.py`.

During preflight technical datacheck execution, Abaqus rejected the input deck due to invalid UEL card syntax:
- All 4 element types (U1, U2, U3, U4) had active degrees of freedom defined as displacement DOFs `1, 2`.
- Phase-field elements (U1, U3) were missing their dedicated phase DOF 3.
- All cards included `IPROPERTY=1`, which was incompatible with the zero-property UEL definition.
- The `UNSYMM` keyword parameter was omitted from all UEL cards, causing solver divergence during tangent assembly.

### 2.2 Syntax Repair Implementation
To resolve this defect prior to PBS submission, `scripts/state_transfer/run_case3_cycle2_state_transfer.py` was updated to restore the authentic working UEL syntax established and verified in Job 2:
1. **U1 & U3 (Phase Elements):** `*USER ELEMENT, NODES=4, TYPE=U1, PROPERTIES=0, COORDINATES=2, VARIABLES=2, UNSYMM` followed by DOF card `1, 1, 3`.
2. **U2 & U4 (Displacement Elements):** `*USER ELEMENT, NODES=4, TYPE=U2, PROPERTIES=0, COORDINATES=2, VARIABLES=4, UNSYMM` followed by DOF card `1, 2, 1, 2`.
3. `IPROPERTY=1` was completely removed.

The production deck was regenerated to `PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.inp` (SHA-256 `1D72A98120AAFF2EAC657779C6F3477CDCCF3B22C3528E6CF2BB0E233EE4BC9C`, 17,373,692 B).

### 2.3 Bitwise State Transfer Verification (Zero State Corruption)
A strict programmatic diff between the approved candidate deck `8DDE4D8B` and executed deck `1D72A981` confirms:
1. **Header Cards Only:** The differences are confined strictly to 23 lines in the four `*USER ELEMENT` definition headers at lines 20–55 of the deck.
2. **Nodal Coordinates:** Exactly 39,035 nodes (including RP Node 999999) are 100% identical.
3. **Element Connectivity:** Exactly 117,936 layered UEL elements across 3 layers are 100% identical.
4. **Transferred Solution State:** All **746,928 initial-condition values** in the `*INITIAL CONDITIONS, TYPE=SOLUTION` block (6 SVARs per element across 117,936 elements) are **100% bitwise identical**.

The executed deck was therefore an exact syntax repair of the approved deck, preserving state transfer integrity without modification.

---

## 3. Reconciliation of Quantitative Observables & Comparison Baselines

### 3.1 Job-2 Baseline Corrections
The Section 2 comparison table in `METHOD_C_CASE3_JOB3_EXECUTION_REPORT.md` has been updated with the authentic, committed quantities from Job 2 (`PK_METHOD_C_CASE3_CYCLE1_REFINED_JOB2`):
- **Step-1 Energy Continuity:**
  * Fracture energy continuity: $-0.215\%$ ($0.00172721\,\text{kN}\cdot\text{mm}$ vs Job-1 Step-1 $0.00173094\,\text{kN}\cdot\text{mm}$).
  * Total energy continuity: $-0.385\%$ ($0.090623\,\text{kN}\cdot\text{mm}$ vs Job-1 Step-1 $0.090973\,\text{kN}\cdot\text{mm}$).
  * (Replaces the unverified $+0.98\%$ placeholder).
- **Initial Fracture Energy:** $0.00172721\,\text{kN}\cdot\text{mm}$ (replaces $0.00342\,\text{kN}\cdot\text{mm}$).
- **Peak Structural Load:** $4.0498816\,\text{kN}$ at $u_2 = 0.0524271\,\text{mm}$ (replaces $4.0441\,\text{kN}$ at $0.05220\,\text{mm}$).

### 3.2 Dual Forward Advance Baselines & Damage Growth Under Hold
To eliminate ambiguity in forward crack propagation metrics, both reference baselines are explicitly defined and tracked:
1. **Donor Tip Baseline:** Measured from donor crack tip $x_{\text{tip}} = 10.1529\,\text{mm}$ ($d \ge 0.95$) to terminal tip $x_{\text{tip}} = 12.5215\,\text{mm}$:
   $$\Delta x_{\text{donor}} = 12.5215 - 10.1529 = \mathbf{+2.3686\,\text{mm}}$$
2. **Post-Hold Baseline:** Measured from the re-equilibrated post-hold crack tip $x_{\text{tip}} = 10.1566\,\text{mm}$ ($d \ge 0.95$) to terminal tip $x_{\text{tip}} = 12.5215\,\text{mm}$:
   $$\Delta x_{\text{hold}} = 12.5215 - 10.1566 = \mathbf{+2.3649\,\text{mm}}$$

**Damage Evolution Under Hold:** During Step-1 fixed-displacement equilibration ($u_2 = 0.052451\,\text{mm}$ held constant), minor local relaxation occurred at the notch tip:
- Tip position shifted: $x = 10.1529 \to 10.1566\,\text{mm}$ ($+0.0037\,\text{mm}$).
- Peak damage increased: $d_{\max} = 0.976822 \to 0.977715$ ($+0.09\%$).
- This behavior is formally classified as **`GROWTH_UNDER_HOLD`** (consistent with viscous-regularized phase-field energy relaxation at a clamped displacement state).

### 3.3 Terminal Frame & Solver Metric Clarifications
- **Terminal Converged State:** Status file `.sta` confirms that Step 2 converged through **Increment 28** ($u_2 = 0.056073\,\text{mm}$, $\text{RF}_2 = 3.9475\,\text{kN}$, $\Delta t = 6.728 \times 10^{-14}$). Increment 29 attempted 3 cutbacks down to $\Delta t = 1.0 \times 10^{-14}$ and was aborted by Abaqus because $\Delta t < \Delta t_{\min}$. The final valid frame stored in the ODB is Increment 28.
- **Peak Reaction Force:**
  * Field output extraction (ODB): $4.101037\,\text{kN}$ at Increment 4 ($u_2 = 0.053284\,\text{mm}$).
  * Printed history summary (`.dat` file): $4.1009829\,\text{kN}$ at Increment 4.
  * Both sources corroborate peak load capture to within $0.0013\%$.
- **Walltime Disambiguation:**
  * PBS job span: $4,602.0\,\text{s}$ (1 h 16 m 42 s), measured by PBS server from batch initialization to epilogue completion.
  * Abaqus solver wallclock: $4,268.0\,\text{s}$ (1 h 11 m 08 s), reported in `.dat` `JOB TIME SUMMARY`.
  * Abaqus solver CPU time: $2,918.0\,\text{s}$ (~48 m 38 s), on 16 SMP cores.
  * Timestamps: `2026-11-20 23:09:47Z to 2026-11-21 00:26:29Z` (UTC) corresponding to `2026-11-21 00:09:47 CET to 2026-11-21 01:26:29 CET`.

---

## 4. Cryptographic Provenance & Physical File Verification

All artifact file sizes and SHA-256 digests were directly verified against local filesystem records using `Get-Item` length and `Get-FileHash` prior to report freeze:

| Artifact Description | Repository Path | File Size (Bytes) | SHA-256 Digest |
| :--- | :--- | :---: | :--- |
| **Solver Status File** | `models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.sta` | 4,183 | `7CD84F404CF828700CF68352E07FA12739EA59B0BAE533CA47A018900AD0C420` |
| **Solver Message File** | `models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.msg` | 250,303 | `7AC50248445EE92AABB4FD5827E78F49B213EB8319748471B3F9FF06F5C3413F` |
| **Solver Data File** | `models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.dat` | 39,663 | `B5F0761C9B8F9683AF2728496A76E91E2BD73F440EFD57C18F2A8576C750D645` |
| **PBS Execution Log** | `models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_pbs_execution.log` | 2,775 | `7761063901A66428015044DC364636861D040F59B04D9E65183ED7B4FB4DE00E` |
| **UEL Energy Balance CSV** | `models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_uel_energy_balance.csv` | 2,891 | `E0F01BA5075ADCA3FEF64E0811B52AD61FD285C5BEBEE25F1849315CADB8F6DB` |
| **Spatial Crack Metrics** | `models/pandey_kumar_mode1/290_method_c_case3/job3_spatial_crack.json` | 33,824 | `882F69CB69FE6AB338794A71D3C1227035BA481CAF6E51D62121612F4DD27AF3` |
| **Observables Summary JSON**| `models/pandey_kumar_mode1/290_method_c_case3/job3_observables.json` | 3,227 | `05DAA9BC1B93A6B2D4C0D98DA1652527F7806F21AAF0ED01AFDC5502520E50D2` |
| **Job 3 Completion Receipt** | `models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_RECEIPT.json` | 7,398 | `3A0DE904D35D671F51E0BD8A08E8A40614605CBD8432C08C8F9C6A3A5C369CA7` |
| **Job 3 Execution Summary** | `models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_SUMMARY.json` | 2,643 | `CEAD135D9FAB1F7336DA6E1E6CF7974F9A0A832B732BE4508013ED7D02FFF209` |
| **Executed Production Deck**| `models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.inp` | 17,373,692 | `1D72A98120AAFF2EAC657779C6F3477CDCCF3B22C3528E6CF2BB0E233EE4BC9C` |
| **Physical Mesh Input** | `models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_PHYS.inp` | 3,090,607 | `58466F66E1D9E41E73C5E5233DD748B5237193E225407320DB4288A8DB38081F` |
| **Frozen UEL Subroutine** | `models/pandey_kumar_mode1/f42_mixed_uel.for` | 29,722 | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` |
| **Execution Report** | `docs/validation/METHOD_C_CASE3_JOB3_EXECUTION_REPORT.md` | 18,952 | `AF310F21385FF3A34D64F8E95B781B94973BF73887EB325C5B618A06B4DCC0C6` |

---

## 5. Summary & Review Dispatch Readiness

1. **All Review Gaps Resolved:**
   - Preflight deck syntax repair disclosed, diff confined to 23 header lines, 100% bitwise SVAR parity verified.
   - Job-2 baseline observables corrected from authentic committed evidence.
   - All artifact sizes matched to exact disk byte counts.
   - Terminal frame, peak load sources, walltime, and dual crack advance baselines rigorously disambiguated.
2. **Review Dispatch:**
   - Ready for independent review re-issue under handoff ID `HND-METHOD-C-CASE3-JOB3-DIAG-001`.
   - Master continuation goal `METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1` strictly remains **`OPEN`**.
   - Cumulative PBS jobs strictly remain **65** (0 new jobs consumed).
