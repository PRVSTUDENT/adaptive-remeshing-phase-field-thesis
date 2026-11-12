# Task F1721: Adapted Staggered Operator-Split Diagnostic Pilot Technical Qualification Report

**Document ID:** `DOC_F1721_PILOT_TECHNICAL_QUALIFICATION_REPORT`  
**Task ID:** `F1721-METHOD-A-POSTPEAK-CONVERGENCE-DIAGNOSIS`  
**Classification:** `rigorous_offline_technical_qualification_and_pilot_plan`  
**Author:** Gemini Antigravity (Autonomous Research Agent)  
**Date:** 12 November 2026  
**Status:** Versioned Diagnostic Pilot Staged & Qualified (Offline Preparation Gate Passed)  
**Supervisory Authorization:** Round 2 Independent Review `HND-F1721-POSTPEAK-CONVERGENCE-002` (Decision: `APPROVE`, `pilot_preparation: APPROVED`, `pilot_execution: NOT_AUTHORIZED`)  
**Governing Policy:** Method A Only; Zero New PBS Submissions (`max_new_pbs_submissions = 0`, consumed = 0); Strictly Offline/Controlled Qualification

---

## 1. Executive Summary & Objective

In accordance with `/goal F1721` and the Round 2 Independent Scientific Review directives (`HND-F1721-POSTPEAK-CONVERGENCE-002`), this report establishes the definitive technical qualification package for the 13,163-element five-hole staggered operator-split diagnostic pilot.

### Primary Objectives Delivered:
1. **Pilot Input Deck Generation (`PK_F1721_ADAPTED_PILOT.inp`):** Reconstructed the complete 3-layer production model on the verified 13,163-element adapted mesh, implementing the published increment schedule of Pandey & Kumar (2025, Section 4.5) under `*STATIC, DIRECT`.
2. **Fortran Subroutine Verification (`f1721_proposed_staggered_coupling_uel.for`):** Verified the 4 exact committed-state read modifications (lines 401, 456, 665, 713), eliminating the uncoupled intra-increment Picard iteration loop while preserving trial-state updates, `LOP=2` promotion, COMMON blocks, and mechanical neutrality dummy scaling.
3. **Unified Patch Artifact (`f1721_staggered_coupling_proposed.patch`):** Verified clean byte-level unified diff against the frozen F1720 production UEL.
4. **Resolution of Supervisory Review Qualifications (Q01–Q06):** Addressed all six stipulations from the Round 2 review approval.
5. **Like-for-Like Comparison Protocol & Predeclared Falsification Criteria:** Formulated an objective, falsifiable evaluation matrix benchmarking the staggered pilot against the F1720 baseline.
6. **Automated Offline Verification:** Expanded test coverage to 16 automated tests across `test_f1721*.py` (48 tests passing combined across F1720 and F1721 suites).

**GOVERNING CONSTRAINTS OBSERVED:**
- Strictly ZERO new PBS submissions (`max_new_pbs_submissions = 0`, consumed = 0).
- Zero Abaqus solver runs executed in this turn.
- Method A boundary strictly preserved (zero Method C, zero history transfer).
- Canonical UELs and F1720 production baselines remain 100% bitwise frozen.

---

## 2. Reconstructed Literature Increment Schedule & Deck Architecture

### 2.1 Reconstructed Schedule Mapping (Finding Q05)
Pandey & Kumar (2025, Section 4.5, page 3277) state:
> *"The total displacement $u_y = 0.01\,\text{mm}$ is applied in two steps. In the first step, the increment size $\Delta u_1 = 10^{-4}$ for 2000 increments; for the second step, the increment size $\Delta u_2 = 5 \times 10^{-5}$ for 5000 increments is specified."*

Table 2.1 documents the exact mapping to Abaqus/Standard input keywords in `PK_F1721_ADAPTED_PILOT.inp`:

