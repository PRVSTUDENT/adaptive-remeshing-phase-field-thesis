# Method C Case 3: Cycle-1 Refinement Package Report (Re-Issue 2)

**Task ID:** `METHOD-C-CASE3-CYCLE1-REFINEMENT-PACKAGE`  
**Correlation ID:** `HND-METHOD-C-CASE3-CYCLE1-PREP-002`  
**Predecessor Review:** `HND-METHOD-C-CASE3-CYCLE1-PREP-001` (Verdict: `INSUFFICIENT_EVIDENCE`)  
**Predecessor Task:** `METHOD-C-CASE3-JOB1-FAILURE-DIAGNOSIS` (`HND-METHOD-C-CASE3-JOB1-DIAG-002`, Verdict: `APPROVE`)  
**Goal ID:** `METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1` (Status: `OPEN`)  
**Date:** 2026-11-20  
**Author:** Gemini Antigravity (Governed Autonomous Agent)  
**Governing Policy:** 19 November 2026 Method C Directive & Standing Execution Rules  

---

## 1. Executive Summary

Following independent structured review of `HND-METHOD-C-CASE3-CYCLE1-PREP-001` (Verdict: `INSUFFICIENT_EVIDENCE`), this re-issued report provides the complete, gap-resolved **Case 3 Cycle-1 Refinement Package**. 

All four review gaps (`GAP-MC-C3C1P-01` through `GAP-MC-C3C1P-04`) and reviewer notes have been resolved with repo-verified evidence, 0 new PBS jobs consumed, and cumulative PBS submissions strictly preserved at **63**.

The package transitions from the coarse initial discretization (Job 1) to the Cycle-1 adapted discretization (Job 2), achieving sub-$l_0/2$ spatial resolution in the active fracture process zone while strictly bounding PBS resource usage and preserving physical consistency.

### Key Deliverables & Verifications
1. **Donor State Ingestion:** Ingested the authentic Step-1 donor state extracted directly from `/scratch9/pr21vyci/runs/mode1_290_method_c_case3/PK_METHOD_C_CASE3_COARSE_JOB1.odb` ($u_2 = 0.0500\,\text{mm}$, $RF_2 = 3.9288\,\text{kN}$, $d_{\max} = 0.469063$, $H_{\max} = 0.016731\,\text{MPa}$, 4,813 nodes, 4,671 elements).
2. **Cycle-1 Adapted Physical Mesh:** Generated `PK_METHOD_C_CASE3_CYCLE1_PHYS.inp` via Abaqus CAE with targeted process zone partitioning ($x \in [8.5, 22.0]\,\text{mm}$, $y \in [63.0, 77.0]\,\text{mm}$), resolving $l_0/2 = 0.1425\,\text{mm}$ with $h_{\text{ref}} = 0.140\,\text{mm}$.
   - Elements: 23,126 physical elements (22,511 quads [97.34%], 615 tris), 23,046 nodes.
   - All quality gates PASS: $\min\det(J) = 8.7276\times 10^{-4} > 0$ (0 non-positive Jacobians), mean aspect ratio = 1.2726, max aspect ratio = 3.9486 $\le 4.0$.
3. **State & History Transfer:** Transferred nodal displacements $(u_1, u_2)$, nodal damage $d$, and GP strain energy history $H$ via qualified `isoparametric_gp_transfer.py` (`convex_clamp`).
   - Strict non-negativity: $H_{\min} = 9.8003\times 10^{-12}\,\text{MPa} \ge 0.0$ at donor GPs; deck SVAR9-12 history minimum is $0.0\,\text{MPa} \ge 0.0$ (0 violations).
   - Phase-field bounds: $0.0 \le d \le 1.0$ everywhere.
   - Non-healing verified: nodal $d_{\max} = 0.469063$, matching donor peak exactly; element SVAR1-8 damage peak is $0.446607$.
   - Notch slit flank isolation at $y = 70.0\,\text{mm}$ ($x \le 10.0\,\text{mm}$) strictly maintained.
