# Stage-D Continuous Target Control Diagnostic Package Preparation & Qualification Record

**Task ID**: `F265PREP-M2-STAGE-D-CONTINUOUS-TARGET-CONTROL-DIAGNOSTIC-PACKAGE1`  
**Date**: 18 August 2026  
**Status**: `PACKAGE_QUALIFIED / DATACHECK_PASSED_EXIT_0 / ONE_DIFF_MANIFEST_VERIFIED / NON_SUBMITTING_READY`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Scientific Purpose & Context

- **Diagnostic Objective**: Isolate static mesh discretization/grading sensitivity from state-transfer and staged restart initialization effects.
- **Model Name**: `M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL`
- **Method**: Run a native continuous-from-zero simulation ($U_1 = 0.0 \to 0.050\text{ mm}$) on the **exact physical Stage-D target mesh** (8,836 physical quads, 9,072 physical nodes + RP 99999) with virgin $d=0$ and virgin committed history $\mathcal{H}=0$.

---

## 2. Frozen Cryptographic SHA-256 Hashes

```text
=============================================================================================================
Package File                                          SHA-256 Checksum
----------------------------------------------------  -------------------------------------------------------
M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.inp      cfef365e4509f1c5ae84463f93640e38142ff3623dcdb91778da80e9ac2e0d00
f44_mixed_uel_restart_stateinit.for                   bd2f207cc60302798877ad02b3ba0cd2ac5d3b6f437a5e5f510b4b924597a09f
submit_job.pbs                                        d32ffb2e83744908e1f7982bb3a597c77fb07e6d4c03ef93dd362e76e5df3007
manifest.json                                         9a98db257321288bbd4bc40e7a2b97c0f135ea5dc2356c38260905156640ca84
one_difference_scientific_manifest.json               c3e3dd20c4e1ff9e2ad71ee31eb5c5553eeb40a9a1eb40989adcf4177d468165
=============================================================================================================
```

---

## 3. One-Difference Scientific Manifest Summary

```text
=============================================================================================================
Attribute / Domain               Stage-D Nonmatching Transfer (1390279)  Continuous Target Control (F265)
-------------------------------  --------------------------------------  ------------------------------------
Nodal Coordinates                9,073 nodes + RP 99999 (Identical)      9,073 nodes + RP 99999 (Identical)
Physical Quad Count              8,836 quads (Identical)                 8,836 quads (Identical)
Element Layers                   8,836 Phase U1 + 8,836 Mech U2          8,836 Phase U1 + 8,836 Mech U2
Element Grading Field            Quartic: h_min=0.00263, h_max=0.03018   Quartic: h_min=0.00263, h_max=0.03018
Material PROPS Array             [0.015, 0.0027, 210.0, 0.3, 1e-7, 8836] [0.015, 0.0027, 210.0, 0.3, 1e-7, 8836]
Phase Field Length l0            0.015000 mm                             0.015000 mm
Fracture Toughness Gc            0.002700 N/mm                           0.002700 N/mm
Young's Modulus E                210.0 kN/mm^2 (210 GPa)                 210.0 kN/mm^2 (210 GPa)
Poisson's Ratio nu               0.3000                                  0.3000
Residual Stiffness k             1.0e-07                                 1.0e-07
Boundary Equations (*EQUATION)   Top edge coupled to RP in DOF 1         Top edge coupled to RP in DOF 1
Bottom Boundary (*BOUNDARY)      Clamped (U1 = U2 = 0)                   Clamped (U1 = U2 = 0)
Step Staging & State Ingestion   4-Step Restart Sequence                 1-Step Continuous (ShearStep)
                                 Ingests STAGE_D_COMMITTED_STATE.bin     Virgin d=0, committed H=0
PBS Resources                    1 CPU, 16 GB, 24:00:00, batch           1 CPU, 16 GB, 24:00:00, batch
Notification Channels            Dual-channel Telegram + Email           Dual-channel Telegram + Email
=============================================================================================================
```

---

## 4. Execution Comparison Plan & Falsifiable Hypotheses

1. **Comparison Observables**:
   - Canonical observable: Reference Point Reaction Force ($RP\_RF_1$) vs physical $U_1$.
   - Damage onset displacement $U_{1,\text{damage}}$ and spatial $d(x,y)$ field evolution.
   - Trajectory and residual norm convergence across the critical interval $U_1 \in [0.010143\text{ mm}, 0.011251\text{ mm}]$.
   - All-four-GP committed history $\mathcal{H}$ evolution at matched process-zone physical coordinates.
   - Crack-tip trajectory $(x_{\text{tip}}, y_{\text{tip}})$ overlaid on the continuous element size field $h(x,y)$.
   - Terminal state metrics: physical $U_1$, minimum increment size $dt$, cutback sequence, and active upper-bound node count ($d \ge 0.999$).
2. **Falsifiable Scientific Hypotheses**:
   - **Supports Mesh-Discretization Hypothesis**: If the continuous control exhibits severe cutback cascades and terminates at $U_1 \approx 0.0112\text{ mm}$ when the crack reaches $x \approx 0.09-0.12\text{ mm}$ entering the element grading transition zone ($h = 0.003 \to 0.025\text{ mm}$).
   - **Contradicts Mesh-Discretization Hypothesis**: If the continuous control traverses smoothly through $U_1 = 0.011251\text{ mm}$ and propagates significantly further across the ligament, indicating that the early termination in `1390279.mmaster02` was caused by state-transfer or restart-staging gradient perturbations.

---

## 5. Non-Submitting Qualification Results

- **Input Syntax / Preprocessor**: `PASSED (Exit 0)`
- **Compilation & Linking**: `PASSED (Intel Fortran Classic 2021.13.0 + GNU ld, Exit 0)`
- **Abaqus Standard Datacheck**: `PASSED (Abaqus 2023, Exit 0)`
- **PBS Launcher Audit**: `PASSED` (resources, module purge/load sequence, dual-channel notification hooks, error traps verified).
- **Submission Readiness**: `READY FOR USER AUTHORIZATION` (No submission performed).

---

## 6. Preserved Conservative Scientific Invariants

```text
same_mesh_restart_validation = VALIDATED
history_transfer_rule_resolved = true
selected_production_history_operator = HOST_NEAREST_GP_WITH_NONNEGATIVE_IRREVERSIBILITY
stage_d_nonmatching_transfer_validation = UNDER_FORENSIC_REVIEW
nonmatching_transfer_algorithm_scientifically_unblocked = false
production_adaptive_accuracy_validation_scientifically_unblocked = false
PK10R1_topology_repair_required = true
telegram_delivery_observed = true
email_delivery_observed = true
notification_pre_submission_gate_passed = true
new_submission_authorized = false
qsub_called = false
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```
