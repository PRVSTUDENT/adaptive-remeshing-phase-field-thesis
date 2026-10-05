# Thesis Task 6: Visualization Workflow Integration & Verification Report

**Author:** Master Thesis Candidate  
**Date:** September 23, 2026  
**Gate 7 / Proposal Task 6 Status:** **`BLOCKED_ON_AUTHENTIC_IMFD_ABAQUSER_ACCESS`**  
**Verified In-Solver Bridge:** **`COMPANION_VISUALIZATION_BRIDGE_FULLY_VERIFIED`** (Internal Project Mechanism; distinct from authentic ABAQUSER)  
**Production Job:** `1400408.mmaster02` (`PK_M1_2P_VIS`)  
**Primary Reference Model:** Pandey & Kumar (2025) Mode-I 2.0% Adaptive Mesh ($N_{\text{el}} = 15{,}396$ finite elements, $15{,}414$ nodes; Total 3-layer model: $46{,}188$ finite elements)

---

## 1. Executive Summary & Epistemological Audit

This report documents the environment inventory, statement classification audit, state variable mapping, and verification results for **Thesis Task 6: IMFD ABAQUSER Visualization Tool Integration** (Gate 7).

### 1.1 Separation of Visualization Approaches
To maintain strict scientific integrity, two distinct visualization routes are distinguished:
1. **Authentic IMFD ABAQUSER Tool (Task 6 Target):** An external visualization tool developed at the Institute of Mechanics and Fluid Dynamics (IMFD), TU Bergakademie Freiberg (Roth et al., 2012/2014; Diddige et al., 2025). The tool source/executable is an external dependency that has not yet been provided. Gate 7 is classified as **`BLOCKED_ON_AUTHENTIC_IMFD_ABAQUSER_ACCESS`**.
2. **In-Solver Companion Visualization Bridge (Project Implementation):** An internal multi-layer element bridge (Phase UEL + Mechanical UEL + companion CPE4/CPE3 UMAT layer with zero parasitic stiffness) developed to enable immediate visualization during solver execution. Fully verified under job `1400408.mmaster02`, but **not** a substitute for authentic ABAQUSER and cannot close Gate 7.

---

## 2. Statement Classification Audit: Authentic IMFD ABAQUSER

In accordance with strict scientific epistemology, every statement regarding the authentic IMFD ABAQUSER tool is categorized into one of four evidential tiers:
- `VERIFIED_FROM_AUTHENTIC_SOURCE`: Confirmed by inspecting the authentic tool source code or executable.
- `VERIFIED_FROM_IMFD_DOCUMENTATION`: Confirmed by published IMFD literature or official institute documentation.
- `INFERRED_FROM_LITERATURE`: Deduced from high-level descriptions in related papers without source verification.
- `UNKNOWN_UNTIL_TOOL_OBTAINED`: Unknown parameter, interface contract, or file dependency requiring the actual tool.

### Classification Matrix of ABAQUSER Statements

| Topic / Statement | Epistemological Status | Evidence / Notes |
|---|---|---|
| **Origin & Purpose:** ABAQUSER is an in-house tool developed at IMFD (TU Bergakademie Freiberg) to visualize user-defined finite elements (UELs) in Abaqus/Viewer. | `VERIFIED_FROM_IMFD_DOCUMENTATION` | Published in S. Roth et al., *GACM Report* 5 (2012/2014), pp. 7–14; cited in V. Diddige, S. Roth, B. Kiefer, *CMAME* 436 (2025), 117688. |
| **General Architecture:** The tool maps UEL results and element geometry onto standard Abaqus library elements in a reconstructed output database (`.odb`). | `INFERRED_FROM_LITERATURE` | Conceptually outlined in Roth et al. (2012/2014). Exact mapping algorithms and internal data structures are uninspected. |
| **Accepted Input File Formats:** Whether authentic ABAQUSER ingests an `.odb`, `.fil`, `.dat`, `.sim`, or custom ASCII geometry/state mapping file. | `UNKNOWN_UNTIL_TOOL_OBTAINED` | Literature mentions post-processing but does not specify the exact file parser requirements. Cannot be asserted as fact. |
| **Execution Mode & Runtime Environment:** Command-line syntax, whether run as `abaqus python abaquser.py`, a compiled standalone binary, an Abaqus GUI plugin, or Python 2.7 / Python 3 module. | `UNKNOWN_UNTIL_TOOL_OBTAINED` | No runnable interface, documentation, or environment wrapper is available in the accessible cluster/local workspace. |
| **Companion Element Requirement:** Whether authentic ABAQUSER completely bypasses the need for companion library elements or requires specific dummy element layers. | `UNKNOWN_UNTIL_TOOL_OBTAINED` | Literature indicates standalone UEL post-processing, but exact input deck conventions and element connectivity constraints remain unverified. |
| **UEL Output Formatting:** Required `*ELEMENT OUTPUT` / `*NODE OUTPUT` requests, SDV numbering conventions, or integration point extrapolation rules in the solver input deck. | `UNKNOWN_UNTIL_TOOL_OBTAINED` | Depends on the specific ABAQUSER version and target UEL implementation. |
| **Supported UEL Topologies:** Supported element types (quadrilateral 4-node, triangular 3-node, higher-order elements, 3D elements). | `UNKNOWN_UNTIL_TOOL_OBTAINED` | Must be verified against tool capabilities upon receipt. |

