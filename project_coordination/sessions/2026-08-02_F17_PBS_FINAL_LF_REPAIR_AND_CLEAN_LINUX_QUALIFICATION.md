# F17 PBS final-LF repair and clean-Linux qualification

- Agent: codex
- Started: 2026-08-02T04:47:55Z
- Ended: 2026-08-02T05:01:25Z
- Starting commit: `48a89b7ce4ff1f414d2167949e1d17cd5dc071b1`
- Preparation commit: `a44c2b6651bd541bfc3bbe82479a2474af743c6c`
- Classification: `f17_clean_linux_manifest_reproducibility_failed_additional_missing_final_lf`

The authorized edit appended exactly one LF byte to `M2RMREG4.pbs`. Its
size is 1,167 bytes, final byte is 10, and SHA-256 is `6375b8c5...`.

The first fresh WSL2 Linux checkout was initially clean. Validation passed
all 11 adaptive-region entries and then stopped on frozen
`M2IRRPENACT1.pbs`: missing final LF, 2,242 bytes, final byte 48, SHA-256
`1d233a82...`. A second checkout existed at the preparation SHA but was not
validated after the fail-closed result.

No scheduler or scientific command was invoked. Execution authorization and
submission approval remain false, and all submission counters are zero.
