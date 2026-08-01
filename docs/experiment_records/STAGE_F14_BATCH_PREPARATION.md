# Stage F14 batch preparation

Two independent qualification lanes are prepared. `M2RTLOAD1` is a benign
one-step 23-element runtime smoke with documented Abaqus log routing and a
pre-analysis undefined-symbol audit. `M2RMREG1` is a CAE-only inspection of
the official coarse deck and ODB; it creates a RemeshingRule but never invokes
adaptiveRemesh, submit, datacheck, or analysis.

The authorization record remains disabled until both independent preflights
are recorded and the authorization commit is published.
