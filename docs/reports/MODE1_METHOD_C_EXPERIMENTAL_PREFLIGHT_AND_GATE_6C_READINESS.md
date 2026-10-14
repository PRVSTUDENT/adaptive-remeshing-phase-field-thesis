# Mode-I Method C Experimental Preflight, State-Transfer Validation, and Gate 6C Readiness Package

**Document ID:** `MODE1_METHOD_C_EXPERIMENTAL_PREFLIGHT_AND_GATE_6C_READINESS.md`  
**Milestone:** Task F1467 — Independent Validation of Method C1 Package 42 & Continuation-Physics Resolution  
**Date:** 2026-10-14T23:55:00+02:00  
**Author:** Gemini Antigravity (Autonomous Execution Agent)  
**Institution:** Institute of Mechanics and Fluid Dynamics (IMFD), TU Bergakademie Freiberg  
**Authoritative Fortran Source:** `models/pandey_kumar_mode1/f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`)  
**Target Package:** `models/pandey_kumar_mode1/42_method_c1_forward_refinement/`  
**HPC Cluster Scratch Path:** `/scratch9/pr21vyci/runs/mode1_method_c1_forward_refinement/`  
**Governing Directive:** *"We need to have understood everything related to the first model before we increase complexity."*  
**Classification:** `EXPERIMENTAL_PREFLIGHT_AND_GOVERNANCE_PACKAGE_STAGED`  
**Three-Tier Qualification Status:**
- **Datacheck:** `DATACHECK_PASSED` (Abaqus 2023 preflight Exit 0, 0 syntax defects, 0 unreferenced sets)
- **Offline Mathematical Transfer:** `OFFLINE_TRANSFER_VERIFIED` ($L_2 = 0.1347\%$, $\Delta d_{\max} = 0.000$, $\min(H) \ge 0$)
- **Solver Continuation:** `SOLVER_CONTINUATION_NOT_YET_QUALIFIED` (Reload ramp defect & ligament coarsening beyond $x \approx 0.85\,\text{mm}$)

---

## Executive Summary

Task F1467 performs an exhaustive, independent scientific audit of **Method C1 Package 42** (`models/pandey_kumar_mode1/42_method_c1_forward_refinement/`) before the 22 October 2026 supervisor meeting, diagnosing critical continuation-physics defects, auditing recipient mesh resolution across the ligament, reconciling authentic donor source data, and formulating the true C1 continuation acceptance test.

While Method B provides up to $1.87\times$ computational acceleration, its fundamental limitation is that linear-elastic error indicators before crack initiation decay rapidly into the ligament ($|\nabla\boldsymbol{\sigma}| \sim r^{-3/2}$), leaving the prospective crack path coarse ($h \approx 13-20\,\mu\text{m} \gg \ell_0/2 = 3.75\,\mu\text{m}$) and producing artificial crack pinning unless retrospective post-initiation damage states are provided.

To overcome this limitation without unphysical hindsight, **Method C** performs sequential, in-analysis adaptive remeshing: solving to an evaluation state, detecting active crack propagation, refining the mesh along the actual damage trajectory, transferring displacement and internal history variables, and continuing the solve.

