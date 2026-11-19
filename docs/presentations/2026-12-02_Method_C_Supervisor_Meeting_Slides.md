# Supervisor Meeting Presentation: Method C Incremental Adaptive Remeshing

**Project:** Master Thesis — Adaptive Remeshing for Phase-Field Fracture Mechanics  
**Institution:** Institute of Mechanics and Fluid Dynamics, TU Bergakademie Freiberg  
**Supervisors:** Prof. Dr.-Ing. B. Kiefer, Dr.-Ing. M. Roth  
**Presenter:** Antigravity / Multi-Agent Research System  
**Meeting Date:** 2 December 2026, 13:00 Europe/Berlin  
**Research Directive:** Method C Standing Directive (19 November 2026)  

---

## Slide 1: Title & Executive Overview

### Incremental Adaptive Remeshing with Nonmatching State & History Transfer in Phase-Field Fracture
#### Demonstration of Forward Crack Growth and Void Capture in Mode-I Fracture

* **Primary Research Milestone:**
  - Transition from fixed-mesh error-guided pre-refinement (Method A) to external-driver incremental adaptive remeshing (Method C).
  - Successful execution of an end-to-end multi-stage simulation:
    $$\text{Solve (Coarse)} \;\longrightarrow\; \text{Evaluate} \;\longrightarrow\; \text{Remesh} \;\longrightarrow\; \text{Transfer } (u, d, H) \;\longrightarrow\; \text{Re-equilibrate} \;\longrightarrow\; \text{Forward Propagation}$$
* **Key Achievements Demonstrated:**
  - **Force Continuity:** $\Delta F = -1.37\%$ across discretization change.
  - **Energy Continuity:** $\Delta E = -0.77\%$ in elastic strain energy.
  - **Zero Healing:** Phase-field damage irreversibility strictly upheld ($\dot{d} \geq 0$).
  - **Forward Propagation:** Macroscopic crack initiates at notch tip ($x = 0.50\,\text{mm}$), traverses $150\,\mu\text{m}$ ligament, penetrates circular void at $x = 0.65\,\text{mm}$, and causes $-59.58\%$ structural load softening.

---

## Slide 2: Context & Transition from Method A to Method C

### Status of Prior Work & Research Focus
* **Method A (Offline Error-Guided Pre-Refinement):**
  - Evaluated on four Mode-I benchmark cases (Cases 1, 2, 3, 5).
  - Accepted as scientifically sufficient and frozen per supervisor guidance.
  - Sizing field derived from recovered stress error (MISESERI) and phase-field gradients.
* **Method C Standing Directive (19 November 2026):**
  - Overcomes the fundamental limitation of fixed pre-refinement: cracks evolving into previously unrefined material.
  - Focuses on a single, rigorous demonstration problem: **Mode-I plate with an initial notch and an offset circular void ahead of the tip**.
  - Requires genuine forward crack growth and hole capture post-transfer; fixed-load equilibration alone is treated as partial.
  - Reuses frozen UEL formulation (`f42_mixed_uel.for`, SHA-256 `CE8D5EDC...`) bitwise identical.

---

## Slide 3: Demonstration Specimen Geometry & Material Parameters

### Mode-I Plate with Offset Void
* **Geometry:**
  - Plate dimensions: $W \times H = 1.0\,\text{mm} \times 1.0\,\text{mm}$ (plane strain).
  - Initial horizontal edge notch: Length $a_0 = 0.50\,\text{mm}$ at $y = 0.50\,\text{mm}$.
  - Circular void: Center $(x_c, y_c) = (0.75, 0.50)\,\text{mm}$, Radius $R = 0.10\,\text{mm}$.
  - Uncracked ligament: $L_{\mathrm{lig}} = x_c - R - a_0 = 0.75 - 0.10 - 0.50 = 0.150\,\text{mm}$ ($150\,\mu\text{m}$).
