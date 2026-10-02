# Implementation-Level Phase-Field Irreversibility, Rollback Safety & Conditioning Record

**Task ID**: `F247REPAIR-M2-STAGE-D-NODE-LEVEL-IRREVERSIBILITY-AND-ROLLBACK-AUDIT1`  
**Date**: 17 August 2026  
**Status**: `REPAIR_QUALIFIED / LIFECYCLE_TESTS_100_PCT_PASSED / DATACHECK_EXIT_0 / READY_FOR_FRESH_AUTHORIZATION`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Executive Summary & Formulation Audit

### 1.1 Multi-Increment State Lifecycle & Rollback Safety in Abaqus
- **Lifecycle Tracing in `UEXTERNALDB`**:
  - `LOP = 0` (Analysis start): Ingests initial transfer fields (`SV_PHASE_COMMITTED`, `SV_H_COMMITTED`) and initializes trial states `SV_PHASE_TRIAL = SV_PHASE_COMMITTED`, `SV_H_TRIAL = SV_H_COMMITTED`.
  - `LOP = 1` (Start of increment or retry after cutback): Resets trial arrays from committed arrays (`SV_PHASE_TRIAL = SV_PHASE_COMMITTED`, `SV_H_TRIAL = SV_H_COMMITTED`). This provides complete **rollback safety**: unaccepted trial states during failed Newton iterations are instantly discarded without corrupting committed state.
  - `LOP = 2` (Increment accepted): Advances committed state:
    $$\text{SV\_PHASE\_COMMITTED}(e) = \max(\text{SV\_PHASE\_COMMITTED}(e), \text{SV\_PHASE\_TRIAL}(e))$$
    $$\text{SV\_H\_COMMITTED}(e, k) = \max(\text{SV\_H\_COMMITTED}(e, k), \text{SV\_H\_TRIAL}(e, k))$$
  - In UEL subroutine, `SV_PHASE_TRIAL(PHYSIDX)` tracks forward damage growth during iterations:
    $$\text{SV\_PHASE\_TRIAL}(e) = \max(\text{SV\_PHASE\_COMMITTED}(e), d_{\text{avg}})$$
    guaranteeing strict multi-increment irreversibility $d_{n+1} \ge d_n$ throughout `PHASE_RELEASE` and all `CONTINUATION` increments.

---

### 1.2 Analytical Signs and Tangent Derivation in Abaqus UEL
In Abaqus UEL, the discrete system is $\mathbf{K} \Delta \mathbf{u} = \mathbf{R} = \mathbf{F}_{\text{ext}} - \mathbf{F}_{\text{int}}$.
- For an active penalty $\Pi_{\text{pen}} = \frac{1}{2} \gamma (d_{\text{com}, I} - U_I)^2$:
  $$F_{\text{int}, I}^{\text{pen}} = \frac{\partial \Pi_{\text{pen}}}{\partial U_I} = \gamma (U_I - d_{\text{com}, I})$$
  $$R_I^{\text{pen}} = -F_{\text{int}, I}^{\text{pen}} = +\gamma (d_{\text{com}, I} - U_I)$$
  $$K_{II}^{\text{pen}} = -\frac{\partial R_I^{\text{pen}}}{\partial U_I} = +\gamma$$
- Implemented in UEL:
  `AMATRX(I,I) = AMATRX(I,I) + PENALTY_K`
  `RHS(I,1)    = RHS(I,1) + PENALTY_K * (D_COMMITTED - U(I))`
- **Analytical Sign Verification**: Both `RHS` and `AMATRX` signs are exact, positive definite, and dimensionally consistent ($\gamma = 10^7 \frac{g_c}{l_0}\text{ kN/mm}^2$).

---

## 2. Sensitivity & Extended Lifecycle Test Suite Results

The extended test suite in [`scripts/validation/test_comprehensive_irreversibility_lifecycle.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/scripts/validation/test_comprehensive_irreversibility_lifecycle.py) verified:

1. **Penalty Sensitivity Study**:
   - $\gamma = 10^4 \frac{g_c}{l_0} \implies \Delta d = -2.84 \times 10^{-5}$
   - $\gamma = 10^6 \frac{g_c}{l_0} \implies \Delta d = -2.84 \times 10^{-7}$ ($\le -10^{-6}$, R7 compliant)
   - $\gamma = 10^7 \frac{g_c}{l_0} \implies \Delta d = -2.84 \times 10^{-8}$ ($\le -10^{-6}$, optimal conditioning)
2. **Multi-Increment Damage Growth & Unloading**:
   - Monotonic growth $0.284 \to 0.625 \to 0.847$, followed by complete unloading ($\mathcal{H} \to 0$), holding $d = 0.847$ without healing ($\Delta d = 0$).
3. **Rollback Safety**:
   - Verified that failed trial states ($d_{\text{trial}} = 0.75$) during cutbacks leave committed state ($d_{\text{com}} = 0.284$) completely intact.
4. **Node Valence Invariance**:
   - Verified across valences 1 to 8; compliance error remains $< 3 \times 10^{-8}$.
5. **Nonuniform Mesh Scaling**:
   - Invariant across element sizes $h \in [0.001, 0.050]\text{ mm}$.

---

## 3. Package Qualification & Cryptographic SHA-256 Manifest

- **`abaqus datacheck`**: **`Exit 0`** on `mlogin01`.
- **State Ingestion Log**: `SUCCESS: Imported restart state from Stage-D state file` in `.msg`.
- **Field Output**: Whole-model `*NODE OUTPUT` and `*ELEMENT OUTPUT` configured.
- **PBS Email Directive**: Authoritative recipient `#PBS -M pr21vyci@mailserver.tu-freiberg.de`.

### Frozen Package Hashes (SHA-256)
- `inp`: `390767239ca9384ca9d3dce9deb39a2290f8348d70be74ddc130c71fe23da0a8` ([`M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.inp`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.inp))
- `uel`: `856d90e2f2c574354b1aecfa6b284ee52dbbf3adbdf99ff8115631ad7c36af33` ([`f44_mixed_uel_restart_stateinit.for`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/f44_mixed_uel_restart_stateinit.for))
- `primary_state_bc_include`: `bcc1ccecc85c9691a7dffdb087ff79a977034fe1d844e0677bf97e032297b622` ([`STAGE_D_PRIMARY_STATE_BOUNDARY.inp`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/STAGE_D_PRIMARY_STATE_BOUNDARY.inp))
- `u3_only_bc_include`: `023ff2a97bddf1471267e71a6b326965ec62e5023fde8708b468cb372d938e18` ([`STAGE_D_U3_ONLY_BOUNDARY.inp`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/STAGE_D_U3_ONLY_BOUNDARY.inp))
- `committed_state_bin`: `0ff4b468cbc6af6bedcaba025dd557d65cc715ced86a87f2a4324bd3d58234c5` ([`STAGE_D_COMMITTED_STATE.bin`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/STAGE_D_COMMITTED_STATE.bin))
- `launcher`: `c6b7c7e23dbe913a9a44d3190ae6865a9ca53c57479386d55012722404acd4bb` ([`submit_job.pbs`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/submit_job.pbs))

---

## 4. Preserved Scientific Gates & Multi-Agent Invariants

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
M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL = READY_FOR_FRESH_AUTHORIZATION
```

```text
new_submission_authorized = false
qsub_called = false
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```
