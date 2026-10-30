# Package148 R1 pre-submission qualification and actual execution

Base: d85d2c7532d07794f179e690db5e96032d1fca7b
Controller fix: c80eaf21bb010111c7c6ef11a0f3588b0586db99
Complete deployment revision: c3f8febad2d46e04d7db05edb0640aca7682665e

The registration circular dependency is repaired. Package148 R1 passed real mechanical and phase Abaqus 2023 datachecks and was submitted once as **1418787.mmaster02**. It terminated Exit1 after 3 seconds on mnode101 before the first solver call. No physical acceptance is established.

## Exact changes

Controller-Qualification.ps1 has a separate HPC_PRE_SUBMISSION / QUALIFIED_FOR_PREFLIGHT contract. It requires a hash-bound reviewed numerical runtime, tests, exact one-job manifest, frozen UEL and the guarded Mode-I execution adapter. It does not require or create a PBS ID before submission. Existing HPC qualification still requires an authentic recorded job ID.

Controller-Operations.ps1 resolves the operation ID to execute_package148_state_transfer.py. That adapter implements the actual controller --workspace/--output interface, revalidates registration, invokes Invoke-Mode1Execution.ps1, and verifies matching durable submission and HPC-ledger receipts before producing an HPC_SUBMISSION result. The controller distinguishes this technical receipt from a numerical finding. Existing dispatch/source pins and the prohibition on operation changes after preflight remain intact: registration is performed before fresh dispatch, never inside a preparation turn.

Both runtime-generated datacheck inputs are hash-bound, and the live preflight/gate now requires the additional phase datacheck. The reviewed sources were missing from the cluster checkout, so the PBS wrapper deploys a hash-bound isolated runtime within the run directory. No numerical algorithm or frozen UEL was changed. The existing Antigravity wrapper/preflight changes were retained and committed with this technical deployment change. The unchanged previously untracked notification helper was added after the first staging attempt exposed its absence from Git. Second staging passed all 22 explicit files. No whole-tree cluster scan or destructive synchronization occurred.

## Actual qualification and scheduler evidence

- Manifest SHA256: 632f29fd163e935043254491d5006d6dcbc2fa08fde53c6df0f27291676025aa
- Mechanical DAT SHA256: b5cbaf4819f140c702aa5dfd763dc03ee2b009dea4affc7d76151e915b973786
- Phase DAT SHA256: 9637b0c2623db7a6ac4e10bbaa5efdbf6474a3723a5065d965d2aab862307c47
- Both real datachecks: ANALYSIS DATACHECK COMPLETE; no ***ERROR.
- Preflight: PASS; live active jobs0; entry_imfdfkmq routing; 1 CPU, 16GB, 8h; once-only reservation1.
- Real login-node Telegram acknowledgement and email transport accepted; lifecycle/trap fixture tests passed; notification config mode600.
- telegram_notification_contract: PASS_LOGIN_NODE. Compute-node START/terminal delivery: UNRESOLVED; static hooks and an exit code are not delivery proof.
- Actual scheduler receipt: 1418787.mmaster02, normal_imfdfkmq, mnode101/0, stateF, Exit_status1, walltime00:00:03.

## Preserved runtime failure

PBS log exists at /scratch9/pr21vyci/runs/mode1_c4_package148_state_transfer_r1/pbs_execution.log. Traceback reaches driver_package146_147_pdas_continuation.py line797:

    blocks = re.split(r'(?m)(?=^\*(?!\*))', self.template)
    ValueError: split() requires a non-empty pattern match.

The observed cluster Python is 3.6.8. The failure occurs while constructing the first mechanical deck, before self.runner invokes Abaqus. This is a Python runtime compatibility failure, not a KKT failure, physical simulation result or registration rejection. The R1 source and failed allocation evidence remain intact. No blind retry, second reservation or identical rerun occurred.

The next technical action is a distinct compatibility correction with a regression exercised on the target Python version, fresh source/manifest qualification and independent review. AGENTS.md requires stopping when a repair would alter an already qualified package; this session therefore did not patch the submitted R1 runtime or submit a replacement.

## Verification

- Package and submission-adapter suite: 44 tests and 8 subtests passed (includes all 38 prior package tests).
- Affected gate and adapter suite: 30 passed, including missing/invalid additional phase proof, once-only accounting and authentic receipt checks.
- Controller fixtures: 8 pre-submission cases, 9 operation checks and 11 preparation checks passed.
- Existing bootstrap suite: first9 checks passed; its unchanged watchdog-text assertion failed. Controller source it checks was not modified in this task; that failure is recorded rather than claimed as a pass.
- Initial registration lookup exposed selection of the older runtime-review packet when resolving only by operation ID. An explicit canonical adapter mapping repaired lookup; registration and fresh task-type resolution then passed.
- One optional encoded historical-evidence query was blocked by Windows antivirus. No security settings were changed; plain guarded qstat and exact-file queries provided the required evidence.
- git diff --check identified one pre-existing whitespace-only line in the adopted audit script. Its reviewed bytes were retained.

No account/profile/credential changes were made. The research preparation loop was not restarted. Historical scientific failures, frozen UEL and all unrelated dirty work remain preserved. Solver binaries and raw .dat/.log files stay outside Git.

Evidence: results/validation/package148/submission.json and results/validation/package148/presubmission_execution.json.
