# Molnar Gate A3 Supervisor Review

Status: `supervisor_review_required`

This package summarizes the candidate-v2 paper-matched Molnar single-notch evidence for a Gate A3 decision. It does not assume supervisor approval and does not authorize another solve.

## Executive Summary

Candidate v2 is technically complete but not scientifically closed. The single authorized HPC execution, job `1374864.mmaster02`, passed the technical gate: PBS `Exit_status = 0`, Abaqus return code zero, ODB/STA/MSG/DAT present, and the STA file reports successful completion. Static validation, deck generation, layer counts, label offsets, and the follow-up full U1/U2/CPS4 mapping audit passed.

The mechanical response is mixed. The simulated peak force is `0.761702 kN` at `U2 = 0.006110 mm`; the approximate digitized Molnar Fig. 7 `lc = 0.0075 mm` reference peak is `0.715536 kN` at `u = 0.005868 mm`. The relative peak-force error is approximately `6.45%`, just outside the provisional `5%` working gate. The full-overlap RF-U NRMSE is approximately `24.57%`, and the mismatch is dominated by the post-peak branch: pre-reference-peak RMSE is `0.044136 kN`, while post-reference-peak RMSE is `0.348093 kN`. The Fig. 7 data are approximate digitized data, not exact author coordinates.

The fracture pattern is qualitatively encouraging. The final crack is connected and approximately horizontal across `SDV15` thresholds `0.80`, `0.90`, `0.95`, and `0.99`; the threshold-dependent final extension ranges from about `0.057 mm` to `0.046 mm`. No disconnected high-damage component is present at those final thresholds.

The state-variable evidence is narrower but still incomplete. `SDV16` is monotone, with `0` decreases at the checked locations. `SDV15` has `6113` retained decrease events; `4816` are at or below ODB precision, `480` above-precision events are classified as `staggered_sync_effect`, and `817` above-precision non-staggered events are now classified as `insufficient_output_evidence`. The layer architecture, connectivity, label offsets, and UMAT integration-point mapping are verified with `0` mapping errors. The remaining SDV15 uncertainty exists because the retained ODB does not expose enough within-increment update-stage information to compare equivalent completed phase-field states.

Gate A3 therefore remains `reference_data_insufficient`. No new Abaqus/PBS solve is currently authorized or justified. A targeted-output rerun should be considered only if the supervisor decides that the missing SDV15 completed-phase-state evidence is essential for Gate A3.

## Evidence Table

All `5%` criteria below are provisional working gates only, not approved thesis criteria.

| Metric/topic | Current result | Evidence quality | Provisional gate | Current disposition |
|---|---:|---|---:|---|
| Technical completion | `paper_matched_v2_technical_pass` | PBS/Abaqus final records | pass required | established |
| Peak force | `+6.4519%` relative error | approximate digitized Fig. 7 comparison | `5%` working gate | supervisor decision needed |
| Peak displacement | `+4.1257%` relative error | approximate digitized Fig. 7 comparison | `5%` working gate | near working gate; supervisor decision needed |
| Pre-peak curve mismatch | RMSE `0.044136 kN`, NRMSE about `0.062` | approximate digitized Fig. 7 comparison | define | supervisor metric needed |
| Post-peak curve mismatch | RMSE `0.348093 kN`, NRMSE about `0.490` | approximate digitized Fig. 7 comparison | define | dominant mismatch |
| Full-curve NRMSE | `24.5705%` | approximate digitized Fig. 7 comparison | `5%` working gate | outside working gate |
| Initial tangent stiffness | about `+51.4%` | derived comparison audit | define | unresolved interpretation |
| Common-domain area | `+19.3324%` relative error | derived comparison audit | define | outside small-error expectation |
| Crack direction | connected, approximately horizontal | final contour threshold audit | qualitative | encouraging; supervisor acceptance needed |
| Crack extension, threshold 0.80 | about `0.057 mm`, 427 damaged elements | element-mean SDV15 threshold audit | choose threshold | threshold-sensitive |
| Crack extension, threshold 0.90 | about `0.053 mm`, 278 damaged elements | element-mean SDV15 threshold audit | choose threshold | threshold-sensitive |
| Crack extension, threshold 0.95 | about `0.051 mm`, 193 damaged elements | element-mean SDV15 threshold audit | choose threshold | current reporting default |
| Crack extension, threshold 0.99 | about `0.046 mm`, 94 damaged elements | element-mean SDV15 threshold audit | choose threshold | threshold-sensitive |
| Disconnected damage | `0` disconnected high-damage elements at final thresholds 0.80-0.99 | crack-threshold audit | none accepted | positive finding |
| SDV15 overshoot | max `1.005600` | ODB scan | define tolerance | supervisor interpretation needed |
| SDV15 decreases below ODB precision | `4816` | detailed event table | retained precision | not physical-healing evidence |
| SDV15 staggered-sync events | `480` above precision | detailed event table and SDV14/SDV15 comparison | source-consistent | explained population |
| SDV15 insufficient-output events | `817` above precision | mapping resolved; completed-state output missing | define requirement | unresolved, not confirmed violation |
| SDV16 monotonicity | `0` decreases | ODB scan and event-location check | monotone required | positive finding |
| Solver convergence | 670 increments, 705 iterations, 0 cutbacks, 0 analysis warnings, 0 errors | solver/resource audit | technical pass | established |
| Runtime and memory | walltime `00:38:38`; CPU `00:35:52`; memory about `2.97 GB`, peak solver memory `2 GB` | PBS and solver records | record only | established |
| Reference-data provenance | approximate digitized Fig. 7 red dashed `lc=0.0075 mm`; uncertainty about `+/-0.00004 mm`, `+/-0.015 kN` | documented digitization, not author data | supervisor acceptance required | independent Gate A3 blocker |

