# Mode-I Benchmark: Corrected Method B Fracture Response Evaluation, In-Flight Progression, and Reference Comparison

**Protocol Version:** 2  
**Task ID:** `F1440-MODE1-CORRECTED-METHOD-B-STEP2-FRACTURE-ANALYSIS` (Updated from Task F1439)  
**Date:** 13 October 2026  
**Author:** Gemini Antigravity  
**Status:** `IN_FLIGHT_SOLVE_STEP2_ACTIVE_WITH_EXPLICIT_FALLBACK`  
**Governing Directive:** *"We need to have understood everything related to the first model before we increase complexity."*  

---

## 1. Problem Definition & Boundary Value Problem

The investigation considers the canonical Pandey & Kumar (2025) Mode-I tensile fracture benchmark:
- **Geometry:** Square plate $\Omega = [0.0, 1.0] \times [0.0, 1.0]\,\text{mm}^2$ ($1.0 \times 1.0\,\text{mm}$).
- **Pre-Existing Crack:** Horizontal zero-gap seam slit at $y = 0.5\,\text{mm}$ spanning $0 \le x \le 0.5\,\text{mm}$ ($a_0 = 0.5\,\text{mm}$).
  *(Note: The initial finite-width notch was an erroneous implementation that radically altered structural compliance; the sharp seam with duplicate node pairs along the flanks is the authoritative benchmark representation).*
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

### Energetic Definitions & Bookkeeping Identity
- **Stored Elastic Energy ($E_{\text{elastic}}$):** $\int_{\Omega} \psi_e(\boldsymbol{\varepsilon}, d)\,d\Omega$, evaluated from UEL SDV18.
- **Fracture Surface Energy ($E_{\text{fracture}}$):** $\int_{\Omega} G_c \gamma(d, \nabla d)\,d\Omega$, evaluated from UEL SDV17.
- **External Work ($W_{\text{ext}}$):** $\int_0^u F(\tilde{u})\,d\tilde{u}$, evaluated by trapezoidal integration of top-edge reaction force vs prescribed displacement.
- **Energy-Balance Residual ($\Delta E$):**
  $$\Delta E = W_{\text{ext}} - \left(E_{\text{elastic}} + E_{\text{fracture}}\right)$$
  In discrete finite-element calculations, $\Delta E$ is non-zero due to finite increment size, numerical integration approximations, and spatial discretization effects. It must be explicitly stated rather than silently assumed to vanish.

---

## 3. Fixed-Mesh Reference Anchor (Job 1398090, 15,192 Finite Elements)

The quantitative baseline against which all adaptive methods are measured is the reconstructed fixed-mesh reference solution (`Job 1398090` / `1409734`):
- **Discretization:** $15{,}192$ finite elements ($45{,}576$ co-located element records across 3 layers: Layer 1 Phase UEL, Layer 2 Mechanical UEL, Layer 3 Companion UMAT).
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
- **Discretization:** $14{,}677$ finite elements ($44{,}031$ co-located element records across 3 layers).
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
2. **Native Remeshing Execution:** Native Abaqus `adaptiveRemesh` with `errorTarget = 1.0` (1% error target) generated `PK_M1_STAGE14_STEP2_ERR_10PCT.inp` ($14{,}483$ finite elements, $43{,}449$ co-located element records).
3. **Refinement Corridor Sizing (Precise Epistemic Boundary):**
   - $96.76\%$ of corridor elements have $h \le l_0/2 = 3.75\,\mu\text{m}$.
   - $99.84\%$ have $h \le l_0 = 7.50\,\mu\text{m}$.
   - All 50 longitudinal slices (spatial bins) along the uncracked ligament $[0.5, 1.0]\,\text{mm}$ contain fine elements ($h \le 3.75\,\mu\text{m}$).
   - Median element size along the uncracked ligament is $h_{\text{median}} \approx 1.85\text{--}2.29\,\mu\text{m}$ ($l_0/h \ge 3.27$).
   - *Epistemic Qualification:* While bin presence confirms that fine elements exist across all longitudinal stations, bin coverage alone does **not** prove a continuously connected, sufficiently resolved crack propagation path. That remains a hypothesis to be evaluated through full-field damage progression in Step 2.
