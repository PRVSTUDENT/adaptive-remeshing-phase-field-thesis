# Mode-I Load Partitioning (Method B) Experiment Specification

**Document Version:** 1.0  
**Date:** 2026-10-08  
**Author:** Gemini Antigravity  
**Governance Framework:** Post-08-October-2026 Supervisor Meeting 3-Method Roadmap  
**Target Milestone:** Supervisor Meeting (Thursday, 22 October 2026)  
**Status:** APPROVED FOR IMPLEMENTATION & TESTING

---

## 1. Executive Summary & Scientific Context

Following the formal Master Thesis supervisor meeting on **Thursday, 08 October 2026**, the project roadmap established the **3-Method Adaptive Refinement Framework** to structure the comparative evaluation of error-guided meshing strategies for phase-field fracture:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    3-METHOD ADAPTIVE REFINEMENT FRAMEWORK                    │
├──────────────────────────────────────────────────────────────────────────────┤
│  Method A: Two-Pass Baseline Refinement (Frozen Reference)                   │
│  - Linear-elastic pre-analysis on coarse mesh (Job-1)                        │
│  - Single error-guided remesh based on recovered stress error (MISESERI)     │
│  - Full phase-field fracture simulation on static refined mesh (Job-2)       │
├──────────────────────────────────────────────────────────────────────────────┤
│  Method B: Multi-Step Load Partitioning Study (Active Specification)        │
│  - Configurable 1-step, 2-step, and 4-step pre-analysis load partitioning    │
│  - Strictly constant displacement increment size (\Delta u held invariant)   │
│  - Single remeshing operation (No state transfer required)                   │
│  - Evaluates pre-analysis loading horizon and incrementation sensitivity     │
├──────────────────────────────────────────────────────────────────────────────┤
│  Method C: Sequential Evolving Remeshing (Future Scope Extension)            │
│  - Chained multi-cycle solve -> remesh -> state transfer -> restart cycles   │
│  - Requires validated state transfer, mesh-to-mesh mapping, and             │
│    thermodynamic energy / damage irreversibility verification gates          │
└──────────────────────────────────────────────────────────────────────────────┘
```

This specification establishes the exact experimental protocol, numerical controls, file naming conventions, and validation criteria for **Method B (Load Partitioning)**.

---

## 2. Scientific Objectives of Method B

The primary scientific questions addressed by Method B are:

1. **Pre-Analysis Loading Horizon Invariance:**  
   Does partitioning the linear-elastic pre-analysis displacement into multiple loading steps ($1, 2, 4$ steps) alter the computed relative error indicator $\eta_e = \text{MISESERI}_e / \text{MISESAVG}$ or the resulting adaptive mesh topology?
2. **Incrementation Coupling Decoupling:**  
   By holding the displacement increment $\Delta u$ strictly constant across step partitions, can we definitively prove that step count does not introduce artificial numerical artifacts into the Abaqus native error estimator?
3. **Accuracy vs. Computational Cost Trade-Off:**  
   How do the resulting phase-field fracture predictions ($K_0$, $F_{\max}$, $u_{\text{peak}}$, softening rate, energy evolution) compare across the 1-partition, 2-partition, and 4-partition mesh lineages?

---

## 3. Benchmark Model & Numerical Constants

Method B adopts the canonical Mode-I square plate benchmark from Pandey & Kumar (2025, Section 4.1):

| Parameter | Symbol | Value | Unit | Description |
| :--- | :---: | :---: | :---: | :--- |
| Specimen Width | $W$ | $1.0$ | $\mathrm{mm}$ | Domain width |
| Specimen Height | $H$ | $1.0$ | $\mathrm{mm}$ | Domain height |
| Initial Crack Length | $a_0$ | $0.5$ | $\mathrm{mm}$ | Horizontal edge crack along $y=0.5\,\mathrm{mm}$ ($0 \le x \le 0.5\,\mathrm{mm}$) |
| Crack Geometry | - | Zero-gap seam | - | True zero-thickness seam (prevents notch compliance distortion) |
| Young's Modulus | $E$ | $210.0$ | $\mathrm{kN/mm^2}$ ($210\,\mathrm{GPa}$) | Isotropic elasticity |
| Poisson's Ratio | $\nu$ | $0.3$ | - | Elastic Poisson ratio |
| Critical Energy Release Rate | $G_c$ | $2.7 \times 10^{-3}$ | $\mathrm{kN/mm}$ ($2.7\,\mathrm{kJ/m^2}$) | Griffith fracture energy |
| Regularizing Length Scale | $l_0$ | $0.0075$ | $\mathrm{mm}$ ($7.5\,\mu\mathrm{m}$) | Phase-field diffusion length scale |
| Numerical Viscous Regularization | $k$ | $1.0 \times 10^{-7}$ | - | Residual stiffness parameter |
| Coarse Baseline Mesh | - | $2{,}906$ FEs | - | Structured quadrilateral/triangular mesh ($2{,}988$ nodes) |

---

## 4. Controlled Load Partitioning Matrix

To decouple step count from load resolution, the total pre-analysis displacement $u_{\text{pre}} = 0.0010\,\mathrm{mm}$ ($1.0\,\mu\mathrm{m}$) is divided with a strictly constant displacement increment $\Delta u = 0.00010\,\mathrm{mm}$ ($0.10\,\mu\mathrm{m}$ per increment):

```
Method B Load Partitioning Matrix: Total Pre-Analysis Horizon u_pre = 1.0 um

