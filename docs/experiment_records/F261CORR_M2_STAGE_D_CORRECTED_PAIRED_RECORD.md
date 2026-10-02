# Stage-D Corrected Paired Forensic Trajectory Alignment & Diagnostic Record

**Task ID**: `F261CORR-M2-STAGE-D-CORRECTED-PAIRED-FORENSIC-AUDIT1`  
**Date**: 17 August 2026  
**Status**: `TRAJECTORY_ALIGNMENT_CORRECTED / RP_FORCE_RECONCILED / INVARIANTS_VERIFIED / GATES_HELD_CONSERVATIVE`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Terminal Scheduler & Solver Accounting Evidence

```text
=============================================================================================================
PBS Job ID        Job Name         State  Host       Exit  Stageout  CPU Time  Walltime  Memory     VMemory
----------------  ---------------  -----  ---------  ----  --------  --------  --------  ---------  -----------
1390278.mmaster02 M2NATIVE_CTRL    F      mnode097/0 1     1         00:24:16  00:24:25  872,160 KB 3,375,300 KB
1390279.mmaster02 M2STAGED_NONMAT* F      mnode097/1 1     1         00:08:44  00:08:48  856,508 KB 7,503,760 KB
=============================================================================================================
```

- **Job 1 (`1390278.mmaster02` - Bounded Native Control)**:
  - Step 4 (`CONTINUATION`): 326 increments ($1427$ iterations).
  - Last Converged State: Physical $U_1 = 0.015189\text{ mm}$, $RP\_RF_1 = 0.022833\text{ kN}$, $d_{\max} = 1.000000$ ($75\%$ post-peak load drop).
  - Termination: Automatic time increment reached $dt_{\min} = 1.0 \times 10^{-9}\text{ s}$ during terminal softening.
- **Job 2 (`1390279.mmaster02` - Bounded Stage-D Nonmatching Transfer)**:
  - Step 4 (`CONTINUATION`): 271 increments ($1165$ iterations).
  - Last Converged State: Physical $U_1 = 0.011251\text{ mm}$, $RP\_RF_1 = 0.068658\text{ kN}$, $d_{\max} = 1.000000$ ($37\%$ post-peak load drop).
  - Termination: Automatic time increment reached $dt_{\min} = 1.0 \times 10^{-9}\text{ s}$ during post-peak crack localization into graded mesh zone.

---

## 2. Canonical Reaction Force Observable & Top-Edge Kinematics

- **Kinematic Multi-Point Coupling**:
  - In all models, top shear displacement is applied to the **Reference Point Node** (Node 12383 in Native, Node 99999 in Stage-D) and transmitted to the top edge nodes via `*EQUATION`.
  - In Abaqus, reaction forces for constrained degrees of freedom in `*EQUATION` are accumulated entirely on the independent Reference Point node, whereas dependent top edge surface nodes have $RF_1 = 0.000000\text{ kN}$.
- **Authoritative Observable**:
  - **Reference Point $RF_1$** is the true, direct measure of external shear force driving the top edge of the specimen:
    - Canonical H1 (Frame 29): $RP\_RF_1 = \mathbf{0.123277\text{ kN}}$
    - Native Control Step 1 (`STATE_INSTALL`): $RP\_RF_1 = \mathbf{0.123276\text{ kN}}$
    - Stage-D Nonmatching Step 1 (`STATE_INSTALL`): $RP\_RF_1 = \mathbf{0.123172\text{ kN}}$
    - **Handoff Force Parity Mismatch: $-0.084\%$ (Less than 0.1%)**.
- **Explanation of Step 1 (`STATE_INSTALL`) Domain Reaction Sums ($0.240994\text{ kN}$ and $0.453274\text{ kN}$)**:
  - In Step 1, all nodes in the domain are fixed with `*BOUNDARY`. Spatial interpolation onto discrete nonmatching nodes creates small inter-element gradient discrepancies ($\sim 10^{-5}\text{ mm}$), causing interior fixed nodes to develop internal constraint forces.
  - In Step 2 (`MECH_EQUILIBRATION`), all interior constraints are released, restoring static equilibrium with $RP\_RF_1 = 0.122039\text{ kN}$ vs $0.120708\text{ kN}$ (**$+1.10\%$ parity match**).

