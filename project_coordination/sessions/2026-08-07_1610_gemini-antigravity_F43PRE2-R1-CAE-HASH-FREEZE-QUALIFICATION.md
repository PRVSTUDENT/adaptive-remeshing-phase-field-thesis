# Session Report: Task F43PRE2-R1 Final On-Disk CAE Hash Contract, External Artifact Freeze, and Separate P/Q Qualification

**Date**: 2026-08-07  
**Agent**: `gemini-antigravity`  
**Task ID**: `F43PRE2_GEOM`  
**Starting Commit**: `b7cceaca714d096165712f8f1f6916b0e465d4f5`  
**Preparation Commit**: `610bc5f5594d485eafe32a96b6b65dd94361327c` (`P43PRE2-R1`)  
**Qualification Commit**: `Q43PRE2-R1` (separate commit after P43PRE2-R1)  
**Status**: `complete`  
**Qualification Decision**: `qualified_not_authorized`  

---

### Executive Summary

1. **Authoritative Final On-Disk CAE Hash Contract**:
   - Updated builder and provenance contract so the authoritative CAE SHA256 is determined on the finalized, post-process on-disk `.cae` binary file (`889c15ba6621ae8435324473bb385cb0da6a62866dd8c996865806b876c051ff`).
   - `pre_finalization_in_process_hash_non_authoritative` (`3b4d2800...`) preserved historically for full auditability.

2. **External HPC CAE Artifact Freeze**:
   - Connected to TU Freiberg cluster via configured SSH route (`ssh -F "$env:USERPROFILE\.ssh\codex_config" tu_freiberg`).
   - Transferred exact binary `ModeII_Geometry_Source.cae` via SCP to `/home/pr21vyci/projects/adaptive-remeshing-artifacts/f43pre2/ModeII_Geometry_Source.cae`.
   - Verified remote SHA256 using `sha256sum`: Local SHA256 == Remote HPC SHA256 == Manifest SHA256 == `889c15ba6621ae8435324473bb385cb0da6a62866dd8c996865806b876c051ff` (`external_artifact_identity = verified`).

3. **Immutable Detached Linux Worktree Qualification**:
   - Qualified package at `P43PRE2-R1` (`610bc5f5594d485eafe32a96b6b65dd94361327c`) in a clean Linux environment with `core.autocrlf=false`.
   - Verified raw Git blob == checked-out file bytes for `F43PRE2_GEOM.inp` (SHA256 `1f16f8525a7e627b90bd4958f8701a418d0ac2960654787853b2688f8fda75dd`), `build_mode_ii_native_cae.py`, `validate_f43pre2_geometry.py`, `F43PRE2_SOURCE_MANIFEST.json`, and `test_f43_geometry_source.py`.
   - Executed complete offline regression suite: 103/103 tests passed cleanly (F43: 17/17, F42: 19/19, F41: 21/21, F40: 46/46).
   - Post-test worktree verified 100% clean (`git status --porcelain` empty).

4. **Separate Preparation (P) and Qualification (Q) Lineage**:
   - `P43PRE2-R1` (`610bc5f5594d485eafe32a96b6b65dd94361327c`) contains the executable package definition.
   - `Q43PRE2-R1` is created as a separate qualification commit following `P43PRE2-R1`.

5. **HPC Repository Synchronization**:
   - Fast-forwarded remote git clone on `tu_freiberg` to HEAD cleanly (`git merge --ff-only origin/main`).
   - Authority flags remain default-closed (`execution_authorized = false`, `maximum_jobs_now = 0`). Zero HPC jobs submitted.