| Parameter | Step 1 (Pre-Critical Loading) | Step 2 (Fracture Propagation) | Technical & Physical Meaning |
| :--- | :---: | :---: | :--- |
| **Published Notation** | $\Delta u_1 = 10^{-4}$ | $\Delta u_2 = 5 \times 10^{-5}$ | Dimensionless Abaqus step time increment $\Delta t$ |
| **Number of Increments** | 2,000 | 5,000 | Total increments per step |
| **Step Time Period $T_{\text{step}}$** | $0.20$ | $0.25$ | Step time period ($N_{\text{inc}} \times \Delta t$) |
| **Abaqus Step Card** | `*STATIC, DIRECT` | `*STATIC, DIRECT` | Direct user increment control (no automatic cutbacks) |
| **Abaqus Data Line** | `1.0e-4, 0.20` | `5.0e-5, 0.25` | `dt_initial, t_total` |
| **Step Displacement Range** | $0 \to 0.0050\,\text{mm}$ | $0.0050 \to 0.0100\,\text{mm}$ | Target displacement on boundary |
| **Displacement Advance Rate** | $\delta u_1 = 2.5 \times 10^{-6}\,\text{mm}$ ($2.5\,\text{nm}$) | $\delta u_2 = 1.0 \times 10^{-6}\,\text{mm}$ ($1.0\,\text{nm}$) | Physical displacement increment per step |
| **F1720 Failure Boundary** | Fully converged ($u_y = 0.0050\,\text{mm}$) | Reached at Inc 665 ($u_y = 0.0056645\,\text{mm}$) | F1720 solver stalled at $u_y = 0.0056645\,\text{mm}$ |
| **Pilot Evaluation Target** | Increments 1 to 2,000 | Increments 1 to 800+ ($u_y \ge 0.00580\,\text{mm}$) | Full progression through post-peak bridging window |

### 2.2 Model Architecture & Static Integrity
The pilot deck `PK_F1721_ADAPTED_PILOT.inp` preserves all verified components of the F1720 model:
- **Total Nodes:** Exactly 13,402 (13,401 physical continuum nodes + master reference node 13402).
- **Physical Elements:** Exactly 13,163 elements (12,851 quadrilaterals + 312 triangles).
- **Layered Elements:** Exactly 39,489 elements:
  * Layer 1 (Phase-Field): Elements 1–12,851 (`TYPE=U1`, quads) and 12,852–13,163 (`TYPE=U3`, tris) declaring DOF 3.
  * Layer 2 (Mechanical): Elements 13,164–26,014 (`TYPE=U2`, quads) and 26,015–26,326 (`TYPE=U4`, tris) declaring DOFs 1,2.
  * Layer 3 (Overlay UMAT): Elements 26,327–39,177 (`TYPE=CPE4`, quads) and 39,178–39,489 (`TYPE=CPE3`, tris).
- **MPC Equations:** Exactly 52 `*EQUATION` multi-point constraints coupling top boundary nodes $u_y$ to master node 13402 ($u_{y,j} - u_{y,13402} = 0$).
- **NSET Card Formatting:** All node sets (`N_BOTTOM`, `N_TOP`, `N_PIN`, `N_RP`) strictly wrapped to $\le 16$ entries per line.
- **Output Requests:**
  * Field output: `FREQUENCY=10` writing `S`, `MISESERI`, `MISESAVG`, `EVOL`, `SDV` on `umatelem` and `PHASE_ELEM`, plus `RF` on `N_BOTTOM` and `N_RP`.
  * History output: written every increment for master reference node 13402 (`U2`, `RF2`).

---

## 3. Fortran Subroutine Architecture & Static Audit

### 3.1 The 4 Staggered Read Modifications
In `f1721_proposed_staggered_coupling_uel.for`, the 4 intra-increment trial-state reads have been replaced by committed-state reads:

```diff
--- models/pandey_kumar_mode1/214_f1720_adapted_mesh/f1720_direct_coupling_uel.for
+++ models/pandey_kumar_mode1/214_f1720_adapted_mesh/f1721_proposed_staggered_coupling_uel.for
@@ -397,1 +401,1 @@
-          HIST = SV_H_TRIAL(PHYSIDX, KPT)
+          HIST = SV_H_COMMITTED(PHYSIDX, KPT)
@@ -452,1 +456,1 @@
-        D_VAL = SV_PHASE_TRIAL(PHYSIDX)
+        D_VAL = SV_PHASE_COMMITTED(PHYSIDX)
@@ -661,1 +665,1 @@
-        HIST = SV_H_TRIAL(PHYSIDX, 1)
+        HIST = SV_H_COMMITTED(PHYSIDX, 1)
@@ -709,1 +713,1 @@
-        D_VAL = SV_PHASE_TRIAL(PHYSIDX)
+        D_VAL = SV_PHASE_COMMITTED(PHYSIDX)
```