* **Boundary & Loading Conditions:**
  - Bottom edge ($y = 0$): Fixed ($u_1 = u_2 = 0$).
  - Top edge ($y = 1.0\,\text{mm}$): Prescribed vertical displacement $u_2(t)$.
  - Stage 1 (Job 1): Monotonic displacement to $u_2 = 0.0050\,\text{mm}$ (linear-elastic + incipient damage).
  - Stage 2 (Job 3): Continued displacement to $0.008756\,\text{mm}$ (forward propagation).
* **Material Parameters (Standard Case 1 Material):**
  - Young's modulus: $E = 210.0\,\text{GPa}$
  - Poisson's ratio: $\nu = 0.30$
  - Critical energy release rate: $G_c = 2.7 \times 10^{-3}\,\text{kN/mm}$ ($2700\,\text{J/m}^2$)
  - Phase-field length scale: $\ell_0 = 0.0075\,\text{mm}$ ($7.5\,\mu\text{m}$)
  - Residual stiffness parameter: $k = 1.0 \times 10^{-7}$

---

## Slide 4: End-to-End Method C Computational Architecture

### Four-Stage Algorithmic Pipeline

```
  [Stage 1: Job 1 Base Solve]
  Coarse Discretization (2,920 Quads)
  Displacement u2 -> 0.0050 mm
  PBS Job 1424517 (Exit 0)
         │
         ▼
  [Stage 2: State & History Transfer]
  Field Extraction: u_nodal, d_nodal, H_ip
  Mesh Adaptation: Sizing h_min = 3 um (10,299 Quads)
  Topology-Preserving Transfer & Irreversibility Enforcement
         │
         ▼
  [Stage 3: Job 2 Re-equilibration]
  Fixed-Load Re-equilibration at u2 = 0.0050 mm
  PBS Job 1424584 (Exit 0, 41 s walltime)
  Continuity: Delta F = -1.37%, Delta E = -0.77%, Zero Healing
         │
         ▼
  [Stage 4: Job 3 Forward Crack Propagation]
  Displacement Continuation u2: 0.0050 -> 0.008756 mm
  PBS Job 1424609 (149 increments)
  Crack Traversal -> Void Capture at x = 0.65 mm -> Load Softening (-59.6%)
```

---

## Slide 5: Step 1: Baseline Coarse Solve (Job 1)

### Observables & Incipient Notch Nucleation
* **Solver Receipt (PBS Job 1424517):**
  - Discretization: 2,920 physical quads, 8,760 layered elements, 3,017 nodes.
  - Solver status: `COMPLETED_EXIT0`, 50 increments to $u_2 = 0.0050\,\text{mm}$, walltime $1,511\,\text{s}$.
  - Structural reaction force: $RF_2 = 0.556024\,\text{kN}$ ($556.02\,\text{N}$).
* **Damage State Analysis:**
  - Peak damage: $d_{\max} = 0.169178$ strictly localized at the notch tip $(0.50, 0.50)\,\text{mm}$.
  - Bulk mean damage: $d_{\mathrm{mean}} = 0.008609$ (bulk material remains fully intact).
  - History variable: $H_{\max} = 0.249872\,\text{MPa}$.
  - Incipient nucleation: Occurs at $\approx 85\%$ of peak structural load; Step 1 is therefore not purely linear-elastic at the tip singularity.
* **Remeshing Decision Signal:**
  - Standard Abaqus `MISESERI` output equals $0.0$ due to `*USER MATERIAL` companion formulation.
  - Remeshing trigger successfully resolved using damage-localization envelope around notch tip.

---

## Slide 6: Step 2: Nonmatching State & History Transfer

### Multi-Field Mapping & Damage Irreversibility
* **Receiver Mesh Generation:**
  - High-density refinement focused across the $150\,\mu\text{m}$ ligament corridor.
  - Local element sizing: $h_{\min} = 0.0030\,\text{mm}$ ($3.0\,\mu\text{m} \approx 0.4\,\ell_0$), resolving the phase-field regularization length scale.
  - Total receiver elements: 10,299 physical quads ($3.53\times$ increase over coarse base).
