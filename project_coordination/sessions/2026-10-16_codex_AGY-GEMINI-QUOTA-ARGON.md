# Gemini quota endpoint recovery and Argon availability
Agent codex; base a2c2e26ef3f6fc9e80a9dd166516fb2490c32fbc. Preserved all pre-existing dirty paths.

Actual API diagnosis using isolated account1 credentials: daily-cloudcode-pa.googleapis.com retrieveUserQuotaSummary HTTP200 returned only Claude/GPT. Standard cloudcode-pa.googleapis.com same grouped endpoint HTTP200 returned Gemini weekly0.87700444 and5h1 plus Claude/GPT. This is actual grouped telemetry, not per-model placeholder quota. Prior display-only repair did not restore Gemini telemetry; corrected now in canonical installed worker.

Worker adapter retains daily-reported groups/values and queries standard grouped endpoint only when Gemini group absent, appends actual missing unique groups, never renames or invents quota. HTTP401 follows existing single refresh path; other unavailable fallback leaves Gemini unknown, so controller still fails closed. No quota thresholds, controller loop code, credentials worker isolation or OAuth-secret extraction logic changed. Dependency package itself unchanged.

Six offline regression tests PASS: actual missing group merged, primary Gemini authoritative/no extra query, HTTP503 cannot invent capacity, HTTP401 bounded refresh signal, deduplication, empty response stays unknown. Existing Test-AgyAccountRefresh.ps1 PASS including smart selection/alias/auth/locked profile/threshold/OAuth/display regressions.

Live five-account quota scan PASS: Gemini weekly account1=87.7%,2=97.3%,3=100%,4=91.9%,5=0%; all5h100%. Actual canonical controller startup-selection functions and post-turn quota function validated without launching agent turns: account1 selected at2%long/20%5h thresholds;5 excluded; post-turn100%notbelowthreshold. State-writing/switching functions were isolated/mocked; only ephemeral temp selection JSON created and deleted. Saved encrypted credentials and active marker unchanged by validation. Account1 selected through supported manager, consistent with human preference; no loop process stopped/restarted. Loop SHA C4CED74B10724453448601FA8C2525AE3F051BF3358F8AB26F32C9725110888C unchanged.

agy models checked on current account5 and account1: only Gemini3.8Flash high/medium/low, Claude Sonnet4.6, Opus4.6thinking, GPTOSS120Bmedium. Argon not listed, so no unsupported model identifier configured; existing gemini-3.8-flash-high retained. Same user loop command can be rerun unchanged. No HPC commands/submissions or authorization changes in this task. Research jobs1413895/1413896 preserved; scientific review remains separate pending work. No credentials logged or committed.

Canonical worker maintained outside Git, not duplicated into repository. Hashes:

C:/Users/pruth/OpenClawPAD/agy_profile_quota.py SHA256 ef3616310b06b5ae552b69135903217cd28e406fe7f9a070057ed4376fa28814
tests/unit/test_agy_quota_group_fallback.py SHA256 e59f00422367a96236a8669733c357a7fd30adf6253e2a68ae561d7880f439a1
