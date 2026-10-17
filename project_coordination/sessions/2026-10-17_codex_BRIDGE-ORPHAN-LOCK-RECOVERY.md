# Bridge orphan lock recovery

Failure: completed AGY turn stopped during ChatGPT handoff because bridge.lock retained owner PID 10528 from a stopped controller. The old implementation rejected young dead locks and removed locks older than 60 minutes even with a live owner. Stopping the earlier controller had left this stale transaction behind.

Repair: canonical and installed Invoke-ChatGPTBridge.ps1 now hold a path-specific OS mutex for the full bridge transaction. Legacy metadata is checked for live owner PID and, when available, process start identity. Dead/reused owners are reclaimed immediately; live owners are never evicted by age. Orphan lock and request/response files are archived under unique names before replacement. Cleanup removes only a lock acquired by this invocation and always releases the mutex. Installed bridge synchronized from canonical source (including current job-first rule check); original installed bytes preserved in .before-owner-lock-v2.

Actual PID 10528 orphan lock and leftover bridge_response.ready were archived without processing that response as a current handoff. No new AGY/controller process, bridge message, scheduler operation or submission was started. Existing Cycle 2 job 1414788.mmaster02 must be reused; repository state records its submission. Scientific results were not reevaluated in this tooling repair.

Validation: Test-BridgeLockRecovery.ps1 passed parser, immediate dead-owner recovery, evidence archival, old live-owner rejection, foreign lock preservation, normal acquisition and release. Initial test harness failed on CRLF substring matching; normalized newlines and reran successfully. Installed and canonical files match. The actual orphan was reclaimed through the same tested acquisition/release block. End-to-end PAD/ChatGPT delivery remains untested here.

Next: resume from current F1530 coordination and existing job; do not replay the original submission task. No background controller remains from this repair.
