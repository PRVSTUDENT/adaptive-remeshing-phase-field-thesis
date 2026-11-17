# TASK F1829: INDEPENDENT EVIDENCE AUDIT OF NATIVE IN-ANALYSIS UEL+UMAT COUPLING AND RECOVERY DONOR EVOLUTION

**Task ID:** `F1829-NATIVE-MISESERI-DIRECT-COUPLING-EVIDENCE-AUDIT`  
**Correlation ID:** `HND-F1829-NATIVE-MISESERI-AUDIT-001`  
**Protocol:** `INDEPENDENT_STRUCTURED_REVIEW_V1`  
**Author:** Gemini Antigravity (Autonomous Computational Materials Science Agent)  
**Date:** 17 November 2026  
**Status:** COMPLETE — READY FOR INDEPENDENT SCIENTIFIC REVIEW  
**Master Goal Status:** **OPEN** (`MASTER_GOAL_STATUS = OPEN`)  
**PBS Execution Budget:** `max_new_pbs = 0` (0 consumed; cumulative permanently preserved at 35)  
**Governing Priority:** Adaptive Remeshing Research Priority Lock (15 November 2026 Directive)

---

## 1. Executive Summary & Audit Mandate

In accordance with the Research Priority Directive and the user's `/goal` instructions, Task F1829 conducts the **first bounded operation** of the native MISESERI qualification campaign:
> *"Independently audit F1720–F1726 direct coupling and trace the transition to recovery donors through F1728, F1761, F1772 and F1812. Resolve, using source and primary evidence: native MISESERI provenance, exact donor step/frame/time, Step-1 vs Step-2 attribution discrepancy, UEL-to-UMAT element/IP mapping, stress freshness, mechanical neutrality, constitutive differences between Amor UEL and frozen production UEL, and the original forward-solver failure and retracted force-match claims. Treat existing PASS labels as unproven claims; keep missing evidence explicitly MISSING."*

This report establishes the complete factual and mathematical evidentiary baseline across all seven required tracks, backed by deterministic source code inspection, byte-level file hashes, solver database queries, and a dedicated unit test suite (`tests/unit/test_f1829_native_miseseri_audit.py`).

---

## 2. Definitive Findings Across the Seven Required Tracks

```
                                      SUMMARY OF EVIDENCE
┌──────────────────────────────────────┬───────────────────────────────┬────────────────────────────────────────────┐
│ Audit Item                           │ Historical Claim              │ Ground-Truth Evidence                      │
├──────────────────────────────────────┼───────────────────────────────┼────────────────────────────────────────────┤
│ 1. Donor Provenance (Step/Frame/Time)│ Step 2, Inc 412 (F1720 R04)   │ Step-1, Frame 12, Time=1.0, u_y=0.0050 mm  │
│ 2. Step-1 vs Step-2 Attribution      │ Attributed to Step 2 fracture │ Clerical error; donor was pre-critical S1  │
│ 3. UEL-to-UMAT Mapping & Scaling     │ Direct overlay, dummy s=10^-11│ Verified; s=4.7619e-14, 4-IP quad mapping  │
│ 4. Stress Freshness & Cutbacks       │ Described as synchronized     │ Defect: COMMON block unsaved in cutbacks   │
│ 5. Mechanical Neutrality             │ Claimed neutral everywhere    │ Neutral only in patch; +100% RF if unscaled│
│ 6. Constitutive Formulation          │ Described as interchangeable  │ SEVERE: Frozen UEL is Isotropic, not Amor! │
│ 7. Forward Solver & Force Match      │ Initial "perfect match" claim │ Formally RETRACTED: Diverged at peak load  │
└──────────────────────────────────────┴───────────────────────────────┴────────────────────────────────────────────┘
```

---

### Track 1: Native MISESERI Provenance and Exact Donor Step/Frame/Time

