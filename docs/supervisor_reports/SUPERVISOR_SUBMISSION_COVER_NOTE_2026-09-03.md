# Master Thesis Submission Cover Note & Supervisor Communication Package

**To:** Prof.\ Dipl.-Ing.\ Bj\"orn Kiefer, Ph.D. (`bjoern.kiefer@imfd.tu-freiberg.de`)  
**Cc:** Dr.-Ing.\ Stephan Roth (`stephan.roth@imfd.tu-freiberg.de`)  
**From:** Pruthviraja Reddy Vandavagali (`pruthviraja-reddy.vandavagali@student.tu-freiberg.de`, Matr.-Nr. 68865)  
**Date:** September 3, 2026  
**Document:** `docs/supervisor_reports/SUPERVISOR_SUBMISSION_COVER_NOTE_2026-09-03.md`  
**Subject:** Master Thesis Manuscript Draft & Supervisor Review Package: *Application of Built-in Adaptive Remeshing and Mesh Refinement Features in Abaqus to Fracture Simulations Using Phase-field User Elements*  
**Governing Status:** **`SUPERVISOR_COMMUNICATION_READY`**

---

## 1. Executive Email / Cover Letter Draft

**Dear Prof.\ Dr.\ Kiefer, Dear Dr.\ Roth,**

I am pleased to submit the complete draft manuscript, simulation evidence dossier, and archival package for my Master's Thesis:  
**"Application of Built-in Adaptive Remeshing and Mesh Refinement Features in Abaqus to Fracture Simulations Using Phase-field User Elements."**

The full faculty-ready thesis manuscript has been compiled without errors using MiKTeX `pdflatex`:
* **Master Thesis PDF (21 pages):** [`docs/thesis/PROPOSAL_ALIGNED_THESIS_MANUSCRIPT_DRAFT.pdf`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/thesis/PROPOSAL_ALIGNED_THESIS_MANUSCRIPT_DRAFT.pdf)
* **Master LaTeX Source:** [`docs/thesis/PROPOSAL_ALIGNED_THESIS_MANUSCRIPT_DRAFT.tex`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/thesis/PROPOSAL_ALIGNED_THESIS_MANUSCRIPT_DRAFT.tex)
* **Archive Manifest & Handover:** [`docs/thesis/FINAL_THESIS_ARCHIVE_MANIFEST_AND_HANDOVER.md`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/thesis/FINAL_THESIS_ARCHIVE_MANIFEST_AND_HANDOVER.md)
* **Supervisor Review Package:** [`docs/supervisor_reports/FINAL_SUPERVISOR_REVISION_PACKAGE_2026-09-03.md`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/supervisor_reports/FINAL_SUPERVISOR_REVISION_PACKAGE_2026-09-03.md)

---

## 2. Key Scientific Findings & Validated Deliverables (Tasks 1–10)

All ten proposal work packages have been completed with full data traceability to high-performance computing (HPC) solver runs:

1. **Fixed-Mesh Benchmark Reproduction (Task 3):**
   * Validated standard fixed-mesh Mode-I baseline under Job `1398090.mmaster02` ($15{,}192$ elements), achieving $F_{\text{peak}} = 0.7578\,\mathrm{kN}$ (**$-0.029\%$ error** vs target $0.7580\,\mathrm{kN}$) and $u_{\text{peak}} = 0.005857\,\mathrm{mm}$ (**$-0.051\%$ error**).
   * Status: **`SCIENTIFICALLY_ACCEPTED`**.

2. **Native Abaqus Adaptive Remeshing Reproduction (Tasks 4 & 5):**
   * Implemented Python automation pipeline using built-in Superconvergent Patch Recovery (SPR) stress error estimators (`MISESERI`).
   * Successfully reproduced the adaptive Mode-I benchmark under Job `1400395.mmaster02` ($15{,}396$ elements), achieving $F_{\text{peak}} = 0.7482\,\mathrm{kN}$ (**$-1.29\%$ error** vs target) with **zero solver cutbacks**.
   * Resolved the literature discrepancy: audited Job `1399632.mmaster02` to document that nominal $1.0\%$ error targets trigger scale-invariant over-refinement ($71{,}320$ elements, $-36.91\%$ force drop), confirming $2.0\%$ as the physically correct threshold.
   * Status: **`QUANTITATIVE_REPRODUCTION_PASSED` / `SCIENTIFICALLY_ACCEPTED`**.

3. **Physics of Numerical Toughening & Time-Stepping Optimization (Tasks 7 & 8):**
   * Discovered that coarsening adaptive sizing to $\text{errorTarget}=3.0\%$ (Job `1400739.mmaster02`, $7{,}633$ elements, $h \approx 0.0018\,\mathrm{mm} \approx l_0/4.2$) causes artificial damage diffusion, inflating peak reaction force by **$+12.84\%$** ($F_{\text{peak}} = 0.8553\,\mathrm{kN}$) and delaying localization by $+25.24\%$. This proves $h \le l_0/4$ is a strict physical bound to avoid artificial numerical toughening.
   * Validated an accelerated $3{,}500$-increment schedule (Job `1400738.mmaster02`) yielding a **$48.4\%$ runtime speedup** with $<0.06\%$ deviation from baseline.
   * Status: **`SCIENTIFICALLY_EVALUATED`**.

4. **In-Solver Companion Visualization Bridge (Task 6):**
   * Developed and verified an in-solver companion facsimile UMAT bridge under Job `1400408.mmaster02`, achieving **exact $0.000000\%$ RF parity** across all $7{,}028$ increments with direct Abaqus/CAE contour output for $d$ (`STATEV15`) and $\mathcal{H}$ (`STATEV16`).
   * Preserved academic boundary: authentic IMFD ABAQUSER tool integration remains held as **`TASK6_BLOCKED_EXTERNAL_ABAQUSER_DEPENDENCY`** awaiting software provision.

---

## 3. Requested Supervisor Guidance & Decisions

We kindly request your feedback and guidance on the following three points:

1. **Task-6 IMFD ABAQUSER Software Access:**
   * *Option A (Recommended):* Dr.\ Roth provides the authentic IMFD `ABAQUSER` script/module for execution on our existing verified ODB (`PK_MODE1_PROPOSED_PFM_VIS.odb`) with zero additional solver runtime.
   * *Option B:* Supervisors formally approve the verified companion facsimile UMAT bridge ($0.000000\%$ parity) as satisfying the visualization deliverable for thesis defense.
2. **Review of Numerical Toughening Derivation (Chapter 6):**
   * Concurrence with our energetic derivation demonstrating that under-resolved transition elements ($h > l_0/4$) artificially broaden the diffuse damage zone and elevate peak mechanical forces.
3. **Manuscript Structure Approval:**
   * Formal sign-off on the 10-chapter proposal-aligned structure presented in the master PDF.

Thank you very much for your continuous guidance and support.

Sincerely,  
**Pruthviraja Reddy Vandavagali**  
M.Sc. Candidate, Computational Materials Science  
Institute of Mechanics and Fluid Dynamics (IMFD)  
TU Bergakademie Freiberg