* **State Transfer Mechanics:**
  - **Displacement ($u$):** Nodal-to-nodal isoparametric interpolation.
  - **Phase Field ($d$):** Nodal-to-nodal interpolation with strict bound enforcement ($0 \leq d \leq 1$).
  - **History Field ($H$):** Donor Gauss-point history mapped to receiver integration points and initialized in SVARS 9..12 of companion elements.
* **Strict Irreversibility ($\dot{d} \geq 0$):**
  - Transfer algorithm guarantees zero healing; transferred damage at all 10,299 elements equals or exceeds donor damage ($d_{\mathrm{rec}} \geq d_{\mathrm{don}}$).

---

## Slide 7: Step 2 Verification: Fixed-Load Re-equilibration (Job 2)

### Quantitative Continuity & Recovery
* **Solver Receipt (PBS Job 1424584):**
  - Fixed-load boundary: $u_2 = 0.005000\,\text{mm}$ maintained.
  - Solver status: `COMPLETED_EXIT0`, 24 increments, total walltime $41.0\,\text{s}$ (66 iterations).
* **Continuity Acceptance Evaluation:**
  - **Force Continuity:**
    $$\Delta RF_2 = \frac{0.548386 - 0.556024}{0.556024} = -1.37\% \quad (\text{Threshold: } \pm 5.0\% \implies \mathbf{PASS})$$
  - **Energy Continuity:**
    $$\Delta E_{\mathrm{elastic}} = \frac{0.001371 - 0.001382}{0.001382} = -0.77\% \quad (\text{Threshold: } \pm 5.0\% \implies \mathbf{PASS})$$
  - **Healing Audit:** Zero healing detected across all elements ($\Delta d \geq 0 \implies \mathbf{PASS}$).
* **Conclusion:** The refined receiver mesh achieves seamless physical equilibrium without spurious relaxation or artificial energy injection.

---

## Slide 8: Step 3: Forward Crack Propagation & Void Penetration (Job 3)

### Dynamic Crack Evolution & Void Capture
* **Solver Receipt (PBS Job 1424609):**
  - Displacement continued monotonically from $u_2 = 0.0050\,\text{mm}$ to $0.008756\,\text{mm}$.
  - 149 total increments (125 in Step 2), total walltime $2,938\,\text{s}$ ($48.9\,\text{min}$).
  - Termination: `CUTBACK_EXIT1` at physical increment cutback limit ($\Delta t < 10^{-8}$) upon complete void severance.
* **Key Propagation Milestones:**
  1. **Frame 0 ($u_2 = 0.0050\,\text{mm}$):** Re-equilibrated state ($F = 0.5484\,\text{kN}$, $d_{\max} = 0.4086$).
  2. **Frame 4 ($u_2 = 0.006117\,\text{mm}$):** Peak structural load ($F_{\max} = 0.648681\,\text{kN}$, $d_{\max} = 0.7300$).
  3. **Frame 5 ($u_2 = 0.006223\,\text{mm}$):** Macroscopic crack initiation ($d_{\max} = 0.9685$).
  4. **Frame 15 ($u_2 = 0.006939\,\text{mm}$):** Mid-ligament rapid advance ($x_{\mathrm{tip}} = 0.5928\,\text{mm}$, $F = 0.4430\,\text{kN}$).
  5. **Frame 116 ($u_2 = 0.008683\,\text{mm}$):** Hole penetration / capture confirmed ($x = 0.6503\,\text{mm}$, $F = 0.3316\,\text{kN}$).
  6. **Frame 125 ($u_2 = 0.008756\,\text{mm}$):** Ligament severed; secondary initiation at void rear ($x_{\mathrm{tip}} = 0.8957\,\text{mm}$, $F = 0.2622\,\text{kN}$).

---

## Slide 9: Structural Response: Load-Displacement Softening

