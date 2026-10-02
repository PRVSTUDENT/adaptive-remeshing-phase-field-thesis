# Session Report: Gate-6B Mode-I Temporal Convergence Candidates Preparation, Invariant Audit, Cluster Datachecks, and Evaluation Pipeline Implementation

- **Session Date:** 02 October 2026, 10:00 CEST
- **Agent:** Gemini Antigravity
- **Active Task:** `F1147-GATE6B-TEMPORAL-CANDIDATES-PREPARATION-AND-DATACHECKS-20261002`
- **Parent Commit:** `42762382e8e0f4a8fc87b43eb0ddfba06028bcaf`
- **Active Phase:** `MODE1_GATE6B_ENERGY_CONVERGENCE_AND_STEP2_RECONCILIATION_ACTIVE`
- **Active Reference Job:** `1409734.mmaster02` (`PK_M1_REF15K_ENERGY`, status `R` on `mnode097/0`) — **Left 100% Untouched (Non-Polling Guard Enforced)**

---

## 1. Executive Summary

In strict compliance with multi-agent governance rules, scheduler policy, and the governing directive (*"We need to have understood everything related to the first model before we increase complexity"*), this session completed the preparation, cryptographic auditing, cluster synchronization, and preflight datacheck qualification of the Mode-I Gate-6B temporal-convergence energy candidates ($T_1, T_2, T_3$).

While the active corrected $S_1$ reference solve (`1409734.mmaster02`, `PK_M1_REF15K_ENERGY`) continued solving monotonically on compute node `mnode097/0` under non-polling invariant guards, candidates $T_1$, $T_2$, and $T_3$ were prepared so that they are fully qualified offline and on the cluster, ready for immediate conditional execution once $S_1$ energy qualification is formally completed.

All three candidates passed Abaqus 2023 / Intel Fortran 2021.13.0 Datacheck preflight on the cluster with **100% Exit Code 0** (0 preprocessor errors). In accordance with the Gate-6B submission gate, they are classified as **`DATACHECK_PASSED_READY_AFTER_CORRECTED_S1_ENERGY_QUALIFICATION`** (strictly unsubmitted, `authorized: false`). A dedicated, modular evaluation pipeline (`scripts/validation/temporal_convergence_pipeline.py`) was implemented and verified with unit tests (15/15 passed in 0.22s, 100% Exit 0), strictly enforcing matched-displacement interpolation with ZERO extrapolation.

---

## 2. Historical Provenance & Mesh/Material Invariance Proof

Historical Mode-I temporal input decks executed on the cluster were retrieved, transferred to the local workspace, and audited against the active $S_1$ reference deck:
- $T_1$ Coarse $2\times$ (`PK_M1_T1_DTCOARSE.inp`, Job `1406020`, SHA-256: `83D34F312D9FFDE32FD14AA8AF1BDB2F6AA16B66A961B99F271FAF120437EC1D`)
- $T_2$ Nominal $1\times$ (`PK_M1_T2_DTNOMINAL.inp`, Job `1406021`, SHA-256: `BC000E0C5791150A711CB7AF447A0BB34D1B9D9AF5C6CE9D096C98749E8EDF61`)
- $T_3$ Fine $0.5\times$ (`PK_M1_T3_DTFINE.inp`, Job `1406317`, SHA-256: `68BEFB3FBE33F1F4DF7723594AA3991589F5E1464EA68F31943B6FF643B8134B`)

A line-by-line diff and semantic audit confirmed:
1. **Mesh Invariance (100.000% Bit-for-Bit Identity):**
   - Physical elements: Exactly 15,192 elements in Layer 1 (Phase UEL 1..15192), Layer 2 (Displacement UEL 15193..30384), and Layer 3 (Companion CPE4 30385..45576).
   - Nodes: Exactly 15,521 nodes (1..15521) plus Reference Point RP (Node 999999).
   - Geometry: $1.0 \times 1.0\,\text{mm}$ square domain with initial horizontal sharp slit at $y=0.5\,\text{mm}$ ($a_0 = 0.5\,\text{mm}$), process zone resolution $h = 0.0030\,\text{mm}$ ($l_0/h = 2.5$).
