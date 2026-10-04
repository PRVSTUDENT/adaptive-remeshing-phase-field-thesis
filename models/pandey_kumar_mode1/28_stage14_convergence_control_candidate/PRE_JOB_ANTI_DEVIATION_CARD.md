# Pre-Job Anti-Deviation Card: Package 28 Convergence Control Candidate

- **Task ID**: `F1217-GATE6B-STAGE14UAH-CONVERGENCE-CRITERIA-RECONSTRUCTION-AND-MINIMAL-CONTROL-PREFLIGHT-20261004`
- **Active Gate**: `GATE_6B_ACTIVE_EVALUATION_AND_CONTINUATION`
- **Package Name**: `28_stage14_convergence_control_candidate`
- **Model / Deck**: `PK_MODE1_STAGE14_ADAPT_14K_CONV_CTRL.inp` (SHA-256 `AB484020E13F12213532B365A57E344E7D4426AE8AD4863AB63C745C10BFC48D`)
- **Fortran Subroutine**: `f42_mixed_uel.for` (SHA-256 `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`)
- **Scientific Question**: Does relaxing the displacement correction tolerance ($C_n = 0.50$) while strictly keeping the default force residual equilibrium tolerance ($R_n = 0.005$) eliminate post-fracture Newton stagnation in the severed crack wake without altering material softening, $k$, or phase-field governing equations?
- **Single Intended Change**: Adding `*CONTROLS, PARAMETERS=FIELD, FIELD=DISPLACEMENT` with `0.005, 0.50` to Step 2.
- **Frozen Invariances**:
  * Mesh: 14,456 nodes, 14,483 base elements, 43,449 layered elements.
  * Elastic & Fracture Properties: $E = 210\,\mathrm{GPa}$, $\nu = 0.3$, $G_c = 0.0027\,\mathrm{kN/mm}$, $l_0 = 0.0075\,\mathrm{mm}$, $k = 10^{-7}$.
  * UEL ABI: `(0.0075, 0.0027, 210.0, 0.3, 1.0e-7, 14483.0)`.
  * Loading Schedule: Step 1 $\Delta u_1 = 2.5\,\mathrm{nm}$, Step 2 $\Delta u_2 = 1.0\,\mathrm{nm}$.
  * Execution Mode: Serial 1-CPU.
- **Submission Hold**: **NOT SUBMITTED**. Marked `CONVERGENCE_CRITERION_CANDIDATE_VALIDATED__TEMPORAL_DIAGNOSTIC_PENDING` until Job `1410027.mmaster02` completes.
