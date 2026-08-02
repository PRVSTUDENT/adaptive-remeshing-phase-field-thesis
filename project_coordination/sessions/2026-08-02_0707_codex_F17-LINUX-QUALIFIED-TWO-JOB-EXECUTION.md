# F17 Linux-qualified two-job execution

- Starting commit: `fc6436ed4f7ba8b38515ccfd17338cc5d523cad7`
- Authorization commit: `0e8e50187c0b020dc681091ef0c7f179d30a5a19`
- Jobs: `1381483.mmaster02`, `1381484.mmaster02`

Cluster preflight passed from a clean detached worktree at the authorization
commit. All four manifests and both PBS hashes matched. The guarded
orchestrator made exactly two qsub calls; both returned zero. At the immediate
post-submission observation the probe was running and adaptive-region job was
queued in `normal_imfdfkmq`. Authority was consumed immediately. Retries,
replacements, direct qsub, qdel, and qmove are zero.
