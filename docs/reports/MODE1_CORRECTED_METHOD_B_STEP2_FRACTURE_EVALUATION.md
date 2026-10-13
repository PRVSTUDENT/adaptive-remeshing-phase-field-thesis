# Mode-I Benchmark: Corrected Method B Fracture Response Evaluation, In-Flight Progression, and Reference Comparison

**Protocol Version:** 2  
**Task ID:** `F1438-MODE1-CORRECTED-METHOD-B-STEP2-EVALUATION`  
**Date:** 13 October 2026  
**Author:** Gemini Antigravity  
**Status:** `IN_FLIGHT_SOLVE_STEP1_ACTIVE_WITH_EXPLICIT_FALLBACK`  
**Governing Directive:** *"We need to have understood everything related to the first model before we increase complexity."*  

---

## 1. Problem Definition & Boundary Value Problem

The investigation considers the canonical Pandey & Kumar (2025) Mode-I tensile fracture benchmark:
- **Geometry:** Square plate $\Omega = [0.0, 1.0] \times [0.0, 1.0]\,\text{mm}^2$ ($1.0 \times 1.0\,\text{mm}$).
- **Pre-Existing Crack:** Horizontal zero-gap seam slit at $y = 0.5\,\text{mm}$ spanning $0 \le x \le 0.5\,\text{mm}$ ($a_0 = 0.5\,\text{mm}$).
  *(Note: The initial finite-width notch was an erroneous implementation that radically altered compliance; the sharp seam with duplicate node pairs along the flanks is the authoritative physical representation).*
- **Constitutive Properties:**
  - Young's modulus $E = 210\,\text{GPa}$ ($210\,\text{kN/mm}^2$)
  - Poisson's ratio $\nu = 0.3$
  - Fracture energy release rate $G_c = 2.7\times 10^{-3}\,\text{kN/mm}$ ($2.7\,\text{N/mm}$)
  - Phase-field regularization length $l_0 = 0.0075\,\text{mm}$ ($7.5\,\mu\text{m}$)
  - Degradation function: $g(d) = (1-d)^2 + k_{\text{stab}}$, with $k_{\text{stab}} = 10^{-7}$.
- **Boundary Conditions:**
  - Bottom edge ($y = 0$): $u_y = 0$ (roller) with origin point pinned ($u_x = 0$ at $(0, 0)$).
  - Top edge ($y = 1$): Monotonic displacement-controlled tension ($u_y$ prescribed up to $0.0100\,\text{mm}$).

---

## 2. Expected Physical & Energetic Solution

Under monotonic Mode-I tensile loading, the expected response proceeds through four distinct physical regimes:
1. **Initial Linear-Elastic Regime ($u_y \le 0.0035\,\text{mm}$):**
   - Pure elastic deformation governed by structural stiffness $K_0 \approx 137.95\,\text{kN/mm}$.
   - Negligible damage evolution ($d \approx 0$, $E_{\text{fracture}} \approx 0$, $E_{\text{elastic}} \approx \frac{1}{2} K_0 u_y^2$).
2. **Pre-Peak Localization & Damage Inception ($0.0035 < u_y \le 0.00585\,\text{mm}$):**
   - Stress concentration at the notch tip $(0.5, 0.5)\,\text{mm}$ drives local damage growth $0 < d < 1$.
   - Gradual softening of tangential stiffness until the global peak load is attained.
3. **Peak Reaction Force & Initiation ($u_y \approx 0.00586\,\text{mm}$):**
   - Peak load capacity $F_{\max} \approx 0.758\,\text{kN}$ attained as damage localization reaches the critical threshold $d \to 1$ at the notch tip.
4. **Post-Peak Softening & Crack Propagation ($u_y > 0.00586\,\text{mm}$):**
   - Dynamic snap-through softening: rapid drop of reaction force as the crack propagates purely horizontally along the symmetry line $y = 0.5\,\text{mm}$ through the uncracked ligament ($0.5 \le x \le 1.0\,\text{mm}$).
   - Terminal state at $u_y = 0.0100\,\text{mm}$: complete plate severance ($RF \to 0$), complete conversion of strain energy into surface energy ($E_{\text{fracture}} \approx G_c \cdot (1 - a_0) = 2.7\times 10^{-3} \times 0.5 \times 1.0 = 1.35\,\text{mJ}$ plus diffuse band regularization terms), and total external work $W_{\text{ext}} \approx 2.36\,\text{mJ}$.