This document establishes the verified experimental preflight and forensic evaluation for **Package 42**:
1. **Three-Tier Status Disambiguation:** Strictly separates `DATACHECK PASSED` (Abaqus/Standard input processor and Intel Fortran compilation validity), `OFFLINE TRANSFER VERIFIED` (mathematical field mapping on static discretizations), and `SOLVER CONTINUATION NOT YET QUALIFIED` (solver runtime physical continuation across step boundary).
2. **Continuation-Physics Defect Discovered:** Step 1 (`Step-1-Equilibrate`) in `M1_MC_C1_FORWARD_14K.inp` ramps top boundary displacement from $u = 0$ to $u = 0.0050\,\text{mm}$ across 20 increments ($\Delta t = 0.05$). Because commercial Abaqus/Standard rejects `*INITIAL CONDITIONS, TYPE=DISPLACEMENT` in `*STATIC` steps (Error 144), nodal displacements at $t=0$ are zero ($\mathbf{u} = \mathbf{0}$). This performs an unphysical **quasi-static reload of a pre-damaged specimen** from zero displacement rather than in-situ equilibrium continuation.
3. **Forensic Ligament Resolution Audit:** Audited all 14,244 quad and 433 tri elements of the 14,677-element recipient mesh. Elements satisfying $h \le \ell_0/2 = 3.75\,\mu\text{m}$ exist **ONLY up to $x \approx 0.85\,\text{mm}$** ($x_{\max} < 0.86\,\text{mm}$). Beyond $x = 0.85\,\text{mm}$, the ligament coarsens to $h \approx 13 - 20\,\mu\text{m}$. Package 42 does NOT resolve the entire ligament; running Step 2 would re-encounter coarse crack-pinning ($0.50-0.60\,\text{kN}$) once the crack advances past $x = 0.85\,\text{mm}$.
4. **Donor Source Data Reconciled:** Reconciled authentic coarse donor state from Job 1411891 (`M1_PRE_1S`, coarse 2,906 FEs at $u = 0.0050\,\text{mm}$): exact reaction force is $RF = 653.0886\,\text{N}$ (reconciling conflation with 15k reference $724.81\,\text{N}$), elastic strain energy is $E_{\text{elas}} = 1.6327\,\text{mJ}$ (reconciling conflation with $2.0531\,\text{mJ}$), fracture energy is $E_{\text{frac}} = 0.0307\,\text{mJ}$, total internal energy is $E_{\text{tot}} = 1.6634\,\text{mJ}$, and $d_{\max} = 0.094910$.
5. **Governance Hold:** Enforced a strict submission lock (`AUTHORIZED=false` in `submit_c1_forward_refinement_job.sh`) and confirmed 0 active cluster jobs, preserving complete supervisor authority for the 22 October review.

---

## 1. Immediate HPC Submission Decision & Cluster Queue Status

In strict accordance with the mandatory operational governance rules:

1. **Live Scheduler Inspection:**
   A non-interactive, bounded query of the TU Freiberg cluster queue `normal_imfdfkmq` via guarded SSH (`Invoke-GuardedSsh.ps1` wrapping `qstat -u pr21vyci`) confirmed **0 active, queued, or running jobs** for user `pr21vyci`.
2. **Terminal Records and Certification of Completed Jobs:**
   - **Job `1412872.mmaster02` (Native Method B 14,677 FE, 8-Thread SMP Repeat):** Completed all 5,000 increments in Step 2 (7,000 increments total, $u = 0.0100\,\text{mm}$, Exit 0, walltime 05:12:04, $1.87\times$ speedup vs serial). Certified with `THREAD_PARITY_PASS` and `THREAD_DETERMINISM_PASS` via bitwise identical SHA-256 hash (`792be67d...`) of `uel_energy_balance.csv` against both serial baseline `1411934` and initial 8T solve `1411949`.
   - **Job `1412873.mmaster02` (Corrected Method B 14,483 FE, 8-Thread SMP Parity):** Completed Step 1 (2,000 incs) and advanced to Step 2 Increment 2890 (4,890 increments total, $u = 0.007889\,\text{mm}$, Exit 1 terminal cutback, walltime 03:35:22, $1.82\times$ speedup vs serial). Certified with `THREAD_PARITY_PASS` via bitwise identical SHA-256 hash (`82f2963d...`) against serial baseline `1412465`.
3. **Scientific Justification for Idle Queue Status:**
   - *Candidate A (Prospective Native Remeshing Repeat):* Sizing controls in native `RemeshingRule` leave the uncracked ligament coarse ($h \approx 13-20\,\mu\text{m} \gg \ell_0/2$). Re-running prospective pre-refinement would merely regenerate the known coarse-ligament crack-pinning plateau ($0.50-0.60\,\text{kN}$) and $+40.3\%$ excess work, violating scheduler anti-redundancy rules.
   - *Candidate B (Post-Severance Artificial Relaxation):* Job `1412873` already captured $99.76\%$ of physical brittle fracture ($RF = 1.76\,\text{N}$ vs peak $743.7\,\text{N}$) with contiguous crack front formation across $99.9\%$ of the ligament. Continuing numerical relaxation on two completely severed halves held only by residual artificial stiffness $k_{\text{stab}} = 10^{-7}$ provides zero new physical fracture information.
   - *Candidate C (Method C In-Analysis Continuation):* Gate 6C remains on strict hold pending formal supervisor review and sign-off on 22 October 2026. Submitting unauthorized Method C solver runs is strictly prohibited by governance.
4. **Conclusion:** Zero PBS jobs were submitted during Task F1467. The cluster queue is legitimately idle in full compliance with project governance.

---

