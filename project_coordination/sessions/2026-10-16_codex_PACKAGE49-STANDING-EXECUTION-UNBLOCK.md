# Minimal execution-unblocking audit
Agent codex; starting commit a3450cdab6a3664dc2a51dc8ab7670c4c8232c18. All pre-existing dirty paths preserved. No solver/job submission or live authorization mutation this turn.

Root cause: initial codex standing issuer hardcoded Package48 technical recovery and enrolled its source hash ddf9b039...; Package49 support was added only to human finite-batch path. Agents repeatedly misclassified this implementation gap as new research approval. Human's already-approved Mode-I progression includes C1-1/C1-2. Enrolled trust itself cannot be rewritten by the controller.

Implemented reusable mode1-qualified-batch-v2: bounded1-2 named serial jobs,1CPU/job,<=16GB,<=8h, entry route only, frozen production UEL, fresh actual preflight, input-bound datacheck artifact hashes, immutable manifest/commands, preserved concurrency/counter/history, revocation, expiry renewal preserving consumed slots, active-permit reuse without reset. New Mode-I stage/package uses a new qualified manifest rather than another human research approval. Scope/privilege/resource expansion remains separate. Human-only upgrade accepts only exact original active grant/pin; preserves grant ID, enrollment, scope, limits, expiration and old consumed permit. No live upgrade was executed.

Actual execution defects repaired: PBS now explicitly cd's to package scratch rather than submitter home; notification helper sourced from package scratch rather than PBS spool script location; required configuration/start/trap installed; compiler checked; rerunnable disabled; no automatic lck deletion; distinct PBS logs. New guarded submit wrapper records exact ID/receipt/ledger before notification. Forward gate now requires actual equilibrium PBS receipt, terminal Exit0, finite individual energy/force/damage/cutback thresholds and explicit nodal-displacement/damage/history/restoration checks plus hashed evidence. No review file pre-created. Existing evaluator is not treated as sufficient proof of state restoration by itself.

Scientific deck/source bytes unchanged: EQUIL eb95ef10b89701f399dacf51fe73fd8ec318cde4d8362d03061b27ec060cb303; FORWARD b4a4414b768fe58e28e33377d8165793c886eddea90a2470c13df12ab7f21ff7; UEL ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6. Corrected execution scripts/metadata staged with original files preserved under pre_controller_repair. Live VerifyOnly PASS: all staged hashes, both actual existing datachecks, compiler, queue, lifecycle and login email/Telegram. Compute delivery UNRESOLVED. Guarded qstat-u showed no active jobs; no qsub invoked.

Validation: final Windows selected battery66 PASS/3 platform skips. Linux isolated reusable30 tests PASS/2 Windows skips plus legacy25 PASS/2 Windows skips; actual file locks and compressed CLI upgrade verified only against temporary state. Native hook detection PASS; real unauthorized qsub payload DENY; DryRun human upgrade+SubmitReady, derivation and submission PASS; PowerShell parse PASS. Original combined-test Windows inherited-stdin WinError50/6 repaired deterministically with stdin=DEVNULL in test subprocess; final full selected rerun passes. Stale historical tests asserting dynamic ACTIVE_TASK status and obsolete dependency label repaired; PBS frozen hash assertions updated to qualified scripts. Test BOM/Unicode transport failure repaired and Linux rerun passes. No credential or secret printed/committed.

Live state readback remains active standing v1 grant and old permit inactive consumed2/max2 with original source pin unchanged. Sole remaining human action:
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\pruth\OpenClawPAD\Set-ControllerAuthorization.ps1" -Standing -UpgradeStandingGrant -SubmitReady
This upgrades the trusted issuer, runs actual preflight, derives Package49 permit and immediately submits equil_test, recording PBS ID. A second invocation cannot reset/re-upgrade or duplicate consumed jobs. Controller thereafter reuses current permits; forward only after real scientific review PASS. No claim that Package49 numerical equilibrium or state preservation has run/passed.

Changed artifact hashes (external issuer maintained canonically outside Git):

AGENTS.md 433d086f1c14a37c663d3e7f09fcf1f817848488c50744ef1aa4049765683220
.agents/scripts/bridge_rules.txt 47c5bb766c2a81cb889b4f57fb46cec640d8c87bc1c2c70279af36abcc4cfaa7
.agents/scripts/project_alignment_guard.txt b50c9a25493103ae7297c6e9d485cf9e26d5f3dfbc8fe7f74adb94c91804fc74
.agents/qsub-safety-gate.ps1 e795abb65e9958849f3b599338f20497c9fc7f5f1edb75cf26ccb9b634626b75
scripts/hpc/standing_authorization_service.py 69b2db59d08900d0935069d1528042eb3b39039d60c7946d1339903ec9548ab6
scripts/hpc/Invoke-StandingAuthorization.ps1 6264419d30f173811c6bc0fed11068d6a1a08675d35649cf1e09d6911689567c
scripts/hpc/Submit-Mode1Batch.ps1 47c2a4887452a1a74833d52a8ee29d94e1e18e0a5e33be24d610ed73aec46f65
scripts/hpc/notify_mode1_submitted.sh 5cb751426adf61c165b2c943386cc746c55bffed1e56f38c0f903708477431de
scripts/hpc/preflight_package49_authorization.py 8601046ff8781f0346e0a9f6d929e9c2b54169d85201bd5e2d3a2a9eececcaa9
tests/unit/test_mode1_reusable_standing_policy.py 8da5238d546fe7a07721ebcfee4f0c0f4c9d2b9f8da9e45c9e8830fe3a616817
tests/unit/test_method_c_batch_gate.py 4c356e300a64b3d78a7bd1a8fc23ebb45fd2cc8a889fcddb7cd95f038156e19f
tests/unit/test_mode1_f1497_package49_execution_and_continuation.py 86c88aa60ceda93580839e9bebb3d2f55bb8ee1bfc251be40273886cd18738eb
tests/unit/test_mode1_f1499_state_transfer_audit_and_equilibrium_qualification.py 45db7a3e2ca9fe6526049dffaabb1c51eb353fc4241955bcd1f02965a7c67976
C:/Users/pruth/OpenClawPAD/Set-ControllerAuthorization.ps1 09d3113c6769081bcad7c882547cb6f799fdf2c15aa4776b6f32985839e93526
models/pandey_kumar_mode1/49_method_c_stage_c1_1_nonmatching_transfer/submit_M1_MC_STAGE_C1_1_EQUIL.pbs 3378495b8e38464834ffc63e27eed848215515c19666b5f382e2b685e2ae0ca5
models/pandey_kumar_mode1/49_method_c_stage_c1_1_nonmatching_transfer/submit_M1_MC_STAGE_C1_1.pbs c6733d2bfa48be27038a5170d90d28819d1cc477d5c600f84c36e5a8f76d4214
models/pandey_kumar_mode1/49_method_c_stage_c1_1_nonmatching_transfer/PACKAGE_MANIFEST.json 8ccd9de804ee719c794f664dff0873b740de54d09a89e4e9d33997bb883a12a0
models/pandey_kumar_mode1/49_method_c_stage_c1_1_nonmatching_transfer/METHOD_C_STAGE_C1_1_AUTHORIZATION.json 269f44c9e2156633ea4acdaf64bdf2a72d912e7868f8ef2e76fc880d9a2bc119
