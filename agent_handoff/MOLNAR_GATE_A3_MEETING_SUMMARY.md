# Molnar Gate A3 Meeting Summary

Purpose: obtain a supervisor decision before starting uniform-reference studies, MISESERI, adaptive remeshing, or state-transfer work.

Commit with current evidence: `49b6943a1ddd959630fa204e248bf7182e691d41`

## Current Status

```text
Technical result: paper_matched_v2_technical_pass
Diagnostic instrumentation: non_intrusive_pass
Scientific result: paper_matched_v2_scientific_review_incomplete
Irreversibility result: sdv15_completed_increment_irreversibility_violation
Gate A3: reference_data_insufficient
New solution run: not authorized
```

## Key Findings

| Finding | Value |
|---|---:|
| Peak-force error vs approximate Fig. 7 | about `6.45%` |
| Full RF-U NRMSE | about `24.57%` |
| Crack path | connected and approximately horizontal |
| SDV16 decreases | `0` |
| Accepted-increment SDV15 decreases | `2184` |
| Accepted-increment SDV15 decreases `> 1e-6` | `2131` |
| Maximum accepted-increment SDV15 decrease | `2.2384e-4` |
| Timing of SDV15 accepted-increment decreases | all after peak load |
| Diagnostic RF-U perturbation | normalized max difference about `6.54e-13` |

## Interpretation

The targeted diagnostic confirms that the history variable remains monotone, but the phase-field variable decreases between some accepted increments. Since most of these decreases exceed the provisional `1e-6` materiality tolerance, they cannot reasonably be attributed only to ODB precision, visualization lag, intermediate solver calls, or intrusive instrumentation.

Candidate v2 is therefore a technically reproducible Molnar implementation baseline, but it should not be described as satisfying strict pointwise phase-field irreversibility.

## Decision Needed

Please choose one route:

| Route | Meaning | Consequence |
|---|---|---|
| Accept with documented limitation | Candidate v2 remains the technical baseline, with SDV15 irreversibility issue reported explicitly. | Proceed to uniform-reference studies. |
| Gate A3 waiver | Treat candidate v2 as a reproduction of the published implementation, not an irreversibility-clean formulation. | Proceed to Stage B with formal limitation. |
| Corrected formulation | Build a new candidate with explicit phase-field irreversibility enforcement. | Requires new static validation and fresh execution authorization. |
| Reject candidate v2 | Candidate v2 is not accepted as Stage A baseline. | Revisit reconstruction or choose another benchmark route. |

## Recommended Route

Preserve candidate v2 as a technically validated reproduction of the Molnar implementation, document the accepted-increment phase-field decreases as a formulation limitation, and request permission to proceed with uniform-reference studies.

A corrected irreversibility-enforced formulation should be treated as a separate later scientific candidate if required, not as a minor repair or retry of candidate v2.

## References

- Full decision report: `docs/decisions/MOLNAR_GATE_A3_SUPERVISOR_REVIEW.md`
- Completed-increment replay and severity audit: `runs/hpc/paper_matched_single_notch_v2_sdv15_diagnostic_r2/evidence/1375028.mmaster02/postprocessing_completed_increment_replay_time_aligned/`
- Stage A execution log: `docs/reports/STAGE_A_EXECUTION_AND_FAILURE_LOG.tex`
