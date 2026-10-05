# Mode-I Active Job 1409912 Source Provenance Integrity Audit Report

Protocol version: 2  
Governing Task: `F1179-GATE6B-SOURCE-PROVENANCE-INTEGRITY-AUDIT-20261003`  
Audit Date: `2026-10-03T10:35:00+02:00`  
Investigating Agent: `gemini-antigravity`  
Audit Target: Fortran user subroutine `f42_mixed_uel.for` in Package 89 (`models/pandey_kumar_mode1/89_mode1_preanalysis_uel_canonical_2906/`) utilized by active PBS Job `1409912.mmaster02` (`PK_M1_JOB1_SOLVE`)  
Cluster Solver Invariance: **Zero active solver files inspected; running jobs 1409912.mmaster02, 1409914.mmaster02, and 1409867.mmaster02 preserved strictly untouched under non-polling guard.**

---

## 1. Executive Summary & Formal Verdict

A forensic source-provenance integrity audit was executed to resolve a concrete inquiry regarding a potential SHA-256 hash discrepancy in the Fortran user subroutine `f42_mixed_uel.for` for active layered pre-analysis Job `1409912.mmaster02`:
- **Submission-reported SHA-256:** `91ad75b0ff65dbd25967feae42af531239a99b3f76d9ef49d7359a66403dea6b`
- **Audit-inquiry reported SHA-256:** `91ad75b06d48b1968fa3d9daee630248f760ca51d9d701041914ebc2901a1db1`

### Forensic Investigation Finding:
1. **Immutable Git History & On-Disk State:**
   Across all 19,310 Git objects and all repository files, there is **EXACTLY ONE** Fortran blob matching prefix `91ad75b0`:
   - Git Blob SHA-1: `9c44b528d30ab71ceb210bdeb3065ce306c15138`
   - File Path: `models/pandey_kumar_mode1/89_mode1_preanalysis_uel_canonical_2906/f42_mixed_uel.for`
   - File Size: `32,129` bytes (927 lines)
   - SHA-256: `91ad75b0ff65dbd25967feae42af531239a99b3f76d9ef49d7359a66403dea6b`
   - Committed at: `4a6dc0d8d8a43a8679acf7fb47ced89f6fde9e7e` (Package creation)
   - Synchronized before submission at: `6b24242a2315ca98aa5085e5f1288781b53c5bb1` (Task F1175)
   - Present on disk at HEAD (`6f1bdbc98a6223f49824e126927ec1381b2f95d4`): bit-identical `32,129` bytes, identical SHA-256.

