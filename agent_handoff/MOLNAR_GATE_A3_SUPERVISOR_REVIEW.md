# Molnar Gate A3 Supervisor Decision Report

Status: `supervisor_decision_required`

Commit with current evidence: `49b6943a1ddd959630fa204e248bf7182e691d41`

## 1. Purpose

This short report asks for a supervisor decision before proceeding to uniform-reference studies, MISESERI pre-refinement, adaptive remeshing, or state-transfer work.

Candidate v2 is a technically reproduced paper-matched Molnar single-notch baseline, but the newest targeted SDV15 diagnostic shows accepted-increment phase-field decreases. The project therefore needs a decision on whether candidate v2 may proceed as a documented-limitation baseline, requires a formal Gate A3 waiver, or must be replaced by a corrected formulation.

No new PBS/Abaqus solution run is currently authorized.

## 2. Model Status

```text
Technical execution: paper_matched_v2_technical_pass
Diagnostic instrumentation: non_intrusive_pass
Paper-curve comparison: paper_matched_v2_scientific_review_incomplete
Irreversibility result: sdv15_completed_increment_irreversibility_violation
Gate A3: reference_data_insufficient
```

Candidate v2 remains valuable as a reproduction of the Molnar implementation and as a technical benchmark artifact. It should not, however, be described as satisfying strict pointwise phase-field irreversibility.

## 3. Main Numerical Findings

| Topic | Current result |
|---|---:|
| Peak-force error vs approximate Fig. 7 | approximately `6.45%` |
| Full RF-U NRMSE | approximately `24.57%` |
| Crack path | connected and approximately horizontal |
| SDV16 decreases | `0` |
| Accepted-increment SDV15 decreases | `2184` |
| SDV15 decreases larger than `1e-6` | `2131` |
| SDV15 decreases larger than `1e-5` | `1362` |
| Maximum SDV15 decrease | `2.2384e-4` |
| Timing of accepted-increment decreases | all after peak load |
| Diagnostic RF-U difference from baseline | normalized max difference approximately `6.54e-13` |

Detailed evidence is preserved in the repository under:

- `runs/hpc/paper_matched_single_notch_v2/scientific_review/`
- `runs/hpc/paper_matched_single_notch_v2_sdv15_diagnostic_r2/`
- `runs/hpc/paper_matched_single_notch_v2_sdv15_diagnostic_r2/evidence/1375028.mmaster02/postprocessing_completed_increment_replay_time_aligned/`

## 4. Interpretation

The diagnostic analysis confirms that the history variable remains monotone, but the phase-field variable exhibits decreases between accepted increments. Because most accepted-increment decreases exceed the provisional numerical tolerance of `1e-6`, the behavior cannot be explained solely by output precision, visualization lag, intermediate solver calls, or intrusive diagnostic instrumentation.

This result is internally consistent with the implementation: the history variable `SDV16` is updated with a maximum operation, while the phase-field state `SDV15` is assigned from the current phase solution without an explicit pointwise `max(previous_phase,current_phase)` enforcement. Thus `SDV16` can remain monotone while `SDV15` decreases at accepted increments.

Candidate v2 is therefore technically reproducible but does not satisfy strict pointwise phase-field irreversibility.

The current scientific status remains incomplete because Gate A3 also depends on supervisor-approved tolerances and acceptance of the approximate digitized Molnar Fig. 7 reference.

## 5. Decisions Required

Please choose one route.

### Option 1: Accept Candidate v2 With A Documented Limitation

Proceed to uniform-reference studies while clearly reporting the SDV15 accepted-increment irreversibility issue as a limitation of the reproduced formulation.

### Option 2: Grant A Formal Gate A3 Waiver

Continue to Stage B while treating candidate v2 as a reproduction of the published implementation rather than an irreversibility-clean formulation.

### Option 3: Request A Corrected Formulation

Create a new scientific candidate with explicit phase-field irreversibility enforcement. This would not be a retry or minor repair of candidate v2. It would require fresh static validation and fresh execution authorization.

### Option 4: Reject Candidate v2 As The Stage A Baseline

Do not proceed with candidate v2. Revisit the reconstruction assumptions or choose another benchmark route.

## 6. Recommended Route

Recommended: preserve candidate v2 as a technically validated reproduction of the Molnar implementation, document the accepted-increment phase-field decreases as a formulation limitation, and request permission to proceed with the uniform-reference studies.

In parallel, a corrected irreversibility-enforced formulation can be treated as a separate later candidate if the supervisor decides that strict pointwise phase-field irreversibility is required for the thesis baseline.

Until the supervisor decides, the project should remain at:

```text
candidate-v2 scientific result: paper_matched_v2_scientific_review_incomplete
SDV15 result: sdv15_completed_increment_irreversibility_violation
Gate A3: reference_data_insufficient
new solution run: not authorized
```
