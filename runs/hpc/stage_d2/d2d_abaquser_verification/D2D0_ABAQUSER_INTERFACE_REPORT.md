# D2D0 ABAQUSER Availability and Interface Report

**Classification:** `BLOCKED_ON_AUTHENTIC_IMFD_ABAQUSER_ACCESS`  
**Date:** September 23, 2026 (Updated from July 22, 2026 baseline)  
**Scope:** Exhaustive Cluster & Environment Inventory, Epistemological Statement Audit, and Interface Dependency Definition. No PBS solver jobs were submitted.

---

## 1. Result & Governance Status

The authentic IMFD ABAQUSER visualization tool is **not currently available** as an executable, module, script, or source repository in the accessible environment. 

- **Gate Status:** Gate 7 / Proposal Task 6 is formally held at **`BLOCKED_ON_AUTHENTIC_IMFD_ABAQUSER_ACCESS`**.
- **Distinction of Mechanisms:** The project's companion visualization bridge (Layer 1 Phase UEL `JTYPE=1/3` + Layer 2 Mechanical UEL `JTYPE=2/4` + Layer 3 CPE4/CPE3 UMAT layer) is fully verified under Job `1400408.mmaster02` as an internal solver bridge, but **cannot** substitute for the authentic IMFD ABAQUSER tool required by Task 6.
- **Decision:** Do not create surrogate companion-layer smoke tests to simulate ABAQUSER completion. Gate 7 remains blocked until the authentic tool is provided by IMFD.

---

## 2. Extended Cluster & Workspace Inventory Log

| Check Target | Command Executed | Detailed Finding | Status |
|---|---|---|---|
| **System Executable PATH** | `which abaquser ABAQUSER; type abaquser ABAQUSER` | No executable found in PATH (`/home/pr21vyci/bin`, `/home/pr21vyci/.local/bin`, `/usr/local/bin`, `/usr/bin`, `/opt/pbs/bin`). | `NOT_FOUND` |
| **Lmod Module Spider** | `module spider abaquser; module spider ABAQUSER` | `Lmod has detected the following error: Unable to find: "abaquser"`. | `NOT_FOUND` |
| **Lmod Available Modules** | `module -t avail 2>&1 \| grep -iE 'abaqus\|imfd\|viewer\|uel'` | No module matches `abaquser`, `imfd`, or UEL visualization utilities. | `NOT_FOUND` |
| **Cluster Applications** | `find /cluster/application/abaqus/2023/ -maxdepth 3 -name '*abaquser*'` | Standard Abaqus 2023 installation; no custom IMFD plugins or user site-packages. | `NOT_FOUND` |
| **IMFD Shared Storage** | `ls -la /projects/imfd` | Permission denied (`drwxrws--- 6 heinri8 t2-dl-rights-hpc_hw_schwarze`). | `PERMISSION_DENIED` |
| **FKM Shared Storage** | `ls -la /projects/imfdfkm/` | Contains `mps2021a` (MATLAB Parallel Server), `examples/balken.inp`, `setup`. No ABAQUSER code or scripts. | `NOT_FOUND` |
| **User Directories** | `ls -la ~/bin ~/.local/bin ~/projects` | Contains user scripts and thesis worktrees; no ABAQUSER binaries or upstream repos. | `NOT_FOUND` |
| **Project Repository** | Git history & codebase search (`D:\Master thesis\Adaptive remeshing`) | Contains `WP6_ABAQUSER_EXTERNAL_BLOCK_CLOSURE.md` and placeholder `src/abaquser/README.md`. No runnable interface. | `NOT_FOUND` |

---

## 3. Epistemological Audit of Interface Statements

Every technical claim regarding the authentic ABAQUSER workflow is classified according to primary evidence:

| Statement / Claim | Epistemological Classification | Evidential Basis |
|---|---|---|
| ABAQUSER was developed at IMFD (TU Bergakademie Freiberg) to visualize user elements in Abaqus/Viewer. | `VERIFIED_FROM_IMFD_DOCUMENTATION` | Documented in S. Roth et al., *GACM Report* 5 (2012/2014); V. Diddige et al., *CMAME* 436 (2025). |
| ABAQUSER maps UEL nodal/element field data onto standard Abaqus library elements in a reconstructed ODB. | `INFERRED_FROM_LITERATURE` | Described conceptually in Roth et al. (2012/2014); exact algorithm and internal data structures are uninspected. |
| ABAQUSER directly consumes `.odb`, `.fil`, `.dat`, or custom text files. | `UNKNOWN_UNTIL_TOOL_OBTAINED` | Literature does not disclose specific input parser formats; cannot be stated as fact prior to source inspection. |
| ABAQUSER operates as an Abaqus Python CLI script or compiled standalone binary. | `UNKNOWN_UNTIL_TOOL_OBTAINED` | Invocation syntax and runtime requirements are unpublished and inaccessible. |
| ABAQUSER requires specific UEL output formatting or element topology constraints. | `UNKNOWN_UNTIL_TOOL_OBTAINED` | UEL output variable conventions (e.g. nodal DOF vs SDV vs integration point) remain to be documented upon receipt. |

---

## 4. Multi-Layer Element Architecture & Governed State-Variable Mapping

To prevent dimensional and semantic ambiguity in future ABAQUSER mapping specifications:
- **Element Topology:**
  - Quadrilateral phase UEL: `JTYPE=1` (nodal DOF 3 = $d$)
  - Quadrilateral mechanical UEL: `JTYPE=2` (nodal DOFs 1,2 = $u_x, u_y$)
  - Triangular phase UEL: `JTYPE=3`
  - Triangular mechanical UEL: `JTYPE=4`
  - Companion UMAT elements: standard Abaqus `CPE4` / `CPE3`.
- **Governed State Variable Mapping:**
  - `STATEV(1)` / `STATEV(14)` = phase field $d$ (dimensionless, $[0, 1]$); `STATEV(14)` / `SDV14` is exposed in companion layer.
  - `STATEV(2)` / `STATEV(16)` = crack driving energy history $\mathcal{H}$ ($\mathrm{kN/mm} = \mathrm{J/mm^2}$ direct 2D area density; volumetric $\mathrm{kN/mm^2} = \mathrm{J/mm^3}$ under explicit unit thickness $B = 1\,\mathrm{mm}$); `STATEV(16)` / `SDV16` is exposed in companion layer.
  - `STATEV(15)` = degradation factor $g(d) = (1-d)^2 + k_{\text{res}}$ with verified residual stiffness $k_{\text{res}} = 10^{-7}$ (dimensionless, $[k_{\text{res}}, 1]$); `STATEV(15)` / `SDV15` is exposed in companion layer.
  - `STATEV(17)` = whole-underlying-finite-element fracture surface energy $E_{\text{frac}}^{(e)} = \int_{\Omega_e} G_c \left[ \frac{d^2}{2 l_0} + \frac{l_0}{2} |\nabla d|^2 \right] d\Omega$, native $\mathrm{kN\cdot mm} = \mathrm{J}$.
  - `STATEV(18)` = whole-underlying-finite-element elastic strain energy $E_{\text{elas}}^{(e)}$, native $\mathrm{kN\cdot mm} = \mathrm{J}$.
  - `STATEV(19)` = $\bar{\psi}_f$, direct source dimension $\mathrm{kN/mm} = \mathrm{J/mm^2}$ (direct area quotient $E_{\text{frac}}^{(e)} / A_{\text{elem}}$).
  - `STATEV(20)` = $\bar{\psi}_e$, direct source dimension $\mathrm{kN/mm} = \mathrm{J/mm^2}$ (direct area quotient $E_{\text{elas}}^{(e)} / A_{\text{elem}}$).
  - *Note:* Volumetric $\mathrm{kN/mm^2} = \mathrm{J/mm^3}$ interpretation for `STATEV(19)` and `STATEV(20)` applies only under the explicit unit thickness convention ($B = 1\,\mathrm{mm}$).

---

## 5. Required Actions & External Dependency Resolution

To resolve the external block on Gate 7 / Proposal Task 6, an explicit access request ([`ABAQUSER_ACCESS_REQUEST.md`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/abaquser_visualization/ABAQUSER_ACCESS_REQUEST.md)) has been compiled requesting:
1. Authentic ABAQUSER source code, script, or binary.
2. User instructions and CLI invocation syntax.
3. Supported Abaqus version(s) and Python environment requirements.
4. Input/output file specifications and accepted UEL output formatting.
5. Reference test example for verification.

Gate 7 remains held at **`BLOCKED_ON_AUTHENTIC_IMFD_ABAQUSER_ACCESS`**.