2. **Origin of the Second Hash (`91ad75b06d48...`):**
   A complete scan of Git history, file systems, and the session trajectory established that the string `91ad75b06d48b1968fa3d9daee630248f760ca51d9d701041914ebc2901a1db1` **never existed as a file, Git object, or committed repository record**. It originated solely in Step 1335 of the conversation transcript as an assistant typographical / generation artifact in a closing markdown summary table. In contrast, all committed artifacts generated during Task F1178 ([`MODE1_ARCHITECTURE_ISOLATION_DECK_AUDIT.md`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/MODE1_ARCHITECTURE_ISOLATION_DECK_AUDIT.md#L40), [`MODE1_ARCHITECTURE_ISOLATION_AUDIT.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/MODE1_ARCHITECTURE_ISOLATION_AUDIT.json#L7), and [`PACKAGE_MANIFEST.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/89_mode1_preanalysis_uel_canonical_2906/PACKAGE_MANIFEST.json#L46)) recorded the true, unaltered SHA-256 `91ad75b0ff65...`.

3. **Classification:**
   - Discrepancy category: **`REPORTING_TYPING_ERROR`** (in conversational closing response text only).
   - Executable code change: **NONE** (`0` lines differ; `0` bytes differ).
   - Non-executable comment/metadata change: **NONE**.

### Formal Assigned Verdict:
# **`ACTIVE_1409912_SOURCE_PROVENANCE_VERIFIED`**

### Direct Governance Consequences:
- **No Job Submission Required:** Zero new PBS jobs are submitted (`MAX_SUBMISSIONS_CONSUMED=0`).
- **Isolation Control Experiment Preserved:** Package 90 continuum control (`1409914.mmaster02`) and Package 89 layered variant (`1409912.mmaster02`) remain 100% valid under **`ARCHITECTURE_ISOLATION_CONTROL_VALID`**.
- **Active Cluster Jobs Preserved:** Active solver jobs `1409914.mmaster02`, `1409912.mmaster02`, and `1409867.mmaster02` remain running untouched under the non-polling guard.

---

## 2. Multi-Record Cryptographic Provenance Cross-Check

Every authoritative project record and committed file was checked byte-for-byte:

| Record / File Path | Line / Key | Recorded SHA-256 | Bit-for-Bit Status |
| :--- | :--- | :--- | :---: |
| [`models/pandey_kumar_mode1/89_mode1_preanalysis_uel_canonical_2906/f42_mixed_uel.for`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/89_mode1_preanalysis_uel_canonical_2906/f42_mixed_uel.for) | Entire File | `91ad75b0ff65dbd25967feae42af531239a99b3f76d9ef49d7359a66403dea6b` | **`MATCH`** |
| [`models/pandey_kumar_mode1/89_mode1_preanalysis_uel_canonical_2906/PACKAGE_MANIFEST.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/89_mode1_preanalysis_uel_canonical_2906/PACKAGE_MANIFEST.json) | Line 46 | `91ad75b0ff65dbd25967feae42af531239a99b3f76d9ef49d7359a66403dea6b` | **`MATCH`** |
| [`project_coordination/ARTIFACT_REGISTRY.csv`](file:///D:/Master%20thesis/Adaptive%20remeshing/project_coordination/ARTIFACT_REGISTRY.csv) | Row 1191 | `91ad75b0ff65dbd25967feae42af531239a99b3f76d9ef49d7359a66403dea6b` | **`MATCH`** |
| [`models/pandey_kumar_mode1/MODE1_ARCHITECTURE_ISOLATION_DECK_AUDIT.md`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/MODE1_ARCHITECTURE_ISOLATION_DECK_AUDIT.md) | Line 40 | `91ad75b0ff65dbd25967feae42af531239a99b3f76d9ef49d7359a66403dea6b` | **`MATCH`** |
| [`models/pandey_kumar_mode1/MODE1_ARCHITECTURE_ISOLATION_AUDIT.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/MODE1_ARCHITECTURE_ISOLATION_AUDIT.json) | Line 7 | `91ad75b0ff65dbd25967feae42af531239a99b3f76d9ef49d7359a66403dea6b` | **`MATCH`** |
| [`project_coordination/sessions/2026-10-03_0810_gemini-antigravity_F1175.md`](file:///D:/Master%20thesis/Adaptive%20remeshing/project_coordination/sessions/2026-10-03_0810_gemini-antigravity_F1175.md) | Line 28 | `91ad75b0ff65dbd25967feae42af531239a99b3f76d9ef49d7359a66403dea6b` | **`MATCH`** |
| [`models/pandey_kumar_mode1/GATE6B_PREANALYSIS_FIDELITY_RECONCILIATION.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/GATE6B_PREANALYSIS_FIDELITY_RECONCILIATION.json) | Line 19 | `91ad75b0ff65dbd25967feae42af531239a99b3f76d9ef49d7359a66403dea6b` | **`MATCH`** |

---

## 3. Byte-by-Byte and Line-by-Line Source Comparison

To provide complete mathematical and cryptographic closure:
1. **Submission Commit Blob vs Disk HEAD Blob:**
   - Commit `6b24242` blob: `9c44b528d30ab71ceb210bdeb3065ce306c15138` (SHA-256 `91ad75b0ff65dbd25967feae42af531239a99b3f76d9ef49d7359a66403dea6b`)
   - Disk HEAD file: `32,129` bytes (SHA-256 `91ad75b0ff65dbd25967feae42af531239a99b3f76d9ef49d7359a66403dea6b`)
   - Exact line diff: **0 lines differ (100.000% identity)**.

2. **Source Evolution from Canonical Reference Subroutine (`16_energy_qualification_reference_15k`, SHA-256 `ce8d5edc...`):**
   The sole modifications made when constructing Package 89 in Task F1173 (commit `4a6dc0d8`) were:
   - Line 871: `NPHYS_VAL = 2906` (parameterized for canonical 2,906 mesh rather than 71,320).
   - Lines 885–912: isotropic plane-strain Hooke stress evaluation in UMAT using $E=210\,\text{GPa}, \nu=0.3$:
     $$\sigma_{11} = C_{11}\varepsilon_{11} + C_{12}\varepsilon_{22},\quad \sigma_{22} = C_{12}\varepsilon_{11} + C_{22}\varepsilon_{22},\quad \sigma_{12} = C_{33}\gamma_{12}$$
   - Lines 913–918: negligible diagonal dummy tangent $10^{-11}\,\text{kN/mm}^2$ preventing duplicate structural stiffness while enabling Abaqus Mises stress recovery.
   - Zero modifications were made to UEL element formulations, quadrature, shape functions, or phase-field equations.

---

## 4. Synthesis & Governance Clearance

- The cryptographic integrity of active layered pre-analysis Job `1409912.mmaster02` is **100% verified and uncompromised**.
- The pre-declared architecture-isolation verdict **`ARCHITECTURE_ISOLATION_CONTROL_VALID`** is reaffirmed with 0 confounds.
- No replacement job is needed or permitted.
- Active cluster jobs remain running under strict non-polling protocol.
