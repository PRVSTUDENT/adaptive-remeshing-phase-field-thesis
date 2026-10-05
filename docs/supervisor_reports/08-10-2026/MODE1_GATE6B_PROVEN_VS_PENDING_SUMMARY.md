# Mode-I Gate-6B Executive Summary: Proven Results vs. Pending Computations

**Target Review:** Supervisory Meeting — Thursday, 08 October 2026, 10:00 CEST  
**Authoritative Framework:** `MODE1_GATE6B_ACTIVE_EVALUATION_AND_CONTINUATION`  
**Governing Directive:** *"We need to have understood everything related to the first model before we increase complexity."*

---

## 1. What Is Already Proven & Numerically Qualified

| Domain / Milestone | Verified Finding | Quantitative / Epistemic Evidence |
| :--- | :--- | :--- |
| **1. Mechanical Defect Closure (Gate 6A)** | N_BOTTOM 16-entry card limit defect identified and resolved. Full fracture response verified. | Structural stiffness $K_0$ matches reference within $-0.09\%$ ($137.82\,\text{kN/mm}$ in Job `1404933`). |
| **2. 13,941 Reproduction Limitation (Gate 5)** | Supervisor accepted missing publication detail boundary. Sizing trends documented. | Closed with sensitivity trends ($1\% \to 71\text{k}, 2\% \to 15.4\text{k}, 3\% \to 7.6\text{k}, 5\% \to 4.2\text{k}$). |
| **3. UEL Energy Formulation & Output (Gate 6B)** | Term-by-term weak form derived; zero double-counting in 3-layer architecture; single-IP extraction rule established. | Verified in `docs/methods/UEL_ENERGY_FORMULATION_AND_BALANCE_AUDIT.md`. |
| **4. Mechanical Parity of Energy Instrumentation** | Energy output instrumentation in `f42_mixed_uel.for` (`CE8D5EDC...`) is mechanically non-invasive. | Exact bitwise match in $K_0$ ($0.000\%$) and $F_{\max}$ ($0.000\%$) across 7,000 increments in Job `1409734`. |
| **5. Global Energy Conservation** | Energy balance $\Delta_{\text{book}} = \mathcal{W}_{\text{ext}} - (\mathcal{E}_{\text{elas}} + \mathcal{E}_{\text{frac}})$ conserved within tight bounds. | Fixed Reference: $\varepsilon_{\text{book}} = 0.76\%$; Adaptive Baseline (14k FE): $\varepsilon_{\text{book}} = 1.10\%$. |
| **6. Temporal Convergence (Pre-Peak)** | Time-step refinement ($1.00\,\text{nm} \to 0.50\,\text{nm}$) demonstrates strict invariance through peak. | $\Delta K_0 = +0.000302\%$, $\Delta F_{\max} = -0.0229\%$, $\Delta \mathcal{E}_{\text{model}}(u_{\text{peak}}) = 0.000000\%$ (Jobs `1409982` vs `1410027`). |
| **7. Post-Peak Temporal Sensitivity Mechanism** | Cutback exhaustion at $u = 7.47\,\mu\text{m}$ in $2\times$ refined run caused by severed-wake tolerance check ($c_{\max} \le C_n \Delta u_{\text{inc}}$). | Analytical tangent Jacobian symmetry verified to machine precision ($\max |\Delta| = 1.36\times 10^{-14}$). |
| **8. Baseline Spatial & Crack-Path Convergence** | Fixed reference ($S_1$, 15k) and Adaptive baseline (ET1, 14k) exhibit matching crack kinematics and symmetry. | Centroid deviation $|y_c - 0.5| < 0.5\,\mu\text{m}$; localization width $w_{0.5} \approx 20.8\,\mu\text{m} \approx 2.77\,l_0$. |
| **9. Clean Single-Variable $l_0$ Sensitivity** | 100% bitwise mesh twins on $S_3$ across $l_0 \in \{7.5, 11.25, 15.0\}\,\mu\text{m}$ establish physical scaling. | $K_0$ invariant ($0.13\%$ spread); $w_{0.5} \approx 3.04\,l_0$ linear scaling; $F_{\max}$ drops $-5.83\%$ (Jobs `1406017`, `1406895`, `1406896`). |
| **10. Length-Scale Resolution Adequacy** | All 6 governed meshes resolve the diffuse damage zone adequately ($h_{\text{corridor},\min} / l_0 \le 0.18 \ll 0.50$). | Adequacy supported across all fixed and adaptive discretizations (`MODE1_GOVERNED_MESHES_LENGTH_SCALE_ADEQUACY.json`). |
| **11. ErrorTarget Energy Reconciliation (ET3 & ET5)** | Jobs `1410358` (5,189 FE) and `1410359` (4,692 FE) completed exit 0 with 0 cutbacks. Pre-peak and peak energy conserved to $< 0.01\%$; post-peak $\varepsilon_{\text{book}} \approx 11\text{--}12\%$ reconciled as physical/numerical broadening ($h_{\mathrm{med}}/l_0 \ge 0.41$). | $K_0$ within $+0.046\%$, $F_{\max}$ within $+1.01\%$, full softening traversed to $u = 0.010\,\text{mm}$ (`ERRORTARGET_RESPONSE_STABLE`). |

---

## 2. What Remains Actively Solving & Pending Terminal Ingestion

| Active Job ID | Discretization / Model Purpose | PBS Status / Progress | Reconstructed $u_y$ | Primary Scientific Question Addressed |
| :--- | :--- | :---: | :---: | :--- |
| **`1410179.mmaster02`** | Spatial Fine Candidate ($57{,}929$ FE) | `R` (Step 1 Inc 1278) | $3.195\,\mu\text{m}$ | Does high-density spatial refinement ($h = 0.72\,\mu\text{m}$) confirm asymptotic force convergence? |
| **`1410180.mmaster02`** | $C_n = 0.50$ Convergence Diagnostic | `R` (Step 2 Inc 1608) | $6.595\,\mu\text{m}$ | Does tolerance relaxation enable post-peak softening traversal to $u = 10.0\,\mu\text{m}$ without cutbacks? |
| **`1410357.mmaster02`** | Adaptive ET2 ($6{,}112$ FE) | `R` (Step 2 Inc 1659) | $6.660\,\mu\text{m}$ | How does errorTarget coarsening ($2\%$) affect post-peak dissipation and residual stiffness? |

*All 3 active jobs are executing strictly under `/scratch9/pr21vyci/` with 0 cutbacks and 3 iterations/increment.*

---

## 3. Summary Blocker Status & Scope Holds

- **Gate 6B Closure Decision**: Awaiting terminal completion of the 3 active scratch solves (`1410179`, `1410180`, `1410357`). Automated evaluator scripts and multi-quantity synthesis schema (`MODE1_GATE6B_MULTIQUANTITY_SYNTHESIS_SCHEMA.json`) are certified and standing by.
- **Active Scope Holds**: Mode-II shear benchmarks, Gate 6C (State Transfer energy preservation), Gate 7 (Visualization integration), and multi-rank MPI remain **on strict hold** until Gate 6B is formally reviewed and closed.