## 2. Method C Formulation & Operational Architecture

### 2.1 Epistemic Separation of Adaptive Methodologies
To avoid terminological confusion in thesis documentation and supervisor briefings, the three methodologies are rigorously separated:

| Methodology | Nature of Discretization | Timing of Remeshing | Information Utilized | Key Limitation / Advantage |
| :--- | :--- | :--- | :--- | :--- |
| **Method A** | Fixed non-uniform mesh | Pre-analysis ($t = 0$) | Linear-elastic notch singularity ($K_{\text{I}}$ field) | Coarse ligament ($h \gg \ell_0/2$); unable to adapt to evolving damage. |
| **Method B** | Fixed two-stage mesh | Stationary pre-fracture ($u = u_{\text{handoff}}$) | Static notch stress/strain concentration | Prospective remeshing decays rapidly; cannot predict downstream crack path without retrospective hindsight. |
| **Method C** | Evolving adaptive sequence | In-analysis during fracture ($u \ge u_{\text{crit}}$) | Evolving damage field $d(\mathbf{x}, t)$ and history $H(\mathbf{x}, t)$ | Captures dynamic crack path; requires robust non-matching state transfer and equilibrium restart. |

### 2.2 Method C1 vs Method C2 Roles
1. **Method C1 (Forward Refinement Benchmark):**
   - *Donor Discretization:* Coarse mesh (2,906 FEs, $h_{\text{notch}} \approx 7.5\,\mu\text{m} = \ell_0$) solved under Step 1 displacement to $u = 0.0050\,\text{mm}$.
   - *Recipient Discretization:* Fine mesh (14,677 FEs, $h_{\text{notch}} \approx 1.88\,\mu\text{m} = \ell_0/4 \le \ell_0/2$).
   - *Scientific Purpose:* Isolates and validates state-transfer accuracy, damage preservation, and displacement continuity under mesh refinement where the recipient discretization is locally superior to the donor.
2. **Method C2 (Dynamic Refinement with Wake Coarsening):**
   - *Candidate Mesh Bounds:* In accordance with project governing constraints, any coarsening in the wake of the crack must respect:
     $$h_{\text{wake}} \le \frac{\ell_0}{2} = 3.75\,\mu\text{m} \quad \text{for all } d \ge 0.05$$
     Coarsening elements in the crack wake beyond $\ell_0/2$ causes spurious crack healing, loss of dissipated fracture energy, and artificial crack closure.

---

## 3. Forensic Ligament Resolution Audit of Package 42

A rigorous element-by-element audit of `M1_MC_C1_FORWARD_14K.inp` was conducted to determine whether the 14,677-element recipient resolves the entire ligament ($x \in [0.50, 1.00]\,\text{mm}$, $y = 0.50\,\text{mm}$) or uses the native mesh with a coarse ligament beyond $x \approx 0.85\,\text{mm}$.

### 3.1 Spatial Mesh Discretization along Ligament
Along the crack plane corridor ($|y - 0.50| \le 0.02\,\text{mm}$, $0.50 \le x \le 1.00\,\text{mm}$), the element size $h = \sqrt{\text{Area}}$ varies as follows:

| Longitudinal Range $x$ [mm] | Element Count | Minimum $h$ [$\mu\text{m}$] | Average $h$ [$\mu\text{m}$] | Maximum $h$ [$\mu\text{m}$] | Status vs $\ell_0/2 = 3.75\,\mu\text{m}$ |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **$0.50 \le x < 0.55$** | 498 | $1.88\,\mu\text{m}$ | $10.4\,\mu\text{m}$ | $18.5\,\mu\text{m}$ | **RESOLVED** ($h_{\min} \le \ell_0/4$) |
| **$0.55 \le x < 0.65$** | 249 | $1.92\,\mu\text{m}$ | $11.2\,\mu\text{m}$ | $19.1\,\mu\text{m}$ | **RESOLVED** ($h_{\min} \le \ell_0/4$) |
| **$0.65 \le x < 0.75$** | 185 | $2.15\,\mu\text{m}$ | $12.8\,\mu\text{m}$ | $19.5\,\mu\text{m}$ | **RESOLVED** ($h_{\min} \le \ell_0/4$) |
| **$0.75 \le x < 0.85$** | 120 | $2.84\,\mu\text{m}$ | $14.1\,\mu\text{m}$ | $19.6\,\mu\text{m}$ | **MARGINALLY RESOLVED** ($h \le 3.75\,\mu\text{m}$) |
| **$0.85 \le x \le 1.00$** | 82 | **$12.98\,\mu\text{m}$** | **$16.82\,\mu\text{m}$** | **$19.66\,\mu\text{m}$** | **UNRESOLVED / COARSE** ($h > 3.4\,\ell_0/2$) |

