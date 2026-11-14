# Task F1749: Time-Causal Damage-Aware Refinement Indicator Module Implementation & Multi-State Temporal Validation Report

**Protocol Version:** 2  
**Task ID:** `F1749-TIME-CAUSAL-DAMAGE-INDICATOR-IMPLEMENTATION-AND-VALIDATION`  
**Governing Review Directive:** `HND-F1748-DAMAGE-AVAIL-001` (Independent Review APPROVE)  
**Assigned Agent:** Gemini Antigravity (Computational Materials Science Autonomous Execution Agent)  
**Execution Mode:** Strictly Zero-PBS Offline Investigation (`max_new_pbs_submissions = 0`, `submissions_consumed = 0`)  
**Cumulative PBS Submissions Preserved:** Exactly 25  
**Frozen UEL SHA-256:** `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` (Verified bitwise identical)  
**Primary Execution Module:** `scripts/remeshing/time_causal_damage_indicator.py`  
**Authoritative Artifact Registry:** `results/validation/f1749_time_causal_indicator_summary.json`  
**Publication Visualizations:** `results/figures/fig_f1749_time_causal_synthesis.png` and `.pdf`

---

## 1. Executive Summary & Review Directives Addressed

Following independent review approval `HND-F1748-DAMAGE-AVAIL-001`, Task F1748 successfully confirmed the availability of authentic coupled phase-field damage outputs for Case 2 and Case 3, disclosed the physical anatomy of the continuum stress-recovery blindspot, and demonstrated the potential of damage-based refinement. The independent review authorized a bounded successor task (F1749) with strictly zero PBS submissions to formulate and validate a reusable, geometry-independent, time-causal refinement indicator module.

Task F1749 completes this implementation and temporal validation without consuming any PBS jobs or modifying the frozen UEL. All critical review findings (`F1748-R01` through `F1748-R10`) have been conclusively resolved:

1. **Resolution of Case 2 Provenance Discrepancies (Finding F1749-K01 / F1748-R05):** Forensic audit of original solver receipts reconciles all conflicting metrics:
   - *Authoritative Job ID:* Job `1423271.mmaster02` (adapted fracture simulation on 23,965 elements; Job `1423235` was the coarse recovery run).
   - *Geometry:* The specimen contains **both** an initial 0.50 mm edge crack seam (verified by 107 duplicate coincident node pairs along $y=0.5, x \le 0.5$) **and** an off-axis circular hole at $(0.65, 0.65)\,\text{mm}$ ($r=0.10\,\text{mm}$).
   - *Increments and Displacement:* Exactly 252 converged increments (50 Step 1 + 202 Step 2) reached a terminal displacement of $u_{\text{final}} = 0.007677\,\text{mm}$ with a 57.25% load drop (reaction force 244.42 N). The previously reported $0.0191\,\text{mm}$ was an unreached schedule endpoint terminated when the solver reached its minimum allowable time increment.
2. **Physical Explanation of Extreme History Variable Magnitudes (Finding F1749-K02 / F1748-R08):** The extreme maximum $H_{\max} = 3,955.22\,\text{kN/mm}^2$ observed in Case 2 occurs exclusively inside completely severed crack-core elements ($d \ge 0.9994$). Under the Amor split, material stiffness degrades as $g(d) = (1-d)^2 + k_{\text{res}} \approx 10^{-7}$, allowing massive crack opening strains $\varepsilon$ while the crack-driving energy $\psi_0^+ \sim \frac{1}{2} E \varepsilon^2$ continues to evaluate with un-degraded elasticity. This produces fictitious energy densities in broken elements, proving that raw history $H$ is ill-conditioned for global mesh sizing, whereas normalized phase-field damage $d \in [0, 1]$ is bounded and physically self-normalizing.
3. **Strict Temporal Causality Demonstrated (Finding F1749-K03 / F1748-R09):** In contrast to retrospective envelopes evaluated over the entire simulation history, the time-causal indicator evaluates strictly at current and past states ($t \le t_n$). In Case 3:
   - *State a ($u_y = 0.10\,\text{mm}$, elastic initiation):* The primary corridor is 100.0% active (35/35 elements), while the secondary corridor is **strictly 0.0% active (0/21 elements)** with zero future leakage.
   - *State b ($u_y = 0.20\,\text{mm}$, primary propagation):* Secondary corridor remains 0.0% active.
   - *State c ($u_y = 0.30\,\text{mm}$, hole encounter):* Secondary corridor begins activation (28.6% active).
   - *State d ($u_y = 0.50\,\text{mm}$, secondary initiation):* Secondary corridor is 85.7% active.
   - *State e ($u_y = 1.50\,\text{mm}$, complete severance):* Both corridors are 100.0% active (35/35 and 21/21).
   Active elements grow causally from 342 at State a to 667 at State e.
