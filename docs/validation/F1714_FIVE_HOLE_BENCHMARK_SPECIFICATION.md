# F1714 — Five-Hole Generalization Benchmark Specification

**Document Version:** 1.0.0  
**Date:** 2026-11-10  
**Author:** Gemini Antigravity  
**Task ID:** `F1714-FIVE-HOLE-GENERALIZATION-BENCHMARK`  
**Literature Anchor:** Pandey & Kumar (2025), *Computer Modeling in Engineering & Sciences (CMES)*, Vol. 144, No. 3, Section 4.5, pp. 3277–3280, Figs. 22(a), 23, 24, 25(a), and Table 5; Han et al. (2023), *Int. J. Numer. Meth. Eng.*, 124(6), 1405–1433 [Ref 106].

---

## 1. Executive Summary & Scientific Purpose

The primary objective of Task F1714 is to extend and demonstrate the **indicator-driven adaptive remeshing methodology (Method A)** on the five-hole tensile fracture benchmark from Pandey & Kumar (2025, Section 4.5).

Unlike previous benchmarks (the Mode-I plate in Section 4.1 with initial notch $a_0 = 0.5\,\text{mm}$ and the notched specimen with hole in Section 4.3 with initial notch $a_0 = 10.0\,\text{mm}$), the five-hole specimen contains **no pre-existing crack or notch**. Damage must nucleate naturally at stress concentrations arising around multiple circular voids. This problem establishes:

1. **Geometry-Independent Generality:** Adaptation operates on arbitrary multi-void configurations without hardcoded crack paths or bounding boxes.
2. **Multi-Site Damage Nucleation:** Refinement emerges at multiple distinct geometric stress concentrations ($h_5, h_4, h_3, h_2$).
3. **Autonomous Selectivity:** The Superconvergent Patch Recovery (SPR) error indicator `MISESERI` autonomously identifies high-stress gradients along ligaments between voids.
4. **Constitutive Split Discipline:** Formal clarification and audit of the volumetric–deviatoric energy split required by the benchmark.

---

## 2. Benchmark Geometry & Void Topology

The specimen consists of a $1.0 \times 1.0\,\text{mm}$ square domain in plane strain with two semi-circular edge notches and three interior circular holes.

### 2.1 Domain Dimensions
- **Width:** $W = 1.0\,\text{mm}$ ($x \in [0.0, 1.0]$)
- **Height:** $H = 1.0\,\text{mm}$ ($y \in [0.0, 1.0]$)
- **Thickness:** $t = 1.0\,\text{mm}$ (plane strain, CPE4/CPE3)
- **Initial Crack / Notch:** None ($a_0 = 0.0\,\text{mm}$)

### 2.2 Void Centers and Radii (Table 5, Pandey & Kumar 2025)

| Hole ID | Topology | Center $(x_c, y_c)$ [mm] | Radius $R$ [mm] | Description / Boundary Intersection |
| :---: | :---: | :---: | :---: | :--- |
| **$h_1$** | Semi-circle | $(0.000, 0.500)$ | $0.100$ | Left edge notch ($x=0$), arc enters domain to $x = 0.100\,\text{mm}$ |
| **$h_2$** | Circle | $(0.350, 0.450)$ | $0.100$ | Interior circular void |
| **$h_3$** | Circle | $(0.600, 0.550)$ | $0.050$ | Interior circular void |
| **$h_4$** | Circle | $(0.750, 0.500)$ | $0.075$ | Interior circular void |
| **$h_5$** | Semi-circle | $(1.000, 0.450)$ | $0.075$ | Right edge notch ($x=1$), arc enters domain to $x = 0.925\,\text{mm}$ |

### 2.3 Inter-Hole Ligament Dimensions

| Ligament Pair | Center-to-Center Distance | Sum of Radii $(R_i + R_j)$ | Minimum Ligament Width |
| :---: | :---: | :---: | :---: |
| **$h_1 \leftrightarrow h_2$** | $\sqrt{0.35^2 + (-0.05)^2} = 0.3536\,\text{mm}$ | $0.100 + 0.100 = 0.200\,\text{mm}$ | **$0.1536\,\text{mm}$** ($153.6\,\mu\text{m}$) |
| **$h_2 \leftrightarrow h_3$** | $\sqrt{0.25^2 + 0.10^2} = 0.2693\,\text{mm}$ | $0.100 + 0.050 = 0.150\,\text{mm}$ | **$0.1193\,\text{mm}$** ($119.3\,\mu\text{m}$) |
| **$h_3 \leftrightarrow h_4$** | $\sqrt{0.15^2 + (-0.05)^2} = 0.1581\,\text{mm}$ | $0.050 + 0.075 = 0.125\,\text{mm}$ | **$0.0331\,\text{mm}$** ($33.1\,\mu\text{m}$) |
| **$h_4 \leftrightarrow h_5$** | $\sqrt{0.25^2 + (-0.05)^2} = 0.2550\,\text{mm}$ | $0.075 + 0.075 = 0.150\,\text{mm}$ | **$0.1050\,\text{mm}$** ($105.0\,\mu\text{m}$) |

