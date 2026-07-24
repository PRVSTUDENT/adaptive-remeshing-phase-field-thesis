# WP6 ABAQUSER External Block Closure

## Question

Can the planned ABAQUSER mapping and comparison gate be completed with the
available TU Freiberg environment?

## Evidence

The D2D0 login-node audit searched the available executable path, module tree,
project source, documentation, and known installation locations. It found no
ABAQUSER executable, loadable module, source implementation, or documented
runnable interface. No D2D PBS or solver job was submitted.

Independent Abaqus/CAE and ODB extraction was used for state, reaction,
history, phase, and reconstructed-energy evidence. This route provides
traceable scientific output but is not represented as an ABAQUSER comparison.

## Decision

WP6 is closed as `externally_blocked`. The original numerical agreement gate
cannot be evaluated and is not replaced by an unsupported equivalence claim.

## Future access required

Reopening WP6 requires:

1. a documented ABAQUSER executable or source distribution;
2. the supported Abaqus/version interface and invocation syntax;
3. field/component/unit and integration-point ordering documentation;
4. a trivial mapping smoke test; and
5. comparison against the retained independent extraction.

The absence of the interface is reported as an implementation limitation and
does not authorize further HPC work.
