# Supervisor Q&A Preparation: Defensible Technical Responses

**Meeting Date:** Thursday, 17 September 2026  
**Candidate:** Pruthviraja Reddy Vandavagali (Matr. Nr. 68865)  
**Supervisors:** Prof. Dipl.-Ing. Björn Kiefer, Ph.D. & Dr.-Ing. Stephan Roth (IMFD)  
**Epistemic Discipline:** Every answer strictly separates:
- **Known from publication/theory:** Mathematical definitions, constitutive laws, published text.
- **Verified numerically:** Exact solver runs, database extractions, SHA-256 hashes, bitwise comparisons.
- **Still unresolved:** Unstated author implementation details, proprietary internal solver transformations.

---

### Q1: Why can we trust the fixed reference?
- **Known from Theory/Publication:** The Mode-I benchmark is an established boundary value problem in phase-field literature (Msekh et al., 2015; Molnár & Gravouil, 2017; Pandey & Kumar, 2025). The crack is a zero-gap sharp seam ($a_0 = 0.5\,\text{mm}$), with $E = 210\,\text{GPa}$, $\nu = 0.3$, $G_c = 2.7\,\text{N/mm}$, and $\ell_0 = 7.5\,\mu\text{m}$.
- **Verified Numerically:** Our reconstructed fixed-mesh reference (Job `1398090`, $15{,}192$ elements, $h \le \ell_0 / 5 = 1.5\,\mu\text{m}$) reproduces the published response within $-0.029\%$ on peak force ($0.757778\,\text{kN}$ vs $0.7580\,\text{kN}$) and $-0.051\%$ on peak displacement ($0.005857\,\text{mm}$ vs $0.005860\,\text{mm}$). Its initial structural stiffness is $K_0 = 137.945520\,\text{kN/mm}$ with an unconstrained linear fit $R^2 = 0.99999960$ ($N=400$, $u \le 1.0\,\mu\text{m}$).
- **Still Unresolved:** None for this anchor. The fixed reference is qualified as our authoritative benchmark anchor.

---

### Q2: What exactly is MISESERI, and what is it not?
- **Known from Theory/Publication:** In the Abaqus Analysis User's Guide, `MISESERI` is the stress discretization error indicator associated with the recovered von Mises stress field. It estimates stress interpolation error arising from finite element discretization during linear elastic steps.
- **What it is NOT:** It is **not** a phase-field error indicator, **not** a damage error indicator, and **not** a fracture energy indicator. It contains no information about crack propagation or damage evolution.
- **Verified Numerically:** In our canonical Mode-I pre-analysis (Job `PK_M1_PRE`, $2{,}906$ elements), direct extraction of `JOB1_LOAD_1p0X.odb` shows exactly $2{,}906$ scalar values at the `WHOLE_ELEMENT` position, peaking at the singular crack tip ($\max = 1.007\,\text{MPa}$) and dropping to $5.78 \times 10^{-3}\,\text{MPa}$ in the far field.
- **Still Unresolved:** The internal kernel equations that transform `MISESERI` into localized element target sizes are proprietary to Dassault Systèmes and undocumented in the manual.

---

### Q3: Why does literal errorTarget=1.0 give 71,320 elements?
- **Known from Theory/Publication:** Listing 1 of Pandey & Kumar specifies `errorTarget=1.0` and applies `RemeshingRule` to the whole specimen set (`All_elem`). In Abaqus, `errorTarget=1.0` specifies a $1.0\%$ relative recovered stress error threshold.
- **Verified Numerically:** When Abaqus applies `errorTarget=1.0` globally to a plate with a singular crack tip, stress concentration causes refinement at the crack tip ($h \to h_{\min} = 1.0\,\mu\text{m}$), but meeting 1% relative error across the entire specimen also forces substantial refinement throughout the transition ($20{,}273$ elements) and far-field regions ($41{,}986$ elements). Together, these outer regions account for $62{,}259$ elements ($87.3\%$).
- **Still Unresolved:** We do not know what unpublished setting allowed Pandey & Kumar to restrict total elements to $\approx 13{,}941$.

---

