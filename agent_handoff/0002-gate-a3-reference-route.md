# Decision Note 0002 - Gate A3 Reference Route

Date: 2026-07-14

Status: supervisor decision pending

## Context

The unchanged Molnar supplementary `SingleNotch` benchmark has passed the local technical gate and has reproducible RF-U, phase-field, crack-path, bound, and irreversibility diagnostics. Gate A3 remains classified:

```text
reference_data_insufficient
```

The reason is scientific, not technical. The published Molnar and Gravouil Fig. 7 single-notch study uses a larger model of about 22,000 elements, while the supplied supplementary `SingleNotch` deck is the smaller model of about 4,000 physical elements. Material parameters and fracture toughness match, but length scale, element count, load-increment details, and the applicable Fig. 7 curve label remain unresolved.

## Routes

### Route 1 - Exact RF-U Reference

Acquire original RF-U coordinates from the authors, supplementary data, or another authoritative source.

Use when:

- the exact source data correspond to the smaller supplementary `SingleNotch` deck, or the mismatch is explicitly documented;
- units, axes, curve label, and uncertainty are known.

Outcome:

- populate `references/derived/molnar_gravouil_2017/single_notch/rf_u_reference.csv`;
- rerun `abaqus python scripts/validation/check_molnar_single_notch.py`;
- Gate A3 can be evaluated quantitatively.

### Route 2 - Approximate Fig. 7 Overlay

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

### Route 3 - Qualitative Supplementary Baseline Approval

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

## Recommendation

Attempt Route 1 first. If exact numerical RF-U data cannot be obtained in a reasonable time, prefer Route 3 for the thesis workflow and record the smaller supplementary model as a reproducible qualitative baseline. Use Route 2 only as a clearly labelled approximate literature overlay, not as an exact validation gate.

## Current Project Rule

Until one route is formally chosen:

```text
Gate A3: reference_data_insufficient
Stage A: open
Baseline source/deck: frozen
New Abaqus run: not required
MISESERI/remeshing: blocked
```
