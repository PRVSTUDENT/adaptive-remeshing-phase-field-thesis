# Msekh et al. (2015)

Source file: `Literature review/1-s2.0-S0927025614004133-main.pdf`

## Thesis Role

Alternative Abaqus implementation for brittle fracture phase-field modeling using UEL and UMAT. Use mainly for variational formulation, residual/tangent structure, monolithic Newton solution, and visualization architecture.

## Extract Before Implementation

- Energy functional, degradation law, and crack-density regularization.
- Monolithic residual and tangent terms.
- UEL/UMAT data flow for visualization.
- Benchmark definitions that overlap with Molnar or Pandey-Kumar.
- Differences from Molnar that must not be silently mixed.

## Starter Decisions

- Use as a formulation and architecture reference, not the first reproduction target.
- Any monolithic/staggered comparison must be documented as a separate decision.

## Open Extraction Items

- Variable naming and state-variable layout.
- Benchmark overlap with the planned Mode I and Mode II/L-panel sequence.
