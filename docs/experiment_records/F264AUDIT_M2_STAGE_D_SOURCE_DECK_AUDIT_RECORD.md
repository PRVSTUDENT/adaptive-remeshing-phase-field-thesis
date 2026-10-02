# Stage-D Source-Deck Mesh Layers, Material Properties, 4-GP History & Termination Audit Record

**Task ID**: `F264AUDIT-M2-STAGE-D-SOURCE-DECK-MESH-PROPERTIES-AND-4GP-AUDIT1`  
**Date**: 18 August 2026  
**Status**: `SOURCE_DECK_AUDITED / 4GP_HISTORY_VERIFIED / MESH_LAYERS_RESOLVED / GATES_HELD_CONSERVATIVE`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Physical Mesh Layer Classification & Reconciled Facts

Direct parsing of element connectivity and nodal coordinates from `M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL.inp` and `M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.inp`:

```text
=============================================================================================================
Mesh Metric / Layer              Native Bounded Control (1390278)       Stage-D Nonmatching Transfer (1390279)
-------------------------------  -------------------------------------  -------------------------------------
Physical Nodes (excl. RP)        12,383 nodes                           9,074 nodes
Physical Quads (Geometric Cells) 12,064 quads                           8,836 quads
Phase Layer Elements (Type U1)   12,064 elements (JTYPE=1, DOF 3)       8,836 elements (JTYPE=1, DOF 3)
Mech Layer Elements (Type U2)    12,064 elements (JTYPE=2, DOF 1,2)     8,836 elements (JTYPE=2, DOF 1,2)
Vis Layer Elements (Type CPE4)   12,064 elements (Dummy Visualization)  0 elements
Total ODB Elements (Deck Total)  36,192 elements                        17,672 elements
Global Element Size h_min        0.003018 mm (3.02 um)                  0.002632 mm (2.63 um)
Global Element Size h_max        0.030178 mm (30.18 um)                 0.030178 mm (30.18 um)
Global Mean Element Size h       0.012413 mm                            0.013907 mm
Process Zone Mean h ([-0.1,0.1]) 0.007760 mm                            0.004452 mm
Ligament Mean h (y=0, x in [0,0.5]) 0.005132 mm                         0.010958 mm
Maximum Aspect Ratio             10.0499 (Mean: 7.1996)                 9.5525 (Mean: 2.7229)
=============================================================================================================
```

- **Reconciliation of F262 Scratch Discrepancy**:
  - In F262, total stacked ODB element counts ($36,192$ and $17,672$) were mistakenly cited as physical element counts. The true physical quad counts are **$12,064$** (Native) and **$8,836$** (Stage-D).
  - The actual physical element sizes in the process zone are $h \approx 0.0026-0.0078\text{ mm}$ ($h/l_0 \approx 0.17-0.52$).

---

## 2. Reconciled Material Parameters from UEL Property Arrays

Direct inspection of `PROPS(1..6)` in Fortran subroutine `f44_mixed_uel_restart_stateinit.for`:

```text
=============================================================================================================
Property Name        Fortran Variable  Deck Value (Native & Stage-D)   Units / Description
-------------------  ----------------  ------------------------------  --------------------------------------
Phase Field Length   E_L0 = PROPS(1)   0.015000 mm (15.0 um)           Established crack regularization scale
Fracture Toughness   E_GC = PROPS(2)   0.002700 N/mm (2.7 J/m^2)       Critical energy release rate
Young's Modulus      E_MOD = PROPS(3)  210.0 kN/mm^2 (210 GPa)         Isotropic elastic modulus
Poisson's Ratio      E_NU = PROPS(4)   0.3000                          Isotropic Poisson's ratio
Residual Stiffness   E_K  = PROPS(5)   1.000000e-07                    Degradation regularization parameter
Physical Quad Count  N_PHYS = PROPS(6) 12064 (Native) / 8836 (Stage-D) Layer element offset
=============================================================================================================
```

- **Process-Zone Discretization Ratio ($h/l_0$)**:
  - Native Control: $h_{\text{pz}} / l_0 = 0.007760 / 0.015000 = \mathbf{0.5173}$ (at notch tip: $0.003018 / 0.015000 = \mathbf{0.2012}$).
  - Stage-D Transfer: $h_{\text{pz}} / l_0 = 0.004452 / 0.015000 = \mathbf{0.2968}$ (at notch tip: $0.002632 / 0.015000 = \mathbf{0.1755}$).

---

## 3. Four-GP Committed History Audit (`STAGE_D_COMMITTED_STATE.bin`)

