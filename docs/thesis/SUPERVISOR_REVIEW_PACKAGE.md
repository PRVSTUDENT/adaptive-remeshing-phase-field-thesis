# Master Thesis Supervisor Review & Decision Package

- **Candidate**: Pruthviraja Reddy Vandavagali (Matr. Nr. 68865)
- **Thesis Title**: Application of Built-in Adaptive Remeshing and Mesh Refinement Features in Abaqus to Fracture Simulations Using Phase-field User Elements
- **1st Examiner (Supervisor)**: Prof. Dipl.-Ing. Björn Kiefer, Ph.D.
- **2nd Examiner (Reviewer)**: Dr.-Ing. Stephan Roth
- **Institution**: Chair of Applied Mechanics -- Solid Mechanics, TU Bergakademie Freiberg
- **Submission Candidate**: [`docs/thesis/THESIS_FACULTY_BUILD.pdf`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/thesis/THESIS_FACULTY_BUILD.pdf) (57 pages)
- **PDF SHA-256**: `DD979D79CE2D52566B331D66DF143858B2529827C97AC3B133E347AC71B168BF`
- **Current Status**: **`PASS_FOR_SUPERVISOR_REVIEW`** (Technical QA complete; awaiting supervisor role sign-off; external submission **NOT PERFORMED**)

---

## 1. Concise Thesis Objective & Contribution

This master thesis investigates whether and how commercial FE software features (specifically Abaqus built-in adaptive remeshing, error indicator pre-refinement, and custom user-element state transfer) can be systematically deployed to overcome the severe mesh-density bottleneck of phase-field fracture modeling. 

The primary contribution is a rigorously verified, multi-stage validation framework that reduces computational CPU time by **greater than an order of magnitude ($12.25\times$)** while maintaining high global accuracy ($<1.43\% L_2$ force error and $<0.25\%$ elastic stiffness error) relative to fine uniform reference models under continuous physical phase-field fracture.

---

## 2. The Multi-Stage Scientific Validation Ladder (Stages A--G)

The methodology was qualified through seven isolated stages:

| Stage | Focus & Scope | Governed Status | Key Scientific Outcome |
| :--- | :--- | :--- | :--- |
| **Stage A** | Baseline Molnar Mode-I | `VALIDATED` | Exact paper-matched benchmark reproduction ($l_c=0.015\,\text{mm}$) |
| **Stage B** | Native Abaqus Restart | `VALIDATED` | Binary solver restart repeatability |
| **Stage C** | Same-Mesh Reconstructed Restart | `VALIDATED` | Nodal/Gauss-point state re-ingestion formulation proof |
| **Stage D** | Nonmatching Transfer (Same Topology) | `VALIDATED_SLIT_BARRIER` | Geometric interpolation proof with corrected slit barrier |
| **Stage E** | Multi-Resolution Transfer | `VALIDATED_DONOR_R2` | Transfer to refined (R1) and coarsened (R2) meshes with runtime proof |
| **Stage F** | Synthetic Topology Benchmark | `VALIDATED_ONE_FACET` | State transfer across discrete mesh split *(numerical benchmark only)* |
| **Stage G** | Production Adaptive Validation | `VALIDATED_PRODUCTION` | Production accuracy & efficiency proof under `CONTINUOUS_PHASE_ONLY` |

---

## 3. Final Frozen Stage-G Evidence & Discretization Comparison

