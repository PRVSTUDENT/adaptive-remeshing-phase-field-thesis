# Task F1728 Case 2 (Single Off-Axis Hole Plate) Companion Degraded Cauchy Stress Recovery Protocol

**Task ID:** `F1728-UNIFIED-METHOD-A-FIVE-GEOMETRIES`  
**Subtask ID:** `F1728-CASE2-EXECUTABLE_RECOVERY_DECK_OFFLINE_QUALIFICATION`  
**Classification:** `CASE2_EXECUTABLE_RECOVERY_DECK_OFFLINE_QUALIFIED`  
**Date:** 14 November 2026  
**Protocol Version:** 2  
**Agent:** `gemini-antigravity`  
**Review Correlation:** `HND-F1728-CASE2-STRESS-RECOVERY-002`  
**Predecessor Reviews:** `HND-F1728-CASE2-STRESS-RECOVERY-001` (REJECT - Hardening Required); `HND-F1728-CASE2-DONOR-QUAL-003` (APPROVED)  
**Governing Directives:**  
- **Zero Forward Fracture Rule:** Strictly NO forward phase-field fracture simulations on adapted meshes.  
- **Zero New PBS Submissions:** `max_new_pbs_submissions = 0`. Bounded offline generator authoring and static deck validation.  
- **No Local Abaqus Solver Executions:** All solver operations execute exclusively on the HPC cluster.  
- **Bitwise Frozen UEL:** Subroutine `f42_mixed_uel.for` (`CE8D5EDC...`) remains unaltered.

---

## 1. Objective and Problem Statement

### 1.1 The Zero-Stress Defect in Candidate Donor 2
In Task F1728 Case 2 (Single Off-Axis Hole Plate, $1.0 \times 1.0\,\text{mm}$, initial notch $a_0 = 0.50\,\text{mm}$, circular void at $(0.65, 0.65)\,\text{mm}$, $R = 0.10\,\text{mm}$, $\ell_0 = 0.0075\,\text{mm}$), independent review `HND-F1728-CASE2-DONOR-QUAL-003` approved the technical qualification of candidate donors:
1. **Candidate Donor 1 (`PK_HOLE_METHOD_A_PREANALYSIS.odb`):** Linear-elastic pre-analysis ($u_y = 0.0050\,\text{mm}$) possesses a genuine native `MISESERI` field peaking at $1,430.27\,\text{MPa}$ at the notch root. However, mutually exclusive disjoint spatial segmentation proved that the uncracked ligament error ($118.79\,\text{MPa}$) is more than $3\times$ lower than the notch root core ($385.55\,\text{MPa}$), starving the uncracked ligament during native remeshing.
2. **Candidate Donor 2 (`PK_HOLE_COARSE_JOB1.odb`):** Authentic coarse phase-field simulation ($518.2\,\text{MB}$, SHA-256 `834b9bb0...`, 389 frames) provides the authentic physical crack trajectory. At Step-2 Peak (Frame 167, $t = 0.3277$, $u_y = 0.00729381\,\text{mm}$, $F_{\max} = 0.731015\,\text{kN}$), damage localization reaches $d_{\max} = 0.5798$, with 48 softening elements ($d \ge 0.10$) forming 3 edge-connected components. The primary component (37 elements) extends across the oblique ligament and establishes physical polygon contact with the circular hole perimeter across 6 elements (`[151, 152, 153, 687, 734, 1088]`, polygon clearance $0.0\,\mu\text{m}$, nearest centroid clearance $7.693\,\mu\text{m}$ at Element 734).

**The Defect:** In `PK_HOLE_COARSE_JOB1.odb`, the 3-layer UEL model utilized `f42_mixed_uel.for`, where the Layer 3 visualizer UMAT explicitly sets:
```fortran
      DO I=1, NTENS
        STRESS(I) = 0.D0
        DO J=1, NTENS
          DDSDDE(I,J) = 0.D0
        ENDDO
        DDSDDE(I,I) = 1.D-11
      ENDDO
```
Consequently, Cauchy stress $\mathbf{S}$ and native `MISESERI` error indicators are identically zero across all 389 increments. `PK_HOLE_COARSE_JOB1.odb` alone **cannot** directly drive native Abaqus `RemeshingRule` sizing under `UNIFORM_ERROR`.