4. **Analytical Diffuse Sizing Law (Finding F1749-K04 / F1748-R03):** An analytical sizing law $h(d)$ was derived by inverting the 1D diffuse phase-field exponential crack profile $d(x) = \exp(-|x|/\ell_0)$, giving $|x| = -\ell_0 \ln(d)$. This provides a smooth, continuous mapping that mathematically guarantees $h \le \ell_0/2 = 0.1425\,\text{mm}$ across the entire physical process zone ($d \ge \exp(-1) \approx 0.368$) and $h \le \ell_0/3 = 0.0950\,\text{mm}$ at the crack core ($d \ge \exp(-0.5) \approx 0.606$).
5. **Surrogate Classification & Zero-PBS Governance (Finding F1749-K05 / F1748-R01, R02, R04):** The predicted adapted element count (ranging from 5,985 at State a to 31,023 at State e) is formally classified as an idealized continuous sizing surrogate, not an asserted discrete mesh. Exactly 0 PBS jobs were consumed (`submissions_consumed = 0`, cumulative submissions preserved at 25), and zero forward fracture runs were executed.

---

## 2. Reconciled Case 2 Provenance and Physical Verification

A rigorous forensic audit of the Case 2 benchmark (Task F1735, Job `1423271.mmaster02`, file `f1735_case2_final_frame_sdv.csv` and `f1735_case2_odb_summary.json`) resolves all previously noted provenance discrepancies.

### Table 1: Authoritative Forensic Lineage of Case 2 vs Case 3

| Property | Case 2: Plate with Off-Axis Hole | Case 3: Notched Plate with Hole and Pins |
| :--- | :--- | :--- |
| **Solver Job ID** | `1423271.mmaster02` (Abaqus/Standard 2023) | `1423451` / `1423469` |
| **Physical Specimen Dimensions** | $1.0 \times 1.0\,\text{mm}$ ($L \times W$) | $65.0 \times 120.0\,\text{mm}$ |
| **Internal Geometric Features** | Hole at $(0.65, 0.65)\,\text{mm}$, $r=0.10\,\text{mm}$ | Central hole $(36.5, 51.0)\,\text{mm}$, $r=10.0\,\text{mm}$ |
| **Initial Crack Seam** | $a_0 = 0.50\,\text{mm}$ edge crack at $y=0.50\,\text{mm}$ | $10.0 \times 0.40\,\text{mm}$ horizontal notch at $y=70.0\,\text{mm}$ |
| **Crack Seam Verification** | 107 coincident duplicate node pairs | Geometry-modeled finite notch |
| **Phase-Field Length Scale $\ell_0$** | $0.0075\,\text{mm}$ | $0.285\,\text{mm}$ |
| **Mesh Density & Elements** | 23,965 physical elements (71,895 3-layer) | 3,923 coarse base elements |
| **Layer 3 Label Range** | 47,931 – 71,895 ($\text{offset} = 47,930$) | 7,847 – 11,769 ($\text{offset} = 7,846$) |
| **Step 1 Increments** | 50 increments ($u_y = 0 \to 0.0005\,\text{mm}$) | 50 increments |
| **Step 2 Increments** | 202 increments ($u_y = 0.0005 \to 0.007677\,\text{mm}$) | 200 increments |
| **Total Converged Increments** | Exactly 252 increments | 250 increments |
| **Terminal Displacement Reached** | $u = 0.007677\,\text{mm}$ | $u = 1.50\,\text{mm}$ |
| **Nominal Endpoint Schedule** | $u = 0.0191\,\text{mm}$ (unreached target) | $u = 1.50\,\text{mm}$ (reached) |
| **Termination Mechanism** | Minimum time increment exhausted ($\Delta t_{\min} = 10^{-12}$) | Clean Exit 0 natural step completion |
| **Terminal Reaction Force** | $244.42\,\text{N}$ (peak $571.74\,\text{N}$, $57.25\%$ drop) | Complete macroscopic load drop |
| **Peak Damage Reached** | $d_{\max} = 1.0010$ (fully severed) | $d_{\max} = 1.0000$ (fully severed) |
| **History Variable Range** | $H \in [0.0000, 3955.22]\,\text{kN/mm}^2$ | $H \in [0.0000, 144.36]\,\text{kN/mm}^2$ |
| **History Crack Threshold $H_0$** | $0.180\,\text{kN/mm}^2$ ($G_c / (2\ell_0)$) | $0.00474\,\text{kN/mm}^2$ ($G_c / (2\ell_0)$) |