```text
========================================================================================================================
METRIC / QUANTITY                     H1 REFERENCE         H2 BASELINE          MM ADAPTIVE (CAND 1)  PK5 ADAPTIVE (CAND 2)
========================================================================================================================
PBS Job ID                            1386447.mmaster02    1386448.mmaster02    1394260.mmaster02     1394261.mmaster02
Physical Elements (N_phys)            12,064               33,852               2,206                 4,894
Physical Nodes (N_nodes)              12,382               34,508               2,294                 4,998
Layered Finite Elements               36,192               101,556              6,618                 14,682
------------------------------------------------------------------------------------------------------------------------
Accepted Increments (Step 1 / Step 2) 500 / 1354 (term)    500 / 1243 (cens)    500 / 2000 (complete) 500 / 2000 (complete)
Total Solver Increments               1,854                1,743                2,500                 2,500
Saved ODB Field Frames                70                   68                   72                    72
------------------------------------------------------------------------------------------------------------------------
Scheduler CPU Time (s)                4,210.0              14,455.0             1,180.0               2,600.0
Endpoint Displacement U1 (mm)         0.009630 (term)      0.009250 (censored)  0.010000 (100%)       0.010000 (100%)
Scheduler CPU Ratio vs H2 Base        —                    1.00x                12.25x (diag ratio)   5.56x (diag ratio)
------------------------------------------------------------------------------------------------------------------------
Domain-A L2 Force Error vs H1 Ref     —                    0.5348%              1.4249%               1.1467%
Domain-A Relative Work Error vs H1    —                    0.2629%              0.8134%               0.5751%
Origin-Constrained Stiffness (kN/mm)  45.9033              45.8739              46.0146               45.9493
Stiffness Error vs H1 Reference       —                    0.0640%              0.2425%               0.1003%
------------------------------------------------------------------------------------------------------------------------
Saved-Frame d >= 0.5 Observation      0.007750 mm          0.007750 mm          0.008250 mm           0.008250 mm
Continuous Initiation Bracket (U1)    0.00750 < U1 <= 0.00775 mm                0.00800 < U1 <= 0.00825 mm
------------------------------------------------------------------------------------------------------------------------
Phase-Field Bounds [0, 1]             [0.0, 0.9975]        [0.0, 0.9985]        [0.0, 0.982310]       [0.0, 0.984000]
Damage Irreversibility Violations     0                    0                    0 (at 72 saved frames)0 (at 72 saved frames)
History Non-Negativity (H >= 0)       [0.0, 48.2]          [0.0, 52.1]          [0.0, 31.4718]        [0.0, 35.3644]
History Monotonicity Violations       0                    0                    0 (at 72 saved frames)0 (at 72 saved frames)
Continuum Formulation                 CONTINUOUS           CONTINUOUS           CONTINUOUS_PHASE_ONLY CONTINUOUS_PHASE_ONLY
========================================================================================================================
```

---

## 4. Prominent Scientific & Evidentiary Limitations

To maintain strict scientific integrity, the manuscript explicitly highlights the following boundaries:
1. **Domain-B Uniform Reference Absence**: Because the fine baseline $H_2$ timed out (walltime-censored at $U_1 = 0.009250\,\text{mm}$) and $H_1$ terminated at $U_1 = 0.009630\,\text{mm}$, no complete uniform reference exists across all of Domain B ($0.009250 < U_1 \le 0.010000\,\text{mm}$). Domain B is evaluated strictly as an internal physical and mutual cross-candidate continuation diagnostic.
2. **Censored Terminal Forces**: The observed terminal reaction forces in $H_1$ and $H_2$ reflect solver termination and walltime limits, respectively, and are not converged physical peaks.
3. **Diagnostic CPU Ratios**: The speedup values of **$12.25\times$** (MM) and **$5.56\times$** (PK5) are scheduler-CPU diagnostic ratios reflecting total run times as executed, rather than like-for-like full-range benchmark speedups.
4. **Saved-Frame Observational Scope**: Independent postprocessed verification of physical invariants ($d \in [0, 1]$, $d_{n+1} \ge d_n$, $H \ge 0$, $H_{n+1} \ge H_n$) is confirmed across all **72 saved ODB field frames**. Intermediate unsaved increment states are enforced algorithmically by the UEL but are not claimed as independently observed.
5. **Damage Initiation Bracketing**: The continuous threshold crossing $d = 0.50$ lies within the discrete bracket $0.00750 < U_1 \le 0.00775\,\text{mm}$ for $H_1/H_2$ and $0.00800 < U_1 \le 0.00825\,\text{mm}$ for MM/PK5 ($\Delta U_1 = 0.25\,\mu\text{m}$ frame sampling).
6. **Energy Accounting Scope**: External work consistency against $H_1$ is verified ($<0.82\%$ error), but raw Abaqus zero-energy history outputs reflect standard UEL encapsulation and are not conflated with complete thermodynamic energy conservation.
7. **Formulation Separation**: Stage F is strictly a synthetic numerical transfer benchmark (artificial single-facet split), while Stage G is physical continuous phase-field fracture (\texttt{CONTINUOUS\_PHASE\_ONLY}).

---

## 5. Provisional Candidate-Role Recommendations