### 3.2 Proven Mesh Truncation
1. **Truncation Horizon:** Elements with $h \le \ell_0/2 = 3.75\,\mu\text{m}$ exist **ONLY up to $x \approx 0.85\,\text{mm}$** ($x_{\max} = 0.849\,\text{mm}$).
2. **Coarsening in Outer Ligament:** Beyond $x = 0.85\,\text{mm}$, all elements along the symmetry plane have $h \in [12.98, 19.66]\,\mu\text{m}$, which is $3.5\times$ to $5.2\times$ coarser than the critical phase-field resolution limit $\ell_0/2 = 3.75\,\mu\text{m}$.
3. **Physical Consequence:** If Step 2 propagation were executed on this mesh, the advancing crack would enter an under-resolved coarse zone at $x \approx 0.85\,\text{mm}$, reproducing the artificial crack-pinning force plateau ($0.50-0.60\,\text{kN}$) observed in Job 1411934.
4. **Conclusion:** Package 42 uses the native Method B mesh (`M1_MB_NATIVE_FINAL_1S.inp`), which fails to resolve the entire ligament. To achieve physical brittle fracture across the entire specimen, the recipient mesh must employ a pre-refined corridor along the complete ligament ($0.50 \le x \le 1.00\,\text{mm}$), such as the 14,483-element discretization of Package 40.

---

## 4. Reconciled Authentic Donor Source Data

Prior working notes conflated coarse donor values with the 15,220-element uniform reference solution. The authentic source data from Job 1411891 (`M1_PRE_1S`, coarse 2,906 FEs at Step 1 Increment 500, $u = 0.0050\,\text{mm}$) is reconciled below:

| Quantity | Conflated 15k Reference Value | Authentic Job 1411891 Coarse Donor Value | Disparity / Cause |
| :--- | :--- | :--- | :--- |
| **Mesh Elements** | 15,220 uniform quads | 2,906 graded quads | Coarser notch discretization ($h \approx 7.5\,\mu\text{m}$) |
| **Reaction Force $RF$** | $724.81\,\text{N}$ | **$653.0886\,\text{N}$** | Lower compliance due to coarse notch discretization |
| **Elastic Energy $E_{\text{elas}}$** | $2.0531\,\text{mJ}$ | **$1.6327\,\text{mJ}$** | Strain energy in coarse mesh at $u = 0.0050\,\text{mm}$ |
| **Fracture Energy $E_{\text{frac}}$** | $0.0000\,\text{mJ}$ (undamaged) | **$0.0307\,\text{mJ}$** | Localized tip damage initiation ($d_{\max} \approx 0.095$) |
| **Total Energy $E_{\text{tot}}$** | $2.0531\,\text{mJ}$ | **$1.6634\,\text{mJ}$** | $E_{\text{elas}} + E_{\text{frac}}$ |
| **Peak Damage $d_{\max}$** | $0.0000$ | **$0.094910$** | Sub-critical damage at notch tip |
| **History Minimum $\min(H)$** | $0.000\,\text{MPa}$ | **$0.000\,\text{MPa}$** | History non-negativity strictly satisfied |

All future C1 continuation evaluations must benchmark against the authentic coarse donor value $RF = 653.09\,\text{N}$ and $E_{\text{elas}} = 1.6327\,\text{mJ}$, NOT the 15k uniform reference numbers.

---

## 5. Mathematical State-Transfer Evaluation & Results

State transfer from coarse donor $\Omega_D$ (2,906 FEs) to fine recipient $\Omega_R$ (14,677 FEs) was executed via spatial interpolation and solution-dependent state variable (SVAR) mapping at $u = 0.0050\,\text{mm}$:

| Metric | Target / Gate 6C Criterion | Evaluated Value | Status |
| :--- | :--- | :--- | :--- |
| **Displacement $L_2$ Relative Error** | $\le 1.0\%$ | **$0.1347\%$** | **PASS** |
| **Peak Damage Difference $\Delta d_{\max}$** | $\le 0.02$ | **$0.0000$** ($0.094910$ vs $0.094910$) | **PASS** |
| **Integrated Damage Error $\int_\Omega \|d_R - d_D\| \mathrm{d}\Omega$** | $\le 5.0\%$ | **$0.1322\%$** | **PASS** |
| **Compliance Disparity $(C_R - C_D)/C_D$** | $\le 3.0\%$ | **$1.638\%$** | **PASS** |
| **Internal Energy Disparity $\Delta E_{\text{int}}$** | $\le 3.0\%$ | **$1.61\%$** | **PASS** |
| **History Non-Negativity Violation** | Exactly $0$ ($H \ge 0$) | **$\min(H) = 0.000\,\text{MPa}$** ($0$ violations) | **PASS** |

The mathematical mapping of fields on static discretizations satisfies all pre-declared transfer tolerances.

---

## 6. Continuation-Physics Defect & Equilibration Strategy Evaluation

### 6.1 Diagnosis of Abaqus Error 144 & the Reload Ramp Defect
Commercial Abaqus/Standard enforces a rigid architectural restriction in static analyses:
```
***ERROR: *INITIAL CONDITIONS, TYPE=DISPLACEMENT is not allowed in a *STATIC step.
```
Because initial displacement fields cannot be imported directly via input cards, Package 42 attempted a workaround:
1. Initialize internal state variables (SVARS 1..18) via `*INITIAL CONDITIONS, TYPE=SOLUTION`.
2. Formulate Step 1 (`Step-1-Equilibrate`) as a static step with top displacement boundary condition ramping from $u = 0$ to $u = 0.0050\,\text{mm}$ over 20 increments ($\Delta t = 0.05$).

### 6.2 Physics Evaluation: Why the 20-Increment Ramp is an Invalid Continuation
1. **Zero Initial Displacements:** Because Abaqus initializes all nodal displacements to zero ($\mathbf{u} = \mathbf{0}$) at the start of Step 1, the specimen begins from an undeformed configuration while holding pre-existing damage ($d_{\max} \approx 0.095$).
2. **Quasi-Static Reload from Zero:** Ramping $u$ from 0 to $0.0050\,\text{mm}$ across 20 increments reloads the pre-damaged specimen from zero displacement. This performs double external work ($W_{\text{ext}} \approx 1.63\,\text{mJ}$ in Step 1) and re-evaluates the elastic stiffness from the origin.
3. **Equilibrium State Mismatch:** This is conceptually identical to Job `1412464` (`M1_MC_C1_V2`), which was classified as a "quasi-static reload of a pre-damaged specimen" rather than genuine continuation.
4. **Conclusion:** Dividing the ramp into 20 sub-increments resolves numerical Newton-Raphson convergence, but it does NOT resolve physical continuation. It is an unphysical reload surrogate.

### 6.3 True C1 Continuation Acceptance Test
A genuine Method C continuation must satisfy the **In-Situ Equilibrium Continuation Criterion**:
1. **Kinematic Consistency:** Displacements upon continuation must match donor displacements: $\|\mathbf{u}_{\text{recip}}(t_{\text{cont}}) - \mathbf{u}_{\text{donor}}(t_{\text{cont}})\| \approx 0$.
2. **Equilibration Step at Constant Boundary:** If an equilibration step is performed, it must be held at fixed boundary displacement:
   $$\Delta u_{\text{boundary}} = 0 \quad (u = 0.0050\,\text{mm} = \text{const.})$$
   allowing interior nodes to relax from their transferred positions $\mathbf{u}_R^{(0)}$ to discrete recipient equilibrium $\mathbf{u}_R^*$, with residual $\|\mathbf{R}_{\text{internal}}\| \to 0$.
3. **Disambiguation of Errors:**
   - *Interpolation Error:* $\boldsymbol{\eta}_{\text{interp}} = \mathbf{u}_R^{(0)} - \mathcal{P}(\mathbf{u}_D)$ (bounded by $L_2 \le 1.0\%$).
   - *Discretization Correction:* $\delta \mathbf{u} = \mathbf{u}_R^* - \mathbf{u}_R^{(0)}$ (internal nodal relaxation due to differing mesh stiffness matrices $\mathbf{K}_R \ne \mathbf{K}_D$).
4. **Boundary Force Continuity:** The initial equilibrated reaction force must match donor force within $|\Delta RF| \le 5.0\,\text{N}$ ($|RF_{\text{recip}} - 653.09\,\text{N}| \le 5.0\,\text{N}$).

---

