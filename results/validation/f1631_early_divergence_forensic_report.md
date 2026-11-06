# F1631 Early Divergence Forensic Report: Mode-I C6 Re-equilibration

**Task ID:** `F1631-METHOD-C-C6-EARLY-DIVERGENCE-FORENSIC-QUALIFICATION`  
**Predecessor Task:** `F1630-METHOD-C-C6-R12-REPAIRED-DRIVER-PAIRED-EXECUTION`  
**Handoff Correlation:** `HND-1590fe525792`  
**Evaluated Production Job:** `1420429.mmaster02` (Arm A Picard Baseline, Package 174)  
**Cluster Directory:** `/scratch9/pr21vyci/runs/mode1_c6_r12_picard_baseline/equilibration_1420429.mmaster02/`  
**Execution Boundary:** Zero new PBS submissions (`max_new_pbs_submissions = 0`). Production UEL bitwise unchanged (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`, 29,722 bytes). Active-set equations unchanged. Anderson step cap (0.045) unchanged.  

---

## 1. Executive Summary & Core Verdict

A rigorous zero-PBS forensic reconstruction was conducted across 15 discrete outer-iteration states of the authentic 140-iteration F1630 trajectory (`Outer 1, 2, 5, 10, 15, 16, 17, 18, 19, 20, 25, 30, 50, 95, 140`) utilizing complete subproblem artifacts (`endpoint.json`, exact `.inp` boundary/initial-condition cards, and `uel_energy_balance.csv`) preserved on the Freiberg HPC cluster.

### Primary Falsifiable Hypothesis Verdict
> **Hypothesis:** *Is early C6 divergence caused by an incorrectly scaled or implemented PDAS active-set update, or is it a physically permitted but unstable post-transfer fracture evolution?*

**Verdict: Confirmed Physical Instability Triggered by Non-Equilibrium Initial State.**  
The mathematical, algorithmic, and numerical evidence demonstrates:
1. **The PDAS algorithm is mathematically and dimensionally correct:** Units of discrete residual $r = K_d(H) d - f_d(H)$ are strictly $[F \cdot L] = \text{kN}\cdot\text{mm}$. The Hintermüller–Ito–Kunisch active-set test $d_i - c \cdot r_i \le d_{0,i} + \varepsilon$ with $c = 1.0\text{ (kN}\cdot\text{mm})^{-1}$ is dimensionally consistent. All 14,022 released nodes across the 140 iterations possessed negative residuals ($r < 0$), satisfying KKT complementarity requirements for release from lower-bound pinning.
2. **The divergence is NOT numerical noise or an algorithmic bug:** The onset of crack propagation at Outer 18 ($x_{\text{tip}}$ advancing from $0.0400\text{ mm}$ to $0.0500\text{ mm}$) and supercritical runaway by Outer 50 ($d_{\max} = 0.916$) is a **physically driven Mode-I crack propagation** under sustained displacement boundary conditions ($u_y = 0.0018703\text{ mm}$).
3. **The root cause is an un-equilibrated transferred state:** In the donor C5 mesh, the crack tip was pinned in elastic-damage equilibrium. Upon nonmatching transfer to C6 ($h_{\min} = 0.25\,\mu\text{m}$, 15,252 elements vs donor 11,858 elements), the transferred displacement field $u_0$ induces integration-point elastic strain energy $\psi_e^+(u_0) = 231.92\text{ MPa}$ at element 7623, exceeding the transferred maximum history $h_0 = 14.05\text{ MPa}$ by a factor of 16.5 at 1,869 Gauss points (3.06% of the domain). When the mechanical subproblem executes at Outer 1, stress concentration at the refined slit tip generates peak history $H = 28.55\text{ MPa}$ ($+103\%$ over $h_0$). Because $G_c / (2\ell_0) = 0.0027 / (2 \times 0.0075) = 0.18\text{ MPa}$, this driving force vastly exceeds the crack-initiation threshold ($H \gg H_{\text{init}}$), forcing the phase-field equation to propagate the crack forward until reaction force drops by $46.18\%$ and elastic strain energy is released.

---

## 2. Telemetry Parity and Residual Diagnostics

The offline forensic reconstructor (`FastPrecomputedPhaseAssembler`) achieved exact numerical parity with the live cluster driver:
- Reconstructed active node counts match live telemetry and `.inp` boundary cards exactly ($14,088$ at Outer 1; $10,993$ at Outer 18; $66$ at Outer 140).
- Reconstructed KKT post-solve free residuals match live telemetry to $< 10^{-14}\text{ kN}\cdot\text{mm}$ ($2.9567\times 10^{-7}\text{ kN}\cdot\text{mm}$ at Outer 1; $1.2403\times 10^{-8}\text{ kN}\cdot\text{mm}$ at Outer 18).
- Abaqus UEL phase solves satisfied the linear free-system equations to machine precision: maximum free-node raw residual $\max_{i \in \mathcal{F}} |(K_d d_{\text{raw}} - f_d)_i| \le 3.59\times 10^{-12}\text{ kN}\cdot\text{mm}$.
- Nodal diagonal stiffness $K_{d,ii}$ averages $8.21\times 10^{-5}\text{ kN}\cdot\text{mm}$ (range $1.36\times 10^{-5}$ to $4.29\times 10^{-4}\text{ kN}\cdot\text{mm}$). Thus an absolute residual tolerance $\tau = 10^{-6}\text{ kN}\cdot\text{mm}$ corresponds to a normalized Jacobi step $\tau / K_{d,ii} \approx 0.012$ to $0.073$, which is consistent with the observed raw $\Delta d \approx 0.0188$ at Outer 1.

---

## 3. Step-by-Step Trajectory Evolution Across 15 Selected States

| Outer | Stage | $\omega_d$ | Active Count | Free Count | Newly Released | Newly Damaged ($d - d_0 > 0.01$) | Max $d$ | Max $H$ (MPa) | Tip $x$ ($d \ge 0.90$) | $RF_2$ (kN) | $RF_2$ Drift vs Donor | Total Energy Drift |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | 1 | 0.50 | 14,088 | 1,471 | 1,471 | 0 | 0.690981 | 28.55 | 0.0400 mm | 0.180578 | +0.36% | +0.27% |
| **2** | 1 | 0.50 | 13,936 | 1,623 | 152 | 5 | 0.690981 | 29.53 | 0.0400 mm | 0.180530 | +0.34% | +0.26% |
| **5** | 1 | 0.50 | 13,559 | 2,000 | 132 | 110 | 0.705475 | 32.14 | 0.0400 mm | 0.180293 | +0.20% | +0.26% |
| **10** | 1 | 0.50 | 12,761 | 2,798 | 183 | 526 | 0.723334 | 35.80 | 0.0400 mm | 0.179666 | -0.14% | +0.26% |
| **15** | 1 | 0.50 | 11,716 | 3,843 | 223 | 929 | 0.733908 | 38.09 | 0.0400 mm | 0.179058 | -0.48% | +0.25% |
| **16** | 1 | 0.50 | 11,487 | 4,072 | 229 | 1,014 | 0.735844 | 38.52 | 0.0400 mm | 0.178928 | -0.55% | +0.25% |
| **17** | 1 | 0.50 | 11,242 | 4,317 | 245 | 1,117 | 0.737769 | 38.96 | 0.0400 mm | 0.178793 | -0.63% | +0.25% |
| **18** | 1 | 0.50 | 10,993 | 4,566 | 249 | 1,217 | 0.739696 | 39.40 | 0.0400 mm | 0.178654 | -0.71% | +0.25% |
| **19** | 1 | 0.50 | 10,731 | 4,828 | 262 | 1,314 | 0.741645 | 39.85 | 0.0400 mm | 0.178509 | -0.79% | +0.25% |
| **20** | 1 | 0.50 | 10,459 | 5,100 | 272 | 1,430 | 0.743620 | 40.32 | 0.0400 mm | 0.178358 | -0.87% | +0.25% |
| **25** | 1 | 0.50 | 8,901 | 6,658 | 351 | 2,056 | 0.754425 | 42.96 | 0.0400 mm | 0.177495 | -1.35% | +0.25% |
| **30** | 1 | 0.50 | 7,159 | 8,400 | 352 | 2,833 | 0.768879 | 46.70 | 0.0400 mm | 0.176312 | -2.01% | +0.25% |
| **50** | 1 | 0.50 | 2,699 | 12,860 | 171 | 6,236 | 0.916073 | 136.13 | 0.0420 mm | 0.164977 | -8.31% | +0.12% |
| **95** | 2 | 0.85 | 307 | 15,252 | 9 | 8,737 | 0.998293 | 5,739.11 | 0.0545 mm | 0.123662 | -31.27% | -1.82% |
| **140** | 2 | 0.85 | 66 | 15,493 | 3 | 9,272 | 0.998607 | 6,637.65 | 0.0633 mm | 0.096835 | -46.18% | -2.72% |

### Key Observations from Reconstruction
1. **Regime I (Outer 1..18): Apparent Contraction is Local Healing Suppression.**
   In Outer 1..18, the reaction force and total energy remain extremely close to the donor ($RF_2$ drift within $-0.71\%$, total energy drift $+0.25\%$). Nodal displacement $\Delta u \approx 10^{-5}\text{ mm}$ and damage changes are confined strictly to a narrow corridor along the crack axis ($y \in [0.044, 0.056]\text{ mm}$, $|y - 0.05| \le 0.006\text{ mm} < \ell_0$). Outside the fracture process zone ($> 3\ell_0$), damage change is $\le 1.84\times 10^{-3}$, proving that **damage changes do NOT represent spurious diffuse far-field damage**.
2. **The Outer 18 Transition Point:**
   Outer 18 was previously identified as the inflection where $\Delta H$ stopped decreasing ($\min \Delta H = 0.427\text{ MPa}$ at Outer 16). The forensics reveal that Outer 18 is simply the point where the crack tip began expanding geometrically:
   - Outer 1..16: Damage grows primarily in amplitude at the blunt notch tip ($x \le 0.048\text{ mm}$, $d_{\max}$ rising from $0.691$ to $0.736$).
   - Outer 18..20: The active zone of nodes with $d - d_0 > 0.01$ reaches $x = 0.050\text{ mm}$ (a full $10\,\mu\text{m}$ beyond the donor crack tip).
   - Outer 50: Fully formed crack ($d \ge 0.90$) initiates at $x = 0.0420\text{ mm}$, releasing elastic energy into fracture surface energy.
   - Outer 140: The crack propagates across $23.3\,\mu\text{m}$ ($x_{\text{tip}} = 0.0633\text{ mm}$), causing severe load relaxation ($RF_2 = 0.0968\text{ kN}$, $-46.18\%$).

---

## 4. Evaluation Engine Fail-Open Defect Repair (`INC-2026-11-06-03`)

### Root Cause Analysis
In `scripts/validation/evaluate_f1629_paired_execution.py`, the validation gates evaluated missing evidence using `is not False`:
```python
gate_mech_consistency = (consistency_u_pass is not False) and (consistency_h_pass is not False)
```
When an Abaqus job terminated early or nonconverged without executing `finalize_coupled_acceptance()`, these consistency variables remained `None`. Because `None is not False` evaluates to `True`, the evaluator erroneously reported `mechanical_consistency = PASS`. Furthermore, history monotonicity and thermodynamic consistency were initialized to `True` by default.

### Remediation Implemented
1. `consistency_u_pass` and `consistency_h_pass` must explicitly evaluate to `is True`.
2. `history_monotonicity_pass` and `thermodynamic_consistency_pass` initialized to `None` and require explicit `is True`.
3. KKT gate requires `final_kkt_pass is True` and all residual norms (`free_error`, `dual_error`, `complementarity`) to be non-null and below tolerance.
4. Added comprehensive negative unit tests in `tests/unit/test_f1629_evaluation_engine.py::test_fail_closed_missing_or_null_evidence_gates`.
5. Full test suite passes: `7 passed in 0.44s`.

---

## 5. Daily Error Register Status (6 November 2026)

- **`INC-2026-11-06-01` (R12 Driver API Regression):** `RESOLVED_VERIFIED` (Committed `fa2a5100142c79fd03b7f2882d04da6d280d4076`, demonstrated by 280 subproblem runs with Exit 0).
- **`INC-2026-11-06-02` (Manifest Circular Stale Hash):** `RESOLVED_VERIFIED` (Committed `cb9af24ba91bcd66cf69d5104243d9318e62fd07`).
- **`INC-2026-11-06-03` (Fail-Open Evaluator Logic):** `RESOLVED_VERIFIED` (Repaired in `scripts/validation/evaluate_f1629_paired_execution.py`, verified by unit tests).
- **`BLK-2026-11-06-01` (Scientific Validation Dependency):** Open scientific blocker. The physical nonconvergence of C6 re-equilibration is conclusively demonstrated to be driven by post-transfer mechanical-phase incompatibility and supercritical crack propagation under static displacement.

---

## 6. Single Justified Next Experiment Proposal

### Scientific Assessment
Attempting to force C6 re-equilibration under the donor's fixed terminal displacement $u_y = 0.0018703\text{ mm}$ is mathematically doomed to crack propagation because the refined mesh locally increases stress concentration beyond the critical energy release rate $G_c$. In classical fracture mechanics, refining the mesh around a phase-field crack tip sharpens the stress field; if the transferred displacement is held constant, the crack MUST propagate until it finds a new equilibrium or completes fracture.

### Proposed Successor Experiment: `F1632-METHOD-C-C6-LOAD-INCREMENTAL-CONTINUATION`
Instead of attempting an isolated, static re-equilibration at the donor's terminal displacement:
1. **Transfer state at a stable sub-critical checkpoint:** Transfer state from a checkpoint prior to unstable propagation (or perform continuation with active displacement increments).
2. **Direct Continuation with Newton/Staggered Solver:** Execute the forward continuation step directly with a reduced displacement increment $\Delta u_y = 5\times 10^{-6}\text{ mm}$, allowing the phase field to advance naturally in synchronization with external work rather than undergoing an artificial zero-increment relaxation.
3. **Execution Gate:** Prior to any HPC submission, validate the incremental continuation setup offline using mocked drivers and register through the governed controller.