The following roles are recommended based on the frozen evidence:
- **Candidate 1 (\texttt{M2PROD\_ADAPT\_MM}, 2,206 physical elements)**: Recommended as the **Primary Production Efficiency Candidate** ($>12\times$ runtime reduction, $1.42\% L_2$ error vs $H_1$).
- **Candidate 2 (\texttt{M2PROD\_ADAPT\_PK5}, 4,894 physical elements)**: Recommended as the **Corridor Resolution Sensitivity Candidate** ($5.56\times$ runtime reduction, $1.15\% L_2$ error vs $H_1$).

*Governance Status*: Designated in the thesis as **`PROVISIONAL_REQUIRES_HUMAN_APPROVAL`** pending supervisor ratification.

---

## 6. Page-Specific Review Pointers for Supervisor

The supervisor is invited to inspect the following pages in [`docs/thesis/THESIS_FACULTY_BUILD.pdf`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/thesis/THESIS_FACULTY_BUILD.pdf):

| Page # | Content / Artifact | Description |
| :---: | :--- | :--- |
| **p. vi** | **Abstract** | Complete summary of the 7-stage validation framework and performance outcomes. |
| **p. 38** | **Table 8.1** | The multi-stage validation ladder hierarchy (Stages A--G). |
| **p. 38** | **Table 8.2** | Discretization and computational resource comparison ($H_1, H_2, \text{MM}, \text{PK5}$). |
| **p. 39** | **Section 8.3** | Three-layer validation framework (Execution, Hard Invariants, Accuracy & Speedup). |
| **p. 39** | **Table 8.3** | Hard physical invariant audit across saved ODB field frames. |
| **p. 40** | **Table 8.4** | Domain-A quantitative accuracy metrics ($L_2$, Work, and Stiffness errors vs $H_1$). |
| **p. 40** | **Table 8.5** | Damage initiation ($d \ge 0.5$) observation brackets across saved field frames. |
| **p. 41** | **Figure 8.1** | Global Mode-II shear reaction force vs displacement curves ($RF_1$--$U_1$). |
| **p. 41** | **Figure 8.2** | Pointwise relative force discrepancy vs $H_1$ reference over Domain A. |
| **p. 42** | **Figure 8.3** | Computational efficiency bar chart (element count reduction vs CPU execution time). |
| **p. 44** | **Chapter 9** | Recommendations, candidate role governance, and practical decision tree. |

---

## 7. Supervisor Decision Sheet

*(Please mark the appropriate selection for thesis finalization)*:

- [ ] **Option A (Approve Primary Recommendations)**:
  Approve `M2PROD_ADAPT_MM` as the primary production efficiency candidate and `M2PROD_ADAPT_PK5` as the corridor resolution sensitivity candidate. Retain current manuscript text as final.

- [ ] **Option B (Approve Single Candidate Only)**:
  Approve only one candidate (specify MM or PK5) for primary thesis conclusions.

- [ ] **Option C (Request Textual Rephrasing)**:
  Approve the computational dataset but request specific textual or formatting adjustments without running new simulations.

- [ ] **Option D (Request Additional Postprocessing Evidence)**:
  Request additional plots or diagnostic extractions from existing ODB artifacts without new HPC simulations.

- [ ] **Option E (Request Additional HPC Simulation)**:
  Request additional HPC simulation runs prior to final thesis defense.

---

## 8. Summary of Review Deliverables

- **Submission Candidate**: [`docs/thesis/THESIS_FACULTY_BUILD.pdf`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/thesis/THESIS_FACULTY_BUILD.pdf) (57 pages)
- **PDF Hash (SHA-256)**: `DD979D79CE2D52566B331D66DF143858B2529827C97AC3B133E347AC71B168BF`
- **Supervisor Review Package**: [`docs/thesis/SUPERVISOR_REVIEW_PACKAGE.md`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/thesis/SUPERVISOR_REVIEW_PACKAGE.md)
- **Readiness Audit Record**: [`docs/thesis/FINAL_SUBMISSION_READINESS.md`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/thesis/FINAL_SUBMISSION_READINESS.md)
- **Defense Storyboard**: [`docs/thesis/DEFENSE_PRESENTATION_PLAN.md`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/thesis/DEFENSE_PRESENTATION_PLAN.md)
