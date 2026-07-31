# Stage F8 candidate source line-by-line difference

Baseline SHA-256:
`49c9054ab5faec9e069e0a9149af5058e6f1e11ab164c2a0e318f60282309b37`

Candidate SHA-256:
`ea3aeb972f1adb8f000a508afb1c7da5a34aa5fec125fb1487c1f81c23e56989`

Only the following executable additions exist:

1. Declare `PHASEOLD`, `PENALTY`, and `GAP` as `REAL*8`.
2. Immediately after loading U1 integration-point `SVARS`, save
   `PHASEOLD=SDV(1)`.
3. After the original phase residual and tangent assembly, set
   `PENALTY=1.0D6*GCPAR/CLPAR` and `GAP=PHASE-PHASEOLD`.
4. When `GAP < 0`, add `PENALTY*N_i*N_j` to the phase tangent and
   `PENALTY*GAP*N_i` to the phase residual, with the same integration weight,
   determinant and thickness factors as the original local term.

No displacement equation, material law, history update, output transfer,
parameter, COMMON layout, element count, or solver interface changed.