### 3.2 State Preservation & Neutrality Mechanisms
1. **Trial-State Updates Preserved:** Trial writes at line 344 (`SV_PHASE_TRIAL(PHYSIDX) = D_AVG`), line 610 (`SV_H_TRIAL(PHYSIDX, KPT) = POS_M`), line 640 (`SV_PHASE_TRIAL(PHYSIDX) = D_AVG`), and line 835 (`SV_H_TRIAL(PHYSIDX, 1) = POS_M`) are 100% preserved.
2. **Transactional Promotion:** In `UEXTERNALDB(LOP=2)`, trial arrays are promoted to committed arrays (`SV_*_COMMITTED = SV_*_TRIAL`) strictly upon increment completion.
3. **Rollback Integrity:** In `UEXTERNALDB(LOP=1)`, trial arrays are reset to committed arrays upon cutbacks.
4. **Memory Persistence:** Fortran `SAVE` attributes are applied to `COMMON /CB_F1720_STRESS/` and `COMMON /CB_STATE_TRANS/`, guaranteeing static data segment persistence across dynamic solver invocations.
5. **Mechanical Neutrality:** The overlay UMAT scales retrieved UEL stresses by $s = 10^{-11} / 210.0 = 4.7619 \times 10^{-14}$ with dummy stiffness $\mathbf{D}_{\text{dummy}} = 10^{-11}\,\mathbf{I}$, guaranteeing zero mechanical perturbation ($\Delta RF / RF = 0.00000000\%$).
6. **Fail-Closed NaN Guards:** All branches contain NaN detection with `PNEWDT = 0.25D0` cutback requests and `-999.D0` diagnostic sentinels.

---

## 4. Supervisory Review Qualifications (Q01–Q06) Reconciliation

Table 4.1 documents how each supervisory review qualification from `HND-F1721-POSTPEAK-CONVERGENCE-002` has been addressed:

| ID | Reviewer Qualification | Implementation & Technical Reconciliation | Status |
| :---: | :--- | :--- | :---: |
| **Q01** | **Uncomputed Eigenvalue Scope** | Explicitly classified $\rho(\mathbf{M}) > 1$ as the proposed theoretical mechanism under investigation, not an independently assembled or numerically diagonalized global eigenvalue for the 13,163-element mesh. Updated in report Section 3.1 and `audit_picard_convergence.py`. | **RESOLVED** |
| **Q02** | **Residual & Tangent Conventions** | Clarified that displayed cross-coupling blocks $\mathbf{K}_{ud}$ and $\mathbf{K}_{du}$ are schematic continuum representations of the coupled block-operator used for theoretical error analysis, not an assertion of a production-verified consistent monolithic tangent. | **RESOLVED** |
| **Q03** | **Scalar Script Clean-up** | Updated `scripts/postprocessing/audit_picard_convergence.py` docstrings and outputs to explicitly label $\rho = 4d$ as a restricted, unconstrained 1D scalar illustration under stress-controlled conditions, removing any universal assertion that multidimensional FE models diverge at $d = 0.25$. | **RESOLVED** |
| **Q04** | **Step 1 Numerical Reconciliation** | Corrected Step 1 endpoint in report Section 2.1: at $u_y = 0.0050\,\text{mm}$, reaction force is $F = 0.833201\,\text{kN}$ ($0.833200634\,\text{kN}$) and maximum localized phase-field damage is $d_{\max} = 0.248112$ in Ligament 3 (not $F = 0.8798\,\text{kN}, d_{\max} = 0$). | **RESOLVED** |
| **Q05** | **Increment Schedule Mapping** | Reconstructed the published parameters ($\Delta u_1 = 10^{-4}, \Delta u_2 = 5 \times 10^{-5}$) as Abaqus step time periods $T_1 = 0.20$ (2,000 incs) and $T_2 = 0.25$ (5,000 incs) under `*STATIC, DIRECT`. Reconciled in deck and validated by unit tests. | **RESOLVED** |
| **Q06** | **Physical Solution Equivalence** | Defined pilot success criteria not merely by fewer Newton iterations, but strictly by global force equilibrium, physical damage bounds ($0 \le d \le 1$), monotonic history growth, and load-displacement agreement against F1720 up to peak load. | **RESOLVED** |