4. **Execution Architecture:**
   - Co-located 3-layer deck `M1_MB_CORRECTED_PROPAGATION_14K.inp` ($43{,}449$ co-located element records, hash `1209F716...`).
   - Frozen UEL `f42_mixed_uel.for` (hash `CE8D5EDC...`).
   - Executed on cluster under PBS Job ID `1412465.mmaster02` (1 CPU serial, 16 GB RAM, on `/scratch9/pr21vyci/`).

---

## 6. Strict Epistemic Evidence Hierarchy

To preserve scientific rigor, all project findings are classified into four mutually exclusive epistemic tiers:

| Tier | Classification | Definition & Acceptance Boundary | Examples in This Task |
| :--- | :--- | :--- | :--- |
| **Tier 1** | `VERIFIED_NUMERICALLY` | Independently verified from completed solver output files with exact numerical values and hashes. | Initial stiffness $K_0 = 137.9096\,\text{kN/mm}$; $R^2 = 0.99999960$; $0$ cutbacks; Step 1 reload $RF = 0.6525\,\text{kN}$; partial energy residual $\Delta E = 0.0103\,\text{mJ}$. |
| **Tier 2** | `VERIFIED_GEOMETRICALLY` | Verified from exact geometric node/element coordinates and mesh metrics without solver execution. | $14{,}483$ finite elements; $96.76\%$ corridor $h \le 3.75\,\mu\text{m}$; 50/50 longitudinal bins contain fine elements; active path continuity remains to be tested under fracture. |
| **Tier 3** | `PENDING_IN_FLIGHT_SOLVE` | Actively computing in PBS queue; results held under explicit no-results fallback. Zero speculative extrapolation. | Peak force $F_{\max}$; softening plateau; terminal $W_{\text{ext}}$; crack-front progression across Step 2. |
| **Tier 4** | `SUPPORTED_HYPOTHESIS` | Plausible physical mechanism consistent with observed trends but awaiting complete confirmation. | **Hypothesis to be tested:** whether extended corridor refinement reduces or eliminates artificial crack pinning, elevated force plateau ($0.50\text{--}0.60\,\text{kN}$), and excess external work. |

> [!IMPORTANT]
> Neither early elastic stiffness agreement nor fine element sizes establish the post-peak fracture behavior. The crack-pinning mechanism remains strictly a hypothesis to be tested against Step-2 data.

---

## 7. Verified Mesh & Pre-Peak Elastic Findings

### 7.1 Linear Elastic Structural Compliance ($u_y \le 0.00100\,\text{mm}$)
- Sample count: $N = 400$ increments ($\Delta u = 2.5\,\text{nm}$).
- Fitted linear stiffness: **$K_0 = 137.909558\,\text{kN/mm}$**.
- Intercept: $4.479\times 10^{-5}\,\text{kN}$ ($0.045\,\text{N}$).
- Quality of fit: **$R^2 = 0.99999960$**.
- Discrepancy vs Canonical Reference ($137.945520\,\text{kN/mm}$): **$-0.02607\%$** (**close numerical agreement**; not bitwise identity).
- Discrepancy vs Original Method B ($137.891881\,\text{kN/mm}$): **$+0.01282\%$**.

