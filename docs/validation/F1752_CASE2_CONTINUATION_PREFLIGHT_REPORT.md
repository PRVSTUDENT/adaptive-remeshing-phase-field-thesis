# Task F1752: Case 2 Method A Controlled Continuation Execution Preflight & Evidence Reconciliation Report

## Executive Summary & Independent Review Governance

Following independent review evaluation `HND-F1752-CASE2-PREFLIGHT-001` (`INSUFFICIENT_EVIDENCE` directing evidence reconciliation), this report provides the definitive, zero-PBS technical evidence resolving all six reviewer findings (**F1752-R01 through F1752-R06**).

Task F1752 prepares a controlled solver-increment continuation experiment on Case 2 (Pandey & Kumar 2025, Section 4.5: *Plate with an Off-Axis Hole*) on the unchanged 23,965-element adapted mesh.

All six review directives have been comprehensively addressed with reproducible, byte-level and source-code evidence:
1. **F1752-R01 (Initial-Increment Sign Discrepancy Resolved):** Verified byte-by-byte that the initial increment is positive `+0.002` in both decks. The `-` character was solely the markdown/diff line removal prefix (`- 0.002...` vs `+ 0.002...`). There is no negative sign in either deck.
2. **F1752-R02 (COMMON-Block Restart Audit):** Conducted an exhaustive source-level audit of `f42_mixed_uel.for` (lines 63–150 and 240–263). Demonstrated that `UEXTERNALDB(LOP=0)` explicitly zeroes `SV_H_COMMITTED` at analysis start, while `UEL` line 249 restricts state restoration to `IF (KSTEP .EQ. 1 .AND. KINC .LE. 1)`. In a Step 2 restart, `KSTEP=2`, so restoration is skipped, leaving all history variables zeroed in OS memory (catastrophic history loss). Modifying the frozen UEL is prohibited; hence, full rerun is the sole valid route.
3. **F1752-R03 (Enforcement of Runtime Stop Conditions):** Delineated hard runtime execution controls from automated post-run scientific filters. Implemented live runtime monitoring daemon `scripts/hpc/monitor_case2_cutbacks.py` polling `.sta` every 5s to terminate the solver via `abaqus terminate` if cutbacks exceed 50. PBS walltime ceiling (10,800s) provides hard scheduler-level termination.
4. **F1752-R04 (Pointwise Damage Irreversibility & History Monotonicity Gates):** Formulated explicit pointwise material-point criteria: $\min_{e,n}(d_e^{(n+1)} - d_e^{(n)}) \ge -1.0\times 10^{-5}$ and $\min_{e,n}(\mathcal{H}_e^{(n+1)} - \mathcal{H}_e^{(n)}) \ge -1.0\times 10^{-6}\,\text{MPa}$, evaluated directly from Layer 3 `SDV1` and `SDV2` across all 23,965 elements and all converged frames.
5. **F1752-R05 (Parity and Continuation Scoped as Testable Hypotheses):** Replaced absolute guarantees with testable hypotheses, defining quantitative numerical parity tolerances at the Increment 252 checkpoint ($|F_{\text{rerun}} - F_{1423271}|/F \le 0.01\%$, $|\Delta u_y| \le 1.0\times 10^{-6}\,\text{mm}$).
6. **F1752-R06 (Node Counts & Reference Peak-Force Reconciled):** Reconciled physical mesh nodes (23,957) versus total input deck node definitions (23,958 including Reference Point Node 999999). Reconciled authentic Case 2 adapted peak force $F_{\max} = 0.57168\,\text{kN}$ (571.68 N, Job 1423271) versus unadapted coarse pre-analysis peak force ($0.5488\,\text{kN}$), establishing the 75% load drop threshold at $F_{\text{final}} \le 0.14292\,\text{kN}$.

---

## 1. Resolution of Finding F1752-R01: Byte-Level Diff Audit of Line 96209

Review finding `F1752-R01` noted: *"The displayed input-deck diff is not a single-parameter change. The removed line begins with -0.002, whereas the replacement begins with +0.002."*

### 1.1 Root Cause of the Misunderstanding
In standard unified diff syntax, the first character of each line is the change marker:
- `-` indicates the removed/old line.
- `+` indicates the added/new line.

In the previous report snippet, the diff marker `-` immediately preceded `0.002`, creating the optical appearance of a negative number `-0.002`.

