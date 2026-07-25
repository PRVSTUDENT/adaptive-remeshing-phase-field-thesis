# Current project state

Updated: 2026-07-25
Protocol version: 1
Classification: `stage_f_mode_ii_h0_datacheck_authorized`

## Git

| Item | Value |
|---|---|
| Authorization parent revision | `cddf916c8422f5f87152205f078e5e8f019e1afd` |
| F0 scientific freeze | `17240f646cf1e382396006ab635976fa22a67890` |
| Active agent | none after F1-J0-AUTH release |
| Active task | **F1-J0** ready_pending_submission_approval |

## Authorization boundary (critical)

```text
datacheck_authorized = true
datacheck_submissions_used = 0
maximum_datacheck_submissions = 1
solver_authorized = false
automatic_retry_authorized = false
submission_approved = false
maximum_jobs_now = 0
```

Exactly **one** F1-J0 Abaqus **datacheck** is authorized in the JSON record.
**Submission is not approved** until a separate explicit human message.
Do **not** run the submit wrapper, `qsub`, or Abaqus without that approval.

## Stage F package (unchanged)

- Package: `models/generated/mode_ii/h0_serial`
- Auth file: `runs/hpc/stage_f/mode_ii_h0/MODE_II_H0_AUTHORIZATION.json`
- Deck SHA-256: `32a25380767bbb0e9e76eb55b3bb7a97d78bb75c4f86c7e8585aa2032ce2d33b`
- Source SHA-256: `5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c`
- F1-P0 qualification: pass

## Next actions

1. **Wait for explicit F1-J0 submission approval**
2. On approval only: submit exactly one `mode_ii_h0_dc` (1 CPU, 16 GB, 00:30)
3. Valid job ID consumes authorization; failure consumes it with no retry
4. F1-J1 only after F1-J0 pass

## Dirty paths

Pre-existing local porcelain remains preserved; not cleaned.
