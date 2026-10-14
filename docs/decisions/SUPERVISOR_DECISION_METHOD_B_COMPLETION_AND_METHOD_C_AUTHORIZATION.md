# Project Decision & Authorization Record: Method B Scientific Completion & Method C Authorization

**Protocol Version:** 2  
**Date:** 2026-10-14  
**Author:** Gemini Antigravity  
**Task ID:** `F1446-MODE1-METHOD-C-INITIATION-AND-TRANSFER-FRAMEWORK`  
**Classification:** `METHOD_B_SCIENTIFIC_OBJECTIVE_COMPLETED_WITH_PARTIAL_HORIZON_LIMITATION`  
**Governance Authority:** Explicit Human Directive (14 October 2026)  

---

## 1. Context & Master Directive Alignment

Supervisor Master Governing Directive:
> *"We need to have understood everything related to the first model before we increase complexity."*

In accordance with this directive, Mode-I phase-field fracture modeling has been investigated through three distinct remeshing architectures:
- **Method A (Fixed-Mesh Reference):** Reconstructed $15{,}192$-element uniform/graded reference model establishing the canonical baseline anchor ($K_0 = 137.9455\,\text{kN/mm}$, $F_{\max} = 0.757778\,\text{kN}$, $u_{\text{peak}} = 0.005857\,\text{mm}$, $W_{\text{ext}} = 2.3587\,\text{mJ}$).
- **Method B (Offline Error-Guided Pre-Refinement):** A fixed non-uniform discretization generated before the fracture simulation using error indicator information from a coarse antecedent pre-analysis.
- **Method C (Sequential Adaptive Remeshing with Nonmatching State Transfer):** Chained simulation stages with intermediate remeshing and state transfer across nonmatching meshes.

---

## 2. Confirmation and Formal Freeze of Method B

### A. Evaluated Scientific Achievements (Task F1442–F1445)
1. **Elimination of Artificial Force Plateau:**
   - In Original Method B ($14{,}677$ elements), coarse ligament elements ($h > 14\,\mu\text{m}$) caused artificial crack pinning, producing an unphysical force plateau of $F \approx 0.50-0.60\,\text{kN}$ across $u_y \in [0.0060, 0.0085]\,\text{mm}$ and an inflated external work of $W_{\text{ext}} = 3.332\,\text{mJ}$ ($+41.2\%$ above reference).
   - In Corrected Method B ($14{,}483$ elements, Package 40, PBS Job `1412465.mmaster02`), extended corridor refinement ($h \le l_0/2 = 3.75\,\mu\text{m}$) completely eliminated the plateau. The reaction force drops monotonically past peak to $F < 0.0021\,\text{kN}$ at $u_y \ge 0.0060\,\text{mm}$ and $F = 0.00176\,\text{kN}$ ($1.76\,\text{N}$, $>99.76\%$ softened) at termination.
2. **Elastic & Initiation Accuracy:**
   - Linear elastic stiffness: $K_0 = 137.9096\,\text{kN/mm}$ ($-0.0261\%$ vs. canonical reference $137.9455\,\text{kN/mm}$, $R^2 = 0.99999960$).
   - Peak initiation force: $F_{\max} = 0.743701\,\text{kN}$ at $u_y = 0.005733\,\text{mm}$ ($-1.8577\%$ vs. reference, well within the $\pm 2.0\%$ thesis acceptance corridor).
3. **Dissipated Work Agreement:**
   - External work over the evaluated horizon dropped by $-31.5\%$ (from $3.332\,\text{mJ}$ to $2.2674\,\text{mJ}$), agreeing within $-3.87\%$ with the canonical reference ($2.3587\,\text{mJ}$).
4. **Global Energy Balance:**
   - Fracture energy accounts for $99.7\%$ of total work ($E_{\text{frac}} = 2.2855\,\text{mJ}$, $E_{\text{elas}} = 0.0070\,\text{mJ}$), yielding an energy residual of $\Delta E = 0.0250\,\text{mJ}$ ($1.10\%$ relative error).
