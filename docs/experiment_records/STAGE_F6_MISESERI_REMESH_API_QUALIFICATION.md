# Stage F6 native MISESERI remeshing API qualification

Date: 2026-07-30

Task: `F6-H2-FULL-AND-MISESERI-REMESH-API-BATCH`

Job: `1379967.mmaster02` (`M2RMAPI1`)

Classification: `abaqus_cae_start_failure`

The independent CAE-only qualification job was submitted once by the guarded
F6 batch orchestrator. PBS routed it to `normal_imfdfkmq` on `mnode105/1`.
The request was one CPU, 8 GB and one hour. It terminated after six seconds
with PBS exit 10, CPU time one second and memory 188,244 kB.

All immutable runtime hashes passed before Abaqus. Abaqus/CAE 2023 started far
enough to check out a CAE license, then its Python 2.7 driver invoked the
qualification script with CAE driver arguments in `sys.argv`. Strict required
argument parsing rejected `-cae`, `-noGUI`, `-lmlog` and `-tmpdir`, producing
script exit 2. Consequently:

- source ODB hash verification inside the CAE script was not reached;
- source deck hash verification inside the CAE script was not reached;
- the installed `RemeshingRule` interface was not queried;
- no rule object was created;
- native remesh executions: 0;
- solver executions: 0;
- candidate refined decks: 0.

The login/orchestrator preflight had independently verified the official
source ODB SHA-256 as
`bfcdbec08669774a9f80939d67c9c86ffe7df707e760450b08b1f6073fc588ac`.
That preflight fact does not replace the unexecuted CAE API qualification.

The failure is preserved as M-104. The repository script is corrected for
future prevention to use explicit environment variables and tolerate Abaqus
driver arguments, but this consumed job is not retried. Canonical evidence:
`runs/hpc/stage_f/f6_h2_full_and_miseseri_remesh_api_batch/evidence/1379967.mmaster02/`.
