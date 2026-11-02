# Task Definition: F1600-PACKAGE166-R3-EXECUTION

## Objective
Execute qualified Stage C2-0 Package 166-R3 coupled re-equilibration on Candidate C5 mesh (12,996 quads, 13,278 nodes, 51,984 GPs).
Test whether the corrected Package 166-R3 implementation (restored donor_source manifest schema, non-accumulating history contract H^(k) = max(H0, psi+(u^(k))), and corrected post-phase damage increment evaluation delta_d <= 1e-5) achieves true physical convergence and thermodynamic consistency under the authentic holding load (target_uy_mm = 0.0018603125442191958).

## Predecessor Tasks
- `F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE`: Diagnostic evaluation of Package 166 (Job 1419480, PHYSICAL_FAIL, true delta_d = 3.0123e-5 > 1e-5) and Package 166-R2 (Job 1419483, TECHNICAL_FAIL, KeyError: 'donor_source').
- `F1599-PACKAGE166-R3-SCHEMA-REPAIR`: Offline package construction, schema repair, manifest restoration, 11/11 passing unit tests, and authentic datacheck verification.

## Execution Constraints
- Maximum PBS Submissions: 1 (Once-only submission; no blind retries).
- Submission Script: `models/pandey_kumar_mode1/166_c5_package166_r3_c2_0_nonaccumulating_history/submit_M1_C5_P166_R3_C2_0.pbs`.
- HPC Limits: Serial Mode-I (1 CPU, <=16 GB RAM, <=8 hours walltime, queue `entry_imfdfkmq`).
- Remote Run Directory: `/scratch9/pr21vyci/runs/mode1_c5_package166_r3_c2_0_nonaccumulating_history`.
- Production UEL: Strictly preserved SHA-256 `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`.

## Physical Acceptance Criteria
1. True post-phase damage difference: delta_d <= 1.0e-5.
2. Coupled displacement increment: delta_u <= 1.0e-9 mm.
3. Reaction force drift: |RF2 - RF2_donor| / RF2_donor <= 2.0%.
4. Raw total energy drift: |E_tot - E_donor| / E_donor <= 2.0%.
5. Pointwise damage irreversibility: zero healing violations across all 13,278 nodes.
6. History consistency: H* >= psi+(u*) across all 51,984 GPs; zero monotonicity violations.
7. Stage C2-0 continuation gate: First +5 nm forward continuation remains strictly withheld until R3 achieves authentic physical PASS.
