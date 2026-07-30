# F5 H2 compiler/datacheck smoke execution

Date: 2026-07-30  
Starting main: `bc9cec0933433065d03bec00d8284c24cd5c48c1`

The smoke runtime was hardened to be self-contained and committed at
`e8a1d32210261745413c12bfe5e378f7fcc14498`. Offline tests and final alias
preflight passed. Immutable run `F5CMP_20260730_113544_e8a1d32` was staged
under Stage F5 scratch and passed file, hash, PBS syntax, datacheck-only,
no-qsub and no-Git audits.

One-job authority was activated and published at
`eb8d72080a12516a0c197611986fcf0b7699b59a`. Exactly one qsub returned job
`1379939.mmaster02`. Authority was immediately consumed and published at
`8b3dea5cd4990e6aebea4288b6a2f248418f6945`.

The job routed from `entry_imfdfkmq` to `normal_imfdfkmq` and remained queued.
The scheduler estimated start at 20:11:32 cluster time and reported a
placement/Qlist constraint while queued. No qmove, qdel, rerun, second qsub,
replacement or full analysis occurred.

Counters: qsub attempts 1; successful submissions 1; retries 0; replacements
0; full-analysis submissions 0. Terminal compiler/datacheck validation remains
pending read-only follow-up.
