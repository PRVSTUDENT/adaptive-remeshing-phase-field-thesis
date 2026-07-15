# Decision Note 0002 - Gate A3 Reference Route

Date: 2026-07-14

Status: superseded by proposal-directed paper-matched benchmark route

Update 2026-07-15:

The three-route framing below is preserved as history, but it is no longer the
active next-step decision. The thesis proposal already defines the benchmark
sequence: reproduce the established phase-field implementation, reproduce the
unrefined Molnar benchmark, establish a uniformly fine reference, then compare
Pandey--Kumar MISESERI refinement against that uniform reference. Therefore the
next Gate A3 action is to prepare a paper-matched Molnar Mode-I single-notch
benchmark, not to ask the supervisor whether the smaller supplementary deck
should be treated as the exact Fig. 7 comparison target.

The smaller supplementary `SingleNotch` deck remains preserved unchanged and
counts as supporting technical reproducibility evidence. It should not be forced
into an exact numerical comparison with Fig. 7 when the mesh/model details do
not match. The applicable paper reference should instead be digitized and
documented as an approximate paper reference for the newly prepared
paper-matched benchmark configuration.

## Context

The unchanged Molnar supplementary `SingleNotch` benchmark has passed the local technical gate and has reproducible RF-U, phase-field, crack-path, bound, and irreversibility diagnostics. Gate A3 remains classified:

```text
reference_data_insufficient
```

The reason is scientific, not technical. The published Molnar and Gravouil Fig. 7 single-notch study uses a larger model of about 22,000 elements, while the supplied supplementary `SingleNotch` deck is the smaller model of about 4,000 physical elements. Material parameters and fracture toughness match, but length scale, element count, load-increment details, and the applicable Fig. 7 curve label remain unresolved.

## Historical Routes Considered For The Smaller Supplementary Deck

These routes are retained to explain why the smaller supplementary deck was not
closed as a scientific Fig. 7 match.

### Historical Route 1 - Exact RF-U Reference

Acquire original RF-U coordinates from the authors, supplementary data, or another authoritative source.

Use when:

- the exact source data correspond to the smaller supplementary `SingleNotch` deck, or the mismatch is explicitly documented;
- units, axes, curve label, and uncertainty are known.

Outcome:

- populate `references/derived/molnar_gravouil_2017/single_notch/rf_u_reference.csv`;
- rerun `abaqus python scripts/validation/check_molnar_single_notch.py`;
- Gate A3 can be evaluated quantitatively.

### Historical Route 2 - Approximate Fig. 7 Overlay

Digitize a selected Fig. 7 curve and use it as an approximate literature overlay.

Required documentation:

- exact Fig. 7 curve label and length scale;
- axis calibration and units;
- digitization method and uncertainty;
- mesh/length-scale/load-increment mismatch against the supplementary deck;
- statement that this is approximate, not exact reproduction.

Outcome:

```text
scientific_comparison_approximate
```

This route should not be described as an exact pass/fail validation.

### Historical Route 3 - Qualitative Supplementary Baseline Approval

Ask the supervisor to approve the smaller unchanged supplementary model as a qualitative baseline if exact RF-U data cannot be obtained.

Evidence already available:

- original source/deck preserved and hash-matched;
- local compile/link/input/solver/ODB technical pass;
- reproducible RF-U extraction;
- peak and post-peak response documented;
- final crack path is connected and approximately horizontal;
- `SDV16` has no decreases;
- `SDV14`/`SDV15` overshoot is confined to final unstable propagation;
- `SDV15` decrease candidates are documented for follow-up rather than hidden.

Possible outcome labels:

```text
scientific_review_waived_exact_reference_unavailable
qualitative_baseline_approved
```

## Revised Recommendation

Follow the thesis proposal. Prepare a new paper-matched Molnar Mode-I
single-notch benchmark deck using the unchanged Molnar user subroutine, matching
the paper geometry, notch, material parameters, \(G_c\), length scale,
boundary conditions, displacement history, mesh resolution and \(h/l\), element
type, load increments, reaction-force extraction set, phase-field output, and
matched displacement states as closely as the paper permits.

Digitize the relevant published Molnar curve as an approximate paper reference
for that paper-matched reconstruction. Record the exact figure and curve label,
axes, units, digitization method, line/symbol uncertainty, published model
parameters, and matched displacement states. Do not use the digitized Fig. 7
curve as an exact validation target for the smaller supplementary deck.

Supervisor input is still needed for final acceptable tolerances or for any
intentional deviation from the proposal, but not for choosing whether to proceed
with the paper-matched benchmark route.

## Current Project Rule

Current active rule:

```text
Gate A3: reference_data_insufficient
Stage A: open
Baseline source/deck: frozen
Smaller supplementary deck: supporting technical reproducibility evidence
Next benchmark target: paper-matched Molnar Mode-I single-notch deck
New Abaqus run: not yet approved
MISESERI/remeshing: blocked
```
