# Stage F20 rollback recovery and adaptive R7 preparation

Starting from `b984f3179b07e71ad24d5646100e4472df29a032`, F19 control and forced
raw call logs were recovered read-only. Native extractor tables were preserved
and semantic aliases plus accepted-increment and cutback tables were generated
under each job's `recovered/` directory with hashes and mappings.

Rollback restoration is proven at the call and scheduler levels, but the
declared response gate fails RF--U NRMSE and relative external work.
Classification is `penalty_rollback_response_mismatch`; no replacement pair is
prepared.

The only selected future job is `M2RMREG7`, package
`models/generated/mode_ii/f20_native_adaptive_region_r7/`, using one CPU, 8 GB,
00:30:00, and route queue `entry_imfdfkmq`. It repairs Abaqus Python 2
iteration and adds real slit-topology connectivity checks. Preparation only:
execution and submission approval are false and qsub attempts are zero.

## M2RMREG7 terminal qualification

The explicitly authorized qualification ran once as PBS job
`1382428.mmaster02`. PBS finished with exit status 0 on `mnode098` after eight
seconds (four CPU seconds; 327324 kb memory). Abaqus/CAE and the compatibility
check returned 0. The geometry-backed adaptive-region API audit, source-model
integrity, remeshing-rule manifest, and slit-topology audit passed. The source
mesh contains 15 coincident slit-face node pairs, no bridge element, and
opposite faces remain disconnected.

Final classification: `native_adaptive_region_contract_qualified`. This proves
construction and association of the native adaptive-region contract only. It
does not execute or validate native remeshing, generate a candidate deck, run a
datacheck or refined phase-field analysis, or establish scientific accuracy.
All corresponding execution counters are zero. Evidence is under
`runs/hpc/stage_f/f20_f19_rollback_evidence_recovery_and_adaptive_r7_preparation/evidence/1382428.mmaster02/`.