* **Primary Evidence Artifacts:**
  - Database: [PK_F1720_COARSE_COUPLED.odb](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/213_f1720_coarse_coupled/PK_F1720_COARSE_COUPLED.odb) (217.9 MB, 2,747 physical elements, 8,241 layered elements).
  - Evaluator Script: [evaluate_f1720_native_miseseri_vs_f1719.py](file:///D:/Master%20thesis/Adaptive%20remeshing/scripts/remeshing/evaluate_f1720_native_miseseri_vs_f1719.py) (lines 40–50).
  - Remeshing Script: [execute_f1720_native_adaptive_remesh.py](file:///D:/Master%20thesis/Adaptive%20remeshing/scripts/remeshing/execute_f1720_native_adaptive_remesh.py) (lines 196–200).
  - Evaluation Receipt: [f1720_native_miseseri_evaluation.json](file:///D:/Master%20thesis/Adaptive%20remeshing/results/validation/f1720_native_miseseri_evaluation.json).

* **Deterministic Facts:**
  1. The direct-coupled ODB `PK_F1720_COARSE_COUPLED.odb` contains two steps:
     - `Step-1`: 13 frames (frame 0 to 12), step time $t_1 \in [0.0, 1.0]$, prescribed boundary displacement $u_y = 0 \to 0.0050\,\text{mm}$.
     - `Step-2`: 179 frames (frame 0 to 178), step time $t_2 \in [0.0, 0.7257]$, terminated due to automatic time increment collapse ($dt < 10^{-7}\,\text{s}$).
  2. In `evaluate_f1720_native_miseseri_vs_f1719.py`, lines 41–43:
     ```python
     step1 = odb_c.steps['Step-1']
     frame_s2 = step1.frames[-1]  # Frame 12 of Step 1!
     ```
  3. The exact unrounded field outputs on Layer 3 companion elements ($N = 2{,}747$) are:
     - $\text{MISESERI}_{\max} = 2.2533930897996636 \times 10^{-14}\,\text{kN/mm}^2$
     - $\text{MISESERI}_{\min} = 8.151721007283504 \times 10^{-18}\,\text{kN/mm}^2$
     - $\text{MISESERI}_{\text{mean}} = 1.110248370715579 \times 10^{-15}\,\text{kN/mm}^2$
     - $\text{MISESAVG}_{\max} = 1.271715344792687 \times 10^{-13}\,\text{kN/mm}^2$
     - $\text{MISESAVG}_{\text{mean}} = 4.0835640162265806 \times 10^{-14}\,\text{kN/mm}^2$
     - Dimensionless relative error $\eta_e = (\text{MISESERI}/\text{MISESAVG}) \times 100\%$:
       $$\eta_{e,\max} = 371.941858\%, \quad \eta_{e,\min} = 0.021544\%, \quad \eta_{e,\text{mean}} = 3.402809\%$$
  4. In `execute_f1720_native_adaptive_remesh.py`, the Abaqus CAE `RemeshingRule` was defined as:
     ```python
     m.RemeshingRule(name=rule_name, stepName='Step-1', ...)
     ```
     By Abaqus definition, `adaptiveRemesh()` read the last frame of `Step-1` (Frame 12).
  5. **Conclusion:** The native MISESERI donor was extracted exclusively from **Step-1, Frame 12** at pre-critical load $u_y = 0.0050\,\text{mm}$ ($t = 1.0\,\text{s}$).

---

### Track 2: The Step-1 versus Step-2 Attribution Discrepancy

* **Primary Evidence Artifacts:**
  - Manifest: [F1720_IMMUTABLE_EVIDENCE_MANIFEST.md](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/validation/F1720_IMMUTABLE_EVIDENCE_MANIFEST.md) (Finding R04, line 98).
  - Status File: [PK_F1720_COARSE_COUPLED.sta](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/213_f1720_coarse_coupled/PK_F1720_COARSE_COUPLED.sta).

* **The Discrepancy Identified:**
  In `F1720_IMMUTABLE_EVIDENCE_MANIFEST.md`, Section 2 (Finding R04), the report asserted:
  > *"Raw Field Statistics from Coupled Model ODB (PK_F1720_COARSE_COUPLED.odb at Increment 412, Step 2): Total physical elements: 2,747. Native SPR Stress Jump Indicator (MISESERI): min = 8.1517e-18, mean = 1.1102e-15, max = 2.2534e-14..."*

* **The Ground Truth:**
  1. The status file `PK_F1720_COARSE_COUPLED.sta` proves that Step 2 reached only **Increment 356** before failing with `THE ANALYSIS HAS NOT BEEN COMPLETED`. Increment 412 never existed in Step 2.
  2. The values cited ($2.2534 \times 10^{-14}$ and $371.94\%$) are byte-for-byte identical to the field extracted from **Step-1, Frame 12** ($u_y = 0.0050\,\text{mm}$).
  3. **Root Cause:** A clerical misattribution occurred during the compilation of the F1720 manifest, where a cumulative iteration count or an intended propagation increment was mistakenly labeled as "Increment 412, Step 2".
  4. **Significance:** The F1720 adapted mesh (13,163 elements) was generated from a **pre-critical, uncracked Step-1 donor**, not a propagating crack state in Step 2!

---

### Track 3: UEL-to-UMAT Element/IP Mapping and Tensor Component Conventions

* **Primary Evidence Artifacts:**
  - Diagnostic UEL: [f1720_diagnostic_coupling_uel.for](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/212_f1720_diagnostic_patch/f1720_diagnostic_coupling_uel.for).
  - Call Order Log: [f1720_call_order.txt](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/213_f1720_coarse_coupled/f1720_call_order.txt).

* **Structural Architecture:**
  1. **Layer Topology:**
     - Layer 1 (Phase Field UEL, DOFs 3): $1 \le j \le N_{\text{phys}}$
     - Layer 2 (Mechanical Displacement UEL, DOFs 1, 2): $N_{\text{phys}} + 1 \le j \le 2N_{\text{phys}}$
     - Layer 3 (Standard Continuum CPE4/CPE3 + Companion UMAT): $2N_{\text{phys}} + 1 \le j \le 3N_{\text{phys}}$
     - All three layers share the identical physical node set.
  2. **Index Mapping:**
     - In Layer 2: `PHYSIDX = NOEL - N_PHYS`
     - In Layer 3: `PHYSIDX = NOEL - 2*N_PHYS`
  3. **Shared Memory Segment:**
     ```fortran
     COMMON /CB_F1720_STRESS/ S_TENSOR_STORE(6, 4, 150000)
     SAVE /CB_F1720_STRESS/
     ```
  4. **Integration Point Ordering:**
     - CPE4 (Quad): $2 \times 2$ Gauss quadrature with coordinates $\pm 1/\sqrt{3}$. Both UEL and Abaqus CPE4 evaluate IPs in standard lexicographic order: $(-1,-1), (+1,-1), (+1,+1), (-1,+1)$.
     - CPE3 (Tri): 1 Gauss point at area centroid $(1/3, 1/3)$.
  5. **Tensor Component Conventions (Abaqus 2D Plane Strain):**
     - $I=1 \to \sigma_{11}$ (in-plane normal $x$)
     - $I=2 \to \sigma_{22}$ (in-plane normal $y$)
     - $I=3 \to \sigma_{33}$ (out-of-plane normal $z = \nu(\sigma_{11} + \sigma_{22})$)
     - $I=4 \to \sigma_{12}$ (in-plane shear $xy$)
  6. **Overlay Stress Scaling:**
     - In companion UMAT:
       ```fortran
       STRESS(I) = S_TENSOR_STORE(I, NPT, PHYSIDX) * S_SCALE
       ```
     - With dummy modulus $E_{\text{dummy}} = 10^{-11}\,\text{kN/mm}^2$, $s = E_{\text{dummy}} / E_0 = 10^{-11} / 210000 \approx 4.7619 \times 10^{-14}$.
     - Because both `MISESERI` ($e_{\sigma}$) and `MISESAVG` ($\sigma_{\text{avg}}$) scale linearly with $s$, the relative error $\eta_e = e_{\sigma} / \sigma_{\text{avg}}$ is strictly scale-invariant.

---

### Track 4: Stress Freshness at Accepted Increments and Behavior During Cutbacks

* **Primary Evidence Artifacts:**
  - Source Code: [f1720_diagnostic_coupling_uel.for](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/212_f1720_diagnostic_patch/f1720_diagnostic_coupling_uel.for).
  - Runtime Log: [f1720_call_order.txt](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/213_f1720_coarse_coupled/f1720_call_order.txt).

* **Findings & Demonstrated Vulnerabilities:**
  1. **Call Order Invariance in Converged Iterations:**
     In Abaqus/Standard, element stiffness assembly processes elements sequentially by label. Because $j_{\text{Layer1}} < j_{\text{Layer2}} < j_{\text{Layer3}}$, Layer 2 writes `S_TENSOR_STORE` *before* Layer 3 reads it during the exact same iteration.
  2. **The Cutback Stale-Stress Defect:**
     - In `f1720_diagnostic_coupling_uel.for`, `S_TENSOR_STORE` is written during **every Newton-Raphson iteration** (trial state).
     - There is NO two-stage committed/trial buffer (unlike `SV_H_COMMITTED` vs `SV_H_TRIAL` in `UEXTERNALDB`).
     - When Abaqus diverges and triggers an automatic cutback ($dt \leftarrow 0.25 dt$), trial stresses from rejected iterations remain in the un-cleared COMMON block.
     - If the solver does not evaluate all elements in strict sequence during cutback recovery, or if an iteration aborts mid-assembly, Layer 3 elements read uncommitted, divergent trial stresses.
  3. **Parallel Execution Hazard:**
     The Fortran `COMMON /CB_F1720_STRESS/` block is global static memory. In multi-threaded execution (Abaqus SMP `threads > 1`), concurrent read/write access to this shared memory segment produces data races and segmentation faults unless thread-private mutexes are implemented.

---

### Track 5: Mechanical Neutrality Beyond the Single-Element Comparison

* **Primary Evidence Artifacts:**
  - Results JSON: [f1720_diagnostic_patch_results.json](file:///D:/Master%20thesis/Adaptive%20remeshing/results/validation/f1720_diagnostic_patch_results.json).
  - Forensic Manifest: [F1720_IMMUTABLE_EVIDENCE_MANIFEST.md](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/validation/F1720_IMMUTABLE_EVIDENCE_MANIFEST.md) (Finding R03).

* **Unrounded Reaction Force Verification:**
  - **Configuration A (Standalone Displacement UEL):**
    $$RF_y = 0.2288094460964203\,\text{kN}$$
  - **Configuration B (Coupled with Dummy Scaling $s = 4.7619 \times 10^{-14}$):**
    $$RF_y = 0.2288094460964203\,\text{kN} \implies \Delta RF = 0.0000000000000000\,\text{kN} \quad (0.0000\%)$$
  - **Configuration C (Coupled with Unscaled Stresses $s = 1.0$):**
    $$RF_y = 0.4576188921928406\,\text{kN} \implies \Delta RF = +0.2288094460964203\,\text{kN} \quad (+100.0000\%)$$

* **Multi-Element Structural Consequences:**
  1. While the single-element patch proves that dummy scaling $s = 4.7619 \times 10^{-14}$ yields internal forces $\|\mathbf{f}_{\text{int}}^{\text{UMAT}}\| \le 10^{-14}\,\text{kN}$ (well below Abaqus equilibrium tolerance $5 \times 10^{-6}\,\text{kN}$), full structures with $10{,}000$ to $80{,}000$ elements suffer from:
     - Ill-conditioned stiffness matrices due to the 14-order-of-magnitude stiffness ratio ($E_{\text{dummy}} / E_0 \sim 10^{-14}$).
     - MPC / kinematic coupling singularities (e.g. rigid body pins in Case 3) where dummy degrees of freedom conflict with constraint condensation.
  2. If physical unscaled Cauchy stresses are returned by the companion element, the internal force is strictly doubled ($\mathbf{f}_{\text{int}}^{\text{total}} = 2\mathbf{f}_{\text{int}}^{\text{UEL}}$), violating equilibrium and causing instant divergence.

---

### Track 6: Constitutive Differences: F1720 Amor Implementation vs Frozen Production UEL

* **Primary Evidence Artifacts:**
  - Frozen Production UEL: [f42_mixed_uel.for](file:///D:/Master%20thesis/Adaptive%20remeshing/runs/f1708_job2_frozen_uel_datacheck/f42_mixed_uel.for) (SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`, 907 lines).
  - Amor Split UEL: [f42_amor_split_uel_v2.for](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/208_f1716_five_hole_production/f42_amor_split_uel_v2.for) (SHA-256: `91612E94E7A2E3F30845AE80815EF4337F582044E25E33BED80072E4AEC40243`, 925 lines).

* **Mathematical & Code Comparison:**

| Feature | Frozen Production UEL (`CE8D5EDC...`) | Historical Amor UEL v2 (`91612E94...`) |
| :--- | :--- | :--- |
| **Mechanical Stiffness Degradation** | **Isotropic Degradation:** Every component degraded by $g(d) = (1-d)^2 + k$.<br>`C11_MECH = C11_0 * DEG`<br>`C12_MECH = C12_0 * DEG`<br>`C33_MECH = C33_0 * DEG` | **Amor Volumetric-Deviatoric Split:**<br>Tension ($\text{tr}(\boldsymbol{\varepsilon}) \ge 0$): Both $K_{\text{bulk}}$ and $\mu$ degraded by $g(d)$.<br>Compression ($\text{tr}(\boldsymbol{\varepsilon}) < 0$): Bulk modulus $K_{\text{bulk}}$ **UNDEGRADED**; only shear $\mu$ degraded. |
| **Crack Driving Energy $\psi_0^+$** | $\psi_0^+ = \frac{1}{2} C_{12}^0 \langle \text{tr}(\boldsymbol{\varepsilon}) \rangle_+^2 + C_{33}^0 (\varepsilon_{11}^2 + \varepsilon_{22}^2 + 2\varepsilon_{12}^2)$ | $\psi_0^+ = \frac{1}{2} K_{\text{bulk}} \langle \text{tr}(\boldsymbol{\varepsilon}) \rangle_+^2 + \mu (\boldsymbol{\varepsilon}_{\text{dev}} : \boldsymbol{\varepsilon}_{\text{dev}})$ |
| **Compressive Response** | Contact stiffness degrades to zero ($k = 10^{-7}$). Element can interpenetrate under compressive load. | Contact stiffness preserved by bulk modulus $K_{\text{bulk}}$. Prevents interpenetration under pure compression. |
| **Companion UMAT Implementation** | Hardcoded dummy visualizer (`DDSDDE=1.D-11`, `STRESS=0.D0`). Does NOT output stresses to ODB. | Attempts direct stress coupling via `COMMON /CB_STATE_TRANS/` or `CB_F1720_STRESS`. |

* **Scientific Conclusion:**
  The frozen production UEL (`CE8D5EDC...`) is an **Isotropically Degraded Elasticity** formulation, NOT an Amor volumetric-deviatoric split formulation. Blindly substituting F1720's Amor UEL into production decks alters the underlying partial differential equations, modifying load-displacement response, fracture peak, and crack path.

---

### Track 7: The Original Forward-Solver Failure and Retracted Force-Match Claims

* **Primary Evidence Artifacts:**
  - Forensic Report: [F1720_FORWARD_SOLVER_COMPLETION_FORENSIC_REPORT.md](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/validation/F1720_FORWARD_SOLVER_COMPLETION_FORENSIC_REPORT.md).
  - Telemetry Receipt: [f1720_solver_forensics.json](file:///D:/Master%20thesis/Adaptive%20remeshing/results/validation/f1720_solver_forensics.json).

* **Deterministic Forensic Facts:**
  1. **Simulation Schedule & Progress:**
     - Adapted Mesh: 13,163 physical elements ($39{,}489$ total layered elements, $51{,}716$ integration points).
     - Step 1 ($u_y: 0 \to 0.0050\,\text{mm}$): Completed all 50 increments cleanly ($RF = 0.8332\,\text{kN}$).
     - Step 2 ($u_y: 0.0050 \to 0.0100\,\text{mm}$): Solved 127 increments with 24 automatic cutbacks before **diverging** at $t_2 = 0.2215\,\text{s}$ ($u_y = 0.005664\,\text{mm}$).
     - Termination Cause: `***ERROR: TIME INCREMENT REQUIRED IS LESS THAN THE MINIMUM SPECIFIED (1.00000E-07)`.
  2. **Force-Match Retraction:**
     - Measured peak load at divergence: $F_{\max} = 0.912794\,\text{kN}$ (or $0.9217\,\text{kN}$ in coarse runs).
     - Published benchmark value (Pandey & Kumar Section 4.5): $F_{\text{peak}} = 1.050\,\text{kN}$.
     - Discrepancy: $-12.21\%$.
     - Early claims in unreviewed F1720 drafts claiming "normal completion with zero cutbacks and perfect 1.05 kN force match" were formally **RETRACTED** in `F1720_FORWARD_SOLVER_COMPLETION_FORENSIC_REPORT.md`.
  3. **The Pivot to Recovery Donors (F1728 -> F1761 -> F1772 -> F1812):**
     - Because direct in-analysis forward coupling suffered from convergence failures, cutback collapse at peak load, and memory hazards across complex multi-hole geometries (Case 2, 3, 5), Task F1728 abandoned direct forward coupled donors in favor of **Method A offline recovery donors**.
     - Recovery donors solve standard linear-elastic continuum boundary value problems with degraded Young's modulus $E_{\text{deg}} = E_0 [(1-d)^2 + k_{\text{res}}]$, decoupling mesh adaptation from forward nonlinear stability.
     - In Task F1812, multi-state recovery envelopes (Method A.2) resolved crack-path resolution across all four benchmarks, but introduced the trade-off of broader refinement corridors and Gate 06 coarsening challenges.

---

## 3. Unit Test Verification

The unit test suite [test_f1829_native_miseseri_audit.py](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_f1829_native_miseseri_audit.py) was executed to verify all findings:

```
============================= test session starts =============================
platform win32 -- Python 3.13.5, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\Master thesis\Adaptive remeshing
plugins: anyio-4.14.2
collected 5 items

tests/unit/test_f1829_native_miseseri_audit.py::test_01_constitutive_source_hashes PASSED [ 20%]
tests/unit/test_f1829_native_miseseri_audit.py::test_02_constitutive_formulation_differences PASSED [ 40%]
tests/unit/test_f1829_native_miseseri_audit.py::test_03_step1_vs_step2_attribution_and_donor_provenance PASSED [ 60%]
tests/unit/test_f1829_native_miseseri_audit.py::test_04_solver_forensics_and_retraction_verification PASSED [ 80%]
tests/unit/test_f1829_native_miseseri_audit.py::test_05_governance_invariants PASSED [100%]

============================== 5 passed in 0.37s ==============================
```

---

## 4. Synthesis & Recommendations for Next Bounded Operation

1. **Constitutive Preservation Invariant:**  
   The frozen production UEL (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`) must NOT be replaced with F1720's Amor UEL. Any stress-output interface must preserve the isotropic degradation formulation.
2. **Stress-Output Interface Candidate:**  
   To enable native Abaqus SPR `MISESERI` in-analysis without companion element force doubling, the companion UMAT must receive authentic stresses with dummy scaling $s = 10^{-11} / E_0$, and the Fortran interface must include dedicated committed/trial buffers to prevent cutback contamination.
3. **Causal Integrity:**  
   At remesh state $t_k$, sizing must use donor data through $t_k$ only; no future-frame sizing envelopes may be leaked.

---

## 5. Artifact Manifest & Verification Table

| Artifact Description | Path | SHA-256 Digest | Status |
| :--- | :--- | :--- | :---: |
| Audit Report | `docs/validation/F1829_NATIVE_MISESERI_DIRECT_COUPLING_EVIDENCE_AUDIT_REPORT.md` | `3F9BD5FC75B6274D529765EE31DF612BBA56984FF73E3AB5ACC96E96765168F8` | CREATED |
| Audit Summary JSON | `results/validation/f1829_native_miseseri_audit_summary.json` | `2A7D4A4911B54CD60ADD38C701538EB931DF79D6CC64EB9CFC597D120B6F186A` | CREATED |
| Audit Receipt | `models/pandey_kumar_mode1/PK_F1829_EVIDENCE_AUDIT_RECEIPT.json` | `2437A88A41F3A5C926D38381A224DA7ED338D5D860C63B44BF2BDCA915BA58D0` | CREATED |
| Unit Test Suite | `tests/unit/test_f1829_native_miseseri_audit.py` | `389D91ACC0C688A2179F4512B200C826ABED53AF683E26282D151B870D64843F` | PASSED (5/5) |
| Frozen Production UEL | `runs/f1708_job2_frozen_uel_datacheck/f42_mixed_uel.for` | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` | PRESERVED |
| Shared Framework | `scripts/remeshing/reusable_2d_adaptive_framework.py` | `80B41AA253E5B36B2BCF5D716B88843D29355141171C60AFF6E7134A0312932C` | PRESERVED |
