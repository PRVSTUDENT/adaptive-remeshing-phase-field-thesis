# Stage 14U-AM: Multi-Quantity Spatial Convergence Protocol and Decision Criteria

## 1. Executive Summary
This document establishes the rigorous, multi-quantity spatial-resolution convergence protocol for the Mode-I adaptive phase-field fracture formulation. Under Gate-6B Stage 14U-AM, spatial mesh refinement is isolated to a single explicit Abaqus `RemeshingRule` parameter: `minElementSize` reduced from $0.0010\,\text{mm}$ ($1.0\,\mu\text{m}$) to $0.0005\,\text{mm}$ ($0.5\,\mu\text{m}$), achieving a factor-of-two reduction in the local crack-corridor element size floor ($h_{\min}/l_0 \approx 0.0738$).

## 2. Invariant Scientific Baseline
All error criteria, pre-analysis physics, companion formulation parameters, and solver controls remain strictly frozen:
- **Pre-Analysis ODB:** `PK_M1_JOB1_INF_COMPANION_2906.odb` (Package 93, Step 1 final frame at $u = 0.005\,\text{mm}$).
- **Remeshing Rule Criteria:** `errorTarget = 1.0%`, `refinementFactor = 10`, `coarseningFactor = NOT_ALLOWED`, `maxElementSize = 0.020 mm`, `region = ALL_ELEM`.
- **Physical Constants:** $E = 210.0\,\text{GPa}, \nu = 0.3, G_c = 0.0027\,\text{kN/mm}, l_0 = 0.0075\,\text{mm}, \eta = 1.0\times 10^{-7}$.
- **Fortran Subroutine:** Authoritative `f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`).
- **Solver Controls:** Stage-14U Step 2 controls (`4, 10, 9, 20, 10, 4, 0, 10`, $\Delta t_{\min} = 1.0\times 10^{-9}$).

## 3. Discretization Telemetry Comparison
| Metric | Baseline Stage 14 (Package 25) | Spatial Fine Candidate (Package 30) | Relative Ratio / Change |
| :--- | :---: | :---: | :---: |
| **Prescribed Min Size Floor ($h_{\text{floor}}$)** | $0.0010\,\text{mm}$ ($1.0\,\mu\text{m}$) | $0.0005\,\text{mm}$ ($0.5\,\mu\text{m}$) | $0.50\times$ (Factor-of-2 finer) |
| **Realized Min Element Size ($h_{\min}$)** | $0.000760\,\text{mm}$ ($0.76\,\mu\text{m}$) | $0.000553\,\text{mm}$ ($0.553\,\mu\text{m}$) | $0.728\times$ |
| **$h_{\min} / l_0$ Ratio ($l_0 = 0.0075\,\text{mm}$)** | $0.1013$ | $0.0738$ | Reduced below $0.08$ |
| **Median Element Size ($h_{\text{median}}$)** | $0.00366\,\text{mm}$ | $0.00310\,\text{mm}$ | $0.847\times$ |
| **Total Base Mesh Elements ($N_{\text{base}}$)** | $14,483$ | $57,929$ | $4.00\times$ increase |
| **Quad Elements (CPE4 / U1 / U2)** | $14,082$ (97.23%) | $56,339$ (97.26%) | Maintained $>97\%$ quads |
| **Tri Elements (CPE3 / U3 / U4)** | $401$ (2.77%) | $1,590$ (2.74%) | Maintained $<3\%$ tris |
| **Total Base Nodes** | $14,456$ | $57,491$ | $3.98\times$ increase |
| **Total 3-Layer Elements** | $43,449$ | $173,787$ | $4.00\times$ increase |
| **Seam Duplicate Node Pairs** | $54$ pairs | $97$ pairs | Clean duplicate pairing |
| **Crack Tip Singleton** | $1$ singleton at $(0.5, 0.5)$ | $1$ singleton at $(0.5, 0.5)$ | Exact single crack tip node |
| **Corridor Elements ($y \in [0.45, 0.55]$)** | $8,338$ (57.57%) | $8,435$ (14.56%) | Dense crack core |

## 4. Multi-Quantity Evaluation Protocol
The response of Package 30 is evaluated against baseline Stage 14 across 10 matched RP displacement states:
$$u \in \{0.0050, 0.0055, 0.0060, 0.0065, 0.0070, 0.0075, 0.0080, 0.0085, 0.0090, 0.0100\}\,\text{mm}$$

### Quantity Classification
1. **`SPATIALLY_STABLE` Quantities:**
   - Initial elastic stiffness $K_0$ ($N=400$ least-squares fit on $u \in [0, 0.0020]\,\text{mm}$), target relative deviation $\le 1.0\%$.
   - Pre-peak linear force-displacement trajectory ($u \le 0.0050\,\text{mm}$), target relative deviation $\le 1.0\%$.
   - Global external work $W_{\text{ext}}$, target relative deviation $\le 1.5\%$.
   - Peak damage $d_{\max} \approx 1.0$.

2. **`SPATIALLY_SENSITIVE` Quantities:**
   - Peak load $F_{\max}$ and peak displacement $u_{\text{peak}}$ (expected slight refinement convergence).
   - Crack tip coordinate $x_{\text{tip}}$ ($d = 0.95$ contour) and damage gradient sharpness $|\nabla d|$.
   - Uncracked ligament profile $d(x, y=0.5)$.
   - Fracture surface energy dissipation $E_{\text{frac}}$ (more tightly resolved crack zone).

3. **`NOT_YET_QUALIFIED` Quantities:**
   - Post-peak terminal dissipation balance and global bookkeeping discrepancy $\varepsilon_{\text{book}}$ pending completion of full solver trajectory.
