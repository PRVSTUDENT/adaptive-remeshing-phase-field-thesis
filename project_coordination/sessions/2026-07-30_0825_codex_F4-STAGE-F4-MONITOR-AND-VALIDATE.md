# Session report: Stage F4 terminal failure closeout

Date: 2026-07-30
Agent: `codex`
Task: `F4-STAGE-F4-MONITOR-AND-VALIDATE`
Starting commit: `668694a041755612c18a3e78fd9900596ecf3ce5`

## Outcome

Both Stage F4 jobs are terminal pre-Abaqus infrastructure failures. Neither
solver started, neither ODB exists, and no scientific validation is possible.
Both jobs exited from the PBS Git ancestry guard after `git -C ... rev-parse
HEAD` returned `unknown` inside the compute job. The same repository was
readable from the login node at commit
`668694a041755612c18a3e78fd9900596ecf3ce5`, so the evidence supports a
compute-job Git availability/environment failure rather than a scientific
input failure.

| Job | Queue route | Host | PBS exit | Walltime | ABAQUS_RC | EXT_RC | VAL_RC | Classification |
|---|---|---|---:|---:|---:|---:|---:|---|
| `1379615.mmaster02` | `entry_imfdfkmq` -> `normal_imfdfkmq` | `mnode100/0` | 10 | 00:00:01 | unavailable | unavailable | unavailable | `stage_f4_h2_pre_abaqus_git_guard_fail` |
| `1379616.mmaster02` | `entry_imfdfkmq` -> `normal_imfdfkmq` | `mnode100/1` | 10 | 00:00:01 | unavailable | unavailable | unavailable | `stage_f4_miseseri_pre_abaqus_git_guard_fail` |

The MISESERI scratch deck SHA-256 is
`a927b8317ff9e20bfa84dd669a2577b095e69d1bf1c343b81b158a83fd075ea2`,
matching the required corrected-deck hash. This verifies staged input identity
only; it does not establish a technical or scientific pass.

`tracejob` no longer retained records for either ID when queried with one-day
and three-day windows. Complete retained `qstat -xf` accounting fields are
preserved in the evidence bundles.

## Boundaries

- M-102 recorded: true.
- qsub calls by Codex in this task: 0.
- retries: 0.
- replacements: 0.
- qdel/qmove calls: 0.
- Abaqus executions: 0.
- No authorization or execution-contract counters changed.
- Further execution requires new explicit human authorization.
