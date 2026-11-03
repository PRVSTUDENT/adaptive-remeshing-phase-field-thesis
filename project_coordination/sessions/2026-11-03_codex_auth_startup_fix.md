# Controller authentication startup fix — 3 November 2026

Root cause: startup unconditionally entered credential recovery before reading the next prompt. Any process named agy caused AUTH_RECOVERY_LIVE_AGY, including the VS Code --hub process PID6388. RECOVERY_ALREADY_RECORDED_NO_REDISPATCH is the durable reporting wrapper, not the original failure. Original pending checkpoint SHA256 BC3FE4E45D01AEAA6412206F6B2134F9F2351E8C711690955E44F50608660907 preserved.

Added a read-only healthy-current-profile path. It accepts only same-user known-path VS Code hubs with valid parent start ordering, no checkpoint-owned worker and no active repository session. Selected-profile marker, saved/native/CLI identity, unexpired access tokens and both live provider identities must agree. Ownership and checkpoint hashes are checked before/after. No switch, refresh, credential writes, checkpoint reset or process termination occurs. Any failed or uncertain check retains the safety block; ordinary recovery remains guarded.

21 authentication regression checks passed, including no-mutation success, owner block, failed-provider block, checkpoint race, original recovery accounting and exact pending resume. The installed controller dot-sources this canonical AuthRecovery file, so no unrelated deployment is necessary. Frozen R6 solver, PBS files, task registration and all unrelated dirty paths untouched.

Live read-only verification result recorded below. No HPC submission or model invocation performed by maintenance.

Live result: READ_ONLY_VERIFICATION_BLOCKED. Account5 marker matches; native and CLI identities match account5, but BOTH tokens are expired and both provider checks failed. No values or secrets were logged. Thus actual credential recovery is required, and the live VS Code hub still legitimately prevents mutation. Close its owning VS Code window/AGY extension normally, then rerun the existing controller command. No hub termination or automatic credential refresh was attempted. All 25 regression checks pass, including hub-vs-worker classification and foreign-owner rejection. Checkpoint hash remains BC3FE4E45D01AEAA6412206F6B2134F9F2351E8C711690955E44F50608660907.

The initial new callback used an unsupported parser SourceName label; corrected to the existing unspecified label before final validation. Live diagnosis separately verified the real expiry/provider failure. Recovery progress is preserved; R6 CRLF and F1602 scientific review/registration remain outside this repair.

Finished.
