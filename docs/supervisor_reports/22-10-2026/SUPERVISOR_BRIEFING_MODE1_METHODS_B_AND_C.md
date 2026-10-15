# Mode-I Adaptive Remeshing Methods B & C: Unified Synthesis & Supervisor Briefing

**Document ID:** `SUPERVISOR_BRIEFING_MODE1_METHODS_B_AND_C.md`  
**Milestone:** Master's Thesis Progress Review â€” Thursday, 22 October 2026 (10:00 CEST)  
**Author:** Pruthviraja Reddy Vandavagali (Matriculation No. 68865)  
**Institution:** Institute of Mechanics and Fluid Dynamics (IMFD), TU Bergakademie Freiberg  
**Authoritative Fortran Source:** `f42_mixed_uel.for` (SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`)  
**Governing Directive:** *"We need to have understood everything related to the first model before we increase complexity."*  
**Operational Status:** `METHODS_B_AND_C_SCIENTIFICALLY_EVALUATED_READY_FOR_SUPERVISOR_REVIEW`  

---

## Immediate HPC Submission Decision & Cluster Queue Status

**Mandatory Governance Review & Active HPC Execution:** In accordance with the supervisor-aligned directive and HPC-First protocol ("Do not leave the cluster idle; formulate and run a scientifically justified, qualified Mode-I experiment before reporting"), a high-priority computational sensitivity study was submitted and is actively running:

- **Active PBS Job:** `1413217.mmaster02` (`M1_MB_DTMIN_8T`)
- **Queue & Placement:** Queue `normal_imfdfkmq` on compute node `mnode097/0*8` (single-rank shared-memory SMP: 8 CPUs, 24 GB RAM, 24h walltime).
- **Execution Mode:** 8-thread shared-memory SMP (`mp_mode=threads`), fully qualified under Stage A/B testing (`THREAD_PARALLELIZATION_QUALIFIED`).
- **Input Deck & Subroutine Hashes:**
  - Deck (`M1_MB_CORRECTED_DTMIN_14K.inp`): `E154264600B381BA9DFD23CAAD0635088A7B4075367E27F6B85B2951DAB03B40`
  - Authoritative Production Subroutine (`f42_mixed_uel.for`): `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` (100% frozen, zero unauthorized alterations).
  - PBS Script (`submit_M1_MB_DTMIN_8T.pbs`): `4CEE7F124DDACB1E7A5FB9415E260127EFC7149EBF22FC904300C6A7581F0137`
- **Preflight & Datacheck:** Full interactive Abaqus 2023 datacheck executed with `ANALYSIS COMPLETE` (Exit Code 0).
- **Scientific Hypothesis & Investigation Scope:**
  - *Retrospective Package 40 Completion Sensitivity:* Jobs 1412465, 1412873, and 1413022 on the 14,483 FE mesh successfully resolved the entire fracture softening curve down to $RF = 1.76\,\text{N}$ ($99.76\%$ drop from $F_{\max} = 743.7\,\text{N}$), but encountered cutback exhaustion (`***ERROR: TIME INCREMENT REQUIRED IS LESS THAN THE MINIMUM SPECIFIED`) at Step 2 Increment 2890 ($u = 0.007889\,\text{mm}$) when 10 consecutive cutbacks were clamped at $dt_{\min} = 1.0\times 10^{-9}$.
  - *Investigation:* Package 43 reduces the minimum solution increment to $dt_{\min} = 1.0\times 10^{-15}$ (`*STATIC, 2.0E-4, 1.0, 1.0E-15, 2.0E-4`) to test whether the solver can traverse the steep post-severance transition and continue toward the requested endpoint $u = 0.0100\,\text{mm}$, while establishing exact response parity over the previously solved interval $[0.0, 0.007889]\,\text{mm}$.
- **Prior Queue State & Transition:** Prior to submitting Job 1413217.mmaster02, verified 0 active, queued, or running jobs for user `pr21vyci` in cluster queue `normal_imfdfkmq` via guarded SSH (`qstat -u pr21vyci`).
- **Terminal Completion of Prior Benchmark Jobs:**
  - Job `1412872.mmaster02` (Native 14.7k 8T SMP repeat, Exit 0, 7,000 incs, walltime 05:12:04, $1.87\times$ speedup);
  - Job `1412873.mmaster02` (Corrected 14.5k 8T SMP parity, Exit 1, 4,890 incs, walltime 03:35:22, $1.82\times$ speedup);
  - Job `1413022.mmaster02` (Corrected 14.5k 8T SMP Stage B repeat, Exit 1, 4,890 incs, walltime 03:22:49, $1.93\times$ speedup, $99.76\%$ softened).
- **Gate 6C Hold Status:** All Method C state continuation solver runs remain strictly on hold (`AUTHORIZED=false` on cluster submission wrappers); zero unauthorized Method C solver runs have been launched.

## Executive Summary & Scientific Sequence Overview

This briefing consolidates the complete numerical and mechanical evidence for **Method B** (load-partitioned propagation pre-refinement) and **Method C** (sequential adaptive remeshing and state transfer) on the canonical Mode-I symmetric tension phase-field fracture benchmark ($l_0 = 7.5\,\mu\mathrm{m}$).

The analysis strictly adheres to the supervisor-mandated scientific sequence:
$$\text{[Problem Definition]} \longrightarrow \text{[Expected Solution]} \longrightarrow \text{[Fixed-Mesh Reference Anchor]} \longrightarrow \text{[Method A/B Results]} \longrightarrow \text{[Method C1 Feasibility]} \longrightarrow \text{[Method C2 Alternatives]} \longrightarrow \text{[Unresolved Limitations]} \longrightarrow \text{[Specific Supervisor Decisions]}$$

```
====================================================================================================
MASTER STATUS DASHBOARD FOR 22 OCTOBER 2026 REVIEW:
----------------------------------------------------------------------------------------------------
* Method A (Two-Pass Pre-Refinement):
    - Status: COMPLETE & VALIDATED (ET2 6k FE; Mode-II ET3 21k FE)
    - Characteristic: Fixed mesh from t=0; sensitive to pre-analysis horizon.
* Method B (Load-Partitioned Pre-Refinement):
    - Definition & Scope: Configurable 1-, 2-, or 4-step loading partitions, followed by ONE
      remeshing operation and a fresh simulation from t = 0. The number of loading steps (1, 2, or 4)
      is NOT the number of adaptive remeshing cycles.
    - Status: COMPLETED WITH PARTIAL HORIZON LIMITATION (Job 1412465, 14,483 FE).
    - Achievement: Completely eliminated artificial 0.50-0.60 kN force plateau; restored brittle
      snap-through softening; reduced external work by 31.4896% (from 3.309642 mJ to 2.267448 mJ
      over matched horizon u <= 0.007889 mm, within -3.87% of canonical reference 2.3586 mJ).
    - Limitation: Terminal cutback at u = 0.007889 mm in deep softening tail (RF = 1.76 N, 99.76% softened).
      All like-for-like comparisons with reference are strictly scoped to u in [0.0, 0.007889] mm.
* Method C (Sequential Adaptive Remeshing during Crack Propagation):
    - Intended Research Objective: Genuine sequential adaptive remeshing during Mode-I crack
      propagation (Solve -> evaluate error -> remesh -> transfer state -> continue), rather than
      merely offline pre-refinement.
    - Status: OFFLINE_TRANSFER_QUALIFIED__CONTINUATION_NOT_QUALIFIED.
    - Actual Documented Milestone Status: One authentic coarse-to-fine refinement candidate
      (2,906 -> 14,677 FEs) and offline transfer verified. ZERO complete sequential remeshing-
      and-continuation cycles qualified in the solver. Multi-cycle experiments un-demonstrated.
    - Commercial Software Barrier: In-analysis continuation is fundamentally blocked in commercial
      Abaqus/Standard: fatal rejection of displacement ICs in *STATIC (Error 144), zero displacement
      DOFs under *INITIAL CONDITIONS, TYPE=SOLUTION, lack of UEL support in *MAP SOLUTION, and
      staggered UEL COMMON-block coupling lag.
====================================================================================================
```

---

## 1. Problem Definition, Expected Response & Canonical Reference Anchor

### 1.1 Boundary Value Problem Specification
- **Domain:** $\Omega = [0, 1] \times [0, 1]\,\text{mm}^2$ square plate.
- **Crack Representation:** Sharp horizontal seam along $y = 0.5\,\text{mm}$ ($0 \le x \le 0.5\,\text{mm}$) with duplicate coincident node pairs (zero initial gap).
- **Material & Phase-Field Parameters:** $E = 210.0\,\text{kN/mm}^2$, $\nu = 0.3$, $G_c = 2.7 \times 10^{-3}\,\text{kN/mm}$ ($2.7\,\text{N/mm}$), $l_0 = 0.0075\,\text{mm}$ ($7.5\,\mu\mathrm{m}$), $k_{\text{stab}} = 1.0 \times 10^{-7}$.
- **Boundary Conditions:** Roller support at $y = 0$ ($u_y = 0$, pinned at $(0,0)$); monotonic tensile top displacement $u_y(t) = t \cdot u_{\text{final}}$ prescribed via kinematic coupling to Reference Point 999999.

### 1.2 Expected Physical Response
1. Initial linear-elastic response with structural stiffness $K_0 \approx 138\,\text{kN/mm}$.
2. Crack-tip phase-field damage localization ($0 \le d \le 1$) within a regularized zone of width $w \approx 2 l_0 = 15\,\mu\mathrm{m}$.
3. Peak reaction force $F_{\max} \approx 0.758\,\text{kN}$ at $u \approx 0.00586\,\text{mm}$.
4. Immediate, sharp brittle softening tail with complete separation ($RF \to 0$) along the symmetry line $y = 0.5\,\text{mm}$.

### 1.3 Canonical Fixed-Mesh Reference Anchor (Job `1398090.mmaster02`)
The fixed-mesh reference solution is the quantitative anchor against which all adaptive methods are judged:
- **Mesh:** $15{,}220$ uniform quadrilateral CPE4 elements ($h = 3.75\,\mu\mathrm{m} = l_0 / 2$).
- **Initial Structural Stiffness:** $K_0 = 137.945520\,\text{kN/mm}$ ($R^2 = 0.99999960$, $u \le 0.0010\,\text{mm}$).
- **Peak Reaction Force:** $F_{\max} = 0.757802\,\text{kN}$ at $u = 0.005857\,\text{mm}$.
- **Post-Peak Response:** Immediate, sharp brittle softening to $F < 0.0005\,\text{kN}$ by $u = 0.0060\,\text{mm}$.
- **Cumulative External Work:** $W_{\text{ext}} = 2.3587\,\text{mJ}$ (over $u \in [0.0, 0.0100]\,\text{mm}$); $W_{\text{ext}} = 2.3586\,\text{mJ}$ (over $u \in [0.0, 0.007889]\,\text{mm}$).
- **Surface Fracture Energy:** $E_{\text{frac}} = 2.3512\,\text{mJ}$ ($99.69\%$ of external work).

---

## 2. Method B: Full-Ligament Refinement and Plateau Elimination

### 2.1 The Problem: Coarse Ligament Crack Pinning in Original Method B
Original Method B ($14{,}677$ FEs, Job `1411934.mmaster02`) was adapted based on an elastic Step-1 pre-analysis ($u \le 0.0050\,\text{mm}$). Because stress error indicators ($\MISESERI$) concentrated exclusively at the initial crack tip ($x \in [0.48, 0.52]\,\mathrm{mm}$), the remaining uncracked ligament ($x \in [0.55, 1.00]\,\mathrm{mm}$) retained coarse elements ($h \approx 19.7\,\mu\mathrm{m} > 2.6\,l_0$).
When the crack initiated into this coarse zone:
- Elements could not resolve the regularized damage gradient ($w_{0.5} \approx 2\,l_0 = 15.0\,\mu\mathrm{m}$).
- An unphysical force plateau of $F \approx 0.50 - 0.60\,\mathrm{kN}$ persisted across $u \in [0.0060, 0.0075]\,\mathrm{mm}$.
- Terminal external work reached $W_{\text{ext}} = 3.3320\,\text{mJ}$ ($+41.3\%$ excess work vs reference).

### 2.2 Expected Solution & Corrected Propagation Discretization
To resolve this defect, **Corrected Method B** (Package 40, Job `1412465.mmaster02`, `M1_MB_CORR_14K`) enforced the critical sizing threshold $h \le l_0 / 2 = 3.75\,\mu\mathrm{m}$ continuously along the entire symmetry ligament from notch tip to specimen boundary.
- **Finite Element Count:** $14{,}483$ FEs ($14{,}303$ CPE4 quads + $180$ CPE3 transition triangles).
- **Co-located Layer Records:** $43{,}449$ element records across the 3-layer architecture.
- **Corridor Sizing Compliance:** $96.76\%$ of elements along the prospective crack path satisfy $h \le 3.75\,\mu\mathrm{m} = l_0/2$, and $99.84\%$ satisfy $h \le 7.5\,\mu\mathrm{m} = l_0$.

### 2.3 Consolidated 4-Model Method B Evidence Matrix

To evaluate Method B comprehensively, the table below consolidates the four key Mode-I benchmark discretizations across their mechanical, energetic, and computational metrics over the common matched displacement horizon $u \in [0.0, 0.007889]\,\text{mm}$ (capturing $>99.76\%$ of brittle load drop):

| Metric / Parameter | Canonical Reference | Historical ET2 | Original Native Method B | Retrospective Corrected B | Metric Significance |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Job ID (Serial 1-CPU)** | `1398090` | `1411895` | `1411934` | `1412465` | Authoritative serial reference |
| **Job ID (8T SMP)** | --- | `1411950` | `1411949` / `1412872` | `1412873` / `1413022` | Certified 8T SMP execution |
| **Discretization Type** | Fixed Uniform | Fixed Pre-Refined | Native Pre-Refined | Retrospective Pre-Refined | Discretization generation mode |
| **Finite Elements** | $15{,}192$ | $6{,}112$ | $14{,}677$ | $14{,}483$ | Physical finite elements |
| **Element Records (3 layers)**| $45{,}576$ | $18{,}336$ | $44{,}031$ | $43{,}449$ | Co-located UEL/UMAT records |
| **Corridor Resolution** | $h = 3.75\,\mu\text{m} = l_0/2$ | $h = 5.0\,\mu\text{m} = 0.67 l_0$ | $h \approx 19.7\,\mu\text{m} > 2.6 l_0$ | $h \le 3.75\,\mu\text{m} = l_0/2$ ($96.8\%$) | Ligament element size |
| **Initial Stiffness $K_0$** | $137.9455\,\text{kN/mm}$ | $137.8900\,\text{kN/mm}$ | $137.8919\,\text{kN/mm}$ | $137.9096\,\text{kN/mm}$ | $\Delta K_0 \le -0.040\%$ across all 4 |
| **Linear Correlation $R^2$** | $0.9999996$ | $0.9999996$ | $0.9999996$ | $0.9999996$ | Linear elastic fit ($u \le 1.0\,\mu\text{m}$) |
| **Peak Force $F_{\max}$** | $0.757802\,\text{kN}$ | $0.756400\,\text{kN}$ | $0.743021\,\text{kN}$ | $0.743701\,\text{kN}$ | Peak load agreement within $1.9\%$ |
| **Displacement at Peak** | $0.005857\,\text{mm}$ | $0.005857\,\text{mm}$ | $0.005727\,\text{mm}$ | $0.005733\,\text{mm}$ | Shift $\le 130\,\text{nm}$ |
| **Force at $u=0.0060\,\text{mm}$**| $0.0005\,\text{kN}$ | $0.5271\,\text{kN}$ | $0.5981\,\text{kN}$ | $\mathbf{0.00208\,\text{kN}}$ | **Plateau Completely Eliminated** |
| **Force at $u=0.0070\,\text{mm}$**| $0.0004\,\text{kN}$ | $0.0151\,\text{kN}$ | $0.5250\,\text{kN}$ | $\mathbf{0.00192\,\text{kN}}$ | **Plateau Completely Eliminated** |
| **Matched Work ($u \le 0.0079$)**| $2.3586\,\text{mJ}$ | $2.8036\,\text{mJ}$ ($+18.9\%$) | $3.3096\,\text{mJ}$ ($+40.3\%$) | $\mathbf{2.2674\,\text{mJ}}^*$ ($\mathbf{-3.87\%}$) | $\mathbf{-31.49\%}$ reduction vs Native B |
| **Full Work ($u = 0.0100\,\text{mm}$)**| $2.3587\,\text{mJ}$ | $2.8276\,\text{mJ}$ | $3.3320\,\text{mJ}$ | \emph{N/A}$^\dagger$ | Baseline; cross-horizon invalid |
| **Fracture Energy $E_{\text{frac}}$**| $2.3512\,\text{mJ}$ | $2.7483\,\text{mJ}$ | $3.0320\,\text{mJ}$ | $2.2855\,\text{mJ}^*$ | $-2.79\%$ vs reference |
| **Elastic Energy $E_{\text{elas}}$**| $0.0003\,\text{mJ}$ | $0.0002\,\text{mJ}$ | $0.0152\,\text{mJ}$ | $0.0070\,\text{mJ}^*$ | Residual elastic strain energy |
| **Bookkeeping Residual $\Delta E$**| $0.0072\,\text{mJ}$ ($0.31\%$) | $0.0553\,\text{mJ}$ ($1.97\%$) | $0.2848\,\text{mJ}$ ($8.61\%$) | $0.0250\,\text{mJ}^*$ ($\mathbf{1.10\%}$) | UEL energy bookkeeping |
| **Verified Endpoint** | $u = 0.0100\,\text{mm}$ | $u = 0.0100\,\text{mm}$ | $u = 0.0100\,\text{mm}$ | $u = 0.007889\,\text{mm}$ | Post-severance ($RF = 1.76\,\text{N}$) |
| **Solver Status** | Exit 0 (7,000 incs) | Exit 0 (5,014 incs) | Exit 0 (7,000 incs) | Exit 1 ($dt < dt_{\min}$, 4,890 incs)| Severed rigid-body cutback |
| **Serial Runtime (1 CPU)** | 06:12:00 | 04:47:23 | 09:43:48 | 06:31:34 | Solver wallclock duration |
| **8T SMP Runtime** | --- | 02:52:08 (Job 1411950) | 05:12:04 (Job 1412872) | 03:35:22 (`1412873`) / 03:22:49 (`1413022`) | 8-thread shared memory solve |
| **8T SMP Speedup & Parity** | --- | $1.67\times$ (`PARITY_PASS`) | $1.87\times$ (`DETERM_PASS`) | $1.82\times - 1.93\times$ (`DETERM_PASS`) | Bitwise identical CSV traces |

$^*$Evaluated at verified terminal state $u = 0.007889\,\text{mm}$ ($RF = 1.7645\,\text{N}$, $99.76\%$ softened).  
$^\dagger$Solver encountered $dt < dt_{\min} = 10^{-9}$ during rigid-body separation of severed halves; nominal $0.0100\,\text{mm}$ horizon was not reached.

### 2.4 Solver Termination Audit & Comparison Horizon Discipline
- **Termination Root Cause:** Job `1412465` executed $4{,}890$ increments and encountered Exit Code 1 at $u = 0.007889\,\text{mm}$ due to cutbacks below $dt_{\min} = 1.0 \times 10^{-12}$ in the deep post-fracture softening tail.
- **Physical State at Termination:** Reaction force had dropped to $RF = 1.76\,\text{N}$ ($99.76\%$ load reduction from peak). The specimen halves were macroscopically severed and undergoing rigid-body separation.
- **Strict Comparison Horizon:** All like-for-like comparisons with reference are strictly valid over $u \in [0.0, 0.007889]\,\text{mm}$. Within this window, the complete linear elastic, initiation, peak, and brittle softening regimes are fully captured.
- **Topological Crack Continuity:** BFS dual-graph search confirms that all $818$ elements with $d \ge 0.95$ form a single $100\%$ connected component traversing $99.9\%$ of the ligament with zero isolated clusters or spatial gaps.

### 2.5 Epistemic Reconciliation: Pre-Analysis Damage, Companion Layer Elasticity, & Adaptive Boundaries
1. **Reconciliation of $d_{\max} = 0.094910$ with Linear Elastic Pre-Analysis (AT-2 Formulation):**  
   - In the standard AT-2 phase-field formulation, the strong-form Euler--Lagrange governing equation is $(H + \psi_0)d - \frac{1}{2} G_c \ell_0 \nabla^2 d = H \iff (H + \psi_0)d - \psi_0 \ell_0^2 \nabla^2 d = H$, derived from the weak form solved in `f42_mixed_uel.for` by dividing $(G_c/\ell_0 + 2H)d - G_c \ell_0 \nabla^2 d = 2H$ by 2. In the homogeneous zero-gradient limit ($\nabla^2 d = 0$), this reduces to $d_{\mathrm{hom}} = H / (H + \psi_0)$, showing damage evolves continuously from $H > 0$ without a discrete initiation threshold.
   - The characteristic fracture energy density scale is $\psi_0 = G_c / (2 \ell_0) = 0.0027 / (2 \times 0.0075) = 0.180\,\text{kN/mm}^2 = 180.0\,\text{MPa}$ (correcting a historical unit transcription error of $0.18\,\text{MPa}$).
   - At a notch tip, steep spatial gradients induce strong negative curvature ($\nabla^2 d < 0$), where the regularizing diffusion term $-\frac{1}{2} G_c \ell_0 \nabla^2 d = -\psi_0 \ell_0^2 \nabla^2 d > 0$ provides essential spatial diffusion, spreading damage over a zone $\sim \ell_0$. Substituting local $H_{\max} \approx 18.88\,\text{MPa}$ into the 0D zero-gradient formula gives a scalar estimate $d_{\mathrm{hom}} \approx 0.0949$, but this represents an idealized analytical back-calculation ignoring the spatial diffusion operator $-\psi_0 \ell_0^2 \nabla^2 d$. In the actual numerical finite-element solve (Job 1411891.mmaster02), the authentic maximum integration-point history variable stored in SVARS is $H_{\max} = 0.05364989\,\text{kN/mm}^2 = 53.64989\,\text{MPa}$, which drives the spatially coupled boundary value problem to the observed nodal damage $d_{\max} = 0.094910$. On the coarse $2{,}906$-element mesh, element sizing ($h \approx 20\,\mu\text{m} > 2.6\,\ell_0$) pins the gradient operator, yielding $d_{\max} = 0.094910$ (Job 1411891), whereas an adequately resolved mesh ($h \le \ell_0/4$) yields $d_{\max} = 0.3195$ at the identical displacement $u = 0.0050\,\text{mm}$ (Job 1411934).
   - Abaqus `RemeshingRule` evaluates `MISESERI` exclusively on Layer 3 (the companion continuum layer with $E_{\text{comp}} = 1.0\times 10^{-11}\,\text{GPa}$), which has **zero phase-field coupling ($d \equiv 0$)**.  
   - Because Layer 3 is governed strictly by linear isotropic continuum elasticity, the normalized error field $\eta_e = \text{MISESERI}_e / \text{MISESAVG}$ is scale-invariant, yielding bitwise identical adapted meshes (14,677 FE) across 1S, 2S, and 4S partitions ($\Delta \eta_{\max} = 0.0$ to double precision).
2. **Retrospective Verification Mesh Provenance vs Automated Adaptive Remeshing:**  
   - **Mode-I Geometry Clarification:** The benchmark domain is $\Omega = [0, 1] \times [0, 1]\,\text{mm}^2$. An initial sharp edge crack extends from $x = 0.0$ to $x = 0.500\,\text{mm}$ along $y = 0.500\,\text{mm}$, with initial crack tip at $(0.500, 0.500)\,\text{mm}$ and uncracked ligament $x \in [0.500, 1.000]\,\text{mm}$ along $y = 0.500\,\text{mm}$ ($L_{\text{lig}} = 0.500\,\text{mm}$). The linear elastic stress singularity $\boldsymbol{\sigma} \propto r^{-1/2}$ is located strictly at $(0.500, 0.500)\,\text{mm}$. The origin $(0,0)$ is simply a pinned corner point providing rigid-body translation restraint ($u_x = 0$) on the roller bottom ($u_y = 0$).
   - **Three-Way Disambiguation of Scale Invariance:** (a) *Analytical Expectation:* In linear elasticity without damage ($d \equiv 0$), $\boldsymbol{\sigma} \propto u$, so relative normalized error fields are scale-invariant. (b) *Abaqus Proprietary Indicator:* `MISESERI` evaluates patch recovery of stress discontinuities with proprietary patch topology and domain-average denominator `MISESAVG`; it reflects empirical solver behavior and must not be asserted as an identical textbook Zienkiewicz--Zhu formula. (c) *Numerical Verification:* Bitwise equality across 1S, 2S, 4S load steps is numerically proven from extracted arrays ($\Delta \text{MISESERI} = 0.0$), yielding identical 14,677-element meshes ($\Delta N = 0$).
   - **ErrorTarget Sizing Rule:** The parameter `errorTarget = 1.0%` represents a 1% global target error tolerance under `UNIFORM_ERROR` sizing, NOT a direct numerical cutoff of `MISESERI = 1.0`.
   - **Quantitative Prospective Remeshing Sensitivity Audit:** Comprehensive spatial auditing across all four native errorTarget tiers ($1.0\%, 2.0\%, 3.0\%, 5.0\%$) quantifies why prospective native remeshing fails to resolve crack propagation:
     * *Tier 1 (1.0%, 71,320 FEs):* Crack tip over-refined to $h_{\text{median}} = 1.89\,\mu\text{m}$ ($h_{\min} = 0.56\,\mu\text{m} \ll \ell_0/2$). Contiguous ligament resolution ($h \le 3.75\,\mu\text{m}$) reaches only $x_{\max} = 0.7529\,\text{mm}$ ($50.6\%$ of ligament). Beyond $x = 0.80\,\text{mm}$, resolution drops to $<4\%$ ($h_{\text{median}} = 5.81\,\mu\text{m}$), causing cutback solver termination at $u = 0.006774\,\text{mm}$ ($F = 0.184\,\text{kN}$).
     * *Tier 2 (2.0%, 15,396 / 14,677 FEs):* Crack tip resolved ($h_{\text{median}} = 1.94\,\mu\text{m}$), but contiguous ligament resolution reaches only $x_{\max} = 0.5950 - 0.6040\,\text{mm}$ ($19.0\% - 20.8\%$ of ligament). Slices $x \in [0.70, 1.00]\,\text{mm}$ coarsen to $h \approx 11 - 15\,\mu\text{m}$, creating severe crack pinning with a $F(u=0.008\,\text{mm}) = 0.427\,\text{kN}$ plateau.
     * *Tier 3 (3.0%, 7,633 / 8,120 FEs):* Contiguous reach $x_{\max} = 0.5556\,\text{mm}$ ($11.1\%$ ligament coverage). Ligament coarsens to $h \approx 11 - 15\,\mu\text{m}$, sustaining an elevated pinning plateau of $F(u=0.008\,\text{mm}) = 0.548\,\text{kN}$.
     * *Tier 4 (5.0%, 4,194 / 4,356 FEs):* Contiguous reach $x_{\max} = 0.5231\,\text{mm}$ ($4.6\%$ ligament coverage), causing artificial fracture delay ($F(u=0.008\,\text{mm}) = 0.750\,\text{kN}$).
     * *Canonical Reference (Job 1398090, 42k FEs):* $F_{\max} = 0.757778\,\text{kN}, K_0 = 137.945520\,\text{kN/mm}, F(u=0.008\,\text{mm}) = 0.000339\,\text{kN}$ (clean, complete fracture drop).
      * *Direct Solver Deck Coordinate Parser Validation (Task F1476) & Dual-Metric Reconciliation:* Full coordinate and element-area extraction across the five exact solver decks (`spatial_resolution_validation.csv`, SHA-256 `DDAD1E84...`) established exact contiguous coverage values: Tier 1 (71.3k FE) reaches $x_{\max} = 0.6648\,\text{mm}$ ($32.96\%$ contiguous coverage, $78.26\%$ corridor elements resolved); Tier 2 (14.7k FE Native) reaches $x_{\max} = 0.5940\,\text{mm}$ ($18.80\%$ coverage, $78.91\%$ resolved); Tier 3 (7.6k FE) reaches $x_{\max} = 0.5556\,\text{mm}$ ($11.11\%$ coverage, $69.87\%$ resolved); Tier 4 (4.2k FE) reaches $x_{\max} = 0.5010\,\text{mm}$ ($0.21\%$ coverage, $4.41\%$ resolved); whereas retrospective Package 40 (14.5k FE) achieves $x_{\max} = 1.0000\,\text{mm}$ ($100.00\%$ contiguous coverage, $96.81\%$ resolved under the Binned Median Corridor metric).
      * *Dual-Metric Clarification for Package 40:* Under the Binned Median Corridor metric (5 µm bins across $|y - 0.500| \le 0.020\,\text{mm}$), the median size in every single bin remains $\le 3.17\,\mu\text{m} < \ell_0/2 = 3.75\,\mu\text{m}$, yielding **100.00% contiguous corridor coverage** across the entire ligament to $x = 1.0000\,\text{mm}$ (explaining complete elimination of the force plateau). Under the Strict Centerline Chain metric (evaluating the unbroken sequence of individual elements on $|y - 0.500| \le 0.010\,\text{mm}$), the very first transition element exceeding $3.75\,\mu\text{m}$ occurs at $x = 0.8911\,\text{mm}$ ($h_A = 3.86\,\mu\text{m}$), establishing **78.21% strict centerline coverage** ($76.45\%$ under $h_{\text{edge}}$ and $69.39\%$ under $\Delta y$). Both metrics are exact and reflect complementary aspects: 100% fine corridor coverage with local boundary transition coarsening in the final 20% of the ligament.
   - **Empirical Boundary vs Impossibility Theorem:** The 1%, 2%, 3%, 5% errorTarget sensitivity studies establish the empirical limitations of the **tested native configuration and indicator parameters** (which either over-refine globally or confine exclusively to the initial notch tip), rather than an abstract mathematical **impossibility theorem** for all prospective remeshing techniques.
   - **Conclusive Causal Theorem:** Native MISESERI refinement principally over-refines the initial crack-tip neighborhood $(0.5, 0.5)\,\text{mm}$ rather than providing uniform corridor coverage along the ligament to $x = 1.0\,\text{mm}$, because an uncracked linear elastic pre-analysis has no stress singularity ahead in the uncracked ligament! When the crack enters the under-resolved zone ($h > 3.75\,\mu\text{m}$), the phase-field regularization cannot be resolved, pinning the crack.
   - **HPC Experiment Justification Decision:** Because complete solver runs and audited force-displacement curves already exist for all 4 errorTarget tiers (Jobs 1404933/1405044 for 71k, Jobs 1400368/1400395/1411934 for 15k/14.7k, Job 1400737 for 8k, Jobs 1400382/1400396 for 4k), zero additional prospective HPC experiments are required. The quantitative proof is airtight.
   - Forensic provenance audit revealed the Package 40 corrected mesh (14,483 FE) was generated from a Step-2 localized damage state ($u = 0.0100\,\text{mm}$, companion frame 1022) of a prior simulation where the crack had already traversed the ligament.
   - Accordingly, the 14,483-element mesh is classified explicitly as a **retrospective, benchmark-specific verification mesh**. It proves that resolving the ligament eliminates the artificial plateau and restores brittle fracture, but it does NOT prove that Method B can prospectively predict an unknown crack path.
   - **Boundary Guard:** A single failed pre-refinement configuration does not mathematically prove that Method C is already capable of resolving general crack propagation. Method C represents an **unqualified candidate sequential remeshing methodology** whose true continuation, nonmatching state transfer, and damage irreversibility enforcement remain open research questions under Gate 6C hold.
3. **8-Thread Shared-Memory SMP Parity and Determinism Certification:**
   - **Native Method B 14,677 FE (Job 1412872):** Stage B determinism repeat completed all 5,000 increments in Step 2 ($u = 0.0100\,\text{mm}$, Exit 0, walltime 05:12:04, 1.87x speedup vs serial). Full-precision SHA-256 hash comparison of `uel_energy_balance.csv` demonstrated **bitwise identity** (`792be67d...`) and identical reaction force ($F = 8.262311\,\text{N}$) across both 8T runs and the serial run, certifying `THREAD_PARITY_PASS` and `THREAD_DETERMINISM_PASS`.
   - **Corrected Method B 14,483 FE (Jobs 1412873 & 1413022):** Stage A parity and Stage B independent repeat completed Step 1 (2,000 incs) and reached Step 2 Increment 2890 ($u = 0.007889\,\text{mm}$, Exit 1, walltimes 03:35:22 and 03:22:49, $1.82\times$ and $1.93\times$ speedup vs serial 06:31:34). Demonstrated physical brittle fracture across $99.76\%$ of the load drop ($RF = 1.7645\,\text{N}$ vs peak $743.7\,\text{N}$) before terminating at $dt < dt_{\min} = 1.0\times 10^{-9}$ on the completely severed plate. Full-precision SHA-256 hash comparison of `uel_energy_balance.csv` confirmed **bitwise identity** across all 4,890 increments (`82f2963d...`), certifying `THREAD_PARITY_PASS`, `THREAD_DETERMINISM_PASS`, and `THREAD_PARALLELIZATION_QUALIFIED`.
---

## 3. Method C: Sequential Adaptive Remeshing Feasibility & State Transfer

### 3.1 Precise Operational Definitions: Methods A, B, and C
To maintain strict methodological discipline and prevent conflation in reporting:

1. **Method A (Fixed Offline Pre-Refinement):**
   - *Operational Definition:* A single static discretization is constructed *prior* to solver execution with a fine mesh corridor ($h \le l_0/2$) pre-seeded along the entire anticipated crack path (e.g. Canonical Reference 15k, Historical ET2 6.1k). The simulation executes continuously from $t = 0$ to $t_{\text{final}}$ on this frozen mesh.
   - *Scientific Scope:* Requires exact *a priori* knowledge of the crack trajectory. It is an engineering baseline, not an adaptive remeshing methodology.

2. **Method B (Load-Partitioned Offline Pre-Refinement with Remeshing Rule):**
   - *Operational Definition:* An initial simulation runs on a coarse mesh ($M_0$) up to an intermediate pre-peak load step ($u_{\text{pre}} = 0.0050\,\text{mm}$). Abaqus built-in `RemeshingRule` evaluates an error indicator ($\MISESERI$) on a companion linear-elastic continuum overlay. Exactly **one** remeshing operation is performed ($M_0 \to M_1$). The fracture simulation is then restarted from $t = 0$ on the new mesh $M_1$.
   - *Crucial Finding:* Loading steps (1S, 2S, 4S) are NOT remeshing cycles. Because the pre-analysis stops before crack propagation, the linear-elastic error field is path-independent and scale-invariant ($\Delta \eta_{\max} = 0.0$). The resulting stationary notch-tip stress field leaves the uncracked ligament coarse ($h \approx 20\,\mu\text{m}$), producing severe crack pinning ($0.50-0.60\,\text{kN}$ plateau, $+40.3\%$ work). Extending the corridor across the ligament (Corrected Method B) eliminates the plateau, but was derived *retrospectively* from a donor state where the crack had already propagated.

3. **Method C (Sequential In-Analysis Adaptive Remeshing during Propagation):**
   - *Operational Definition:* True automated adaptive fracture simulation: $\text{Solve} \to \text{Evaluate Error} \to \text{Remesh} \to \text{Transfer State} \to \text{Continue}$, repeated sequentially during active crack propagation.
   - *Documented Milestone Status:* One authentic coarse-to-fine refinement candidate ($2{,}906 \to 14{,}677$ FEs) and offline state transfer have been verified, but **zero complete sequential remeshing-and-continuation cycles have been qualified in the solver**. Two-cycle and four-cycle Method C experiments remain un-demonstrated. Commercial Abaqus/Standard barriers (rejection of displacement ICs in `*STATIC`, zero DOFs in solution ICs, lack of UEL mapping) fundamentally block native in-analysis continuation.

The state-transfer comparison across the three canonical physical fields at $u = 0.0050\,\text{mm}$ (donor deck `M1-MB-1S.inp` / `M1_MB_INF_1S.inp`, $2,906$ FEs, $2,988$ physical nodes) established:
- **Field 1 (Coarse Donor Solution, 2.9k FEs):** $d_{\max} = 0.094910$ evaluated at true notch-tip **Node 97** ($x=0.500\,\text{mm}, y=0.500\,\text{mm}$). Coarse mesh ($h = 20\,\mu\mathrm{m} > 2.6\,l_0$) pinned damage evolution, retarding crack initiation. (Note: 2,142 nodes in `coarse_donor_state_u0050.json` reflects nodes with active damage $d \ge 1.3 \times 10^{-7}$, while 846 intact far-field nodes receive $d = 0.0$).
- **Field 2 (Coarse Solution Interpolated on Fine Mesh):** $d_{\max} = 0.094910$. Exact identity with Field 1 ($\Delta d = 0.000000$) at the coincident notch tip node ($x=0.5, y=0.5\,\text{mm}$). Proves **mathematical transfer fidelity**.
- **Field 3 (Independently Solved Fine Reference, 14.7k FEs):** $d_{\max} = 0.319455$. Fine mesh ($h = 1.875\,\mu\mathrm{m} \le l_0/4$) resolved steep damage gradient from $t = 0$.
- **Spatial Separation of $H_{\max}$ and $d_{\max}$:** Global maximum strain energy history $H_{\max} = 53.6499\,\text{MPa}$ is located inside Element 1208 at its crack-tip Gauss points ($x \approx 0.501, y \approx 0.500$), separated from the continuous nodal field $d_{\max} = 0.094910$ at Node 97. Pointwise 0D algebraic equivalence must never be claimed between them.

### 3.2 Offline State Transfer Evaluation (Gate 6C Criteria)

| Gate 6C Criterion | Physical Target Quantity | Pre-declared Acceptance Bound | Achieved Evaluation | Qualification Verdict |
| :---: | :--- | :---: | :---: | :---: |
| **Criterion 1** | Displacement $L_2$ Error | $\le 1.0\%$ | $\mathbf{0.1347\%}$ | **PASS** |
| **Criterion 2** | Peak Damage Discrepancy $\Delta d_{\max}$ | $\le 0.020$ | $\mathbf{0.000000}^*$ | **PASS** |
| **Criterion 3** | Domain-Integrated Damage Error | $\le 5.0\%$ | $\mathbf{0.1322\%}$ | **PASS** |
| **Criterion 4** | Strain-History Non-Negativity | $\min(\Hist) \ge 0.0$ | $\mathbf{1.579 \times 10^{-9}\,\text{kN/mm}^2}$ | **PASS** (0 negative GPs) |
| **Criterion 5** | Step-Boundary Force Discontinuity | $\le 5.0\,\mathrm{N}$ | \emph{Not Yet Evaluated}$^\dagger$ | **UN-RUN IN SOLVER** |
| **Criterion 6** | Offline Mesh Compliance Disparity | $\le 5.0\%$ | $\mathbf{1.6662\%}^\ddagger$ | **PASS** |
| **Criterion 7** | Continuation Energy Residual | $\le 10.0\%$ | \emph{Not Yet Evaluated}$^\dagger$ | **UN-RUN IN SOLVER** |

$^*$Evaluated at coincident notch tip node 97 ($x=0.5, y=0.5\,\text{mm}$). (Prior reports referenced node 129 from the 15k reference mesh).  
$^\dagger$Forward recipient mesh has never been solved in Abaqus. Reverse coarsening metrics (Job 1412809: $21.55\,\text{N}$ and $22.22\%$) are kept strictly decoupled.  
$^\ddagger$Criterion 6 evaluates the static compliance disparity between the independently solved coarse donor ($1.6634\,\text{mJ}$) and fine reference ($1.6911\,\text{mJ}$) equilibrium states at $u = 0.0050\,\text{mm}$.

### 3.3 Mathematical Tangent Disambiguation & Nonmatching Projection Residual
1. **Mechanical Tangent for Fixed Damage ($\mathbf{K}_{uu}$):**
   $$\mathbf{K}_{uu} = \int_{\Omega} \mathbf{B}^T g(d) \mathbf{C}_0 \mathbf{B} \, d\Omega$$
   Because $g(d) = (1-d)^2 + k_{\text{stab}} \ge 10^{-7} > 0$ everywhere, $\mathbf{K}_{uu}$ is **strictly symmetric and positive definite** for any fixed damage state. One must not infer loss of positive definiteness of $\mathbf{K}_{uu}$ solely from material degradation.
2. **Coupled Damage-Evolution Tangent ($\mathbf{K}_{\text{coupled}}$):**
   When damage evolves ($\dot{d} > 0$), the variation $-\frac{\partial g}{\partial d}\dot{d}\mathbf{C}_0:\boldsymbol{\varepsilon}$ introduces negative eigenvalues into the coupled system operator $\mathbf{K}_{\text{coupled}}$, which causes loss of positive definiteness during localized crack propagation.
3. **Nonmatching Projection Residual ($\mathbf{R}_{\text{internal}, 0}$):**
   For the candidate forward transfer ($2,906 \to 14,677$ FEs at $u = 0.0050\,\text{mm}$), the compliance disparity of $1.64\%$ produces an estimated internal un-equilibrated nodal residual norm of $\|\mathbf{R}_{\text{internal}, 0}\| \approx \mathcal{O}(10\,\text{N})$ across the $\sim 11,846$ newly created interior nodes.
4. **Three Zero Quantities Disambiguated:**
   - $\Delta \mathbf{U}_{\text{prescribed}} = \mathbf{0}$ (prescribed boundary condition increment)
   - $\mathbf{R}_{\text{internal}, 0} = \mathbf{0}$ (discrete internal equilibrium residual, which is strictly non-zero: $\boldsymbol{\rho}_{\text{transfer}} \ne \mathbf{0}$)
   - $\Delta RF = 0$ (boundary reaction force discontinuity)
   Prescribing zero incremental displacement does NOT ensure internal equilibrium or force continuity.

5. **Four-Stage Thermodynamic State-Transfer Energy Balance:**
   - *Stage 1 (Donor State):* $W_{\text{ext}, D} = E_{\text{elas}, D} + E_{\text{frac}, D} + \mathcal{D}_{\text{num}, D} + \Delta E_{\text{book}, D}$ ($W_{\text{ext}} = 1.6327\,\text{mJ}, E_{\text{elas}} = 1.6327\,\text{mJ}, E_{\text{frac}} = 0.0307\,\text{mJ}, E_{\text{tot}} = 1.6634\,\text{mJ}$).
   - *Stage 2 (Post-Projection State):* $E_{\text{elas}, R}^{(0)} = E_{\text{elas}, D} + \Delta E_{\text{proj, elas}}$, with out-of-balance residual norm $\|\mathbf{R}_R^{(0)}\| \approx \mathcal{O}(10\,\text{N})$.
 - *Stage 3 (Fixed-$u$ Equilibration, $\Delta u_{\text{boundary}} = 0$, $d$ frozen):* $\Delta W_{\text{ext}} = 0 = \Delta E_{\text{elas, relax}} + \mathcal{D}_{\text{num, relax}} \iff \Delta E_{\text{elas, relax}} = -\mathcal{D}_{\text{num, relax}} \le 0$, where discrete algorithmic residual dissipation $\mathcal{D}_{\text{num, relax}} \ge 0$ absorbs the projection residual. Newton iterations seek a stationary equilibrium state ($\nabla_{\mathbf{u}}\Pi = \mathbf{0}$) rather than guaranteeing monotonic energy reduction at each iterate. In a conservative elastic medium with frozen damage ($\Delta d = 0$), zero physical thermodynamic dissipation occurs ($\Delta \mathcal{D}_{\text{phys}} \equiv 0$), strictly distinguishing algorithmic potential energy minimization from physical thermodynamic dissipation.
   - *Stage 4 (Forward Propagation, $u > u_D$):* $\Delta W_{\text{ext}} = \int_{u_D}^u F \, \mathrm{d}\tilde{u} = \Delta E_{\text{elas}} + \Delta E_{\text{frac}} + \Delta \mathcal{D}_{\text{visc}} + \Delta \mathcal{D}_{\text{num}}$.

---

## 4. Formal Decisions Submitted for Supervisor Consideration & Determination (22 October 2026)

During the upcoming meeting on Thursday, 22 October 2026 at 10:00 CEST, the following formal decisions and technical notes are submitted for the supervisor's review, consideration, and formal determination:

### 4.1 Decision 1: Formal Closure of Gate 6B (Method B)
- **Submitted for Supervisor Determination:** Formal closure and sign-off of Gate 6B with the classification:
  `METHOD_B_SCIENTIFIC_OBJECTIVE_COMPLETED_WITH_PARTIAL_HORIZON_LIMITATION`
- **Technical Basis:** Corrected Method B completely resolved the central research question by eliminating the $0.50-0.60\,\text{kN}$ force plateau, restoring brittle snap-through softening, and reducing external work by $31.4896\%$ (from $3.309642\,\text{mJ}$ to $2.267448\,\text{mJ}$ over the matched horizon $u \le 0.007889\,\text{mm}$, within $-3.87\%$ of canonical reference $2.3586\,\text{mJ}$). All scientific claims are strictly scoped to the verified common displacement horizon $u \in [0.0, 0.007889]\,\text{mm}$ (capturing $>99.76\%$ softening).

### 4.2 Decision 2: Formal Evaluation of Gate 6C (Method C)
- **Submitted for Supervisor Determination:** Formal classification of Gate 6C under the strict three-tier evaluation:
  - **Datacheck Qualification:** `DATACHECK_PASSED` (Abaqus 2023 preflight Exit 0, 0 syntax defects, 0 unreferenced sets across 102,830 lines).
  - **Offline Mathematical Transfer:** `OFFLINE_TRANSFER_VERIFIED` ($L_2 = 0.1347\%$, $\Delta d_{\max} = 0.000000$, $\min(\Hist) \ge 0.0\,	ext{MPa}$, compliance disparity $1.64\%$).
  - **Solver Continuation Qualification:** `SOLVER_CONTINUATION_NOT_YET_QUALIFIED` (Reload ramp defect & ligament coarsening beyond $x pprox 0.85\,	ext{mm}$).
- **Technical Basis & Forensic Audit Findings:**
  1. *Continuation-Physics Defect (Error 144 Workaround):* Package 42 Step 1 (`Step-1-Equilibrate`) ramps boundary displacement from $u = 0$ to $u = 0.0050\,	ext{mm}$ across 20 increments. Because commercial Abaqus/Standard rejects `*INITIAL CONDITIONS, TYPE=DISPLACEMENT` in `*STATIC` steps (Error 144), initial nodal displacements at $t=0$ are zero ($\mathbf{u} = \mathbf{0}$). This performs an unphysical **quasi-static reload of a pre-damaged specimen** from zero displacement rather than in-situ equilibrium continuation.
  2. *Automated Spatial Resolution & Ligament Truncation Audit:* Automated element-by-element geometry audit (`spatial_resolution_audit.py`, full report in `docs/reports/MODE1_METHOD_C1_STATE_INITIALIZATION_AND_CONTINUATION_ARCHITECTURE.md`) definitively quantifies the spatial resolution limitations:
     - *Package 42 Native Mesh (`M1_MC_C1_FORWARD_14K`, 14,647 nodes, 14,677 FEs / 44,031 UEL records):* Out of 288 elements intersecting the crack line ($y=0.50\,	ext{mm}, x \in [0.50, 1.00]\,	ext{mm}$), only 147 ($51.0\%$) meet the Nyquist criterion $h \le \ell_0/2 = 3.75\,\mu	ext{m}$. Contiguous resolved coverage extends only from $x = 0.5000\,	ext{mm}$ to $x = 0.5939\,	ext{mm}$ (**only 18.8% of the uncracked ligament!**). Beyond $x = 0.65\,	ext{mm}$, resolution drops to $0.0\%$, with element size jumping from $h_{	ext{avg}} = 9.15\,\mu	ext{m}$ to $18.66\,\mu	ext{m}$ ($>5	imes \ell_0/2$). Advancing crack propagation on this mesh would hit coarse elements within 2 increments, triggering severe crack pinning and regenerating the $0.50-0.60\,	ext{kN}$ plateau.
     - *Package 40 Corrected Mesh (`M1_MB_CORRECTED_PROPAGATION_14K`, 14,457 nodes, 14,483 FEs / 43,449 UEL records):* Contains 852 crack-line elements, with 777 ($91.2\%$) meeting $h \le 3.75\,\mu	ext{m}$. Contiguous resolved extent spans $x \in [0.5000, 0.8911]\,	ext{mm}$ (**78.2% contiguous ligament coverage**, $100\%$ resolved up to $x=0.85\,	ext{mm}$, with maximum size bounded at $5.21\,\mu	ext{m}$).
  3. *Reconciled Authentic Donor Source Data & History Field:* Reconciled authentic coarse donor state from Job 1411891 (`M1_PRE_1S`, coarse 2,906 FEs at $u = 0.0050\,\text{mm}$): exact reaction force is $RF = 653.0886\,\text{N}$ (reconciling prior conflation with 15k reference $724.81\,\text{N}$), elastic strain energy is $E_{\text{elas}} = 1.6327\,\text{mJ}$ (reconciling conflation with $2.0531\,\text{mJ}$), fracture energy is $E_{\text{frac}} = 0.0307\,\text{mJ}$, total internal energy is $E_{\text{tot}} = 1.6634\,\text{mJ}$, $d_{\max} = 0.094910$, and authentic maximum Gauss-point history is $H_{\max} = 53.64989\,\text{MPa}$ ($0.053650\,\text{kN/mm}^2$, resolving prior conflation with the 0D back-calculated estimate of $18.88\,\text{MPa}$).
  4. *Multi-Cycle Status:* Zero complete sequential remeshing-and-continuation cycles have been qualified in the solver; multi-cycle experiments remain un-demonstrated.



*Comprehensive Technical Reference:* The full feasibility matrix across all 8 Abaqus state restoration mechanisms, mathematical derivation of the Kinematic-Offset UEL, donor-consistent residual benchmark, and four-objective methodological separation are documented in `docs/reports/MODE1_METHOD_C1_STATE_INITIALIZATION_AND_CONTINUATION_ARCHITECTURE.md`.

### 4.3 Decision 3: Strategic Thesis Path Forward
- **Submitted for Supervisor Consideration & Determination:** The strategic research direction for the thesis remains for determination between the user and supervisor. Two scientifically defensible options are submitted:
  - **Option A (Preserve & Report Baseline Methods):** Preserve and report Methods A and B as verified offline pre-refinement engineering workflows, alongside a rigorous documentation of the current commercial Abaqus/Standard Method C feasibility limitations and architectural software barriers, without further solver modifications.
  - **Option B (Investigate Separate Experimental Continuation Architecture):** Authorize implementing and evaluating the smallest isolated experimental C1 continuation prototype on a dedicated development branch (`f42_experimental_offset_uel.for`), keeping the authoritative, frozen baseline `f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`) strictly unchanged and protected (critiquing tangent positive definiteness, removing unconditional solvability guarantees, and enforcing a 5-stage qualification progression with strict rollback boundaries) (technical feasibility and controlled single-cycle validation plan detailed in `docs/reports/MODE1_METHOD_C1_CONTINUATION_FEASIBILITY_AND_PLAN.md` and independent architectural validation and Method C2 wake coarsening audit in `docs/reports/MODE1_METHOD_C_CONTINUATION_ARCHITECTURE_VALIDATION.md`).
- **Epistemic Discipline:** The choice between Option A and Option B belongs strictly to the user and the supervisor. The controller/agent does not independently terminate Method C or resume Mode-II. General PBS permission does NOT authorize C1 solver execution without explicit supervisor review.

### 4.4 Technical Note: Mandatory Qualification Criteria for a Single Genuine Method C Remeshing Cycle

For supervisor consideration regarding Option B (or any future continuation investigation detailed in `docs/reports/MODE1_METHOD_C1_CONTINUATION_FEASIBILITY_AND_PLAN.md`), a future single genuine Method C remeshing-and-continuation cycle ($\text{Solve} \to \text{Evaluate Error} \to \text{Remesh} \to \text{Transfer State} \to \text{Continue}$) must rigorously demonstrate the following six pre-declared verification criteria before multi-cycle execution can be considered:

1. **State-Preserving Nonzero-Displacement Initialization:**
   The solver must initialize directly at the transferred deformed equilibrium state ($\mathbf{u} = \mathbf{u}_{\text{handoff}} \ne \mathbf{0}$) on the recipient mesh without requiring an artificial quasi-static reload from $u = 0$, thereby preserving the active stress state and kinematic history.
2. **Phase-Field and Strain-History Preservation:**
   Nodal damage values ($0 \le d \le 1$) and element history variables ($\Hist \ge 0$) must be transferred with high spatial fidelity without unphysical diffusion, negative values, or loss of localization ($L_2 \le 1.0\%$, $\Delta d_{\max} \le 0.02$).
3. **Reaction-Force Continuity Within Declared Tolerance:**
   The initial reaction force upon continuation on the recipient mesh must match the donor handoff reaction force within the declared tolerance of $|\Delta RF| \le 5.0\,\text{N}$, eliminating step-boundary discontinuities.
4. **Quantified Transfer-Induced Energy Discrepancy:**
   The energy discrepancy introduced purely by mesh-to-mesh state transfer must be rigorously bounded and tracked ($\Delta E_{\text{transfer}} / W_{\text{ext}} \le 5.0\%$), and global energy balance must be satisfied throughout subsequent continuation ($\Delta E \le 10.0\%$).
5. **Actual Forward-Recipient Fracture Response Against Fixed Reference:**
   Continuation must demonstrate physical crack propagation on the fine recipient mesh matching the canonical fixed-mesh reference in stiffness $K_0$, peak load $F_{\max}$, and brittle post-peak softening without crack pinning.
6. **Repeatability Before Extending to Multi-Cycle Execution:**
   A single remeshing cycle must be proven robust, deterministic, and repeatable before extending the workflow to two or more sequential remeshing cycles.

*Epistemic Guard:* Developing an experimental UEL modification or alternative initialization architecture is treated strictly as an engineering hypothesis requiring separate empirical verification; it must not be assumed or claimed that an experimental UEL modification will necessarily resolve these commercial solver constraints.

### 4.5 Technical Note: Defensible Progressive Progression from Gate C1 to Gate C2

To ensure scientific rigor, a two-stage sequential validation gate structure is established (detailed in `docs/reports/MODE1_METHOD_C_CONTINUATION_ARCHITECTURE_VALIDATION.md`):

1. **Gate C1 (Forward-Refinement Continuation Validation):**
   - Must demonstrate one genuine forward continuation ($2,906 \to 14,677$ FEs at $u = 0.0050\,\mathrm{mm}$).
   - Mandatory criteria: reaction-force continuity ($|\Delta RF| \le 5.0\,\mathrm{N}$), transfer energy error ($\le 5.0\%$), global balance residual ($\le 10.0\%$), damage irreversibility ($\Delta d \ge -10^{-6}$), reference fracture response parity ($|F_{\max} - F_{\max}^{\mathrm{ref}}| \le 3.0\%$, no crack pinning), and 0 pre-peak cutbacks.
   - Staged re-equilibration is treated as a provisional reload surrogate requiring proof of state equivalence at handoff, while kinematic-offset UEL is an experimental candidate.

2. **Gate C2 (Selective Crack-Wake Coarsening Validation):**
   - Activated **only after Gate C1 achieves PASS**.
   - Distinguishes coarsening in intact far-field material ($d = 0$, safe to coarsen to $20-50\,\mu\mathrm{m}$), active FPZ ($0 < d < 1$, strictly forbidden to coarsen), and fully fractured wake ($d \approx 1$, where coarsening risks altering arm compliance, COD, and fracture energy quadrature).
   - Applies the candidate mesh-resolution guideline $h_{\mathrm{wake}} \le l_0/2 = 3.75\,\mu\mathrm{m}$ across damaged zones ($d \ge 0.05$) as an engineering heuristic awaiting numerical validation, without hardcoding crack trajectories.
   - Requires demonstrating net computational efficiency ($\ge 15\%$ walltime reduction vs C1) without corrupting global fracture physics.

3. **Governance & Authorization Status:**
   - Gate 6B is ready for supervisor sign-off on 22 October 2026.
   - **Gate 6C remains ON HOLD PENDING SUPERVISOR REVIEW.** Passing unit tests or general PBS script presence do NOT constitute scientific gate clearance. Zero new solver jobs are submitted without explicit supervisor/user release.

---

## 5. Traceable Epistemic Evidence Matrix

The complete evidence base is classified under the formal schema (`Evidence_ID`, `Epistemic_Tier`, `Claim_Statement`, `Governing_Metric`, `Pass_Threshold`, `Measured_Value`, `Evaluation_Status`):

```
+=======================================================================================================================================================+
|                                                      TRACEABLE EPISTEMIC EVIDENCE MATRIX                                                              |
+============+========================+====================================+======================+================+==================+=================+
| Evidence ID| Epistemic Tier         | Claim Statement                    | Governing Metric     | Pass Threshold | Measured Value   | Status          |
+============+========================+====================================+======================+================+==================+=================+
| EVD-M1-001 | [SOURCE CODE AUDIT]    | UEXTERNALDB zeroing loop prevents  | Code presence in     | Exact syntax   | Verified lines   | VERIFIED_PASS   |
|            |                        | Fortran state carryover            | f42_mixed_uel.for    | LOP=0 loop     | 88-101           |                 |
+------------+------------------------+------------------------------------+----------------------+----------------+------------------+-----------------+
| EVD-M1-002 | [SOURCE CODE AUDIT]    | SVARS(8+KPT) ingests history H     | SV_H_COMMITTED assign| Exact syntax   | Verified lines   | VERIFIED_PASS   |
|            |                        | from *INITIAL CONDITIONS, TYPE=SOL | from SVARS(8+KPT)    | in Step 1 Inc 1| 248-262          |                 |
+------------+------------------------+------------------------------------+----------------------+----------------+------------------+-----------------+
| EVD-M1-003 | [MATHEMATICAL DERIV.]  | Fixed-damage tangent Kuu is        | Eigenvalues of Kuu   | min(lambda)>0  | lambda > 0       | VERIFIED_PASS   |
|            |                        | strictly positive-definite         | for g(d) >= k_stab   | for all d      | analytically     |                 |
+------------+------------------------+------------------------------------+----------------------+----------------+------------------+-----------------+
| EVD-M1-004 | [MATHEMATICAL DERIV.]  | Coupled tangent K_coupled loses    | Eigenvalues of       | lambda <= 0    | lambda < 0       | VERIFIED_PASS   |
|            |                        | definiteness during softening      | K_coupled with soft. | during crack   | during localized |                 |
|            |                        |                                    |                      | propagation    | softening        |                 |
+------------+------------------------+------------------------------------+----------------------+----------------+------------------+-----------------+
| EVD-M1-005 | [MATHEMATICAL DERIV.]  | Reference update X*=X+u0 is        | F = d(x)/d(X*)       | F != I         | F = I, eps = 0,  | VERIFIED_FAIL   |
|            |                        | physically invalid                 | Strain and stress    | sigma != 0     | sigma = 0        | (DISQUALIFIED)  |
+------------+------------------------+------------------------------------+----------------------+----------------+------------------+-----------------+
| EVD-M1-006 | [MATHEMATICAL DERIV.]  | 1D chordal error formula produces  | eps(xi) =            | Illustrative   | +53.25% for      | PROPOSED_       |
|            |                        | +53.25% for coarse elements        | xi*coth(xi) - 1      | analytical     | h/l0 = 2.67      | GUIDELINE       |
+------------+------------------------+------------------------------------+----------------------+----------------+------------------+-----------------+
| EVD-M1-007 | [OFFLINE NUM. PROJ.]   | Forward transfer displacement error| ||u_recip - u_donor||| <= 1.0%        | 0.1347%          | VERIFIED_PASS   |
|            |                        | on 2,906 -> 14,677 FEs             | / ||u_donor|| (L2)   |                |                  |                 |
+------------+------------------------+------------------------------------+----------------------+----------------+------------------+-----------------+
| EVD-M1-008 | [OFFLINE NUM. PROJ.]   | Forward transfer peak damage error | |d_max^recip -       | <= 0.02        | 0.000000         | VERIFIED_PASS   |
|            |                        | at coincident notch tip node 129   | d_max^donor|         |                |                  |                 |
+------------+------------------------+------------------------------------+----------------------+----------------+------------------+-----------------+
| EVD-M1-009 | [OFFLINE NUM. PROJ.]   | Forward transfer damage integral   | |int d_recip -       | <= 5.0%        | 0.1322%          | VERIFIED_PASS   |
|            |                        | discrepancy across 2D domain       | int d_donor| / int d |                |                  |                 |
+------------+------------------------+------------------------------------+----------------------+----------------+------------------+-----------------+
| EVD-M1-010 | [OFFLINE NUM. PROJ.]   | Forward transfer history variable  | min(H_recip)         | >= 0.0         | 1.579e-9 kN/mm^2 | VERIFIED_PASS   |
|            |                        | non-negativity                     | across all GPs       | (0 negative)   | (0 negative GPs) |                 |
+------------+------------------------+------------------------------------+----------------------+----------------+------------------+-----------------+
| EVD-M1-011 | [OFFLINE NUM. PROJ.]   | Forward transfer internal node     | ||R_internal,0|| /   | <= 2.0%        | ~1.5 - 2.0%      | PROPOSED_       |
|            |                        | projection residual estimate       | ||F_ext,0||          |                | (~10 - 15 N)     | GUIDELINE       |
+------------+------------------------+------------------------------------+----------------------+----------------+------------------+-----------------+
| EVD-M1-012 | [ABAQUS DATACHECK]     | Native 14,677 FE recipient deck    | Abaqus datacheck     | Exit 0         | Exit 0 on        | VERIFIED_PASS   |
|            |                        | syntax and card wrapping validity  | preflight exit       |                | Job-2_UEL.inp    |                 |
+------------+------------------------+------------------------------------+----------------------+----------------+------------------+-----------------+
| EVD-M1-013 | [SOLVER RUNTIME VERIF.]| Abaqus fatal error on displacement | Solver execution of  | Rejection      | Exit 1 with      | VERIFIED_PASS   |
|            |                        | IC in general static step          | *INITIAL COND., DISP | recorded       | Error 144        | (LIMITATION)    |
+------------+------------------------+------------------------------------+----------------------+----------------+------------------+-----------------+
| EVD-M1-014 | [SOLVER RUNTIME VERIF.]| Single-increment coarsening force  | |RF_step2_inc1 -     | <= 5.0 N       | 21.55 N          | VERIFIED_FAIL   |
|            |                        | jump in Job 1412809                | RF_step1_end|        |                |                  | (DISCONTINUITY) |
+------------+------------------------+------------------------------------+----------------------+----------------+------------------+-----------------+
| EVD-M1-015 | [SOLVER RUNTIME VERIF.]| Coarse mesh crack pinning in       | F_max vs reference   | <= 0.78 kN     | 1085.41 N        | VERIFIED_FAIL   |
|            |                        | Job 1412809                        | (0.758 kN)           | (+3.0%)        | (+43.2%)         | (PINNING)       |
+------------+------------------------+------------------------------------+----------------------+----------------+------------------+-----------------+
| EVD-M1-016 | [SOLVER RUNTIME VERIF.]| Corrected Method B plateau         | RF at u >= 0.0060 mm | <= 0.005 kN    | 0.00208 kN       | VERIFIED_PASS   |
|            |                        | elimination (Job 1412465)          |                      | (plateau gone) | (plateau gone)   |                 |
+------------+------------------------+------------------------------------+----------------------+----------------+------------------+-----------------+
| EVD-M1-017 | [SOLVER RUNTIME VERIF.]| Corrected Method B matched work    | W_ext(u <= 0.0079 mm)| <= 2.45 mJ     | 2.2674 mJ        | VERIFIED_PASS   |
|            |                        | reduction vs reference             | vs Ref (2.3586 mJ)   | (within 5.0%)  | (-3.87% vs ref)  |                 |
+============+========================+====================================+======================+================+==================+=================+
```

---

## 6. Smallest C1 Experiment Specification & Four-Stage Progression

To establish an actionable, controlled experimental roadmap (pending explicit supervisor authorization), a disciplined four-stage progression is specified, anchored to authentic coarse donor Job 1411891 (`M1_PRE_1S`, $2,906$ FEs, $2,988$ physical nodes, $u = 0.0050\,\text{mm}$, $RF = 653.0886\,\text{N}$, $E_{\text{elas}} = 1.6327\,\text{mJ}$, $E_{\text{frac}} = 0.0307\,\text{mJ}$, $E_{\text{tot}} = 1.6634\,\text{mJ}$, $d_{\max} = 0.094910$ at Node 97, $H_{\max} = 53.6499\,\text{MPa}$ at Element 1208):

### 6.1 Four-Stage Gate 6C Qualification Sequence
1. **Stage C1-0: Same-Mesh Offset Reproduction ($2,906 \to 2,906$ FEs):**
   - *Objective:* Validate kinematic-offset continuation on the identical donor mesh. Analytical derivation demonstrates that zero geometric interpolation error does NOT independently guarantee an assembled zero residual ($\|\mathbf{R}_R^{(0)}\| \approx 0$) in an unimplemented continuation solver; simultaneous exact restoration of boundary conditions, mechanical DOFs 1 and 2, phase-field nodal DOF 3, quadrature SVARS, and dual-layer Fortran common block synchronization is mandatory.
   - *Displacement BC:* Held fixed at $u = 0.0050\,\text{mm}$ ($\Delta u_{\text{boundary}} = 0$).
   - *Phase-Field DOF:* Nodal DOF 3 must be initialized to donor values ($d = d_0$), avoiding uninitialized zero-compliance shock.
   - *Acceptance:* $|\Delta RF| = |RF_{\text{equil}} - 653.0886\,\text{N}| \le 0.5\,\text{N}$ ($< 0.1\%$); $|\Delta E_{\text{elas}}| \le 0.05\%$; $|\Delta d_{\max}| \le 10^{-5}$.
   - *Discipline:* Retract unsupported guarantees of "exactly 1 Newton iteration" or "unconditional positive definiteness". Standard Abaqus convergence criteria apply.
   - *Rollback:* If $|\Delta RF| > 2.0\,\text{N}$ or solver fails to converge at fixed boundary, halt immediately.
2. **Stage C1-1: Nonmatching Fixed-Displacement Equilibration ($2,906 \to 14,677$ FEs):**
   - *Objective:* Measure discrete projection residual norm $\|\mathbf{R}_R^{(0)}\|$ and verify static potential energy minimization ($\Delta \Pi \le 0$, with $\Delta E_{\text{elas, relax}} = -\mathcal{D}_{\text{num, relax}} \le 0$, rigorously distinguishing algorithmic energy minimization from physical thermodynamic dissipation with frozen damage $\Delta d = 0$).
   - *Acceptance:* Reaction force continuity $|\Delta RF| \le 5.0\,\text{N}$; relaxation energy $|\Delta E_{\text{elas, relax}}| / W_{\text{ext}} \le 2.0\%$; zero negative history ($\min(H) \ge 0$); no crack healing ($\Delta d \ge 0$).
   - *Rollback:* If cutbacks occur or $|\Delta RF| > 15.0\,\text{N}$, halt solver and preserve evidence.
3. **Stage C1-2: Small Forward Continuation ($u \in [0.0050, 0.0055]\,\text{mm}$):**
   - *Objective:* Advance displacement by $\Delta u = 0.0005\,\text{mm}$ to verify tangent stiffness and physical phase-field evolution prior to peak load.
   - *Acceptance:* Monotonic post-handoff load increase ($K_0 \approx 138\,\text{kN/mm}$); zero force plateau; smooth transition across handoff point without numerical snap.
   - *Rollback:* If crack pinning occurs ($RF$ hangs at $0.50 - 0.60\,\text{kN}$) or non-convergence triggers cutbacks, rollback to offline analysis.
4. **Stage C1-3: Prospective Native Remeshing and Continuation:**
   - *Objective:* Complete single genuine sequential cycle ($\text{Solve} \to \text{Remesh} \to \text{Transfer} \to \text{Continue}$) to full fracture.
   - *Scope Constraint:* Method C2 selective wake coarsening is strictly excluded from active scope. Only forward refinement is investigated.

- **Governance Guard:** None of these solver steps are executed without explicit supervisor authorization. Production UEL `f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`) remains 100% frozen; experimental offset logic is isolated on a dedicated branch.

---

## 7. Ten-Minute Presentation Outline for Supervisor Review (22 October 2026)

A disciplined 10-minute presentation is structured to walk the supervisor through the complete scientific sequence without operational jargon:

```
+=======================================================================================================================+
|                                      TEN-MINUTE PRESENTATION OUTLINE (10 SLIDES)                                      |
+=======+======================================+========================================================================+
| Slide | Topic / Milestone                    | Core Scientific Message & Key Visual                                   |
+=======+======================================+========================================================================+
| 1     | Problem Definition & Scope           | Mode-I tension benchmark (l_0 = 7.5 um). Governing thesis goal:       |
|       |                                      | energy-preserving adaptive remeshing vs brute-force uniform grids.     |
+-------+--------------------------------------+------------------------------------------------------------------------+
| 2     | Fixed-Mesh Reference Anchor          | 15,220 CPE4 uniform mesh (h = 3.75 um = l_0/2). F_max = 0.758 kN,       |
|       |                                      | W_ext = 2.359 mJ, clean brittle snap-through drop to RF < 0.001 kN.    |
+-------+--------------------------------------+------------------------------------------------------------------------+
| 3     | Method B Implementation & Plateau    | Load-partitioned pre-refinement (1S, 2S, 4S) yields 14.7k native mesh.|
|       |                                      | Solves linear elastic range, but exhibits unphysical 0.50-0.60 kN      |
|       |                                      | force plateau (+40.3% excess work).                                    |
+-------+--------------------------------------+------------------------------------------------------------------------+
| 4     | Root Cause: Stress Gradient          | Uncracked linear pre-analysis has no singularity ahead of notch tip    |
|       | Starvation & Dual-Metric Resolution  | (sigma ~ r^-1/2 at tip only). Coarse ligament (h ~ 20 um) pins crack.  |
|       | Audit                                | Reconciled metrics: 100% binned corridor vs 78.2% centerline chain.    |
+-------+--------------------------------------+------------------------------------------------------------------------+
| 5     | Method B Remediation & Verification  | Package 40 (14,483 FEs): 100% fine corridor across ligament            |
|       |                                      | eliminates plateau (RF -> 1.76 N, 99.76% drop, W_ext within 3.87%).    |
|       |                                      | Retrospective proof: resolving ligament is necessary & sufficient.     |
+-------+--------------------------------------+------------------------------------------------------------------------+
| 6     | Computational Sensitivity: dt_min    | Job 1413217 (M1_MB_DTMIN_8T) actively testing dt_min = 10^-15 to       |
|       | Cutback Traversal                    | overcome post-peak cutback clamping at u = 0.007889 mm.                |
+-------+--------------------------------------+------------------------------------------------------------------------+
| 7     | Commercial Software Barrier          | Native Abaqus/Standard blocks in-analysis continuation: Error 144 on   |
|       | in Abaqus/Standard                   | displacement ICs in *STATIC, zero displacement DOFs in solution ICs.  |
+-------+--------------------------------------+------------------------------------------------------------------------+
| 8     | Method C Feasibility & 4 Stages      | Disciplined progression: Stage C1-0 (same-mesh 2.9k->2.9k reproduction)|
|       |                                      | -> C1-1 (nonmatching equilibration) -> C1-2 (continuation) -> C1-3.   |
+-------+--------------------------------------+------------------------------------------------------------------------+
| 9     | Methodological Separation of 4 Goals | Strict decoupling: State Transfer (Demonstrated) vs Continuation       |
|       |                                      | (Software Blocked) vs Error Refinement vs Multi-Cycle Adaptivity.      |
+-------+--------------------------------------+------------------------------------------------------------------------+
| 10    | Decisions Requested from Supervisor  | 1. Sign off on closing Gate 6B (Method B fully understood & bounded).  |
|       |                                      | 2. Approve experimental Kinematic-Offset branch for Gate 6C Stage C1-0.|
|       |                                      | 3. Preserve frozen production UEL (CE8D5EDC...).                       |
+=======+======================================+========================================================================+
```

---

## 8. Comparative Method Matrix (A vs B vs C) & Gate 6B Closure Decision Package

### 8.1 Comparative Method Synthesis Matrix

```
+===========================================================================================================================+
|                                          COMPREHENSIVE METHOD COMPARISON MATRIX                                           |
+============================+==============================+==============================+================================+
| Feature / Characteristic   | Method A (Fixed Pre-Refined) | Method B (Load-Partitioned)  | Method C (Sequential Adaptive) |
+============================+==============================+==============================+================================+
| Operational Concept        | Single static mesh generated | Initial coarse solve -> one  | Solve -> assess -> remesh ->   |
|                            | before run; fixed from t = 0 | error evaluation -> single   | transfer -> continue cycles    |
|                            | to full fracture.            | remesh -> restart from t = 0 | during active crack growth.    |
+----------------------------+------------------------------+------------------------------+--------------------------------+
| Crack Path Dependency      | Requires strict a priori     | Prospective native starves   | Capable of tracking arbitrary, |
|                            | knowledge of crack path.     | uncracked ligament; requires | unknown, curved crack paths    |
|                            |                              | retrospective corridor seed. | autonomously.                  |
+----------------------------+------------------------------+------------------------------+--------------------------------+
| Force Plateau Status       | Eliminated (no plateau)      | Native: 0.55 kN plateau.     | Eliminates plateau if new mesh |
|                            |                              | Corrected: plateau gone.     | resolves active crack tip.     |
+----------------------------+------------------------------+------------------------------+--------------------------------+
| External Work Fidelity     | Reference benchmark (2.36 mJ)| Native: +40.3% excess work.  | Preserves energy across handoff|
|                            |                              | Corrected: -3.87% vs ref.    | (Delta E_elas <= 2.0%).        |
+----------------------------+------------------------------+------------------------------+--------------------------------+
| State Transfer Required    | None (continuous single run) | None (restarts from t = 0)   | Mandatory (u, d, H transfer)   |
|                            |                              |                              | across nonmatching meshes.     |
+----------------------------+------------------------------+------------------------------+--------------------------------+
| Abaqus Native Feasibility  | 100% Native                  | 100% Native                  | Fundamentally blocked in       |
|                            |                              |                              | native Abaqus (requires UEL    |
|                            |                              |                              | kinematic-offset architecture).|
+----------------------------+------------------------------+------------------------------+--------------------------------+
| Current Milestone Status   | FULLY QUALIFIED BENCHMARK    | CLOSED & BOUNDED (GATE 6B)   | UNQUALIFIED CANDIDATE (GATE 6C)|
| Role in Master's Thesis    | Authoritative physical anchor| Establishes limits of static | Active research frontier for   |
|                            | for accuracy comparison.     | error-guided pre-refinement. | algorithmic innovation.        |
+============================+==============================+==============================+================================+
```

### 8.2 Gate 6B Closure Recommendation & Supervisor Actions

1. **Gate 6B Formal Closure:**
   - The physics of Method B are completely understood: linear elastic pre-analysis cannot guide refinement into an uncracked ligament because stress singularities decay as $r^{-1/2}$ away from the notch tip.
   - Retrospective Package 40 proves that resolving the ligament restores physical softening ($RF \to 1.76\,\text{N}$, $W_{\text{ext}}$ within $3.87\%$).
   - 8-thread shared-memory SMP determinism and bitwise parity are rigorously certified (`THREAD_PARALLELIZATION_QUALIFIED`).
   - Gate 6B is recommended for immediate supervisor sign-off and formal closure.
2. **Gate 6C Experimental Roadmap (Conditional Authorization):**
   - Authorize development of the Kinematic-Offset UEL architecture on a separate development branch (`f42_experimental_offset_uel.for`).
   - Production UEL `f42_mixed_uel.for` (`CE8D5EDC...`) remains 100% frozen.
   - Approve Stage C1-0 ($2,906 \to 2,906$ FE same-mesh reproduction) as the first gate of Method C qualification.