## Decision Questions

Please answer with checkboxes or short notes. No answer is selected by the project record.

A. Is the approximate digitized Molnar Fig. 7 curve acceptable as the Stage A published reference?

- [ ] Yes
- [ ] Yes, with limitations
- [ ] No
- Notes:

B. Is a peak-force error of approximately `6.45%` acceptable for the paper-reconstructed candidate?

- [ ] Yes
- [ ] Revise tolerance
- [ ] No
- Notes:

C. Is the approximately `24.57%` full-curve NRMSE acceptable, given that the mismatch is predominantly post-peak?

- [ ] Yes
- [ ] Yes only with separate pre/post-peak treatment
- [ ] No
- Notes:

D. Should pre-peak and post-peak responses have separate acceptance metrics?

- [ ] Yes
- [ ] No
- Notes:

E. Is the qualitatively horizontal connected crack sufficient for Stage A, or is a quantitative crack-extension target required?

- [ ] Qualitative direction is sufficient
- [ ] Quantitative crack-extension target required
- Notes:

F. Which SDV15 crack threshold should be used for reporting?

- [ ] `0.80`
- [ ] `0.90`
- [ ] `0.95`
- [ ] Other:
- Notes:

G. Is an SDV15 overshoot to approximately `1.0056` acceptable as numerical overshoot, or must the implementation enforce bounds?

- [ ] Accept as numerical overshoot
- [ ] Require additional evidence
- [ ] Require implementation bounds
- Notes:

H. Is the current SDV15 evidence sufficient, or is a targeted output-enabled rerun required to inspect completed phase-update states?

- [ ] Current evidence sufficient
- [ ] Targeted output-enabled rerun required
- [ ] Not needed for Gate A3 but record as limitation
- Notes:

I. May Gate A3 be classified as:

- [ ] Passed provisionally
- [ ] Waived with limitations
- [ ] Kept open pending additional evidence
- [ ] Failed for candidate v2
- Notes:

J. May Stage B uniform-reference studies begin while Gate A3 limitations remain documented?

- [ ] Yes
- [ ] No
- [ ] Only after a defined additional evidence step
- Notes:

## Decision Consequences

| Route | Gate A3 decision | Consequence |
|---|---|---|
| Route 1 | Provisional Gate A3 pass | Freeze candidate v2 as the paper-matched reconstructed baseline and proceed to Stage B uniform mesh, length-scale, and load-increment studies. |
| Route 2 | Explicit Gate A3 waiver | Proceed with Stage B while preserving the RF-U and SDV15 limitations as known benchmark-reconstruction uncertainties. |
| Route 3 | Keep Gate A3 open | Do not start MISESERI or remeshing work; decide whether a better reference, revised reconstruction, or targeted output-enabled rerun is needed. |
| Route 4 | Candidate-v2 scientific fail | Diagnose reconstruction assumptions before creating any new candidate. |

## Current Project Classification

```text
technical result: paper_matched_v2_technical_pass
scientific result: paper_matched_v2_scientific_review_incomplete
SDV15 mapping: structurally verified
SDV15 completed-state monotonicity: not observable from retained output
Gate A3: reference_data_insufficient
new solution run: not authorized
```
