# Paper-Matched Single-Notch v2 Run Summary

Date: 2026-07-16

## Status

- Candidate: `paper_matched_candidate_v2`
- Job: `1374864.mmaster02`
- Candidate revision: `711dd495bdcb830d695f9d7e56283316c9d417d5`
- Technical result: `paper_matched_v2_technical_pass`
- Scientific comparison: `paper_matched_v2_scientific_review_incomplete`
- Gate A3: `reference_data_insufficient`
- Retry authorization: none

## Technical Result

PBS finished with `Exit_status = 0` on `mnode099/0` after walltime `00:38:38`.
Abaqus returned zero, the ODB/STA/MSG/DAT files exist on scratch, and the STA file reports `THE ANALYSIS HAS COMPLETED SUCCESSFULLY`.

The ODB remains on scratch:

```text
/scratch/pr21vyci/adaptive-remeshing/runs/molnar_paper_matched_single_notch_v2_1374864.mmaster02/molnar_paper_matched_single_notch_v2.odb
```

## Postprocessing Result

The existing ODB was postprocessed read-only. No new Abaqus solution run was submitted.

Key results:

- Peak RF2: `0.761702 kN` at `U2 = 0.006110 mm`
- Final RF2: `0.749110 kN` at `U2 = 0.006700 mm`
- RF-U NRMSE against the approximate digitized Fig. 7 `lc = 0.0075 mm` curve: `0.247493`
- Relative peak force error: `0.064519`
- Relative peak displacement error: `0.041257`
- Final crack extension at `SDV15 >= 0.95`: about `0.0505 mm`
- `SDV16` decrease count: `0`
- `SDV15` decrease count: `6113`
- `SDV15` maximum overshoot: `1.005600`

## No-Solution Scientific Review

Additional no-solution forensic review artifacts were written under:

```text
runs/hpc/paper_matched_single_notch_v2/scientific_review/
```

The review records an RF extraction audit, Fig. 7 comparison audit, response-state selection, crack-path threshold and aggregation-sensitivity checks, SDV15/SDV16 irreversibility audits, solver/resource behavior, and a decision report. The decision classification is `paper_matched_v2_scientific_review_incomplete`; Gate A3 remains `reference_data_insufficient`.

## Boundary

This is not a final scientific pass. Do not submit a retry, second candidate, multi-CPU run, sweep, MISESERI run, remeshing run, state-transfer run, or parameter study without explicit new authorization.
