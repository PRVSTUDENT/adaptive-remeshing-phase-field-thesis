# Final Pre-Meeting Evidence Freeze: Mode-I Benchmark Package

**Document Status:** `PREMEETING_EVIDENCE_FROZEN`  
**Date:** Monday, 14 September 2026 (for Thursday, 17 September 2026 Meeting)  
**Candidate:** Pruthviraja Reddy Vandavagali (Matr. Nr. 68865)  
**Supervisors:** Prof. Dipl.-Ing. Björn Kiefer, Ph.D. & Dr.-Ing. Stephan Roth  
**Chair:** Chair of Applied Mechanics (IMFD), TU Bergakademie Freiberg  
**Location:** `D:/Master thesis/Adaptive remeshing/docs/supervisor_reports/17-09-2026/`

---

## 1. Executive Status & Governance Notice

> [!IMPORTANT]
> **Pre-Meeting Status:** `PREMEETING_EVIDENCE_FROZEN`
> - This package represents a complete, mathematically verified, and frozen briefing pack for the Thursday (17-09-2026) supervisor meeting.
> - **Gate Status:** `MODE1_RESOLUTION_EXTENSION_COMPLETE` is **NOT** declared. Gate 5 remains formally open pending supervisor determination between **Option A** (accept Gate 5 as externally under-specified) and **Option B** (authorize author inquiry).
> - **Author Inquiry:** The prepared 6-question reproducibility inquiry letter to Dr. Pandey and Dr. Kumar remains **strictly UNSENT**.
> - **Mandatory Scope Holds:** Gate 7 (`ABAQUSER` integration), Mode-II shear fracture benchmarks, multi-step state transfer, and higher-complexity modeling remain **explicitly ON HOLD**.

---

## 2. Authoritative Numerical Definitions & Regression Protocol

### 2.1 Unconstrained Ordinary Least Squares (OLS) Formulation
Initial structural stiffness $K_0$ is evaluated from the unconstrained linear model:
$$F(u) = K_0 u + b$$
over the active initial deformation domain $0 < u \le 0.0010\,\text{mm}$ ($1.0\,\mu\text{m}$).

### 2.2 Discrete Sampling & Value-Based Filtering Rule
- **Physical Increment Spacing:** $\Delta u = 2.5 \times 10^{-6}\,\text{mm}$ ($2.5\,\mu\text{m}$ nominal).
- **Zero-Displacement Base State:** In `curve_1404933_extracted.csv`, row 0 contains the un-loaded initial condition ($u=0.0\,\text{mm}, F=0.0\,\text{kN}$, frame 0).
- **Solver Floating-Point Accumulation:** In Abaqus ODB output, numerical accumulation produces $u = 1.0000000475 \times 10^{-3}\,\text{mm}$ at frame 400 ($+4.75 \times 10^{-11}\,\text{mm}$ above nominal $0.001000\,\text{mm}$).
- **Value-Based Half-Bin Selection:** To eliminate the un-deformed base state ($u=0$) while including all active loading increments up to the nominal $1.0\,\mu\text{m}$ limit, the discrete half-bin selection rule is applied:
  $$\frac{1}{2}\Delta u < u \le u_{\max} + \frac{1}{2}\Delta u \quad (\Delta u = 2.5 \times 10^{-6}\,\text{mm}, \; u_{\max} = 0.0010\,\text{mm})$$
  This robustly selects exactly $N = 400$ increments without relying on positional slicing (`iloc`).

### 2.3 Obsolete Numerical Artifact Explanation
- An unhedged Python filter `u <= 0.0010` dropped frame 400 ($1.0000000475 \times 10^{-3} > 0.0010$), and a positional slice `df.iloc[1:400]` extracted rows 1 through 399 ($N=399$).
- Both bugs produced an incomplete 399-point sample, yielding the superseded value $K_0 = 137.821802\,\text{kN/mm}$ (which was naively rounded to $137.822\,\text{kN/mm}$).
- The authoritative $N=400$ regression yields $K_0 = 137.820804\,\text{kN/mm}$.
- **Proper Mathematical Rounding of $137.820804\,\text{kN/mm}$:**
  - Six decimals: $\mathbf{137.820804\,\text{kN/mm}}$
  - Three decimals: $\mathbf{137.821\,\text{kN/mm}}$ *(NOT $137.822$)*
  - Two decimals: $\mathbf{137.82\,\text{kN/mm}}$

---

## 3. Cross-Document Numerical Benchmark Ledger

All percentage shifts are recomputed from the verified exact values:

| Simulation Model / Job ID | Finite Elements | Initial Stiffness $K_0$ [kN/mm] | Intercept $b$ [kN] | Goodness of Fit ($R^2$) | Boundary Set Cardinality ($N_{\mathrm{bottom}}$) | Peak Force $F_{\max}$ [kN] | Peak Stroke $u(F_{\max})$ [mm] | Shift vs Ref Anchor |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Fixed Reference Anchor** (`1398090.mmaster02`) | $15{,}192$ (\texttt{CPE4}) | $\mathbf{137.945520}$ | $4.472 \times 10^{-5}$ | $0.99999960$ | $150/150$ | $\mathbf{0.757778}$ | $\mathbf{0.005857}$ | Reference Anchor |
| **Corrected Frozen 71k** (`1405044.mmaster02`) | $71{,}320$ | $\mathbf{138.021013}$ | $9.948 \times 10^{-12}$ | $1.00000000$ | $150/150$ (0 lift) | -- (frozen elastic) | -- (frozen elastic) | $+0.0547\%$ |
| **Corrected Nominal 1\%** (`1404933.mmaster02`) | $71{,}320$ | $\mathbf{137.820804}$ | $4.470 \times 10^{-5}$ | $0.99999960$ | $150/150$ (0 lift) | $\mathbf{0.745325}$ | $\mathbf{0.005750}$ | $-0.0904\%$ |
| **Supporting 4T Twin** (`1405003.mmaster02`) | $71{,}320$ | $\mathbf{137.820804}$ | $4.470 \times 10^{-5}$ | $0.99999960$ | $150/150$ (0 lift) | $0.745325$ | $0.005750$ | $-0.0904\%$ |
| **DEFECTIVE PREPROC. (Diag. Only)** (`1399632.mmaster02`) | $71{,}320$ | $122.379$ | -- | -- | $16/150$ (lift $\le 48.34\%$) | $0.478203$ | $0.004150$ | $-11.28\%$ |

