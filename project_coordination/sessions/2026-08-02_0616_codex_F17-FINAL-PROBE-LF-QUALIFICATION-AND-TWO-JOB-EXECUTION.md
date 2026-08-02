# F17 final probe-LF qualification and conditional execution

- Agent: codex
- Starting commit: `f676b09ad82f9e7dcec3f709ddf0a341b5fc935b`
- Classification: `f17_probe_lf_repair_blocked_declared_manifest_hash_mismatch`

The exact LF trial passed its byte contract: 2,242 to 2,243 bytes, final byte
48 to 10, and PBS SHA-256 `1d233a82...` to `10451ed7...`. Updating only that
entry yielded `F17_SHA256SUMS` SHA-256 `e304820b...` and `SHA256SUMS` SHA-256
`bde9ba48...`; neither matched the hashes declared in the authorization.

The trial package edits were restored. No repair, authorization, submission,
or evidence-execution commit was created. No cluster or scheduler command was
run; qsub attempts and job IDs are zero/none. Unrelated dirty paths were
preserved. Exact next action: issue corrected checksum-file hashes and fresh
conditional authority based on current main.
