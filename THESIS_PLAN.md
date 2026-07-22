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
- D2B serial continuation was attempted once as job `1376819.mmaster02` and failed technically before validation: PBS `Exit_status=10`, solver exit `1`, classification `stage_d2b_solver_fail`, with `TOO MANY INCREMENTS NEEDED TO COMPLETE THE STEP` during the tiny continuation. No `D2B.ok` exists. A corrected D2B deck is prepared with unchanged transfer values and increased release/continuation increment allowance (`inc=50`), but it has not been submitted.
- D2C/D2D were not submitted and remain blocked until the corresponding upstream `.ok` marker exists.

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
