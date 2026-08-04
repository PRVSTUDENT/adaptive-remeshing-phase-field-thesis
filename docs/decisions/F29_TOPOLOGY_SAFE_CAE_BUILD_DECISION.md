# Decision Record: F29 Topology Safe CAE Build Decision

Protocol version: 1
Task ID: `F29-INVALIDATE-F28-AND-PREPARE-TOPOLOGY-SAFE-CAE-BUILD`
Date: 2026-08-04
Agent: gemini-antigravity
Starting revision: `c5b0607c937e28cb6b35c4268fcc73fb099c0059`
Package preparation revision P: `b2a3535742a08961688ee5e65dbe4c8e412e4118`

## 1. Executive Summary & F28 Invalidation

The F28 `M2RMBUILD3` qualification package contained blocking defects:
1. Runtime audit parser called `os.path.exists` without importing `os` (causing `NameError`).
2. Notification configuration was optional instead of mandatory, allowing CAE execution without startup notifications.
3. Terminal Telegram failure did not cause an otherwise successful job to fail.
4. `collector.returncode` was masked by `cp ... || true` capturing `$?` of `true` (0).
5. Execution counters reported operations that may not have occurred (hardcoded `1` in trap).
6. Lower and upper notch-face selections used identical bounding boxes (`yMin=-0.001, yMax=0.001`), failing to distinguish coincident crack edges.
7. Lower and upper crack-face identity and disconnection were not proved.
8. Slit topology, coincident-face pairing, and bridge-element absence were not audited.
9. Assembly `All_elem` region was not explicitly reconstructed.
10. Source field-output requests were not explicitly rebound to assembly `All_elem`.
11. Generated input audit verified only a hash rather than checking keywords, sets, equations, BC values, MISESERI output, instance ownership, and slit topology.
12. Rebinding records contained hardcoded pass and ownership values.
13. Stale-orphan detection checked only active instance count.
14. Orchestrator did not compare package blobs against preparation revision P.
15. Package path was not restricted to the tracked frozen package.

**Corrected Full SHAs**:
- F28 Package Preparation P: `7c2c680bad77301a2d2f8f13c4f001b80eb5827d`
- F28 Qualification-Binding Q: `13f358b0ecc7be2286b2277a6411168e2cdf906d`
- F28 Session Release: `c5b0607c937e28cb6b35c4268fcc73fb099c0059`

**F28 Invalidation**:
- All F28 qualification claims are **invalidated**.
- Corrected F28 classification: `f28_m2rmbuild3_package_invalid_no_submission_authorized`.

## 2. Abaqus API & Topology-Safe Crack-Face Reconstruction (`build_f29_geometry_backed_model.py`)

1. **Topology-Safe Crack-Face Separation**:
   - Query candidate slit edges along y = 0, x in [-0.5, 0.0).
   - Inspect adjacent continuum-face centroids (`f_cy = adj_faces[0].pointOn[0][1]`).
   - Assign to `notch_lower_face` if `f_cy < 0.0` and `notch_upper_face` if `f_cy > 0.0`.
   - Verified in `SLIT_GEOMETRY_AUDIT.json` (`distinct_geometry_edge_ids = True`).
2. **Slit Mesh Topology Audit**:
   - Query mesh nodes on lower and upper crack-face sets.
   - Verified disjoint node sets (excluding notch tip vertex at (0.0, 0.0)).
   - Verified coincident node pairs along slit (x-coordinates match within 1e-5).
   - Verified zero bridge elements (`bridge_element_count = 0`).
   - Verified open slit topology preserved in `SLIT_MESH_TOPOLOGY_AUDIT.json`.
3. **Explicit Rebinding**:
   - Reconstructed assembly `All_elem` set targeting `Part-1-1` elements.
   - Reconstructed `F-Output-1` field output request targeting assembly `All_elem` set (`U`, `RF`, `MISESERI`, `MISESAVG`, `S`, `E`, `EVOL`).
4. **True Dynamic Rebinding Audit**:
   - Queried live `mdb` objects for every source entity.
   - Enforced `unresolved_entity_count = 0`, `stale_orphan_reference_count = 0`, `output_region_mismatch_count = 0`, `crack_face_identity_failure_count = 0`, `source_contract_coverage = 1.0`.

## 3. Fail-Closed PBS Wrapper & Evidence Contracts (`M2RMBUILD4.pbs`)

- Workspace: `/scratch/pr21vyci/m2rmbuild4_${PBS_JOBID}`.
- Exit trap uses non-zero `first_failure` logic and disables itself (`trap - EXIT`) before exiting.
- Mandatory notification checks require `~/.config/adaptive-remeshing/notifications.env` permissions 600 or stricter, valid credentials, and successful START Telegram delivery before CAE.
- Terminal delivery failure causes exit code 17 when no earlier failure exists.
- Actual collector returncode measured without masking (`cp` returncodes aggregated into `collector.returncode`).
- Dedicated Python script generates valid `MISSING_EVIDENCE_REPORT.json`.
- Dedicated Python script `validate_generated_input.py` parses `M2RMPROV1.inp` keywords, sets, equations, BCs, step parameters, and MISESERI output.

## 4. Frozen-Package Binding

- Package Preparation Revision P: `21c4d1a8c17cd0e8223644ef773aed22b998000b`.
- Orchestrator checks ancestry, diff against P, exact git blob IDs against P, package directory path restriction, and manifest hashes.

## 5. Decision Gate Selection

- **Final Classification**: `f29_m2rmbuild4_static_clean_linux_qualified_not_authorized`
- **Prepared Job**: `M2RMBUILD4` (CAE build qualification only)
- **`M2RMPROV1` Solver Execution Prepared**: `false`
- **`M2RMEXEC2` Prepared**: `false`
- **Execution Authorized**: `false` (No submission; authority consumed = 0).