### Visual Evidence: $RF_2$ vs $u_2$
* *Reference Figure:* `results/figures/method_c_demo/fig_method_c_load_displacement.png`

```
  RF2 [kN]
   0.70 ───┐               ★ Peak Load: 0.6487 kN (u2 = 6.12 µm)
   0.60 ───┤             ╱   ╲
   0.50 ───┤  ●        ╱       ╲
   0.40 ───┤ ┌───────╱           ╲
   0.30 ───┤ │Transfer: -1.37%     ◆ Void Penetration: 0.3316 kN (u2 = 8.68 µm)
   0.20 ───┤ │                                 ✖ Terminal Softening: 0.2622 kN (-59.6%)
   0.10 ───┤ │
   0.00 ───┴─┴───────┴───────┴───────┴───────┴───────┴───────
           0.0      2.0     4.0     6.0     8.0     10.0   u2 [µm]
```

* **Physical Discussion on Peak Load:**
  - Peak load of $0.6487\,\text{kN}$ is $\approx 13.5\%$ lower than crude un-notched/coarse estimates ($\sim 0.75\,\text{kN}$).
  - Attributed to the stress concentration and compliance of the circular void ($R = 0.10\,\text{mm}$) located just $150\,\mu\text{m}$ ahead of the tip.
* **Demonstrated Softening:**
  - Structural load drops by **$-59.58\%$** ($0.6487\,\text{kN} \rightarrow 0.2622\,\text{kN}$), proving genuine physical crack propagation and energy dissipation.

---

## Slide 10: Crack Trajectory & Hole Capture Dynamics

### Visual Evidence: $x_{\mathrm{tip}}$ vs $u_2$ & Damage Evolution Sequence
* *Reference Figures:*
  - Trajectory: `results/figures/method_c_demo/fig_method_c_crack_extension.png`
  - Sequence: `results/figures/method_c_demo/fig_method_c_damage_evolution_sequence.png`
  - Animation: `results/figures/method_c_demo/fig_method_c_damage_evolution.gif`

* **Trajectory Characteristics:**
  - **Stationary Phase ($u_2 \leq 6.12\,\mu\text{m}$):** Crack remains pinned at notch tip ($x_{\mathrm{tip}} = 0.500\,\text{mm}$); elastic energy accumulates.
  - **Dynamic Breakthrough Phase ($u_2 \in [6.22, 6.94]\,\mu\text{m}$):** Rapid crack propagation across the ligament ($x = 0.50 \rightarrow 0.65\,\text{mm}$).
  - **Void Arrest & Boundary Capture ($u_2 \in [6.94, 8.68]\,\mu\text{m}$):** Crack tip enters the void; load redistributes around the void flanks.
  - **Secondary Propagation ($u_2 > 8.68\,\mu\text{m}$):** High stress on far side initiates secondary cracking ($x = 0.85 \rightarrow 0.8957\,\text{mm}$). Total extension $\Delta a = 0.3957\,\text{mm}$.

---

## Slide 11: Scientific Summary & Master Thesis Roadmap

### Project Milestones & Submission Timeline

* **Method C Standing Directive Successfully Fulfilled:**
  - Solved, evaluated, remeshed, transferred, re-equilibrated, and propagated forward into a void.
  - Re-equilibration continuity strictly within $\pm 5\%$ ($\Delta F = -1.37\%$, $\Delta E = -0.77\%$).
  - Full ligament severance and void capture verified on authentic cluster outputs.
  - HPC submission budget capped at 60 jobs; zero administrative overhead.

* **Governing Thesis Timeline:**
  - **2 December 2026 (13:00):** Supervisor Meeting & Presentation of Method C Demonstration.
  - **13 December 2026:** Comprehensive Research Freeze (all solver simulations concluded).
  - **14 Dec 2026 – 12 Jan 2027:** Final Thesis Drafting & LaTeX Document Compilation (`MA_AdaptiveRemeshing_Report_2026/`).
  - **13 January 2027:** Master Thesis Official Submission.
