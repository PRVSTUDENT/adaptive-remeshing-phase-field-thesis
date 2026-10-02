# Mode-II NM1 State Transfer Semantics & Artifact Integrity Scientific Audit Record

**Task ID**: `F196AUDIT-M2-NM1-TRANSFER-SEMANTICS-AND-ARTIFACT-INTEGRITY1`  
**Date**: 16 August 2026  
**Status**: `AUDIT COMPLETED / CRITICAL DEFECTS IDENTIFIED / TRANSFER REMAINS BLOCKED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Executive Summary

A strict offline scientific audit was performed on the `NM1` nonmatching state-transfer infrastructure and target restart artifacts generated in Task `F195`.

The audit evaluated 5 critical domains:
1. **History-Field Transfer Operator**: The claimed Gauss-point extrapolation and interpolation rule is classified as **`UNSUPPORTED_TRANSFER_RULE`** (ad-hoc heuristic lacking mathematical/literature foundation for non-smooth phase-field history).
2. **Constitutive Irreversibility**: Enforcing $\mathcal{H} = \max(0, \mathcal{H})$ is identified as a **`MATHEMATICAL_FALLACY`** (confusing non-negativity with thermodynamic irreversibility $\dot{\mathcal{H}} \ge 0$ relative to source state).
3. **Source Mesh Topology**: Fully audited and reconciled: `PK10R1` possesses 9850 nodes (9849 physical + 1 RP) and 9612 physical elements ($9588\text{ quads} + 24\text{ triangles}$), correctly parsed across two active UEL layers ($19224\text{ total elements}$).
4. **Reference Point (RP) Boundary Treatment**: Identified **`RP_BOUNDARY_CONTAMINATION_DEFECT`** (target RP node 6562 was treated as a spatial interior node, assigned bogus $U_1, U_2, U_3$, and given Dirichlet BCs in `STATE_INSTALL` and `U3_ONLY` includes, causing DOF 3 activation errors and locking vertical dilation $U_2$).
5. **Binary State Structure**: `TARGET_NM1_INC29_SOURCE_STATE.bin` possesses compliant Fortran unformatted structure ($4,000,016\text{ bytes}$, column-major), but propagated an all-zero history ($\mathcal{H} = 0$) due to reading a 1055-byte placeholder header (`SOURCE_BINARY_PLACEHOLDER_ZERO_HISTORY_PROPAGATION`).

As a consequence of these findings, `history_transfer_rule_resolved` is explicitly set to **`false`**, and the project gate **`nonmatching_transfer_algorithm_scientifically_unblocked = false`** is strictly preserved.

---

## 2. Detailed Audit Findings by Section

### Section 1: Claimed History-Field Transfer Operator
- **Authoritative UEL Storage (`f44_mixed_uel_restart_stateinit.for` / `f42_mixed_uel.for`)**:
  - `SV_H_COMMITTED(N_CAPACITY, 4)`: Stores strain energy history $\mathcal{H}_n(\mathbf{x}_{\text{gp}, k})$ at the 4 Gauss integration points of each quadrilateral element (`JTYPE = 1, 2`) and 3 Gauss integration points of each triangle (`JTYPE = 3, 4`).
  - History is stored **per Gauss integration point**, NOT per node and NOT as an element-average scalar.
  - `PHYSIDX` semantics: In `f44` lines 143-154, `PHYSIDX = JELEM` for Layer 1 and `PHYSIDX = JELEM - N_PHYS` for Layer 2, mapping mechanical integration points to phase integration points.
- **Scientific Flaws in F195 Operator**:
  - F195 mapped Gauss points by scaling natural coordinates by $\sqrt{3}$ ($\hat{\xi} = \xi \sqrt{3}, \hat{\eta} = \eta \sqrt{3}$) and evaluating bilinear quad shape functions.
  - In finite element mechanics, direct interpolation of localized, non-smooth internal state variables across nonmatching meshes causes spurious diffusion and energy dissipation.
  - **Classification**: **`UNSUPPORTED_TRANSFER_RULE`**.

---

### Section 2: Irreversibility Semantics vs Non-Negativity
- F195 claimed: *"Gauss-point history H transfer via Gauss-normalized isoparametric shape functions with irreversibility enforcement H=max(0,H)"*.
- **Scientific Audit**:
  - $H = \max(0, H)$ guarantees **non-negativity** only ($H \ge 0$).
  - **Thermodynamic Irreversibility** in phase-field fracture (Bourdin et al. 2000, Miehe et al. 2010) requires:
    $$\dot{d}(\mathbf{x}) \ge 0, \quad \dot{\mathcal{H}}(\mathbf{x}) \ge 0 \implies \mathcal{H}_{\text{target}}(\mathbf{x}) \ge \mathcal{H}_{\text{source}}(\mathbf{x})$$
  - Furthermore, consistency with the elastic state requires:
    $$\mathcal{H}_{\text{target}}(\mathbf{x}) \ge \psi_+(\boldsymbol{\varepsilon}(\mathbf{u}_{\text{transferred}}(\mathbf{x})))$$
  - F195's rule allows $\mathcal{H}_{\text{target}}(\mathbf{x}) < \mathcal{H}_{\text{source}}(\mathbf{x})$ (artificial damage healing / unphysical softening delay upon reload).
  - **Classification**: **`MATHEMATICAL_FALLACY`**.
  - **Status**: `history_transfer_rule_resolved = false`.

---

### Section 3: Source Mesh Topology & Element Count Audit
- **Mesh Inspected**: `models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050/M2CORR_PK10R1_CONTINUOUS_U050.inp`
- **Audit Findings**:
  - Total Nodes: **9850** (9849 physical nodes + 1 RP node at $(0.0, 0.5)$).
  - Phase Quads (`U1`): 9588 elements.
  - Phase Triangles (`U3`): 24 elements.
  - Total Physical Phase Elements (Layer 1): **9612 elements**.
  - Mechanical Quads (`U2`): 9588 elements.
  - Mechanical Triangles (`U4`): 24 elements.
  - Total Physical Mechanical Elements (Layer 2): **9612 elements**.
  - Total INP Elements: **19224 elements**.
  - Reconciliation: `6048 elements` belongs to `PK10R2`; `9612 physical elements` belongs to `PK10R1`. F195 correctly parsed all 9612 elements once `U3` triangles were included.
  - **Classification**: **`VERIFIED_ACCURATELY_RECONCILED`**.

---

### Section 4: Reference Point (RP) Boundary Treatment
- **Inspected Artifacts**:
  - `TARGET_NM1_INC29_PRIMARY_STATE.csv`
  - `TARGET_NM1_INC29_STATE_INSTALL_BOUNDARY.inp`
  - `TARGET_NM1_INC29_U3_ONLY_BOUNDARY.inp`
- **Audit Findings**:
  - Target Node 6562 is defined as the Reference Point (`*NSET, NSET=RP_NODE`) at coordinates $(0.0, 0.5)$.
  - F195 treated Node 6562 as an ordinary physical interior node and interpolated fields from source element 4812:
    $U_1 = 0.01014330\text{ mm}$, $U_2 = 1.4596\times 10^{-5}\text{ mm}$, $U_3 = 0.0154137$.
  - In `TARGET_NM1_INC29_STATE_INSTALL_BOUNDARY.inp`, Dirichlet BCs were written:
    ```abaqus
    6562, 1, 1, 1.01433005e-02
    6562, 2, 2, 1.45963359e-05
    6562, 3, 3, 1.54137295e-02
    ```
  - In `TARGET_NM1_INC29_U3_ONLY_BOUNDARY.inp`, Dirichlet BC was written:
    ```abaqus
    6562, 3, 3, 1.54137295e-02
    ```
  - **Critical Flaws**:
    1. **Nonexistent DOF 3 on RP**: Reference Point has no phase-field degree of freedom. In Abaqus, applying `*Boundary` on DOF 3 of an RP node either aborts input processing or corrupts residual equations.
    2. **Kinematic Violation of `top U2 FREE`**: Prescribing $U_2 = 1.4596\times 10^{-5}\text{ mm}$ on the RP node locks vertical dilation during state initialization, directly conflicting with the governing Mode-II unconstrained top boundary condition.
  - **Classification**: **`RP_BOUNDARY_CONTAMINATION_DEFECT`**.

---

### Section 5: Binary State Structure & History Propagation
- **Inspected File**: `TARGET_NM1_INC29_SOURCE_STATE.bin`
- **File Size**: $4,000,016\text{ bytes}$ ($4 + 800000 + 4 + 4 + 3200000 + 4$).
- **Memory Layout**: Column-major ($KPT$ outer, element ID inner), perfectly matching `READ(99) SV_PHASE_COMMITTED` and `READ(99) SV_H_COMMITTED` in Fortran.
- **Payload Audit**:
  - Because source file `PK10R1_INC29_SOURCE_STATE.bin` (SHA256: `28e0fc1c...`) was a 1055-byte placeholder header created in F140, no actual history values existed in the file.
  - As a result, all 25,600 transferred history values in `TARGET_NM1_INC29_SOURCE_STATE.bin` are identically `0.0`.
  - The binary state is format-compliant but empty of physical strain energy history.
  - **Classification**: **`FORMAT_COMPLIANT_BUT_ZERO_PAYLOAD`**.

---

## 3. Project Gate Status & Invariants

```text
same_mesh_restart_validation = PARTIALLY_VALIDATED
history_transfer_rule_resolved = false
nonmatching_transfer_algorithm_scientifically_unblocked = false
production_adaptive_accuracy_validation_scientifically_unblocked = false
PK10R1_topology_repair_required = true
new_submission_authorized = false
fresh_human_authorization_required = true
```

- **QSUB/QDEL/QMOVE Operations**: `false` (Zero solver calls made).
- **Frozen Scientific Packages**: `M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R6` and `M2CORR_PK10R2_TOPOLOGY_CORRECTED` remain strictly unmodified.
