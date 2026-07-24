# Stage P3-SB finalized-evidence decision

Date: 2026-07-24

Job: `1378094.mmaster02`

## Dual classification

1. The original automated lane remains `stage_p3sb_baseline_serial_fail_validation`.
2. Its immediate technical cause was evidence ordering: required stdout and `.sta` files were copied into the validator-visible directory only by the exit finalizer, after validation.
3. The original `P3SB_STATUS.json` remains immutable at SHA-256 `54d15323295cf712f50a26e5194b28a61826a3803374c4342b61ca8c546653de`; `P3SB_COMPLETION.ok` remains absent.
4. An isolated replay of the exact unchanged validator against finalized evidence passed as `stage_p3sb_finalized_evidence_offline_pass`.

## Allowable conclusion

The accepted uninstrumented D2 source completed the eight-element serial baseline. The P3-SB automated lane failed solely because its validator ran before required finalized log files were copied.

The replay verified solver exit zero, compile/link/input/Standard completion, readable-ODB evidence, all eight CPS4 visualization elements and four integration points per element, 32/32 state records, finite RF and energy histories, zero phase/history violations, zero transfer mismatches, and 13 increment/attempt records.

## Unsupported claims

This evidence does not establish UEXTERNALDB compatibility, GETRANK or GETTHREADID safety, COMMON/SAVE thread safety, four-thread repeatability, MPI support, or hybrid support.

No P3-SB retry is justified. P3-SM0 may be prepared, but its execution remains unauthorized.

## Permanent validation-order rule

Every future PBS lane must:

1. finish the solver;
2. copy required stdout, `.sta`, job record, and extraction outputs into the validator-visible evidence directory;
3. verify those files exist;
4. invoke the scientific validator;
5. retain the exit finalizer only as a fallback copy mechanism.

The P3-SM0 static suite enforces this ordering. The closed P3-SB PBS script is not modified retrospectively.
