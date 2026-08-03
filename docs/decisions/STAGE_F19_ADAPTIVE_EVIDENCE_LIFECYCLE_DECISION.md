# Stage F19 adaptive evidence-lifecycle decision

F19 writes executable outputs only to `$WORK_ROOT/generated_evidence` and stages every available lightweight artifact to the final evidence directory after each command. Compatibility and CAE stdout, stderr, and return codes are distinct. The collector parses available JSON, inventories partial outputs, and writes a machine-readable missing-file report.

Exit priority is environment contract, compatibility helper, CAE, missing evidence, manifest validation, then success. A later manifest check cannot replace the first true command failure. The source ODB remains frozen at SHA-256 `bfcdbec08669774a9f80939d67c9c86ffe7df707e760450b08b1f6073fc588ac`. Solver, datacheck, AdaptivityProcess, `model.adaptiveRemesh`, native remesh, candidate, and refined-execution counters must remain zero.