5. **Topological Damage Contiguity:**
   - Dual-graph BFS proves that a single, contiguous connected component of elements with $d \ge 0.95$ extends from the notch tip (node 129) to the rightmost element layer ($x_{\text{centroid}} = 0.998982\,\text{mm}$), traversing $99.9\%$ of the specimen ligament with zero spatial disconnects.

### B. Documented Limitations & Epistemic Boundaries
Method B is frozen with the explicit classification:
`METHOD_B_SCIENTIFIC_OBJECTIVE_COMPLETED_WITH_PARTIAL_HORIZON_LIMITATION`

1. **Solver Termination Limitation:**
   - Job `1412465.mmaster02` completed 4,890 increments (Step 1: 2,000, Step 2: 2,890) and terminated with Abaqus Exit 1 due to minimum time-step cutback ($dt < dt_{\min}$) at $u_y = 0.007889\,\text{mm}$ in the deep post-fracture softening tail ($RF = 1.76\,\text{N}$). Full-horizon completion to $u_y = 0.0100\,\text{mm}$ was not demonstrated.
2. **Confounded Remeshing Parameters:**
   - Both the pre-analysis source step (Step 2 post-peak vs. Step 1 pre-peak) and the error target (`errorTarget = 1.0` vs. `2.0`) were altered simultaneously. While the resulting refined corridor ($h \le l_0/2$) successfully eliminated the pinning plateau, the isolated contribution of each variable remains unseparated.
3. **Offline Pre-Refinement Nature:**
   - Method B is an offline pre-refinement method, NOT an automated online adaptive remeshing scheme.

### C. Artifact Freeze
All Method B input decks, user subroutines, simulation evidence, and evaluation reports are frozen:
- Input deck: `models/pandey_kumar_mode1/40_method_b_corrected_propagation_14k/M1_MB_CORRECTED_PROPAGATION_14K.inp` (`1209F716...`)
- Subroutine: `models/pandey_kumar_mode1/40_method_b_corrected_propagation_14k/f42_mixed_uel.for` (`CE8D5EDC...`)
- PBS script: `models/pandey_kumar_mode1/40_method_b_corrected_propagation_14k/submit_M1_MB_CORRECTED_14K.pbs` (`06DE87F6...`)
- Evaluation report: `docs/reports/MODE1_CORRECTED_METHOD_B_STEP2_FRACTURE_EVALUATION.md`
- Status: **FROZEN — NO RE-RUNS OR ARBITRARY MODIFICATIONS PERMITTED**.

---

## 3. Human Authorization for Method C (14 October 2026)

### A. Authorization Terms
- **Human User Directive:** Given that Method B's principal fracture-response research objective is completed and its unphysical force plateau resolved, proceed immediately with Method C investigation. Do not wait unnecessarily for the 22 October 2026 supervisor meeting.
- **Independence from Supervisor Gate 6B Sign-Off:**
  - This human authorization is recorded **separately from formal supervisor Gate 6B sign-off**.
  - Formal supervisor review of Gate 6B remains scheduled for **Thursday, 22 October 2026, 10:00 CEST**.
  - In all thesis and project documentation, supervisor approval is NOT claimed or misrepresented; the current state is recorded as *Human Authorized Early Progression to Method C under Supervisor Scope Holds*.

### B. Governing Method C Scope Constraints
1. **Mode-I Benchmark Only:**
   - The investigation is strictly confined to the qualified Pandey-Kumar Mode-I benchmark ($\Omega = 1\,\text{mm} \times 1\,\text{mm}$, sharp slit along $y = 0.5\,\text{mm}$, $x \le 0.5\,\text{mm}$).
   - Zero Mode-II, zero mixed-mode, zero holes, and zero multi-crack models.
2. **Authoritative Subroutine Integrity:**
   - Subroutine source `f42_mixed_uel.for` remains frozen at SHA-256 `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`.
3. **No Retesting of Gate C1 V2 (Job 1412464):**
   - Job 1412464 is preserved as `QUASI_STATIC_RELOAD_WITH_TRANSFERRED_HISTORY` and will not be repeated.
4. **State-Transfer Accuracy Preceding HPC Execution:**
   - The first acceptance gate is mathematical state-transfer accuracy and energy conservation across nonmatching meshes, not merely launching cluster jobs.
