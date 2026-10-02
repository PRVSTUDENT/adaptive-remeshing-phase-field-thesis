# Session Log: Evidence-Provenance and Reproducibility Audit of F151 (Task F152AUDIT)

- **Date**: 15 August 2026
- **Agent**: `gemini-antigravity`
- **Task ID**: `F152AUDIT-M2-F151-EVIDENCE-PROVENANCE-AND-REPRODUCIBILITY1`
- **Starting Commit**: `b6e9b4ea5d4b3d012b2500a52b069a6a3423e37c`
- **Context**: Performed a rigorous evidence-provenance and reproducibility audit of F151 same-mesh restart validation claims using raw ODB, DAT, STA, and MSG files from jobs `1389684.mmaster02` and `1389696.mmaster02`.

## Audit Findings & Provenance Classification

1. **Detection of Hardcoded F151 Metrics**:
   - `F151_hardcoded_metrics_detected` = **`true`**.
   - F151 reported exact zero values for `handoff_RP_U1_error_mm`, `handoff_RF1_relative_error`, `nodal_U_relative_L2`, `phase_d_relative_L2`, `history_H_relative_L2`, `SV_PHASE_relative_L2`, `maximum_dmax_absolute_error`, and `fraction_of_IPs_with_history_decrease` by direct construction in code rather than extracting full fields from ODB/DAT files.

2. **Source Frame Mapping & Handoff Discrepancy**:
   - Continuous Source Frame 29 (`ShearStep`, Frame 29): Step time $t = 0.0101433$, RP physical displacement $U_1 = 0.000507165\text{ mm}$, Reaction Force $RF_1 = \mathbf{0.305426\text{ kN}}$ ($305.43\text{ N}$).
   - Restart `STATE_INIT` (Step 1, Frame 1): $U_1 = 0.000507165\text{ mm}$, Reaction Force $RF_1 = \mathbf{0.016224\text{ kN}}$ ($16.22\text{ N}$).
   - **Handoff Force Relative Error**: $\mathbf{94.69\%}$ ($0.016224\text{ kN}$ vs $0.305426\text{ kN}$).
   - **Cause**: In `STATE_INIT`, all nodal phase DOFs in Abaqus mesh were clamped at 0, so Abaqus static equilibrium evaluated un-degraded elastic stiffness load $16.22\text{ N}$ rather than the degraded handoff load $305.43\text{ N}$.
   - `phase_release_artifact` = **`FAIL`**.

3. **Peak Displacement Contradiction Resolution**:
   - `authoritative_continuous_peak_U1_mm` = **`0.013606 mm`** ($RF_{1,\text{peak}} = 0.383101\text{ kN}$).
   - `authoritative_restart_peak_U1_mm` = **`0.013266 mm`** ($RF_{1,\text{peak}} = 0.378129\text{ kN}$).
   - Peak $RF_1$ Relative Error = **`1.30%`**, Peak $U_1$ Relative Error = **`2.50%`**.
   - **Resolution**: Early reports for small displacement sweeps ($U_1 = 0.002500\text{ mm}$) placed peak at $u_1 \approx 0.000680\text{ mm}$. Linear scaling by total BC displacement factor $0.050000 / 0.002500 = 20$ yields $0.000680 \times 20 = 0.013600\text{ mm}$, resolving the contradiction.
   - `peak_displacement_discrepancy_resolved` = **`true`**.

4. **Scientific Conclusions & Governance**:
   - `same_mesh_restart_validation` = **`PARTIALLY_VALIDATED`** (Continuation load trajectory and peak force match to within $1.30\%$, but handoff `STATE_INIT` nodal phase initialization causes a transient force mismatch).
   - `nonmatching_transfer_algorithm_scientifically_unblocked` = **`false`**.
   - `production_adaptive_accuracy_validation_scientifically_unblocked` = **`false`**.
   - `PK10R1_topology_repair_required` = **`true`**.
