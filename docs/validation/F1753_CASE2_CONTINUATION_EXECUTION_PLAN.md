# Task F1753: Case 2 Method A Controlled-Only Continuation Production Simulation Execution Plan

## 1. Executive Summary & Objective

Task **F1753-CASE2-CONTROL-ONLY-CONTINUATION-EXECUTION** is the authorized successor to Task F1752. Following comprehensive zero-PBS preflight qualification and evidence reconciliation (HND-F1752-CASE2-PREFLIGHT-001 and HND-F1752-CASE2-PREFLIGHT-002), Task F1753 requests formal authorization to execute **exactly ONE bounded PBS continuation simulation** on the HPC cluster for Case 2 (Pandey & Kumar 2025, Section 4.5, Plate with an Off-Axis Hole).

The objective is to determine whether relaxing the artificial solver cutoff `dt_min` from $1.0\times 10^{-8}$ to $1.0\times 10^{-11}$ in Step 2 of the unchanged, 23,965-element adapted mesh enables the solver to overcome the cutback stall at Node 8056, continue nonlinear fracture propagation through the secondary distal ligament, and complete specimen failure under full physical governance.

---

## 2. Predecessor Task F1752 Closeout & Readiness Reconciliation

Task F1752 conclusively resolved all six findings from `HND-F1752-CASE2-PREFLIGHT-001` and completed the two targeted execution-readiness verifications directed by `HND-F1752-CASE2-PREFLIGHT-002`:

1. **Finding F1752-R01 (Unified Diff Sign):** Resolved. Confirmed positive initial increment `0.002` in both decks; exactly 1 line changed in 96,220 lines.
2. **Finding F1752-R02 (COMMON-Block Restart Disqualification):** Resolved. Proved `UEXTERNALDB(LOP=0)` zeroes `SV_H_COMMITTED` and `UEL` line 249 guard skips restoration at Step 2 (`KSTEP=2`), establishing that Step 2 restart produces catastrophic history loss. Controlled full rerun on unchanged mesh is the sole valid route.
3. **Finding F1752-R03 (Runtime Monitor Verification):** Resolved. Authored `scripts/hpc/monitor_case2_cutbacks.py` and validated offline via `tests/unit/test_monitor_case2_cutbacks.py` across 7 test cases covering line parsing, cutback counting, reset on converged increments, threshold crossing at 50, authentic Job 1423271 tail parsing, multi-chunk streaming carryover, partial line buffering, delayed updates, and simulated termination without external Abaqus calls.
4. **Finding F1752-R04 (Field Output Coverage & Irreversibility Gates):** Resolved. Verified production deck specifies `*OUTPUT, FIELD, FREQUENCY=1` in both steps (every converged increment is an ODB frame). Verified Layer 3 UMAT maps `STATEV(1)=d` and `STATEV(2)=H` across all 23,965 physical elements at all integration points. Verified authentic F1735 data covers 23,965 elements across 254 frames. Formally defined observation boundary: irreversibility is verified across 100% of saved converged equilibrium frames; unconverged cutback trials are discarded by Abaqus solver memory and classified as unobserved.
5. **Finding F1752-R05 (Testable Parity & Continuation Hypotheses):** Resolved. Scoped continuation and checkpoint parity ($|F_{\text{rerun}} - F_{1423271}|/F_{1423271} \le 0.01\%$, $|\Delta u_y| \le 1.0\times 10^{-6}\,\text{mm}$) as testable scientific hypotheses.
6. **Finding F1752-R06 (Node Counts & Peak Force):** Resolved. Reconciled 23,957 physical mesh nodes vs 23,958 total deck nodes (including Reference Point Node 999999). Reconciled authentic adapted peak force $F_{\max} = 0.57168\,\text{kN}$ (571.68 N, Job 1423271) vs coarse pre-analysis peak force ($0.5488\,\text{kN}$), establishing the 75% load drop threshold at $F_{\text{final}} \le 0.14292\,\text{kN}$.

---

## 3. Authoritative Technical Configuration & Execution Manifest

