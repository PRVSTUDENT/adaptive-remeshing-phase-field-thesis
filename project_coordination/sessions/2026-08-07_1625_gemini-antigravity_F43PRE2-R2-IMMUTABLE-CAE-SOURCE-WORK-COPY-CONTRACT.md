# Session Report: Task F43PRE2-R2 Immutable CAE Source / Scratch Work-Copy Contract, Package Reconciliation, and True Detached Qualification

**Date**: 2026-08-07  
**Agent**: `gemini-antigravity`  
**Task ID**: `F43PRE2_GEOM`  
**Starting Commit**: `b691ef4d8921c2e9d9ecb454a6aa930edb5e7296`  
**Preparation Commit**: `b72174bada751f05bbf075963392a950f5580c3e` (`P43PRE2-R2`)  
**Qualification Commit**: `Q43PRE2-R2` (separate commit after P43PRE2-R2)  
**Status**: `complete`  
**Qualification Decision**: `qualified_not_authorized`  

---

### Executive Summary

1. **Reconciliation & Superseded Lineage**:
   - Audited post-`P43PRE2-R1` package changes. Confirmed material edits existed in `build_mode_ii_native_cae.py`, `F43PRE2_SOURCE_MANIFEST.json`, `validate_f43pre2_geometry.py`, and `test_f43_geometry_source.py`.
   - Recorded `P43PRE2-R1` (`610bc5f...`) and `Q43PRE2-R1` (`29d59e1...`) as `superseded_for_authorization_due_to_post_preparation_package_changes_and_missing_demonstrated_exact_detached_qualification`.
   - Created fresh preparation commit `P43PRE2-R2` (`b72174bada751f05bbf075963392a950f5580c3e`).

2. **Immutable CAE Source / Scratch Work-Copy Contract**:
   - Implemented strict two-file semantics:
     - **Source CAE**: External immutable provenance artifact (`/home/pr21vyci/projects/adaptive-remeshing-artifacts/f43pre2/ModeII_Geometry_Source.cae`), SHA256 `889c15ba6621ae8435324473bb385cb0da6a62866dd8c996865806b876c051ff`. In-place opening is strictly forbidden (`cae_source_open_in_place = false`).
     - **Work CAE**: Temporary scratch copy created at runtime. Source is hashed before copy; work copy is hashed before Abaqus open; Abaqus `openMdb` is executed ONLY on the work copy.
   - Empirical proof of immutability:
     - `source_hash_before`: `889c15ba6621ae8435324473bb385cb0da6a62866dd8c996865806b876c051ff`
     - `source_hash_after`: `889c15ba6621ae8435324473bb385cb0da6a62866dd8c996865806b876c051ff` (`source_immutable_test = pass`).
     - Work copy mutated cleanly on disk (`c166576a...`) without altering source.

3. **Input Deck Integrity**:
   - `F43PRE2_GEOM.inp` raw SHA256 verified unchanged at `1f16f8525a7e627b90bd4958f8701a418d0ac2960654787853b2688f8fda75dd` (3707 elements, 3597 CPE4, 110 CPE3, 3793 nodes).

4. **True Detached Linux Worktree Qualification**:
   - Created clean detached Linux worktree at `b72174bada751f05bbf075963392a950f5580c3e` (`core.autocrlf=false`).
   - Verified `git rev-parse HEAD == b72174bada751f05bbf075963392a950f5580c3e` and `git status --porcelain` empty (`pre_test_clean = true`).
   - Verified raw Git blob SHA == checked-out file SHA for all package files (`F43PRE2_GEOM.inp`, etc.).
   - Verified remote external CAE source over SSH (`889c15ba...`).
   - Executed full unit test suite inside detached worktree: 109/109 tests passed (F43: 23/23, F42: 19/19, F41: 21/21, F40: 46/46).
   - Post-test clean status verified (`post_test_clean = true`).
   - Removed detached worktree cleanly.

5. **HPC Synchronization**:
   - Fast-forwarded remote git clone on `tu_freiberg` to HEAD cleanly (`git merge --ff-only origin/main`).
   - Authority flags remain default-closed (`execution_authorized = false`, `maximum_jobs_now = 0`). Zero HPC jobs submitted.
