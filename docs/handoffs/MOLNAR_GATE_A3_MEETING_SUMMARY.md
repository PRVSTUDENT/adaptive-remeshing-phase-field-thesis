# Molnar Gate A3 Meeting Summary

Purpose: decide how to classify Gate A3 for the paper-matched Molnar candidate-v2 baseline and whether Stage B may proceed with documented limitations.

## Model And Run

- Candidate: `paper_matched_candidate_v2`
- HPC job: `1374864.mmaster02`
- Technical result: `paper_matched_v2_technical_pass`
- Scientific result: `paper_matched_v2_scientific_review_incomplete`
- Gate A3: `reference_data_insufficient`
- New solution run: not currently authorized or justified

## Five Key Numerical Results

| Result | Value |
|---|---:|
| Peak RF2 | `0.761702 kN` at `U2 = 0.006110 mm` |
| Peak-force error vs approximate Fig. 7 | `6.4519%` |
| Full-overlap RF-U NRMSE | `24.5705%` |
| Final crack extension at `SDV15 >= 0.95` | about `0.051 mm` |
| SDV15 unresolved output-evidence events | `817` above precision, with `0` mapping errors |

## Positive Findings

- The technical execution passed cleanly: PBS `Exit_status = 0`, Abaqus return code zero, and successful STA completion.
- The final high-damage crack is connected and approximately horizontal across thresholds `0.80` to `0.99`.
- SDV layer architecture, element labels, connectivity, and UMAT IP mapping are verified; `SDV16` is monotone.

## Blockers

- The RF-U mismatch is large over the full overlap and dominated by the post-peak branch.
- The Fig. 7 comparison uses approximate digitized data, not exact author data or approved thesis tolerances.
- `817` SDV15 above-precision non-staggered decreases remain `insufficient_output_evidence` because the retained ODB does not expose completed phase-update states.

## Supervisor Decisions Requested

- Accept, limit, or reject the approximate digitized Fig. 7 curve as the Stage A reference.
- Decide whether peak-force error around `6.45%` and full-overlap NRMSE around `24.57%` are acceptable, or whether pre/post-peak metrics should be separated.
- Decide whether the horizontal connected crack is sufficient qualitatively, and which SDV15 threshold should be reported.
- Decide whether the current SDV15 evidence is sufficient or whether a targeted output-enabled rerun is required.
- Choose the Gate A3 route: provisional pass, waiver with limitations, keep open, or candidate-v2 scientific fail.

## Next Action By Decision Route

| Decision route | Next action |
|---|---|
| Provisional Gate A3 pass | Freeze candidate v2 as the reconstructed baseline and begin Stage B uniform mesh, length-scale, and load-increment studies. |
| Gate A3 waiver with limitations | Proceed to Stage B while preserving RF-U and SDV15 limitations as known benchmark-reconstruction uncertainties. |
| Keep Gate A3 open | Do not start MISESERI/remeshing; decide whether to obtain a better reference, revise reconstruction assumptions, or authorize a targeted output-enabled rerun. |
| Candidate-v2 scientific fail | Diagnose reconstruction assumptions before creating any new candidate. |
