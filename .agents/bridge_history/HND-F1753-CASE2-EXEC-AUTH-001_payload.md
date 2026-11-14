# Task F1753 Case 2 Method A Controlled Continuation Production Simulation Execution Authorization Packet

```json
{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "HND-F1753-CASE2-EXEC-AUTH-001",
  "predecessor_correlation_id": "HND-F1752-CASE2-PREFLIGHT-002",
  "task_id": "F1753-CASE2-CONTROL-ONLY-CONTINUATION-EXECUTION",
  "predecessor_task_id": "F1752-CASE2-CONTROL-ONLY-CONTINUATION-EXECUTION-PREFLIGHT",
  "action_requested": "AUTHORIZE_1_BOUNDED_PBS_JOB",
  "requested_pbs_jobs": 1,
  "cumulative_pbs_submissions": 25,
  "target_cumulative_pbs_submissions": 26,
  "execution_boundary": {
    "benchmark": "Pandey & Kumar (2025) Section 4.5, Plate with Off-Axis Hole",
    "mesh_elements": 23965,
    "total_deck_elements": 71895,
    "physical_mesh_nodes": 23957,
    "total_deck_nodes": 23958,
    "input_deck": "models/pandey_kumar_mode1/234_f1752_case2_continuation/PK_F1752_CASE_2_CONTINUATION.inp",
    "input_deck_sha256": "CCB35B34BFAE015EA4846D3D0765FC2646E6C9AF47958F8C21A0A4F25A14CC4A",
    "uel_subroutine": "models/pandey_kumar_mode1/234_f1752_case2_continuation/f42_mixed_uel.for",
    "uel_subroutine_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
    "pbs_script": "models/pandey_kumar_mode1/234_f1752_case2_continuation/submit_f1753_case2_continuation.pbs",
    "pbs_script_sha256": "4CC1285F9C853595599FF862C47AB53F6FB2558C4E64C04EE058F015850D4B11",
    "cluster_staging_dir": "/scratch9/pr21vyci/runs/f1752_case2_continuation/",
    "resources": {
      "cpus": 1,
      "memory_gb": 8,
      "walltime_seconds": 10800,
      "queue": "normal_imfdfkmq"
    },
    "datacheck_result": "EXIT_0_ZERO_ERRORS_EIGHT_ELEMENT_NOTICES"
  }
}
```

---

## 1. Context & Purpose

In `HND-F1752-CASE2-PREFLIGHT-002`, independent supervision found:
- `preflight_assessment: TECHNICAL_PREPARATION_SUBSTANTIALLY_COMPLETE`
- Findings F1752-R01 (diff sign), F1752-R02 (restart history loss), F1752-R05 (testable hypotheses), and F1752-R06 (node & force counts) formally accepted as `RESOLVED`.
- Supervision directed:
  1. Complete offline testing of `scripts/hpc/monitor_case2_cutbacks.py` on authentic/synthetic `.sta` sequences without launching external Abaqus commands.
  2. Verify production field-output coverage (`FREQUENCY=1`), Layer 3 SDV mapping (`STATEV(1)=d`, `STATEV(2)=H`), and authentic F1735 ODB extraction data, explicitly documenting the observation boundary.
  3. Close zero-PBS Task F1752 through the legitimate controller lifecycle and register successor execution task `F1753-CASE2-CONTROL-ONLY-CONTINUATION-EXECUTION` requesting 1 bounded PBS job.

Both readiness requirements are now completely fulfilled and verified with 59/59 passing regression unit tests. Task F1753 formally requests execution authorization for **exactly 1 bounded PBS simulation**.

---

## 2. Final Execution-Readiness Verification Evidence

