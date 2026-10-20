# F1597 trace technical qualification

A separate logging-only diagnostic was qualified and submitted once as PBS 1415522.mmaster02, through Invoke-Mode1Execution.ps1. No autonomous loop has started. Existing KKT and mechanical/history diagnostics remain completed and protected.

- Exact input 58B1E69F40C5A65C7B9F1049E42AD745152AB8B5CF6B0F15547ED3276CD54964.
- Exact offset table 87C7954EFEF0134094BBFB03D7ADA03D66F9A84281D0BB50F524AE88DFC65ADD.
- Instrumented source D8A56A216F17D148925DDFBE85F862350DA6145B5AA6AE1E9E1CD5EF9A9C9BAD; logging removal restores parent EF92ED58 exactly.
- Abaqus/Standard 2023 compiled, linked and completed datacheck. Captured interactive console is the actual log; no second datacheck was run to repair the collection-path assumption.
- 39 local execution/source/trace/parity regression checks pass.
- Real login-node notification and scheduler checks passed; source-bound preflight retained in NOTIFICATION_PREFLIGHT.json. Compute-node delivery still UNRESOLVED pending actual job evidence.
- Resources: one serial CPU, 16 GB, four-hour upper bound, one maximum submission, automatic_retry=false.
- Predeclared all-sample RF and accepted-increment energy parity against preserved job 1415199, rtol 1e-8, force atol 1e-12 kN and energy atol 1e-14 kNmm. No new baseline solve.

Terminal outcome, solver parity and controller readiness are not claimed until verified.
