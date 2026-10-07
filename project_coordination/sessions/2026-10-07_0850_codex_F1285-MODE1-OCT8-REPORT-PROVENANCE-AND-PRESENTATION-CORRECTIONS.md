# F1285 — Mode-I October 8 Report Provenance and Presentation Corrections

- **Agent:** Codex
- **Start:** 2026-10-07T08:30:08+02:00
- **End:** 2026-10-07T08:50:00+02:00
- **Starting commit:** `7639d57cbdcd979bb012c853a615f2fbb7c4b083`
- **Phase:** `GATE6B_EVALUATION_COMPLETE_READY_FOR_SUPERVISOR_SIGNOFF`
- **HPC activity:** None. No submission, authorization change, retry, deletion, or scheduler action occurred.

## Outcome

The focused October 8 supervisor report remains 10 pages and now separates the three scientific mesh roles unambiguously:

1. Historical Stage-13/Step-1 broad morphology: exactly 57,901 base finite elements; morphology evidence only.
2. Corrected ET1: 14,483 base finite elements; preferred practical adaptive mesh.
3. Spatial-fine adaptive: 57,929 base finite elements; Job `1410504.mmaster02`; fine adaptive convergence check.

The report now uses the fixed 15,192-FE reference, corrected ET1, and spatial-fine adaptive case consistently in the main mechanical, stiffness, and spatial verification figures. Page 2 retains only the requested 71,320-FE full-domain and crack-tip views. The tolerance page is simplified, Table 3 contains the 57,929-FE mechanical row and purpose column, the ET1 stiffness legend is corrected to Job `1409982`, the mechanical section no longer claims cost evidence, the energy residual is defined explicitly, and the localization wording uses “reference width” rather than claiming an exact analytical identity.

## Provenance resolution

- `PK_M1_STAGE13_ET10.inp`: 57,901 elements = 56,351 CPE4 + 1,550 CPE3; SHA-256 `872B54A69A882D96CFDEE40A69D12464472AD42143D2163ED0E9C900BA7D2F8A`.
- `PK_M1_STAGE14_STEP1_ALLINC.inp`: the same 57,901-element historical morphology; SHA-256 `AAE0EE43...`.
- `PK_M1_STAGE10_INF_ADAPTED_RAW_1PCT.inp`: 57,929 elements = 56,339 CPE4 + 1,590 CPE3; SHA-256 `380CD726...`.
- `PK_MODE1_STAGE14_ADAPT_SPATIAL_FINE_FRACTURE.inp`: 57,929 base finite elements per layer and 173,787 total three-layer element records; SHA-256 `537C8C6617945AFD66E135C1DF4E2C34211F47FBEEEC44E4C145A8551CC1EEFD`.

Therefore, 57,901 and 57,929 are distinct meshes and not alternative labels for the same discretization.

## Verification

- Final PDF: 10 pages, 6,710,754 bytes.
- Final PDF SHA-256: `4942529C35DCF062118A31B1D24B4C2D689513BD386B8CA690BEFDEF176A4406`.
- LaTeX build: passed with no LaTeX/package warnings, overfull boxes, underfull boxes, or fatal errors in the final isolated-build log.
- Visual QA: all 10 pages inspected; the page-2 crop and revised page-7 stiffness plot were re-rendered and re-inspected after their final changes.
- Regression tests: `173 passed in 8.47s`.

The first regression run produced `172 passed, 1 failed` because the reproduction manifest retained old hashes for two edited plotting scripts. The failure was deterministic and local; both manifest hash/size entries were updated, and the full suite then passed. An initial crop rebuild also resolved the output directory relative to the report folder and wrote derived LaTeX files locally; subsequent builds used an explicit absolute temporary directory. Pre-existing dirty `report_main.bbl` and `report_main.blg` remain un-staged.

## Files governed by this task

- Supervisor report source and final PDF.
- Report-local three-case convergence, spatial-localization, and stiffness figures.
- Canonical stiffness figure and its reproducible generator.
- Supervisor-mode options in the two Gate-6B synthesis generators.
- Reproduction-manifest hashes for the two modified governed generators.
- Coordination ledgers and this session report.

All unrelated pre-existing dirty and untracked paths were left unstaged and otherwise untouched.