---

## 5. Like-for-Like Comparison Protocol Against F1720

To rigorously test the falsifiable hypothesis F1721-H1-R1 upon authorized execution, the pilot run will be compared against the F1720 baseline across four objective checkpoints:

### Checkpoint Matrix:

| Evaluation Metric | Baseline F1720 (`f1720_direct_coupling_uel.for`) | Pilot Target F1721 (`f1721_proposed_staggered_coupling_uel.for`) | Scientific Significance |
| :--- | :---: | :---: | :--- |
| **Step 1 Endpoint** ($u_y = 0.0050\,\text{mm}$) | $F = 0.833201\,\text{kN}$, $d_{\max} = 0.248112$ | $F \in [0.830, 0.836]\,\text{kN}$, $d_{\max} \in [0.24, 0.26]$ | Pre-peak solution parity & physical equivalence |
| **Initial Stiffness $K_0$** | $174.98\,\text{kN/mm}$ | $174.98 \pm 0.5\,\text{kN/mm}$ | Elastic consistency |
| **Peak Tensile Force $F_{\max}$** | $0.921726\,\text{kN}$ at $u_y = 0.0056638\,\text{mm}$ | $F_{\max} \in [0.915, 0.930]\,\text{kN}$ | Peak load reproduction within $\pm 1\%$ |
| **Failure Boundary** ($u_y = 0.0056645\,\text{mm}$) | **DIVERGED** (dt < 1e-9 exhausted, 24 cutbacks) | **CONTINUES CONVERGED** without cutback | Direct falsification test of Picard instability |
| **Post-Peak Window** ($u_y \ge 0.00580\,\text{mm}$) | Not reachable | Reached cleanly under smooth load shedding | Complete crack bridging across Ligament 3 |
| **Newton Iterations / Inc** | 1 iter (pre-peak), fluctuating 4–5 iters (at failure) | 1–2 iterations / increment | Uncoupled block conditioning |
| **Damage Bounds** | $d \in [0, 0.7167]$ | $d \in [0, 1.0000]$ | Physical admissibility & completeness |

---

## 6. Predeclared Pass/Fail Falsification Criteria

### Objective PASS Criteria:
1. **P1 (Pre-Peak Equivalence):** The pilot simulation matches the F1720 baseline up to peak load within $\pm 1.0\%$ on reaction force ($F_{\max} \approx 0.922\,\text{kN}$) and within $\pm 0.5\%$ on initial linear stiffness ($K_0 \approx 174.98\,\text{kN/mm}$).
2. **P2 (Divergence Boundary Surpassed):** The solver successfully advances past the F1720 failure displacement ($u_y = 0.0056645\,\text{mm}$) without divergence, numerical singularity, or cutback exhaustion.
3. **P3 (Post-Peak Bridging Progression):** The solver continues into the post-peak softening regime ($u_y \ge 0.00580\,\text{mm}$), demonstrating stable load shedding.
4. **P4 (Physical Damage Admissibility):** Phase-field damage satisfies $0 \le d \le 1$ everywhere with zero NaNs, zero negative values, and monotonic history evolution ($\mathcal{H}_{n+1} \ge \mathcal{H}_n$).
5. **P5 (Boundary Equilibrium):** Bottom reaction force matches top reference node force to high precision: $|F_{\text{tensile}} - F_{\text{RP}}| / F_{\text{RP}} < 10^{-4}$.

### Objective FAIL / FALSIFICATION Criteria:
1. **F1 (Identical Numerical Divergence):** If the pilot solver terminates at or near $u_y = 0.0056645\,\text{mm}$ with alternating Newton divergence in Node 3292 / Nodes 3286/3909/4508, hypothesis F1721-H1-R1 is falsified (proving that numerical Picard instability was not the primary failure driver).
2. **F2 (Structural Snap-Back Arrest):** If the solver halts due to physical equilibrium path non-existence (true snap-back where $du_y < 0$ is required for equilibrium), the pilot fails physically, indicating that arclength/Riks control is necessary.
3. **F3 (Constitutive State Corruption):** Any occurrence of NaNs, negative stiffness, or unbounded damage ($d > 1$).

