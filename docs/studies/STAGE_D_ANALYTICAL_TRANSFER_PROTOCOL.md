# Stage D1 Analytical Transfer Protocol

Status: `stage_d1_local_harness_defined`

Purpose: verify transfer mechanics on tiny nonmatching meshes before any
fracture continuation or Abaqus restart.

## Test fields

The first controlled fields are:

```text
d(x,y) = 0.2 + 0.6 exp(-((x-x0)^2 + (y-y0)^2) / r^2)
```

and:

```text
H(x,y) = max(H_old(x,y), psi0(x,y))
```

where `d` is bounded by the physical phase-field convention and `H` is a
monotone history field. The harness reports raw values before any required
bounding and bounded values after applying physical guards.

## Required outputs

- nodal L2 and maximum error for `d`;
- integration-point L2 and maximum error for `H`;
- raw and bounded field ranges;
- `0 <= d <= 1`;
- `H_new >= H_old`;
- deterministic repeat check;
- unmapped node and integration-point counts;
- coverage fraction;
- energy before and after transfer;
- element/IP ordering check.

## Gate D1

`stage_d1_analytical_transfer_pass` requires:

- all target nodes and target integration points mapped;
- finite raw transferred values;
- bounded `d` in `[0, 1]`;
- monotone `H`;
- deterministic repeated transfer;
- element/IP ordering verified;
- L2, maximum-error, and energy-jump values reported.

No tolerance-only pass is claimed from hiding errors through clipping. Accuracy
metrics are recorded even when the guard checks pass.