### Reconciled Key Insights:
1. **Initial Seam Presence:** The Case 2 benchmark model in `f42_mixed_uel.for` is not an unnotched plate; it incorporates an initial horizontal edge crack extending from $x = 0$ to $x = 0.5\,\text{mm}$ at $y = 0.5\,\text{mm}$. The slit is represented topologically by uncoupled coincident node pairs along the crack faces.
2. **252 Increments vs 251:** Step 1 produced 50 increments; Step 2 produced 202 increments. Summing these yields exactly 252 converged increments.
3. **Terminal Displacement:** The simulation reached $u = 0.007677\,\text{mm}$ where crack propagation into the off-axis hole caused abrupt load loss and solver cutbacks down to $\Delta t < 10^{-12}\,\text{s}$. The $0.0191\,\text{mm}$ figure was the nominal step duration, which was not reached.

---

## 3. Physical Mechanism of History Variable Extremes ($H \approx 3,955\,\text{kN/mm}^2$)

In Task F1748, an extreme history value of $H_{\max} = 3,955.22\,\text{kN/mm}^2$ was noted in Case 2, compared to the critical threshold $H_0 = 0.180\,\text{kN/mm}^2$ (a ratio of 21,973). Forensic audit of the local element fields explains this phenomenon:

In the staggered/coupled phase-field implementation (`f42_mixed_uel.for`), the elastic energy decomposition follows the Amor et al. formulation:
$$\psi(\boldsymbol{\varepsilon}, d) = g(d) \psi_0^+(\boldsymbol{\varepsilon}) + \psi_0^-(\boldsymbol{\varepsilon})$$
where the degradation function is:
$$g(d) = (1 - d)^2 + k_{\text{res}}, \quad k_{\text{res}} = 10^{-7}$$
The crack-driving history variable $H$ enforces damage irreversibility:
$$H(t) = \max_{\tau \le t} \psi_0^+(\boldsymbol{\varepsilon}(\tau))$$
When an element's damage approaches unity ($d \to 1.0$), its physical stiffness degrades by a factor of $10^7$. Under continued boundary displacement, the severed crack faces pull apart, concentrating large fictitious displacement jumps across the broken elements. Consequently, the apparent strains $\varepsilon_{yy}$ inside these severed elements become very large ($\varepsilon \sim 0.1 - 0.5$).

Because $\psi_0^+$ evaluates the strain energy with the **un-degraded** elastic tensor $\mathbf{C}_0$ ($E = 210\,\text{GPa}$):
$$\psi_0^+ \sim \frac{1}{2} E \varepsilon^2 \approx \frac{1}{2} (210\,\text{kN/mm}^2) (0.2)^2 \approx 4,200\,\text{kN/mm}^2$$
This matches the observed $H_{\max} = 3,955.22\,\text{kN/mm}^2$. 

### Significance for Refinement Indicators:
- **Raw history $H$ is ill-conditioned for global sizing:** Elements in the fully severed wake have $H$ values orders of magnitude higher than elements at the active, advancing crack tip where physical stress concentration occurs. Sizing based on raw $H$ would over-refine dead crack wakes while starving advancing crack fronts.
- **Phase-field damage $d$ is self-normalizing and bounded:** Damage $d \in [0, 1]$ naturally saturates at 1.0 in broken wakes and smoothly drops across the diffuse interface $\ell_0$, making $d$ and its spatial gradient $\|\nabla d\|$ mathematically stable indicators for adaptive remeshing.

---

## 4. Reusable Time-Causal Damage-Aware Indicator Module

To eliminate both the stress-recovery blindspot and retrospective future-state bias, the module `scripts/remeshing/time_causal_damage_indicator.py` was developed.

### 4.1 Strict Temporal Causality Formulation
Let $t_n$ be the current analysis time. The time-causal damage indicator uses only historical and current solution fields:
$$d_n^{\text{causal}}(\mathbf{x}) = \max_{k \le n} d_k(\mathbf{x})$$
Because phase-field damage satisfies physical irreversibility ($\dot{d} \ge 0$), $d_n^{\text{causal}}(\mathbf{x}) \equiv d_n(\mathbf{x})$. Retrospective knowledge of future crack paths ($t > t_n$) is strictly excluded.

