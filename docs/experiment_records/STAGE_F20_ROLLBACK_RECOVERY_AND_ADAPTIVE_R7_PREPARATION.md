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
