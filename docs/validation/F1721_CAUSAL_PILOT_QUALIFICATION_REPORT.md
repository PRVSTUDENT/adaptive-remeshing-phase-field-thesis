# Task F1721: Bounded Causal-Isolation Diagnostic Pilot Technical Qualification Report

**Document ID:** `DOC_F1721_CAUSAL_PILOT_QUALIFICATION_REPORT`  
**Task ID:** `F1721-METHOD-A-POSTPEAK-CONVERGENCE-DIAGNOSIS`  
**Classification:** `rigorous_offline_causal_isolation_qualification_and_plan`  
**Author:** Gemini Antigravity (Autonomous Research Agent)  
**Date:** 12 November 2026  
**Status:** Versioned Bounded Causal-Isolation Pilot Staged & Qualified (Offline Preparation Gate Passed)  
**Supervisory Authorization:** Round 3 Independent Review `HND-F1721-PILOT-QUAL-001` (Decision: `APPROVE`, `approval_scope: VERSIONED_OFFLINE_PILOT_PREPARATION_ONLY`, `next_action: PREPARE_BOUNDED_CAUSAL_ISOLATION_PILOT`)  
**Governing Policy:** Method A Only; Zero New PBS Submissions (`max_new_pbs_submissions = 0`, consumed = 0); Strictly Offline/Controlled Qualification

---

## 1. Executive Summary & Supervisory Directive Compliance

In direct compliance with the Round 3 Independent Scientific Review instructions (`HND-F1721-PILOT-QUAL-001`), this report establishes the bounded causal-isolation diagnostic pilot package (`PK_F1721_CAUSAL_PILOT.inp`) for the 13,163-element five-hole adapted phase-field model.

### Key Supervisory Directives Resolved:
1. **Finding Q01 (Causal Isolation of F1721-H1-R1):** The supervisor observed that changing both the UEL coupling implementation (trial $\to$ committed) and the solver time-incrementation strategy (`*STATIC` automatic $\to$ `*STATIC, DIRECT` 7,000 incs) simultaneously would confound the experiment, preventing unambiguous causal attribution. The causal pilot resolves this by holding the original F1720 automatic incrementation controls strictly constant, isolating the coupling change as the single experimental variable.
2. **Finding Q02 (Bounded Pilot Scope):** The displacement target of Step 2 is shortened from $u_y = 0.0080\,\text{mm}$ (and $0.0100\,\text{mm}$) to $u_y = 0.00580\,\text{mm}$. Because the F1720 failure occurred at $u_y = 0.0056645\,\text{mm}$ and complete crack bridging across Ligament 3 concludes by $u_y \approx 0.00575\,\text{mm}$, targeting $0.00580\,\text{mm}$ spans the entire critical post-peak failure window while eliminating thousands of post-severance increments.
3. **Preservation of Literature-Aligned Candidate:** The full 7,000-increment literature-aligned deck (`PK_F1721_ADAPTED_PILOT.inp`) is strictly preserved bitwise as a subsequent physical-validation candidate.
4. **Governing Safety & Resource Limits Observed:** Strictly ZERO new PBS submissions consumed (`max_new_pbs_submissions = 0`, consumed = 0); zero Abaqus production runs launched; Method A boundary strictly preserved.

---

## 2. Experimental Design & Causal Isolation Architecture

### 2.1 The Two-Dimensional Confounding Problem
In Task F1720, simulation `PK_F1720_ADAPTED_PFM` failed at $u_y = 0.0056645\,\text{mm}$ with:
- **Coupling Implementation:** Uncoupled Picard iteration using trial-state reads (`SV_H_TRIAL`, `SV_PHASE_TRIAL`) in block-diagonal Abaqus solver ($\mathbf{K}_{ud} \equiv \mathbf{0}, \mathbf{K}_{du} \equiv \mathbf{0}$).
- **Incrementation Controls:** Automatic time stepping (`*STATIC`, initial $\Delta t = 0.0025$, minimum $\Delta t_{\min} = 1.0 \times 10^{-9}$, cutbacks enabled).

If the pilot had simultaneously introduced both:
1. Committed-state reads (`SV_H_COMMITTED`, `SV_PHASE_COMMITTED`); and
2. Direct fixed incrementation (`*STATIC, DIRECT`, $\Delta t = 5.0 \times 10^{-5}$, physical rate $\delta u = 1.0\,\text{nm/inc}$ [7.5x finer]);
then a successful post-peak run could have been caused either by the committed-state decoupling OR by the 7.5x finer time step preventing cutbacks.

