# Mode-I Method B Evidence Audit, Prospective Adaptive Remeshing Limitations, and 22 October 2026 Supervisor Decision Package

**Document ID:** `MODE1_METHOD_B_EVIDENCE_AUDIT_AND_SUPERVISOR_DECISION_PACKAGE.md`  
**Milestone:** Task F1465 — Validate Frozen Method B Evidence, Audit Adaptive-Remeshing Conclusions, and Complete the 22 October Supervisor Decision Material  
**Date:** 2026-10-14T21:30:00+02:00  
**Author:** Gemini Antigravity (Autonomous Execution Agent)  
**Institution:** Institute of Mechanics and Fluid Dynamics (IMFD), TU Bergakademie Freiberg  
**Authoritative Fortran Source:** `models/pandey_kumar_mode1/f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`)  
**Governing Directive:** *"We need to have understood everything related to the first model before we increase complexity."*  
**Classification:** `SCIENTIFIC_AUDIT_AND_DECISION_PACKAGE_COMPLETE`

---

## 1. Immediate HPC Submission Decision & Cluster Queue Status

In strict accordance with the mandatory operational sequence ("Put job submission before report work" and "State why the queue is idle"):

1. **Live Scheduler Inspection:**
   A non-interactive, bounded query of the TU Freiberg cluster queue `normal_imfdfkmq` via guarded SSH (`qstat -u pr21vyci`) confirmed **0 active, queued, or running jobs** for user `pr21vyci`.
2. **Terminal Records and Certification of Completed Jobs:**
   - **Job `1412872.mmaster02` (Native Method B 14,677 FE, 8-Thread SMP Repeat):** Completed all 5,000 increments in Step 2 (7,000 increments total, $u = 0.0100\,\text{mm}$, Exit 0, walltime 05:12:04, $1.87\times$ speedup vs serial). Certified with `THREAD_PARITY_PASS` and `THREAD_DETERMINISM_PASS` via bitwise identical SHA-256 hash (`792be67d...`) of `uel_energy_balance.csv` against both serial baseline `1411934` and initial 8T solve `1411949`.
   - **Job `1412873.mmaster02` (Corrected Method B 14,483 FE, 8-Thread SMP Parity):** Completed Step 1 (2,000 incs) and advanced to Step 2 Increment 2890 (4,890 increments total, $u = 0.007889\,\text{mm}$, Exit 1, walltime 03:35:22, $1.82\times$ speedup vs serial). Certified with `THREAD_PARITY_PASS` via bitwise identical SHA-256 hash (`82f2963d...`) against serial baseline `1412465`.
3. **Scientific Justification for Idle Queue Status:**
   - *Candidate A (Prospective Native Remeshing Repeat):* Sizing controls in native `RemeshingRule` leave the uncracked ligament coarse ($h \approx 20\,\mu\text{m} \gg \ell_0/2$). Re-running prospective pre-refinement would merely regenerate the known coarse-ligament crack-pinning plateau ($0.50-0.60\,\text{kN}$) and $+40.3\%$ excess work, violating scheduler anti-redundancy rules.
   - *Candidate B (Post-Severance Artificial Relaxation):* Job `1412873` already captured $99.76\%$ of physical brittle fracture ($RF = 1.76\,\text{N}$ vs peak $743.7\,\text{N}$) with contiguous crack front formation across $99.9\%$ of the ligament. Continuing numerical relaxation on two completely severed halves held only by residual artificial stiffness $k_{\text{stab}} = 10^{-7}$ provides zero new physical fracture information.
   - *Candidate C (Method C In-Analysis Continuation):* Gate 6C remains on strict hold pending formal supervisor review and sign-off on 22 October 2026. Submitting unauthorized Method C solver runs is strictly prohibited by governance.
4. **Conclusion:** No unanswered, scientifically useful Mode-I question exists that can be resolved without modifying the frozen UEL or bypassing Gate 6C. The cluster queue is legitimately idle in full compliance with project governance.

