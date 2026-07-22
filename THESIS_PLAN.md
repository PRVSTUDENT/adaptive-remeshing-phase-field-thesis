# Thesis Execution Plan

## Topic

**Application of Built-in Adaptive Remeshing and Mesh Refinement Features in Abaqus to Fracture Simulations Using Phase-field User Elements**

## Research question

Can Abaqus native error-estimation and remeshing functions be connected reliably to a phase-field UEL workflow so that local mesh refinement captures the relevant fracture zone while preserving accuracy, required state information, reproducibility, and compatibility with IMFD/ABAQUSER post-processing?

## Working thesis contribution

The contribution should not be framed merely as "a crack was simulated with a refined mesh." A defensible contribution is a verified, automated, and documented Abaqus workflow that:

1. reproduces an established phase-field fracture reference implementation;
2. exposes a stress field to Abaqus native error estimation;
3. generates a locally refined mesh from MISESERI information;
4. rebuilds the UEL/UMAT model correctly on the refined mesh;
5. quantifies accuracy and cost against a uniformly fine reference;
6. identifies limitations of pre-refinement, state transfer, shared data, and parallel execution; and
7. connects the final fields to IMFD/ABAQUSER visualization.

## Current execution posture

- The full starter pipeline is in place, the local user-subroutine smoke gate passed, and the unchanged Molnar one-element technical and source-relation scientific gates passed.
- The unchanged Molnar single-notch benchmark has a local technical pass and first RF-U/phase-field extraction. The immediate implementation target is now scientific comparison against Molnar reference behavior.
- HPC is the intended Abaqus runtime, but production submissions are blocked until maintenance clears and `docs/methods/ENVIRONMENT.md` is completed.
- Evolving remeshing with state transfer is mandatory for the thesis scope, but no online-remesh claim is allowed until controlled transfer tests and fracture-relevant transfer checks pass.
- Numeric tolerances are provisional working gates only until supervisor-approved thesis tolerances are recorded.

## Source roles

| Source | Thesis role |
|---|---|
| Molnar and Gravouil (2017) | Main reproducible staggered UEL baseline; mesh/length-scale/load-increment behavior; UMAT visualization layer |
| Msekh et al. (2015) | Monolithic variational UEL/UMAT reference; residual/tangent construction and visualization architecture |
| Pandey and Kumar (2025) | Direct MISESERI-driven Python pre-refinement workflow and benchmark/sensitivity design |
| Diddige, Roth, and Kiefer (2025) | IMFD multi-field UEL architecture and ABAQUSER post-processing context |
| Rapid study guide | Working synthesis, checklist, and gap analysis |

## Work packages

### WP0 - Environment, starter pipeline, and source preservation

Deliverables:
- Completed starter repository structure, configs, and dry-run validators.
- Structured literature notes and equation/benchmark/implementation maps.
- Software environment record: OS, Abaqus, compiler, precision, CPU layout.
- Read-only archive/checksums of original code and example decks.
- Repository initialized with large-output exclusions.
- Successful compiler/linker smoke test.

Exit gate:
- Starter validators pass, original code compiles, and a trivial job starts without undocumented physics changes.

### WP1 - One-element verification

Tasks:
- Reproduce the supplied one-element problem.
- Record DOF ordering, phase-field convention, `PROPS`, `SVARS/STATEV`, integration points, and staggered sequence.
- Verify elastic response, degradation, phase-field evolution, and irreversibility.
- Add a finite-difference tangent/residual check where practical.

Deliverables:
- `ONE_ELEMENT_VERIFICATION.md`.
- Automated extraction script.
- Reference curves and tolerances.

Exit gate:
- Status: passed locally for the unchanged one-element ODB using provisional numerical tolerances.
- Analytical/source-defined trends match and interface mappings are documented.

### WP2 - Uniform-mesh benchmark reproduction

Start with:
- single-edge-notched Mode I benchmark;
- add Mode II or L-panel only after the first benchmark is stable.

Current local status:
- Unchanged Molnar single-notch technical run: `technical_pass_scientific_unchecked`.
- First extraction path: RF-U curve, matched displacement states, `SDV14`/`SDV15`/`SDV16` contour CSVs, warnings, element count, and job timing are recorded.
- Scientific comparison against the Molnar paper/reference behavior is pending.

Tasks:
- Reproduce geometry, material, fracture parameters, loading, and output.
- Perform separate studies of `h/l`, `l`, and load increment.
- Create a uniformly fine reference.
- Quantify force-displacement and crack-path agreement.

Deliverables:
- Reference run manifest and processed data.
- Mesh/load/length-scale convergence report.
- Automated validation script.

Exit gate:
- A reference solution is justified and acceptance metrics are fixed before adaptive testing.

### WP3 - MISESERI pre-analysis and remeshing reproduction

