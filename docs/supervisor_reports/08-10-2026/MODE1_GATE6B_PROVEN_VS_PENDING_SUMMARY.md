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
| **3. UEL Energy Formulation & Output (Gate 6B)** | Term-by-term weak form derived; zero double-counting in 3-layer architecture; single-IP extraction rule established. Status: `UEL_ENERGY_OUTPUT_QUALIFIED_MECHANICALLY_NONINVASIVE`. | Verified in `docs/methods/UEL_ENERGY_FORMULATION_AND_BALANCE_AUDIT.md`. |
| **4. Mechanical Parity of Energy Instrumentation** | Energy output instrumentation in `f42_mixed_uel.for` (`CE8D5EDC...`) is mechanically non-invasive. | Exact bitwise match in $K_0$ ($0.000\%$) and $F_{\max}$ ($0.000\%$) across 7,000 increments in Job `1409734`. |
| **5. Global Energy Conservation** | Energy balance $\Delta_{\text{book}} = \mathcal{W}_{\text{ext}} - (\mathcal{E}_{\text{elas}} + \mathcal{E}_{\text{frac}})$ conserved within tight bounds. | Fixed Reference: $\varepsilon_{\text{book}} = 0.76\%$; Adaptive Baseline (14k FE): $\varepsilon_{\text{book}} = 1.10\%$. |
| **6. Temporal Convergence (Pre-Peak)** | Time-step refinement ($1.00\,\text{nm} \to 0.50\,\text{nm}$) demonstrates strict invariance through peak. | $\Delta K_0 = +0.000302\%$, $\Delta F_{\max} = -0.0229\%$, $\Delta \mathcal{E}_{\text{model}}(u_{\text{peak}}) = 0.000000\%$ (Jobs `1409982` vs `1410027`). |
| **7. Post-Peak Temporal Sensitivity Mechanism** | Cutback exhaustion at $u = 7.47\,\mu\text{m}$ in $2\times$ refined run caused by severed-wake tolerance check ($c_{\max} \le C_n \Delta u_{\text{inc}}$). | Analytical tangent Jacobian symmetry verified to machine precision ($\max |\Delta| = 1.36\times 10^{-14}$). |
| **8. Baseline Spatial & Crack-Path Convergence** | Fixed reference ($S_1$, 15k) and Adaptive baseline (ET1, 14k) exhibit matching crack kinematics and symmetry. | Centroid deviation $|y_c - 0.5| < 0.5\,\mu\text{m}$; localization width $w_{0.5} \approx 20.8\,\mu\text{m} \approx 2.77\,l_0$. |
| **9. Clean Single-Variable $l_0$ Sensitivity** | 100% bitwise mesh twins on $S_3$ across $l_0 \in \{7.5, 11.25, 15.0\}\,\mu\text{m}$ establish physical scaling. | $K_0$ invariant ($0.13\%$ spread); $w_{0.5} \approx 3.04\,l_0$ linear scaling; $F_{\max}$ drops $-5.83\%$ (Jobs `1406017`, `1406895`, `1406896`). |
| **10. Length-Scale Resolution Adequacy** | All 6 governed meshes resolve the diffuse damage zone adequately ($h_{\text{corridor},\min} / l_0 \le 0.18 \ll 0.50$). | Adequacy supported across all fixed and adaptive discretizations (`MODE1_GOVERNED_MESHES_LENGTH_SCALE_ADEQUACY.json`). |
| **11. ErrorTarget Energy Reconciliation (ET2, ET3 & ET5)** | Jobs `1410357` (6,112 FE), `1410358` (5,189 FE) and `1410359` (4,692 FE) completed Exit 0 with 0 cutbacks. Pre-peak bookkeeping discrepancy is strictly $< 0.010\%$ across all tested meshes, demonstrating excellent pre-peak bookkeeping consistency without evidence of implementation defect (not global mathematical proof of exactness); post-peak energetic response ($\varepsilon_{\text{book}} \approx 8.6\%\text{--}12.1\%$) scales monotonically with corridor coarsening and damage-band broadening ($w_{0.5} \approx 52\,\mu\text{m}$), with mechanistic explanation held as provisional pending 58k (`1410179` / `1410504`) completion. | $K_0$ within $+0.046\%$, $F_{\max}$ within $+1.01\%$, full softening traversed to $u = 0.010\,\text{mm}$ (`MECHANICAL_RESPONSE_STABLE`, `POSTPEAK_ENERGETIC_RESPONSE_MESH_SENSITIVE`). |
| **12. Convergence-Control Diagnostic ($C_n = 0.50$)** | Job `1410180` (14,483 FE) completed all 7,014 increments with 0 cutbacks to $u = 0.010\,\text{mm}$ ($99.84\%$ load drop), verifying that canonical ET1 termination was sensitive to the severed-wake displacement correction normalization check (`POST_FRACTURE_CONVERGENCE_NORMALIZATION_SENSITIVITY_VERIFIED`). Broader constitutive breakdown or physical non-convergence is not disproven, and `POST_FRACTURE_ILL_CONDITIONING` remains `NOT_ESTABLISHED`. | Identical elastic and peak metrics to canonical ET1; $\varepsilon_{\text{book}} = 0.8207\%$ across full trajectory. Classified strictly as an algorithmic convergence-control diagnostic, not a temporal convergence proof. |
| **13. Shared-Memory 8-Thread Parallelism (Gate 6B)** | 8-thread shared-memory SMP execution empirically qualified for the tested Mode-I formulation/controls ($S_8 = 3.62\times$, 100% bitwise parity across 4,890 increments); 16-thread execution remains unqualified pending independent Stage-A and Stage-B verification; distributed multi-rank MPI strictly disqualified due to replicated mutable `COMMON` state. | Qualified in `docs/methods/MODE1_SHARED_MEMORY_8THREAD_PARITY_AND_SCALING_AUDIT.md` and enforced via `tests/unit/test_mode1_shared_memory_8thread_template_and_guards.py`. |

