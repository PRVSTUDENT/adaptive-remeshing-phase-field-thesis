# Master Thesis Supervisor Meeting Talk Track -- 08 October 2026, 10:00

**Candidate:** Pruthviraja Reddy Vandavagali (Matr. Nr. 68865)  
**Supervisors:** Prof. Dipl.-Ing. Björn Kiefer, Ph.D., Dr.-Ing. Stephan Roth (IMFD)  
**Governing Directive:** *"We need to have understood everything related to the first model before we increase complexity."*  
**Active Scientific Phase:** `MODE1_GATE6B_ENERGY_CONVERGENCE_AND_STEP2_QUALIFICATION_ACTIVE`  
**Front-of-Pack Document:** [`MODE1_STEP2_LOCALIZATION_DECISION_SHEET.md`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/supervisor_reports/01-10-2026/MA_ModeI_Supervisor_Meeting_Pack_2026-10-01/MODE1_STEP2_LOCALIZATION_DECISION_SHEET.md) / [`MODE1_STEP2_LOCALIZATION_DECISION_SHEET.pdf`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/supervisor_reports/01-10-2026/MA_ModeI_Supervisor_Meeting_Pack_2026-10-01/MODE1_STEP2_LOCALIZATION_DECISION_SHEET.pdf)

---

## 0. Executive Decision Sheet: Mode-I Adaptive Localization Diagnosis & Baseline Selection (00:00 -- 06:00)
- **Problem Observed:** In our initial reproduction, evaluating the Abaqus `RemeshingRule` on the Step-1 pre-peak error field concentrated refinement only around the initial notch tip ($(0.5, 0.5)\,\mathrm{mm}$), with downstream elements coarsening rapidly along the ligament ($h_A = 4.68\,\mu\mathrm{m}$ at $x=0.65\,\mathrm{mm}$, $5.21\,\mu\mathrm{m}$ at $x=0.75\,\mathrm{mm}$, $12.58\,\mu\mathrm{m}$ at $x=0.90\,\mathrm{mm}$, exceeding $h \le l_0/2 = 3.75\,\mu\mathrm{m}$).
- **Verified Project Root Cause:** In linear elasticity (Step 1), no crack propagates, so stress gradients downstream are smooth. Evaluating `RemeshingRule` on Step-2 crack propagation, with all sizing and indicator parameters unchanged (`MISESERI`, target 1%, $h \in [1, 20]\,\mu\mathrm{m}$, `refinementFactor=10`, `All_elem`), captures the propagating front and continuously refines the horizontal ligament ($62{,}057$ finite elements).
- **Quantitative Improvements:**
  - Forward crack corridor elements: $3{,}351 \to 9{,}442$ ($+181.8\%$).
  - Wake elements: $1{,}773 \to 428$ ($-75.9\%$, suppressing unnecessary wake refinement).
  - Ligament intersects: $150 \to 293$ ($+95.3\%$).
  - Median $h_A$: $x=0.65\,\mathrm{mm} \to 1.20\,\mu\mathrm{m}$ ($-74.4\%$), $x=0.75\,\mathrm{mm} \to 1.49\,\mu\mathrm{m}$ ($-71.4\%$), $x=0.90\,\mathrm{mm} \to 3.86\,\mu\mathrm{m}$ ($-69.3\%$).
- **Epistemological Distinction:**
  - *Verified Project Root Cause:* Evaluated internally; resolves spatial localization deficit.
  - *Unknown Author Implementation Detail:* Pandey & Kumar (2025) omitted script-level step arguments; we cannot claim they used Step 2.
- **Mechanical Qualification & Audited HPC Solve:** Serial 1-CPU Job `1409585.mmaster02` solved to $u = 0.006554\,\text{mm}$, tracking smooth, stable softening ($F: 0.741 \to 0.089\,\text{kN}$, $87.9\%$ load drop) and planar crack advance across $94.0\%$ of the ligament with 0 solver warnings and 0 element distortions. Termination at breakthrough occurred due to the nonlinear solver control limit ($dt < 10^{-8}\,\text{s}$), classified under the Master Evidence Matrix as `ROOT_CAUSE_CANDIDATE_NOT_YET_RECONCILED` with zero retries.
- **Supervisor Decision Requested:**
  - *Option A:* Adopt Step-2 mesh ($62{,}057$ finite elements) as the thesis adaptive remeshing baseline, recognizing the successful $94\%$ ligament traversal and smooth softening.
  - *Option B:* Retain Step-1 ($48{,}329$ finite elements) as literal reproduction baseline; present Step-2 as project improvement.