---

## 2. Strong-Form AT-2 Phase-Field Audit vs Exact Fortran Weak Form

### 2.1 Weak Form in Production UEL (`f42_mixed_uel.for`)
The production user element (`f42_mixed_uel.for`, SHA-256: `CE8D5EDC...`) implements the coupled staggered phase-field system. In Layer 1 (phase-field UEL), the element residual vector `RHS` and stiffness matrix `AMATRX` are assembled at each integration point as follows (lines 341--370):

```fortran
AMATRX(I,J) = AMATRX(I,J) + CJAC * (
     1 (E_GC * E_L0) * BDB +
     2 (E_GC / E_L0 + TWO * HIST) * N_VEC(I) * N_VEC(J) )
RHS(I,1) = RHS(I,1) + CJAC * TWO * HIST * N_VEC(I)
...
RHS(I,1) = RHS(I,1) - AMATRX(I,J) * U(J)
```

At Newton-Raphson equilibrium ($RHS = 0$), the discrete weak form equation corresponds to:
$$\int_\Omega \left[ \left(\frac{G_c}{\ell_0} + 2H\right) d - 2H \right] \delta d\,\mathrm{d}\Omega + \int_\Omega G_c \ell_0 \nabla d \cdot \nabla(\delta d)\,\mathrm{d}\Omega = 0$$

### 2.2 Strong-Form Euler--Lagrange Derivation
Applying integration by parts under natural Neumann boundary conditions ($\nabla d \cdot \mathbf{n} = 0$ on $\partial\Omega$):
$$\int_\Omega \delta d \left[ \left(\frac{G_c}{\ell_0} + 2H\right) d - G_c \ell_0 \nabla^2 d - 2H \right] \mathrm{d}\Omega = 0$$
Because this holds for all admissible test variations $\delta d$, the strong-form governing equation is:
$$\left(\frac{G_c}{\ell_0} + 2H\right) d - G_c \ell_0 \nabla^2 d = 2H$$
Dividing the entire equation by 2 yields the standard canonical form:
$$(H + \psi_0)\,d - \frac{1}{2} G_c \ell_0 \nabla^2 d = H \quad \iff \quad (H + \psi_0)\,d - \psi_0 \ell_0^2 \nabla^2 d = H$$
where:
$$\psi_0 \equiv \frac{G_c}{2\ell_0} = \frac{0.0027\,\text{kN/mm}}{2 \times 0.0075\,\text{mm}} = 0.180\,\text{kN/mm}^2 = 180.0\,\text{MPa}$$
and the regularizing diffusion factor satisfies:
$$\frac{1}{2} G_c \ell_0 = \left(\frac{G_c}{2\ell_0}\right) \ell_0^2 = \psi_0 \ell_0^2$$

### 2.3 Dimensional Consistency and Zero-Gradient Limit
- **Dimensional Consistency:**
  - $[H] = \text{MPa} = \text{N/mm}^2$
  - $[\psi_0] = \text{MPa}$
  - $[\psi_0 \ell_0^2 \nabla^2 d] = \text{MPa} \times \text{mm}^2 \times \text{mm}^{-2} = \text{MPa}$
  - Every term in $(H + \psi_0) d - \psi_0 \ell_0^2 \nabla^2 d = H$ has consistent physical units of energy density / stress ($\text{MPa}$).
- **Zero-Gradient Scalar Limit ($\nabla^2 d = 0$):**
  $$(H + \psi_0) d_{\mathrm{hom}} = H \implies d_{\mathrm{hom}} = \frac{H}{H + \psi_0}$$
  For pre-peak Mode-I notch history $H_{\max} \approx 18.88\,\text{MPa}$:
  $$d_{\mathrm{hom}} = \frac{18.88}{18.88 + 180.0} = \frac{18.88}{198.88} \approx 0.09493$$
  This matches the coarse $2{,}906$-element pinned peak $d_{\max} = 0.094910$ (Job `1411891`), where element size $h \approx 20\,\mu\text{m} > 2.6\,\ell_0$ suppresses the sub-element curvature of the Laplacian operator.