### 1.2 Byte-Level and Character Verification
An exact Python audit (`scripts/validation/audit_f1752_diff_and_provenance.py`) was executed on the actual input deck files:
- **Parent Deck:** `models/pandey_kumar_mode1/224_f1734_case2_distal_refinement/PK_F1728_CASE_2_PROD.inp` (96,220 lines)
- **Candidate Deck:** `models/pandey_kumar_mode1/234_f1752_case2_continuation/PK_F1752_CASE_2_CONTINUATION.inp` (96,220 lines)

```text
Full-file comparison across all 96,220 lines:
Total differing lines: EXACTLY 1 (Line 96209)

Line 96209 String Representations:
Parent line:    '0.002, 1.0, 1.0e-8, 0.002\n'
Candidate line: '0.002, 1.0, 1.0e-11, 0.002\n'

Line 96209 Byte Values (ASCII decimal):
Parent bytes:    [48, 46, 48, 48, 50, 44, 32, 49, 46, 48, 44, 32, 49, 46, 48, 101, 45, 56, 44, 32, 48, 46, 48, 48, 50, 10]
Candidate bytes: [48, 46, 48, 48, 50, 44, 32, 49, 46, 48, 44, 32, 49, 46, 48, 101, 45, 49, 49, 44, 32, 48, 46, 48, 48, 50, 10]

Token-by-Token Comparison:
  Token 1 (initial dt): parent='0.002', cont='0.002'  --> 100% IDENTICAL (Positive 0.002)
  Token 2 (step time):  parent='1.0',   cont='1.0'    --> 100% IDENTICAL (Positive 1.0)
  Token 3 (min dt):     parent='1.0e-8',cont='1.0e-11'--> MODIFIED (1.0e-8 -> 1.0e-11)
  Token 4 (max dt):     parent='0.002', cont='0.002'  --> 100% IDENTICAL (Positive 0.002)
```

**Conclusion:** Neither file contains a negative sign. The initial increment is positive `0.002` in both decks. Across all 96,220 lines, **strictly one parameter on one line is modified**.

---

## 2. Resolution of Finding F1752-R02: COMMON-Block Source Audit and Restart Disqualification

Review finding `F1752-R02` requested an in-depth source-level audit demonstrating why an Abaqus restart at Step 2 is technically disqualified.