*Key Observation:* The narrowest ligament is between $h_3$ and $h_4$ ($33.1\,\mu\text{m}$), while the right edge ligament between $h_4$ and $h_5$ is $105.0\,\mu\text{m}$. Under vertical tension, the highest tensile stress concentration occurs at the lateral flank of $h_5$ and $h_4$, leading to crack nucleation near $h_5$ propagating toward $h_4$, then snapping across the narrow $h_3 \leftrightarrow h_4$ and $h_2 \leftrightarrow h_3$ ligaments.

---

## 3. Material & Phase-Field Properties

| Parameter | Symbol | Value | Units | Provenance / Publication Note |
| :--- | :---: | :---: | :---: | :--- |
| Young's Modulus | $E$ | $210.0$ | $\text{GPa}$ ($\text{kN/mm}^2$) | Section 4.5, same as Mode-I steel |
| Poisson's Ratio | $\nu$ | $0.30$ | — | Section 4.5 |
| Fracture Energy | $G_c$ | $2.7 \times 10^{-3}$ | $\text{kN/mm}$ ($\text{kJ/m}^2$) | Section 4.5 |
| Length Scale Parameter | $\ell_0$ | $0.008$ | $\text{mm}$ ($8.0\,\mu\text{m}$) | Explicitly specified in Section 4.5 & Fig. 23 caption |
| Residual Stiffness | $k$ | $1.0 \times 10^{-7}$ | — | Phase-field numerical stabilization parameter |
| Energy Decomposition | — | Amor et al. (2009) | — | Explicitly specified in Section 4.5 (see Audit Report) |

---

## 4. Boundary Conditions & Loading Schedule

### 4.1 Boundary Constraints
- **Bottom Edge ($y = 0.0\,\text{mm}$):** $u_y = 0.0$ on all nodes $x \in [0.0, 1.0]$.
- **In-Plane Rigid Translation Pin:** $u_x = 0.0$ at corner node $(0.0, 0.0)$ or bottom midpoint $(0.5, 0.0)$.
- **Top Edge ($y = 1.0\,\text{mm}$):** Kinematically coupled to Reference Node $N_{\text{RP}} = (0.5, 1.0)$ with applied vertical tensile displacement $u_y(t)$.
- **Free Boundaries:** Left edge ($x = 0$), right edge ($x = 1$), and all internal void perimeters ($h_1, h_2, h_3, h_4, h_5$) are traction-free.

### 4.2 Loading Protocol
- **Total Vertical Displacement:** $u_y = 0.010\,\text{mm}$ ($10.0\,\mu\text{m}$).
- **Step 1 (Pre-Critical Loading):** $\Delta u_1 = 1.0 \times 10^{-4}$ for 2,000 increments.
- **Step 2 (Fracture Evolution):** $\Delta u_2 = 5.0 \times 10^{-5}$ for 5,000 increments.
- **Job-1 Linear Elastic Pre-Analysis:** $u_y = 0.005\,\text{mm}$ tensile displacement to generate the elastic stress field for SPR `MISESERI` computation.

---

## 5. Mesh Discretization & Remeshing Targets

| Mesh Phase | Target Element Count | Target Node Count | Min Element Size $h_{\min}$ | Max Element Size $h_{\max}$ | Notes |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Coarse Model (Job 1)** | $\sim 2,747$ | $\sim 2,844$ | $0.010\,\text{mm}$ | $0.020\,\text{mm}$ | Global seed $h = 0.02\,\text{mm}$ |
| **Published Standard PFM** | $45,399$ | — | $0.001\,\text{mm}$ | $0.020\,\text{mm}$ | Uniform fine mesh in fracture corridor |
| **Published Proposed PFM** | **$12,944$** | — | **$0.001\,\text{mm}$** | **$0.020-0.30\,\text{mm}$** | Adaptive remesh from `MISESERI` |
| **Target Parity Range** | $12,500 - 13,500$ | $\sim 13,000$ | $0.001\,\text{mm}$ | $0.020\,\text{mm}$ | $\pm 5\%$ of published 12,944 target |

### Remeshing Rule Configuration (Abaqus CAE Listing 4)
- **Variable:** `MISESERI`
- **Sizing Method:** `UNIFORM_ERROR`
- **Error Target:** Adjusted to match $\sim 12,944$ elements
- **Minimum Element Size:** $h_{\min} = 0.001\,\text{mm}$ ($1.0\,\mu\text{m} = \ell_0 / 8$)
- **Maximum Element Size:** $h_{\max} = 0.020\,\text{mm}$ ($20.0\,\mu\text{m}$)
- **Refinement Factor:** $10$
- **Coarsening:** `NOT_ALLOWED`