- **Coupled Finite Element Laplacian Diffusion:**
  At a localized notch tip, steep negative curvature ($\nabla^2 d < 0$) induces regularizing spatial diffusion via $-\psi_0 \ell_0^2 \nabla^2 d > 0$. When the mesh is adequately resolved ($h \le \ell_0/4$), this coupled spatial operator allows the physical damage to concentrate sharply, reaching $d_{\max} = 0.3195$ at the identical macroscopic displacement $u = 0.0050\,\text{mm}$ (Job `1411934`).

---

## 3. Re-Examination of Prospective Remeshing Limitations

### 3.1 Asymptotic Scaling vs Elementwise Error Indicators
In prior discussions (F1464), an asymptotic scaling argument was proposed:
$$\sigma_{ij} \sim K_I r^{-1/2} \implies |\nabla \boldsymbol{\sigma}| \sim r^{-3/2}$$
While this power-law decay correctly illustrates why linear-elastic stress gradients attenuate rapidly away from a stationary notch tip, it does not constitute an abstract impossibility theorem for prospective adaptive remeshing.

### 3.2 Numerical Findings Across `errorTarget` Studies (1%, 2%, 3%, 5%)
The actual remeshing in Abaqus is driven by the elementwise Zienkiewicz--Zhu stress-recovery error indicator:
$$\eta_e = \frac{\|\boldsymbol{\sigma}^* - \boldsymbol{\sigma}_h\|_{L^2(e)}}{\|\bar{\boldsymbol{\sigma}}\|_{L^2(\Omega)}}$$
Empirical parametric studies varying `errorTarget` across $1\%$, $2\%$, $3\%$, and $5\%$ demonstrate:
1. **At `errorTarget` = 1%:** Refinement is triggered globally throughout the specimen, generating an excessively dense mesh of over $71{,}000$ elements, which defeats the computational objective of localized adaptivity.
2. **At `errorTarget` = 2%, 3%, 5%:** Refinement localizes in a tight circular bubble around the notch tip ($r \le 0.10\,\text{mm}$), but drops below the refinement threshold along the symmetry ligament ($x \in [0.55, 1.00]\,\text{mm}$), leaving elements at $h \approx 20\,\mu\text{m} > 2.6\,\ell_0$.
3. **Synthesis:** This behavior establishes an **empirical limitation of the tested native configuration and indicator parameters**, rather than an abstract mathematical impossibility theorem for all conceivable prospective remeshing techniques (such as damage-gradient, strain-energy-density-gradient, or automated corridor-tracking indicators).

---

## 4. Consolidated 4-Model Method B Evidence Matrix

To evaluate Method B rigorously and transparently, the table below compares the four central Mode-I benchmark discretizations over the common matched displacement horizon $u \in [0.0, 0.007889]\,\text{mm}$ (capturing $>99.76\%$ of brittle load drop):