---

## 3. Comprehensive Cluster & Environment Inventory Evidence

An exhaustive read-only search was conducted across the local project workspace and the TU Freiberg HPC cluster environment (`login.hpc.tu-freiberg.de`, user `pr21vyci`):

### 3.1 HPC Cluster Audit Commands & Results

1. **Environment Modules & Lmod:**
   - Command: `module spider abaquser; module spider ABAQUSER; module -t avail 2>&1 | grep -iE 'abaqus|imfd|viewer|uel'`
   - Result: `Lmod has detected the following error: Unable to find: "abaquser"`. No module exists for `abaquser`, `ABAQUSER`, `imfd`, or UEL visualization utilities.
2. **Cluster Software & Application Trees:**
   - Inspected `/cluster/application/abaqus/` (versions `2019`, `2021`, `2022`, `2023`).
   - Command: `find /cluster/application/abaqus/2023/ -maxdepth 3 -name '*abaquser*' -o -name '*imfd*'`
   - Result: No custom ABAQUSER plugins, site-packages, or IMFD user subroutines present.
   - Inspected `/opt/` (contains only `intel`, `pbs`, `xcat`) and `/usr/local/bin/` (standard URZ/Panasas utilities).
3. **IMFD & Shared Group Directories:**
   - Inspected `/projects/imfd`: `ls: cannot open directory '/projects/imfd': Permission denied`.
   - Inspected `/projects/imfdfkm`: Contains `HPC-FKM-Nutzunganleitung.pdf`, `examples/` (`balken.inp`, `qaba_local`), and `mps2021a/` (MATLAB Parallel Server 2021a). No ABAQUSER tool, script, or documentation.
4. **User Home & Project Directories:**
   - Inspected `/home/pr21vyci/bin`, `/home/pr21vyci/.local/bin`, `/home/pr21vyci/projects/`.
   - Result: Only local adaptive-remeshing repository checkouts, PBS submit helpers (`qsub_abq_guarded`), and standard binaries.
5. **System PATH, Executables & Aliases:**
   - Command: `which abaquser ABAQUSER; type abaquser ABAQUSER`
   - Result: No executable or shell alias found in PATH.
6. **Project Workspace & Git History:**
   - Full repository audit confirmed `WP6_ABAQUSER_EXTERNAL_BLOCK_CLOSURE.md` and placeholder `src/abaquser/README.md`. No runnable code or external distribution exists.

**Conclusion:** The authentic IMFD ABAQUSER tool is strictly classified as **`NOT_FOUND_IN_CURRENT_ENVIRONMENT`** and **`REQUIRES_IMFD_INTERNAL_ACCESS`**. Gate 7 remains held at **`BLOCKED_ON_AUTHENTIC_IMFD_ABAQUSER_ACCESS`**.

---

## 4. Multi-Layer Element Architecture & Governed State-Variable Mapping

To ensure rigorous physical, numerical, and dimensional consistency across the modeling framework, all element types, state variables, and energy densities are defined under the governed mapping.

