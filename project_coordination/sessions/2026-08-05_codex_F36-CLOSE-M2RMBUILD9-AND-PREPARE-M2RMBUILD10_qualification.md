# F36 qualification and closeout

Preparation package: `b17b9af263c12e124ae4f39288150fd4ce2f44a5`.

Detached Linux qualification used `/tmp/f36-qual-venv/bin/python` (Python
3.12.3, pytest 8.4.1). The original pytest version was not recoverable; the
explicitly pinned replacement environment was used. All required checks
passed: clean checkout, both six-file SHA-256 manifests, PBS and guarded
wrapper syntax, Python compilation, 12/12 tests, static validator, diff
check, F34 identity, LF checks, and prohibited-token/API scans.

F34 byte preservation is zero modified, added, deleted, and hash-mismatched
files relative to `aa4d18100d9b3bd8f0d8585d02f063a52a825fe1`. M2RMBUILD9
(`1384122.mmaster02`) is terminal failed with CAE return code 1, skipped
validators, no scientific result, and consumed authorization.

M2RMBUILD10 is qualified but unsubmitted. No HPC, scheduler, Abaqus, solver,
datacheck, remeshing, state-transfer, or downstream action occurred.
