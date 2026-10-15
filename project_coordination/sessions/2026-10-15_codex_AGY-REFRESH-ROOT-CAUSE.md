# AGY expired-token root cause and repair

Starting commit e1d257c1da87301ec797dfb075df596e0fa2f024. All pre-existing dirty work preserved. Only canonical external quota worker/tests and coordination updated. No HPC operations, authorization changes, controller launches, or saved credential writes.

Evidence: new pasted run used repaired isolated reader, but every eligible account failed after access token expiry. Installed ai_limit_checker.antigravity._extract_from_agy_binary uses greedy GOCSPX-[A-Za-z0-9_-]{20,}, capturing a 70-character string including adjacent Go binary text. Credential JWT audience matched resolved client ID. Refresh request using extracted secret: HTTP 401 invalid_client. Same account and client with correctly bounded 35-character GOCSPX secret: HTTP 200 with access token. No secrets printed or persisted.

Repair: canonical local quota worker installs a scoped resolver adapter bounding binary-discovered GOCSPX secrets to prefix plus 28 characters, preserving explicit environment overrides. Third-party package untouched; both startup and post-turn isolated queries inherit adapter. Fresh access tokens stay in worker memory.

Validation: forced expiry_epoch=0 independently for all five saved accounts; all five performed real token refresh plus quota query and returned status ok. Existing PowerShell parser/credential isolation/selection regressions PASS. Added mock greedy-secret extraction and override-preservation regression PASS. Full autonomous controller not launched. New initial test-append command hit nested here-string PowerShell parse error before execution; repaired quoting and reran successfully. No scientific data affected.

Hashes:
- C:\Users\pruth/OpenClawPAD/agy_profile_quota.py : 24F3D29F5D0CDE683938F45F7620C41B474C5AD1C833B45349E640FFF21B7930
- C:\Users\pruth/OpenClawPAD/Test-AgyAccountRefresh.ps1 : DBC6F9574ECCDBE94A36C777AFF9D1BA07C2208628115B3A01654FF96BABBE82

Remote: fetched origin/main and verified it is ancestor of current HEAD. Previous push targeted stale local main rather than current working branch; this closeout publishes current HEAD forward-only to origin/main.
