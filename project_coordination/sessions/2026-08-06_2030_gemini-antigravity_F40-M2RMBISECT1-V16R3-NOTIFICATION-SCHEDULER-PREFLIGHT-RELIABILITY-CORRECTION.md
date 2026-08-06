# Session Report: F40 v16R3 Notification and Scheduler-Preflight Reliability Correction Closeout

**Agent**: Gemini Antigravity  
**Date**: 2026-08-06  
**Task ID**: `F40-M2RMBISECT1-V16R3-NOTIFICATION-SCHEDULER-PREFLIGHT-RELIABILITY-CORRECTION`  
**Starting Commit**: `8e95c22f594fa421e7e4c5523dd36db5b086928b`  
**Preparation Commit P16R3**: `3fb422104e739f93348faa6f2cb31fd3baff5504`  
**Qualification Commit Q16R3**: `a0b0779b3fe860b96c668529f1e34e33ca3c8b28`  
**Coordination Commit M16R3**: pending  
**Classification**: `f40_notification_scheduler_preflight_reliability_corrected_clean_linux_qualified`

## Executive Summary

The F40 v16R3 notification and scheduler-preflight reliability correction sequence was completed strictly offline without any PBS job submission or lock modification.

All 14 specified reliability requirements were systematically implemented and verified by unit tests (`46/46` passed), static gate validator (`pass`), and detached clean-Linux qualification proof.

## Key Technical Solutions

1. **Fail-Closed Queue Preflight**: Replaced `qstat ... || true` in `submit_stage_f40_cae_bisect.sh` with explicit exit status checking. `qstat -u "$USER"` failure stops execution before lock creation or `qsub` and archives stdout/stderr to `QSTAT_U_PRECHECK.stdout`/`QSTAT_U_PRECHECK.stderr`.
2. **Full `qstat -f` Duplicate Audit**: Extracted all job IDs from `qstat -u` and ran `qstat -f "$JOB_ID"` for each to parse full `Job_Name`, `job_state`, and `Job_Owner`. Aborts if `Job_Name = M2RMBISECT1` even if tabular output displays truncated `M2RMBISEC*`. Writes `QSTAT_EXISTING_JOB_AUDIT.json`.
3. **Safe `QSTAT_F_VERIFICATION.json` Generation**: Passed string arguments via `sys.argv` to inline Python (`verification_passed = (verif_ok == 'true')`) to generate real JSON boolean without raw shell interpolation or `|| true`.
4. **Post-`qsub` Output Archiving**: Captured `qsub` stdout, stderr, and returncode (`QSUB_OUTPUT.stdout`, `QSUB_OUTPUT.stderr`, `QSUB_RETURNCODE.txt`) as well as `qstat -f` stdout, stderr, and returncode.
5. **Post-`qsub` Verification Failure Handling**: Verification failure after genuine `qsub` consumes authorization, attempts submission notifications, records failure, and never re-invokes `qsub`.
6. **Monitor Script Renaming**: Renamed `scripts/hpc/stage_f/monitor_stage_f40_terminal_state.sh` to `scripts/hpc/stage_f/monitor_stage_f40_terminal_state.py`.
7. **Strict Terminal State Criteria**: Required `job_state in {"F", "C"}` AND `Exit_status` present. State `E` alone is excluded.
8. **Monitoring Timeout & Non-Zero Exit**: On timeout or unresolvable scheduler query error, writes `TERMINAL_MONITOR_STATUS.json`, suppresses terminal notification, and exits with `sys.exit(1)`.
9. **Scientific Classification Source**: Reads `overall_classification` directly from `evidence/<job-id>/STATUS.json`.
10. **Secure User Notification Configuration**: Introduced `~/.config/adaptive-remeshing/notifications.json` (dir mode 700, file mode 600) for credentials and recipient sets.
11. **Isolated Preflight Test Output Directory**: Pre-submission notification test mode writes strictly inside `runs/hpc/stage_f/f40_notification_live_test/<timestamp>/` (zero files written to repository root).
12. **Path Freezing**: Updated `FREEZE_PATHS` in `submit_stage_f40_cae_bisect.sh` to freeze `scripts/hpc/stage_f/monitor_stage_f40_terminal_state.py`.

## Verification Results

- **Unit Tests**: `46/46` passed under Python 3.12 (WSL).
- **Static Gate Validator**: Passed (`"classification": "pass"`).
- **Detached Clean-Linux Qualification**: Completed OK at `/tmp/f40_clean_qual_daea0e0`.

## Authority Status

All execution and submission authority flags remain strictly `false` and `0`. No scheduler job, solver, datacheck, F41 execution, remeshing simulation, retry, replacement, or new submission is authorized.