### 2.2 The Controlled 1-Variable Causal Pilot Design
The causal pilot `PK_F1721_CAUSAL_PILOT.inp` implements a controlled single-variable intervention:

| Experimental Dimension | F1720 Baseline Run | F1721 Literature Candidate | **F1721 Causal Pilot (`PK_F1721_CAUSAL_PILOT.inp`)** |
| :--- | :---: | :---: | :---: |
| **Mesh Configuration** | 13,163 elements (13,402 nodes) | 13,163 elements (13,402 nodes) | **13,163 elements (13,402 nodes) — IDENTICAL** |
| **Overlay Layer** | Dummy scaling $s = 4.7619 \times 10^{-14}$ | Dummy scaling $s = 4.7619 \times 10^{-14}$ | **Dummy scaling $s = 4.7619 \times 10^{-14}$ — IDENTICAL** |
| **Step 1 Procedure** | `*STATIC`, $0.02, 1.0, 10^{-8}, 0.02$ | `*STATIC, DIRECT`, $10^{-4}, 0.20$ | **`*STATIC`, $0.02, 1.0, 10^{-8}, 0.02$ — IDENTICAL TO F1720** |
| **Step 1 Target** | $u_y = 0.0050\,\text{mm}$ (50 incs) | $u_y = 0.0050\,\text{mm}$ (2,000 incs) | **$u_y = 0.0050\,\text{mm}$ (50 incs) — IDENTICAL TO F1720** |
| **Step 2 Procedure** | `*STATIC`, $0.0025, 1.0, 10^{-9}, 0.0025$ | `*STATIC, DIRECT`, $5 \times 10^{-5}, 0.25$ | **`*STATIC`, $0.0025, 0.2666666666667, 10^{-9}, 0.0025$ — IDENTICAL RATE (0.0030 mm/time)** |
| **Step 2 Cutbacks** | Enabled (down to $\Delta t_{\min} = 10^{-9}$) | Disabled (fixed $\Delta t = 5 \times 10^{-5}$) | **Enabled (down to $\Delta t_{\min} = 10^{-9}$) — IDENTICAL TO F1720** |
| **Step 2 Target Disp.** | $u_y = 0.0080\,\text{mm}$ | $u_y = 0.0100\,\text{mm}$ | **$u_y = 0.00580\,\text{mm}$ (Bounded critical window)** |
| **Initial Disp. Inc.** | $\delta u_0 = 7.5\,\text{nm}$ | $\delta u = 1.0\,\text{nm}$ (fixed) | **$\delta u_0 = 7.5\,\text{nm}$ — EXACT MATCH TO F1720** |
| **Min. Disp. Resolution**| $\delta u_{\min} = 3.0 \times 10^{-12}\,\text{mm}$ | Fixed | **$\delta u_{\min} = 3.0 \times 10^{-12}\,\text{mm}$ — EXACT MATCH TO F1720** |
| **UEL Subroutine** | `f1720_direct_coupling_uel.for` | `f1721_proposed_staggered_coupling_uel.for` | **`f1721_proposed_staggered_coupling_uel.for` (COMMITTED READS)** |
| **Variable Under Test** | Baseline failure | Combined intervention | **STRICTLY THE COUPLING FORMULATION (F1721-H1-R1)** |

---

## 3. Input Deck Architecture & Exact Unified Diff

### 3.1 Model Preservation
The model definition region of `PK_F1721_CAUSAL_PILOT.inp` is **100% bitwise identical** to `PK_F1720_ADAPTED_PFM.inp` across all lines between `*USER ELEMENT` (line 7) and the final MPC `*EQUATION` card (line 53,053):
- Exactly 13,402 nodes.
- Exactly 39,489 layered elements (13,163 Layer 1 PF, 13,163 Layer 2 Mech, 13,163 Layer 3 UMAT).
- Exactly 52 top-edge MPC equations tied to master reference node 13402 ($u_{y,j} - u_{y,13402} = 0$).
- All `*NSET` lines wrapped to $\le 16$ entries per line.

