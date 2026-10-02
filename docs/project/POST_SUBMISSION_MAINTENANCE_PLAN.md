# Master Thesis Post-Submission Maintenance Plan & Repository Governance

**Project Title:** Application of Built-in Adaptive Remeshing and Mesh Refinement Features in Abaqus to Fracture Simulations Using Phase-field User Elements  
**Author:** Pruthviraja Reddy Vandavagali (Matriculation No. 68865)  
**Institutions:** Institute of Mechanics and Fluid Dynamics (IMFD), TU Bergakademie Freiberg  
**Supervisors:** Prof. Dipl.-Ing. Björn Kiefer, Ph.D., Dr.-Ing. Stephan Roth  
**Date:** September 3, 2026  
**Document Identifier:** [`docs/project/POST_SUBMISSION_MAINTENANCE_PLAN.md`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/project/POST_SUBMISSION_MAINTENANCE_PLAN.md)  
**Governing Status:** **`PROJECT_CLOSED_AWAITING_SUPERVISOR_FEEDBACK`**

---

## 1. Current Repository State

The Master Thesis research campaign, scientific implementation, numerical validation, and manuscript preparation (Tasks 1–10) are formally completed, verified, and placed into a stable, frozen maintenance state.

### 1.1 State Summary
* **Active Working Branch:** `main` (clean working state, zero uncommitted simulation changes).
* **Scientific Campaign Status:** **`ALL_SIMULATION_TASKS_COMPLETED_AND_PRESERVED`**.
* **HPC Execution Constraints:** Serial single-CPU execution constraint (`SERIAL_CPUS_1_ONLY`) and two-job concurrent scheduler threshold (`2_ACTIVE_JOBS_MAX`) maintained across all historical and archival runs.
* **Notification Status:** Telegram HPC notification workflow verified and active; standard email notification anomaly recorded as an environmental defect.
* **Master Thesis Manuscript PDF:** [`docs/thesis/PROPOSAL_ALIGNED_THESIS_MANUSCRIPT_DRAFT.pdf`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/thesis/PROPOSAL_ALIGNED_THESIS_MANUSCRIPT_DRAFT.pdf) (21 pages, 337,300 bytes, MiKTeX `pdflatex` build clean, 0 errors, 100% resolved citations and cross-references).
* **Authoritative Progress Report PDF:** [`docs/supervisor_reports/SUPERVISOR_PROGRESS_REPORT_2026-09-02.pdf`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/supervisor_reports/SUPERVISOR_PROGRESS_REPORT_2026-09-02.pdf) (45 pages, SHA-256: `FD56980515B45C998B7F71A7D3CEF33B17F73CD71E9FEF41CB12EA212819E73B`).

### 1.2 Directory Organization & Function Map
```text
D:\Master thesis\Adaptive remeshing\
├── docs/
│   ├── project/                  # Maintenance plans, checklists, mistakes logs
│   ├── supervisor_reports/       # Formal supervisor update dossiers, submission cover notes
│   ├── thesis/                   # Manuscript LaTeX source, compiled PDF, build QA reports
│   └── guides/                   # Meshing guidelines (Task 8), future user manual (Task 9)
├── models/
│   ├── pandey_kumar_mode1/       # Validated Mode-I fixed and adaptive models (Tasks 3, 5, 7)
│   ├── abaquser_visualization/   # Companion facsimile visualization bridge (Task 6)
│   ├── state_transfer/           # Multi-layer co-located UEL/UMAT transfer harnesses
│   └── parallelization/          # Serial common-block thread-safety verification suites
├── project_coordination/         # Governed ledgers (TASK_LEDGER, HPC_JOB_LEDGER, ACTIVE_TASK)
├── results/                      # Extracted reaction curves, telemetry JSONs, convergence logs
├── runs/hpc/                     # Archival HPC job run directories and solver logs
├── scripts/                      # Automated Python remeshing pipeline and verification tools
└── src/                          # Phase-field user element and state transfer core algorithms
```