2. **Material & Phase-Field Parameter Invariance:**
   - Young's modulus: $E = 210.0\,\text{kN/mm}^2$ (GPa)
   - Poisson's ratio: $\nu = 0.3$
   - Fracture toughness: $G_c = 0.0027\,\text{kN/mm}$ (kJ/m$^2$)
   - Regularization length scale: $l_0 = 0.0075\,\text{mm}$
   - Residual stiffness: $k = 1.0 \times 10^{-7}$
   - Companion scaling constant: $N_{\text{phys}} = 15192.0$ in `*User Material, constants=3`
3. **Kinematic Coupling & Boundary Invariance:**
   - Bottom edge: $u_y = 0.0$ on `N_BOTTOM`
   - Bottom-left corner pin: $u_x = 0.0$ on `N_PIN`
   - Top edge horizontal restraint: $u_x = 0.0$ on `N_TOP`
   - Top edge vertical displacement tied via linear kinematic coupling equations to Reference Point RP (Node 999999)
   - Prescribed loading: Step 1 $u \in [0, 0.0050]\,\text{mm}$ ($t = 1.0\,\text{s}$), Step 2 $u \in [0.0050, 0.0100]\,\text{mm}$ ($t = 1.0\,\text{s}$). Total endpoint $u = 0.010000\,\text{mm}$.
4. **Thickness Normalization Convention:**
   - Standard project normalization convention $t_{\text{ref}} = 1.0\,\text{mm}$ slice adopted consistently across all candidate packages and companion `*Solid Section ... 1.0` cards, confirming that literature formulation (Pandey & Kumar 2025 Sec. 4.1) omits thickness prescription.

---

## 3. The Single Intended Numerical Difference: Time Discretization Schedules

The only parameter varying across $T_1$, $T_2$, and $T_3$ is the time-step size $\Delta t$:

| Candidate ID & Package | Ratio | Step 1 $\Delta t$ [s] (incs) | Step 2 $\Delta t$ [s] (incs) | Total Incs | Solver Walltime Request | Intended Role |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **$T_1$ Coarse** (`17_...`) | $2\times$ | $1.0 \times 10^{-3}$ (1,000) | $4.0 \times 10^{-4}$ (2,500) | **3,500** | 24:00:00 | Coarse temporal upper bound |
| **$T_2$ Nominal** (`18_...`) | $1\times$ | $5.0 \times 10^{-4}$ (2,000) | $2.0 \times 10^{-4}$ (5,000) | **7,000** | 48:00:00 | Nominal baseline (matches $S_1$) |
| **$T_3$ Fine** (`19_...`) | $0.5\times$ | $2.5 \times 10^{-4}$ (4,000) | $1.0 \times 10^{-4}$ (10,000) | **14,000** | 48:00:00 | Fine temporal resolution asymptotic limit |

---

## 4. Qualified Gate-6B Energy Output Architecture Propagation