### 2.1 Subroutine Architecture in `f42_mixed_uel.for`
In `f42_mixed_uel.for` (bitwise frozen SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`), history tracking and staggered phase-field coupling are managed through Fortran named `COMMON` blocks:

```fortran
C Lines 76-79 of f42_mixed_uel.for:
      COMMON /CB_STATE_TRANS/ SV_PHASE_COMMITTED, SV_PHASE_TRIAL,
     1                        SV_H_COMMITTED, SV_H_TRIAL,
     2                        SV_E_FRAC, SV_E_ELAS,
     3                        SV_PSI_F, SV_PSI_E
```

### 2.2 Initialization at Start of Analysis (`UEXTERNALDB`)
At the start of an Abaqus execution (`LOP = 0`), Abaqus invokes `UEXTERNALDB`:

```fortran
C Lines 88-101 of f42_mixed_uel.for:
      IF (LOP .EQ. 0) THEN
C       Start of Analysis: Zero committed and trial state & energy arrays
        DO I=1, N_CAPACITY
          SV_PHASE_COMMITTED(I) = 0.D0
          SV_PHASE_TRIAL(I)     = 0.D0
          SV_E_FRAC(I)          = 0.D0
          SV_E_ELAS(I)          = 0.D0
          SV_PSI_F(I)           = 0.D0
          SV_PSI_E(I)           = 0.D0
          DO KPT=1, 4
            SV_H_COMMITTED(I, KPT) = 0.D0
            SV_H_TRIAL(I, KPT)     = 0.D0
          ENDDO
        ENDDO
```
When Abaqus launches a restart job (`*RESTART, READ`), Abaqus invokes `UEXTERNALDB` with `LOP = 0`. Lines 88–101 execute and **explicitly zero out** `SV_H_COMMITTED` across all 150,000 capacity elements in memory.

### 2.3 Hardcoded Step-1 Guard in `SUBROUTINE UEL`
Inside `SUBROUTINE UEL`, state restoration from `SVARS` into `COMMON` memory is strictly guarded by:

```fortran
C Lines 248-262 of f42_mixed_uel.for:
      IF (JTYPE .EQ. 1 .OR. JTYPE .EQ. 3) THEN
        IF (KSTEP .EQ. 1 .AND. KINC .LE. 1) THEN
          IF (JTYPE .EQ. 1) THEN
            DO KPT=1, 4
              SV_H_COMMITTED(PHYSIDX, KPT) = SVARS(8+KPT)
              SV_H_TRIAL(PHYSIDX, KPT)     = SVARS(8+KPT)
            ENDDO
          ELSE
            DO KPT=1, 3
              SV_H_COMMITTED(PHYSIDX, KPT) = SVARS(6+KPT)
              SV_H_TRIAL(PHYSIDX, KPT)     = SVARS(6+KPT)
            ENDDO
          ENDIF
        ENDIF
      ENDIF
```

### 2.4 The Fatal Defect in Step 2 Restart
1. In a restart job resuming at Step 2 (`*RESTART, READ, STEP=2, INC=201`), the step counter passed by Abaqus Standard is `KSTEP = 2`.
2. The condition `IF (KSTEP .EQ. 1 .AND. KINC .LE. 1)` evaluates strictly to `.FALSE.`.
3. Consequently, the loop assigning `SV_H_COMMITTED(PHYSIDX, KPT) = SVARS(...)` is **never executed**.
4. Combined with `UEXTERNALDB(LOP=0)` zeroing memory, `SV_H_COMMITTED(PHYSIDX, KPT)` remains **`0.0D0` throughout the entire restart analysis**.
5. With `SV_H_COMMITTED = 0`, the phase-field crack-driving source term is wiped out, completely destroying damage irreversibility and causing the crack wake to heal elastically upon loading.

### 2.5 Absolute Governance Constraint
Could this be repaired in the Fortran code?
Modifying `f42_mixed_uel.for` is **strictly prohibited by governance**. Subroutine SHA-256 `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` is the bitwise frozen standard across all thesis benchmarks.

**Conclusion:** Step 2 restart is structurally impossible with the frozen subroutine. A controlled full rerun on the unchanged 23,965-element mesh is the **sole technically valid, mathematically consistent, and reproducible path**.

---

## 3. Resolution of Finding F1752-R03: Enforcement Mechanisms for Runtime Stop Conditions

Review finding `F1752-R03` requested clear identification of how each proposed stop condition is monitored and enforced.

| Stop Condition | Threshold | Enforcement Classification | Exact Enforcement Mechanism |
| :--- | :--- | :--- | :--- |
| **Condition 1 (Cutback Stagnation)** | $> 50$ consecutive cutbacks in Step 2 | **Live Runtime Monitor Process Trap** | Handled by daemon script `scripts/hpc/monitor_case2_cutbacks.py` launched in the PBS execution script alongside the solver. The daemon polls `PK_F1752_CASE_2_CONTINUATION.sta` every 5 seconds. If cutbacks reach 50 without a converged increment, it executes `abaqus terminate job=PK_F1752_CASE_2_CONTINUATION` and terminates the job. |
| **Condition 2 (Displacement Stagnation)** | $\Delta u_y < 1.0\times 10^{-7}\,\text{mm}$ over 10 consecutive increments | **Automated Post-Run Scientific Filter** | Post-processing script `audit_f1752_continuation_results.py` inspects all consecutive increments. If advance rate stalls below $1.0\times 10^{-7}\,\text{mm}$, the simulation is classified as `REJECT_NUMERICAL_STAGNATION`. |
| **Condition 3 (Walltime Ceiling)** | 10,800 seconds (3 hours) | **PBS Scheduler Hard Limit** | Hard ceiling enforced directly by the cluster PBS scheduler (`#PBS -l walltime=03:00:00`). Upon reaching 10,800s, PBS sends SIGTERM followed by SIGKILL, guaranteeing bounded resource consumption. |
| **Condition 4 (Nonphysical Damage)** | $d < -1.0\times 10^{-5}$ or $d > 1.02$ | **Automated Post-Run Scientific Filter** | Post-processing script inspects all integration point SDV1 values across all frames. If bounds are violated, the simulation is classified as `REJECT_UNPHYSICAL_DAMAGE`. |

---

## 4. Resolution of Finding F1752-R04: Direct Pointwise Damage Irreversibility & History Monotonicity Gates

Review finding `F1752-R04` noted that global fracture energy monotonicity and damage bounds do not exclude local healing.

### 4.1 Pointwise Mathematical Criteria
Two explicit pointwise physical acceptance criteria are established:

1. **Pointwise Damage Irreversibility Gate:**
   For every physical element $e \in \{1, \dots, 23965\}$ and every consecutive converged increment pair $(n, n+1)$:
   $$\Delta d_e^{(n+1)} = d_e^{(n+1)} - d_e^{(n)} \ge -\epsilon_{\text{irr}}, \quad \text{with } \epsilon_{\text{irr}} = 1.0\times 10^{-5}$$
   The simulation fails if $\min_{e,n} \Delta d_e^{(n+1)} < -1.0\times 10^{-5}$ (`FAIL_LOCAL_HEALING`).

2. **Pointwise History Monotonicity Gate:**
   For every physical element $e$ and every consecutive converged increment pair $(n, n+1)$:
   $$\Delta \mathcal{H}_e^{(n+1)} = \mathcal{H}_e^{(n+1)} - \mathcal{H}_e^{(n)} \ge -\epsilon_{\mathcal{H}}, \quad \text{with } \epsilon_{\mathcal{H}} = 1.0\times 10^{-6}\,\text{MPa}$$
   The simulation fails if $\min_{e,n} \Delta \mathcal{H}_e^{(n+1)} < -1.0\times 10^{-6}\,\text{MPa}$ (`FAIL_HISTORY_NONMONOTONIC`).

### 4.2 Data-Extraction Procedure
- Read Layer 3 companion elements ($NOEL \in [47931, 71895]$, corresponding to $PHYSIDX = NOEL - 47930$) from the ODB.
- Extract `SDV1` (damage $d$) and `SDV2` (history variable $\mathcal{H}$) at all integration points for every saved frame.
- Compute the global minimum increment delta:
  $$\Delta d_{\min} = \min_{n} \left[ \min_{e} \left( d_e^{(n+1)} - d_e^{(n)} \right) \right], \quad \Delta \mathcal{H}_{\min} = \min_{n} \left[ \min_{e} \left( \mathcal{H}_e^{(n+1)} - \mathcal{H}_e^{(n)} \right) \right]$$
- Publish the exact scalar values in `f1752_case2_continuation_summary.json`.

---

## 5. Resolution of Finding F1752-R05: Formulation of Claims as Testable Hypotheses

Review finding `F1752-R05` directed replacing "guaranteed parity" and "guaranteed continuation" with testable expectations and quantitative checkpoint comparisons.

### 5.1 Testable Scientific Hypothesis 1 (Pre-Bottleneck Checkpoint Parity)
**Hypothesis:** Because the initial increment ($\Delta t = 0.002$), maximum increment ($\Delta t = 0.002$), mesh, geometry, material parameters, boundary conditions, and user subroutine are 100% bitwise preserved, the full rerun will replicate Job 1423271 up to increment 252 within strict numerical tolerances:
- Global Reaction Force at Inc 252 ($u_y = 0.00762\,\text{mm}$):
  $$\frac{|F_{\text{rerun}}(\text{inc 252}) - F_{1423271}(\text{inc 252})|}{F_{1423271}(\text{inc 252})} \le 1.0\times 10^{-4} \quad (0.01\%)$$
- Specimen Displacement at Inc 252:
  $$|u_{y,\text{rerun}}(\text{inc 252}) - u_{y,1423271}(\text{inc 252})| \le 1.0\times 10^{-6}\,\text{mm}$$
- Peak Reaction Force:
  $$\frac{|F_{\max,\text{rerun}} - F_{\max,1423271}|}{F_{\max,1423271}} \le 1.0\times 10^{-4} \quad (0.01\%)$$

### 5.2 Testable Scientific Hypothesis 2 (Continuation Capability)
**Hypothesis:** Relaxing the minimum increment limit from $1.0\times 10^{-8}$ to $1.0\times 10^{-11}$ provides Abaqus Standard with the cutback resolution needed to resolve the localized phase-field DOF 3 damage correction divergence ($\Delta d = 0.0788$) at Node 8056, permitting fracture propagation to advance through the secondary ligament toward the right boundary.

---

## 6. Resolution of Finding F1752-R06: Node Counts and Peak Force Reconciliation

Review finding `F1752-R06` requested reconciliation of node counts and reference peak force.

### 6.1 Node Count Reconciliation
A script-based audit of `PK_F1752_CASE_2_CONTINUATION.inp` establishes:
- `*NODE` card starts at Node 1 and defines sequentially through Node 23,957.
- Reference Point Node 999999 is defined on the final line of the `*NODE` block.
- **Physical mesh nodes:** exactly **23,957**.
- **Reference point nodes:** exactly **1** (Node 999999).
- **Total nodes in deck:** exactly **23,958**.
- Both quantities are authentic: 23,957 refers strictly to the finite element mesh, while 23,958 refers to the total node definitions in the Abaqus input deck.

### 6.2 Reference Peak Force Reconciliation
- Authentic Case 2 adapted fracture simulation (Job 1423271): Peak reaction force is **$F_{\max} = 0.57168\,\text{kN}$** (**$571.68\,\text{N}$**) at increment 97 ($u_y = 0.00696\,\text{mm}$).
- The previously cited figure $0.548\,\text{kN}$ ($548.8\,\text{N}$) belongs to the unadapted coarse pre-analysis linear-elastic model (`PK_CASE2_PREANALYSIS.inp`).
- **Reconciled acceptance threshold:** The post-peak load drop criterion ($\ge 75\%$ drop) must be evaluated against the true Case 2 peak force $F_{\max} = 0.57168\,\text{kN}$:
  $$F_{\text{final}} \le (1 - 0.75) \times 0.57168\,\text{kN} = \mathbf{0.14292\,\text{kN}} \quad (\mathbf{142.92\,\text{N}})$$

---

## 7. Cluster Abaqus Datacheck Receipt

- **Subroutine:** `f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`)
- **Production Deck:** `PK_F1752_CASE_2_CONTINUATION.inp` (`CCB35B34BFAE015EA4846D3D0765FC2646E6C9AF47958F8C21A0A4F25A14CC4A`)
- **Compilation:** Intel Fortran Compiler Classic 2021.13.0 compiled and linked `f42_mixed_uel.for` cleanly.
- **Datacheck Exit Code:** **`Exit Code 0`** (0 errors, 8 benign element notices).
- **Elapsed Time:** 1.5s CPU, 3s wallclock on compute cluster.

