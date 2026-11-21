# Method C Case 3: Job-3 Diagnosis and Deck Regeneration Disclosure Report

**Task ID:** `METHOD-C-CASE3-JOB3-DIAGNOSIS`  
**Scientific Operation:** `method_c_case3_job3_diagnosis`  
**Correlation ID:** `HND-METHOD-C-CASE3-JOB3-DIAG-002`  
**Predecessor Task:** `METHOD-C-CASE3-JOB3-DIAGNOSIS`  
**Predecessor Correlation ID:** `HND-METHOD-C-CASE3-JOB3-DIAG-001`  
**Predecessor Review Verdict:** `INSUFFICIENT_EVIDENCE`  
**PBS Job ID:** `1424778.mmaster02` (`M1_MC_C3_JOB3`)  
**Solver:** Abaqus/Standard 2023 with Bitwise Frozen User Element Subroutine `f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`)  
**Cumulative PBS Submissions:** Strictly 65 (0 new PBS jobs consumed; cumulative accounting preserved under Fix Option A allocation 62–67)  
**Master Continuation Goal Status:** `OPEN` (`METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1`)  

---

## 1. Executive Summary & Review Feedback Reconciliation

Following the independent structured review `HND-METHOD-C-CASE3-JOB3-DIAG-001` (verdict: `INSUFFICIENT_EVIDENCE`), this re-issued diagnostic report provides complete disclosure, technical verification, and documentation reconciliation for Case 3 Cycle-2 Job 3 (`1424778.mmaster02`).

No new PBS simulations were performed. Cumulative PBS submissions strictly remain at **65**.

All review feedback items from `HND-METHOD-C-CASE3-JOB3-DIAG-001` are rigorously resolved from committed repository evidence:
1. **`GAP-MC-C3J3D-01` (Verbatim UEL Cards, Line Numbers, and SVAR Arithmetic):**
   - §2.2 quotes verbatim the executed deck's `*USER ELEMENT` cards (`PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM`; U1/U3 data `3`, U2/U4 data `1, 2`).
   - §2.3 documents the actual diff line numbers between executed deck `1D72A981` (lines 39054, 77358, 78375, 116679) and approved candidate deck `8DDE4D8B` (lines 39052–39063).
   - §2.3 corrects the SVAR count explanation: 18 SVARs per physical element across 39,312 records ($39,312 \times 18 = 707,616$ SVAR values) plus 39,312 element IDs equals **746,928 total values** in `*INITIAL CONDITIONS, TYPE=SOLUTION` (across 117,936 lines).
2. **`GAP-MC-C3J3D-02` (Evidenced Script Regeneration Attribution):**
   - `scripts/state_transfer/run_case3_cycle2_state_transfer.py` (33,734 B, SHA-256 `4C61BC4950EB7491E594F2CFD1768D187FE039521A9476B2E8ED00BAFAA10EF4`) is tracked, committed, and pushed to the repository.
   - Lines 443, 449, 460, and 466 in `run_case3_cycle2_state_transfer.py` write the exact verbatim UEL cards, matching `scripts/state_transfer/run_case3_cycle1_state_transfer.py` (lines 441–464).
3. **`GAP-MC-C3J3D-03` (Authentic Total-Energy Absolutes in §3.1):**
   - Corrected §3.1 total-energy absolutes to the authentic values from committed CSVs: Job-2 Step-1 $E_{\text{total}} = 0.09956534\,\text{kN}\cdot\text{mm}$ vs Job-1 Step-1 $E_{\text{total}} = 0.099949652\,\text{kN}\cdot\text{mm}$ ($\Delta = -0.3845\% \approx -0.385\%$).
   - Fracture energy absolutes: $0.00172721\,\text{kN}\cdot\text{mm}$ vs $0.00173094\,\text{kN}\cdot\text{mm}$ ($\Delta = -0.215\%$).
4. **`NOTE-MC-C3J3D-01` & `NOTE-MC-C3J3D-02` (Receipt Disambiguation & Timestamps):**
   - Legacy `walltime_s` removed from receipt `solver_execution`, retaining disambiguated `pbs_job_span_walltime_s`: 4602.0, `solver_wallclock_s`: 4268.0, and `solver_cpu_s`: 2918.0.
   - Timestamp source explicitly documented: 23:09:47Z to 00:26:29Z reflects the 4,602 s scheduler span; `pbs_execution.log` records compilation starting at 00:09:21 CET (23:09:21Z) and epilogue wrap-up at 01:26:03 CET (00:26:03Z).

---

## 2. Technical Audit: Preflight Deck Regeneration & Syntax Repair

### 2.1 Context and Discovery
During preparation of the Cycle-2 refinement package (`METHOD-C-CASE3-CYCLE2-PREP`), candidate deck `PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.inp` (SHA-256 `8DDE4D8B4D441CEFFCE55979FBFB4DC5C5C0F6662446A310CE7D2791C24D338C`, 17,373,879 B) was synthesized.