| Metric / Quantity | Canonical Reference | Historical ET2 | Original Native Method B | Retrospective Corrected B | Metric Significance |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Job ID (Serial 1-CPU)** | `1398090` | `1411895` | `1411934` | `1412465` | Authoritative serial solves |
| **Job ID (8T SMP)** | --- | `1411950` | `1411949` / `1412872` | `1412873` | Certified 8T SMP execution |
| **Discretization Type** | Fixed Uniform | Fixed Pre-Refined | Native Pre-Refined | Retrospective Pre-Refined | Generation methodology |
| **Finite Elements** | $15{,}192$ | $6{,}112$ | $14{,}677$ | $14{,}483$ | Physical finite elements |
| **Element Records (3 layers)**| $45{,}576$ | $18{,}336$ | $44{,}031$ | $43{,}449$ | Co-located UEL/UMAT records |
| **Corridor Resolution** | $h = 3.75\,\mu\text{m} = l_0/2$ | $h = 5.0\,\mu\text{m} = 0.67 l_0$ | $h \approx 19.7\,\mu\text{m} > 2.6 l_0$ | $h \le 3.75\,\mu\text{m} = l_0/2$ ($96.8\%$) | Ligament element size |
| **Initial Stiffness $K_0$** | $137.9455\,\text{kN/mm}$ | $137.8900\,\text{kN/mm}$ | $137.8919\,\text{kN/mm}$ | $137.9096\,\text{kN/mm}$ | $\Delta K_0 \le -0.040\%$ across all 4 |
| **Linear Correlation $R^2$** | $0.9999996$ | $0.9999996$ | $0.9999996$ | $0.9999996$ | Linear elastic fit ($u \le 1.0\,\mu\text{m}$) |
| **Peak Force $F_{\max}$** | $0.757802\,\text{kN}$ | $0.756400\,\text{kN}$ | $0.743021\,\text{kN}$ | $0.743701\,\text{kN}$ | Peak load parity within $1.9\%$ |
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
| **8T SMP Runtime** | --- | 02:52:08 (Job 1411950) | 05:12:04 (Job 1412872) | 03:35:22 (Job 1412873) | 8-thread shared memory solve |
| **8T SMP Speedup & Parity** | --- | $1.67\times$ (`PARITY_PASS`) | $1.87\times$ (`DETERM_PASS`) | $1.82\times$ (`PARITY_PASS`) | Bitwise identical CSV traces |

$^*$Evaluated at verified terminal state $u = 0.007889\,\text{mm}$ ($RF = 1.7645\,\text{N}$, $99.76\%$ softened).  
$^\dagger$Solver encountered $dt < dt_{\min} = 10^{-9}$ during rigid-body separation of severed halves; nominal $0.0100\,\text{mm}$ horizon was not reached.

---

## 5. Precise Operational Distinctions: Methods A, B, and C

To prevent methodological conflation across the thesis chapters and supervisor briefing:

1. **Method A (Fixed Offline Pre-Refinement):**
   - *Definition:* A single static discretization is created *prior* to solver execution with a fine mesh corridor ($h \le \ell_0/2$) pre-seeded along the entire anticipated crack path (e.g. Canonical Reference 15k, Historical ET2 6.1k). The simulation runs from $t = 0$ to $t_{\text{final}}$ on this frozen mesh.
   - *Scope & Limitations:* Requires complete *a priori* knowledge of the crack trajectory. It is an engineering baseline, not an automated adaptive remeshing method.
2. **Method B (Load-Partitioned Offline Pre-Refinement with Remeshing Rule):**
   - *Definition:* An initial simulation is executed on a coarse mesh ($M_0$) up to an intermediate pre-peak load step ($u_{\text{pre}} = 0.0050\,\text{mm}$). Abaqus built-in `RemeshingRule` evaluates an error indicator ($\MISESERI$) on a companion linear-elastic continuum overlay. Exactly **one** remeshing cycle is performed ($M_0 \to M_1$). The fracture simulation is then restarted from $t = 0$ on the new mesh $M_1$.
   - *Key Findings:* Loading steps (1S, 2S, 4S) are NOT remeshing cycles. The pre-peak linear-elastic error field is strictly path-independent and scale-invariant ($\Delta \eta_{\max} = 0.0$). Because the pre-analysis stops before crack propagation, the stationary notch stress concentration leaves the uncracked ligament coarse ($h \approx 20\,\mu\text{m}$), producing severe crack pinning ($0.50-0.60\,\text{kN}$ plateau, $+40.3\%$ work). Extending the corridor across the ligament (Corrected Method B) completely eliminates the plateau and restores brittle fracture, but was derived *retrospectively* from a donor state where the crack had already propagated.