---

## 2. What Remains Actively Solving & Pending Terminal Ingestion

| Active Job ID | Discretization / Model Purpose | PBS Hardware Allocation | PBS Status / Progress | Reconstructed $u_y$ | Primary Scientific Role in Gate 6B |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **`1410179.mmaster02`** | Spatial Fine Candidate ($57{,}929$ FE, serial) | `nodes=1:ppn=1`, `mem=16gb`, `walltime=24:00:00` | `RUNNING` (Step 2 Inc $>1884$) | $u_y \approx 6.87\,\mu\text{m}$ | **Partial Softening Diagnostic**: Retained untouched to harvest valuable post-peak softening data until PBS 24h walltime termination. |
| **`1410504.mmaster02`** | Spatial Fine Candidate ($57{,}929$ FE, 8T SMP) | `nodes=1:ppn=8`, `mem=16gb`, `walltime=48:00:00` | `RUNNING` (Step 1 Inc $>121$) | $u_y \approx 0.3025\,\mu\text{m}$ | **Authoritative Full-Horizon Candidate**: Complete solve through $u_y = 10.0\,\mu\text{m}$ ($0$ cutbacks, $\approx 558\,\text{incs/hr}$) required for final spatial qualification. |

*Both active jobs execute strictly under `/scratch9/pr21vyci/` with zero home filesystem footprint on compute node `mnode097`.*

---

## 3. Summary Blocker Status & Scope Holds

- **Gate 6B Closure Decision**: Awaiting terminal completion of the active spatial fine scratch solves (serial diagnostic Job `1410179` and authoritative 8-thread candidate Job `1410504`). Automated evaluator scripts and multi-quantity synthesis schema (`MODE1_GATE6B_MULTIQUANTITY_SYNTHESIS_SCHEMA.json` v2.3.0) are certified and standing by.
- **Active Scope Holds**: Mode-II shear benchmarks, Gate 6C (State Transfer energy preservation; strictly on hold until Gate 6B closure, no auto-promotion), Gate 7 (Visualization integration), and multi-rank MPI remain **on strict hold** until Gate 6B is formally reviewed and closed.
