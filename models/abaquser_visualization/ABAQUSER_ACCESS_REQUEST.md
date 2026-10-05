# Formal IMFD Dependency Request Package: Authentic ABAQUSER Tool Integration

**To:** Master Thesis Supervisors & Tool Authors (Prof. Dr. Bjoern Kiefer, Dr.-Ing. Stephan Roth, IMFD, TU Bergakademie Freiberg)  
**From:** Master Thesis Candidate  
**Date:** September 23, 2026  
**Subject:** Software Access & Technical Interface Specification Request for Thesis Task 6 (IMFD ABAQUSER Tool Integration)  
**Gate 7 Status:** **`BLOCKED_ON_AUTHENTIC_IMFD_ABAQUSER_ACCESS`**  
**Internal Verified Bridge:** **`COMPANION_VISUALIZATION_BRIDGE_FULLY_VERIFIED`** (Production Job `1400408.mmaster02`, `PK_M1_2P_VIS`, 7,028 solver increments, $\Delta \text{RF} = 0.000000\,\mathrm{kN}$)

---

## 1. Background & Objective

Under the approved master thesis proposal (*"Application of Built-in Adaptive Remeshing and Mesh Refinement Features in Abaqus to Fracture Simulations Using Phase-field User Elements"*), **Task 6: Integration of the ABAQUSER visualization tool, developed at IMFD, into the modeling framework** represents the milestone deliverable for Gate 7.

In published literature from IMFD:
- *S. Roth, G. Hütter, U. Mühlich, B. Nassauer, L. Zybell, M. Kuna, "Visualisation of user defined finite elements with ABAQUS/Viewer", GACM Report 5 (2012/2014), pp. 7–14.*
- *V. Diddige, S. Roth, B. Kiefer, "A phase-field approach for modeling fracture in viscoelastic solids at large deformations", Comput. Methods Appl. Mech. Engrg. 436 (2025) 117688, p. 2.*

Visualization of phase-field user elements is performed using the in-house IMFD tool **ABAQUSER**.

---

## 2. Environment Audit & Access Status

A thorough read-only search was conducted across the TU Freiberg HPC cluster environment (`login.hpc.tu-freiberg.de`):
- **Environment Modules:** `module spider abaquser` and `module spider ABAQUSER` report no matching modules.
- **Cluster Software Trees:** `/cluster/application/abaqus/` contains standard Abaqus installations (`2019`, `2021`, `2022`, `2023`) without custom IMFD plugins or site-packages.
- **FKM Shared Directory:** `/projects/imfdfkm/` contains MATLAB Parallel Server (`mps2021a`) and general examples (`balken.inp`), but no ABAQUSER tool.
- **IMFD Shared Directory:** `/projects/imfd` is permission-restricted (`drwxrws--- 6 heinri8 t2-dl-rights-hpc_hw_schwarze`) for student accounts (`t2-dg-role_student`).
- **User Environment:** `~/bin`, `~/.local/bin`, and `~/projects/` contain no runnable ABAQUSER distributions.

Because no authentic distribution was found in the currently accessible environment, Gate 7 is classified as **`BLOCKED_ON_AUTHENTIC_IMFD_ABAQUSER_ACCESS`**.

---

## 3. Explicit Materials & Technical Interface Specification Requested

To integrate and verify the authentic ABAQUSER tool in compliance with Task 6, we kindly request the following materials from IMFD (Dr.-Ing. Stephan Roth):