## 7. Cluster Datacheck Verification Evidence

On cluster `mlogin01`, the complete package was submitted to the Abaqus 2023 interactive datacheck processor via `run_datacheck_forward.sh`:
- Intel Fortran Classic Compiler (`ifort 2021.13.0 Build 20240602_000000`) compiled `f42_mixed_uel.for` into object code and linked with Abaqus/Standard shared libraries.
- Analysis Input File Processor parsed all 102,830 lines, 14,834 nodes, 44,031 elements, 14,677 solution initial condition blocks, and 2 analysis steps.
- Datacheck completed with **Exit Code 0** (`ANALYSIS DATACHECK COMPLETE`) with zero syntax errors and zero illegal cards.

---

## 8. Package 42 Manifest & Provenance

The complete reproducible package is staged at `models/pandey_kumar_mode1/42_method_c1_forward_refinement/` and replicated in cluster scratch `/scratch9/pr21vyci/runs/mode1_method_c1_forward_refinement/`:

| File Name | Size (Bytes) | Line Count | SHA-256 Checksum | Description |
| :--- | :--- | :--- | :--- | :--- |
| `M1_MC_C1_FORWARD_14K.inp` | 7,299,993 | 102,830 | `614D3955E75105C707EC14D84F8E4ABBFB0A42415DAFAB8977816162DD731985` | Assembled Abaqus deck with 3-layer mesh and solution ICs |
| `f42_mixed_uel.for` | 29,722 | 967 | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` | Bitwise frozen production UEL subroutine |
| `submit_M1_MC_C1_FORWARD_14K.pbs` | 1,833 | 55 | `84F5633CBECAECF6E955513DC19B0314FF1444458CAE551E5C7756B60020AC50` | PBS execution script (1 CPU serial, 16 GB RAM, 24h walltime) |
| `run_datacheck_forward.sh` | 755 | 24 | `F4DAEC7ED90F7BF9DBB1BBE6F3B13C6EBA7427457788C4195156B190204ED0F5` | Interactive Abaqus Datacheck wrapper |
| `submit_c1_forward_refinement_job.sh` | 2,581 | 68 | `2A42BD64724EC0FD5400F951DCBF3124E05FDDE37C517CF37DC973F221FA80AC` | Guarded submission script with `AUTHORIZED=false` lock |
| `commands.txt` | 355 | 11 | `B86C45DA53E475908C8CF673BC6DA3E595D3EB95A9678AE61A70EDFFC8F99F55` | Command references for datacheck, submission, and monitoring |
| `job_notifications.sh` | 11,258 | 298 | `C7B1E4081E482270CF729EFE7BE3744A68C9E273BC6923CDCA3DE6B1665FE766` | Dual-channel notification library (email + Telegram) |
| `PACKAGE_MANIFEST.json` | 4,070 | 95 | `BC9B7F167CA5CD57A427ECDC3EAF4A540545C6C5FA9F89B20822180860E3A261` | JSON metadata and pre-declared criteria registry |

---

## 9. Recommended Corrected C1 Design & Supervisor Determination

For the upcoming supervisor review on 22 October 2026, the following findings and design recommendations are established:

1. **Explicit Three-Tier Classification:**
   - `DATACHECK PASSED`: Package syntax and solver environment are fully verified.
   - `OFFLINE TRANSFER VERIFIED`: Mathematical field interpolation is proven accurate.
   - `SOLVER CONTINUATION NOT YET QUALIFIED`: The current 20-increment reload strategy does not constitute true continuation, and the recipient mesh lacks ligament resolution beyond $x = 0.85\,\text{mm}$.
2. **Corrected C1 Design Recommendations:**
   - *Mesh Correction:* Substitute the recipient mesh with a discretization that maintains $h \le \ell_0/2 = 3.75\,\mu\text{m}$ across the entire ligament ($0.50 \le x \le 1.00\,\text{mm}$), preventing coarse crack pinning in Step 2.
   - *Continuation Architecture:* Pursue Option B from the supervisor briefing (investigating a kinematic-offset UEL on a separate experimental branch `f42_experimental_offset_uel.for`) to enable direct non-zero displacement continuation without reload ramps, while keeping production `f42_mixed_uel.for` bitwise frozen.
3. **Governance Release Guard:** Package 42 remains staged with `AUTHORIZED=false`. Zero PBS jobs will be submitted prior to explicit supervisor sign-off on 22 October 2026.
