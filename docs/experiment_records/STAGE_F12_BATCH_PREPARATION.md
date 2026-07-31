# Stage F12 batch preparation

Stage F12 prepares two automatic-increment minimal candidate analyses whose
only model-control difference is their increment tuple. Geometry, mesh,
mapping, physics, endpoint, output, diagnostics, residual, tangent, and
boundary conditions remain frozen from Stage F11. The bounded UEL call log
covers phase elements 1--2 and integration points 1--2 for at most 40 calls
per increment.

The CAE-only lane imports the official corrected 3,930-element MISESERI deck,
attaches the qualified Python 2 byte-string tuple rule to the real coarse
model, writes a coarse input where supported, and performs no solver,
datacheck, adaptive, or remesh execution.

The canonical H1 U1=0.020 population was independently confirmed as 12,064
physical elements. Instrumented baseline and penalty packages are prepared
with N_ELEM=12064 and mapped COMMON bounds guards. Both remain
`prepared_not_authorized`; no H1 datacheck or analysis is part of Stage F12.