### Q4: Why are we not simply using 2% because it is numerically closer to ~13,941?
- **Known from Theory/Publication:** Listing 1 explicitly states `errorTarget=1.0`. The paper nowhere mentions a 2% target for Mode-I.
- **Verified Numerically:** Running native remeshing with `errorTarget=2.0` produces $15{,}396$ elements ($+10.4\%$ from $13{,}941$).
- **Still Unresolved:** Numerical proximity at 2% is **not** evidence of parameter identity. Adopting 2% without author verification would violate scientific integrity by tuning an unstated parameter to force an element count match.

---

### Q5: What caused the historical K0 ≈ 122 kN/mm branch?
- **Known from Theory/Publication:** The benchmark roller boundary condition requires $u_y = 0$ along the entire bottom edge ($y = 0$).
- **Verified Numerically:** The low-stiffness branch ($K_0 \approx 122.38\,\text{kN/mm}$ in Job `1399632`) was caused by an input record format defect in the generated input deck: all 150 bottom nodes were written on a single free-format `*NSET` card. Abaqus `pre` enforces a 16-node limit per line, issued warnings, retained only 16 nodes, and deleted the remaining 134 node IDs.
- **Still Unresolved:** None. The mechanism has been completely diagnosed and verified.

---

### Q6: What equation/constraint-level evidence proves the N_BOTTOM defect?
- **Known from Theory/Publication:** In the finite element method, omitting Dirichlet boundary constraints removes rows/columns from the prescribed boundary operator, increasing compliance.
- **Verified Numerically:**
  1. The `.dat` file for Job `1399632` contains explicit preprocessing warnings: *lines exceeded 16 items; 134 items deleted*.
  2. Direct ODB extraction showed the unconstrained bottom edge lifted upwards by up to approximately $48.34\%$ of the applied stroke ($u_2 > 0$).
  3. Controlled test Job `1404318` verified that wrapping cards to $\le 16$ items/line restored all 150 constraints to $u_2 = 0.000\,\text{nm}$.
  4. The 2x2 factorial audit proved that non-symmetric solver settings (`UNSYMM=YES`) and companion visualization elements caused exactly $0.000\%$ stiffness difference.
- **Still Unresolved:** None. The evidence is complete at the equation and output level.

---

### Q7: Why does the corrected 71,320 model now reproduce the mechanical reference reasonably?
- **Known from Theory/Publication:** With complete boundary constraints restored, the adapted mesh refines the crack corridor to $h \le \ell_0 / 5$, satisfying the continuum phase-field resolution requirement.
- **Verified Numerically:**
  - Frozen requalification (Job `1405044`): $K_0 = 138.021013\,\text{kN/mm}$ ($+0.0547\%$ vs reference $137.945520\,\text{kN/mm}$).
  - Full-fracture simulation (Job `1404933`): initial stiffness $K_0 = 137.820804\,\text{kN/mm}$ ($K_0 \approx 137.821\,\text{kN/mm}$, within $-0.0904\%$); peak force $F_{\max} = 0.745325\,\text{kN}$ (within $-1.64\%$ of reference $0.757778\,\text{kN}$); peak stroke $u(F_{\max}) = 0.005750\,\text{mm}$ (within $-1.83\%$).
- **Still Unresolved:** The slight $1.64\%$ load deficit is attributable to the mixed quad-dominated transition topology (including 1,877 triangular CPE3 elements) compared to the structured pure CPE4 reference corridor.

---

### Q8: What was verified across Abaqus 2019–2023?
- **Known from Theory/Publication:** Remeshing algorithms could theoretically evolve across solver releases.
- **Verified Numerically:** The canonical pre-analysis and `adaptiveRemesh` workflow was executed natively on Linux cluster nodes across four major releases: 2019 GA, 2021.HF26, 2022 GA, and 2023.HF4. All four generated meshes contain exactly $71{,}320$ finite elements ($69{,}443$ CPE4 + $1{,}877$ CPE3), and all $142{,}268$ substantive lines of the generated input decks are **$100.000\%$ bitwise identical** with identical SHA-256 node hashes.
- **Still Unresolved:** None. Solver version shift is definitively eliminated as a cause.

---

