# Session F43MODEREF-H2-ENDPOINT-RESOLUTION-CLOSEOUT1

Collected scheduler, solver, ODB, identity, overlap, convergence, field-integrity, and cost evidence for `1388330.mmaster02`. The job terminated after Step 2 increment 1906 at `U1=0.009762500412762165 mm` due genuine Abaqus divergence (`FIXED TIME INCREMENT IS TOO LARGE`), not the 24-hour PBS limit. Old/new H2 overlap histories are exactly identical through `0.00925 mm`. H1/H2 common-window RF L2 is `0.535998817939661%` through `0.00963249988853931 mm`. No submission or retry was performed.

Primary report: `models/generated/mode_ii/reference_convergence/M2REF_H2_FRACFIX_ENDPOINT/evidence/1388330.mmaster02/H2_ENDPOINT_CLOSEOUT_REPORT.md`.

Limitations: direct fracture-energy history was unavailable; exact H1/H2 crack Hausdorff at the new common endpoint is not extractable because no H2 field frame exists there. The frozen `0.00925 mm` Hausdorff remains `0.005443 mm` and fails the `0.00375 mm` gate.
