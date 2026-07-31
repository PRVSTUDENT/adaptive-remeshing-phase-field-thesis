# Stage F10 corrected minimal penalty candidate

Job `1380092.mmaster02` completed with no COMMON-array failure or cutback.
The prior-converged-state and residual/tangent finite-difference gates passed
before submission. Initial stiffness and peak force match the baseline; the
largest RF1 difference is 1.81345967575908e-07, or 5.22573221662402e-06 of
the common peak.

The minimum fixed-point phase change is `-5.96046447753906e-08`. Under the
declared single-precision `1e-7` policy there are no meaningful decreases,
and SDV16 is monotone. The solve used 100 increments, 121 total iterations,
and zero cutbacks.

Classification: `irreversibility_candidate_inconclusive`. The result
strongly supports suppression of healing, but the invalid energy-output
request and absent penalty-activation histories leave mandatory acceptance
criteria unmeasured. It is therefore not yet eligible for medium H1.
