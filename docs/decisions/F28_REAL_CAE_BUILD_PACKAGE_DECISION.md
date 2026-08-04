# Decision Record: F28 Real CAE Build Package Decision

Protocol version: 1
Task ID: `F28-INVALIDATE-F27-AND-COMPLETE-REAL-CAE-BUILD-PACKAGE`
Date: 2026-08-04
Agent: gemini-antigravity
Starting revision: `740299cbd180eac0810c4e569142ff6e57755abb`
Package preparation revision P: `7c2c680bad77301a2d2f8f13c4f001b80eb5827d`

## 1. Executive Summary & F27 Invalidation

The F27 `M2RMBUILD2` qualification package contained blocking defects:
1. Orchestrator `PREP_SHA` pointed to F26 release (`32c3f1f6...`) instead of F27 package.
2. `assembly.renameFeature` was called (not an established Assembly API in Abaqus documentation).
3. Suppressed orphan feature still occupied the required `Part-1-1` name.
4. Model-entity rebinding was represented by a hardcoded `pass=True` list without executing real Abaqus reconstruction calls.
5. Equation objects were inventoried from `assembly.equations` instead of `model.constraints`.
6. `collector.returncode` was checked before being created.
7. `MISSING_EVIDENCE_REPORT.json` generation was invalid when files were missing.
8. `compatibility.returncode` was fabricated.
9. Notification configuration and terminal delivery remained fail-open.
10. Reported SHAs in text were reconstructed from short prefixes rather than exact git outputs.

**Corrected Full SHAs**:
- F27 implementation: `377f88057d3e3fc7867ae9dcaf72548b2e9d921c`
- F27 session release: `740299cbd180eac0810c4e569142ff6e57755abb`

**F27 Invalidation**:
- All F27 qualification claims are **invalidated**.
- Corrected F27 classification: `f27_m2rmbuild2_package_invalid_no_submission_authorized`.

## 2. Abaqus API & Genuine Model Rebinding Corrections

1. **Documented Instance Replacement Sequence**:
   - `assembly.deleteFeatures(featureNames=('Part-1-1',))`
   - `assembly.Instance(name='Part-1-1', part=geom_part, dependent=ON)`
   - `assembly.regenerate()`
   - Recorded in `INSTANCE_REPLACEMENT_API_AUDIT.json`.
2. **Actual Entity Reconstruction**:
   - Reconstructed part sets (`bottom`, `top`, `notch_lower_face`, `notch_upper_face`, `notch_tip`, `All_elem`) on `Part-1-GEOM`.
   - Reconstructed assembly sets (`bottom`, `top`, `RP`) on `assembly`.
   - Reconstructed boundary conditions (`BC-bottom`, `BC-top`, `BC-RP`) on `model.boundaryConditions`.
   - Reconstructed equation constraints (`RP-equation`) under `model.constraints`.
3. **Dynamic Rebinding Audit (`MODEL_ENTITY_REBINDING_AUDIT.json`)**:
   - Computed dynamically from live `mdb` objects.
   - Enforced `unresolved_entity_count = 0` and `stale_orphan_reference_count = 0`.

## 3. Fail-Closed PBS Wrapper & Evidence Contracts (`M2RMBUILD3.pbs`)

- Workspace: `/scratch/pr21vyci/m2rmbuild3_${PBS_JOBID}`.
- Exit trap uses non-zero `first_failure` logic without shell zero expansion ambiguity, and disables itself (`trap - EXIT`) before exiting.
- Actual compatibility evidence recorded (`compatibility.returncode` computed from hash/python checks).
- Dedicated Python script generates valid `MISSING_EVIDENCE_REPORT.json` for 0, 1, or many missing files without string interpolation.
- Runtime status uses `cae_geometry_build_contract_passed` / `cae_geometry_build_contract_failed`.

## 4. Decision Gate Selection

- **Final Classification**: `f28_m2rmbuild3_static_clean_linux_qualified_not_authorized`
- **Prepared Job**: `M2RMBUILD3` (CAE build qualification only)
- **`M2RMPROV1` Solver Execution Prepared**: `false`
- **`M2RMEXEC2` Prepared**: `false`
- **Execution Authorized**: `false` (No submission; authority consumed = 0).