- **File Architecture**:
  - Record 1: `SV_ELEM_NODAL_PHASE_COM(100000, 4)` = $3,200,000\text{ bytes}$ (Double Precision).
  - Record 2: `SV_H_COMMITTED(100000, 4)` = $3,200,000\text{ bytes}$ (Double Precision).
  - Total Size: $6,400,016\text{ bytes}$ (exact binary match).
- **All 8,836 Elements $\times$ 4 Gauss Points ($35,344$ values)**:
  - $\min \mathcal{H} = 1.096641 \times 10^{-11}\text{ MPa} \ge 0.0$ (**Strictly Non-negative**).
  - $\max \mathcal{H} = 0.848870\text{ MPa}$ at the notch tip.
- **Representative Process-Zone Elements**:

```text
=============================================================================================================
Elem ID  | Centroid (x, y)  | H_GP1 (MPa)  | H_GP2 (MPa)  | H_GP3 (MPa)  | H_GP4 (MPa)  | max_d (Nodes)
-------------------------------------------------------------------------------------------------------------
3695     | (-0.049, -0.020) | 2.2484e-03   | 2.2484e-03   | 2.2484e-03   | 2.2484e-03   | 0.0346
4641     | (-0.033, +0.007) | 3.5652e-04   | 3.5652e-04   | 2.9059e-04   | 2.9059e-04   | 0.0212
4084     | (-0.014, -0.009) | 1.0841e-02   | 1.4224e-02   | 1.1337e-02   | 1.5831e-02   | 0.1539
5030     | (+0.001, +0.017) | 1.4707e-02   | 1.7489e-02   | 9.1240e-03   | 1.0253e-02   | 0.1246
4473     | (+0.020, +0.001) | 1.8652e-02   | 1.6987e-02   | 1.7208e-02   | 1.5869e-02   | 0.1535
3916     | (+0.038, -0.014) | 6.0865e-03   | 5.6214e-03   | 6.3732e-03   | 5.8428e-03   | 0.0765
4862     | (+0.055, +0.012) | 4.5222e-03   | 4.4226e-03   | 4.9010e-03   | 4.8044e-03   | 0.0543
4305     | (+0.096, -0.004) | 1.9802e-03   | 1.8081e-03   | 1.9520e-03   | 1.7828e-03   | 0.0238
=============================================================================================================
```

---

## 4. Reconstructed Crack Path Overlay & Termination Diagnosis

1. **Native Control (`1390278`)**:
   - Uniform structured mesh ($h \approx 0.003-0.010\text{ mm}$ across the ligament).
   - Crack propagates across the entire ligament from $x = 0.0\text{ mm} \to +0.50\text{ mm}$ ($940$ nodes reaching $d \ge 0.999$, $75\%$ post-peak load drop) before $dt < 1.0 \times 10^{-9}\text{ s}$ at $U_1 = 0.015189\text{ mm}$.
2. **Stage-D Nonmatching Transfer (`1390279`)**:
   - Fine mesh box $[-0.15, 0.15] \times [-0.15, 0.15]$ ($h \approx 0.0026-0.0045\text{ mm}$), grading to $h \approx 0.025-0.030\text{ mm}$ for $x > 0.15\text{ mm}$.
   - Crack initiates at $(0,0)$ and propagates to $x = +0.0915\text{ mm}$, $y \in [-0.065, +0.024]\text{ mm}$ ($820$ nodes reaching $d \ge 0.999$, $37\%$ post-peak load drop) at $U_1 = 0.011251\text{ mm}$.
   - The diffuse damage band ($2l_0 = 0.030\text{ mm}$) reaches $x \approx 0.12\text{ mm}$, entering the element grading transition zone ($h = 0.003 \to 0.025\text{ mm}$).
   - The abrupt mesh grading step creates localized residual jumps during Mode II shear cracking, forcing time cutbacks down to $dt_{\min} = 1.0 \times 10^{-9}\text{ s}$.

---

## 5. Smallest Falsifiable Next Diagnostic

To definitively distinguish state-transfer error from static mesh grading sensitivity:
- **Diagnostic Proposal**: Run a Matching Continuous Baseline directly on the Stage-D Target Mesh (starting from $U_1 = 0$ without transfer).
- **Hypothesis**: If the continuous run on the Stage-D mesh exhibits identical cutback divergence at $U_1 \approx 0.0112\text{ mm}$ as the crack approaches $x \approx 0.09\text{ mm}$, termination is 100% proven to be a mesh-discretization artifact.
- **Status**: Diagnostic definition recorded; job submission deferred pending user authorization.

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
qsub_called = true (Jobs 1390278.mmaster02 and 1390279.mmaster02 completed)
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```