Case B1 (1 Partition / 1 Step):
Step 1: [0.0 um ─────────────────────────────> 1.0 um] (10 increments @ 0.10 um)
                                                ▲ Remesh Frame (Frame 10, u=1.0 um)

Case B2 (2 Partitions / 2 Steps):
Step 1: [0.0 um ────────────> 0.5 um] (5 incs)  ▲ Intermediate Remesh Frame (Opt)
Step 2: [0.5 um ────────────> 1.0 um] (5 incs)  ▲ Final Remesh Frame (Frame 10, u=1.0 um)

Case B4 (4 Partitions / 4 Steps):
Step 1: [0.00 um ────> 0.25 um] (2.5 incs -> 3 incs @ 0.083 um)
Step 2: [0.25 um ────> 0.50 um] (2.5 incs -> 2 incs @ 0.125 um)
Step 3: [0.50 um ────> 0.75 um] (2.5 incs -> 3 incs @ 0.083 um)
Step 4: [0.75 um ────> 1.00 um] (2.5 incs -> 2 incs @ 0.125 um)
                                                ▲ Final Remesh Frame (Frame 10, u=1.0 um)
```

### Table 1: Detailed Load Partitioning Configuration

| Case ID | Partitions | Step Setup | Increments per Step | $\Delta u$ per Inc [$\mu\mathrm{m}$] | Total Increments | Evaluation Frame ($u_x = 1.0\,\mu\mathrm{m}$) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **B1** | 1 | Step 1: $u = 0 \to 1.0\,\mu\mathrm{m}$ | 10 | $0.100$ | 10 | Step 1, Frame 10 |
| **B2** | 2 | Step 1: $u = 0 \to 0.5\,\mu\mathrm{m}$<br>Step 2: $u = 0.5 \to 1.0\,\mu\mathrm{m}$ | 5<br>5 | $0.100$<br>$0.100$ | 10 | Step 2, Frame 5 |
| **B4** | 4 | Step 1: $u = 0 \to 0.25\,\mu\mathrm{m}$<br>Step 2: $u = 0.25 \to 0.50\,\mu\mathrm{m}$<br>Step 3: $u = 0.50 \to 0.75\,\mu\mathrm{m}$<br>Step 4: $u = 0.75 \to 1.00\,\mu\mathrm{m}$ | 3<br>2<br>3<br>2 | $0.083$<br>$0.125$<br>$0.083$<br>$0.125$ | 10 | Step 4, Frame 2 |

---

## 5. Automated Remeshing & Fracture Execution Workflow

For each partition case ($B1, B2, B4$):

1. **Pre-Analysis Job Execution:**  
   Execute linear-elastic continuum pre-analysis on coarse baseline ($2{,}906$ FEs). Output MISESERI and MISESAVG field variables to ODB.
2. **Native Remeshing Rule Construction:**  
   Open the partition ODB in Abaqus/CAE. Build native `RemeshingRule` targeting `errorTarget = 2.0%` (or parameterized $1.0\%, 3.0\%, 5.0\%$).
3. **Native Adaptive Remesh:**  
   Invoke `mdb.models['Model-1'].adaptiveRemesh()` to produce native adapted input deck `PK_M1_METHOD_B{1,2,4}_RAW.inp`.
4. **UEL Layer Reconstruction:**  
   Reconstruct 3-layer co-located UEL structure (Layer 1 Phase U1, Layer 2 Mech U2, Layer 3 Companion CPE4/UMAT) using verified deterministic rebuilder.
5. **Production Fracture Simulation:**  
   Execute full phase-field fracture simulation from $u = 0 \to 0.010\,\mathrm{mm}$ ($10.0\,\mu\mathrm{m}$) across 5,000 increments.
6. **No State Transfer:**  
   The fracture analysis starts from the pristine initial intact state ($d=0$), completely bypassing state-transfer interpolation errors.

---

## 6. Predeclared Acceptance & Convergence Criteria

The Method B experimental series will be evaluated against the following quantitative gates:

1. **Pre-Analysis Topological Scale-Invariance:**  
   The maximum finite element count deviation across the three adapted meshes must satisfy:
   $$\Delta N_{\text{FE}} = \frac{\max(N_{\text{FE}}) - \min(N_{\text{FE}})}{\text{mean}(N_{\text{FE}})} \le 1.5\%$$
2. **Initial Continuum Stiffness Parity ($K_0$):**  
   The initial elastic structural stiffness $K_0$ on the adapted fracture meshes must match the reference $K_0 = 137.95\,\mathrm{kN/mm}$ within:
   $$\Delta K_0 \le 0.50\% \quad (137.26 \le K_0 \le 138.64\,\mathrm{kN/mm})$$
3. **Peak Force Invariance ($F_{\max}$):**  
   The peak fracture load across all three partition meshes must agree within:
   $$\Delta F_{\max} \le 1.0\% \quad (|F_{\max, B_i} - F_{\max, B_j}| / F_{\max} \le 0.01)$$
4. **Damage Localization Morphology:**  
   The phase-field damage corridor must maintain pure horizontal symmetry along $y = 0.50\,\mathrm{mm}$ with $d_{\max} \ge 1.000$ and zero spurious branching.

---

## 7. Package Layout & Provenance Governance

All Method B files will reside under `models/pandey_kumar_mode1/methods_comparison/method_b_load_partitioning/`:

```
models/pandey_kumar_mode1/methods_comparison/method_b_load_partitioning/
├── b1_single_step/
│   ├── PK_M1_PRE_B1.inp
│   ├── PK_M1_ADAPT_B1_FRACTURE.inp
│   └── MANIFEST.json
├── b2_two_step/
│   ├── PK_M1_PRE_B2.inp
│   ├── PK_M1_ADAPT_B2_FRACTURE.inp
│   └── MANIFEST.json
├── b4_four_step/
│   ├── PK_M1_PRE_B4.inp
│   ├── PK_M1_ADAPT_B4_FRACTURE.inp
│   └── MANIFEST.json
└── METHOD_B_SYNTHESIS_EVALUATION_REPORT.md
```

This ensures complete isolation from the frozen Mode-I baseline (`v2026.10.08-supervisor-meeting-mode1-freeze`) while providing a repeatable, automated benchmark for the upcoming supervisor review on 22 October 2026.