The historical decks had `*Depvar 18` and `*Element Output, elset=umatelem` (only 1 element). To ensure complete, authoritative energetic observability, the qualified Gate-6B architecture was propagated into each candidate:
1. **Production Fortran User Subroutine:**
   - Linked to verified production source `f42_mixed_uel.for` (SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`).
   - Integrated with `CALL GETOUTDIR(OUTDIR_STR, L_OUTDIR)` in `UEXTERNALDB` to write `uel_energy_balance.csv` directly into the simulation working directory at every converged increment.
2. **Input Deck Energy Instrumentation:**
   - Upgraded `*Depvar 18` $\to$ `*Depvar 20`.
   - Mesh companion constant $N_{\text{phys}} = 15192.0$ verified in `*User Material, constants=3`.
   - Field output in Step 1 and Step 2 updated to:
     ```
     *Restart, write, frequency=0
     *Output, field, frequency=1
     *Node Output, nset=N_RP
      U, RF
     *Element Output, elset=All_elem
      SDV
     *Node Print, freq=1, nset=N_RP
      U2, RF2
     ```
   - This records all 20 state variables (including `SDV17 = E_frac`, `SDV18 = E_elas`, `SDV19 = psi_f`, `SDV20 = psi_e`) on all 15,192 visualization elements in the ODB, while keeping file size bounded by omitting full-mesh nodal output.

---

## 5. Candidate Package Inventory & Cryptographic Manifest

Three clean, self-contained model candidate packages were created and deployed:

### A. $T_1$ Coarse (`models/pandey_kumar_mode1/17_temporal_convergence_t1_coarse/`)
- `PK_MODE1_T1_COARSE_ENERGY.inp` (SHA-256: `33183ADA17DA6712F93DA5648D1D4C9B41C27398DA472EE6619E0839E96ACCFF`)
- `f42_mixed_uel.for` (SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`)
- `job_notifications.sh` (SHA-256: `96756A681D2D36C11B36B89288F631F8ECC9537543C2C745A4BAE1B425984B47`)
- `submit_datacheck.pbs` (SHA-256: `7F6E45E8D6BF4C7A53AC608C66EDDF1D54FE75278D95FD7862085A65FE6A34F9`)
- `submit_solver.pbs` (SHA-256: `C6C8AE190FE70821557F26C6B0EB011D447AE6A6C1BFDE821ED268153C4D35C7`)
- `PRE_JOB_CARD.md`, `manifest.json`, `extract_authoritative_mode1_energy_complete.py`

### B. $T_2$ Nominal (`models/pandey_kumar_mode1/18_temporal_convergence_t2_nominal/`)
- `PK_MODE1_T2_NOMINAL_ENERGY.inp` (SHA-256: `4A0302C60FB47D59FF024BCD40EBADC4B2F036FE155F1C632F6D8874665CD6F1`)
- `f42_mixed_uel.for` (SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`)
- `job_notifications.sh` (SHA-256: `96756A681D2D36C11B36B89288F631F8ECC9537543C2C745A4BAE1B425984B47`)
- `submit_datacheck.pbs` (SHA-256: `57CF2EFE8C99933EF2B2A3ED6C3F3B77FFDE22E6EC66B72D325EEB99EFA1C57F`)
- `submit_solver.pbs` (SHA-256: `084B67E28E954DC6FD92850DE7E8715893C4E3D52A0FAEE674EC45062C953DB0`)
- `PRE_JOB_CARD.md`, `manifest.json`, `extract_authoritative_mode1_energy_complete.py`

### C. $T_3$ Fine (`models/pandey_kumar_mode1/19_temporal_convergence_t3_fine/`)
- `PK_MODE1_T3_FINE_ENERGY.inp` (SHA-256: `72D6CC5176326BFAB60FB9B23AFBE4AD6882A0ABC030465BAF10A5DC2A19519C`)
- `f42_mixed_uel.for` (SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`)
- `job_notifications.sh` (SHA-256: `96756A681D2D36C11B36B89288F631F8ECC9537543C2C745A4BAE1B425984B47`)
- `submit_datacheck.pbs` (SHA-256: `B481008064F9FE4F22C5C1045E1B5158229F5C5B9781D9E71F424CF20BCF4640`)
- `submit_solver.pbs` (SHA-256: `C6C8AE190FE70821557F26C6B0EB011D447AE6A6C1BFDE821ED268153C4D35C7`)
- `PRE_JOB_CARD.md`, `manifest.json`, `extract_authoritative_mode1_energy_complete.py`

---

## 6. Cluster Datacheck Execution & Preflight Qualification

All three candidate packages were synchronized to the cluster via non-interactive SSH/SCP and tested with live Abaqus 2023 / Intel Fortran 2021.13.0 Datacheck preflights:

1. **$T_1$ Coarse (`PK_MODE1_T1_COARSE_ENERGY`)**:
   - Fortran Compilation: Intel(R) Fortran 2021.13.0 compiled `uel_` and `umat_` with automatic CPU dispatch.
   - Subroutine Linkage: GNU ld version 2.30-128.el8_10 cleanly resolved symbols.
   - Preprocessor Analysis: 0 errors, 4 standard informational datacheck warnings.
   - Exit Code: **0** (`Abaqus JOB PK_MODE1_T1_COARSE_ENERGY COMPLETED`).
