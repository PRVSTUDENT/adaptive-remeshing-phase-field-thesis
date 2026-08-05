# Stage F33 M2RMBUILD8 offline repair

- Task: `F33-M2RMBUILD8-OFFLINE-REPAIR`
- Predecessor: `1383537.mmaster02` / `M2RMBUILD7`
- Predecessor classification: `cae_geometry_build_contract_failed`
- Replacement: `M2RMBUILD8`
- Package: `models/generated/mode_ii/f33_cae_runtime_gate_repair/`
- Execution: not run; no submission authorized

Repairs remove unsupported `UNPLANNED`, use the minimal constant set `ON`, `CPE4`, `STANDARD`, `STRUCTURED`, select verified `python3` for standalone helpers, capture actual return codes outside `set -e`, and mark unexecuted commands `skipped`.

Offline WSL validation: unit tests 10/10 passed; static validator passed; PBS and orchestrator shell syntax passed; both six-file package manifests passed. A detached clean-Linux checkout at `a6c4f4377b7fc04fab7a5311de4ffaeeb32c40d7` repeated every check successfully without scheduler access or submission.

Classification: `f33_m2rmbuild8_clean_linux_qualified_not_authorized`. Any replacement requires separate explicit authorization for at most one submission with automatic retry false.
