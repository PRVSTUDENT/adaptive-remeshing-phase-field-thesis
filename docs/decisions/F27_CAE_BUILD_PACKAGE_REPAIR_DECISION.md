# Decision Record: F27 CAE Build Package Repair Decision

Protocol version: 1
Task ID: `F27-INVALIDATE-F26-AND-REPAIR-CAE-BUILD-PACKAGE`
Date: 2026-08-04
Agent: gemini-antigravity
Starting revision: `32c3f1f6df35e3fa7a8bb7605b2fe893ce4932a0`

## 1. Executive Summary & F26 Invalidation

The F26 `M2RMBUILD1` qualification package contained known defects:
1. `STANDARD` was used in `mesh.ElemType` without import.
2. `RemeshingRule` used `errorIndicator=MISESERI` instead of `variables=('MISESERI',)`.
3. `PartInstance.suppress()` was called instead of an Assembly feature operation.
4. Active geometry instance was named `Part-1-1-GEOM` rather than preserving `Part-1-1`.
5. Model entities (sets, BCs, equations) were inventoried but not explicitly rebound.
6. Telegram configuration loading and HTTP response validation were fail-open.
7. Terminal trap installation occurred after hash/module checks.
8. Audit file parsing was absent in PBS (checked only file existence).
9. Orchestrator was not bound to an exact preparation SHA.

**F26 Invalidation**:
- All F26 qualification claims are **invalidated**.
- Corrected F26 classification: `f26_m2rmbuild1_package_invalid_no_submission_authorized`.

## 2. Abaqus API & Model Rebinding Corrections

1. **RemeshingRule Constructor**:
   ```python
   m.RemeshingRule(
       name=rule_name,
       stepName='Step-1',
       variables=('MISESERI',),
       region=remesh_region,
       sizingMethod=DEFAULT
   )
   ```
2. **Explicit Symbolic Constants**: `CPE4`, `STANDARD`, `STRUCTURED`, `ANALYSIS`, `OFF`, `ON`, `DEFAULT`. `MISESERI` is passed as a string tuple `('MISESERI',)`.
3. **Assembly Feature Suppression**: `assembly.suppressFeatures(featureNames=('Part-1-1',))`.
4. **Instance Name Preservation**: `Part-1-1-TEMP` is created, `Part-1-1` orphan instance is suppressed, and `Part-1-1-TEMP` is renamed to `Part-1-1` (`assembly.renameFeature`). Recorded in `INSTANCE_REPLACEMENT_API_AUDIT.json`.
5. **Model Entity Rebinding**: All materials, sections, section assignments, part sets, assembly sets, surfaces, BCs, equations, loads, constraints, interactions, steps, field output, and history output requests are inventoried and audited. Recorded in `MODEL_ENTITY_REBINDING_AUDIT.json` with `unresolved_entity_count = 0` and `model_entity_rebinding_pass = true`.

## 3. Fail-Closed PBS Wrapper & Evidence Contracts (`M2RMBUILD2.pbs`)

- Scratch directory: `/scratch/pr21vyci/m2rmbuild2_${PBS_JOBID}`.
- Terminal trap installed immediately after evidence path validation.
- Qualified module sequence (`module purge`, `gcc/11.4.0`, `intel/2024.2.0`, `abaqus/2023`) fails closed on error.
- Telegram START delivery reads `~/.config/adaptive-remeshing/notifications.env`, validates curl return code and JSON `"ok": true`, and fails before CAE if delivery fails.
- PBS parses runtime JSON audit fields (`contract_pass`, `abaqus_cae_execution`, `documented_remeshing_rule_signature`, `final_geometry_instance_name`, `model_entity_rebinding_pass`, `unresolved_entity_count`, `input_written_by_job_writeInput`).
- Captures `CAE_TRACEBACK.txt` on error and generates `MISSING_EVIDENCE_REPORT.json`.

## 4. Decision Gate Selection

- **Final Classification**: `f27_m2rmbuild2_clean_linux_qualified_not_authorized`
- **Prepared Job**: `M2RMBUILD2` (CAE build qualification only)
- **`M2RMPROV1` Solver Execution Prepared**: `false`
- **`M2RMEXEC2` Prepared**: `false`
- **Execution Authorized**: `false` (No submission; authority consumed = 0).