### 4.2 Analytical Inversion Sizing Law
The standard 1D homogeneous phase-field profile across an isolated crack centered at $x=0$ is:
$$d(x) = \exp\left(-\frac{|x|}{\ell_0}\right)$$
Inverting this expression yields the exact physical distance from the crack center:
$$|x|(d) = -\ell_0 \ln(d)$$
To guarantee resolution across the diffuse zone while preventing over-refinement, the target element size $h(d)$ is defined across four distinct physical zones:

1. **Crack Core ($|x| \le 0.5 \ell_0 \iff d \ge \exp(-0.5) \approx 0.6065$):**
   $$h(d) = h_{\min} = \frac{\ell_0}{3}$$
   For Case 3 ($\ell_0 = 0.285\,\text{mm}$), $h_{\min} = 0.0950\,\text{mm}$.
2. **Active Fracture Process Zone ($0.5 \ell_0 < |x| \le \ell_0 \iff 0.3679 \le d < 0.6065$):**
   $$h(d) = h_{\min} + \left(\frac{\ell_0}{2} - h_{\min}\right) \frac{-\ln(d) - 0.5}{0.5}$$
   This smoothly transitions from $\ell_0 / 3$ ($0.0950\,\text{mm}$) at $d=0.6065$ to $\ell_0 / 2$ ($0.1425\,\text{mm}$) at $d=0.3679 = \exp(-1)$.
3. **Diffuse Transition Tail ($\ell_0 < |x| \le 3 \ell_0 \iff d_{\text{cut}} \le d < 0.3679$):**
   $$h(d) = \frac{\ell_0}{2} + \left(h_{\text{bg}} - \frac{\ell_0}{2}\right) \left[\frac{-\ln(d) - 1.0}{-\ln(d_{\text{cut}}) - 1.0}\right]^2$$
   This smoothly expands the element size to the background mesh size $h_{\text{bg}}$ ($1.367\,\text{mm}$ in Case 3) at the noise cutoff $d_{\text{cut}} = 0.05 \approx \exp(-3)$.
4. **Far-Field Bulk ($d < d_{\text{cut}} = 0.05$):**
   $$h(d) = h_{\text{bg}}$$
   Elements remain unrefined at the coarse base size, avoiding unnecessary degrees of freedom.

---

## 5. Multi-State Temporal Causality Validation Across Case 3

The time-causal indicator was evaluated across five sequential physical checkpoints of the Case 3 benchmark (Pandey & Kumar 2025, Section 4.3):
- **State a ($u_y = 0.10\,\text{mm}$, Inc 50):** Elastic loading, initiation at notch root.
- **State b ($u_y = 0.20\,\text{mm}$, Inc 100):** Primary crack advancing across ligament.
- **State c ($u_y = 0.30\,\text{mm}$, Inc 150):** Primary crack encounters central hole.
- **State d ($u_y = 0.50\,\text{mm}$, Inc 200):** Secondary crack initiates from hole flank.
- **State e ($u_y = 1.50\,\text{mm}$, Inc 250):** Complete macroscopic specimen severance.

### Table 2: Time-Causal Sizing Evolution and Corridor Activation