| Parameter | Specification / Value | Provenance / Verification |
| :--- | :--- | :--- |
| **Benchmark Geometry** | Pandey & Kumar (2025), Section 4.5 | Plate with Off-Axis Hole ($1.0 \times 1.0\,\text{mm}$) |
| **Execution Strategy** | Controlled Full Rerun on Unchanged Mesh | Required to preserve COMMON-block history |
| **Physical Elements** | 23,965 elements | 97.2% CPE4 quads, 2.8% CPE3 tris |
| **Total Deck Elements** | 71,895 layered elements | Layer 1 (CPE4/CPE3), Layer 2 (UEL), Layer 3 (UMAT) |
| **Physical Mesh Nodes** | 23,957 nodes | Intact quadrilateral mesh |
| **Total Deck Nodes** | 23,958 nodes | Includes Reference Point Node 999999 |
| **Input Deck Path** | `models/pandey_kumar_mode1/234_f1752_case2_continuation/PK_F1752_CASE_2_CONTINUATION.inp` | Staged at `/scratch9/pr21vyci/runs/f1752_case2_continuation/` |
| **Input Deck SHA-256** | `CCB35B34BFAE015EA4846D3D0765FC2646E6C9AF47958F8C21A0A4F25A14CC4A` | Verified bitwise parity |
| **Subroutine Path** | `models/pandey_kumar_mode1/234_f1752_case2_continuation/f42_mixed_uel.for` | Bitwise frozen canonical Amor UEL |
| **Subroutine SHA-256** | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` | Verified bitwise parity |
| **PBS Script Path** | `models/pandey_kumar_mode1/234_f1752_case2_continuation/submit_f1753_case2_continuation.pbs` | Verified bitwise parity |
| **PBS Script SHA-256** | `4CC1285F9C853595599FF862C47AB53F6FB2558C4E64C04EE058F015850D4B11` | Staged on cluster |
| **Cluster Staging Dir** | `/scratch9/pr21vyci/runs/f1752_case2_continuation/` | Cluster scratch9 filesystem |
| **Datacheck Status** | **Exit Code 0** (0 errors, 8 informational element notices) | Intel Classic 2021.13.0 + Abaqus 2023 |
| **CPUs & Mode** | 1 CPU (Serial) | Race-free, deterministic COMMON-block execution |
| **Memory** | 8 GB RAM | Dedicated node allocation |
| **Walltime Ceiling** | 10,800 seconds (3 hours) | Hard scheduler ceiling |
| **Queue** | `normal_imfdfkmq` | Default production queue |
| **Requested Jobs** | **Exactly 1 bounded PBS job** | Prospective 26th cumulative submission |
| **Runtime Daemon** | `monitor_case2_cutbacks.py` | Enforces Stop Condition 1 (50 cutbacks) |
| **Notifications** | Dual-Channel (Email `#PBS -m abe` + Telegram shell traps) | `job_notifications.sh` |

---

## 4. Predeclared Scientific Hypotheses & Acceptance Gates

### Hypothesis 1: Checkpoint Parity (Increment 252)
A controlled full rerun with the sole modification of $dt_{\min} = 1.0\times 10^{-11}$ in Step 2 will reproduce the authentic Job 1423271 trajectory up to Increment 252 ($u_y \approx 0.00764\,\text{mm}$) within strict numerical tolerances:
$$\frac{|F_{\text{rerun}} - F_{1423271}|}{F_{1423271}} \le 0.01\%, \quad |\Delta u_y| \le 1.0\times 10^{-6}\,\text{mm}$$

### Hypothesis 2: Secondary Crack Continuation Beyond Increment 252
Lowering $dt_{\min}$ will allow the solver to overcome the convergence bottleneck at Node 8056, advancing the fully damaged crack front ($d \ge 0.90$) through the intermediate distal ligament toward the right specimen boundary.

### Stop Condition 1: Cutback Stagnation Guard
If 50 consecutive cutbacks occur in Step 2, the live background daemon `monitor_case2_cutbacks.py` immediately issues `abaqus terminate job=PK_F1752_CASE_2_CONTINUATION` to abort solver execution and prevent token/resource exhaustion.

### Stop Condition 2: Structural Severance / Load Drop Gate
The simulation is classified as structurally complete if the vertical reaction force drops by $\ge 75\%$ from the peak load:
$$F_{\text{final}} \le 0.14292\,\text{kN} \quad (142.92\,\text{N})$$

### Stop Condition 3: Walltime Ceiling
The job terminates automatically upon reaching the 10,800s walltime ceiling.

### Post-Run Acceptance Gates:
1. **Convergence Gate:** Solver executes beyond Increment 252 without diverging.
2. **Pointwise Damage Irreversibility Gate:**
   $$\min_{e, t} \Delta d_e(t) \ge -1.0\times 10^{-5}$$
   evaluated across all 23,965 physical elements across all converged saved equilibrium frames.
3. **Pointwise History Monotonicity Gate:**
   $$\min_{e, t} \Delta \mathcal{H}_e(t) \ge -1.0\times 10^{-6}\,\text{MPa}$$
   evaluated across all 23,965 physical elements across all converged saved equilibrium frames.
4. **Thermodynamic Energy Balance Gate:** UEL incremental fracture work $\Delta W_{\text{frac}} \ge 0$.