Tasks:
- Build coarse model and facsimile/UMAT stress-output layer.
- Validate `umatelem` and `All_elem` connectivity mapping.
- Request `MISESERI`, `MISESAVG`, `S`, `EVOL`, `U`, `RF`, and `SDV`.
- Implement configuration-driven remeshing rule.
- Save coarse ODB, MISESERI map, remeshing parameters, refined mesh, and regenerated input deck.
- Run refined elastic dry test.

Deliverables:
- Reusable Abaqus Python remeshing script.
- Deck-integrity checker.
- Reproduction of one Pandey-Kumar example.

Exit gate:
- Refined deck is structurally valid and local element size satisfies the selected `h/l` target.

### WP4 - Refined phase-field benchmark and efficiency comparison

Tasks:
- Run final phase-field analysis on the refined mesh.
- Compare with the uniform fine reference at matched displacement states.
- Report peak-force error, curve error, fracture-energy error, crack-path distance, element count, wall time, CPU time, memory, increments, and iterations.
- Study `errorTarget`, `refinementFactor`, coarse mesh size, and min/max element size.

Deliverables:
- Accuracy-cost Pareto plots.
- Sensitivity matrix.
- Clear separation between MISESERI prediction and final crack result.

Exit gate:
- At least one refined configuration meets the approved scientific tolerance and shows measured resource benefit, or a well-supported negative result explains why it does not.

### WP5 - Mandatory evolving remesh/state transfer investigation

The thesis branch requires evolving remesh/state transfer. Phase field, history, and integration-point variables must be transferred during the fracture process before any online-remesh claim is made.

Current D2 status:
- D1 established deterministic, bounded transfer mechanics, not negligible transfer error.
- D1 retained baselines: nodal `d` L2 error `0.0270`, nodal `d` maximum error `0.0850`, IP `H` L2 error `0.0108`, IP `H` maximum error `0.0234`, and energy difference `-0.00769`.
- D2A executable ingestion package is prepared for a tiny Abaqus UEL/UMAT target model under `models/state_transfer/d2_tiny_transfer/executable/`.
- D2A passed on HPC job `1376785.mmaster02` with classification `stage_d2a_state_ingestion_pass`, solver exit `0`, readable ODB, `D2A.ok`, `target_ip_coverage=1.0`, maximum `SDV15` interpolation error `0.0`, and maximum `SDV16/H` error `6.428999999030793e-09`.
- The D2A route uses a separate D2 source variant, confirms the preserved Molnar U1 phase DOF as `3`, initializes transferred `H` once from an element/IP keyed table, and mirrors transferred phase/history to visualization `SDV15`/`SDV16`. Abaqus did not expose the UEL phase DOF as usable nodal `U` output in the smoke ODB, so the accepted phase-ingestion proof is through `SDV15`.
- D2B serial continuation first attempt `1376819.mmaster02` is preserved as `stage_d2b_solver_fail_increment_limit`: initialization and release completed, continuation partially converged, and the maximum increment count was exhausted.
- Corrected D2B R1 job `1376825.mmaster02` passed with classification `stage_d2b_serial_continuation_pass`, solver exit `0`, readable ODB, `D2B_R1.ok`, canonical `D2B.ok`, `target_ip_coverage=1.0`, maximum initial and release `SDV15`/`SDV16` differences `0.0`, observed `U2=1e-05`, finite `RF2=3.46317381026e-07`, and recorded `ALLWK` continuation jump `1.2830926425511091e-11`.
- D2C four-thread repeatability job `1376831.mmaster02` passed with classification `stage_d2c_thread_repeatability_pass`, solver exit `0`, readable ODB, confirmed `1 MPI RANK x 4 THREAD`, `D2C.ok`, `target_ip_coverage=1.0`, maximum `SDV15` and `SDV16` thread-vs-serial differences `0.0`, final `U2` difference `0.0`, final `RF2` absolute/relative differences `0.0`, RF-U NRMSE `0.0`, F3 `ALLWK` absolute difference `0.0`, and unchanged increment sequence.
- D2D0 ABAQUSER availability audit is formally blocked as `stage_d2d_blocked_abaquser_not_found`: no executable, module, source implementation, or documented runnable interface was found on the login node. Evidence is under `runs/hpc/stage_d2/d2d_abaquser_verification/`.
- D3 interrupted transfer is prepared only as a design/package plan around a small H0 diagnostic early pre-peak checkpoint near `U=0.003 mm`. No D2D PBS job, D3 solver job, or interrupted Molnar transfer was submitted.
- D3A0/D3A1 tested reuse of the existing H0 ODB `1376154.mmaster02`. The corrected CAE/ODB-only extraction attempt `1376879.mmaster02` selected `U2=0.003000000026077032 mm`, extracted 15720 element/IP rows with `target_ip_coverage=1.0`, finite `SDV15`/`SDV16`, `max_d=0.08412302285432816`, `max_H=0.0512588769197464`, checkpoint `RF2=0.39450356364250183`, and `RF2/H0_peak=0.5421925638518931`. D3A remains blocked/not accepted because the source ODB lacks `ALLIE`, `ALLSE`, and `ALLWK`; no `D3A.ok` exists and D3A2 was not executed.
- D3A-E independently reconstructed checkpoint energy from the existing H0 ODB exports and H0 deck connectivity in CAE/ODB-only job `1376885.mmaster02`. Bulk-energy consistency passed (`SDV12` vs `0.5*S:E` relative difference `8.341766862422363e-10`) and the reported energy-balance residual was `0.012594035606728515`, but validation failed because five Jacobian determinants from the accepted H0 deck connectivity were non-positive. Classification: `stage_d3a_energy_reconstruction_fail`; no `D3A.ok` exists and D3A2 remains blocked.