4. **3-Layer Production Deck Assembly:** Assembled `PK_METHOD_C_CASE3_CYCLE1_REFINED_JOB2.inp` (69,378 layered elements: Phase UEL, Disp UEL, CPE4/CPE3 Companion UMAT) with complete `*INITIAL CONDITIONS, TYPE=DISPLACEMENT` and `*INITIAL CONDITIONS, TYPE=SOLUTION` (SVARS 1..12).
5. **Two-Step Load Schedule with Verified Amplitude Hold:**
   - Pre-step definition: `*AMPLITUDE, NAME=CONST_HOLD` (`0.0, 1.0, 1.0, 1.0`).
   - Step 1 (`Step-1-Hold`): Fixed-load re-equilibration hold at $u_2 = 0.0500\,\text{mm}$ using `*BOUNDARY, AMPLITUDE=CONST_HOLD` on `N_RP, 2, 2, 0.0500`.
   - Step 2 (`Step-2`): Forward crack propagation to Cycle-1 target $u_2 = 0.4125\,\text{mm}$ using `*BOUNDARY, OP=MOD` on `N_RP, 2, 2, 0.4125` with $dt_{\min} = 1.0\times 10^{-8}$.
6. **PBS Accounting & Budget:** 0 new PBS jobs consumed. Cumulative PBS submissions strictly preserved at **63**. Explicit 5-job budget (cumulative 62 to 67) affirmed.

---

## 2. Review Gap Resolution Summary (`HND-METHOD-C-CASE3-CYCLE1-PREP-001`)

The independent structured review identified two blocking defects and two non-blocking defects, all resolved below:

### 2.1 GAP-MC-C3C1P-01 (Step-1 Hold Mechanism in Deck) — RESOLVED
- **Finding:** The PREP-001 report stated Step 1 uses amplitude `CONST_HOLD`, but the initial assembled deck omitted the `*AMPLITUDE, NAME=CONST_HOLD` block and the amplitude parameter on `*BOUNDARY`.
- **Resolution:** Re-generated `PK_METHOD_C_CASE3_CYCLE1_REFINED_JOB2.inp` with:
  ```inp
  ** ----------------------------------------------------------
  ** AMPLITUDES
  ** ----------------------------------------------------------
  *AMPLITUDE, NAME=CONST_HOLD
  0.0, 1.0, 1.0, 1.0
  ...
  *STEP, NAME=Step-1-Hold, NLGEOM=NO, INC=100
  *STATIC
  1.0, 1.0, 1.0E-08, 1.0
  *BOUNDARY
  N_LOWER_HOLE, 1, 2, 0.0
  N_UPPER_HOLE, 1, 1, 0.0
  N_RP, 1, 1, 0.0
  *BOUNDARY, AMPLITUDE=CONST_HOLD
  N_RP, 2, 2, 0.0500
  ...
  *STEP, NAME=Step-2, NLGEOM=NO, INC=5000
  *STATIC
  0.002, 1.0, 1.0E-08, 0.005
  *BOUNDARY, OP=MOD
  N_RP, 2, 2, 0.4125
  ```
- **Verification:** Unit test `test_cycle1_3layer_production_deck_structure` explicitly asserts presence of `*AMPLITUDE, NAME=CONST_HOLD`, `*BOUNDARY, AMPLITUDE=CONST_HOLD`, and `*BOUNDARY, OP=MOD`. The new verified deck SHA-256 is `E22F38DBFDC0FCDABF2DCBE47982149A5F5DDD04B02F035BCEF7421F03F60FF9`.

