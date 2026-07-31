# Stage F10 qualification decision

The corrected model-specific `N_ELEM=23` mapping is runtime-qualified for the
minimal pair and is not a constitutive change. Both analyses completed without
a COMMON-array bounds failure.

The penalty candidate reduces meaningful fixed-point healing below the
single-precision threshold and preserves RF--U response and convergence.
Nevertheless, its formal classification is
`irreversibility_candidate_inconclusive` because energy and explicit penalty
diagnostics were not captured. A later medium H1 verification is not
eligible from this result.

The native RemeshingRule variables type remains unresolved because the
CAE wrapper failed before the bounded type matrix.
