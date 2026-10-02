# Supervisor & IMFD Dependency Request: Authentic ABAQUSER Tool Integration

**To:** Master Thesis Supervisors (Prof. Dr. Bjoern Kiefer, Dr.-Ing. Stephan Roth)  
**From:** Master Thesis Candidate  
**Date:** September 2, 2026  
**Subject:** External Dependency Resolution for Proposal Task 6 (IMFD ABAQUSER Visualization Tool Integration)  
**Current Status:** **`BLOCKED_ON_AUTHENTIC_IMFD_ABAQUSER_ACCESS`**  
**Verified Internal Workaround:** **`COMPANION_VISUALIZATION_BRIDGE_FULLY_VERIFIED`**

---

## 1. Context & Mandatory Proposal Requirement

According to the master thesis proposal (*"Application of Built-in Adaptive Remeshing and Mesh Refinement Features in Abaqus to Fracture Simulations Using Phase-field User Elements"*), **Task 6: Integration of the ABAQUSER visualization tool, developed at IMFD, into the modeling framework** is a mandatory deliverable.

In recent literature from IMFD (V. Diddige, S. Roth, and B. Kiefer, *Comput. Methods Appl. Mech. Engrg.* 436, 2025, 117688, p. 2), the workflow is described as:
> *"The numerical material model developed here is implemented as a User Element Subroutine (UEL) in Abaqus [46], and the post-processing is performed using the developed in-house ABAQUSER visualization tool [47]."*  
> **Reference [47]:** S. Roth, G. Hütter, U. Mühlich, B. Nassauer, L. Zybell, M. Kuna, *"Visualisation of user defined finite elements with ABAQUS/Viewer"*, *GACM Report* 5 (2012/2014), pp. 7–14.

---

## 2. Current Implementation Status: Companion Bridge Verified

In the absence of the authentic external ABAQUSER software in the cluster environment, an internal in-solver **companion facsimile UMAT visualization bridge** was developed and executed to terminal completion under HPC production job **`1400408.mmaster02`** (Job name: `PK_M1_2P_VIS`, Queue: `normal_imfdfkmq`, Exit status: 0):
- **Mechanical Parity:** Evaluated across all **7,028 solver increments** against the accepted Task-5 baseline (`1400395.mmaster02`), yielding **$0.000000\,\mathrm{kN}$ max difference ($0.000000\%$)**, confirming zero parasitic stiffness.
- **Field Integrity:** Element-average phase-field surrogate $d$ and history field $\mathcal{H}$ (native dimension $\mathrm{kN/mm^2} = \mathrm{J/mm^3}$) are successfully transferred to companion state variables (`SDV14` / `SDV1` for $d$, and `SDV16` / `SDV2` for $\mathcal{H}$, with degradation $g(d) \in [10^{-7}, 1+10^{-7}]$ in `SDV15`).
- **CAE Visualization:** Direct headless Abaqus/CAE contour renderings were generated successfully with standard bounds $[0, 1]$.

**However:** To maintain strict academic integrity, this internal companion bridge is classified as a project mechanism and is **not** represented as an authentic execution of the IMFD ABAQUSER tool.

---

## 3. The External Dependency Blocker

Exhaustive checks across the project repository, Git history, local accounts, and the HPC system (`login.hpc.tu-freiberg.de`) confirm that the authentic ABAQUSER code/script is **not present in the accessible environment** (`REQUIRES_IMFD_INTERNAL_ACCESS` / `NOT_FOUND_IN_CURRENT_ENVIRONMENT`).

Consequently, Task 6 is formally held at **`BLOCKED_ON_AUTHENTIC_IMFD_ABAQUSER_ACCESS`**.

---

## 4. Specific Artifacts & Information Requested from IMFD

To complete the mandatory proposal deliverable, we kindly request the following items from the Institute of Mechanics and Fluid Dynamics (Dr.-Ing. Stephan Roth):

1. **Software Artifact:**
   - The authentic ABAQUSER script, Python module, or binary executable.
2. **Execution & Environment Instructions:**
   - Command-line invocation syntax and options.
   - Compatible Abaqus and Python runtime environments (e.g., Abaqus 2023 Python 3 / Python 2.7).
   - Any external library or environment variable dependencies.
3. **Interface Requirements:**
   - Expected input files (e.g., whether it requires `.odb`, `.dat`, `.fil`, or element topology text mappings).
   - Expected user element numbering or nodal connectivity requirements.
4. **Sample Package:**
   - A minimal reference example (input deck / test model and resulting reconstructed output) or user guide, if available.

---

## 5. Execution Plan upon Delivery (Zero Additional Solver Time)

Because the authentic tool interface conventions are currently classified as `UNKNOWN_UNTIL_TOOL_OBTAINED`:
1. We will qualify the tool first on our verified tiny-model benchmark.
2. Once the authentic ABAQUSER implementation and its interface instructions are provided, I will integrate it with the existing verified Mode-I benchmark according to the documented input/output requirements and perform the minimum necessary verification.
3. **No unnecessary additional multi-hour nonlinear solver jobs will be required**, provided the input requirements match standard Abaqus UEL output.
4. We will compare the ABAQUSER-reconstructed field against our verified UEL/UMAT field to close Task 6 with full academic rigor.