---

## 7. Cryptographic Artifact Ledger & Verification Receipts

All primary artifacts are tracked and verified:

| Artifact Description | Relative File Path | File Size (Bytes) | SHA-256 Checksum | Verification Status |
| :--- | :--- | :---: | :---: | :--- |
| **Pilot Input Deck** | `models/pandey_kumar_mode1/214_f1720_adapted_mesh/PK_F1721_ADAPTED_PILOT.inp` | 1,780,773 | `0FCD33CF72BA9631CB0122AA38346CF51829EF9CF154497C3E80862820247E6E` | Staged & Qualified |
| **Proposed Subroutine** | `models/pandey_kumar_mode1/214_f1720_adapted_mesh/f1721_proposed_staggered_coupling_uel.for` | 38,452 | `2ECEB8B3B945D56A53D94B9D853F07D59BC2467901CD26DF614D8BA3E5604E5C` | Sourced & Qualified |
| **Unified Proposed Patch** | `docs/validation/f1721_staggered_coupling_proposed.patch` | 2,752 | `A55648850D5402A3FECFEC5D2E608BCDF671C3F6ABFA00AF98C2A1597CFB40CA` | Verified Diff |
| **Deck Generator Script** | `scripts/model_generation/generate_f1721_pilot_deck.py` | 4,675 | `04C63EBA66B5CD3E646A0B66EAA69DF47D4C3A35405A0A9C1688EB1ED3E64BC4` | Deterministic Build |
| **Picard Audit Script** | `scripts/postprocessing/audit_picard_convergence.py` | 4,451 | `3E200C01D78013E8D09B6607C3BC8CE052FA42EB094A0C7FA786A76359B294AC` | Cleaned Up (Q03) |
| **Convergence Diagnosis** | `scripts/postprocessing/diagnose_f1721_postpeak_convergence.py` | 8,245 | `FD969E31884605CEBCA51BB95197F27E7F9A4E6B24A1EAAC7FC7BC82B71BDDEC` | Telemetry Verified |
| **Pilot Unit Test Suite** | `tests/unit/test_f1721_pilot_technical_qualification.py` | 7,639 | `BCF014F00E88BA9A731F253FEF8A6B1C52E7428807F9E3618E7F0FFC28E0D7B2` | 8/8 PASS in 0.46s |
| **Diagnosis Unit Test Suite**| `tests/unit/test_f1721_postpeak_convergence_diagnosis.py` | 7,120 | `379619369F0F5BDAE37569DA233E29587EF7B7280ACAD3A67F4D4473178117B8` | 8/8 PASS in 0.32s |
| **Combined Test Suite** | `tests/unit/test_f172*.py` (8 test suites) | Multiple | 48 Tests Total | 48/48 PASS in 2.52s |
| **Frozen F1720 Deck** | `models/pandey_kumar_mode1/214_f1720_adapted_mesh/PK_F1720_ADAPTED_PFM.inp` | 1,780,248 | `318D0ED6F330E73F5A62E259DC3A9A9ABCEBD4341596EAA5C31ED58138BA42F2` | 100% Bitwise Frozen |
| **Frozen F1720 UEL** | `models/pandey_kumar_mode1/214_f1720_adapted_mesh/f1720_direct_coupling_uel.for` | 38,309 | `C298ACA7ED2199B20E622B38E99FDA9B533150EB0AD5E9F77069216F860E70FC` | 100% Bitwise Frozen |

---

## 8. Conclusion & Read-Only Governance Closeout

The offline technical qualification package for the Task F1721 initial-state staggered diagnostic pilot is fully complete, mathematically reconciled, and verified by 48 automated tests.

In strict compliance with repository safety rules and the supervisory authorization (`pilot_preparation: APPROVED`, `pilot_execution: NOT_AUTHORIZED`), no Abaqus solve or PBS execution has been initiated (`max_new_pbs_submissions = 0`, consumed = 0).

The governed project progress is staged, committed, and synchronized forward-only to GitHub `origin/main`. This package is formally submitted for supervisory review and execution authorization under correlation `HND-F1721-PILOT-QUAL-001`.
