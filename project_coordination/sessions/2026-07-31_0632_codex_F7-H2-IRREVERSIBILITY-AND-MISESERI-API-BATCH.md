# Session report: F7 H2 irreversibility and MISESERI API batch

Date: 2026-07-31  
Agent: codex  
Task: `F7-H2-IRREVERSIBILITY-AND-MISESERI-API-BATCH`

## Execution

- Starting main: `2ca77ea71af7d2ead7c3b6ef00bc8f44571abdc5`
- Preparation: `cac6974675d54ea354351e68647286b50856d432`
- Authorization: `7bc07551ba53e55e277f6c28264cc2c5a455428e`
- Submission/authority consumption: `c949346cd0ab77663aa12a610b87e0c687b8044e`
- Evidence and scientific records: `e6cdb62fbbea208621707ae27d693f38c37a8910`
- Immutable run: `F7_20260731_040750_cac6974`
- qsub attempts/successes/failures: `2/2/0`
- Direct qsub/retry/replacement/qdel/qmove: `0/0/0/0/0`

## Terminal results

`1380084.mmaster02` (`M2H2IRR1`) finished with PBS exit 12. The Abaqus
Python extraction completed. Across 102 frames, 1,120 fixed-point SDV15
decreases were found; the minimum was `-5.853176116943359e-4`, affecting 126
material points and 75 elements. The Python 3.11 report step then failed when
it cast the textual CSV step label `Step-1` to float. Scientific decision:
genuine local irreversibility failure; H2 is not accepted.

`1380085.mmaster02` (`M2RMAPI2`) finished with PBS exit 1. Exact source ODB
and deck hashes matched. The script reached `RemeshingRule`, which rejected
Unicode `variables[0]`. Solver count, native-remesh count and candidate-deck
count are zero. Decision: native MISESERI API remains unqualified.

Both final qstat records, tracejob outputs, logs, JSON summaries, raw forensic
tables and SHA-256 inventories were retained under the canonical F7 evidence
directory. No ODB, CAE database, or other binary database was committed.

Validation passed for the three Stage F7 contract tests, Python compilation,
and JSON parsing. The thesis master compiled successfully with TeX Live to a
36-page PDF; existing overfull/underfull box warnings remain nonfatal.

## Validation and authority

The two-job authority is consumed and terminal. No job is active and no HPC
execution is authorized. Pre-existing dirty and untracked paths outside the
claimed scope were preserved.