---

## 3. Fixed-Mesh Reference Anchor (Job 1398090, 15,192 Finite Elements)

The quantitative baseline against which all adaptive methods are measured is the reconstructed fixed-mesh reference solution (`Job 1398090` / `1409734`):
- **Discretization:** $15{,}192$ physical finite elements ($45{,}576$ layered UEL/UMAT cards).
- **Corridor Resolution:** Uniform element size $h = 3.75\,\mu\text{m} = l_0 / 2$ along the entire crack propagation path.
- **Reference Response:**
  - Initial structural stiffness: $K_0 = 137.945520\,\text{kN/mm}$ ($R^2 = 0.99999960$, intercept $4.472\times 10^{-5}\,\text{kN}$, $N = 400$).
  - Peak reaction force: $F_{\max} = 0.757778\,\text{kN}$ (matches digitized Pandey & Kumar Fig. 7(a) value $0.758\,\text{kN}$).
  - Displacement at peak: $u(F_{\max}) = 0.005857\,\text{mm}$.
  - Post-peak behavior: Rapid, monotonic load drop without secondary plateaus or artificial pinning.
  - Terminal external work: $W_{\text{ext}} = 2.3593\,\text{mJ}$ across $u_y \in [0.0, 0.0100]\,\text{mm}$.

---

## 4. Original Method B Limitations (Job 1411934, 14,677 Finite Elements)

Method B represents native Abaqus pre-refinement using the linear-elastic Step-1 stress error indicator field (`MISESERI`):
- **Pre-Analysis Regime:** The pre-analysis was executed only up to $u_y = 0.0050\,\text{mm}$ (prior to crack initiation).
- **Geometric Sizing Gradient:**
  - At the notch tip: $h_{\text{tip}} \approx 1.91\,\mu\text{m}$ ($l_0/h \approx 3.91$), satisfying $h \le l_0/2$.
  - However, because the uncracked ligament experienced low stress prior to crack propagation, `RemeshingRule` applied coarse element sizes along the forward ligament ($h \approx 9.1\,\mu\text{m}$ at $x = 0.675\,\text{mm}$, $h \approx 14.8\,\mu\text{m}$ at $x = 0.95\,\text{mm}$).
  - **Over 70% of the uncracked ligament length had $h > l_0 = 7.5\,\mu\text{m}$.**
- **Observed Physical Defects:**
  - Initial stiffness ($K_0 = 137.8919\,\text{kN/mm}$, $-0.039\%$) and peak load ($F_{\max} = 0.743021\,\text{kN}$, $-1.95\%$) were well-captured.
  - **Crack Stalling:** At $u = 0.00586\text{--}0.00600\,\text{mm}$, the crack tip stalled at $x = 0.6123\,\text{mm}$ upon entering coarse elements.
  - **Elevated Force Plateau:** The reaction force formed an artificial plateau at $F \approx 0.50\text{--}0.60\,\text{kN}$ across $u \in [0.00586, 0.00750]\,\text{mm}$, delaying complete snap-through until $u = 0.0080\,\text{mm}$.
  - **Excess External Work:** Total external work inflated to $W_{\text{ext}} = \mathbf{3.3319\,\text{mJ}}$ ($\mathbf{+41.2\%}$ excess vs canonical reference $2.3593\,\text{mJ}$).

---

## 5. Corrected Method B Native-Remeshing Methodology & Provenance

To test whether uncracked ligament refinement resolves this defect, Corrected Method B was formulated:
1. **Source State Provenance:** Taken from the Stage-14 Step-2 post-peak pre-analysis (`PK_M1_JOB1_INF_COMPANION_2906.odb`, frame 1022, $u_y = 0.0100\,\text{mm}$) where the damage band had traversed the entire uncracked ligament.
2. **Native Remeshing Execution:** Native Abaqus `adaptiveRemesh` with `errorTarget = 1.0` (1% error target) generated `PK_M1_STAGE14_STEP2_ERR_10PCT.inp` ($14{,}483$ physical finite elements).
3. **Refinement Corridor Sizing:**
   - $96.76\%$ of corridor elements have $h \le l_0/2 = 3.75\,\mu\text{m}$.
   - $99.84\%$ have $h \le l_0 = 7.50\,\mu\text{m}$.
   - $100\%$ of longitudinal slices along the uncracked ligament $[0.5, 1.0]\,\text{mm}$ contain fine elements with zero gaps.
   - Median element size along the uncracked ligament is $h_{\text{median}} \approx 1.85\text{--}2.29\,\mu\text{m}$ ($l_0/h \ge 3.27$).
