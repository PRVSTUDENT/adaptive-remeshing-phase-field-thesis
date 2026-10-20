# Credential lifecycle maintenance - 20 October 2026

Credential-only repair and live validation PASSED. No generative/scientific model call, research turn, PBS submission or scheduler command was performed. F1597 diagnostic commit `0720bbd1901eb17fb932f0fa4412d5bc34343dfd` remains complete and was not replayed. This does not claim validation of a new full research turn or qualification of Package 72 transfer.

## Diagnosis and repair

The initial current CLI access token expired on October 19; the fixed Google userinfo endpoint returned HTTP 401. The previous native cache lacked identity metadata. Neither condition was treated as identity proof. The saved-profile switch mechanism restores an older credential snapshot, so it is no longer used by missing-identity recovery.

After a private CurrentUser-DPAPI encrypted backup of the native entry, one bounded non-generative `agy models` call refreshed the native credential successfully. Google userinfo then independently established that the current native access token belongs to the run-selected account3. The CLI file was still stale. The repair preserves the refreshed native access/refresh grant and synchronizes the CLI file from that provider-verified grant. It restores missing identity metadata only after provider subject equality with the selected saved identity. Saved access/refresh tokens are never restored by this repair; profile markers are not identity proof.

The PRE/POST guard invokes this repair only for native ID_TOKEN_MISSING. It rejects contradictory native or CLI identities, failed provider proof, concurrent store changes, failed native readback, and malformed credentials. Expired native grants can receive one bounded 30-second non-generative account-discovery refresh; provider lookup is bounded to 15 seconds. Native write preserves entry metadata; CLI writes retain private ACLs. No credential contents, emails, token hashes, provider responses or account subject values are logged or committed. The encrypted backup remains outside the repository under OpenClawPAD/backups.

The credential-only entrypoint is `scripts/controller/Invoke-AgyCredentialValidation.ps1 -Profile account3`. It never dispatches a model prompt. Repeating it verified both stores and provider identity at PRE_AGY, POST_AGY and POST_AGY_REPEAT; native bytes and CLI file hashes remained unchanged on repeat. The actual installed Set-AndVerifyAgyRunProfile functions also passed PRE_AGY and POST_AGY twice with ControlledSingleTurn enabled. No agy.exe process remained.

## Validation

- Credential unit regressions PASS: synthetic refresh/token rotation, missing metadata, PRE/POST recovery, idempotent repeated POST, zero profile switches; provider failure/mismatch, conflicting native/CLI identity, concurrent changes, failed readback; fixed HTTPS endpoint, lookup bound and sanitized transport failure. Real credentials are untouched by unit tests.
- Profile guard suite: 6/6 PASS; PowerShell syntax PASS.
- Bootstrap suite: 20/20 PASS in isolated fixtures, including completed-task replay rejection.
- Recovery suite: 25/25 PASS in isolated fixtures.
- Progress/ownership suite: 20/20 PASS in isolated fixtures.
- Canonical controller deployed with backup; installed SHA256 equals canonical: `4F8A76EA52F38A1C60E0A817F8B34DA881EE68E44CE895CC9B7FEC795B277262`.
- Frozen UEL SHA256 remains `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`.
- HPC_JOB_LEDGER SHA256 `DE737E9CE4A383863F22DB71730F890D322FBCC972B560257CAFF81D72CF5AF5`; MODE1_EXECUTION_LEDGER SHA256 `8086F9726DCBB347E6EDA02FCD22D87285D4FBD5B2FDD9862713483B221D1876`. No submission accounting edits; pre-existing dirty paths preserved.

## Next safe action

The credential maintenance gate is satisfied. Do not replay the recorded F1597 frozen-history diagnostic or launch a 20-turn loop. Define the next bounded mechanical/history/call-order investigation from the recorded next safe action before a later controlled research turn. ACTIVE_TASK and INITIAL_PROMPT were not changed. The old BLOCKED runtime checkpoint is retained as historical failure evidence; this maintenance does not reset or relabel that earlier controller run. A subsequent dispatch must reconcile that checkpoint with the committed completed diagnostic, preserving once-only accounting. Five-minute no-progress guard and 2400-second timeout are unchanged.