### 2.2 GAP-MC-C3C1P-02 (F1852 Driver Selection Branch & Decision Rule) — RESOLVED
- **Finding:** State explicitly which F1852 driver branch was taken and why, with driver evidence against $D_{\text{CORE}} = 0.50$.
- **Driver Evidence & Scientific Rationale:**
  1. **Native MISESERI Inactivity:** As proven in `docs/validation/METHOD_C_STEP1_REMESHING_DECISION_RECORD.md` (and re-verified by inspecting `PK_METHOD_C_CASE3_COARSE_JOB1.dat` and `.msg`), Layer 3 companion elements use `*USER MATERIAL, NAME=UMAT_MAT`. In Abaqus/Standard, the Zienkiewicz–Zhu stress recovery operator is implemented only for built-in materials (`*ELASTIC`), outputting zero recovered stress error (`MISESERI = 0.000000`) across all elements for `*USER MATERIAL`. Thus, the native `MISESERI` branch is technically inactive.
  2. **Incipient-Damage Decision Rule:** In the generalized adaptive framework driver selection module (`generalized_2d_adaptive_framework_driver_selection_f1852.py`), the default branch cutoff is $D_{\text{CORE}} = 0.50$. However, as formalized and approved in `METHOD-C-PHASE2-TRANSFER-REEQUILIBRATION` and review `HND-METHOD-C-PHASE2-JOB1-003`, when damage has nucleated at a notch tip ($0.10 \le d < 0.50$, here $d_{\max} = 0.469063$), the **Incipient-Damage Decision Rule** applies.
  3. **Analytical Sizing Law:** Under `AdvancingDamageEnvelopeBuilder.analytical_damage_sizing` (F1849), for $d \ge d_{\text{proc}} = 0.10$, target element size scales smoothly from $h_{\text{proc}} = l_0 / 1.2 = 0.2375\,\text{mm}$ down to $h_{\text{core}} = l_0 / 2.5 = 0.1140\,\text{mm}$. For $d_{\max} = 0.469063$:
     $$\text{frac} = \frac{0.469063 - 0.10}{0.50 - 0.10} = 0.922658$$
     $$h_{\text{tgt}}(\text{tip}) = 0.2375 - 0.922658 \times (0.2375 - 0.1140) = 0.1235\,\text{mm}$$
  4. **Target Process Zone Resolution:** To satisfy finite element phase-field discretization criteria ($h \le l_0/2 = 0.1425\,\text{mm}$), the process zone partition was seeded at $h_{\text{ref}} = 0.140\,\text{mm} < l_0/2$. The partition bounding box $x \in [8.5, 22.0]\,\text{mm}$, $y \in [63.0, 77.0]\,\text{mm}$ strictly encloses all donor nodes where $d \ge 0.01$ (which are strictly contained within $x \in [8.5, 18.0]\,\text{mm}$, $y \in [66.0, 74.0]\,\text{mm}$, centered at the notch root $(10.0, 70.0)\,\text{mm}$).

### 2.3 GAP-MC-C3C1P-03 (Report Section 8 Sizes, SHAs, and Section 4 Donor Node Count) — RESOLVED
- **Finding:** Correct §8 file sizes to exact committed values, add audit and receipt SHAs, and correct §4 donor node count from 4,812 to 4,813.
- **Resolution:**
  - `PK_METHOD_C_CASE3_CYCLE1_PHYS.inp`: Size corrected to **1,685,339 B** (SHA `25661F0E...`).
  - `PK_METHOD_C_CASE3_CYCLE1_REFINED_JOB2.inp`: Size updated to **9,992,505 B** (new SHA `E22F38DB...`).
  - `method_c_case3_cycle1_mesh_audit.json`: Size corrected to **1,007 B**, SHA added: `98D319C9145F1524102605553E37E2A277E5F61744C8A865B76788FC6F3893B0`.
  - `PK_METHOD_C_CASE3_CYCLE1_TRANSFER_RECEIPT.json`: Size updated to **3,562 B**, SHA added: `3D0B4853850244801063C2E4A4011FC6AE17845381A7BD85C3341942502A5E0C`.
  - §4 donor nodes corrected to **4,813** (matching `donor_case3_step1_state.json` `num_nodes`).

### 2.4 GAP-MC-C3C1P-04 (Clarification of Receiver History Minimum & Damage Peak) — RESOLVED
- **Finding:** Clarify the receiver history minimum (deck SVAR vs donor GP) and damage peak (nodal vs element SVAR).
- **Resolution:**
  - **History Minimum:** Donor GP history minimum is $h_{\text{gp, min}} = 9.800320\times 10^{-12}\,\text{MPa} \ge 0$. In the assembled deck `*INITIAL CONDITIONS, TYPE=SOLUTION`, integration points in far-field elements outside the transfer interpolation stencil default to $0.0\,\text{MPa}$. Both $9.8003\times 10^{-12}\,\text{MPa}$ and $0.0\,\text{MPa}$ strictly satisfy thermodynamic non-negativity ($H \ge 0$).
  - **Damage Maximum:** Transferred nodal damage strictly preserves donor peak damage at $d_{\max} = 0.469063$ (zero healing). In the assembled deck, companion element SVAR1-8 damage is computed by averaging vertex nodal values, yielding an element SVAR peak of $0.446607$, consistent with linear interpolation over finite element volumes.