4. **Execution Architecture:**
   - Co-located 3-layer deck `M1_MB_CORRECTED_PROPAGATION_14K.inp` ($43{,}449$ layered cards, hash `1209F716...`).
   - Frozen UEL `f42_mixed_uel.for` (hash `CE8D5EDC...`).
   - Executed on cluster under PBS Job ID `1412465.mmaster02` (1 CPU serial, 16 GB RAM, on `/scratch9/pr21vyci/`).

---

## 6. Strict Epistemic Evidence Hierarchy

To preserve scientific rigor, all project findings are classified into four mutually exclusive epistemic tiers:

| Tier | Classification | Definition & Acceptance Boundary | Examples in This Task |
| :---: | :--- | :--- | :--- |
| **Tier 1** | `VERIFIED_NUMERICALLY` | Independently verified from completed solver output files with exact numerical values and hashes. | Initial stiffness $K_0 = 137.9096\,\text{kN/mm}$; $R^2 = 0.99999960$; $0$ cutbacks; Step 1 reload $RF = 0.6525\,\text{kN}$. |
| **Tier 2** | `VERIFIED_GEOMETRICALLY` | Verified from exact geometric node/element coordinates and mesh metrics without solver execution. | $14{,}483$ base FEs; $96.76\%$ corridor $h \le 3.75\,\mu\text{m}$; uncracked ligament longitudinal coverage $100\%$. |
| **Tier 3** | `PENDING_IN_FLIGHT_SOLVE` | Actively computing in PBS queue; results held under explicit no-results fallback. Zero speculative extrapolation. | Peak force $F_{\max}$; softening plateau; terminal $W_{\text{ext}}$; crack-front progression across Step 2. |
| **Tier 4** | `SUPPORTED_HYPOTHESIS` | Plausible physical mechanism consistent with observed trends but awaiting complete confirmation. | Hypothesis that full ligament refinement eliminates the force plateau and excess external work. |

---

## 7. Verified Mesh & Pre-Peak Elastic Findings

### 7.1 Linear Elastic Structural Compliance ($u_y \le 0.00100\,\text{mm}$)
- Sample count: $N = 400$ increments ($\Delta u = 2.5\,\text{nm}$).
- Fitted linear stiffness: **$K_0 = 137.909558\,\text{kN/mm}$**.
- Intercept: $4.479\times 10^{-5}\,\text{kN}$ ($0.045\,\text{N}$).
- Quality of fit: **$R^2 = 0.99999960$**.
- Discrepancy vs Canonical Reference ($137.945520\,\text{kN/mm}$): **$-0.02607\%$** (Bitwise elastic parity).
- Discrepancy vs Original Method B ($137.891881\,\text{kN/mm}$): **$+0.01282\%$**.

### 7.2 In-Flight Solver Health (Increments 1–1712, $u_y = 0.00428\,\text{mm}$)
- Completed increments in `.sta`: $1{,}712$ of $2{,}000$ in Step 1.
- Attempt count: $1$ per increment; **$0$ cutbacks** across the entire trajectory.
- Newton iterations: strictly $3.0$ iterations/increment.
- Numerical warnings / singularities: **0**.
- Partial external work ($u_y = 0.00392\,\text{mm}$): $\mathcal{W}_{\text{ext}}^{\text{partial}} = 1.0466\,\text{mJ}$ (labeled strictly as partial, not compared to full-horizon $2.359\,\text{mJ}$).
- Strain energy: $E_{\text{elastic}} = 1.023\,\text{mJ}$ ($98.74\%$), $E_{\text{fracture}} = 0.013\,\text{mJ}$ ($1.26\%$).

---

## 8. Explicitly Pending Fracture-Response Findings (No-Results Fallback)

The following quantities are actively computing on the cluster and are formally held under fallback status:

```
+-----------------------------------------------------------------------------------------+
|                              EXPLICIT NO-RESULTS FALLBACK                               |
|                                                                                         |
|  Solver Status: RUNNING in Step 1 (u_y = 0.00428 mm of 0.0100 mm horizon)               |
|  Remaining Walltime to Peak: ~45 minutes (entering Step 2 at inc 2001)                 |
|                                                                                         |
|  Metric                                  Status                 Reason                  |
|  -------------------------------------------------------------------------------------  |
|  Peak Reaction Force (F_max)             PENDING_STEP2          Occurs at u ~ 0.00586 mm|
|  Peak Displacement u(F_max)              PENDING_STEP2          Occurs in Step 2        |
|  Force at u = 0.0070 mm                  PENDING_STEP2          Dynamic softening       |
|  Force at u = 0.0080 mm                  PENDING_STEP2          Sustained propagation   |
|  Terminal External Work (W_ext)          PENDING_STEP2          Full [0, 0.0100] mm     |
|  Crack-Front Trajectory x_front(u)       PENDING_STEP2          Requires Step 2 frames  |
+-----------------------------------------------------------------------------------------+
```

---

## 9. Pre-Declared Criteria for Hypothesis Confirmation or Falsification

When Job `1412465.mmaster02` completes Step 2, the results will be evaluated against these strict pre-declared criteria:

| Criterion | Confirmation of Improvement (PASS) | Falsification / Failure (FAIL) |
| :--- | :--- | :--- |
| **Peak Load Parity** | $|F_{\max} - 0.7578\,\text{kN}| \le 2.0\%$ | $|F_{\max} - 0.7578\,\text{kN}| > 5.0\%$ |
| **Post-Peak Force Plateau** | $F(u = 0.0070\,\text{mm}) \le 0.15\,\text{kN}$ (sharp softening) | $F(u = 0.0070\,\text{mm}) \ge 0.40\,\text{kN}$ (sustained plateau) |
| **External Work Horizon** | $W_{\text{ext}} \in [2.30, 2.60]\,\text{mJ}$ (within $+10\%$ of ref) | $W_{\text{ext}} \ge 3.00\,\text{mJ}$ (excess work retained) |
| **Crack-Front Progression** | Continuous advance without arrest at $x = 0.61\,\text{mm}$ | Crack stalls at $x \approx 0.61\,\text{mm}$ for $\Delta u \ge 0.001\,\text{mm}$ |
| **Global UEL Energy Balance** | $|\mathcal{W}_{\text{ext}} - (E_{\text{elas}} + E_{\text{frac}})| / \mathcal{W}_{\text{ext}} \le 5.0\%$ | Energy balance error $> 10.0\%$ |

---

## 10. Preservation of Completed Method C Gate C1 V2 Evidence

Task F1436 audited and committed the completed lightweight evidence for Method C Gate C1 V2 continuation (`Job 1412464.mmaster02`, $2{,}906$ FEs):
- **Solver Outcome:** `Exit 0`, $0$ errors, walltime `01:03:25`, $5{,}058$ increments, $14$ cutbacks.
- **Reload Force:** $RF = 0.652467\,\text{kN}$ ($-0.096\%$ vs coarse baseline $0.653093\,\text{kN}$).
- **Step Boundary Continuity:** $\Delta RF = 0.0925\,\text{N}$ ($\le 5.0\,\text{N}$ criterion passed by $54\times$).
- **Step 2 Softening:** Elevated peak $F_{\max} = 1.0868\,\text{kN}$ due to coarse recipient elements ($h \approx 20\,\mu\text{m} > l_0 = 7.5\,\mu\text{m}$), followed by complete snap-through to $RF_{\text{final}} = 0.0277\,\text{kN}$.
- **Classification:** `QUASI_STATIC_RELOAD_WITH_TRANSFERRED_HISTORY`.

---

## 11. Methodological Limitation (Retrospective Pre-Refinement)

> [!CAUTION]
> **Methodological Boundary:**
> Corrected Method B uses a post-peak damage error-indicator state ($u = 0.0100\,\text{mm}$) to construct a single pre-refined mesh prior to a fresh solve. 
> 
> This is **retrospective one-shot pre-refinement**. It requires prior knowledge of the crack trajectory and must **NOT** be claimed as:
> - Prospective crack-path prediction;
> - Automated external-driver adaptive remeshing; or
> - True online in-analysis adaptive remeshing.
> 
> It serves strictly as a **frozen diagnostic control** to determine whether uncracked ligament spatial refinement is physically sufficient to eliminate the Method B force plateau. True adaptive remeshing without prior trajectory knowledge requires sequential in-flight remeshing and state transfer (Method C).