### A. Offline Testing of Live Runtime Monitor Daemon (`scripts/hpc/monitor_case2_cutbacks.py`)
- Authored dedicated test suite `tests/unit/test_monitor_case2_cutbacks.py` containing 7 test cases:
  1. `test_parse_sta_line_types`: Verified parsing of converged, cutback (`U`), header, and terminal banners (`SUCCESS`, `INCOMPLETE`).
  2. `test_consecutive_cutback_counting_and_reset`: Verified that cutback count increments on `U` attempts and strictly resets to 0 upon any converged increment.
  3. `test_cutback_threshold_trigger`: Verified that threshold callback triggers at exactly cutback #50 on line 50 when 55 cutbacks occur.
  4. `test_authentic_f1735_tail_sequence`: Verified authentic Job 1423271 terminal sequence parses with exactly 3 cutbacks, 5 total cutbacks, 2 converged increments, and zero false triggers.
  5. `test_multi_chunk_cutback_carryover`: Verified streaming state retention across polling chunks (2 cutbacks in chunk 1 + 3 cutbacks in chunk 2 correctly triggers at 5 cutbacks).
  6. `test_monitor_daemon_live_file_streaming_and_termination`: Verified line-buffering on incomplete solver writes and mock termination invocation without calling Abaqus in dry-run mode.
  7. `test_monitor_daemon_clean_completion_exit`: Verified monitor exits cleanly with code 0 upon detecting normal analysis completion.
- Daemon enhanced with CLI options (`--max-cutbacks`, `--poll-interval`, `--max-idle-seconds`, `--dry-run`), line-buffering, and chunk state carryover.

### B. Field-Output Coverage & Irreversibility Observation Boundary
- Executed `scripts/validation/audit_f1752_output_coverage.py`:
  1. **Output Requests:** Confirmed `PK_F1752_CASE_2_CONTINUATION.inp` contains `*OUTPUT, FIELD, FREQUENCY=1` in both Step 1 and Step 2. Because frequency is 1, **every single converged equilibrium increment is saved as an ODB frame**.
  2. **Layer 3 SDV Mapping:** Source audit of `f42_mixed_uel.for` confirms Layer 3 companion UMAT elements (`NOEL 47931 to 71895`) write `STATEV(1) = SV_PHASE_TRIAL(PHYSIDX)` (damage $d$) and `STATEV(2) = SV_H_TRIAL(PHYSIDX, KPT_IDX)` (history $\mathcal{H}$) across all 23,965 physical elements at all integration points.
  3. **Authentic Data Coverage:** Audited authentic F1735 extracted dataset (`f1735_case2_final_frame_sdv.csv` and `f1735_case2_odb_summary.json`): 23,965 physical elements extracted across 254 saved frames (100.0% coverage).
  4. **Observation Boundary Statement:** Local pointwise damage irreversibility ($\min \Delta d \ge -1.0\times 10^{-5}$) and history monotonicity ($\min \Delta \mathcal{H} \ge -1.0\times 10^{-6}\,\text{MPa}$) are strictly observed and verifiable across 100% of converged equilibrium frames. Unconverged trial cutback iterations within the solver are discarded by Abaqus internal memory and are explicitly classified as unobserved.

---

## 3. Predeclared Stop Conditions & Parity Hypotheses

1. **Stop Condition 1 (Cutback Stagnation Guard):**
   If 50 consecutive cutbacks occur in Step 2, `monitor_case2_cutbacks.py` terminates the job via `abaqus terminate job=PK_F1752_CASE_2_CONTINUATION`.
2. **Stop Condition 2 (Structural Severance / Load Drop):**
   The run is classified as structurally complete if $F_{\text{final}} \le 0.14292\,\text{kN}$ (75% drop from peak $F_{\max} = 0.57168\,\text{kN}$).
3. **Stop Condition 3 (Walltime Ceiling):**
   10,800 seconds (3 hours) hard scheduler limit.
4. **Hypothesis 1 (Checkpoint Parity at Inc 252):**
   $|F_{\text{rerun}} - F_{1423271}| / F_{1423271} \le 0.01\%$, $|\Delta u_y| \le 1.0\times 10^{-6}\,\text{mm}$.
5. **Hypothesis 2 (Secondary Crack Continuation):**
   Nonlinear solver continues beyond Increment 252, advancing crack front ($d \ge 0.90$) through the distal ligament toward the right boundary.

---

## 4. Execution Request

- Request: Independent Review Approval for **Task F1753** to submit **exactly ONE bounded PBS job** (`PK_F1753_C2_CONT`) using `submit_f1753_case2_continuation.pbs`.
- Zero PBS jobs were consumed in F1752. Cumulative historical submissions remain exactly 25. Task F1753 will represent the 26th submission.