### 3.2 Step 1 and Step 2 Definitions
```inp
** ----------------------------------------------------------
** STEP 1: Pre-Critical Loading to u = 0.0050 mm (Identical to F1720 Baseline)
** ----------------------------------------------------------
*STEP, NAME=Step-1, NLGEOM=NO, INC=2500
*STATIC
0.02, 1.0, 1.0e-8, 0.02
*BOUNDARY
N_BOTTOM, 2, 2, 0.0
N_PIN, 1, 1, 0.0
N_RP, 1, 1, 0.0
N_RP, 2, 2, 0.0050
*OUTPUT, FIELD, FREQUENCY=1
*ELEMENT OUTPUT, ELSET=umatelem
S, MISESERI, MISESAVG, EVOL, SDV
*ELEMENT OUTPUT, ELSET=PHASE_ELEM
SDV
*NODE OUTPUT, NSET=N_RP
U, RF
*NODE OUTPUT, NSET=N_BOTTOM
RF
*OUTPUT, HISTORY
*NODE OUTPUT, NSET=N_RP
U2, RF2
*END STEP
** ----------------------------------------------------------
** STEP 2: Critical Fracture Propagation to uy = 0.00580 mm (Bounded Causal Pilot)
** Retains F1720 *STATIC automatic incrementation (dt_initial=0.0025, dt_min=1.0e-9)
** Sets Step 2 time period T2 = 0.2666666666667 to preserve physical loading rate 0.0030 mm/time
** ----------------------------------------------------------
*STEP, NAME=Step-2, NLGEOM=NO, INC=5000
*STATIC
0.0025, 0.2666666666667, 1.0e-9, 0.0025
*BOUNDARY
N_BOTTOM, 2, 2, 0.0
N_PIN, 1, 1, 0.0
N_RP, 1, 1, 0.0
N_RP, 2, 2, 0.00580
*OUTPUT, FIELD, FREQUENCY=1
*ELEMENT OUTPUT, ELSET=umatelem
S, MISESERI, MISESAVG, EVOL, SDV
*ELEMENT OUTPUT, ELSET=PHASE_ELEM
SDV
*NODE OUTPUT, NSET=N_RP
U, RF
*NODE OUTPUT, NSET=N_BOTTOM
RF
*OUTPUT, HISTORY
*NODE OUTPUT, NSET=N_RP
U2, RF2
*END STEP
```

### 3.3 Exact Diff Against F1720 Deck
In Step 2, the **only functional modifications** against `PK_F1720_ADAPTED_PFM.inp` are the matched time period $T_2 = 0.2666666666667$, the bounded target displacement $u_y = 0.00580\,\text{mm}$, and bottom reaction output:
```diff
--- PK_F1720_ADAPTED_PFM.inp
+++ PK_F1721_CAUSAL_PILOT.inp
@@ -53080,2 +53091,2 @@
-*STATIC
-0.0025, 1.0, 1.0e-9, 0.0025
+*STATIC
+0.0025, 0.2666666666667, 1.0e-9, 0.0025
@@ -53086,1 +53097,1 @@
-N_RP, 2, 2, 0.0080
+N_RP, 2, 2, 0.00580
```
plus the addition of `*NODE OUTPUT, NSET=N_BOTTOM` with `RF` to audit reaction force equilibrium. This guarantees that over the shared loading interval $u_y \in [0.0050, 0.0056645]\,\text{mm}$, the physical loading rate $\dot{u}_y = 0.0030\,\text{mm/unit step time}$, the initial displacement increment $\delta u_0 = 7.5\,\text{nm}$, and the minimum displacement resolution $\delta u_{\min} = 3.0\times 10^{-12}\,\text{mm}$ are **strictly identical** to F1720.

---

## 4. Fortran Subroutine Architecture

The causal pilot pairs `PK_F1721_CAUSAL_PILOT.inp` with `f1721_proposed_staggered_coupling_uel.for`, which restores the authentic staggered operator-split contract (Molnár & Gravouil 2017, Pandey & Kumar 2025):
- **Line 401 (Quad PF):** `HIST = SV_H_COMMITTED(PHYSIDX, KPT)`
- **Line 456 (Quad Mech):** `D_VAL = SV_PHASE_COMMITTED(PHYSIDX)`
- **Line 665 (Tri PF):** `HIST = SV_H_COMMITTED(PHYSIDX, 1)`
- **Line 713 (Tri Mech):** `D_VAL = SV_PHASE_COMMITTED(PHYSIDX)`