### 4.1 Multi-Layer Finite Element Architecture
In the dual/multi-layer phase-field fracture framework, co-located elements share identical node coordinates:
- **Phase-Field UEL (Layer 1):** Quadrilateral user element `JTYPE=1` (or triangular variant `JTYPE=3`). Solves the regularized phase-field evolution equation; primary nodal degree of freedom is DOF 3 ($d$).
- **Mechanical UEL (Layer 2):** Quadrilateral user element `JTYPE=2` (or triangular variant `JTYPE=4`). Solves momentum balance with phase-field degradation; nodal degrees of freedom are DOF 1 ($u_x$) and DOF 2 ($u_y$).
- **Companion Visualization Layer (Layer 3):** Standard Abaqus library continuum plane strain elements (`CPE4` for quadrilaterals, `CPE3` for triangles) with vanishing stiffness ($E_{\text{comp}} = 10^{-11}\,\mathrm{kN/mm^2}$) driven by `f42_companion_vismat.for`. Receives state data via Fortran `COMMON /CB_STATE_TRANS/`.

### 4.2 Governed State-Variable & Energy Mapping

| Variable Slot | Symbol / Meaning | Native Mathematical Dimension | Physical Interpretation & Conventions |
|---|---|---|---|
| `STATEV(1)` / `STATEV(14)` | Phase field $d$ | Dimensionless ($-$) | Continuous crack phase field with continuum range $[0, 1]$. Exposed as `SDV1` and `SDV14` (element-average phase-field surrogate $d$) in the companion layer. |
| `STATEV(2)` / `STATEV(16)` | Crack driving energy history $\mathcal{H}$ | $\mathrm{kN/mm^2} = \mathrm{J/mm^3}$ (tensile energy density) | Maximum-in-time tensile elastic strain energy density $\psi^+ = \max_{\tau \le t} \psi^+(\tau)$. Enters the phase-field evolution equation directly alongside $G_c/l_0$ ($\mathrm{kN/mm^2} = \mathrm{J/mm^3}$). Direct volumetric dimension is $\mathrm{kN/mm^2} = \mathrm{J/mm^3}$ (not area-normalized). Exposed as `SDV2` and `SDV16` in the companion layer. |
| `STATEV(15)` | Degradation factor $g(d) = (1-d)^2 + k_{\text{res}}$ | Dimensionless ($-$) | Quadratic degradation function with verified residual stiffness $k_{\text{res}} = 10^{-7}$ ($1\times 10^{-7}$). Under the continuum range $0 \le d \le 1$, $g(d) \in [10^{-7}, 1 + 10^{-7}]$ (with $g(0) = 1 + 10^{-7}$ and $g(1) = 10^{-7}$). Unconstrained Galerkin discrete solutions may show small numerical $d > 1$ overshoot without a hard discrete constraint. Exposed as `SDV15` in the companion layer. |
| `STATEV(17)` | Whole-element fracture energy $E_{\text{frac}}^{(e)}$ | $\mathrm{kN\cdot mm} = \mathrm{J}$ (native energy) | Whole-underlying-finite-element integrated regularized crack surface energy in AT2 form: $E_{\text{frac}}^{(e)} = \int_{\Omega_e} G_c \left[ \frac{d^2}{2 l_0} + \frac{l_0}{2} |\nabla d|^2 \right] d\Omega$. Exposed as `SDV17` in the companion layer. |
| `STATEV(18)` | Whole-element elastic energy $E_{\text{elas}}^{(e)}$ | $\mathrm{kN\cdot mm} = \mathrm{J}$ (native energy) | Whole-underlying-finite-element integrated stored elastic strain energy: $E_{\text{elas}}^{(e)} = \int_{\Omega_e} \psi_e(\boldsymbol{\varepsilon}, d) d\Omega$. Exposed as `SDV18` in the companion layer. |
| `STATEV(19)` | Area-specific fracture energy $\bar{\psi}_f$ | $\mathrm{kN/mm} = \mathrm{J/mm^2}$ (direct source algebra) | Direct source-algebra quotient ($E_{\text{frac}}^{(e)} / A_{\text{elem}}$) with direct-source dimension $\mathrm{kN/mm} = \mathrm{J/mm^2}$. Volumetric $\mathrm{kN/mm^2} = \mathrm{J/mm^3}$ interpretation applies only under explicit unit thickness $B = 1\,\mathrm{mm}$. Exposed as `SDV19` in the companion layer. |
| `STATEV(20)` | Area-specific elastic energy $\bar{\psi}_e$ | $\mathrm{kN/mm} = \mathrm{J/mm^2}$ (direct source algebra) | Direct source-algebra quotient ($E_{\text{elas}}^{(e)} / A_{\text{elem}}$) with direct-source dimension $\mathrm{kN/mm} = \mathrm{J/mm^2}$. Volumetric $\mathrm{kN/mm^2} = \mathrm{J/mm^3}$ interpretation applies only under explicit unit thickness $B = 1\,\mathrm{mm}$. Exposed as `SDV20` in the companion layer. |

