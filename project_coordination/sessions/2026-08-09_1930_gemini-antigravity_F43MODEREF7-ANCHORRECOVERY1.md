# Session Report: F43MODEREF7-ANCHORRECOVERY1 Lineage Recovery & Qualification

Date: 2026-08-09T19:30:00+02:00
Agent: gemini-antigravity
Task ID: F43MODEREF7-ANCHORRECOVERY1
Base Commit (P): `226cfc837205f5a0665ec84e9ac993279a4022ce`
Preparation Tag (P): `P43MODEREF7-FINAL1` (`226cfc837205f5a0665ec84e9ac993279a4022ce`)
Qualification Location: Detached worktree `/tmp/p7_final1_test_worktree` on `tu_freiberg` (`mlogin01.cluster`)

## Executive Summary
This task establishes a governance-compliant, immutable preparation and qualification lineage for Pair 1R (`M2REF_ONEEL_FRACFIX_VERIFY_R2` and `M2REF_H0_EXACT_FRACFIX_REPRO`).

The historical tags `P43MODEREF6-FINAL2` and `Q43MODEREF6` are preserved unchanged as invalid historical anchors because `P43MODEREF6-FINAL2` was moved/force-pushed and `Q43MODEREF6` pointed to the exact same commit as `P` (`9c8d267d76eb9be8ecc8bc64499dfe5d35afeecf`), violating anchor immutability and provenance separation rules.

A fresh preparation anchor `P43MODEREF7-FINAL1` was pushed ONCE to origin pointing to commit `226cfc837205f5a0665ec84e9ac993279a4022ce`.
Exact-P detached qualification was executed on HPC host `mlogin01.cluster` in `/tmp/p7_final1_test_worktree` with toolchain `gcc/11.4.0`, `intel/2024.2.0`, `abaqus/2023`, `python/gcc/11.4.0/3.11.7`.

All 619 unit tests in the full discovery suite passed with exit code 0 (`OK`). All focused qualification checks passed. Natural post-testing repository status was 100% clean (`git status --porcelain=v1` empty, `git diff` exit code 0, `git diff --cached` exit code 0).

## Historical Anchor Invalidation Record
- `historical_P6_tag_movement_recorded = true`
- `P43MODEREF6_FINAL2_tag_moved_multiple_times = true`
- `P43MODEREF6_FINAL2_force_pushed = true`
- `P43MODEREF6_FINAL2_deleted_or_recreated = true`
- `P43MODEREF6_FINAL2_authorization_anchor_valid = false`
- `Q43MODEREF6_commit == P43MODEREF6_FINAL2_commit` (`9c8d267d76eb9be8ecc8bc64499dfe5d35afeecf`)
- `Q43MODEREF6_differs_from_P = false`
- `Q43MODEREF6_qualification_anchor_valid = false`

Both historical tags `P43MODEREF6-FINAL2` and `Q43MODEREF6` remain preserved in Git history without modification or deletion.

## Frozen Execution Bytes & Hash Contract (Pair 1R)
All 8 execution-critical files under `models/generated/mode_ii/verification_batch` match expected SHA-256 hashes 100% byte-for-byte:

### Job 1: `M2REF_ONEEL_FRACFIX_VERIFY_R2`
- Input (`M2REF_ONEEL_FRACFIX_VERIFY_R2.inp`): `40e5adf0dff1b03da96ab0bef09d3aa45317d5790b4a19931e228d85e33041ea`
- Subroutine (`f42_mixed_uel.for`): `0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8`
- PBS Script (`M2REF_ONEEL_FRACFIX_VERIFY_R2.pbs`): `02ee8081d7b0c77595db0e13e132cd1ec95be9219cb42ecf3b7cc0407b25c7c2`
- Submit Wrapper (`submit_m2ref_oneel_fracfix_verify_r2.sh`): `54543ee9c80310522a07b5f335a66331865f0240e1844e830f00d5f296116c43`

### Job 2: `M2REF_H0_EXACT_FRACFIX_REPRO`
- Input (`M2REF_H0_EXACT_FRACFIX_REPRO.inp`): `3f5d5457977513a92463c05e5220e74ef2fcfc890422010e65c2e1055e6e3c34`
- Subroutine (`f42_mixed_uel.for`): `0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8`
- PBS Script (`M2REF_H0_EXACT_FRACFIX_REPRO.pbs`): `4b91b22ab4afd2ce0338974f164a57fd2bace2682433b7ab206b1cc9ca06a934`
- Submit Wrapper (`submit_m2ref_h0_exact_fracfix_repro.sh`): `cf7c0cd9759713ea6413ebe0cccbb1acc63daa5cb0aa5f3225e685bde061f7ca`

- `pair1r_execution_bytes_changed_since_candidate = false`

## Exact-P Detached Qualification Evidence
- Location: Host `mlogin01.cluster` (`tu_freiberg`), user `pr21vyci`
- Path: `/tmp/p7_final1_test_worktree`
- Detached HEAD: `226cfc837205f5a0665ec84e9ac993279a4022ce` (`P43MODEREF7-FINAL1`)
- Toolchain:
  - GCC: `11.4.0` (`gcc/11.4.0`)
  - Intel Fortran: `2024.2.0` / `ifort 2021.13.0` (`intel/2024.2.0`)
  - Abaqus: `2023` (`abaqus/2023`)
  - Python: `3.11.7` (`python/gcc/11.4.0/3.11.7`)

### Full Suite Discovery Test Run
- Test Command: `python3 -m unittest discover -s tests/unit -p 'test_*.py'`
- `full_test_count`: 619
- `full_test_rc`: 0
- `full_failures`: 0
- `full_errors`: 0
- `full_skips`: 0

### Focused Qualification Checks
- Exact-H0 semantic identity validator: `PASS` (3,998 physical nodes, 3,930 physical elements)
- Pointwise auditor unit tests: `PASS`
- Preflight immutability regression test: `PASS` (all 22 execution files byte-identical)
- PBS notification unit tests: `PASS`
- Mode-II reference regression gate: `PASS`
- UEL phase residual / tangent tests: `PASS`
- SDV14/15/16 producer ownership tests: `PASS`
- UEL VARIABLES/SVARS contract tests: `PASS`
- Read-only submission preflight: `PASS`
- PBS bash syntax check (`bash -n`): `PASS` for both jobs
- Submit wrapper syntax check (`bash -n`): `PASS` for both jobs
- `focused_qualification_pass = true`

### Natural Cleanliness Proof
- `git status --porcelain=v1`: Empty
- `git diff --exit-code`: 0
- `git diff --cached --exit-code`: 0
- `natural_status_empty = true`

## Authority Boundary & Job Justification
- `authorization_ready_for_corrected_verification_batch = true`
- `authorization_ready_for_pair2 = false`
- `execution_authorized = false`
- `submission_approved = false`
- `maximum_jobs_now = 0`
- `qsub_called = false`
- `HPC_submissions = 0`

Job 1 (`M2REF_ONEEL_FRACFIX_VERIFY_R2`) execution justification: `governance_clean_repeat_of_previously_scientifically_useful_one_element_verification` (retained because job 1386248 had useful science but previous batch had a hash-contract governance deviation).
Job 2 (`M2REF_H0_EXACT_FRACFIX_REPRO`) execution justification: `exact_H0_accepted_3930_element_benchmark_reproduction`.