3. **Method C (Sequential In-Analysis Adaptive Remeshing during Propagation):**
   - *Definition:* True automated adaptive fracture simulation: $\text{Solve} \to \text{Evaluate Error} \to \text{Remesh} \to \text{Transfer State} \to \text{Continue}$, repeated sequentially during active crack propagation.
   - *Documented Milestone Status:* One authentic coarse-to-fine candidate ($2{,}906 \to 14{,}677$ FEs) and offline state transfer have been verified, but **zero complete sequential remeshing-and-continuation cycles have been qualified in the solver**. Multi-cycle experiments remain un-demonstrated. Commercial Abaqus/Standard constraints (rejection of displacement ICs in `*STATIC`, zero DOFs in solution ICs, lack of UEL mapping support) fundamentally block native in-analysis continuation.

---

## 6. The 22 October 2026 Supervisor Decision Package

The following three formal decision requests are consolidated for the supervisor meeting:

### 6.1 Decision Request 1: Formal Sign-Off of Gate 6B (Method B)
- **Proposed Classification:** `METHOD_B_SCIENTIFIC_OBJECTIVE_COMPLETED_WITH_PARTIAL_HORIZON_LIMITATION`
- **Justification:** Corrected Method B conclusively resolved the central research question by eliminating the artificial $0.50-0.60\,\text{kN}$ force plateau, restoring physical brittle snap-through softening, and reducing external work by $31.4896\%$ (from $3.309642\,\text{mJ}$ down to $2.267448\,\text{mJ}$ over the common matched horizon $u \le 0.007889\,\text{mm}$, within $-3.87\%$ of canonical reference $2.3586\,\text{mJ}$). All claims are strictly scoped to the verified common horizon $u \in [0.0, 0.007889]\,\text{mm}$ (capturing $>99.76\%$ softening).

### 6.2 Decision Request 2: Formal Evaluation of Gate 6C (Method C)
- **Proposed Classification:** `OFFLINE_TRANSFER_QUALIFIED__CONTINUATION_NOT_QUALIFIED`
- **Justification:** Milestone 1 (native mesh refinement) and Milestone 2 (offline mathematical state transfer) meet all Gate 6C criteria ($L_2 = 0.13\%$, $\Delta d = 0.000000$, $\min(\Hist) \ge 0.0$, compliance disparity $1.67\%$). Milestone 3 (in-analysis mechanical continuation in Abaqus/Standard) cannot be achieved natively due to commercial software constraints (rejection of displacement ICs in `*STATIC` Error 144, zero DOFs in solution ICs, lack of UEL mapping). Zero complete sequential remeshing-and-continuation cycles have been qualified in the solver.

### 6.3 Decision Request 3: Strategic Thesis Path Forward
- **Options Submitted for Supervisor Determination:**
  - **Option A (Preserve & Report Baseline Methods):** Preserve and report Methods A and B as verified offline pre-refinement engineering workflows, alongside rigorous documentation of commercial Abaqus/Standard Method C feasibility limitations and architectural software barriers, without further solver modifications.
  - **Option B (Investigate Separate Experimental Continuation Architecture):** Authorize implementing and evaluating the smallest isolated experimental C1 continuation prototype on a dedicated development branch (`f42_experimental_offset_uel.for`), keeping the authoritative baseline `f42_mixed_uel.for` (`CE8D5EDC...`) strictly unchanged and protected.
- **Epistemic Discipline:** The choice between Option A and Option B belongs strictly to the user and supervisor. General PBS permission does NOT authorize C1 solver execution without explicit supervisor review.

---

## 7. Verification and Governance Traceability

- **Production UEL Hash:** `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` (100% verified and preserved).
- **Active Task Ledger Status:** F1465 marked `COMPLETED` upon review.
- **Cluster Scratch Safety:** All outputs strictly conform to cluster scratch policy with zero heavy simulation binaries committed to git.
