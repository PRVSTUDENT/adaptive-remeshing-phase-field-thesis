# Stage F4 replacement runtime-bundle session

Task: `F4-COMPUTE-NODE-RUNTIME-BUNDLE-REPAIR-AND-REPLACEMENT`
Agent: `codex`
Date: 2026-07-30
Starting commit: `f72514bf515d4d5abb0a0729de4c6a8e7e64bb3c`

## Published revisions

- Failure evidence: `f72514bf515d4d5abb0a0729de4c6a8e7e64bb3c`
- Runtime repair: `86ec6c795b5256f6932981fd8fbd16a001cc841e`
- Corrected runtime contract: `e0a453b`
- Explicit authorization: `f53d5c6bc34c1b1d7b87ea2ed0b9859db2d959d4`
- Offline validator repair: `f4d4ef1`
- Submission and evidence: `848cb85181fa77cc016210819eeeb93bd9a43d57`

## Qualification

- Direct H2 and MISESERI static validators: pass.
- Unit tests: 263 passed.
- Bash syntax and bootstrap validation: pass.
- Cluster runtime-bundle preflight: pass with zero qsub calls.
- Compute PBS scripts contain no Git or login-checkout dependency.

## Submission

Run ID: `F4R1_20260730_065138_86ec6c79`

The single orchestrator made exactly two qsub attempts. Both succeeded:

| Job | ID | Queue route | Result |
|---|---|---|---|
| `M2H2U20R1` | `1379892.mmaster02` | `entry_imfdfkmq` -> `normal_imfdfkmq` | Abaqus rc 1; compile environment failure (`ifort` unavailable) |
| `M2MISER1` | `1379893.mmaster02` | `entry_imfdfkmq` -> `normal_imfdfkmq` | Abaqus/exporter 0/0; original PBS validator rc 1 |

Authorization was consumed after the two attempts. There were no retries,
manual qsub calls, qdel calls, or qmove calls.

## MISESERI repaired offline validation

The original PBS ODB was preserved. An isolated offline Abaqus-Python
extraction and Python 3 validator run passed as
`official_corrected_pbs_validation_pass`, while preserving the original PBS
codes `ABAQUS_RC=0`, `EXT_RC=0`, `VAL_RC=1`.

- Final U1: `0.0010000000474974513 mm`
- Final RF1: `0.046069372445344925`
- Rows/elements: `3930`
- MISESERI min/max/mean: `6.865544128231704e-05` /
  `0.18701137602329254` / `0.001633144879951595`
- All values finite: true
- Positive MISESERI present: true
- Required `MISESERI`, `MISESAVG`, `S`, `E`, `EVOL`, `U`, `RF`: present
- True slit topology: retained
- ODB SHA-256:
  `bfcdbec08669774a9f80939d67c9c86ffe7df707e760450b08b1f6073fc588ac`

H2 scientific metrics and H1-H2 nonlinear comparison remain unavailable
because no H2 ODB was created. No further execution is authorized.
