# Decision Record: F26 CAE Geometry Build Qualification Decision

Protocol version: 1
Task ID: `F26-INVALIDATE-F25-AND-PREPARE-CAE-BUILD-QUALIFICATION`
Date: 2026-08-04
Agent: gemini-antigravity
Starting revision: `441d822a1c7c2bba8082157615b217798b0f3aec`

## 1. Executive Summary & F25 Invalidation

The F25 package contained critical fail-open defects:
1. `build_f25_geometry_backed_model.py` caught all exceptions and fell back to ordinary Python, merely prepending comment lines to the orphan-mesh source deck.
2. The fallback hardcoded geometry counts and model inventories.
3. `real_abaqus_cae_build=false` coexisted with `contract_pass=true`.
4. The committed generated input deck was not produced by `job.writeInput`.
5. The PBS wrapper fell back from Abaqus/CAE to `python3`.
6. The PBS wrapper did not validate `real_abaqus_cae_build` or parse the complete contract.
7. Abaqus module loading was fail-open (`|| true`).
8. Telegram JSON file writing was present without actual Telegram delivery.
9. The F25 preparation task used forbidden SSH/qstat even though no job was submitted.

**F25 Invalidation**:
- All F25 qualification claims are **invalidated**.
- Corrected F25 classification: `f25_m2rmprov1_package_invalid_no_submission_authorized`.

## 2. Real Builder — Fail Closed (`build_f26_geometry_backed_model.py`)

Repaired the model builder to run **only** under Abaqus/CAE (`abaqus cae noGUI=...`):
- Explicitly imports actual Abaqus modules: `from abaqus import mdb`, `from abaqusConstants import CPE4, STRUCTURED, ANALYSIS, OFF, ON, MISESERI, DEFAULT`, `import regionToolset`, `import mesh`.
- **No standalone-Python fallback**; **no broad exception catching**. Any import or build error exits with code 1.
- All audit values (`geometry_face_count`, `geometry_node_count`, `geometry_element_count`, material/section/set/BC/load/step names) are queried directly from the live `mdb` model objects.
- Uses actual Abaqus APIs: `mdb.ModelFromInputFile`, `Part2DGeomFrom2DMesh`, `SectionAssignment`, `mesh.ElemType`, `setElementType`, `setMeshControls`, `seedPart`, `generateMesh`, `rootAssembly.Instance`, `rootAssembly.regenerate`, `regionToolset.Region`, `RemeshingRule`, `mdb.Job`, `job.writeInput(consistencyChecking=OFF)`.

## 3. Preparation of M2RMBUILD1 Only

- **Purpose**: Run Abaqus/CAE `noGUI`, construct the real geometry-backed model, export `M2RMPROV1.inp`, retain construction evidence, stop before Abaqus/Standard.
- **Resource Request**: `queue: entry_imfdfkmq`, 1 CPU, 8 GB, 00:30:00 walltime.
- **Execution Counters** (`EXECUTION_COUNTERS.json`):
  - `cae_builder_calls = 1`
  - `standard_solver_calls = 0`
  - `adaptive_remesh_calls = 0`
  - `datacheck_calls = 0`
  - `state_transfer_calls = 0`
  - `refined_analysis_calls = 0`
  - `nested_qsub_calls = 0`
- **PBS Wrapper (`M2RMBUILD1.pbs`)**: Enforces absolute package/evidence paths, isolated `/scratch`, frozen hash check (`sha256sum -c F26_SHA256SUMS`), fail-closed module load (`module load abaqus/2023`), actual Telegram delivery, single `abaqus cae noGUI=...` invocation without `python3` fallback, zero Abaqus/Standard calls, and evidence collection.

## 4. Decision Gate Selection

- **Final Classification**: `f26_m2rmbuild1_clean_linux_qualified_not_authorized`
- **Prepared Job**: `M2RMBUILD1` (CAE build qualification only)
- **`M2RMPROV1` Solver Execution Prepared**: `false`
- **`M2RMEXEC2` Prepared**: `false`
- **Execution Authorized**: `false` (No submission; authority consumed = 0).