> [!NOTE]
> **Table Semantic Clarification:**  
> The quantity $16/150$ bottom nodes in Job `1399632` is strictly a **boundary-set cardinality metric** (16 nodes retained out of 150 intended due to preprocessor card limits), **not** an increment regression sample. All initial stiffness regressions are evaluated over $N=400$ increments ($u \le 1.0\,\mu\text{m}$).

---

## 4. Cryptographic Checksum Ledger of Meeting Deliverables

All deliverables in `docs/supervisor_reports/17-09-2026/` have been compiled, verified, and locked:

### Key PDF Deliverables
1. **Master 12-Page Report:**
   - File: `SUPERVISOR_MEETING_REPORT_MODE1_2026-09-17.pdf`
   - SHA-256: `61b74c0b2feb2e0609e9fe9705805ebcd640ec64798e4c25d0dcfc09a0aedbbb`
   - Size: $2{,}755{,}617$ bytes
   - Verification: Exactly 12 pages, 0 undefined references, 0 overflows, updated with $K_0 = 137.820804\,\text{kN/mm}$ ($K_0 \approx 137.821\,\text{kN/mm}$).
2. **One-Page Briefing Agenda:**
   - File: `MEETING_AGENDA_ONE_PAGE.pdf`
   - SHA-256: `b5db7528831b0cb22c099c62ec7b3dbebeebab6f5f54a0d87ed2a30ada131034`
   - Size: $386{,}643$ bytes
   - Verification: Strictly 1 page, 45-minute flow, 0 undefined references.
3. **One-Page Numbers Cheat Sheet:**
   - File: `MEETING_KEY_NUMBERS_ONE_PAGE.pdf`
   - SHA-256: `4869b7011a6ad367cb527a7aca65b92f7812ad7566babbd790a9b85763b61f2c`
   - Size: $393{,}518$ bytes
   - Verification: Strictly 1 page, print-friendly, includes mechanical table, canonical pre-analysis, multi-release audit, and regional decomposition.

### Briefing Markdown Documents
- `MEETING_TALK_TRACK.md`: SHA-256 `d801b4fc6e98c497abdf966c167b980abe11af376b6659f182a4bd6e58a24996` (5–7 min first-person physical narrative).
- `SUPERVISOR_QA_PREP.md`: SHA-256 `0cbecff79be44104f71423342965bad7b8cfef254dd9e500f2b6f540053eb080` (14 defensible short answers with known/verified/unresolved separation).
- `QUESTIONS_FOR_SUPERVISOR.md`: SHA-256 `af95e0014cede76155f724e9b703e9bc357854db454865111643f51a469681cf` (Option A vs Option B decision request).

### Value-Based Reconciliation Artifacts
- `reconcile_k0_1404933.py`: SHA-256 `9dd26db7d77669a5e033f3e16dcba2c06da2d8aa981917a5a3627bbfad037b29`
- `reconciliation_artifact_1404933.md`: SHA-256 `10997ab2de67f05ad7203e7ea21dc7c49d1f993b958afc34d9a11d09a1cd9aeb`
- `k0_1404933_reconciliation_artifact.json`: SHA-256 `8c51808ff4b2277c949264bacf78b3d7be9d82c3efa390b165d1cb49ba056e0e`
- `reconciliation_1404933_selected_rows.csv`: SHA-256 `2505bacdc8545ed108866210b82e8f344e03cd3e52852ba1bb1b36d97d0e636c`

---

## 5. Unresolved Gate-5 Reproduction Discrepancy Statement

- **Observed Discrepancy:** The literal published remeshing rule (`errorTarget=1.0`, `All_elem`) yields $71{,}320$ finite elements across Abaqus 2019 GA, 2021.HF26, 2022 GA, and 2023.HF4 ($100.000\%$ bitwise identical decks).
- **Physical Reason for High Element Count:** Sizing depends on relative recovered von Mises stress discretization error (`MISESERI`). Meeting 1% error globally forces Abaqus to refine not only the crack tip ($h \to h_{\min} = 1.0\,\mu\text{m}$) but also the transition zone ($20{,}273$ elements) and far-field ($41{,}986$ elements). These outer regions account for $62{,}259$ elements ($87.3\%$ of the mesh).
- **Epistemic Status:** An exhaustive 15-factor One-Factor-At-A-Time (OFAT) audit ruled out release shifts, load scale, output frequency, coarsening, and mesher controls. The accessible evidence does not identify which unpublished implementation detail accounts for the reported $\approx 13{,}941$-element mesh. Possible distinctions such as call-site parameter linkage or an unstated region definition remain hypotheses requiring author information; neither is established.
- **Classification:** `GATE5_AUDIT_COMPLETE / EXTERNAL_INFO_REQUIRED`.
