# RUN_MANIFEST - paper_matched_single_notch_v2

Prepared: 2026-07-16

Status:

```text
completed_postprocessed
```

## Candidate

- Candidate name: `paper_matched_candidate_v2`
- Reconstruction version: `paper_matched_candidate_v2`
- Static validation: `static_validation_pass`
- Runnable status: `true`
- Gate A3: open, scientific review required
- Scientific status: `paper_matched_v2_scientific_review_incomplete`

## Repository

- Preparation base revision: `79c2bcc18726ef9bfa34e209044f7cb344ab0af4`
- Candidate commit revision: `711dd495bdcb830d695f9d7e56283316c9d417d5`
- Generator revision: `711dd495bdcb830d695f9d7e56283316c9d417d5`
- PBS submission revision: `711dd495bdcb830d695f9d7e56283316c9d417d5`
- PBS job ID: `1374864.mmaster02`
- Submission time: `2026-07-16 07:39:46 Europe/Berlin`
- Initial scheduler state: `R` on `mnode099`, one node, one CPU, `32gb`, `24:00:00`.
- Notification boundary: this job was already submitted before the permanent PBS email-notification rule was added and remains unchanged.
- Final PBS state: `F`
- Final PBS `Exit_status`: `0`
- Execution host: `mnode099/0`
- Run count: `1`
- Resource use: walltime `00:38:38`, CPU time `00:35:52`, CPU percent `95`, memory `2970760kb`, vmem `3565868kb`.

## Deck And Source

- Candidate deck: `models/generated/molnar_gravouil_2017/paper_matched_single_notch_v2/paper_matched_single_notch_v2.inp`
- Candidate deck SHA-256: `f4d135d6c12d42a94c1874a6453a8865b4806a4e2d3b5018141471ba9245ecf2`
- Preserved Molnar source: `models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension/SingleNotch.for`
- Preserved Molnar source SHA-256: `18944e5bb2a3b7973fd0d4bff03f8e078eef667965343d8a29156d093f53f5f1`
- Candidate user subroutine: `models/generated/molnar_gravouil_2017/paper_matched_single_notch_v2/SingleNotch_v2.for`
- Candidate user subroutine SHA-256: `e587c195c50a5c52a000ca54d3ed00e1bf8161ba2f6aa7b3cf5aacec8425913a`
- Source-copy note: `SingleNotch_v2.for` is copied from the preserved Molnar implementation with only `N_ELEM` updated to `33852` for the candidate-v2 physical element count.

## Model Parameters

- Geometry: `1.0 mm x 1.0 mm`
- Notch: left-edge split-node notch, length `0.5 mm`, `y=0`
- Loading angle: `90 deg`
- Plane strain: `true`
- Thickness: `1.0 mm`
- Young's modulus: `210 kN/mm^2`
- Poisson's ratio: `0.3`
- Critical energy release rate: `0.0027 kN/mm`
- Length scale `lc`: `0.0075 mm`
- Local mesh size `h`: `0.001 mm`
- `h/l`: `0.13333333333333333`
- Physical elements: `33852`
- Layered elements: `101556`
- Minimum element size: `0.001 mm`
- Maximum element size: `0.025 mm`
- Maximum neighboring-size ratio: `1.5`
- Maximum aspect ratio: `25.000000000001368`

## Loading Schedule

| Step | Initial displacement | Final displacement | Increment | Count |
|---|---:|---:|---:|---:|
| Step-1 | 0.0 mm | 0.005 mm | 1e-5 mm | 500 |
| Step-2 | 0.005 mm | 0.0067 mm | 1e-5 mm | 170 |

Arithmetic:

```text
500 * 1e-5 mm = 0.005 mm
170 * 1e-5 mm = 0.0017 mm
0.005 mm + 0.0017 mm = 0.0067 mm
```

## Reference

- Selected approximate reference: Molnar Fig. 7 red dashed `lc = 0.0075 mm`
- Processed reference CSV: `references/derived/molnar_gravouil_2017/paper_matched_single_notch/fig7_lc_0p0075_processed.csv`
- Raw digitized point count: `877`
- Processed point count: `91`
- Digitization uncertainty: `+/-0.00004 mm`, `+/-0.015 kN`
- Classification after extraction must be `approximate_published_reference_comparison`, not exact author-data validation.

## Mesh Preflight

