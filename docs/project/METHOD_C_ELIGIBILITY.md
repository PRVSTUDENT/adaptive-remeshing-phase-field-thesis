# Versioned Method C eligibility candidate, v1

Status: **NOT ACTIVATED / NOT PRODUCTION READY**. No real eligible-operation execution/recovery cycle is claimed.

The candidate policy is project_coordination/policies/method_c_serial_continuation_v1.json. It is intentionally restricted to the existing R6 C4 serial continuation procedure: authentic accepted predecessor, one +5 nm increment, <=130 outer iterations, frozen production UEL, 1 CPU/16 GB/8 h, original coupled/KKT/irreversibility/force/RAW-energy thresholds. New formulations, runtime source changes, different controls, C5 transfer or new operation classes require a fresh independent policy review. This task does not designate a draft procedure as previously approved.

scripts/controller/method_c_eligibility.py emits a hash-bound review request covering the exact policy, evaluator, eligibility validator, wrapper, provenance verifier and execution/SSH adapters plus pinned numerical sources. Its activation record is separate and must be genuinely independently reviewed. The author cannot self-activate: candidate metadata is insufficient, and no activation record or production signature was created. Existing ChatGPT structured independent review is retained; its authenticated bridge signer remains unavailable. A public key alone is not proof that the author lacks access to its signer. All author-writable workspace scripts also require a separately controlled/protected execution boundary before this can be called a protected production service. No OS protection, independent identity or deployment is asserted merely by checking a filename or hash. Missing independent review and that protected boundary are explicit stop conditions, not per-job human permits.

Once genuinely activated and protected, the candidate wrapper Invoke-MethodCEligibleExecution.ps1 validates scientific eligibility and invokes only Invoke-Mode1Execution.ps1. It never runs definition-provided shell commands. The existing engine retains live technical/notification/resource checks and once-only reservation/receipt recovery. The protected scientific evaluator is rerun; Gemini-written PASS flags are insufficient. No per-job LLM registration is needed within an activated unchanged class, but genuine predecessor acceptance remains mandatory. No automatic activation or watcher deployment occurred here.

R6's prepared status now routes to exactly one pending-review event. PREPARED_FOR_INDEPENDENT_REGISTRATION_REVIEW and REVIEW_REQUIRED both remain non-executable. Regression tests verify repeated calls leave the event unchanged. The operation definition and original review history are preserved.

## Actual R6 predecessor result

The exact-load request is uy=0.0018603125442191958 mm. Actual saved Abaqus outer90/91 mechanical endpoints were retrieved read-only from the existing 1419162 run. All 7265 nodes, 14530 displacement components and 28224 GP histories were checked against the authentic checkpoint. Displacement/damage and saved-history identity differences are zero. Recomputed H differs from saved H by at most1.04e-13 MPa from floating-point reconstruction; this diagnostic is not a failure of saved-state preservation.

| Gate | Measured | Required |
|---|---:|---:|
| Delta H | 9.146627109e-7 MPa | <=1e-6 |
| Delta d | 4.000000009e-8 | <=1e-5 |
| Delta u | 1.813670015e-11 mm | <=1e-9 |
| Signed dual | 0 | 0 |
| Complementarity | 1.026386847e-14 | <=1e-6 |
| Free residual | 1.377257507e-12 | <=1e-6 |
| Minimum damage change | +4.1136e-6 | >=-1e-6 |
| Minimum history change | 0 | >=0 |
| Reaction force | 0.18411666272311777 kN | discrepancy<=5% |
| RAW total energy | 0.00022418821426719904 kNmm | discrepancy<=2% |

The last two discrepancies are **UNVERIFIED**, because the inspected authentic donor1416259 table contains no exact-load row (nearest saved load0.00186359370mm). No interpolation, nearest-row substitution or summary-derived reference was used. The alternative reference path named in the prior projection, models/pandey_kumar_mode1/146_c4_package146_c1_2_continuation/converged_checkpoint_01.json, is absent; its named runtime report is absent too. No complete checkpoint physical PASS can be issued from this evidence.

Reproduce numerical assessment with py -3 scripts/validation/evaluate_package157_r6_checkpoint.py --output <fresh-path>. Canonical quantitative result: results/validation/package157_r6_checkpoint_scientific_review.json. The earlier package157_r6_checkpoint_acceptance.json is retained as nonauthoritative failed assessment-tool evidence: an unnecessary bitwise comparison against recomputed H falsely flagged roundoff. The correction compares all H values to the authentic saved checkpoint exactly and retains recomputation differences diagnostically, without changing any scientific threshold. It does not supersede any authentic solver failure.

R6 staging/datachecks remain PASS_BOTH from fb17c37e. No rerun was needed. Actual R5 1419269 remains RUNNING on mnode097, run_count1. No R6, dummy job or replacement package was submitted. Next scientific work is to obtain/review an authentic independent exact-load reference, not assert acceptance or start another generic controller audit. Missing reference and missing independent policy activation stop this path. December13 target retained.
