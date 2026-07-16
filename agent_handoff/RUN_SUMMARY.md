# Molnar v2 SDV15 Targeted Diagnostic Run Summary

Status: `finished_technical_fail`

Classification: `molnar_v2_sdv15_diagnostic_technical_fail`

Job `1375020.mmaster02` was submitted exactly once on 2026-07-16 at
`12:21:59+0200` from revision
`efd5f60ebb9cc6ea8ce89b508a6e9df4183e5611`.

PBS accepted the notification settings:

- `Mail_Users = pr21vyci@mailserver.tu-freiberg.de`
- `Mail_Points = abe`

The scheduler finished the job with `Exit_status = 3` after about one second on
`mnode098/0`. Abaqus did not launch. The PBS output records:

```text
/var/spool/pbs/mom_priv/jobs/1375020.mmaster02.SC: Zeile 40: git: Kommando nicht gefunden.
revision_mismatch current= requested=efd5f60ebb9cc6ea8ce89b508a6e9df4183e5611
```

This is a pre-solver batch-environment failure caused by `git` being unavailable
inside the PBS job PATH at the revision guard. It is not a diagnostic model
failure, not an Abaqus solver failure, and not a scientific SDV15 result.

No retry or second diagnostic run is authorized.

Evidence:

- `evidence/1375020.mmaster02/qstat_xf_1375020_final.txt`
- `evidence/1375020.mmaster02/molnar_v2_sdv15_diag.o1375020`
- `evidence/1375020.mmaster02/run_environment.txt`
- `evidence/1375020.mmaster02/technical_classification.txt`