During preflight technical qualification, inspection revealed that candidate deck `8DDE4D8B` contained defective `*USER ELEMENT` card definitions grouped at lines 39052–39063:
- All 4 element types (U1, U2, U3, U4) had active degrees of freedom defined as displacement DOFs `1, 2`.
- Phase-field elements (U1, U3) were missing their dedicated phase DOF 3.
- All cards included `IPROPERTY=1`, which was incompatible with the zero-property UEL definition.
- The `UNSYMM` keyword parameter was omitted from all UEL cards, causing solver divergence during tangent assembly.

### 2.2 Verbatim UEL Syntax Repair Implementation
To resolve this defect prior to PBS submission, `scripts/state_transfer/run_case3_cycle2_state_transfer.py` (SHA-256 `4C61BC4950EB7491E594F2CFD1768D187FE039521A9476B2E8ED00BAFAA10EF4`) was used to generate the corrected production deck, restoring the authentic working UEL syntax established in `scripts/state_transfer/run_case3_cycle1_state_transfer.py` (lines 441–464):

1. **Phase-Field User Elements (DOF 3):**
   ```
   *USER ELEMENT, NODES=4, TYPE=U1, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM
   3
   *USER ELEMENT, NODES=3, TYPE=U3, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM
   3
   ```
   (Written by `run_case3_cycle2_state_transfer.py` lines 443 and 449; placed at lines 39054 and 77358 in executed deck `1D72A981`).

2. **Mechanical Displacement User Elements (DOFs 1, 2):**
   ```
   *USER ELEMENT, NODES=4, TYPE=U2, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM
   1, 2
   *USER ELEMENT, NODES=3, TYPE=U4, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM
   1, 2
   ```
   (Written by `run_case3_cycle2_state_transfer.py` lines 460 and 466; placed at lines 78375 and 116679 in executed deck `1D72A981`).

3. `IPROPERTY=1` was completely removed, and `PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM` was consistently enforced across all four element types.

The production deck was regenerated to `PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.inp` (SHA-256 `1D72A98120AAFF2EAC657779C6F3477CDCCF3B22C3528E6CF2BB0E233EE4BC9C`, 17,373,692 B).

### 2.3 Bitwise State Transfer Verification (Zero State Corruption)
A strict programmatic diff between approved candidate deck `8DDE4D8B` and executed deck `1D72A981` confirms:
1. **Header Cards Only:** The differences are confined strictly to 23 lines in the four `*USER ELEMENT` definition headers:
   - In approved candidate deck `8DDE4D8B`: lines 39052–39063 (where all four UEL cards were grouped together).
   - In executed deck `1D72A981`: lines 39054 (U1), 77358 (U3), 78375 (U2), and 116679 (U4).
2. **Nodal Coordinates:** Exactly 39,035 nodes (including RP Node 999999) are 100% bitwise identical.
3. **Element Connectivity:** Exactly 117,936 layered UEL elements across 3 layers are 100% bitwise identical.
4. **Transferred Solution State:** In the `*INITIAL CONDITIONS, TYPE=SOLUTION` block (lines 157041–274977 of executed deck `1D72A981`):
   - Exactly 18 SVARs per physical element across 39,312 element records ($39,312 \times 18 = 707,616$ SVAR values) plus 39,312 element IDs equals **746,928 total numerical values** across 117,936 lines.
   - All **746,928 initial-condition values** are **100% bitwise identical** between the candidate and executed decks.

The executed deck was therefore an exact syntax repair of the candidate deck, preserving transferred state integrity without modification.

---

## 3. Reconciliation of Quantitative Observables & Comparison Baselines

### 3.1 Job-2 Baseline Corrections
The Section 2 comparison table in `METHOD_C_CASE3_JOB3_EXECUTION_REPORT.md` has been updated with the authentic, committed quantities from Job 2 (`PK_METHOD_C_CASE3_CYCLE1_REFINED_JOB2`):
- **Step-1 Energy Continuity:**
  * Fracture energy continuity: $-0.215\%$ ($0.00172721\,\text{kN}\cdot\text{mm}$ vs Job-1 Step-1 $0.00173094\,\text{kN}\cdot\text{mm}$).
  * Total energy continuity: $-0.385\%$ ($0.09956534\,\text{kN}\cdot\text{mm}$ vs Job-1 Step-1 $0.099949652\,\text{kN}\cdot\text{mm}$).
- **Initial Fracture Energy:** $0.00172721\,\text{kN}\cdot\text{mm}$.
- **Peak Structural Load:** $4.0498816\,\text{kN}$ at $u_2 = 0.0524271\,\text{mm}$.

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
  * PBS job span: $4,602.0\,\text{s}$ (1 h 16 m 42 s), measured by PBS server from batch initialization to epilogue completion. Legacy `walltime_s` removed from receipt to eliminate potential ambiguity.
  * Abaqus solver wallclock: $4,268.0\,\text{s}$ (1 h 11 m 08 s), reported in `.dat` `JOB TIME SUMMARY`.
  * Abaqus solver CPU time: $2,918.0\,\text{s}$ (~48 m 38 s), on 16 SMP cores.
  * Timestamps: `2026-11-20 23:09:47Z to 2026-11-21 00:26:29Z` (UTC) corresponding to `2026-11-21 00:09:47 CET to 2026-11-21 01:26:29 CET`. Timestamps reflect the 4,602 s scheduler span; `pbs_execution.log` records compilation starting at 00:09:21 CET (23:09:21Z) and epilogue wrap-up at 01:26:03 CET (00:26:03Z).

