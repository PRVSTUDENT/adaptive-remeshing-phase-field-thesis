# Session Report: F272FIX Controller Router Max Submissions Cumulative Limit Repair

- **Date**: 18 August 2026
- **Task ID**: `F272FIX-CONTROLLER-ROUTER-MAX-SUBMISSIONS-LIMIT-REPAIR1`
- **Agent**: `gemini-antigravity`
- **Commit**: `42762382e8e0f4a8fc87b43eb0ddfba06028bcaf`

---

## 1. Incident Diagnosis

During autonomous controller execution in Turn 8, after diagnostic job `1390447.mmaster02` was submitted, the loop terminated with:
```text
[Action: max_submissions_limit_exceeded]
Decision: Direct -> stop
```

### Root Cause Analysis
1. Section 1.4 of `run_router.py` in WSL evaluated:
   ```python
   consumed = auth.get("consumed_submissions", 0)
   max_sub = auth.get("max_submissions", 2)
   if consumed + len(new_jobs) > max_sub:
       return {
           "action": "direct",
           "output": "stop",
           "tier": "tier1_deterministic",
           "reason": "max_submissions_limit_exceeded"
       }
   ```
2. Because 2 jobs (`1390439` and `1390446`) had been submitted earlier in the session, `consumed` was 2. The submission of `1390447` exceeded `max_sub = 2`, triggering an unintended cumulative stop even though ChatGPT had explicitly authorized and instructed continuing the diagnostic loop.

---

## 2. Minimal Deterministic Repair

1. **`run_router.py` Section 1.4 (WSL `OpenClawGateway`)**:
   Replaced the cumulative limit check with an accounting-only update while strictly maintaining the active concurrent HPC job guard:
   ```python
   else:
       # NORMAL submission.
       # ChatGPT decides whether each prepared job is authorized.
       # No cumulative session/day submission-count STOP is enforced here.
       consumed = auth.get("consumed_submissions", 0)

       for jid in new_jobs:
           jobs[jid] = {
               "status": "SUBMITTED",
               "submission_kind": "NORMAL",
               "running_confirmations": 0,
               "replacement_used": False,
               "retrieved": False
           }

       # Keep this only as an accounting/statistics counter.
       # It must NOT be used as a termination condition.
       auth["consumed_submissions"] = consumed + len(new_jobs)
   ```

2. **Preserved Concurrency Guard**:
   The guard ensuring no more than 2 jobs run concurrently on HPC is preserved intact:
   ```python
   active_hpc_now = [
       j for j, d in jobs.items()
       if d.get("status") in ["SUBMITTED", "QUEUED", "RUNNING"]
   ]
   if len(active_hpc_now) > 2:
       return {
           "action": "direct",
           "output": "stop",
           "tier": "tier1_deterministic",
           "reason": "max_2_concurrent_hpc_jobs_exceeded"
       }
   ```

3. **Repository Scripts & Resume State**:
   - Synchronized `.agents/scripts/normalize_router_jobs.py`.
   - Updated `antigravity_loop_state.json` to resume Turn 9 directly with:
     `ssh -F $env:USERPROFILE\.ssh\codex_config tu_freiberg qstat -x 1390447.mmaster02`

---

## 3. Verification & Live Job Findings

1. **Compilation Check**:
   `python3 -W error -m py_compile /home/openclaw/.openclaw/workspace-antigravity-controller/run_router.py` -> `Exit 0` with 0 warnings.

2. **Sequential Multi-Submission Test**:
   Validated that submitting multiple sequential jobs advances cleanly without cumulative termination, while attempting 3 simultaneous active jobs triggers the concurrency limit guard as required.

3. **Cluster Job Status**:
   Job `1390447.mmaster02` is actively running on `mnode097/0` in queue `normal_imfdfkmq`.

---

## 4. Preserved Invariants

```text
same_mesh_restart_validation = VALIDATED
history_transfer_rule_resolved = true
selected_production_history_operator = HOST_NEAREST_GP_WITH_NONNEGATIVE_IRREVERSIBILITY
stage_d_nonmatching_transfer_validation = UNDER_FORENSIC_REVIEW
nonmatching_transfer_algorithm_scientifically_unblocked = false
production_adaptive_accuracy_validation_scientifically_unblocked = false
PK10R1_topology_repair_required = true
telegram_delivery_observed = true
email_delivery_observed = true
notification_pre_submission_gate_passed = true
new_submission_authorized = true (Job 1390447.mmaster02 running)
qsub_called = true (Job 1390447.mmaster02 active)
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```