### 1.2 Purpose and Classification of Companion Stress Recovery
This protocol defines the exact mathematical, topological, and computational procedure to recover an authentic, non-zero degraded Cauchy stress field $\boldsymbol{\sigma}_h$ on the coarse mesh from the Step-2 Peak damage state of `PK_HOLE_COARSE_JOB1.odb`. The resulting companion recovery database natively supplies Abaqus Superconvergent Patch Recovery (SPR) with the inter-element stress jumps needed to compute `MISESERI` and `MISESAVG`, driving native adaptive remeshing across the oblique fracture corridor.

**Surrogate Classification (Resolving Finding F1728-R25):**  
An empirical extraction performed on the HPC cluster using Abaqus Python (`scripts/remeshing/extract_case2_nodal_u.py`) demonstrated that `PK_HOLE_COARSE_JOB1.odb` wrote field output `U` **only** for node 999999 (Reference Point, $u_y = 0.00729381\,\text{mm}$), due to the coarse deck card `*NODE OUTPUT, NSET=N_RP`. Physical nodes 1..3010 have no recorded displacement in the coarse ODB.  
Therefore, the companion recovery solve is **explicitly and transparently classified as a re-equilibrated surrogate continuum solve** with spatially heterogeneous degraded stiffness under the prescribed boundary kinematics ($u_y = 0.00729381\,\text{mm}$ at $y=1.0\,\text{mm}$, fixed $y=0.0\,\text{mm}$, pinned corner), rather than a prescribed nodal kinematics interpolation.

---

## 2. Lineage, Data Sources, and Provenance

The companion stress recovery workflow depends strictly on verified, immutable project assets:

| Asset Name | Repository Path | Size / Details | SHA-256 / Hash Provenance |
| :--- | :--- | :--- | :--- |
| **Coarse Physical Mesh** | `models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_COARSE_PHYS.inp` | 2,906 elements (2,832 quads, 74 tris), 3,010 nodes | Bitwise verified (Finding F1728-R27 reconciled) |
| **Authentic Coarse ODB** | `/scratch9/pr21vyci/runs/mode1_method_a_hole_coarse/PK_HOLE_COARSE_JOB1.odb` | 518,169,932 bytes, 389 frames | `834b9bb035fcf7b25dbb0deb7f8c344d7a9783dcfaa6d92a0c986affb689ad4c` |
| **Extracted Coarse Fields** | `results/validation/f1728_case2_coarse_job1_fields.json` | 763,246 bytes (all 2,906 elements at 3 checkpoints) | `6427CEF0E84DE87A63A2F370A8D0D0B93C1E704CA0840DD805B248FF022509C9` |
| **Damage Connectivity Graph** | `results/validation/f1728_case2_damage_connectivity.json` | 48 elements, 3 components, 6 boundary-touching elements | Verified in Round 3 review |
| **Frozen UEL Subroutine** | `models/pandey_kumar_mode1/219_f1728_five_geometry_study/f42_mixed_uel.for` | 38,455 bytes (Frozen Mode-I UEL) | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` |
| **Executable Recovery Deck** | `models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_COMPANION_RECOVERY.inp` | 2,906 elements, 3,010 nodes, 13 populated bins | Generated deterministically offline |
| **Deck Audit Receipt** | `results/validation/f1728_case2_recovery_deck_audit.json` | Static audit of nodes, elements, BCs, outputs | Verified `RECOVERY_STEP`, 100% disjoint |
| **Quantization Audit** | `results/validation/f1728_case2_quantization_error.json` | Evaluation of 20-bin vs anchored vs 100-bin | Reconciled with Finding F1728-R26 |

---

## 3. Mathematical Formulation and Quantization Error Analysis

### 3.1 Degraded Cauchy Stress State
In the standard phase-field fracture formulation for brittle solids, the Cauchy stress tensor in the softening regime is degraded by the energetic degradation function $g(d)$:
$$\boldsymbol{\sigma} = g(d) \boldsymbol{\sigma}_0 = \left[ (1 - d)^2 + k_{\text{res}} \right] \mathbf{C}_0 : \boldsymbol{\varepsilon}$$
where:
- $\mathbf{C}_0$ is the fourth-order isotropic linear elasticity tensor:
  $$C_{ijkl} = \frac{E_0 \nu}{(1+\nu)(1-2\nu)} \delta_{ij} \delta_{kl} + \frac{E_0}{2(1+\nu)} (\delta_{ik} \delta_{jl} + \delta_{il} \delta_{jk})$$
- $E_0 = 210\,\text{GPa} = 210,000\,\text{MPa}$ ($210.0\,\text{kN/mm}^2$)
- $\nu = 0.30$ (plane strain conditions: `CPE4` and `CPE3` elements)
- $k_{\text{res}} = 1.0 \times 10^{-7}$ (numerical residual stiffness parameter preventing ill-conditioning in fully broken regions)
- $d(\mathbf{x}) \in [0, 1]$ is the scalar phase-field damage variable evaluated at Step-2 Peak ($u_y = 0.00729381\,\text{mm}$)

### 3.2 Quantization Error Evaluation and Intact-Anchored Scheme (Resolving Finding F1728-R26)
In `HND-F1728-CASE2-STRESS-RECOVERY-001`, the reviewer established that a naive 20-bin partitioning based on $g(d)$ introduces significant discretization bias:
- **Naive 20-Bin Partitioning:** Bins elements by floor index $b = \lfloor 20 \cdot g(d) \rfloor$ and assigns midpoint representative values $g_b = (b + 0.5)/20$. Undamaged elements ($d = 0$, $g = 1.0$) fall into bin 19 and receive $g_{19} = 19.5/20 = 0.975$, imposing a **systematic 2.5% stiffness reduction across the entire elastic far field**. This yields a mean relative error of $1.7659\%$ (maximum $5.8855\%$), with $81.0\%$ of elements (2,354 of 2,906) exceeding $1.0\%$ relative error.
- **Intact-Anchored 20-Bin Formulation (Adopted):**  
  To eliminate artificial far-field compliance while preserving compatibility with standard Abaqus CAE section limits, the intact-anchored scheme assigns:
  $$g_{\text{eff}}(d_i) = \begin{cases} 1.0 & \text{if } d_i < 0.01 \\ \max\left(\frac{\lfloor 20 \cdot g(d_i) \rfloor + 0.5}{20}, k_{\text{res}}\right) & \text{if } d_i \ge 0.01 \end{cases}$$
  This anchors 2,858 undamaged bulk elements to exact $E_0$ ($0.0\%$ error), confining the binning discretization strictly to the 48 actively softening elements. The global mean relative error drops to **$0.8565\%$**, and the bulk elastic field is preserved without artificial compliance distortion.
- **Higher-Fidelity Options Available:**  
  The generator script (`scripts/remeshing/generate_case2_companion_recovery_deck.py`) also supports:
  - `HIGH_FIDELITY_100_BIN`: Mean relative error $0.2485\%$, max $1.0005\%$.
  - `EXACT_ELEMENTWISE`: Exact $g(d_i) = (1-d_i)^2 + k_{\text{res}}$ assigned to each element across 2,623 unique materials ($0.0000\%$ relative error).

### 3.3 Variable Definition and Scale Invariance Realism (Resolving Finding F1728-R28)
- **`MISESAVG` Definition:** In Abaqus, `MISESAVG` is an **element-average equivalent stress output variable** (`WHOLE_ELEMENT` scalar representing the average equivalent von Mises stress over the integration points of each element), not a domain-average scalar.
- **Physical Scale vs. Theoretical Invariance:**  
  While mathematical scale invariance proves that the ratio $\eta_e = \text{MISESERI}_e / \text{MISESAVG}_e$ is invariant to uniform scalar modulus scaling under identical kinematic boundary conditions, numerical implementations with small scaling factors ($s \sim 10^{-14}$) risk truncation and solver cutback sensitivity. Therefore:
  - **The primary, authoritative implementation uses physical scale ($E_0 = 210\,\text{GPa} = 210,000\,\text{MPa}$)**.
  - The resulting stresses, forces, and error indicators reflect genuine physical values ($\mathrm{MPa}$).
  - Dummy overlay scaling is retained only as an analytical reference explaining historical 10^-12 ~ 10^-19 magnitudes in published literature.

---

## 4. Implementation Protocol and Executable Deck Architecture (Resolving Findings F1728-R27 & F1728-R30)

### 4.1 Reconciled Mesh Inventory (Finding F1728-R27)
A rigorous topological audit of `models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_COARSE_PHYS.inp` established the exact element inventory:
- **Nodes:** Exactly 3,010 nodes.
- **Quadrilateral Elements (`CPE4`):** Exactly 2,832 elements (Elements 1 to 2832).
- **Triangular Elements (`CPE3`):** Exactly 74 elements (Elements 2833 to 2906).
- **Total Physical Elements:** Exactly 2,906 elements.
*(Historical mention of 2,818 quads and 88 triangles belonged to the pre-analysis donor mesh, whereas the physical coarse mesh possesses 2,832 quads and 74 triangles).*

### 4.2 Executable Deck Structure (`PK_HOLE_COMPANION_RECOVERY.inp`)
The companion recovery deck is deterministically generated by `scripts/remeshing/generate_case2_companion_recovery_deck.py`:
1. **Nodes & Connectivity:** 3,010 nodes, 2,832 `CPE4` quads, 74 `CPE3` tris imported directly from `PK_HOLE_COARSE_PHYS.inp`.
2. **Element Sets:**
   - `QUADS`: Elements 1..2832
   - `TRIS`: Elements 2833..2906
   - `All_elem`: Elements 1..2906 (combination of `QUADS` and `TRIS`)
   - `umatelem`: Alias for `All_elem`
3. **Disjoint Material Sections:**
   Populates 13 active material bins (`ELSET_BIN_0` through `ELSET_BIN_19`), covering 100% of the 2,906 elements with zero overlapping or unassigned elements:
   - `ELSET_BIN_19` (Intact bulk, $E = 210,000\,\text{MPa}$): 2,858 elements.
   - Softening bins (`ELSET_BIN_0` to `ELSET_BIN_18`): 48 elements.
4. **Step Name & Boundary Conditions (Finding F1728-R30):**
   ```abaqus
   *STEP, NAME=RECOVERY_STEP, NLGEOM=NO
   *STATIC
   1.0, 1.0, 1.0, 1.0
   *BOUNDARY
   N_BOTTOM, 2, 2, 0.0
   N_PIN, 1, 1, 0.0
   N_TOP, 2, 2, 0.007293812465
   *OUTPUT, FIELD
   *ELEMENT OUTPUT, ELSET=All_elem, DIRECTION=YES
   MISESERI, MISESAVG, S, EVOL
   *NODE OUTPUT
   U, RF
   *END STEP
   ```

### 4.3 Engine Step & Region Alignment Safeguards (Finding F1728-R30)
In `scripts/remeshing/reusable_2d_adaptive_framework.py` (lines 1297–1325), the remeshing engine was hardened with fail-closed alignment checks:
1. If `step_target` (e.g. `RECOVERY_STEP`) does not exist in the CAE model `m`, it is created dynamically as a Static Linear Perturbation step.
2. An explicit assertion confirms that `step_target` exists in both `odb_donor.steps` and `m.steps`.
3. An explicit assertion confirms that `All_elem` exists on the part instance before `adaptiveRemesh()` is invoked.

---

## 5. Comparative Evaluation: Pure Continuum vs. Companion Phase-Field Recovery

| Metric / Attribute | Candidate Donor 1 (Linear-Elastic Pre-Analysis) | Proposed Companion Recovery (Step-2 Peak Phase-Field) |
| :--- | :--- | :--- |
| **Physical Source State** | Intact linear elasticity ($u_y = 0.0050\,\text{mm}$, $d \equiv 0$) | Authentic coarse phase-field softening ($u_y = 0.00729\,\text{mm}$, $d_{\max} = 0.5798$) |
| **Error Indicator Source** | Native `MISESERI` in `PK_HOLE_METHOD_A_PREANALYSIS.odb` | Recovered `MISESERI` via companion degraded solve |
| **Singular Notch Root Error** | Concentrates strictly at root ($385.55\,\text{MPa}$ core, $1,430.27\,\text{MPa}$ peak) | Captures softened notch root and relief ($d = 0.5798$) |
| **Oblique Ligament Error** | Starved ($118.79\,\text{MPa}$, only $7.90\times$ bulk, $3.2\times$ lower than tip) | Concentrated stress jumps across the 37-element primary damage component |
| **Hole Flank Boundary Error** | $162.63\,\text{MPa}$ ($10.81\times$ bulk) | Concentrates at physical contact nodes (`[6, 7, 636, 637, 638, 639]`) |
| **Expected Adaptive Refinement** | Refines notch tip ($h \le \ell_0/2$) but leaves ligament coarse ($h > \ell_0/2$) | Drives continuous refinement ($h \le \ell_0/2$) along the entire oblique path into the hole |

---

## 6. Calibrated Verification and Acceptance Criteria (Resolving Finding F1728-R29)

To ensure scientifically defensible qualification without imposing unphysical strict-positivity or predetermined peak element constraints, acceptance criteria are calibrated as follows:

1. **Gate REC-01 (Solvability & Exit Code):** `PK_HOLE_COMPANION_RECOVERY.inp` must complete Abaqus/Standard solve with Exit Code 0 in 1 increment with 0 cutbacks.
2. **Gate REC-02 (Valid Field Generation & Non-Degeneracy):** The recovered ODB must provide valid, readable `MISESERI`, `MISESAVG`, and `S` field outputs for all 2,906 elements. No `NaN`, infinite, or undefined values are permitted.
3. **Gate REC-03 (Spatial Contrast & Ligament Polarization):** The mean `MISESERI` across the 37-element primary damage corridor ($y \in [0.48, 0.68]\,\text{mm}$, $x \in [0.50, 0.65]\,\text{mm}$) must achieve at least **$5.0\times$ contrast** relative to the far-field bulk mean ($x > 0.80\,\text{mm}$), verifying that error polarization successfully shifts into the softening ligament.
4. **Gate REC-04 (Static Equilibrium & Reaction Force Check):** Total vertical reaction force $\sum RF_y$ on `N_BOTTOM` must balance $RF_y$ on `N_TOP` to within $|\Delta RF / RF| \le 1.0 \times 10^{-4}$, confirming numerical equilibrium of the surrogate continuum solve.
5. **Gate REC-05 (Zero Forward Fracture Enforcement):** Under NO circumstances shall forward phase-field fracture propagation be executed on adapted meshes during this task.

---

## 7. Execution Accounting and Governance Boundary

- **Submissions Consumed for Protocol Definition:** `0` (`max_new_pbs_submissions = 0`, `submissions_consumed = 0`).
- **Cumulative Project Submissions:** Permanently reconciled at `5` in all ledgers (`1423095`, `1423101`, `1423102`, `1423103`, `1423169`).
- **Execution Location:** If a companion recovery job is staged, it MUST execute exclusively on the HPC cluster compute nodes via guarded PBS submission (`Invoke-GuardedSsh.ps1`), with zero local Abaqus solver execution on the Windows PC.
