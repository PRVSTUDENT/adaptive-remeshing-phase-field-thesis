# Stage D3D-A1H0 Mechanical Checkpoint Protocol

## Purpose

Re-equilibrate mechanical fields after the offline phase correction while
holding the corrected phase fixed at every node and retaining the unchanged
actual F3 history as the ingested state.

## Prepared steps

1. `INGEST_D3D_A1_CANDIDATE`: ingest corrected phase and actual F3 history
   with phase fixed at all 6,601 nodes.
2. `D3D_A1_MECHANICAL_CHECKPOINT_EQUILIBRATION`: impose bottom \(U_2=0\),
   anchor \(U_1=0\), and top
   \(U_2=0.003000000026077032\) mm while phase remains fixed everywhere.

No phase-release or continuation step is permitted.

## Frozen gates

Ingestion requires 6,601 phase nodes, 25,600 history points, SDV15/SDV16
transfer error at most \(10^{-8}\), and zero non-positive Jacobians.

The fixed-phase endpoint requires 81 top nodes, top displacement error at most
\(10^{-8}\), finite reaction, phase drift at most \(10^{-10}\), no phase or
history decrease, retained spatial variation, and no state reset. Relative
reaction and reconstructed-energy changes from accepted F3 must each be at
most 1%.

Actual-history KKT uses the equilibrated phase, actual endpoint SDV16,
original F3 lower bound, and candidate 6,374/227 membership. Gates remain:
free residual at most \(10^{-8}\), minimum active multiplier at least
\(-10^{-8}\), and active-bound error at most \(10^{-10}\).

Prepared outcomes are:

- `stage_d3d_a1h0_mechanical_checkpoint_pass`;
- `stage_d3d_a1h0_actual_history_update_required`;
- `stage_d3d_a1h0_solver_fail`;
- `stage_d3d_a1h0_postprocessing_fail`.

This protocol authorizes preparation only.
