# Final Thesis Tolerance Policy

Status: `supervisor_review_required`

This record consolidates the numerical gates actually used in the thesis. It
does not convert provisional values into supervisor-approved values. Final
acceptance requires explicit supervisor review.

| Quantity | Working final policy | Status and scope |
|---|---:|---|
| RF--U curve comparison | Report NRMSE over the matched displacement interval; no unconditional global pass threshold adopted | provisional, comparison metric only |
| Peak-force error | Report relative error; Stage C scoped acceptance uses the committed Stage C decision rather than a new threshold | conditionally supported |
| State-transfer SDV15/phase error | maximum absolute error \(\le 10^{-8}\) where exact retention is required | accepted operational gate |
| State-transfer SDV16/history error | maximum absolute error \(\le 10^{-8}\) | accepted operational gate |
| Irreversibility/lower-bound violation | none beyond \(10^{-10}\) phase tolerance; history decreases none beyond extraction precision | accepted operational gate |
| Free KKT residual infinity norm | \(\le 10^{-8}\) | accepted operational gate |
| Minimum active multiplier | \(\ge -10^{-8}\) | accepted operational gate |
| Active-bound error | \(\le 10^{-10}\) | accepted operational gate |
| Mechanical RF discontinuity | relative jump \(\le 1\%\) | accepted bounded-checkpoint gate |
| Reconstructed-energy discontinuity | relative jump \(\le 1\%\) | accepted bounded-checkpoint gate |
| Crack-path comparison | report threshold, connectedness, horizontal deviation, and matched state; no single scalar pass threshold approved | provisional; post-peak equivalence withheld |

Until reviewed, the thesis must distinguish operational gates from
supervisor-approved universal tolerances. No new computation is authorized by
this policy.
