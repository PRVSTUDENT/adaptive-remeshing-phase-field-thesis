# Stage F10 qualification batch preparation

The corrected minimal pair uses compact runtime-compatible populations:
phase UEL `1..23`, displacement UEL `24..46`, and visualization CPE4
`47..69`. Both UEL and UMAT use model-specific `N_ELEM=23`. Identical
fail-safe guards validate phase, displacement, visualization, and integration
point indices before the corresponding `USRVAR` branch can execute.

Changing `N_ELEM` is a reduced-model mapping adaptation, not a constitutive or
fracture-model change. Geometry, connectivity, material properties, loading,
steps, increments, outputs, and decks are byte-identical between baseline and
candidate. The frozen H2 source is unchanged.

The candidate reads `PHASEOLD` from incoming UEL `SVARS` before overwriting
the current trial state. The preflight records Abaqus beginning-of-increment,
accepted-increment commit, and cutback rollback semantics. The active penalty
residual and tangent pass a centered finite-difference directional derivative
test.

The remeshing replacement uses `no_solver_audit.py` consistently in the PBS
script and runtime contract. The submission orchestrator counts attempts and
outcomes in the parent shell and limits simultaneous execution to two by
holding the third job behind an `afterany` scheduler dependency.

All 18 Stage F8/F9/F10 targeted tests pass. Abaqus Python compatibility,
shell syntax, package hashes, static validators, and bootstrap validation are
required before authorization activation.
