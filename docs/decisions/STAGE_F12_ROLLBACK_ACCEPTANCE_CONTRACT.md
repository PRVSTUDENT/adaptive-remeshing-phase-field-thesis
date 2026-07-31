# Stage F12 rollback acceptance contract

The rollback test requires a genuine Abaqus cutback identified jointly by a
reduced repeated increment attempt and Abaqus text evidence. State restoration
is assessed directly from bounded UEL-call evidence, not inferred from final
response agreement.

The phase restoration tolerance is `1e-12`; fixed-point phase monotonicity
retains the Stage F11 `1e-7` policy. The cutback/reference RF--U maximum
absolute difference limit is `1e-5`, the final phase-field maximum absolute
difference limit is `1e-5`, and diagnostic-energy imbalance retains the F11
two-percent-of-maximum-work policy. Failure to trigger a cutback is
`penalty_rollback_not_exercised` and does not authorize a retry.