---

## 8. Summary Acceptance Matrix

| Gate ID | Criterion | Value / Threshold | Classification |
| :--- | :--- | :--- | :--- |
| **Gate 1** | Global Fracture Energy Monotonicity | $E_{\text{frac}}(t_{n+1}) \ge E_{\text{frac}}(t_n) - 1.0\times 10^{-6}\,\text{kJ}$ | Physical Acceptance Gate |
| **Gate 2** | Physical Damage Bounds | $0 \le d \le 1.0004$ across all elements | Physical Acceptance Gate |
| **Gate 3** | Pointwise Damage Irreversibility | $\min_{e,n} \Delta d_e \ge -1.0\times 10^{-5}$ | Physical Acceptance Gate |
| **Gate 4** | Pointwise History Monotonicity | $\min_{e,n} \Delta \mathcal{H}_e \ge -1.0\times 10^{-6}\,\text{MPa}$ | Physical Acceptance Gate |
| **Gate 5** | Secondary Crack Extension | $d \ge 0.90$ advances past $x = 0.9031\,\text{mm}$ | Physical Acceptance Gate |
| **Gate 6** | Substantial Load Drop | $F_{\text{final}} \le 0.14292\,\text{kN}$ ($\ge 75\%$ drop vs $0.57168\,\text{kN}$) | Physical Acceptance Gate |
| **Gate 7** | Secondary Front Resolution Audit | Explicit classification as PARTIAL vs FULL | Resolution Gate |

---

## 9. Governance & Authorization Request

- **PBS Consumed in F1752:** **0** (strictly 0 new submissions).
- **Cumulative Historical Submissions:** **25** (preserved bitwise).
- **Request:** With all 6 review directives resolved with reproducible evidence, authorization is requested for **exactly 1 bounded PBS submission** for the controlled continuation rerun (`PK_F1752_CASE_2_CONTINUATION.inp`).