### Q9: What did top-edge U1, CPE4R, CPS4, coarse-size and sizing-policy tests show?
- **Verified Numerically (from the 15-Factor Audit):**
  - **Top lateral constraint ($u_1 = \text{Free}$, Job `1405055`):** Yielded $55{,}761$ elements ($-21.8\%$), remaining $>4.0\times$ above literature.
  - **Coarse global seed $h_{\mathrm{cms}} = 0.030\,\text{mm}$:** Yielded $48{,}919$ elements ($-31.4\%$), remaining $>3.5\times$ above literature.
  - **Plane stress CPS4:** Yielded $58{,}679$ elements ($-17.7\%$), but violates the plane strain formulation.
  - **Reduced integration CPE4R (Job `1405056`):** Yielded $103{,}706$ elements ($+45.4\%$), driving element count further away due to hourglassing error.
  - **Sizing bounds and coarsening:** Disabling bounds preserved $71{,}320$; enabling coarsening yielded $71{,}037$ ($-0.4\%$).
- **Epistemic Conclusion:** None of the accessible parameters reproduce $\approx 13{,}941$ elements without violating the published formulation.

---

### Q10: Why is ~13,941 still unresolved?
- **Known from Theory/Publication:** The publication states that a single-pass adaptive remeshing was performed using Listing 1 with `errorTarget=1.0`, resulting in approximately $13{,}941$ elements.
- **Verified Numerically:** Following those instructions literally produces $71{,}320$ elements across all tested Abaqus versions.
- **Still Unresolved:** The accessible evidence does not identify which unpublished implementation detail accounts for the reported $\approx 13{,}941$-element mesh. Possible distinctions such as call-site parameter linkage or an unstated region definition remain hypotheses requiring author information; neither is established.

---

### Q11: Exactly what information is missing from the publication?
- **Missing Technical Details:**
  1. *Remeshing region set:* Was `RemeshingRule` applied to `All_elem` or a local geometric corridor?
  2. *Exact runtime errorTarget:* Was $\texttt{errorTarget}=1.0$ modified at the call site or overridden in the GUI?
  3. *Pre-analysis coarse mesh provenance:* What were the exact element and node counts of the pre-analysis donor deck?
  4. *Coarsening settings:* Was `coarseningFactor` left at `NOT_ALLOWED` or enabled?
  5. *Abaqus environment:* What exact Abaqus build and OS platform were used?
  6. *Sizing controls:* Were any advanced mesh controls applied (e.g., `sizeDeviationFactor`, curvature controls)?

---

### Q12: What are the UEL energy limitations?
- **Known from Theory/Publication:** In phase-field mechanics, energetic criteria integrate total strain energy $\Psi_e$ and fracture dissipation $\Psi_f$ across the entire domain.
- **Verified Numerically:** In our co-located UEL formulation, Abaqus' built-in `ENERGY` array is not populated for user elements (`ALLSE`, `ALLPD`, etc.). Standard ODB extractions cannot provide an authentic internal energy balance. The integrated quantity $W_{\mathrm{ext}} = \int F\,\mathrm{d}u$ represents external work, not internal energy.
- **Thesis Policy:** We explicitly state this limitation in the report and thesis rather than claiming a complete energy convergence study.

---

### Q13: What work remains on hold?
- **Strict Scope Freeze (Supervisor Directive):**
  - Mode-II shear fracture benchmarks (Task 7): **ON HOLD**.
  - Nonmatching multi-step state transfer: **ON HOLD** (avoid numerical diffusion of the damage gradient).
  - External `ABAQUSER` integration (Task 6): **ON HOLD**.
  - Multi-threading scaling benchmarks: serial 1-CPU remains authoritative; 4-thread parity is demonstrated as supporting evidence only.

---

### Q14: What changes under supervisor Choice A versus Choice B?
- **Under Option A (Pragmatic Advancement):**
  - Gate 5 is formally accepted as externally under-specified.
  - The $71{,}320$-element model is frozen as the verified publication-literal reconstruction.
  - The 15-factor audit and regional distribution ($87.3\%$ outside corridor) are documented in the thesis.
  - Work proceeds strictly to Mode-I thesis documentation and synthesis.
- **Under Option B (Author Inquiry):**
  - The prepared 6-question inquiry is transmitted to Dr. Pandey and Dr. Kumar.
  - Gate 5 remains open pending their response.
  - If the authors provide their exact script parameters, a single confirmatory run will test for exact count matching.
- **Universal Rule:** Under **both** options, model complexity is not increased without separate supervisor authorization.