1. **Authentic Software Artifact:** The authentic ABAQUSER source code, script (`.py`), compiled binary, or cluster path location.
2. **User Instructions & README:** Documentation or build/execution guidelines.
3. **Supported Abaqus Release(s):** Compatibility matrix (e.g. Abaqus 2021, 2022, 2023).
4. **Exact Invocation Command:** CLI syntax and options (e.g. `abaqus python abaquser.py [options]`).
5. **Required Input Format:** Specific input files required (e.g. whether it requires `.odb`, `.fil`, `.dat`, `.sim`, or custom ASCII geometry/state mapping files).
6. **Output Database Format:** Format and structure of the reconstructed visualization database.
7. **Supported Element Topologies:** Supported UEL and library element types (quadrilateral 4-node `CPE4`, triangular 3-node `CPE3`, 3D continuum).
8. **Numbering & Connectivity Assumptions:** Any element numbering, node ordering, or dual-layer mesh alignment conventions required by the parser.
9. **Required UEL Output & State-Variable Conventions:** Expected field output requests and SDV ordering. For reference, the thesis framework uses the governed mapping:
   - `STATEV(1)` / `STATEV(14)` = Element-average phase-field surrogate $d$ (dimensionless, $[0, 1]$);
   - `STATEV(2)` / `STATEV(16)` = Crack driving energy history $\mathcal{H}$ ($\mathrm{kN/mm^2} = \mathrm{J/mm^3}$ tensile strain energy density);
   - `STATEV(15)` = Degradation factor $g(d) = (1-d)^2 + k_{\text{res}}$ with verified $k_{\text{res}} = 10^{-7}$ (dimensionless, $g(d) \in [10^{-7}, 1+10^{-7}]$ for continuum $0 \le d \le 1$);
   - `STATEV(17)` = Whole-element fracture surface energy $E_{\text{frac}}^{(e)} = \int_{\Omega_e} G_c \left[ \frac{d^2}{2 l_0} + \frac{l_0}{2} |\nabla d|^2 \right] d\Omega$ ($\mathrm{kN\cdot mm} = \mathrm{J}$);
   - `STATEV(18)` = Whole-element elastic strain energy $E_{\text{elas}}^{(e)} = \int_{\Omega_e} \psi_e(\boldsymbol{\varepsilon}, d) d\Omega$ ($\mathrm{kN\cdot mm} = \mathrm{J}$);
   - `STATEV(19)` = $\bar{\psi}_f = E_{\text{frac}}^{(e)} / A_{\text{elem}}$ ($\mathrm{kN/mm} = \mathrm{J/mm^2}$ direct source algebra; volumetric $\mathrm{kN/mm^2} = \mathrm{J/mm^3}$ only under explicit $B=1\,\mathrm{mm}$);
   - `STATEV(20)` = $\bar{\psi}_e = E_{\text{elas}}^{(e)} / A_{\text{elem}}$ ($\mathrm{kN/mm} = \mathrm{J/mm^2}$ direct source algebra; volumetric $\mathrm{kN/mm^2} = \mathrm{J/mm^3}$ only under explicit $B=1\,\mathrm{mm}$).
10. **Minimal Example Model:** A small test case (sample `.inp`, solver output, and expected reconstructed output) to serve as an initial verification benchmark.
11. **Module & Environment Setup:** Any environment variables, module loads, or Python library prerequisites on the cluster.
12. **License or Path Requirements:** Any cluster group permissions (e.g., membership in `/projects/imfd` or specific Unix rights) needed to execute the tool.

---

## 4. Operational Execution Plan (Zero Additional Solver Costs)

Upon receipt of the authentic ABAQUSER package:
1. The tool will be cryptographically registered in `src/abaquser/upstream/` with SHA256 hashes recorded.
2. A smoke test will be executed on the minimal 4-element benchmark model.
3. Once the authentic ABAQUSER implementation and its interface instructions are provided, I will integrate it with the existing verified Mode-I benchmark according to the documented input/output requirements and perform the minimum necessary verification.
4. Reconstructed contour fields and state variables will be compared point-by-point against raw UEL fields and companion UMAT fields to close Gate 7 with complete academic rigor.
5. **No unnecessary additional multi-hour solver jobs will be required.**

---

## 5. Ready-to-Send Email Draft to Dr.-Ing. Stephan Roth

```text
Subject: Master Thesis Task 6: Request for Authentic IMFD ABAQUSER Tool / Cluster Access

Dear Dr. Roth,

I hope this email finds you well.

In the context of my Master Thesis ("Application of Built-in Adaptive Remeshing and Mesh Refinement Features in Abaqus to Fracture Simulations Using Phase-field User Elements" under the supervision of Prof. Dr. Kiefer and yourself), I am currently working on Thesis Task 6 (Gate 7): "Integration of the ABAQUSER visualization tool, developed at IMFD, into the modeling framework."

We have successfully established and verified an internal in-solver companion visualization bridge (confirming zero parasitic stiffness across 7,028 solver increments in job 1400408.mmaster02). However, to formally complete Task 6 and adhere to the proposal requirements and published literature (Roth et al., GACM Report 5, 2012/2014; Diddige, Roth, Kiefer, CMAME 2025), we want to integrate and benchmark against the authentic IMFD ABAQUSER tool.

I performed an inventory of the TU Freiberg HPC cluster environment (login.hpc.tu-freiberg.de), but did not find a runnable distribution in the accessible module system (module spider abaquser) or shared application paths. Furthermore, the directory /projects/imfd is permission-restricted for my student account (pr21vyci).

Could you please provide access to the authentic ABAQUSER tool (or let me know its location on the cluster / git repository), along with:
1. Brief execution/invocation instructions (e.g. CLI command syntax and supported Abaqus/Python versions);
2. Required input file format and interface conventions;
3. Expected UEL output/state-variable formatting conventions;
4. A minimal sample input/output example for initial testing, if available.

Once the authentic ABAQUSER implementation and its interface instructions are provided, I will integrate it with the existing verified Mode-I benchmark according to the documented input/output requirements and perform the minimum necessary verification.

Thank you very much for your guidance and support.

Best regards,

Pruthvirajsinh Padhiyar
Master Thesis Candidate
Institute of Mechanics and Fluid Dynamics (IMFD)
TU Bergakademie Freiberg
```
