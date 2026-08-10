# Project Current State

Last Updated: 2026-08-10T04:04:00+02:00
Active Agent: gemini-antigravity
Protocol Version: 1

## Active Task
- Task ID: `F43MODEREF-VERIFY-SUBMIT2`
- Task Description: Guarded Submission and Monitoring of Authorized Pair 1R Verification Batch (1-element analytical verify & exact 3,930-element H0 reproduction).
- Status: `pair1r_verification_batch_authorized_submitting`
- Historical Invalid Tag Lineage: `P43MODEREF7-FINAL1` (`P43MODEREF7_FINAL1_created_after_qualification = true`, invalid authorization anchor), `Q43MODEREF7-FINAL1` (preserved historically)
- Final Immutable Preparation Tag (P): `P43MODEREF7-FINAL2` (`13ea9ec77c75c98f6d80028264d344fc84143aa4` pointing to preparation commit `55822a75adc0e9a8223a703ca6ca8f168b96facd`)
- Final Immutable Qualification Tag (Q): `Q43MODEREF7-FINAL2` (`ea64ce9577f678ae4050d2915f1947e45748d5d2`)
- Qualification Location: Isolated worktree `/tmp/p7_final2_test_worktree` on `tu_freiberg` (619/619 unit discovery tests pass, rc=0, 12/12 focused qualification checks pass, naturally clean)

## Verification Batch Pair 1 Historical Results & Corrected Classification
1. **`M2REF_ONEEL_FRACFIX_VERIFY`**:
   - `Job_ID`: `1386248.mmaster02` (Finished, Exit status 0)
   - `Scheduler_Result`: `PASS`
   - `Technical_Result`: `PASS`
   - `Scientific_Result`: `provisional_PASS_for_local_UEL_behavior`

2. **`M2REF_H0_FRACFIX_REPRO`**:
   - `Job_ID`: `1386249.mmaster02` (Finished, Exit status 0)
   - `Scheduler_Result`: `PASS`
   - `Technical_Result`: `PASS`
   - `Scientific_Result`: `HOLD_reference_identity_mismatch` (2,500 quads synthetic grid instead of 3,930 physical element accepted H0 benchmark)

## Scientific & Governance Summary
- `pair1_scientific_result = HOLD`
- `authorization_ready_for_pair2 = false`
- `pointwise_irreversibility_audit`: 0 negative phase transitions ($\Delta d < 0 = 0$) and 0 negative history transitions ($\Delta H < 0 = 0$) across 710,000 IP transitions.
- `pointwise_sdv14_vs_sdv15_agreement`: max abs diff $|SDV14 - SDV15| = 0.0000000000$ across all 720,000 sample points!
- `exact_H0_semantic_identity`: `PASS` (3,998 physical nodes, 3,930 physical quad elements per layer, 101 split-notch nodes, 0 non-positive area elements).

## Prepared Verification Batch Pair 1R (Authorized by Human Directive)
1. **`M2REF_ONEEL_FRACFIX_VERIFY_R2`** (1-element analytical/unit verification):
   - `INP_SHA256`: `40e5adf0dff1b03da96ab0bef09d3aa45317d5790b4a19931e228d85e33041ea`
   - `UEL_SHA256`: `0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8`
   - `PBS_SHA256`: `02ee8081d7b0c77595db0e13e132cd1ec95be9219cb42ecf3b7cc0407b25c7c2`
   - `SH_SHA256`:  `54543ee9c80310522a07b5f335a66331865f0240e1844e830f00d5f296116c43`
   - Resources: 1 CPU, 8 GB memory (`mem=8GB`), 00:15:00 walltime, queue `entry_imfdfkmq`

2. **`M2REF_H0_EXACT_FRACFIX_REPRO`** (Exact 3,930-element accepted H0 benchmark reproduction):
   - `INP_SHA256`: `3f5d5457977513a92463c05e5220e74ef2fcfc890422010e65c2e1055e6e3c34`
   - `UEL_SHA256`: `0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8`
   - `PBS_SHA256`: `4b91b22ab4afd2ce0338974f164a57fd2bace2682433b7ab206b1cc9ca06a934`
   - `SH_SHA256`:  `cf7c0cd9759713ea6413ebe0cccbb1acc63daa5cb0aa5f3225e685bde061f7ca`
   - Resources: 1 CPU, 8 GB memory (`mem=8GB`), 01:00:00 walltime, queue `entry_imfdfkmq`

## Current HPC Authority Boundary
- `authorization_ready_for_corrected_verification_batch = true`
- `execution_authorized = true`
- `submission_approved = true`
- `maximum_jobs_authorized = 2`
- `authorized_jobs = ["M2REF_ONEEL_FRACFIX_VERIFY_R2", "M2REF_H0_EXACT_FRACFIX_REPRO"]`
- `qsub_called = true` (via guarded submission wrappers)

