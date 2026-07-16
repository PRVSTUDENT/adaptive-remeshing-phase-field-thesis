# Fig. 7 Comparison Audit

Classification: `approximate_published_reference_comparison`

The reference is the local digitization of Molnar and Gravouil Fig. 7, red dashed `lc = 0.0075 mm`. It has estimated uncertainty of about `+/-0.00004 mm` and `+/-0.015 kN`, and is not exact author data.

## Metrics

- Simulation peak: `0.761702 kN` at `U2 = 0.006110 mm`.
- Reference peak: `0.715536 kN` at `u = 0.005868 mm`.
- Relative peak-force error: `0.064519`.
- Relative peak-displacement error: `0.041257`.
- Full-overlap NRMSE by reference force range: `0.245705`.
- Pre-reference-peak RMSE: `0.044136 kN`.
- Post-reference-peak RMSE: `0.348093 kN`.
- Area-under-curve relative error over the overlap: `0.193324`.
- Compared simulation points within the force digitization uncertainty: `0/184`.

## Interpretation

The peak response is promising, but the full RF-displacement curve still has substantial mismatch relative to the approximate digitized curve. This supports `scientific_review_required`, not a scientific pass/fail based on exact reference data.
