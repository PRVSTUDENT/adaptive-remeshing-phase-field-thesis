# F17 preparation session

Agent: codex
Task: F17-PENALTY-ACTIVATION-AND-ADAPTIVE-REGION-REPAIR-PREPARATION
Starting commit: `c716053b28c53349e0c63c78372136b75f501c78`
Ending commit: preparation commit containing this report
Files read: mandatory coordination bootstrap; F16 R3 packages and closeout; F11 extractor; notification wrapper
Files created: two F17 immutable package trees, F17 batch contracts, F17 analyzer/compatibility/build scripts, targeted tests
Files modified: coordination state, ledgers, bootstrap allowlist, phase checklist
Commands run: Git read-only bootstrap/fetch; PowerShell package builder; WSL Python static tests; Bash syntax checks; local gfortran compile and relocatable link
Tests run: 68 existing Stage F1x unittest cases; 5 F17 static/contract tests; 11 parameterless F11-F17 tests; Python compile; JSON parsing; shell syntax; bootstrap validator; local Fortran compile/relocatable link; git diff check
Tests passed/failed: all final checks passed; Abaqus/Intel compile-link and Abaqus-Python runtime self-test deferred to the future PBS jobs because this task explicitly prohibited Abaqus/CAE execution
HPC commands: none
Jobs submitted: none
Job IDs: none
Authorization changes: none; execution and submission remain false
Scientific changes: preserved 0.003/0.001/0.006 mm load-unload/reload history; disabled forced cutback; added fail-closed penalty activation and evidence-retention contract; repaired generator-based finite counting
Hashes: recorded in both package `F17_SHA256SUMS` files and the batch `F17_SHA256SUMS`
Known failures: none in final preparation; installed Abaqus runtime compatibility remains an execution-time qualification gate
Dirty paths deliberately preserved: all unrelated pre-existing modified, deleted, and untracked paths
Exact next action: obtain one explicit authorization covering only M2IRRPENACT1 and M2RMREG4 before any staging or qsub