*Governed Duplicate Companion Mappings & Dimensional Summary:*
- `SDV1` and `SDV14` = element-average phase-field surrogate $d$ (dimensionless);
- `SDV2` and `SDV16` = history field $\mathcal{H}$ ($\mathrm{kN/mm^2} = \mathrm{J/mm^3}$);
- `SDV15` = degradation factor $g(d) = (1-d)^2 + 10^{-7} \in [10^{-7}, 1+10^{-7}]$;
- `SDV17` = whole-underlying-finite-element fracture energy $E_{\mathrm{frac}}$ ($\mathrm{kN\cdot mm} = \mathrm{J}$);
- `SDV18` = whole-underlying-finite-element elastic energy $E_{\mathrm{elas}}$ ($\mathrm{kN\cdot mm} = \mathrm{J}$);
- `SDV19` and `SDV20` = area-normalized source quantities $\bar{\psi}_f, \bar{\psi}_e$ with direct-source dimension $\mathrm{kN/mm} = \mathrm{J/mm^2}$, and volumetric interpretation ($\mathrm{kN/mm^2} = \mathrm{J/mm^3}$) only under explicit out-of-plane unit thickness $B = 1\,\mathrm{mm}$.

---

## 5. In-Solver Companion Visualization Verification (`1400408.mmaster02`)

Under production job `1400408.mmaster02` (`PK_M1_2P_VIS`, 15,396 finite elements, 46,188 total 3-layer elements), the companion visualization bridge was verified across all 7,028 increments against the baseline job `1400395.mmaster02`:

### 5.1 Mechanical Parity Matrix

```text
=======================================================================================================================================================
METRIC / GATE                       TASK-5 BASELINE (1400395)          TASK-6 PRODUCTION (1400408)        DIFFERENCE          VERDICT
=======================================================================================================================================================
Scheduler State                     F, Exit 0                          F, Exit 0                          0                   PASSED
Total Increments                    7,028 (2000 + 5028)                7,028 (2000 + 5028)                0                   PASSED
Peak Reaction Force F_peak          0.74819672 kN                      0.74819672 kN                      0.000000%           PASSED
Peak Displacement u_peak            0.00577500 mm                      0.00577500 mm                      0.000000%           PASSED
Final Reaction Force F_final        0.012670855 kN                     0.012670855 kN                     0.000000%           PASSED
Post-Peak Load Drop                 98.30648%                          98.30648%                          0.000000%           PASSED
Full-History Max Abs RF Diff        --                                 0.000000 kN                        0.000000 kN         PASSED
External Work W_ext                 3.654820e-3 kJ                     3.654820e-3 kJ                     0.000000%           PASSED
Phase Field Boundedness             N/A (UEL private SDV)              0.000000 <= d <= 1.005181          +0.52% max excess   QUALIFIED (UEL Field)
Driving Energy Positivity           N/A (UEL private SDV)              min(H) = 0.000000 kN/mm^2          Strictly >= 0.0     PASSED
CAE Viewport Exports                N/A                                5 PNGs rendered [0, 1]             Verified Clean      PASSED
=======================================================================================================================================================
```

### 5.2 Matched Benchmark States & Field Telemetry

