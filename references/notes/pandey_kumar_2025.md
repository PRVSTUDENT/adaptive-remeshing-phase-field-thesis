# Pandey and Kumar (2025)

Source file: `Literature review/TSP_CMES_67858.pdf`

## Thesis Role

Direct reference for Abaqus native error estimation and Python-driven MISESERI pre-refinement for phase-field fracture simulations.

## Extract Before Implementation

- Coarse pre-analysis setup and output requests.
- Meaning and limitations of `MISESERI` and `MISESAVG`.
- Refinement rule parameters: `errorTarget`, `refinementFactor`, `minElementSize`, `maxElementSize`, coarsening, and pass count.
- Required `All_elem` and `umatelem` mapping checks.
- Benchmark sequence, sensitivity studies, and computational savings metrics.

## Starter Decisions

- Reproduce one Pandey-Kumar-style MISESERI pre-refinement case after uniform baseline validation.
- Keep MISESERI marked regions separate from final phase-field crack-path evidence.
- Do not call this online remeshing unless remeshing occurs during fracture evolution with verified state transfer.

## Open Extraction Items

- Exact remeshing API calls for the installed Abaqus release.
- Reproducible benchmark and parameter set for first remeshing test.