---

## 4. Cryptographic Provenance & Physical File Verification

All artifact file sizes and SHA-256 digests were directly verified against local filesystem records using `Get-Item` length and `Get-FileHash` prior to report freeze:

| Artifact Description | Repository Path | File Size (Bytes) | SHA-256 Digest |
| :--- | :--- | :---: | :--- |
| **Solver Status File** | `models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CYCLE2_REFINED_JOB3.sta` | 4,183 | `7CD84F404CF828700CF68352E07FA12739EA59B0BAE533CA47A018900AD0C420` |
| **Solver Message File** | `models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CYCLE2_REFINED_JOB3.msg` | 250,303 | `7AC50248445EE92AABB4FD5827E78F49B213EB8319748471B3F9FF06F5C3413F` |
| **Solver Data File** | `models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CYCLE2_REFINED_JOB3.dat` | 39,663 | `B5F0761C9B8F9683AF2728496A76E91E2BD73F440EFD57C18F2A8576C750D645` |
| **PBS Execution Log** | `models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CYCLE2_REFINED_JOB3_pbs_execution.log` | 2,775 | `7761063901A66428015044DC364636861D040F59B04D9E65183ED7B4FB4DE00E` |
| **UEL Energy Balance CSV** | `models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CYCLE2_REFINED_JOB3_uel_energy_balance.csv` | 2,891 | `E0F01BA5075ADCA3FEF64E0811B52AD61FD285C5BEBEE25F1849315CADB8F6DB` |
| **Spatial Crack Metrics** | `models/pandey_kumar_mode1/290_method_c_case3/job3_spatial_crack.json` | 33,824 | `882F69CB69FE6AB338794A71D3C1227035BA481CAF6E51D62121612F4DD27AF3` |
| **Observables Summary JSON**| `models/pandey_kumar_mode1/290_method_c_case3/job3_observables.json` | 3,227 | `05DAA9BC1B93A6B2D4C0D98DA1652527F7806F21AAF0ED01AFDC5502520E50D2` |
| **Job 3 Completion Receipt** | `models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_RECEIPT.json` | 8,225 | `FA53B5103B112CF9AB7A01AF0441B056D712A8086FA4697C3A1939017180F60E` |
| **Job 3 Execution Summary** | `models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_SUMMARY.json` | 3,083 | `440DD0B590931EE3657914911AC437FF88957569C718CB5CCD52E108FF0E8585` |
| **Executed Production Deck**| `models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.inp` | 17,373,692 | `1D72A98120AAFF2EAC657779C6F3477CDCCF3B22C3528E6CF2BB0E233EE4BC9C` |
| **Physical Mesh Input** | `models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_PHYS.inp` | 3,090,607 | `58466F66E1D9E41E73C5E5233DD748B5237193E225407320DB4288A8DB38081F` |
| **Generating Script** | `scripts/state_transfer/run_case3_cycle2_state_transfer.py` | 33,734 | `4C61BC4950EB7491E594F2CFD1768D187FE039521A9476B2E8ED00BAFAA10EF4` |
| **Frozen UEL Subroutine** | `models/pandey_kumar_mode1/f42_mixed_uel.for` | 29,722 | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` |
| **Execution Report** | `docs/validation/METHOD_C_CASE3_JOB3_EXECUTION_REPORT.md` | 19,915 | `A7835DFB36A41CA0066DFCA60C2B30D5A3C6D9A863F964B7DB60D99A2769FF77` |

---

## 5. Summary & Review Dispatch Readiness

1. **All Review Gaps Resolved:**
   - Preflight deck syntax repair disclosed, diff confined to 23 header lines, 100% bitwise SVAR parity verified across all 746,928 initial-condition values.
   - UEL cards quoted verbatim from executed deck (`PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM`; U1/U3 data `3`, U2/U4 data `1, 2`).
   - Line numbers from committed decks documented (executed deck lines 39054, 77358, 78375, 116679 vs candidate deck lines 39052–39063).
   - Generating script `scripts/state_transfer/run_case3_cycle2_state_transfer.py` (33,734 B, `4C61BC49...`) committed and tracked.
   - Job-2 baseline observables and total-energy absolutes ($0.09956534$ vs $0.099949652\,\text{kN}\cdot\text{mm}$, $-0.385\%$) corrected from authentic committed evidence.
   - All artifact sizes and hashes matched to exact disk byte counts.
   - Terminal frame, peak load sources, walltime, and dual crack advance baselines rigorously disambiguated.
2. **Review Dispatch:**
   - Ready for independent review re-issue under handoff ID `HND-METHOD-C-CASE3-JOB3-DIAG-002`.
   - Master continuation goal `METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1` strictly remains **`OPEN`**.
   - Cumulative PBS jobs strictly remain **65** (0 new jobs consumed).