Tasks:
- Inventory all state variables.
- Transfer a known field between meshes.
- Measure L2/max errors and energy jumps.
- Verify bounds and irreversibility.
- Check serial/parallel repeatability.
- Apply the verified transfer path to a fracture-relevant checkpoint only after controlled-field transfer passes.

Deliverables:
- State-transfer design and test report.
- Explicit list of supported/unsupported fields.

Exit gate:
- No evolving-remesh claim without verified controlled-field and fracture-relevant state-transfer tests.

### WP6 - IMFD/ABAQUSER integration

Tasks:
- Identify the minimal interface needed to expose phase-field and mechanical quantities.
- Map variable names, components, units, interpolation, and integration-point ordering.
- Verify selected ABAQUSER values against an independent extraction script.
- Document visualization steps.

Deliverables:
- Minimal test case.
- Interface mapping table.
- Reproducible visualization procedure.

Exit gate:
- ABAQUSER output numerically matches independent results for selected checkpoints.

### WP7 - Final recommendations and thesis writing

Recommendations must be tied to measured evidence for:
- suitable `h/l` ranges;
- coarse pre-analysis resolution;
- `errorTarget` and `refinementFactor`;
- size-transition quality;
- one versus multiple remeshing passes;
- limits of MISESERI as a fracture-zone predictor;
- state-transfer and parallelization risks;
- accuracy-versus-cost tradeoffs.

## Minimum benchmark progression

1. One element - interface and constitutive verification.
2. Single-edge-notched Mode I - basic initiation and straight propagation.
3. Mode II or L-panel - curved/mixed-mode crack path.
4. Notched plate with hole - competing stress concentration/path deflection.
5. Multi-hole case only if time and baseline stability permit.

Do not begin all benchmarks in parallel. Each new benchmark should reuse a validated pipeline.

## Validation matrix

| Study | Suggested levels | Hold fixed | Primary outputs |
|---|---|---|---|
| Mesh convergence | `h/l = 1, 1/2, 1/3, 1/4` as feasible | `l`, `Gc`, loading | peak force, energy, crack path |
| Length scale | 3-4 values | maintain selected `h/l` | strength regularization, crack width |
| Load increment | coarse/medium/fine/adaptive | mesh and `l` | initiation, unstable propagation, iterations |
| Error target | several values | min/max size | marked area, elements, accuracy |
| Refinement factor | mild to aggressive | error target | transition quality, runtime |
| Coarse mesh | several sizes | same final local size | prediction reliability |
| State transfer | before/after mapping | same physical state | L2/max errors, bounds, energy jump |
| Parallelization | serial and available CPU layouts | same model | reproducibility, shared-data safety |

## Quantitative outputs

Use a common displacement grid for curve comparison.

```text
e_peak  = abs(Fmax_adapt - Fmax_ref) / abs(Fmax_ref) * 100%
e_curve = norm(F_adapt(U) - F_ref(U), 2) / norm(F_ref(U), 2) * 100%
saving  = (cost_ref - cost_adapt) / cost_ref * 100%
```

For crack path, define before comparison:
- phase-field threshold;
- path extraction method;
- matched displacement/load state;
- geometric distance metric.

## Evidence required for every thesis figure/table

- Run identifiers and source revision.
- Exact parameters and units.
- Software/hardware environment.
- Generation script.
- Matched comparison state.
- Definition of plotted quantities.
- Classification: exploratory, feasibility-only, provisional, or validated.

## Suggested thesis chapter structure

1. Introduction and research questions.
2. Variational phase-field fracture and numerical resolution requirements.
3. Abaqus UEL/UMAT and IMFD/ABAQUSER implementation architecture.
4. Baseline verification and uniform-mesh reference studies.
5. Abaqus MISESERI-based mesh-refinement methodology.
6. Refined benchmark results, sensitivity, and computational efficiency.
7. State-transfer and implementation limitations.
8. Practical recommendations and conclusions.

## Critical thesis distinctions

- stress-error indicator versus phase-field error estimator;
- pre-refinement versus online adaptive remeshing;
- technical completion versus scientific validation;
- visualization transfer versus physical-state transfer;
- visual crack agreement versus quantitative curve/path/energy agreement.