---

## 1. Fixed Reference Anchor & Closed Historical Issues (06:00 -- 12:00)
- **Problem Formulation:** Single-edge-notched square plate ($1.0 \times 1.0\,\mathrm{mm}$) with a sharp, zero-gap horizontal seam crack ($a_0 = 0.5\,\mathrm{mm}$) along $y = 0.5\,\mathrm{mm}$.
- **Structural Stiffness Disambiguation:** Replacing the blunt finite-width notch ($K_0 \approx 75.47\,\mathrm{kN/mm}$) with the sharp zero-gap seam restored reference structural stiffness to $K_0 \approx 137.95\,\mathrm{kN/mm}$.
- **Fixed Reference Anchor (Job 1398090, 15,192 finite elements):**
  - Initial structural stiffness: $K_0 = 137.945520\,\mathrm{kN/mm}$ ($R^2 = 0.99999960$, unconstrained OLS over initial 400 increments, $u \le 1.0\,\mu\mathrm{m}$).
  - Peak reaction force: $F_{\max} = 0.757778\,\mathrm{kN}$ at $u(F_{\max}) = 0.005857\,\mathrm{mm}$.
  - Digitized reference (Pandey & Kumar, 2025, Fig. 7(a)): $F_{\max} \approx 0.758\,\mathrm{kN}$, $u(F_{\max}) \approx 0.005860\,\mathrm{mm}$.
- **Closed Prior Issues:**
  - `71,320-Mesh Stiffness Defect`: Proven to arise from Abaqus keyword `*NSET` 16-card line limit silently omitting 134/150 bottom nodes; corrected by card line wrapping, verified in Jobs 1405044 and 1404933 (`RESOLVED_AND_CLOSED`).
  - `13,941 vs 71,320 Reproduction Discrepancy`: Supervisor accepted publication limitation (`SUPERVISOR_ACCEPTED_REPRODUCTION_LIMITATION_CLOSED`); parametric sensitivity trends preserved ($1.0\% \to 71{,}320$, $2.0\% \to 17{,}687 / 15{,}396$, $3.0\% \to 8{,}120 / 7{,}633$, $5.0\% \to 4{,}356 / 4{,}194$).

---

## 2. Priority 1: UEL Energy Formulation & Global Energy Audit (12:00 -- 22:00)
- **Mathematical Formulations:**
  - Stored elastic strain energy: $E_{\mathrm{elas}} = \sum_e \int_{\Omega_e} \frac{1}{2} g(\bar{d}_e) \boldsymbol{\varepsilon} : \mathbb{C}_0 : \boldsymbol{\varepsilon} \,\mathrm{d}\Omega$.
  - Fracture surface energy: $E_{\mathrm{frac}} = \sum_e \int_{\Omega_e} G_c \left[ \frac{\bar{d}_e^2}{2 l_0} + \frac{l_0}{2} |\nabla d|^2 \right] \mathrm{d}\Omega$.
  - External boundary work: $W_{\mathrm{ext}} = \int_0^u F(\tilde{u})\,\mathrm{d}\tilde{u} \approx W_{\mathrm{trap}}$.
- **Single-IP Deduplication Rule:** Companion visualizer UMAT elements (Layer 3, CPE4) replicate scalar element energies across all 4 Gauss integration points. Summing all 4 IPs creates an unphysical $4\times$ overcounting artifact ($4 E_{\mathrm{elas}}$). Extracting **Integration Point 1 (IP1) only** strictly recovers the once-per-element global energy integral under 2D plane strain ($B = 1.0\,\mathrm{mm}$).
- **Non-Invasiveness & Bit-for-Bit Parity:** Energy calculation does not enter element residual (`RHS`) or stiffness (`AMATRX`). Proven bit-for-bit identical against uninstrumented baselines across elastic (30 incs) and fully softened post-peak states (129 incs, $u = 0.035\,\mathrm{mm}$, $|\Delta F| = 0.0\,\mathrm{kN}$).
- **Discrete Potential Non-Existence & Observability Boundary:**
  - Because the staggered solver alternates between displacement $\mathbf{u}_n$ and damage $d_{n+1}$, discrete cross-derivatives do not commute ($\partial^2 \Pi / \partial \mathbf{u} \partial d \ne \partial^2 \Pi / \partial d \partial \mathbf{u}$).
  - Standard Abaqus ODB files do not persist within-increment Newton subiteration paths.
  - Therefore, the quantity $\Delta_{\mathrm{book}} \equiv W_{\mathrm{trap}} - (E_{\mathrm{elas}} + E_{\mathrm{frac}})$ is strictly designated as the `TWO_TERM_BOOKKEEPING_DIFFERENCE`, and `GLOBAL_ENERGY_IDENTITY --- NOT_YET_CLOSED` is strictly maintained.