- Preflight file: `results/validation/molnar_paper_matched_single_notch_v2/MESH_QUALITY_PREFLIGHT.md`
- Classification: `mesh_quality_preflight_pass`
- High-aspect-ratio limitation: documented reconstruction limitation; high-aspect elements are outside the notch-tip/fracture-process corridor and do not intersect the expected horizontal crack path.
- Elements bridging open notch: `0`

## Requested PBS Resources

- PBS script: `scripts/hpc/molnar_paper_matched_single_notch_v2.pbs`
- Queue: `entry_imfdfkmq`
- Nodes: `1`
- CPUs: `1`
- Memory: `32gb`
- Walltime: `24:00:00`
- Email notification for future submissions: keep `#PBS -m abe` in tracked PBS scripts, pass the private recipient at submission time with `qsub -M "pr21vyci@mailserver.tu-freiberg.de" -m abe`, validate with `scripts/hpc/validate_pbs_email_notifications.py`, and verify `Mail_Users = pr21vyci@mailserver.tu-freiberg.de` plus `Mail_Points = abe` with `qstat -f` immediately after submission. Verification status: `historically_scheduler_verified`; old-project PBS `qstat` record for job `1362636.mmaster02` reported the same mail user and `abe` mail points.
- Modules: `gcc/11.4.0`, `intel/2024.2.0`, `abaqus/2023`
- Scratch run root: `/scratch/pr21vyci/adaptive-remeshing/runs`
- Lightweight stage root: `/scratch/pr21vyci/adaptive-remeshing/stage`
- ODB retention: scratch only

## Technical Acceptance Criteria

Technical pass classification:

```text
paper_matched_v2_technical_pass
```

Required:

- PBS execution completed.
- Abaqus license checkout succeeded.
- Fortran compilation succeeded.
- Linking succeeded.
- Input processing succeeded.
- Abaqus return code was zero.
- `.sta` exists.
- `.msg` exists.
- `.dat` exists.
- `.odb` exists in scratch.
- `.sta` contains `THE ANALYSIS HAS COMPLETED SUCCESSFULLY`.
- Final PBS success marker printed.

Technical failure classification:

```text
paper_matched_v2_technical_fail
```

Failure categories include `license_failure`, `compilation_failure`, `link_failure`, `input_processing_failure`, `numerical_nonconvergence`, `walltime_exceeded`, `memory_failure`, and `evidence_preservation_failure`.

## Technical Result

Classification:

```text
paper_matched_v2_technical_pass
```

Evidence:

- Final scheduler record: `runs/hpc/paper_matched_single_notch_v2/evidence/qstat_xf_1374864_final.txt`
- Technical summary: `runs/hpc/paper_matched_single_notch_v2/evidence/TECHNICAL_SUMMARY.txt`
- STA: `runs/hpc/paper_matched_single_notch_v2/evidence/molnar_paper_matched_single_notch_v2.sta`
- MSG: `runs/hpc/paper_matched_single_notch_v2/evidence/molnar_paper_matched_single_notch_v2.msg`
- DAT: `runs/hpc/paper_matched_single_notch_v2/evidence/molnar_paper_matched_single_notch_v2.dat`
- Abaqus stdout: `runs/hpc/paper_matched_single_notch_v2/evidence/molnar_paper_matched_single_notch_v2.abaqus_stdout.log`

Acceptance notes:

- PBS finished with `Exit_status = 0`.
- Abaqus return code was `0`.
- ODB, STA, MSG, and DAT exist in scratch.
- STA reports `THE ANALYSIS HAS COMPLETED SUCCESSFULLY`.
- The PBS technical summary reports `classification=paper_matched_v2_technical_pass`.
- The ODB remains on scratch at `/scratch/pr21vyci/adaptive-remeshing/runs/molnar_paper_matched_single_notch_v2_1374864.mmaster02/molnar_paper_matched_single_notch_v2.odb`; it is not copied into Git or handoff.

## Scientific Postprocessing Plan

After a technical pass, extract without rerunning Abaqus:

- top-boundary displacement;
- total reaction force;
- RF-displacement curve;
- peak RF and displacement at peak;
- final RF and displacement;
- area under RF-displacement curve;
- phase-field/SDV fields at response-based states;
- crack-path coordinates;
- SDV16 monotonicity;
- SDV15 local decreases and overshoot;
- final damaged-element count;
- connected crack extension;
- maximum and mean vertical crack-path deviation.