### 7.2 Solver Telemetry & Energy Bookkeeping (Step 1 Complete, Step 2 In-Flight)
- **Step 1 Completion:** All $2{,}000$ of $2{,}000$ increments completed ($t_1 = 1.000$, $u_y = 0.00500\,\text{mm}$).
- **Step 2 In-Flight Telemetry:** Actively advancing through increments $>70$ of $5{,}000$ ($u_y > 0.00507\,\text{mm}$).
- **Attempt Count & Convergence:** $1$ attempt per increment; **$0$ cutbacks** across all $>2{,}070$ increments.
- **Newton Iterations:** strictly $3.0$ iterations/increment (quadratic asymptotic convergence).
- **Numerical Warnings / Singularities:** **0**.
- **Energy Bookkeeping at $u_y = 0.00392\,\text{mm}$ (Increment 1568):**
  - External work: $\mathcal{W}_{\text{ext}}^{\text{partial}} = 1.0466\,\text{mJ}$ (integrated over $u_y \in [0.0, 0.00392]\,\text{mm}$).
  - Stored elastic strain energy: $E_{\text{elastic}} = 1.0232\,\text{mJ}$ ($97.76\%$ of $\mathcal{W}_{\text{ext}}$).
  - Phase-field fracture surface energy: $E_{\text{fracture}} = 0.0131\,\text{mJ}$ ($1.25\%$ of $\mathcal{W}_{\text{ext}}$).
  - Total internal energy: $E_{\text{total}} = E_{\text{elastic}} + E_{\text{fracture}} = 1.0363\,\text{mJ}$ ($99.02\%$ of $\mathcal{W}_{\text{ext}}$).
  - **Energy-Balance Residual:**
    $$\Delta E = \mathcal{W}_{\text{ext}}^{\text{partial}} - (E_{\text{elastic}} + E_{\text{fracture}}) = 1.0466 - 1.0363 = 0.0103\,\text{mJ} \quad (0.98\%)$$
  - *Residual Characterization (Rigorous Epistemic Boundary):* The $0.0103\,\text{mJ}$ ($0.98\%$) residual at $u_y = 0.00392\,\text{mm}$ is an observed numerical discrepancy whose precise decomposition remains unverified; trapezoidal integration approximations over non-uniform increment intervals, time-step truncation, and early-stage spatial discretization are plausible contributing mechanisms, but have not been independently isolated as proven causes.

---

## 8. Explicitly Pending Fracture-Response Findings (No-Results Fallback)

The following quantities are actively computing on the cluster in Step 2 and are formally held under fallback status:

```
+-----------------------------------------------------------------------------------------+
|                              EXPLICIT NO-RESULTS FALLBACK                               |
|                                                                                         |
|  Solver Status: RUNNING in Step 2 (u_y > 0.00507 mm of 0.0100 mm horizon)               |
|  Step 1: COMPLETED (2,000 of 2,000 increments, u_y = 0.00500 mm, 0 cutbacks)            |
|  Step 2 Progress: Increment >70 of 5,000 (total increments >2,070, 0 cutbacks)          |
|  Estimated Incs to Peak Load (u_y ~ 0.005857 mm): ~780 increments in Step 2            |
|                                                                                         |
|  Metric                                  Status                 Reason                  |
|  -------------------------------------------------------------------------------------  |
|  Peak Reaction Force (F_max)             PENDING_STEP2          Occurs at u ~ 0.00586 mm|
|  Peak Displacement u(F_max)              PENDING_STEP2          Occurs in Step 2        |
|  Force at u = 0.005857 mm (matched ref)  PENDING_STEP2          Occurs in Step 2        |
|  Force at u = 0.0060 mm                  PENDING_STEP2          Early post-peak         |
|  Force at u = 0.0070 mm                  PENDING_STEP2          Plateau test point      |
|  Force at u = 0.0080 mm                  PENDING_STEP2          Propagation test point  |
|  Force at u = 0.0100 mm (terminal)       PENDING_STEP2          Full severance point    |
|  Terminal External Work (W_ext)          PENDING_STEP2          Full [0, 0.0100] mm     |
|  Crack-Front Trajectory x_front(u)       PENDING_STEP2          Requires Step 2 frames  |
+-----------------------------------------------------------------------------------------+
```

### Pre-Declared Extraction Contract for Step 2
When Step-2 increments become available:
1. Extract reaction force $RF_y$ at prescribed displacements matching canonical milestones: $u_y \in \{0.005857, 0.0060, 0.0070, 0.0080, 0.0100\}\,\text{mm}$.
2. Evaluate $F_{\max}$, $u(F_{\max})$, and softening force differences without extrapolation beyond the last accepted increment.
3. For crack-front progression, evaluate actual phase-field output in the ODB using a documented damage threshold ($d \ge 0.95$) and contiguous spatial connectivity from the notch tip $(0.5, 0.5)\,\text{mm}$. If ODB field outputs are not yet accessible, report crack-front progression as pending rather than inferring it from reaction force alone.

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

Task F1436 audited and committed the completed lightweight evidence for Method C Gate C1 V2 continuation (`Job 1412464.mmaster02`, $2{,}906$ finite elements):
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