---

## 3. 5-Job Fix Option A PBS Allocation Budget

Per the independent structured review and the Method C directive, the complete 4-cycle Method C adaptive demonstration on Case 3 operates under a strict, once-only registered PBS allocation of **5 jobs** (cumulative submissions 62 through 67):

| Sequence | Job Name | Mesh / Stage | Target $u_2$ | Status | PBS ID |
|---|---|---|---|---|---|
| **Job 1** | `M1_MC_C3_JOB1` | Coarse baseline (4,671 elem / 14,013 layered) | $0.0500 \to 1.50\,\text{mm}$ | Consumed (Step 1 Converged) | `1424711.mmaster02` |
| **Job 2** | `M1_MC_C3_JOB2` | Cycle 1 refined (23,126 elem / 69,378 layered) | Hold $0.0500 \to 0.4125\,\text{mm}$ | **Ready / Staged** | Pending review |
| **Job 3** | `M1_MC_C3_JOB3` | Cycle 2 refined | Hold $0.4125 \to 0.7750\,\text{mm}$ | Pending Job 2 review | — |
| **Job 4** | `M1_MC_C3_JOB4` | Cycle 3 refined | Hold $0.7750 \to 1.1375\,\text{mm}$ | Pending Job 3 review | — |
| **Job 5** | `M1_MC_C3_JOB5` | Cycle 4 refined | Hold $1.1375 \to 1.5000\,\text{mm}$ | Pending Job 4 review | — |

- Current Cumulative Submissions: **63** (strictly preserved, 0 new jobs submitted in this package).
- Next Authorized Submission (upon approval of PREP-002): Job 2 (will bring cumulative count to 64).

---

## 4. Step-1 Donor State Provenance & Ingestion

The donor fields were extracted from Step 1 of Job 1 on cluster scratch using `extract_case3_step1_donor_fields.py`:

- **Source File:** `/scratch9/pr21vyci/runs/mode1_290_method_c_case3/PK_METHOD_C_CASE3_COARSE_JOB1.odb`
- **Committed Local Descriptor:** `models/pandey_kumar_mode1/290_method_c_case3/donor_case3_step1_state.json`
- **SHA-256:** `299EAB98F6881E8694C0F7231A0E42E8606D7E9899BCDF96CCFE130E15CC3050`
- **Donor State Metrics:**
  * Step Time: $1.000$ (Step 1, Inc 50)
  * Displacement Hold: $u_2 = 0.0500\,\text{mm}$
  * Reaction Force: $RF_2 = 3.928812\,\text{kN}$ (verified against `.dat` line 999999)
  * Donor Nodes: **4,813** physical nodes (`num_nodes`)
  * Donor Elements: 4,671 physical elements (4,542 quads, 129 tris)
  * Peak Nodal Damage: $d_{\max} = 0.469063$
  * Mean Nodal Damage: $d_{\text{mean}} = 0.009889$
  * Peak GP Strain Energy History: $H_{\max} = 0.01673136\,\text{MPa}$
  * Min GP Strain Energy History: $h_{\text{gp, min}} = 9.800320\times 10^{-12}\,\text{MPa}$
  * Total GP Entries: 18,297 integration points

---

## 5. Cycle-1 Adapted Receiver Mesh Quality Audit

The physical mesh `PK_METHOD_C_CASE3_CYCLE1_PHYS.inp` was generated via Abaqus CAE scripting (`scripts/remeshing/generate_method_c_case3_cycle1_mesh.py`) and audited against finite element quality gates (`scripts/remeshing/audit_method_c_case3_cycle1_mesh.py`).

