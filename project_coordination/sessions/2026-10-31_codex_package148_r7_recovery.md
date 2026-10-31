# Package 148 R7 manifest/startup correction

Starting commit: 173fb3c5c6026c1da3aa280e6744b5289c71413c.

User-directed recovery of run 8412f8cc-d26e-4674-a12b-f9af5c91d0f4. The stopped turn-363 checkpoint contained the released R6 session; the later active R7 claim reused the run ID and had no report. No live controller process was found. Original checkpoint and active session preserved under project_coordination/controller/recovery-2026-10-31-8412f8cc/ with hashes in reconciliation.json. Session reconciled on this evidence before claiming Codex scope. No forced controller restart or turn rewind; legacy recovery script was not executed because it hardcodes turn 12.

R6 live qstat -xf confirmed terminal F, Exit_status=1, run_count=1, walltime=2 seconds. Exact remote pbs_execution.log confirmed ValueError in CoupledAbaqusRuntime.load before the first iteration. HPC ledger reconciled without touching once-only accounting. R6 supplies no new convergence evidence.

R7 is a distinct technical candidate. All scientific decks, CSVs, includes and frozen UEL remain byte-identical to R6. Runtime manifest uses validated builder schema, recomputes four donor and four runtime hashes, restores GP ordering and donor/receiver metadata. Scheduling stays in EXECUTION_MANIFEST.json. Preserved timeout=7200, max_outer=25, serial 1 CPU/16 GB/8 h, original force/energy/KKT/healing gates, automatic_retry=false, no C1-2.

Actual loader and independent fixed-field decoder check every one of 28,224 history mappings. Initial overly strict 1e-14 comparison exposed existing %.8e include precision; checker repaired to compare exact declared formatting, with no data or physical threshold change. Guarded upload initially failed on Windows nested-quote stripping; repaired to shell-escaped hex encoding, without scheduler action. Both failures retained in execution review.

Qualification, submission and final synchronization results will be recorded below.

Independent donor-to-receiver recomputation PASS: 28,224/28,224 GPs, 100% coverage, zero rejected GPs, zero flank violations, maximum coordinate reconstruction error 3.925231146709438e-17 mm. Every baseline H0 value matches the recomputed HOST_NEAREST_GP transfer at its declared CSV precision.

Final qualification: cluster Python 3.6.8 actual load PASS, authentic mechanical and phase datachecks PASS, 64 tests PASS, R7 controller registration validated. An obsolete unknown-revision test first rejected the newly registered R7; corrected the negative case to R8 and reran successfully. Local stdin-based proof capture produced no artifact; repaired with explicit read-only --record-datachecks, without rerunning Abaqus. Actual live guarded preflight PASS, zero active jobs before submission, login notifications PASS; compute-node notification delivery UNRESOLVED.

Submitted once through Invoke-Mode1Execution.ps1: 1418938.mmaster02. Receipt, atomic reservation and HPC ledger preserved. Live qstat observed RUNNING on mnode101, run_count=1, 1 CPU/16 GB/8 h. No R6 rerun, no C1-2, no controller loop restart. Stage C1-1 physical acceptance UNVERIFIED. Manifest SHA256: 24c6c53d6cc45ad2ace711aa3689912f3425d34ac4cca5a5b4f1e3a911d16774. Full source/evidence hashes in qualification and technical preflight records.
