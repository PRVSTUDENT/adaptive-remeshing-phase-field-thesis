# Account refresh and CLI parity repair

User loop switched account1, launched agy models, then attempted account2-5 switches while AGY PID 14016 remained alive. Switches failed but the unguarded loop continued saving. Identity-mismatch protection preserved profiles 2-5. Unsaved-login backup was protective, not evidence of profile loss. At inspection no AGY/controller worker remained; prior F1553 active marker was abandoned after reboot. Released that stale lock and claimed tooling-only work; preserved scientific files and unrelated dirty paths.

Live read-only CLI /usage on current account1 (CLI 1.4.2): weekly 54.65%, five-hour 100.00%, quota available. Closed diagnostic CLI normally. No model prompt or scientific execution occurred. Current worker already contained authentic CLI User-Agent installed by prior F1551 work; raw primary daily endpoint now reports both groups. Thus today's full five-hour capacity is independently confirmed on account1; previous endpoint mismatch was real and should not have been generalized to today's readings.

Updated external worker: removed legacy supplemental endpoint/per-model synthesis; only CLI-compatible primary grouped quota used. Missing groups remain unavailable. Preserved disabled-bucket handling; added fraction validation and two-decimal precision. Updated refresh display: shorter columns, two-decimal percentages, fully available bucket shows Available now rather than moving synthetic reset countdown. Read-only refresh is the supported command; no switch/models/save loop required. Preserved .before-cli-parity source backups outside repository.

Validation: six Python regressions PASS. Existing Test-AgyAccountRefresh.ps1 PASS (selection limits, identity protections, error propagation, provider groups, missing/invalid values), after updating old one-decimal string expectations; initial formatting expectation failure preserved here. PowerShell parser PASS. Live all-five-profile refresh: account1 weekly54.65%, account5 weekly47.13%, other weekly100%; five-hour100% all. All statuses OK; no login/profile writes in refresh path. No AGY worker remains from this task. No PBS submissions or duplicate Cycle2 execution.

Earlier first edit command failed with Python SyntaxError from Windows -c quote transport before modifying files; reran the same deterministic patch through stdin successfully.

The user should run only: & "$env:USERPROFILE\OpenClawPAD\Refresh-AgyAccounts.ps1"