| Matched Benchmark State | Step / Frame | Prescribed Disp $u$ | Solved UEL $\max(\text{DOF } 3)$ | Companion $\max(\text{SDV14})$ ($d$) | Companion $\min(\text{SDV15})$ ($g(d)$) | Discrepancy ($\Delta d$) | Elements $d > 1$ | Driving Energy $\max(\mathcal{H})$ |
|---|---|---|---|---|---|---|---|---|
| **Linear Elastic** | Step-1, Frame 800 | $0.002000\,\mathrm{mm}$ | $0.03887600$ | $0.03887600$ | $0.92376$ | $0.000000$ ($0.0\%$) | 0 of 15,396 (0.00%) | $8.1250 \times 10^{-2}\,\mathrm{kN/mm^2}$ |
| **Pre-Peak Localization** | Step-1, Frame 2000 | $0.005000\,\mathrm{mm}$ | $0.31531233$ | $0.31531233$ | $0.46880$ | $0.000000$ ($0.0\%$) | 0 of 15,396 (0.00%) | $9.3982 \times 10^{-1}\,\mathrm{kN/mm^2}$ |
| **Peak Reaction Force** | Step-2, Frame 750 | $0.005750\,\mathrm{mm}$ | $0.58365315$ | $0.58365315$ | $0.17335$ | $0.000000$ ($0.0\%$) | 0 of 15,396 (0.00%) | $2.9904 \times 10^{0}\,\mathrm{kN/mm^2}$ |
| **Crack Propagation** | Step-2, Frame 2000 | $0.007000\,\mathrm{mm}$ | $1.00086784$ | $1.00086784$ | $1.00 \times 10^{-7}$ | $0.000000$ ($0.0\%$) | 18 of 15,396 (0.12%) | $2.0374 \times 10^{3}\,\mathrm{kN/mm^2}$ |
| **Full Separation** | Step-2, Frame 5028 | $0.010000\,\mathrm{mm}$ | $1.00451183$ | $1.00451183$ | $1.00 \times 10^{-7}$ | $0.000000$ ($0.0\%$) | 32 of 15,396 (0.21%) | $5.0943 \times 10^{3}\,\mathrm{kN/mm^2}$ |

### 5.3 Phase-Field Overshoot ($d > 1$) Mechanism
- Telemetry: $\max(d) = 1.00518084$ (+0.52% max excess across 32 of 15,396 elements at final state).
- In `f42_mixed_uel.for`, phase field $d$ is assigned to `STATEV(1)` and transferred to companion `STATEV(14)` / `SDV14` (and `SDV1`). Solved nodal DOF 3 and companion `SDV14` match identically ($\Delta d = 0.000000$). History field $\mathcal{H}$ is transferred to `STATEV(16)` / `SDV16` (and `SDV2`) in native dimension $\mathrm{kN/mm^2} = \mathrm{J/mm^3}$.
- Degradation factor $g(d) = (1-d)^2 + k_{\text{res}}$ in `STATEV(15)` / `SDV15` strictly reaches the lower plateau $k_{\text{res}} = 10^{-7}$ in fully damaged elements ($g(d) \in [10^{-7}, 1+10^{-7}]$ for continuum $0 \le d \le 1$).
- **Mechanism:** `FORMULATION_LEVEL_DISCRETIZATION_EFFECT`. The minor overshoot originates from unconstrained Galerkin discretization of the linear phase-field equation without active-set projection ($d \le 1$). It is not an artifact of state transfer or visualization mapping.

---

## 6. Actionable Conclusion & Governance State

1. **Gate 7 Governance State:** **`BLOCKED_ON_AUTHENTIC_IMFD_ABAQUSER_ACCESS`**. Task 6 cannot be formally closed until authentic ABAQUSER materials are obtained from IMFD.
2. **No Surrogate Smoke Tests:** No surrogate companion smoke tests or dummy solver runs will be created to bypass this dependency.
3. **Formal Request Package:** An explicit access request document ([`ABAQUSER_ACCESS_REQUEST.md`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/abaquser_visualization/ABAQUSER_ACCESS_REQUEST.md)) and email draft have been compiled detailing all required materials and interface specifications needed from IMFD. Once the authentic ABAQUSER implementation and its interface instructions are provided, it will be integrated with the existing verified Mode-I benchmark according to the documented input/output requirements and verified accordingly.