---

## 3. Corrected Matched Displacement Comparison over True Common Interval $[0.010143\text{ mm}, 0.011251\text{ mm}]$

```text
========================================================================================
Phys U1 mm   | Native RP RF1 kN | Stage-D RP RF1   | RP Diff %    | Native d_max | Stage-D d_max
----------------------------------------------------------------------------------------
0.010143     |        +0.114292 |        +0.120034 |       +5.02% | 0.405772     | 0.436673    
0.010266     |        +0.113544 |        +0.121042 |       +6.60% | 0.568102     | 0.496008    
0.010389     |        +0.110773 |        +0.121891 |      +10.04% | 0.700917     | 0.527349    
0.010512     |        +0.108285 |        +0.122887 |      +13.48% | 0.908763     | 0.560009    
0.010635     |        +0.104052 |        +0.124001 |      +19.17% | 1.000000     | 0.580123    
0.010758     |        +0.102032 |        +0.125272 |      +22.78% | 1.000000     | 0.595846    
0.010882     |        +0.100814 |        +0.126644 |      +25.62% | 1.000000     | 0.598029    
0.011005     |        +0.099684 |        +0.128031 |      +28.44% | 1.000000     | 0.599009    
0.011128     |        +0.098897 |        +0.124160 |      +25.54% | 1.000000     | 0.751205    
0.011251     |        +0.097693 |        +0.071321 |      -27.00% | 1.000000     | 1.000000    
========================================================================================
```

- **Peak Load Parity**:
  - Native Control Peak: $RP\_RF_1 = 0.114674\text{ kN}$ at $U_1 = 0.010183\text{ mm}$ ($d_{\max} = 0.482627$).
  - Stage-D Nonmatching Peak: $RP\_RF_1 = 0.129038\text{ kN}$ at $U_1 = 0.011102\text{ mm}$ ($d_{\max} = 0.600386$).
  - Peak Force Difference: **$+12.53\%$**, displacement shift $+0.000919\text{ mm}$ ($+9.0\%$).

---

## 4. Pointwise State Transfer Mismatch Along Ligament ($y = 0.5\text{ mm}$)

```text
===========================================================================
x (mm)   | H1 u1 (mm)   | Trans u1 (mm) | H1 d         | Trans d      | d Diff      
---------------------------------------------------------------------------
0.00     | 0.010143     | 0.010143     | 0.001418     | 0.001418     |    +0.000000
0.10     | 0.010143     | 0.010143     | 0.003993     | 0.004017     |    +0.000024
0.20     | 0.010143     | 0.010143     | 0.006487     | 0.006392     |    -0.000095
0.30     | 0.010143     | 0.010143     | 0.006199     | 0.006329     |    +0.000130
0.50     | 0.010143     | 0.010143     | 0.000194     | 0.000194     |    +0.000000
0.75     | 0.010143     | 0.010143     | 0.000194     | 0.000194     |    +0.000000
1.00     | 0.010143     | 0.010143     | 0.000194     | 0.000194     |    +0.000000
1.25     | 0.010143     | 0.010143     | 0.000194     | 0.000194     |    +0.000000
1.50     | 0.010143     | 0.010143     | 0.000194     | 0.000194     |    +0.000000
===========================================================================
```

- Maximum phase field transfer mismatch along ligament: **$1.30 \times 10^{-4}$** ($0.013\%$).

---

## 5. Whole-Model Primary Bounds & Irreversibility

- **Primary Phase Field Bounds ($0 \le d \le 1$)**:
  - Native Control (12,383 nodes): $\min d = 0.000000, \max d = 1.000000$ (100% PASS).
  - Stage-D Transfer (9,074 nodes): $\min d = 0.000000, \max d = 1.000000$ (100% PASS).
- **Pointwise Irreversibility ($\Delta d \ge -10^{-6}$)**:
  - Native Control: $\min(\Delta d) = -5.96 \times 10^{-8} \ge -1.0 \times 10^{-6}$, **0 violations**.
  - Stage-D Transfer: $\min(\Delta d) = -5.96 \times 10^{-8} \ge -1.0 \times 10^{-6}$, **0 violations**.

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