Scientific labels remain separate from technical completion:

```text
paper_matched_v2_scientific_comparison_pending
paper_matched_v2_scientific_provisional_pass
paper_matched_v2_scientific_fail
```

## Scientific Postprocessing Result

Classification:

```text
paper_matched_v2_scientific_review_incomplete
```

Evidence:

- Extraction summary: `runs/hpc/paper_matched_single_notch_v2/extracted/SINGLE_NOTCH_EXTRACTION.md`
- RF-U / phase summary: `runs/hpc/paper_matched_single_notch_v2/extracted/single_notch_rf_u_phase_summary.csv`
- Matched states: `runs/hpc/paper_matched_single_notch_v2/extracted/single_notch_matched_displacement_states.csv`
- Scientific summary: `runs/hpc/paper_matched_single_notch_v2/scientific_check/SINGLE_NOTCH_SCIENTIFIC_CHECK.md`
- Scientific JSON: `runs/hpc/paper_matched_single_notch_v2/scientific_check/single_notch_scientific_check.json`
- RF-U comparison: `runs/hpc/paper_matched_single_notch_v2/scientific_check/rf_u_curve_comparison.csv`
- Crack-path comparison: `runs/hpc/paper_matched_single_notch_v2/scientific_check/crack_path_comparison.csv`
- No-solution forensic review: `runs/hpc/paper_matched_single_notch_v2/scientific_review/SCIENTIFIC_REVIEW_SUMMARY.md`
- Scientific decision: `runs/hpc/paper_matched_single_notch_v2/scientific_review/SCIENTIFIC_DECISION.md`
- RF extraction audit: `runs/hpc/paper_matched_single_notch_v2/scientific_review/RF_EXTRACTION_AUDIT.md`
- Fig. 7 audit metrics: `runs/hpc/paper_matched_single_notch_v2/scientific_review/fig7_comparison_metrics.json`
- Crack threshold audit: `runs/hpc/paper_matched_single_notch_v2/scientific_review/crack_path_threshold_metrics.csv`
- SDV audit metrics: `runs/hpc/paper_matched_single_notch_v2/scientific_review/sdv_irreversibility_metrics.json`
- Solver/resource audit: `runs/hpc/paper_matched_single_notch_v2/scientific_review/solver_resource_metrics.json`

Key results:

- Peak RF2: `0.7617020010948181 kN` at `U2 = 0.00610999995842576 mm`.
- Final RF2: `0.7491104602813721 kN` at `U2 = 0.0066999997943639755 mm`.
- Area under RF-U: `0.0028830400600231396`.
- RF-U comparison against approximate digitized Fig. 7 `lc = 0.0075 mm`: NRMSE `0.24749339943787088`.
- Relative peak force error: `0.06451931788601317`.
- Relative peak displacement error: `0.041256590238391636`.
- Matched RF errors: `27.48%` at `U2=0.002`, `4.98%` at `U2=0.005`, `11.55%` at `U2=0.00599`; final `U2=0.0067` is outside the processed reference range.
- Final matched contour at `SDV15 >= 0.95`: 193 damaged elements, connected crack extension about `0.0505 mm`, approximately horizontal.
- `SDV16` decrease count: `0`.
- `SDV15` decrease count: `6113`; current script categories include `817` genuine-healing candidates, `1764` staggered-sync candidates, and `4816` smaller-than-ODB-precision events.
- `SDV15` maximum overshoot: `1.005600094795227`.
- Scientific decision: `paper_matched_v2_scientific_review_incomplete`.
- Decision basis: post-peak RF-U mismatch dominates, high-damage crack path is connected and horizontal but short/threshold-dependent, and retained SDV15 summaries are insufficient to separate roundoff, staggered-sync, and possible irreversibility-violation populations.

Boundary:

- This is not a final scientific pass.
- Do not submit a retry or any additional Abaqus/PBS job under the completed one-run authorization.
- Gate A3 remains `reference_data_insufficient` pending supervisor-approved tolerances and uniform-reference justification.

## Submission

- Job ID: `1374864.mmaster02`
- Submission time: `2026-07-16 07:39:46 Europe/Berlin`
- Synchronized HPC revision: `711dd495bdcb830d695f9d7e56283316c9d417d5`
- Active-job precheck: passed before this one authorized submission
- HPC working tree precheck: clean enough for the submitted revision
- Retry authorization: none
