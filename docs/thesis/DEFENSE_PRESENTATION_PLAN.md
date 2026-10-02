# Master Thesis Defense Presentation Plan & Storyboard

- **Thesis Title**: Application of Built-in Adaptive Remeshing and Mesh Refinement Features in Abaqus to Fracture Simulations Using Phase-field User Elements
- **Candidate**: Pruthviraja Reddy Vandavagali (Matr. Nr. 68865)
- **Supervisors**: Prof. Dipl.-Ing. Björn Kiefer, Ph.D. / Dr.-Ing. Stephan Roth
- **Institution**: Chair of Applied Mechanics -- Solid Mechanics, TU Bergakademie Freiberg
- **Planned Format**: ~20 minutes presentation (12 slides) + 15 minutes scientific discussion

---

## Slide-by-Slide Storyboard

### Slide 1: Title, Problem Motivation & Context
- **Central Message**: Introducing adaptive remeshing and state transfer into commercial FE software (Abaqus) to overcome the severe computational cost bottleneck of phase-field fracture modeling.
- **Visuals**: Title block, TU Freiberg logo, schematic of high-resolution crack corridor versus coarse far-field.
- **Speaker Notes**:
  1. Phase-field fracture replaces discrete jump discontinuities with a continuous damage variable $d \in [0, 1]$, regularized by a material length scale $l_c$.
  2. Resolving $l_c$ typically requires fine element sizes ($h \le l_c / 5$) throughout the domain, leading to extreme computational costs in 2D and intractable models in 3D.
  3. This thesis presents a robust, multi-stage validated framework for adaptive mesh grading and state transfer using custom user elements (UELs).

---

### Slide 2: Governing Phase-Field Continuum Formulation
- **Central Message**: Variational brittle fracture formulation with staggered displacement/phase-field operator splitting and custom UEL encapsulation.
- **Visuals**: Governing differential equations, energy functional $\Psi(\boldsymbol{\varepsilon}, d)$, history variable $H = \max_{\tau \le t} \psi_+(\boldsymbol{\varepsilon}(\tau))$.
- **Speaker Notes**:
  1. Total potential energy comprises degraded elastic strain energy $(g(d) \psi_+ + \psi_-)$ and fracture surface energy $g_c \gamma(d, \nabla d)$.
  2. Staggered operator splitting uncouples displacement and phase-field solves within each time increment, ensuring unconditional algorithmic stability.
  3. History field $H$ strictly prevents unphysical crack healing ($d_{n+1} \ge d_n$) across arbitrary loading histories.

---

### Slide 3: The Multi-Stage Scientific Validation Ladder (Stages A--G)
- **Central Message**: A rigorous, stepwise verification hierarchy from foundational solver reproducibility to full production adaptive fracture.
- **Visuals**: Table from thesis (`validation_ladder_a_to_g.csv` / Table 8.1 in thesis).
- **Speaker Notes**:
  1. Rather than attempting a monolithic adaptive solve immediately, the framework was qualified through seven isolated stages (A through G).
  2. Stages A--C verified baseline physics, native restart, and same-mesh state reconstruction.
  3. Stages D--F validated nonmatching spatial interpolation, multi-resolution coarsening/refinement, and synthetic topological transfer.
  4. Stage G delivers the definitive production efficiency proof under physical continuous phase field.

---

### Slide 4: Baseline Physics & Pre-Refinement Indicators (Stages A & C)
- **Central Message**: Exact verification of the Molnar Mode-I benchmark and evaluation of Abaqus recovery-error indicators ($\text{MISESERI}$) for offline pre-refinement.
- **Visuals**: Single-edge notch tension reaction force curve ($RF_1$--$U_2$), $\text{MISESERI}$ error distribution contour plot.
- **Speaker Notes**:
  1. Stage A established exact paper-matched baseline reproducibility in Abaqus 2023 with $l_c = 0.015\,\text{mm}$.
  2. Stage C evaluated $\text{MISESERI}$ as an elastic stress-recovery indicator to guide initial crack-corridor refinement.
  3. Findings demonstrate that pre-refinement accurately captures pre-peak stiffness and peak load, but continuous adaptivity is essential once damage localizes.

---

### Slide 5: Controlled Nonmatching State Transfer & Multi-Resolution Proof (Stages D & E)
- **Central Message**: High-fidelity field interpolation of displacements, phase damage ($d$), and history variables ($H$) across nonmatching discretizations.
- **Visuals**: Source vs target mesh state transfer contours, nodal error maps, force relaxation curves after state ingestion.
- **Speaker Notes**:
  1. Transfer operator maps continuous primal fields ($u_1, u_2, d$) and internal Gauss-point history ($H$) between nonmatching donor and target meshes.
  2. Stage D proved strict geometric interpolation fidelity with corrected slit-barrier boundary treatment.
  3. Stage E proved stable multi-resolution continuation on both coarsened (R2) and refined (R1) target meshes with quantified release-hold equilibrium.

---

### Slide 6: Synthetic Topological Benchmark vs Physical Phase Field (Stage F vs Stage G)
- **Central Message**: Distinguishing synthetic numerical transfer benchmarks (artificial mesh cutting) from physical continuous phase-field fracture.
- **Visuals**: Comparison diagram showing artificial single-facet topological cut (Stage F) versus smooth continuous phase-field localisation corridor (Stage G).
- **Speaker Notes**:
  1. Stage F evaluated state transfer across an artificial discrete topology change (mesh split along one facet), proving post-peak continuation mechanics.
  2. In contrast, physical Mode-II fracture in Stage G operates entirely under continuous topology (\texttt{CONTINUOUS\_PHASE\_ONLY}).
  3. Preserving continuum regularisation avoids unphysical crack-tip stress singularities and mesh alignment dependencies.

