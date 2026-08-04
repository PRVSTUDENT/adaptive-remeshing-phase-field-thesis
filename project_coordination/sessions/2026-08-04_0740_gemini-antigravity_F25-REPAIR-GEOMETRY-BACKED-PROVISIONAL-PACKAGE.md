# Session Report: F25-REPAIR-GEOMETRY-BACKED-PROVISIONAL-PACKAGE

Protocol version: 1
Agent: gemini-antigravity
Date: 2026-08-04
Task ID: `F25-REPAIR-GEOMETRY-BACKED-PROVISIONAL-PACKAGE`
Starting commit: `f32a5b5ab4d3b019c56a3d44740619e6e39f55bb`

## 1. Accomplished Work

1. **Invalidation of F24 Claims**:
   - Recorded invalidation of F24 claims (`M2RMPROV1` geometry-backed status, input deck equivalence, authorization eligibility).
   - Invalidation evidence: `build_f24_geometry_backed_model.py` raw file copy defect; identical SHA-256 (`a927b831...`); `M2RMPROV1.pbs` directly executing `source_deck.inp`; missing notification and evidence contracts.
   - Corrected F24 classification: `f24_m2rmprov1_package_invalid_no_submission_authorized`.

2. **Real Abaqus/CAE Model Builder (`build_f25_geometry_backed_model.py`)**:
   - Replaced no-op builder with real Abaqus Python script importing `abaqus.mdb`, `abaqusConstants`, `regionToolset.Region`, `mesh.ElemType`.
   - Implemented 17-step construction sequence: `Part2DGeomFrom2DMesh`, `SectionAssignment`, `CPE4`, `STRUCTURED`, `seedPart`, `generateMesh`, `Instance`, `regenerate`, `Region(faces)`, `RemeshingRule`, `job.writeInput`.
   - Verified input hash inequality (`source_sha256: a927b831... != generated_sha256: 7e59929a...`).

3. **PBS & Notification Repair (`M2RMPROV1.pbs`)**:
   - Configured `queue: entry_imfdfkmq`, 1 CPU, 8 GB memory, 01:00:00 walltime.
   - Implemented isolated scratch workspace `/tmp/m2rmprov1_${PBS_JOBID}`.
   - Enforced frozen hash verification (`sha256sum -c F25_SHA256SUMS`).
   - Added explicit module loading (`module load abaqus/2023`).
   - Implemented Telegram START notification (`NOTIFICATION_START_TELEGRAM.json`) and terminal notification trap (`NOTIFICATION_TERMINAL_TELEGRAM.json`).
   - Enforced build audit `contract_pass = true` before Abaqus/Standard invocation.
   - Preserved DAT, MSG, STA, LOG evidence and return codes (`builder.returncode`, `solver.returncode`, `collector.returncode`, `first_failure.returncode`).

4. **Guarded Submission Orchestrator**:
   - Created `scripts/hpc/stage_f/submit_stage_f25_provisional_analysis.sh` with activation gate `F25_ACTIVATE_SUBMISSION` and authorization gate `F25_EXPLICIT_AUTHORIZATION`. Exactly 1 qsub call site.

5. **Testing & Validation**:
   - Created `scripts/validation/validate_f25_geometry_backed_provisional_package_repair.py` (passed with 0 failures).
   - Created `tests/stage_f/test_f25_geometry_backed_provisional_package_repair.py` (all 40 stage_f unit tests passed).
   - Passed `check_multi_agent_bootstrap.py`.

## 2. Evidence Artifacts Created

- `runs/hpc/stage_f/f25_geometry_backed_provisional_package_repair/F24_INVALIDATION_AUDIT.json`
- `runs/hpc/stage_f/f25_geometry_backed_provisional_package_repair/REAL_GEOMETRY_BUILDER_AUDIT.json`
- `runs/hpc/stage_f/f25_geometry_backed_provisional_package_repair/PBS_EXECUTION_CONTRACT.json`
- `runs/hpc/stage_f/f25_geometry_backed_provisional_package_repair/NOTIFICATION_CONTRACT.json`
- `runs/hpc/stage_f/f25_geometry_backed_provisional_package_repair/EVIDENCE_RETENTION_CONTRACT.json`
- `runs/hpc/stage_f/f25_geometry_backed_provisional_package_repair/F25_DECISION.json`
- `runs/hpc/stage_f/f25_geometry_backed_provisional_package_repair/NO_EXECUTION_AUDIT.json`
- `runs/hpc/stage_f/f25_geometry_backed_provisional_package_repair/PACKAGE_MANIFEST.json`
- `runs/hpc/stage_f/f25_geometry_backed_provisional_package_repair/F25_RUNTIME_MANIFEST.json`
- `runs/hpc/stage_f/f25_geometry_backed_provisional_package_repair/STATUS.json`
- `models/generated/mode_ii/f25_geometry_backed_provisional_package_repair/M2RMPROV1.inp`
- `models/generated/mode_ii/f25_geometry_backed_provisional_package_repair/M2RMPROV1.pbs`
- `models/generated/mode_ii/f25_geometry_backed_provisional_package_repair/GEOMETRY_BACKED_MODEL_AUDIT.json`
- `models/generated/mode_ii/f25_geometry_backed_provisional_package_repair/F25_CLEAN_LINUX_QUALIFICATION.json`
- `models/generated/mode_ii/f25_geometry_backed_provisional_package_repair/F25_NO_EXECUTION_AUDIT.json`
- `scripts/hpc/stage_f/submit_stage_f25_provisional_analysis.sh`
- `docs/decisions/F25_M2RMPROV1_PACKAGE_REPAIR_DECISION.md`
- `docs/experiment_records/STAGE_F25_GEOMETRY_BACKED_PROVISIONAL_PACKAGE_REPAIR.md`
- `scripts/validation/validate_f25_geometry_backed_provisional_package_repair.py`
- `tests/stage_f/test_f25_geometry_backed_provisional_package_repair.py`

## 3. Boundary Audit

- `execution_authorized`: false
- `submission_approved`: false
- `m2rmexec2_prepared`: false
- `approved_submissions_now`: 0
- `maximum_jobs_now`: 0
- `qsub_attempts`: 0
- `successful_submissions`: 0