2. **$T_2$ Nominal (`PK_MODE1_T2_NOMINAL_ENERGY`)**:
   - Fortran Compilation: Intel(R) Fortran 2021.13.0 compiled `uel_` and `umat_` with automatic CPU dispatch.
   - Subroutine Linkage: GNU ld version 2.30-128.el8_10 cleanly resolved symbols.
   - Preprocessor Analysis: 0 errors, 4 standard informational datacheck warnings.
   - Exit Code: **0** (`Abaqus JOB PK_MODE1_T2_NOMINAL_ENERGY COMPLETED`).
3. **$T_3$ Fine (`PK_MODE1_T3_FINE_ENERGY`)**:
   - Fortran Compilation: Intel(R) Fortran 2021.13.0 compiled `uel_` and `umat_` with automatic CPU dispatch.
   - Subroutine Linkage: GNU ld version 2.30-128.el8_10 cleanly resolved symbols.
   - Preprocessor Analysis: 0 errors, 4 standard informational datacheck warnings.
   - Exit Code: **0** (`Abaqus JOB PK_MODE1_T3_FINE_ENERGY COMPLETED`).

All scratch datacheck binaries (`.sim`, `.stt`, `.mdl`, `.odb`, `.cax`, `.023`, `.com`) were cleaned from the remote directories, while evidence files (`.dat`, `.msg`, `.prt`) are preserved. All three candidates are classified as **`DATACHECK_PASSED_READY_AFTER_CORRECTED_S1_ENERGY_QUALIFICATION`** (strictly unsubmitted, `authorized: false`).

---

## 7. Dedicated Temporal Convergence Pipeline Implementation

A dedicated post-processing evaluation module was created:
- Module: `scripts/validation/temporal_convergence_pipeline.py`
- Test Suite: `tests/unit/test_mode1_temporal_convergence_pipeline.py`
- Key Features:
  1. Enforces strict 1D linear interpolation between adjacent bracketing frames at canonical checkpoints $u \in \{0.0010, 0.0050, 0.005857, 0.0060, 0.0062, 0.0065, 0.0070, 0.0100\}\,\text{mm}$.
  2. Raises `CensoredTrajectoryError` if $u_{\text{target}} > u_{\text{final}}$ (strict **ZERO EXTRAPOLATION** policy).
  3. Computes common-domain normalized $L_2$ curve discrepancies on $F(u)$, $E_{\text{elas}}(u)$, $E_{\text{frac}}(u)$, and $W_{\text{ext}}(u)$ strictly over $[0, \min(u_{\max 1}, u_{\max 2})]$.
  4. Computes outcome-independent successive-resolution relative differences $\delta(T_1 \to T_2)$ and $\delta(T_2 \to T_3)$ under `TREND_ONLY` governance.
  5. Regression status: **15 / 15 passed in 0.22s (100% Exit 0)** alongside the spatial suite.

---

## 8. Invariant & Governance Compliance

- **S1 Reference Job `1409734.mmaster02` (`PK_M1_REF15K_ENERGY`):** Left completely untouched. Zero polling loops, zero intrusive queries, and zero file-read operations were issued against the running reference solve.
- **Queue & Cluster Policy:** Zero solver jobs submitted. Only offline preparation, package staging, and preflight datachecks executed.
- **Step-2 62k Mesh:** Maintained frozen under `ROOT_CAUSE_CANDIDATE_NOT_YET_RECONCILED`.
- **Mode-II & State Transfer:** Maintained paused in accordance with Gate-6B priority.
- **Coordination Ledgers:** `TASK_LEDGER.csv`, `ACTIVE_TASK.json`, `CURRENT_STATE.md`, `ARTIFACT_REGISTRY.csv`, and `MODE1_CONVERGENCE_EXECUTION_MATRIX.md` (Revision 16) synchronized.
