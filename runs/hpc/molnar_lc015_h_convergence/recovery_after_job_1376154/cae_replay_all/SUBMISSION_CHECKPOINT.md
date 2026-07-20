# Consolidated CAE-Only Replay Submission Checkpoint

Status: `completed_cae_all_pass`

## Authorization

```text
Abaqus/Standard solves: 0
CAE-only PBS submissions: 1 of 1 (consumed)
Automatic retry: not authorized
Solver reruns: not authorized
```

## Job

| Field | Value |
|---|---|
| Job ID | `1376236.mmaster02` |
| Job name | `molnar_hconv_cae_all` |
| Initial state | Q |
| Queue | `normal_imfdfkmq` (via `entry_imfdfkmq`) |
| select | `1:ncpus=1:mem=32gb` |
| walltime | `04:00:00` |
| Mail_Users | `pr21vyci@mailserver.tu-freiberg.de` |
| Mail_Points | `abe` |
| Submission revision | `bd09bc4f33a1415bba70769458d5bbbf218e1592` |
| Submission time | `20260720T173217+0200` |
| Prestage | `/scratch/pr21vyci/adaptive-remeshing/prestage/molnar_hconv_cae_all_20260720T173217+0200_bd09bc4f33a1` |
| PBS output | `/scratch/pr21vyci/adaptive-remeshing/pbs_output/molnar_hconv_cae_all_20260720T173217+0200_bd09bc4f33a1/molnar_hconv_cae_all.out` |

## Eligible cases (exactly three)

| Case | Solver job | ODB size | ODB SHA-256 |
|---|---|---:|---|
| H0 | 1376154.mmaster02 | 88827548 | `01601effd2a110dc7124356cb3d9baf6d772d55f4fb344414ad219ba9b78e07b` |
| H1 | 1376185.mmaster02 | 244467576 | `4898164c4205b0fb957e68cdefc0eba43bdb2fcf74175b6211ae09391131b6c3` |
| H2-PUB | 1376186.mmaster02 | 660842080 | `9c3755b3359a6aa61f4de8a8358bffd489da8cbd2ac45ba4f9c8c9f2922fa825` |

All three: Abaqus technical pass, ODB present, valid CAE package absent.

## Runtime contract

- Paths via `MOLNAR_CASE_ID`, `MOLNAR_ODB_PATH`, `MOLNAR_OUTPUT_DIR` only
- Sequential H0 → H1 → H2-PUB
- One case failure must not block remaining cases
- ODBs read-only; no Standard solve

## Completion (job already finished)

| Field | Value |
|---|---|
| Exit_status | `0` |
| Walltime | `00:00:12` |
| Overall class | `molnar_hconv_cae_all_pass` |
| Host | `mnode103` |

| Case | CAE classification | peak RF2 [kN] | U2 at peak [mm] | RF2-U2 CSV |
|---|---|---:|---:|---|
| H0 | `CAE replay pass` | 0.7276 | 0.00610 | yes (origin included) |
| H1 | `CAE replay pass` | 0.6996 | 0.00580 | yes (origin included) |
| H2-PUB | `CAE replay pass` | 0.6963 | 0.00580 | yes (origin included) |

Image/contour PNG export warned for all cases (viewport API); RF2–U2 packages are present.  
Evidence: `.../cae_replay_all/evidence/1376236.mmaster02/`  

Do not submit a second consolidated replay without a new decision.  
Scientific h-convergence analysis may now use the RF2–U2 CSVs.