---

## 2. Supervisor-Dependent Pending Items

The repository is placed on hold pending formal feedback and decision-making by academic supervisors:

```text
=======================================================================================================================================================
ITEM   DECISION AREA                      CURRENT STATUS                      REQUIRED SUPERVISOR ACTION
=======================================================================================================================================================
1      Task-6 IMFD ABAQUSER Integration   EXTERNALLY_BLOCKED                  Decision between Option A (provide authentic Python module)
                                                                              and Option B (approve verified companion bridge for defense).
2      Physical Numerical Toughening      SCIENTIFICALLY_EVALUATED            Concurrence on energetic derivation in Chapter 6 proving that
                                                                              under-resolved meshes (h > l0/4) cause artificial toughening.
3      Manuscript Structure & Content     COMMUNICATION_READY                 Editorial review and formal sign-off on the 10-chapter structure
                                                                              in PROPOSAL_ALIGNED_THESIS_MANUSCRIPT_DRAFT.pdf.
4      Thesis Defense & Final Submission  PENDING_REVIEW                      Scheduling of oral defense date and submission of final printed copies.
=======================================================================================================================================================
```

### Detailed Supervisor Guidance Options for Task 6:
* **Option A (Authentic IMFD ABAQUSER Tool):**
  * Dr.-Ing. Stephan Roth provides the authentic IMFD `ABAQUSER` Python module/script.
  * The tool will be executed directly upon the pre-generated, verified database `PK_MODE1_PROPOSED_PFM_VIS.odb` and `.fil` output.
  * **Zero solver runtime or cluster resubmission required.**
* **Option B (Formal Approval of Companion Bridge):**
  * Supervisors formally accept the companion facsimile UMAT bridge (Job `1400408.mmaster02`, exact $0.000000\%$ RF parity across all $7{,}028$ increments, zero parasitic stiffness, direct Abaqus/CAE contour output for $d$ and $\mathcal{H}$) as fully meeting the visual verification requirements for graduation.

---

## 3. External IMFD ABAQUSER Dependency Status

* **Governed State:** **`TASK6_BLOCKED_EXTERNAL_ABAQUSER_DEPENDENCY`**.
* **Companion Subroutine State:** **`COMPANION_VISUALIZATION_BRIDGE_FULLY_VERIFIED`**.
* **Technical Provenance:**
  * Subroutine File: `models/abaquser_visualization/task6_production_2pct_vis/f42_mixed_uel.for` (SHA-256: `C540B54A2A7EE96A51DEEE49BDAB714ED0FB27344F703F11ABF17F76E985B14B`).
  * Bridge Input Deck: `models/abaquser_visualization/task6_production_2pct_vis/PK_M1_PROPOSED_FACSIMILE_BRIDGE.inp` (SHA-256: `E29694CF60F47B2DCEB84D904999715C5857E36EECDCСEB5DBCDF17C89DBD07B`).
  * Verified Solver Run: PBS Job `1400408.mmaster02` (Exit Status 0, 7,028 increments, walltime 07h 04m).
  * Equivalence Metrics: Max difference in reaction force $\Delta RF_1 = 0.000000\,\mathrm{kN}$ ($0.000000\%$ relative difference across the entire deformation history vs. Job `1400395.mmaster02`).
  * Native Abaqus/CAE Contours: Verified field output mappings for phase-field damage $d$ (`STATEV15`) and driving history energy $\mathcal{H}$ (`STATEV16`).
* **Preservation Policy:** No mock scripts or placeholder codes will be substituted under the name of `ABAQUSER`. The scientific boundary between the validated companion bridge and the external proprietary tool is strictly maintained in all publications and reports.

---

## 4. Immutable Files for Exact Reproducibility

To ensure strict scientific reproducibility across all future evaluations, the following core input decks, user subroutines, configuration records, scripts, and compiled documents are frozen and **must remain completely unchanged**:

```text
=======================================================================================================================================================
FILE PATH                                                    BYTE SIZE   SHA-256 CHECKSUM                   REPRODUCIBILITY ROLE
=======================================================================================================================================================
docs/thesis/PROPOSAL_ALIGNED_THESIS_MANUSCRIPT_DRAFT.pdf        337,300   9A47172FEF31420F49FCAED4B1FE04C4   Master compiled thesis PDF (MiKTeX exit 0)
                                                                         8922C22CC506E2B4972C30C8037FC9FC
docs/thesis/PROPOSAL_ALIGNED_THESIS_MANUSCRIPT_DRAFT.tex         30,702   6024081F8DD2CCF88B49DC38DC26DBC0   Master LaTeX thesis source document
                                                                         AA53E05219E66E62FC88616E791DAB91
docs/supervisor_reports/SUPERVISOR_PROGRESS_REPORT_2026-09-02.pdf 5,978,868 FD56980515B45C998B7F71A7D3CEF33B   45-page intermediate supervisor progress report
                                                                         17F73CD71E9FEF41CB12EA212819E73B
docs/supervisor_reports/SUPERVISOR_SUBMISSION_COVER_NOTE_2026-09-03.md 5,816 17B6FBF08581065014BF2E602CDC3F24   Executive submission cover letter to supervisors
                                                                         ED8E92554E7B53118539EBA2AFF9AED9
docs/supervisor_reports/FINAL_SUPERVISOR_REVISION_PACKAGE_2026-09-03.md 7,863 52A1BC62767FF447673F9D9098186726   Comprehensive supervisor review and audit package
                                                                         B1D3A531A03F2B8833350A78B03E48E3
docs/thesis/FINAL_THESIS_ARCHIVE_MANIFEST_AND_HANDOVER.md        9,190   47E22ACD128893290A6F14C4FB46CB57   Complete archive manifest and artifact checksums
                                                                         20D4D683C9076ED4B4B4ECD056803374
docs/guides/TASK8_MESHING_AND_INCREMENT_RECOMMENDATIONS.md      11,491   895AF1D1550504FEA2E180DC4BE104BD   Task 8 mesh resolution & increment guidelines
                                                                         DFF3C07FE47883EA57ABF7B212A75A24
docs/guides/TASK9_FUTURE_USER_WORKFLOW_GUIDE.md                 11,683   4770B66234B59E0743E4C54F772E7C4A   Task 9 future user reproduction instructions
                                                                         805DF0646BCD9082C66EF305BAAC952D
models/abaquser_visualization/task6_production_2pct_vis/f42_mixed_uel.for 22,406 C540B54A2A7EE96A51DEEE49BDAB714E   Co-located 3-layer UEL/UMAT user subroutine
                                                                         D0FB27344F703F11ABF17F76E985B14B
project_coordination/HPC_JOB_LEDGER.csv                          6,849   0B6B9EC9BA176D7EA28FF644ADB547A3   Complete provenance of all PBS solver jobs
                                                                         F310664FB592D8C4E1631623A59DBED7
project_coordination/TASK_LEDGER.csv                           364,856   91CE629E226AA484558A657A63F80271   Comprehensive ledger of all project transactions
                                                                         60B58EB78E27A8571B55A7196862365E
=======================================================================================================================================================
```

---

## 5. Maintenance Protocol During Review Period

1. **Read-Only Preservation:** No modifications to mesh generation scripts, Fortran subroutines, solver input decks, or LaTeX sources will occur during the supervisor review period.
2. **Cluster Job Moratorium:** No new HPC jobs or PBS submissions shall be launched.
3. **Standby Post-Processing:** In the event that the external IMFD `ABAQUSER` script is provided, execution shall occur exclusively on local compute nodes against pre-existing ODB files, strictly respecting the pre-declared execution scope.
4. **Reactivation Gate:** Formal reopening of the repository occurs only upon receipt of written supervisor feedback, at which point minor editorial revisions or defense presentation preparation will be scheduled.

---
*End of Post-Submission Maintenance Plan.*