---

### Slide 7: Stage-G Production Adaptive Model Discretizations
- **Central Message**: Adaptive mesh generation achieving 60%--80% physical element reduction relative to fine uniform references.
- **Visuals**: Mesh layout comparisons of $H_1$ (12,064 elements), $H_2$ (33,852 elements), MM Adaptive (2,206 elements), and PK5 Adaptive (4,894 elements). Table 8.2 from thesis.
- **Speaker Notes**:
  1. Adaptive meshes deploy high element density ($h \approx 0.0025\,\text{mm}$) concentrated along the Mode-II shear plane, transitioning to coarse far-field elements.
  2. Candidate 1 (MM): 2,206 physical elements (primary production efficiency candidate).
  3. Candidate 2 (PK5): 4,894 physical elements (corridor resolution sensitivity candidate).

---

### Slide 8: Global Mode-II Reaction Force & Displacement Response
- **Central Message**: Complete structural response comparison up to $U_1 = 0.0100\,\text{mm}$ across uniform and adaptive models.
- **Visuals**: Figure 8.1 from thesis ([`fig_stage_g_rf1_u1_curves.pdf`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/thesis/figures/fig_stage_g_rf1_u1_curves.pdf)).
- **Speaker Notes**:
  1. Uniform reference $H_1$ terminates at $U_1 = 0.00963\,\text{mm}$; $H_2$ is walltime-censored at $U_1 = 0.00925\,\text{mm}$.
  2. Both adaptive production models (MM and PK5) complete the full 2,500 increment loading trajectory to $U_1 = 0.0100\,\text{mm}$.
  3. Close structural tracking across all models confirms that local adaptive grading introduces no spurious stiffness or artificial softening.

---

### Slide 9: Domain-A Quantitative Accuracy & Damage Initiation Observations
- **Central Message**: Bounded reference errors ($L_2 \le 1.43\%$, Work $\le 0.81\%$, Stiffness $\le 0.25\%$) and consistent damage threshold crossing.
- **Visuals**: Figure 8.2 from thesis ([`fig_stage_g_domain_a_error.pdf`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/thesis/figures/fig_stage_g_domain_a_error.pdf)), Table 8.4 and Table 8.5.
- **Speaker Notes**:
  1. In Domain A ($0 \le U_1 \le 0.00925\,\text{mm}$), normalized $L_2$ force error vs $H_1$ is $1.42\%$ (MM) and $1.15\%$ (PK5), well within the provisional $\le 2.0\%$ envelope.
  2. Origin-constrained initial stiffness differs by $<0.25\%$ ($K \approx 45.95$--$46.01\,\text{kN/mm}$).
  3. Discrete damage initiation ($d \ge 0.5$) occurs at $U_1 = 0.00775\,\text{mm}$ ($H_1, H_2$) and $U_1 = 0.00825\,\text{mm}$ (MM, PK5), cleanly bracketed within 2 frame output intervals ($\Delta U_1 = 0.25\,\mu\text{m}$).

---

### Slide 10: Computational Runtime Efficiency & Speedup Ratios
- **Central Message**: Greater than an order-of-magnitude reduction in CPU time ($12.25\times$ diagnostic ratio) achieved through adaptive remeshing.
- **Visuals**: Figure 8.3 from thesis ([`fig_stage_g_efficiency_speedup.pdf`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/thesis/figures/fig_stage_g_efficiency_speedup.pdf)).
- **Speaker Notes**:
  1. Fine uniform baseline $H_2$ required $14,455.0\,\text{s}$ CPU time (4.0 hours) before walltime timeout at $U_1 = 0.00925\,\text{mm}$.
  2. Adaptive Candidate 1 (MM) completed the full loading range in $1,180.0\,\text{s}$ (19.7 min), yielding a **$12.25\times$ scheduler CPU ratio**.
  3. Adaptive Candidate 2 (PK5) completed in $2,600.0\,\text{s}$ (43.4 min), yielding a **$5.56\times$ scheduler CPU ratio**.

---

### Slide 11: Thermodynamic Hard Invariants & Energy Accounting
- **Central Message**: Full physical compliance verified across all saved ODB states with clarified UEL energy accounting boundaries.
- **Visuals**: Table 8.3 from thesis (Hard physical invariant audit summary).
- **Speaker Notes**:
  1. Phase bounds ($0 \le d \le 0.9840$) and history non-negativity ($H \ge 0$) are strictly satisfied everywhere.
  2. Framewise damage irreversibility ($d_{n+1} \ge d_n$) and temporal history monotonicity ($H_{n+1} \ge H_n$) have zero violations across all 72 saved ODB frames.
  3. External work matches $H_1$ within $0.81\%$; raw Abaqus zero-energy counters are clarified as UEL subroutine encapsulation.

---

### Slide 12: Conclusions, Contributions & Outlook
- **Central Message**: The thesis proves that adaptive remeshing combined with custom UEL state transfer delivers high-accuracy phase-field fracture modeling at a fraction of standard uniform mesh computational costs.
- **Visuals**: Summary key takeaway bullet points, recommended workflow schematic.
- **Speaker Notes**:
  1. **Primary Contribution**: Developed, implemented, and verified a 7-stage validation framework integrating UEL state transfer with Abaqus adaptive remeshing.
  2. **Performance Gain**: Demonstrated $>12\times$ runtime reduction while preserving $<1.43\% L_2$ force error.
  3. **Outlook**: Extension of the validated framework to 3D mixed-mode crack propagation, dynamic crack branching, and automated online error indicator remeshing cycles.