All trial-state writes (`SV_PHASE_TRIAL`, `SV_H_TRIAL`), `LOP=2` incremental promotion, `LOP=1` cutback rollback, COMMON blocks with Fortran `SAVE` attributes, and dummy scaling ($s = 4.7619 \times 10^{-14}$) are 100% preserved.

---

## 5. Causal Comparison Protocol & Falsification Matrix

Upon authorized execution, `PK_F1721_CAUSAL_PILOT` will be evaluated directly against the recorded telemetry of `PK_F1720_ADAPTED_PFM`:

### Checkpoint Evaluation Matrix:

| Checkpoint / State | Baseline F1720 Result (`f1720_direct_coupling_uel.for`) | Causal Pilot Target (`f1721_proposed_staggered_coupling_uel.for`) | Scientific Causal Deduction |
| :--- | :---: | :---: | :--- |
| **Step 1 Endpoint** ($u_y = 0.0050\,\text{mm}$) | 50 incs, 0 cutbacks, $F = 0.833201\,\text{kN}$, $d_{\max} = 0.248112$ | 50 incs, 0 cutbacks, $F \approx 0.8332\,\text{kN}$, $d_{\max} \approx 0.248$ | Confirms identical pre-peak trajectory under automatic incrementation |
| **Peak Tensile Force** ($u_y = 0.0056638\,\text{mm}$) | $F_{\max} = 0.921726\,\text{kN}$, $d_{\max} = 0.4676$ | $F_{\max} \in [0.915, 0.930]\,\text{kN}$, $d_{\max} \approx 0.47$ | Peak load parity within $\pm 1\%$ |
| **F1720 Failure Point** ($u_y = 0.0056645\,\text{mm}$) | **DIVERGED** (dt < 1e-9, 24 cutbacks, Node 3292 / Nodes 3286/3909/4508) | **CONVERGES** (advances without cutback exhaustion) | **Evidence supporting Hypothesis F1721-H1-R1**: Picard loop removal significantly improves convergence |
| **Crack Bridging Complete** ($u_y \approx 0.00575\,\text{mm}$) | Not reachable | Reached; Ligament 3 completely severed ($d \to 1.0$) | Verification of physical crack bridging under automatic incrementation |
| **Pilot Target Endpoint** ($u_y = 0.00580\,\text{mm}$) | Not reachable | Reached cleanly; post-peak load drops toward plateau (~$0.6\,\text{kN}$) | Bounded pilot completion |
| **Cutback Behavior** | 24 cutbacks culminating in solver stall | Solver either advances without cutbacks or successfully recovers from cutbacks | Robustness under automatic time stepping |

### Predeclared Conditional Falsification Logic:
In strict compliance with independent review directives (CP-R03 and CP-R04), experimental outcomes will be evaluated under the following conditional framework:
1. **Conditional PASS (Support for Hypothesis F1721-H1-R1):**
   If `PK_F1721_CAUSAL_PILOT` successfully surpasses $u_y = 0.0056645\,\text{mm}$ and reaches $u_y = 0.00580\,\text{mm}$ under the exact same automatic incrementation controls and physical loading rate as F1720, this result will be classified as **strong empirical evidence supporting Hypothesis F1721-H1-R1** (that the uncoupled Picard loop contributed substantially to the stall). Subsequent comparison against the literature candidate (`PK_F1721_ADAPTED_PILOT.inp`) will independently evaluate the physical-response differences and temporal lag introduced by the committed-state operator split.
2. **Conditional FAIL (Weakening of Sufficiency Claim):**
   If `PK_F1721_CAUSAL_PILOT` diverges identically at $u_y = 0.0056645\,\text{mm}$ with cutback exhaustion down to $1.0 \times 10^{-9}$, this result will **weaken the sufficiency claim** for the committed-state decoupling alone in this tested configuration. Further candidate causes (such as finer fixed incrementation, tangent consistency, or structural snap-through instability) remain undetermined until independently investigated.
3. **INDETERMINATE Outcome:**
   If `PK_F1721_CAUSAL_PILOT` surpasses $u_y = 0.0056645\,\text{mm}$ but stalls at an intermediate displacement $u_y \in (0.0056645, 0.00580)\,\text{mm}$, this will indicate partial stabilization, requiring granular inspection of local Jacobian determinants, cutback histories, and damage profiles before attributing causation.

---

## 6. Cryptographic Evidence Ledger

