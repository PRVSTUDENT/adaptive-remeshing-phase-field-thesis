# Molnar Layered Deck Mapping

Date: 2026-07-16

Candidate: `paper_matched_candidate_v2`

This mapping follows the preserved Molnar supplementary `SingleNotch.inp` and `SingleNotch.for` conventions. The preserved source files are not modified.

| Layer | Role | Element type | ID range | Properties | State variables | Output role |
|---|---|---|---|---|---:|---|
| U1 | phase-field UEL | `U1` | `1..N` | `lc, Gc, thickness` | 8 | phase/history UEL state |
| U2 | displacement UEL | `U2` | `N+1..2N` | `E, nu, thickness, k` | 56 | mechanical UEL state |
| CPS4 | visualization/UMAT | `CPS4` | `2N+1..3N` | `UMAT k, nu` | 16 | ODB SDV visualization |

Candidate-v2 generated value:

```text
N = 33852 physical elements
layered elements = 101556
```

Property ordering:

- U1: `PROPS(1)=lc`, `PROPS(2)=Gc`, `PROPS(3)=thickness`
- U2: `PROPS(1)=E`, `PROPS(2)=nu`, `PROPS(3)=thickness`, `PROPS(4)=k`
- UMAT material constants: visualization residual stiffness and Poisson ratio

The static validator checks the declarations, property blocks, layer counts, element offsets, and visualization connectivity.