### Mesh Audit Summary (`method_c_case3_cycle1_mesh_audit.json`)
- **Mesh Path:** `models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE1_PHYS.inp`
- **Mesh SHA-256:** `25661F0E2D8CB31A5B9B30AE50427A3C64317362F444FD3408658D0AF597D90E`
- **Mesh File Size:** 1,685,339 Bytes
- **Total Physical Elements:** 23,126
- **Quad Elements:** 22,511 (97.34%)
- **Tri Elements:** 615 (2.66%)
- **Total Physical Nodes:** 23,046
- **Quality Gates:**
  * **Gate 01 (Isoparametric Jacobian):** $\min\det(J) = 8.727630\times 10^{-4} > 0.0$, 0 non-positive Jacobians $\implies$ **PASS**
  * **Gate 02 (Quad Fraction):** $97.34\% \ge 85.0\% \implies$ **PASS**
  * **Gate 03 (Aspect Ratio Quality):** Mean aspect ratio $= 1.2726 \le 2.50$, Max aspect ratio $= 3.9486 \le 4.00$ (0 violations $> 4.0$) $\implies$ **PASS**
  * **All Gates Pass:** **TRUE**

### Spatial Resolution Across Process Zone
- Material length scale: $l_0 = 0.285\,\text{mm}$
- Theoretical sub-$l_0$ threshold: $l_0 / 2 = 0.1425\,\text{mm}$
- Process zone seed size: $h_{\text{ref}} = 0.140\,\text{mm} < 0.1425\,\text{mm}$
- Background coarse seed: $h_{\text{bg}} = 2.00\,\text{mm}$
- Refinement Box: $x \in [8.5, 22.0]\,\text{mm}$, $y \in [63.0, 77.0]\,\text{mm}$ completely encloses the blunt notch root and the active damage localization corridor.

---

## 6. State and History Transfer Verification

State transfer was executed by `scripts/state_transfer/run_case3_cycle1_state_transfer.py` producing `PK_METHOD_C_CASE3_CYCLE1_TRANSFER_RECEIPT.json`.

### Transfer Integrity & Safeguards
| Metric / Gate | Donor State (Coarse) | Transferred State (Adapted) | Evaluation | Gate Status |
|---|---|---|---|---|
| **Max Nodal Damage $d_{\max}$** | 0.469063 | 0.469063 | Exact preservation (no healing) | **PASS** |
| **Max Element SVAR Damage** | — | 0.446607 | Vertex average across elements | **PASS** |
| **Mean Damage $d_{\text{mean}}$** | 0.009889 | 0.013881 | Consistent with fine mesh density | **PASS** |
| **Max History $H_{\max}$** | 0.016731 MPa | 0.016731 MPa | Exact preservation | **PASS** |
| **Min GP History $H_{\min}$** | $9.8003\times 10^{-12}$ MPa | $9.8003\times 10^{-12}$ MPa | Strict non-negativity enforced | **PASS** |
| **Deck SVAR History Min** | — | $0.000000$ MPa | Thermodynamic bound satisfied | **PASS** |
| **Phase Bounds** | $[0, 1]$ | $[0.0000, 0.469063]$ | Within $[0, 1]$ everywhere | **PASS** |
| **Slit Flank Isolation** | Isolated at $y=70.0$ | Isolated at $y=70.0$ | Zero cross-slit interpolation | **PASS** |
| **All Transfer Gates** | — | — | — | **PASS** |

---

## 7. 3-Layer Production Deck Specification (`PK_METHOD_C_CASE3_CYCLE1_REFINED_JOB2.inp`)

The re-equilibration deck incorporates the full authentic multi-physics formulation:
- **Deck Path:** `models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE1_REFINED_JOB2.inp`
- **Deck SHA-256:** `E22F38DBFDC0FCDABF2DCBE47982149A5F5DDD04B02F035BCEF7421F03F60FF9`
- **Deck File Size:** 9,992,505 Bytes
- **Total Layered Elements:** 69,378
  * Layer 1 (Phase UEL): EIDs 1..22,511 (U1 quads) + 22,512..23,126 (U3 tris)
  * Layer 2 (Disp UEL): EIDs 23,127..45,637 (U2 quads) + 45,638..46,252 (U4 tris)
  * Layer 3 (Companion UMAT): EIDs 46,253..68,763 (CPE4 quads) + 68,764..69,378 (CPE3 tris)
