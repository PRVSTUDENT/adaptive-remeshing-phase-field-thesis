# Task F1728 Case 2 (Single Off-Axis Hole Plate) Companion Degraded Cauchy Stress Recovery Protocol

**Task ID:** `F1728-UNIFIED-METHOD-A-FIVE-GEOMETRIES`  
**Subtask ID:** `F1728-CASE2-COMPANION_STRESS_RECOVERY_OFFLINE_QUALIFICATION`  
**Classification:** `CASE2_COMPANION_STRESS_RECOVERY_PROTOCOL_QUALIFIED`  
**Date:** 13 November 2026  
**Protocol Version:** 1  
**Agent:** `gemini-antigravity`  
**Review Correlation:** `HND-F1728-CASE2-STRESS-RECOVERY-001`  
**Predecessor Review:** `HND-F1728-CASE2-DONOR-QUAL-003` (APPROVED)  
**Governing Directives:**  
- **Zero Forward Fracture Rule:** Strictly NO forward phase-field fracture simulations on adapted meshes.  
- **Zero New PBS Submissions:** `max_new_pbs_submissions = 0`. This document defines an offline, bounded specification.  
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

### 1.2 Purpose of Companion Stress Recovery
This protocol defines the exact mathematical, topological, and computational procedure to recover an authentic, non-zero degraded Cauchy stress field $\boldsymbol{\sigma}_h$ on the coarse mesh from the Step-2 Peak damage state of `PK_HOLE_COARSE_JOB1.odb`. The resulting companion recovery database will natively supply Abaqus Superconvergent Patch Recovery (SPR) with the inter-element stress jumps needed to compute `MISESERI` and `MISESAVG`, driving native adaptive remeshing across the oblique fracture corridor.

---

## 2. Lineage, Data Sources, and Provenance

The companion stress recovery workflow depends strictly on verified, immutable project assets:

| Asset Name | Repository Path | Size / Details | SHA-256 / Hash Provenance |
| :--- | :--- | :--- | :--- |
| **Coarse Physical Mesh** | `models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_COARSE_PHYS.inp` | 2,906 elements (2,818 quads, 88 tris), 3,010 nodes | Bitwise verified against cluster scratch |
| **Authentic Coarse ODB** | `/scratch9/pr21vyci/runs/mode1_method_a_hole_coarse/PK_HOLE_COARSE_JOB1.odb` | 518,169,932 bytes, 389 frames | `834b9bb035fcf7b25dbb0deb7f8c344d7a9783dcfaa6d92a0c986affb689ad4c` |
| **Extracted Coarse Fields** | `results/validation/f1728_case2_coarse_job1_fields.json` | 763,246 bytes (all 2,906 elements at 3 checkpoints) | `6427CEF0E84DE87A63A2F370A8D0D0B93C1E704CA0840DD805B248FF022509C9` |
| **Damage Connectivity Graph** | `results/validation/f1728_case2_damage_connectivity.json` | 48 elements, 3 components, 6 boundary-touching elements | Verified in Round 3 review |
| **Frozen UEL Subroutine** | `models/pandey_kumar_mode1/219_f1728_five_geometry_study/f42_mixed_uel.for` | 38,455 bytes (Frozen Mode-I UEL) | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` |

---

## 3. Mathematical and Constitutive Formulation

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

### 3.2 Piecewise Degradation Discretization (20-Bin Partitioning)
Following the validated Section 4.3 (Tasks F1697–F1703) and Section 4.5 (Tasks F1718–F1719) recovery architectures, the continuous degradation function $g(d) = (1-d)^2 + k_{\text{res}}$ across the 2,906 physical elements is partitioned into $N_{\text{bins}} = 20$ discrete material bins:
$$b_i = \min\left(19, \max\left(0, \left\lfloor 20 \cdot g(d_i) \right\rfloor\right)\right), \quad i \in \{1, \dots, 2906\}$$
For each bin $b \in \{0, \dots, 19\}$, the representative degradation factor is:
$$g_b = \frac{b + 0.5}{20.0}$$
The effective isotropic Young's modulus for element set `ELSET_BIN_b` is:
$$E_b = E_0 \cdot \max(g_b, k_{\text{res}})$$
All elements in `ELSET_BIN_b` share the baseline Poisson's ratio $\nu = 0.30$.

### 3.3 Proof of Scale Invariance for Relative Error Indicator $\eta_e$
To reproduce the numerical magnitude order of published Figure 25(a) ($\text{MISESERI} \sim 10^{-12}\,\text{MPa}$), a dummy modulus scaling factor $s = 4.7619 \times 10^{-14}$ ($E_{\text{dummy}} = 1.0 \times 10^{-11}\,\text{kN/mm}^2 = 1.0 \times 10^{-8}\,\text{MPa}$) may optionally be applied.

**Theorem (Modulus Scale Invariance):**  
Let $\boldsymbol{\sigma}^{(1)} = s_1 \mathbf{C} : \boldsymbol{\varepsilon}$ and $\boldsymbol{\sigma}^{(2)} = s_2 \mathbf{C} : \boldsymbol{\varepsilon}$ be two Cauchy stress fields evaluated on identical meshes under identical kinematic boundary conditions with scalar scale ratio $\alpha = s_2 / s_1$.  
1. Because the elasticity problem is linear, $\boldsymbol{\sigma}^{(2)}(\mathbf{x}) = \alpha \boldsymbol{\sigma}^{(1)}(\mathbf{x})$ pointwise.
2. The superconvergent patch recovery operator $\mathcal{P}$ is a linear projection on stress patches:
   $$\mathbf{s}_e^{(2)} = \mathcal{P}(\boldsymbol{\sigma}^{(2)}) - \boldsymbol{\sigma}^{(2)} = \alpha \left(\mathcal{P}(\boldsymbol{\sigma}^{(1)}) - \boldsymbol{\sigma}^{(1)}\right) = \alpha \mathbf{s}_e^{(1)}$$
3. The recovered von Mises error indicator scales linearly:
   $$\text{MISESERI}^{(2)} = \sqrt{\frac{3}{2} \mathbf{s}_e^{(2)} : \mathbf{s}_e^{(2)}} = \alpha \sqrt{\frac{3}{2} \mathbf{s}_e^{(1)} : \mathbf{s}_e^{(1)}} = \alpha \text{MISESERI}^{(1)}$$
4. The domain-average equivalent stress $\text{MISESAVG}$ scales linearly:
   $$\text{MISESAVG}^{(2)} = \frac{1}{V_{\Omega}} \int_{\Omega} \sigma_{\text{mises}}^{(2)} \, d\Omega = \alpha \text{MISESAVG}^{(1)}$$
5. The dimensionless relative error indicator $\eta_e$ is strictly invariant:
   $$\eta_e^{(2)} = \frac{\text{MISESERI}_e^{(2)}}{\text{MISESAVG}^{(2)}} = \frac{\alpha \text{MISESERI}_e^{(1)}}{\alpha \text{MISESAVG}^{(1)}} = \eta_e^{(1)}$$
Therefore, the element sizing distribution $h_e = h_0 (\eta_{\text{target}} / \eta_e)^{1/p}$ computed by Abaqus `RemeshingRule` is **mathematically identical** regardless of whether physical scale ($E_0 = 210\,\text{GPa}$) or dummy overlay scale ($E_{\text{dummy}} = 10^{-8}\,\text{MPa}$) is utilized.

---

## 4. Implementation Protocol and Model Assembly

### 4.1 Input Deck Structure (`PK_HOLE_COMPANION_RECOVERY.inp`)
The companion recovery deck is a single-step, linear-elastic continuum model (`CPE4` and `CPE3` elements) constructed as follows:

1. **Mesh Nodes:** Exact coordinates of all 3,010 nodes imported from `PK_HOLE_COARSE_PHYS.inp`.
2. **Element Definitions:** Exact element connectivities of all 2,818 quads (`CPE4`) and 88 triangles (`CPE3`), assigned to element sets `QUADS` and `TRIS`.
3. **Facsimile Element Sets:**
   ```abaqus
   *ELSET, ELSET=All_elem
   QUADS
   TRIS
   *ELSET, ELSET=umatelem
   All_elem
   ```
4. **Material Degradation Sections:** 20 distinct `*SOLID SECTION` and `*MATERIAL` definitions mapping `ELSET_BIN_0` through `ELSET_BIN_19` to degraded elastic moduli $E_b$.
5. **Boundary Conditions (Kinematic State Enforcement):**
   - Bottom boundary $y = 0.0\,\text{mm}$ (`N_BOTTOM`): $u_y = 0.0$
   - Pinned corner $(0.0, 0.0)\,\text{mm}$ (`N_PIN`): $u_x = 0.0$
   - Top boundary $y = 1.0\,\text{mm}$ (`N_TOP`): $u_y = 0.00729381\,\text{mm}$ (exact peak displacement from Frame 167)
6. **Analysis Step:**
   ```abaqus
   *STEP, NAME=RECOVERY_STEP, NLGEOM=NO
   *STATIC
   1.0, 1.0, 1.0, 1.0
   *BOUNDARY
   N_BOTTOM, 2, 2, 0.0
   N_PIN, 1, 1, 0.0
   N_TOP, 2, 2, 0.00729381
   *OUTPUT, FIELD
   *ELEMENT OUTPUT, ELSET=All_elem, DIRECTION=YES
   MISESERI, MISESAVG, S, EVOL
   *NODE OUTPUT
   U, RF
   *END STEP
   ```

### 4.2 Superconvergent Patch Recovery Execution
Solving `PK_HOLE_COMPANION_RECOVERY.inp` with Abaqus/Standard executes the Zienkiewicz–Zhu SPR algorithm on element set `All_elem`:
1. Stresses at integration points are sampled across polynomial element patches.
2. Higher-order continuous polynomial stress fields $\boldsymbol{\sigma}^*$ are fitted to patch sampling points.
3. Stress difference $\mathbf{s}_e = \boldsymbol{\sigma}^* - \boldsymbol{\sigma}_h$ is integrated across each element to yield $\text{MISESERI}_e$.
4. The resulting ODB contains non-zero `MISESERI` and `MISESAVG` fields reflecting the physical softening across the oblique ligament.

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

## 6. Verification and Acceptance Criteria

Before declaring the companion stress recovery protocol qualified for subsequent native remeshing, the following quantitative gates must be passed:

1. **Gate REC-01 (Solvability & Exit Code):** `PK_HOLE_COMPANION_RECOVERY.inp` must complete Abaqus/Standard solve with Exit Code 0 in 1 increment with 0 cutbacks.
2. **Gate REC-02 (Nonzero Field Availability):** 100% of the 2,906 physical elements must evaluate strictly positive, non-zero values for `MISESERI` and `MISESAVG`.
3. **Gate REC-03 (Spatial Concentration):** Peak `MISESERI` must localize within the 37-element primary damage corridor ($y \in [0.48, 0.68]\,\text{mm}$, $x \in [0.50, 0.65]\,\text{mm}$), verifying that error polarization shifts from the notch tip into the softening ligament.
4. **Gate REC-04 (Scale Invariance):** Relative error $\eta_e = \text{MISESERI}_e / \text{MISESAVG}_e$ must match between physical scale and dummy overlay scale to within $|\Delta \eta / \eta| \le 1.0 \times 10^{-4}\%$.
5. **Gate REC-05 (Zero Forward Fracture):** Under NO circumstances shall forward phase-field fracture propagation be executed on adapted meshes during this task.

---

## 7. Execution Accounting and Governance Boundary

- **Submissions Consumed for Protocol Definition:** `0` (`max_new_pbs_submissions = 0`, `submissions_consumed = 0`).
- **Cumulative Project Submissions:** Permanently reconciled at `5` in all ledgers (`1423095`, `1423101`, `1423102`, `1423103`, `1423169`).
- **Execution Location:** If a companion recovery job is staged, it MUST execute exclusively on the HPC cluster compute nodes via guarded PBS submission (`Invoke-GuardedSsh.ps1`), with zero local Abaqus solver execution on the Windows PC.
