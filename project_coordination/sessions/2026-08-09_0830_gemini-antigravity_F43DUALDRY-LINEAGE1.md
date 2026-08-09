# Session Report: F43DUALDRY-LINEAGE1 Immutable Final Dry-Test Preparation / Q Reconciliation

- **Task ID**: `F43DUALDRY-LINEAGE1`
- **Agent**: `gemini-antigravity`
- **Date**: `2026-08-09`
- **Historical Preparation Tag**: `P43DUALDRY1`
- **Historical P Tag Moved**: `true` (acknowledged and preserved without deletion)
- **Accepted Execution SHA**: `2b9a9809ad1848c65cbc4b72231e1ebd2abd4df6`
- **Final P Tag**: `P43DUALDRY1-FINAL1` (pointing to `2b9a9809ad1848c65cbc4b72231e1ebd2abd4df6`)
- **Final Q Tag**: `Q43DUALDRY1-FINAL1`
- **Execution Bytes Unchanged Since Accepted SHA**: `true`
- **MM Rebuilt SHA**: `b6642e77655f4f953485cba1274dd0aaae220a327ebf2ac334b67e425673af7f`
- **PK5 Rebuilt SHA**: `01b2914ee00717af82d9c8bf4437d4b5aebdc6c0ccd0c76423052ed40606b0d6`
- **UEL SHA**: `5dc005383773a2923b943024b97dc15590a4f220e319fd289c891b15c30844f3`
- **Retained Detached HEAD**: `2b9a9809ad1848c65cbc4b72231e1ebd2abd4df6`
- **Retained Full Repository Test Count**: `599`
- **Retained Failures**: `0`
- **Retained Errors**: `0`
- **Retained Skips**: `17`
- **Retained Natural Post-Test Clean**: `true`
- **Authorization Ready for Dual Dry Test**: `true`
- **Execution Authorized**: `false`
- **Submission Approved**: `false`
- **Maximum Jobs Now**: `0`
- **Qsub Called**: `false`
- **HPC Submissions**: `0`

---

## 1. Provenance and Immutable Reconciliation Summary

Task `F43DUALDRY-LINEAGE1` reconciled the tag provenance history of the dual-candidate dry test packages.

1. **Tag Movement History**:
   - Historical tag `P43DUALDRY1` was moved during local/offline script iterations in task `F43DUALDRY-PREP1`.
   - The final code state of `P43DUALDRY1` at `2b9a9809ad1848c65cbc4b72231e1ebd2abd4df6` was fully and rigorously qualified on the cluster.
   - To establish a permanent, immutable lineage without modifying or deleting historical tags, the clean immutable alias tag **`P43DUALDRY1-FINAL1`** was created directly on `2b9a9809ad1848c65cbc4b72231e1ebd2abd4df6`.

2. **Execution Byte Invariance**:
   - Byte-level comparison between `2b9a9809ad1848c65cbc4b72231e1ebd2abd4df6` and `HEAD` confirms that **zero execution-critical files** were modified (`git diff` clean).
   - Rebuilt decks (`F43UEL_MM_REBUILT.inp`, `F43UEL_PK5_REBUILT.inp`), subroutine (`f43_mixed_uel.for`), PBS scripts (`F43DRY_MM.pbs`, `F43DRY_PK5.pbs`), submission wrappers (`submit_f43dry_mm.sh`, `submit_f43dry_pk5.sh`), and manifest files remain byte-identical.

3. **Retained Qualification Evidence**:
   - Detached qualification on `tu_freiberg` at `2b9a9809ad1848c65cbc4b72231e1ebd2abd4df6`:
     - Environment preflight: `gcc/11.4.0`, `intel/2024.2.0`, `abaqus/2023`, `python/gcc/11.4.0/3.11.7`.
     - Full repository unit suite: **599 passed, 0 failures, 0 errors, 17 skips (`OK`) in 7.915s**.
     - Natural post-test cleanliness: verified clean.
     - Static validation: MM (6,618 elements, all U1..U4 present) and PK5 (14,682 elements, all U1..U4 present) passed.
     - Cross-candidate formulation fairness: passed.

4. **New Immutable P/Q Lineage**:
   - `P43DUALDRY1-FINAL1`: points to `2b9a9809ad1848c65cbc4b72231e1ebd2abd4df6`.
   - `Q43DUALDRY1-FINAL1`: points to the provenance-only qualification commit, descending from $P$, with zero execution-critical changes.

---

## 2. Technical Dry-Test Batch Contract

When authorized by explicit human instruction, the technical dry-test batch consists of:

| Job Name | Directory | Deck | Subroutine | Queue | Resources |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`F43DRY_MM`** | `models/.../dry_test_mm/` | `F43UEL_MM_REBUILT.inp` | `f43_mixed_uel.for` | `entry_imfdfkmq` | 1 CPU, 8 GB, 00:30:00 |
| **`F43DRY_PK5`** | `models/.../dry_test_pk5/` | `F43UEL_PK5_REBUILT.inp` | `f43_mixed_uel.for` | `entry_imfdfkmq` | 1 CPU, 8 GB, 00:30:00 |

- Maximum Submissions: 2.
- Scheduler Policy: Both jobs may run concurrently (2-job scheduler contract).
- Objective: Technical execution qualification only (Abaqus parse, compilation/linking, U1..U4 branch execution, passive facsimile stability, initial elastic stiffness).
- No fracture comparison or production mesh selection is encoded at the dry-test gate.
