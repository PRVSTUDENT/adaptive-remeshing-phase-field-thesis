# F1495 preflight transport hardening
Starting commit c5c2cd366d577f99a13586b1331f545b3c7c69ed; all pre-existing dirty paths preserved.
User human invocation failed in remote base64 decode with Incorrect padding, before issuance. Intact original invocation could not reproduce on this environment, including WindowsPowerShell5.1. Exact corruption origin remains unestablished; do not claim padding repair alone is proof of root cause.

Canonical external issuer hardened: gzip source before base64 (previous source argument8644 characters), total remote command bounded to6000, strict base64 decode and SHA256 integrity assertion before exec. No blind padding, no insecure fallback. Optional omitted Command deterministically selects and prints the same exact approved batch-bound guarded command; supplied mismatches still rejected. Human approval mode remains human-only; VerifyOnly returns before issuing anything.

Validation: live route1 VerifyOnly under WindowsPowerShell5.1 PASS, actual package and login notification checks PASS, compute-node deliveryUNRESOLVED. Five tests PASS: active/duplicate/stale permit preservation, history preservation, new-permit archive, route-only/disabled queue refusal, compressed transport valid/truncated/hash-mismatch behavior. Tests operate on isolated fake state. Real state readback unchanged: original batchMODE1_PACKAGE48_DONOR inactive consumed1/max1. No route1 permit issued, no qsub attempted, no counters reset.

Next human command: & "$env:USERPROFILE\OpenClawPAD\Set-ControllerAuthorization.ps1" -BatchName MODE1_PACKAGE48_DONOR_ROUTE1 -MaxSubmissions 1
Expected actual preflight followed by AUTHORIZATION_RECORDED for ROUTE1. Controller then consumes that new permit exactly once and submits bound route command.
Issuer SHA256: 59E9A12EDCDCA5ADC65CCAD6C0144A96EA3EA490036BAAA63C03C69851F62D11