All artifacts are live on GitHub https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis:

| Artifact Description | File Path | Size (Bytes) | SHA-256 Checksum | Classification |
| :--- | :--- | :---: | :---: | :--- |
| **Causal Pilot Input Deck** | `models/pandey_kumar_mode1/214_f1720_adapted_mesh/PK_F1721_CAUSAL_PILOT.inp` | 1,780,955 | `23525C2AB9A62A461D6489803FE3D679A80840D58E13339517F9539838170E95` | Staged & Qualified (T2=0.2667) |
| **Literature Pilot Deck** | `models/pandey_kumar_mode1/214_f1720_adapted_mesh/PK_F1721_ADAPTED_PILOT.inp` | 1,780,773 | `0FCD33CF72BA9631CB0122AA38346CF51829EF9CF154497C3E80862820247E6E` | Bitwise Preserved |
| **Frozen F1720 Deck** | `models/pandey_kumar_mode1/214_f1720_adapted_mesh/PK_F1720_ADAPTED_PFM.inp` | 1,780,248 | `318D0ED6F330E73F5A62E259DC3A9A9ABCEBD4341596EAA5C31ED58138BA42F2` | 100% Bitwise Frozen |
| **Proposed Subroutine** | `models/pandey_kumar_mode1/214_f1720_adapted_mesh/f1721_proposed_staggered_coupling_uel.for` | 38,655 | `2ECEB8B3B945D56A53D94B9D853F07D59BC2467901CD26DF614D8BA3E5604E5C` | Sourced & Qualified |
| **Frozen F1720 UEL** | `models/pandey_kumar_mode1/214_f1720_adapted_mesh/f1720_direct_coupling_uel.for` | 38,309 | `C298ACA7ED2199B20E622B38E99FDA9B533150EB0AD5E9F77069216F860E70FC` | 100% Bitwise Frozen |
| **Proposed Patch** | `docs/validation/f1721_staggered_coupling_proposed.patch` | 2,752 | `A55648850D5402A3FECFEC5D2E608BCDF671C3F6ABFA00AF98C2A1597CFB40CA` | Verified Diff |
| **Causal Deck Generator** | `scripts/model_generation/generate_f1721_causal_pilot_deck.py` | 6,298 | `F7577347D7A5F5E445F838AD33832D6E4794B86AF67857D312E046F9A4B4EBED` | Deterministic Build |
| **Causal Pilot Unit Tests** | `tests/unit/test_f1721_causal_pilot_qualification.py` | 9,759 | `F032C81BBE17B3049E2B53307875FE1E22FDB6FB6DFC6B8EC51263226A01B7A1` | 8/8 PASS in 0.49s |
| **Literature Pilot Tests** | `tests/unit/test_f1721_pilot_technical_qualification.py` | 7,639 | `BCF014F00E88BA9A731F253FEF8A6B1C52E7428807F9E3618E7F0FFC28E0D7B2` | 8/8 PASS in 0.46s |
| **Diagnosis Unit Tests** | `tests/unit/test_f1721_postpeak_convergence_diagnosis.py` | 7,120 | `379619369F0F5BDAE37569DA233E29587EF7B7280ACAD3A67F4D4473178117B8` | 8/8 PASS in 0.32s |
| **Combined Test Pass** | All F1720 + F1721 test files (9 test suites) | Multiple | 56 Tests Total | 56/56 PASS in 2.91s |

---

## 7. Conclusion & Governance Closeout

The offline technical qualification package for the Task F1721 bounded causal-isolation diagnostic pilot has been rigorously corrected per supervisory directives:
1. Physical loading rate ($\dot{u}_y = 0.0030\,\text{mm/unit time}$), initial increment ($\delta u_0 = 7.5\,\text{nm}$), and minimum resolution ($\delta u_{\min} = 3.0\times 10^{-12}\,\text{mm}$) match F1720 exactly via $T_2 = 0.2666666666667$.
2. Epistemic interpretations have been carefully calibrated with conditional PASS, FAIL, and INDETERMINATE categories.
3. 56 automated tests pass cleanly offline.
4. Strictly ZERO new PBS submissions consumed (`max_new_pbs_submissions = 0`, consumed = 0); zero Abaqus runs; Method A boundary strictly preserved.

Submitted for independent review under correlation `HND-F1721-CAUSAL-PILOT-002`.
