# D2D0 ABAQUSER Availability and Interface Report

Classification: `stage_d2d_blocked_abaquser_not_found`

Date: 2026-07-22

Scope: login-node audit only. No PBS job was submitted.

## Result

ABAQUSER is not currently available as an executable, module, source file, or
documented interface in the inspected environment. D2D output-route verification
is therefore externally blocked. D1, D2A, D2B, and D2C remain valid controlled
state-transfer evidence.

## Audit Commands

| Check | Result |
| --- | --- |
| `command -v abaquser` | no executable found |
| `command -v ABAQUSER` | no executable found |
| `module spider abaquser` | Lmod reports unable to find `abaquser` |
| `module avail` filtered for `abaquser`, `imfd`, `post` | no matching module reported |
| filesystem search under `$HOME/projects`, `$HOME/bin`, `$HOME/.local` | only the repository placeholder `scripts/hpc/stage_d2/04_d2d_abaquser_verification.pbs` matched |
| repository text search | planning notes and README placeholders only; no runnable interface |

## Missing Interface Information

| Required item | Status |
| --- | --- |
| executable/source path | missing |
| version or source commit | missing |
| required modules | missing |
| command syntax | missing |
| accepted input format | missing |
| output format | missing |
| element/IP identification method | missing |
| access or license restrictions | unknown |

## Decision

Do not substitute a normal Abaqus Python extractor and call it ABAQUSER
verification. D2D can resume only after the real ABAQUSER executable or source
and its interface contract are provided.