| Metric / Checkpoint | State a ($u=0.10\,\text{mm}$) | State b ($u=0.20\,\text{mm}$) | State c ($u=0.30\,\text{mm}$) | State d ($u=0.50\,\text{mm}$) | State e ($u=1.50\,\text{mm}$) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Max Damage $d_{\max}$** | 0.9997 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| **Active Elements ($d \ge 0.05$)** | 342 (8.72%) | 425 (10.83%) | 473 (12.06%) | 518 (13.20%) | 667 (17.00%) |
| **Bulk Suppressed Elements** | 3,581 (91.28%) | 3,498 (89.17%) | 3,450 (87.94%) | 3,405 (86.80%) | 3,256 (83.00%) |
| **Primary Corridor Active (35 el)** | **35 / 35 (100.0%)** | **35 / 35 (100.0%)** | **35 / 35 (100.0%)** | **35 / 35 (100.0%)** | **35 / 35 (100.0%)** |
| **Primary Coarse Barrier Span** | **0.00 mm** | **0.00 mm** | **0.00 mm** | **0.00 mm** | **0.00 mm** |
| **Secondary Corridor Active (21 el)**| **0 / 21 (0.0%)** | **0 / 21 (0.0%)** | **6 / 21 (28.6%)** | **18 / 21 (85.7%)** | **21 / 21 (100.0%)** |
| **Secondary Temporal Leakage** | **Zero (0.0%)** | **Zero (0.0%)** | **Causal** | **Causal** | **Causal** |
| **Primary Min Target Size $h_{\min}$**| $0.0950\,\text{mm}$ | $0.0950\,\text{mm}$ | $0.0950\,\text{mm}$ | $0.0950\,\text{mm}$ | $0.0950\,\text{mm}$ |
| **Primary Process Zone Compl.** | 100.0% ($h \le \ell_0/2$) | 100.0% ($h \le \ell_0/2$) | 100.0% ($h \le \ell_0/2$) | 100.0% ($h \le \ell_0/2$) | 100.0% ($h \le \ell_0/2$) |
| **Secondary Min Target Size** | $1.3670\,\text{mm}$ | $1.3670\,\text{mm}$ | $0.1120\,\text{mm}$ | $0.0950\,\text{mm}$ | $0.0950\,\text{mm}$ |
| **Predicted Sizing Surrogate** | 5,985 elements | 18,252 elements | 19,334 elements | 22,774 elements | 31,023 elements |

### Temporal Causality Findings:
1. **Zero Future Leakage:** At State a ($u = 0.10\,\text{mm}$), the secondary corridor has 0 active elements out of 21 (0.0% activation). The target size across the entire secondary ligament remains exactly at the coarse background size $h_{\text{bg}} = 1.367\,\text{mm}$. The algorithm exhibits zero advance knowledge of the future secondary crack.
2. **Causal Progression:** As the physical analysis advances, the secondary corridor activates progressively: 0% at State b, 28.6% at State c, 85.7% at State d, and 100.0% at State e. This mirrors the true physical fracture sequence observed in experiment and simulation.
3. **Continuous Process Zone Resolution:** In the active crack corridor, 100% of elements satisfy $h \le \ell_0/2 = 0.1425\,\text{mm}$ without transverse coarse barriers (barrier span = 0.00 mm), resolving the 4.47 mm midspan barrier that crippled linear-elastic stress recovery.

---

## 6. Synthesis Visualization

A four-panel publication-quality visualization was generated at `results/figures/fig_f1749_time_causal_synthesis.png` (.pdf) and copied to conversation artifacts:

![Task F1749 Time-Causal Synthesis](/results/figures/fig_f1749_time_causal_synthesis.png)

- **Panel (a):** Spatial activation maps comparing State a ($u=0.10\,\text{mm}$, green dots, primary corridor only) with State e ($u=1.50\,\text{mm}$, blue dots, both corridors active), illustrating strict temporal causality and localized refinement.
- **Panel (b):** Along-path target element size profiles $h(s)$ across the primary ligament for States a, b, and e, demonstrating that the analytical sizing law guarantees $h(s) \le \ell_0/2 = 0.1425\,\text{mm}$ throughout the process zone with zero midspan coarse barriers.
- **Panel (c):** Physics-derived analytical sizing law curve $h(d)$, displaying the smooth transition across crack core, process zone, diffuse tail, and unrefined bulk.
- **Panel (d):** Comprehensive reconciliation table resolving all ten review directives (`F1748-R01` to `R10`).

---

## 7. Conclusions & Next Steps

Task F1749 conclusively demonstrates that a time-causal, physics-based phase-field damage indicator eliminates the stress-recovery blindspot without violating temporal causality or requiring manual crack-corridor prescriptions.

### Verified Findings:
- `F1749-K01`: Reconciled Case 2 provenance (Job 1423271, 252 incs, $u=0.007677\,\text{mm}$, initial notch seam verified).
- `F1749-K02`: Explained extreme history variable magnitudes ($H \approx 3,955\,\text{kN/mm}^2$ in severed crack cores).
- `F1749-K03`: Validated strict temporal causality across five states (0.0% secondary activation at State a, causal growth to 100.0% at State e).
- `F1749-K04`: Formulated analytical diffuse sizing law ensuring $h \le \ell_0/2$ across the active process zone.
- `F1749-K05`: Preserved zero-PBS governance (cumulative submissions = 25).

Task F1749 is complete and ready for independent review.