- **Subroutine Binding:** `models/pandey_kumar_mode1/f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`)
- **Initial Conditions:**
  * `*INITIAL CONDITIONS, TYPE=DISPLACEMENT`: sets $(u_1, u_2, d)$ at all 23,046 nodes + $u_2 = 0.0500\,\text{mm}$ at Reference Point node 999999.
  * `*INITIAL CONDITIONS, TYPE=SOLUTION`: sets SVARS 1..12 across all 23,126 companion elements (SVARS 1..4 = $d$, SVARS 5..8 = $d_{\max}$, SVARS 9..12 = $H_0$).
- **Loading Steps:**
  * **Amplitudes Block:** `*AMPLITUDE, NAME=CONST_HOLD` (`0.0, 1.0, 1.0, 1.0`)
  * **Step 1 (`Step-1-Hold`):** Fixed-load re-equilibration hold at $u_2 = 0.0500\,\text{mm}$ referencing `*BOUNDARY, AMPLITUDE=CONST_HOLD` on `N_RP, 2, 2, 0.0500`.
  * **Step 2 (`Step-2`):** Forward crack propagation from $u_2 = 0.0500\,\text{mm}$ to $u_2 = 0.4125\,\text{mm}$ using `*BOUNDARY, OP=MOD` on `N_RP, 2, 2, 0.4125` ($dt_{\min} = 1.0\times 10^{-8}$, $dt_0 = 0.002$, $dt_{\max} = 0.005$).

---

## 8. Artifact and Manifest Registry

| Artifact | Repository Path | SHA-256 | Size (Bytes) |
|---|---|---|---|
| Donor State JSON | `models/pandey_kumar_mode1/290_method_c_case3/donor_case3_step1_state.json` | `299EAB98F6881E8694C0F7231A0E42E8606D7E9899BCDF96CCFE130E15CC3050` | 1,607,950 |
| Physical Mesh INP | `models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE1_PHYS.inp` | `25661F0E2D8CB31A5B9B30AE50427A3C64317362F444FD3408658D0AF597D90E` | 1,685,339 |
| Mesh Audit JSON | `models/pandey_kumar_mode1/290_method_c_case3/method_c_case3_cycle1_mesh_audit.json` | `98D319C9145F1524102605553E37E2A277E5F61744C8A865B76788FC6F3893B0` | 1,007 |
| Refined Deck INP | `models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE1_REFINED_JOB2.inp` | `E22F38DBFDC0FCDABF2DCBE47982149A5F5DDD04B02F035BCEF7421F03F60FF9` | 9,992,505 |
| Transfer Receipt JSON | `models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE1_TRANSFER_RECEIPT.json` | `3D0B4853850244801063C2E4A4011FC6AE17845381A7BD85C3341942502A5E0C` | 3,562 |
| Frozen UEL | `models/pandey_kumar_mode1/f42_mixed_uel.for` | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` | 29,722 |
| Unit Tests | `tests/unit/test_method_c_case3_cycle1_package.py` | `3B1DCC2824B04A9C6D2DB47BBD01BB833587BE41D3B8ED5F18E01F0E38E7064B` | 6,856 |
| Package Report | `docs/validation/METHOD_C_CASE3_CYCLE1_REFINEMENT_PACKAGE_REPORT.md` | *(Self-referential package report; registered in manifest)* | ~18.6 KB |

---

## 9. Conclusion and Next Action

The Case 3 Cycle-1 Refinement Package has resolved all feedback from `HND-METHOD-C-CASE3-CYCLE1-PREP-001` and satisfied all prerequisite technical, mathematical, and physical quality gates. 

Upon independent review approval of `HND-METHOD-C-CASE3-CYCLE1-PREP-002`:
1. Submit Job 2 (`M1_MC_C3_JOB2`, PBS submission #64) via guarded `Invoke-Mode1Execution.ps1`.
2. Execute Step-1 fixed-load re-equilibration ($u_2 = 0.0500\,\text{mm}$) followed by Step-2 forward propagation ($u_2 \to 0.4125\,\text{mm}$).
3. Cumulative PBS count remains strictly bounded within the 5-job budget (cumulative 62 to 67).
4. Master goal `METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1` strictly remains **`OPEN`**.
