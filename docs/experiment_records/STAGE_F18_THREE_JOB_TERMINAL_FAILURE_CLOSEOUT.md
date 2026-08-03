# Stage F18 three-job terminal failure closeout

Date: 2026-08-03

Preparation `192308e473f0726a6ee1a04b5cb4020109f4d5e6`, authorization `5b1159be6fe139e30c23ccf43c015dcd9bc613f8`, and submission `2a35c7fd93c532511313616d691a0abdd865c43d` produced exactly three successful submissions. The `afterany:1381487.mmaster02` dependency attached to `1381489.mmaster02` as intended. F18 authority remains fully consumed: three qsub attempts, three successful submissions, zero failed submission calls, retries, replacements, direct qsub, qdel, and qmove.

Direct scheduler and scratch re-collection was attempted from Windows and WSL on 2026-08-03, but all configured SSH routes timed out. Consequently, exit status, walltime, dependency operation, and notification facts below are explicitly user-reported rather than newly scheduler-verified. No scheduler mutation was attempted.

`1381487.mmaster02` (`M2IRRROLLCTL4`) and `1381488.mmaster02` (`M2IRRROLLFORCE4`) reportedly exited 1 after compilation, linking, and input processing. Canonical source inspection identifies the exact defect at lines 287 and 294: both absent flag files were opened with `STATUS='OLD'` without a preceding `INQUIRE`. Although `IOSTAT` was supplied, Intel Fortran raised runtime error 29 during initial-stress UEL execution. Neither job reached the qualified penalty-active trigger, requested `PNEWDT`, abandoned/retried an increment, or began extraction. Both are classified `penalty_rollback_runtime_failure`, not rollback-state failures.

`1381489.mmaster02` (`M2RMREG5`) reportedly exited 11 after three seconds. The source audit establishes the first evidence-contract failure: the compatibility helper can return zero but never writes its required `ABAQUS_PYTHON_COMPATIBILITY.json`. The wrapper then validates a fixed manifest and exits 11, masking the original compatibility/CAE lifecycle. The other missing JSON files cannot be classified as never-generated versus unstaged without remote retained directories. The fail-closed classification is `native_adaptive_region_evidence_incomplete`.

Telegram terminal evidence and a remote retained-artifact inventory could not be independently recollected during this session. The exact access limitation is preserved in the scheduler and inventory JSON records rather than silently inferred.

Scientific consequences are unchanged: no rollback qualification was obtained; H1 remains blocked; adaptive-region qualification was not obtained; and native remeshing remains blocked. F19 is preparation-only and has no execution authority.
