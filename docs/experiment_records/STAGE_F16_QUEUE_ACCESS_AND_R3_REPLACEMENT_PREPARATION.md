# Stage F16 routed-queue R3 replacement preparation

Classification: `f16_r3_replacement_batch_prepared_not_authorized`

Read-only queue audit selected `entry_imfdfkmq` as the submission route and
`normal_imfdfkmq` as the routed execution destination. Both rollback packages
retain source SHA `8d30f10b8c668b9b1e256aeb389e9cf53e38d03fec4e1650bf1e30d975da133a`
and deck SHA `a84df34a2bdbfbd55d7f2642082710f1d410cd8480637f9da9aa47c107beed3b`.
The CAE-only package retains source-deck SHA
`a927b8317ff9e20bfa84dd669a2577b095e69d1bf1c343b81b158a83fd075ea2`.
Telegram remains required and PBS email remains best-effort/unconfirmed.

The future guarded order is control, forced, adaptive-region, with the third
lane held by `afterany:<M2IRRROLLCTL3_PBS_ID>` solely to preserve at most two
running project jobs. No qsub, solver, CAE, datacheck, or remesh call occurred.
