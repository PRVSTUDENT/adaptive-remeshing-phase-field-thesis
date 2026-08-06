# Session Report: F40 Abaqus CAE Invocation & Model Building Bisection Preparation & Qualification

- **Date**: 2026-08-06
- **Agent**: gemini-antigravity
- **Task ID**: `F40-ISOLATE-F38-CAE-INVOCATION-AND-MODEL-BUILDING-FAILURE`
- **Starting Revision**: `9f03e5c98bd3414338ddd52cfb0690bc779cf738`
- **Preparation Revision (P40)**: `36a779a4e106c812899218a1dd9db0dd00d430e4`
- **Classification**: `f40_f38_cae_invocation_model_building_bisect_clean_linux_qualified_not_authorized`

---

## 1. Summary of Accomplishments

1. **Bisection Diagnostic Package Creation (`M2RMBISECT1`)**:
   - Created package directory `models/generated/mode_ii/f40_f38_cae_invocation_model_building_bisect/`.
   - **Contract Delta Auditor (`f40_invocation_contract_delta.py`)**: Compares F38 vs F39 vs F40 queue directives, resources, modules, abaqus command resolution, working directory, argument forms, absolute paths, environment variables (`PYTHONPATH`, `LD_LIBRARY_PATH`), source deck path/permissions, line endings, and Python 2.7 compatibility. Generates `F38_F39_INVOCATION_DELTA_AUDIT.json`.
   - **12-Stage Bisection Runner (`f40_cae_bisection_runner.py`)**:
     - Executes diagnostic probes `P00` (minimal kernel startup), `P01` (core imports), `P02` (F38 module loading), `P03` (source deck discovery), `P04` (`ModelFromInputFile`), `P05` (imported model inventory), `P06` (geometry conversion), `P07` (independent model ownership), `P08` (assembly operations), `P09` (topology measurement), `P10` (sets/surfaces inventory), and `P11` (step/field output probing).
     - Writes detailed JSON audits after every phase (`P00_KERNEL_STARTUP_AUDIT.json` through `P11_STEP_OUTPUT_PROBING_AUDIT.json`) and stops at the first failure to preserve preceding evidence.
   - **PBS Exit Status & Queue Directives (`M2RMBISECT1.pbs`)**: Uses `#PBS -q entry_imfdfkmq` and `#PBS -l select=1:ncpus=1:mpiprocs=1:ompthreads=1:mem=8gb`, executing `trap - EXIT` and `exit "$first_failure"`.
   - **Disjoint Evidence Reporting (`generate_missing_evidence_report.py`)**: Guarantees `missing_files ∩ existing_files = ∅`.

2. **Guarded Submission Orchestrator (`submit_stage_f40_cae_bisect.sh`)**:
   - Single guarded wrapper containing exactly 1 `qsub` line.
   - Closed default gates (`F40_ALLOW_SUBMISSION=false`, `F40_AUTHORIZE_M2RMBISECT1=false`).

3. **Static & Unit Testing**:
   - Static validator `scripts/validation/validate_f40_cae_bisect_gate.py` passed with 0 failures.
   - Unit test suite `tests/unit/test_stage_f40_batch.py` passed 11/11 tests.

4. **Detached Clean-Linux Qualification**:
   - Preparation commit P40 `36a779a4e106c812899218a1dd9db0dd00d430e4` checked out in `/tmp/f40_clean_qual_36a779a`.
   - Verified 11/11 unit tests, static validator, bash syntax, Python compilation, and package SHA-256 manifests (`SHA256SUMS`, `F40_SHA256SUMS`).

---

## 2. Consumed & Remaining Authority

- `execution_authorized`: `false`
- `submission_approved`: `false`
- `maximum_jobs_now`: `0`
- `maximum_future_submissions`: `0`
- `retry_authorized`: `false`
- `replacement_authorized`: `false`
- `automatic_retry`: `false`
