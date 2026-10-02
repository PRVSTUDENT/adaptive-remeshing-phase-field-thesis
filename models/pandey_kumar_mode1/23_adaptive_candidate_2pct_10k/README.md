# Mode-I 2% Adaptive Candidate Production Package (10,253 Finite Elements)

## Package Overview

This package contains the fully qualified production candidate for the Mode-I 2% adaptive pre-analysis remeshed simulation:
* **Job Identifier**: `PK_M1_ADAPT_2PCT_10K_ENERGY`
* **Finite Elements**: $10,253$ (9,952 quads, 301 tris)
* **Nodes**: $10,321$
* **Mesh Origin**: Job-1 Pre-Analysis Lineage B ($h_{\min}=1.0\,\mu\text{m}, h_{\max}=20.0\,\mu\text{m}, \text{errorTarget}=2.0\%$)
* **Classification**: `DATACHECK_PASSED_READY_AFTER_CORRECTED_S1_ENERGY_QUALIFICATION`
* **Status**: **Strictly unsubmitted** (`authorized: false`). Awaiting completion and scientific review of baseline reference Job `1409734.mmaster02` (`PK_M1_REF15K_ENERGY`).

---

## File Structure & Hashes

| File | Description | SHA-256 Hash |
| :--- | :--- | :--- |
| `PK_MODE1_ADAPT_2PCT_10K_ENERGY.inp` | 4-layer fracture input deck ($N_{\text{phys}}=10253.0$) | `F9B9BB907DA83AFCADCF50D58528BDE8029D5C4277D5012967940A04C653EBA9` |
| `f42_mixed_uel.for` | Governed single-source energy user subroutine | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` |
| `submit_solver.pbs` | PBS execution script (1-CPU serial, 16 GB, dual-channel notification) | - |
| `submit_datacheck.pbs` | PBS datacheck script (8 GB, dual-channel notification) | - |
| `submit_pk_mode1_adapt_2pct_10k_energy.sh` | Guarded submission wrapper script | - |
| `job_notifications.sh` | HPC notification integration script | - |
| `extract_authoritative_mode1_energy_complete.py` | Complete post-processing extraction script | `C064C4D789547565985FB5E72E0124D9FD35B57A2DBB9D6E7711B8006E1B6B22` |
| `MANIFEST.json` | Complete machine-readable metadata manifest | - |
| `PRE_JOB_ANTI_DEVIATION_CARD.md` | Pre-job governance checklist | - |