---

## 3. Priority 2: Multifaceted Mode-I Convergence Findings (22:00 -- 30:00)
- **Spatial Fixed-Mesh Series ($S_1$--$S_4$, $h/l_0 \in [0.167, 0.400]$):**
  - Initial stiffness $K_0$ is exceptionally stable: $137.84$ to $137.95\,\mathrm{kN/mm}$ ($\Delta < 0.09\%$, $R^2 > 0.999999$). Classified as `CONVERGED / STABLE`.
  - Peak reaction force $F_{\max}$ drops monotonically from $0.7578\,\mathrm{kN}$ ($S_1$) to $0.7312\,\mathrm{kN}$ ($S_4$) (extending to $0.7255\,\mathrm{kN}$ on historical fine mesh, $4.26\%$ total variation). Classified as `MESH-SENSITIVE`.
  - Spatial energetic convergence at $u = 6.20\,\mu\mathrm{m}$: $E_{\mathrm{frac}}$ varies by $1.56\%$ across $S_1$--$S_4$ ($2.33886 \to 2.37531\,\mathrm{mJ}$), classified as `STABLE_OVER_TESTED_RANGE`.
- **Temporal Series ($T_1$--$T_3$):**
  - Peak force $F_{\max}$ invariant under time-step scaling ($<0.07\%$, $0.75815 \to 0.75763\,\mathrm{kN}$). Classified as `CONVERGED / STABLE`.
  - External work and bookkeeping difference are temporally sensitive ($W_{\mathrm{trap}} = 2.4101 \to 2.3319\,\mathrm{mJ}$, $\Delta_{\mathrm{book}} = +0.38\% \to +3.54\%$).
- **Adaptive Series ($A_1$--$A_4$):**
  - Pre-peak stiffness and work agree with reference anchor within $0.01\%$.
  - Post-peak plateau on coarse background meshes ($A_2$--$A_4$) associated with coarse elements outside the crack corridor.

---

## 4. Crack-Path Symmetry, Localization & Length-Scale Study (30:00 -- 37:00)
- **Crack Centroid Trajectory:** Damage-weighted crack-centroid offset $|y_c - 0.500\,\mathrm{mm}| \le 3.10\,\mu\mathrm{m}$ across all fixed and adaptive meshes, confirming pure Mode-I symmetry within element bounds.
- **Diffusive Localization Band:** Full transverse width $w_{d \ge 0.5} \approx 20.0$--$30.0\,\mu\mathrm{m}$ across the ligament ($20.0$--$22.9\,\mu\mathrm{m}$ at $x = 0.55\,\mathrm{mm}$), qualified as `MESH-SENSITIVE / RESOLUTION-LIMITED`.
- **Completed 3-Point Length-Scale Study:** Single-factor $l_0$ parameter sweep ($l_0 \in \{7.5, 11.25, 15.0\}\,\mu\mathrm{m}$ with $h/l_0 \le 0.20$) on qualified $S_3$ mesh (Jobs 1406017, 1406895, 1406896). $K_0$ stable within $0.13\%$; $F_{\max}$ sensitive ($0.732 \to 0.690\,\mathrm{kN}$).

---

## 5. Thesis Integration & Next Decisions (37:00 -- 45:00)
- Presentation of updated thesis chapters (Chapters 1--3, 7--8) reflecting all verified Mode-I evidence.
- Request supervisor approval on Gate 6B closure acknowledging `GLOBAL_ENERGY_IDENTITY --- NOT_YET_CLOSED`.
- Decision on Step-2 Adaptive Remeshing Baseline (Option A vs Option B).
- Authorization to proceed to Gate 6C (Mode-I State-Transfer Energy Conservation).
- Reaffirmation of strict holds on Mode-II, multi-crack configurations, and Gate 7 (ABAQUSER).
