# Stage F17 Linux manifest repair decision

The ten failures were checkout-byte failures, not scientific changes. Git on
Windows used `core.autocrlf=true`; the original manifests recorded CRLF
working-tree bytes. Git blobs and clean Linux checkouts contain LF bytes. All
user-frozen scientific and runtime hashes already matched on Linux.

The repair changes only the two `F17_SHA256SUMS` files to describe canonical
committed/Linux bytes and adds explicit allowlists plus deterministic tooling.
No `.gitattributes` change is needed because the committed blobs are already
UTF-8, BOM-free, LF-terminated bytes and the qualification target is a clean
Linux checkout. The generator rejects CR bytes, BOMs, missing final LF,
duplicate/missing entries, and self-hashing.

The invalidated execution authorization remains invalid. This is a new
preparation only; all execution counters remain zero.

## Final-LF supersession

The user subsequently permitted exactly one appended LF byte to
`M2RMREG4.pbs`. The old 1,166-byte hash
`4c8088c6d113d5387b8728a25f1aeb886b1cbdf24a7b5f334d57e0569ee12705`
is superseded by the 1,167-byte canonical hash
`6375b8c5b739133046c8c402e9155a247ba1cb0512c305bffb22560de1a31cdf`.
No semantic PBS content changed. Execution remains unauthorized pending a
passing clean-Linux proof and fresh human authorization.

### Final-LF qualification result

Preparation `a44c2b6` contains the authorized one-byte `M2RMREG4.pbs`
repair. Clean Linux validation passed the 11-entry adaptive manifest, then
failed closed because `M2IRRPENACT1.pbs` also lacks a final LF. That frozen
file was outside scope; the second proof and all execution were stopped.

### Final qualification

Preparation `b4d9fad` repaired only adaptive legacy `SHA256SUMS`. The second
Linux proof passed all four manifests and blob comparisons. The batch is
Linux-qualified but not execution-authorized.
