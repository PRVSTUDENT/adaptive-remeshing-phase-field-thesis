# Method C Paired Same-Mesh Abaqus Control Staging & Datacheck Qualification Report

**Task ID:** `F1622-METHOD-C-SAME-MESH-ABAQUS-CONTROL-STAGING`  
**Protocol Version:** 2  
**Date:** 5 November 2026  
**Agent:** Gemini Antigravity  
**Predecessor Task:** `F1621-METHOD-C-GP-TRANSFER-SAFETY-REQUALIFICATION` (Status: `SAFETY_REQUALIFICATION_APPROVED`)  
**Supervisory Directive Intake:** ChatGPT PAD Bridge Decision `HND-44aee77a63a1` (Option 2 — Accept Offline Safety Requalification and Prioritize a Controlled Same-Mesh Abaqus Experiment)  
**Governing Submission Constraint:** Strictly 0 production solver PBS submissions authorized under Task F1622 (`production_pbs_submissions: 0`, `zero_pbs_enforced: True`)

---

## 1. Executive Summary

In accordance with supervisory directive `HND-44aee77a63a1`, this report establishes the completed preparation, cluster staging, and authentic Abaqus 2023 datacheck qualification for a paired same-mesh control experiment on accepted C5 donor Checkpoint 03 (Job `1419566.mmaster02`, $u_y = 0.0018703125$ mm, 12,996 elements).

The experiment isolates Gauss-point history transfer as a candidate cause of coupled staggered non-convergence by comparing two experimental arms under strictly identical physical and numerical conditions:
- **Arm 1 (Control Old / Package 172):** Same-mesh state transfer using the original element-averaged GP history operator, reproducing the severe intra-element flattening defect ($\max |\Delta H| = 6.3491$ MPa, $\text{RMS} = 0.0681$ MPa).
- **Arm 2 (Control Corrected / Package 173):** Same-mesh state transfer using the hardened isoparametric bilinear GP history operator, achieving exact machine-precision history identity ($\max |\Delta H| = 2.7089\times 10^{-13}$ MPa, $\text{RMS} = 2.2206\times 10^{-15}$ MPa, $\le 10^{-12}$ MPa tolerance satisfied at 100% of 51,984 Gauss points).

Both packages have been deployed to compute cluster scratch, validated via remote bash syntax checks and Python import smoke tests, and qualified through authentic interactive Abaqus 2023 mechanical and phase datachecks on `mlogin01.cluster`. All 4 subproblem datachecks passed with Exit 0, 0 errors, and authentic completion banners.

---

## 2. Experimental Matrix and Controlled Variables

To guarantee an unconfounded, scientifically rigorous comparison, all variables between Arm 1 and Arm 2 are held strictly invariant with the sole exception of the transferred Gauss-point history field and necessary job/output labels:

| Parameter / Variable | Arm 1 (Control Old - P172) | Arm 2 (Control Corrected - P173) | Controlled Parity Status |
| :--- | :--- | :--- | :--- |
| **Package Directory** | `models/pandey_kumar_mode1/172_c5_same_mesh_old_control` | `models/pandey_kumar_mode1/173_c5_same_mesh_corrected_control` | Distinct staging paths |
| **Cluster Scratch Dir** | `/scratch9/pr21vyci/runs/mode1_c5_package172_old_control` | `/scratch9/pr21vyci/runs/mode1_c5_package173_corrected_control` | Dedicated scratch areas |
| **Mesh Topology** | C5 (12,996 CPE4 Quads, 13,278 physical nodes + RP 999999) | C5 (12,996 CPE4 Quads, 13,278 physical nodes + RP 999999) | **Bitwise Identical** |
| **Coincident Slit Pairs** | 53 slit node pairs along $y = 0.05$ mm, $x \le 0.04$ mm | 53 slit node pairs along $y = 0.05$ mm, $x \le 0.04$ mm | **Bitwise Identical** |
| **Initial Displacement $u_0$** | Checkpoint 03 ($u_y = 0.0018703125$ mm, 13,278 nodes) | Checkpoint 03 ($u_y = 0.0018703125$ mm, 13,278 nodes) | **Bitwise Identical** |
| **Initial Damage $d_0$** | Checkpoint 03 ($d \in [0.000676, 0.999933]$, 13,278 nodes) | Checkpoint 03 ($d \in [0.000676, 0.999933]$, 13,278 nodes) | **Bitwise Identical** |
| **Active-Set Boundary Cards** | `active_set_boundary_cards.inc` (431,976 bytes) | `active_set_boundary_cards.inc` (431,976 bytes) | **Bitwise Identical** |
| **Frozen Production UEL** | `f42_mixed_uel.for` (`CE8D5EDC...`, 29,722 bytes) | `f42_mixed_uel.for` (`CE8D5EDC...`, 29,722 bytes) | **Bitwise Identical** |
| **History Operator** | Element-Averaged Scalar Mean | Hardened Isoparametric Bilinear + Convex Clamp | **Experimental Variable** |
| **History Perturbation Max** | **6.3491085 MPa** (63,491x coupled tolerance) | **$2.7089\times 10^{-13}$ MPa** ($< 10^{-12}$ MPa) | **$2.3\times 10^{13}\times$ Error Reduction** |
| **History Perturbation RMS** | **0.0680823 MPa** (681x coupled tolerance) | **$2.2206\times 10^{-15}$ MPa** ($< 10^{-14}$ MPa) | **Machine Precision Identity** |
| **Points Exceeding $10^{-4}$ MPa** | **34,720 / 51,984 (66.79%)** | **0 / 51,984 (0.00%)** | **100% Elimination of Violations** |
| **Anderson Acceleration** | **DISABLED** (`anderson_enabled = False`) | **DISABLED** (`anderson_enabled = False`) | **Identical (Unconfounded)** |
| **Picard Phase Relaxation** | Stage 1 $\omega_d = 0.50$, Stage 2 $\omega_d = 0.85$ | Stage 1 $\omega_d = 0.50$, Stage 2 $\omega_d = 0.85$ | **Identical** |
| **Displacement Relaxation** | Stage 1 $\omega_u = 1.00$, Stage 2 $\omega_u = 0.85$ | Stage 1 $\omega_u = 1.00$, Stage 2 $\omega_u = 0.85$ | **Identical** |
| **Compound Active-Set Switch** | $\|A_k\| \le 500, \|\Delta A_k\| \le 10, \Delta A^+ = 0$ ($W=3$) | $\|A_k\| \le 500, \|\Delta A_k\| \le 10, \Delta A^+ = 0$ ($W=3$) | **Identical** |
| **Rollback Safeguards** | Growth factor 1.05, Divergence 1.50, Cap 0.05 | Growth factor 1.05, Divergence 1.50, Cap 0.05 | **Identical** |
| **Iteration Budget** | Max 140 outer iterations | Max 140 outer iterations | **Identical** |
| **Coupled Tolerances** | $\Delta d \le 10^{-5}, \Delta u \le 10^{-9}, \Delta H \le 10^{-4}$, KKT $\le 10^{-6}$ | $\Delta d \le 10^{-5}, \Delta u \le 10^{-9}, \Delta H \le 10^{-4}$, KKT $\le 10^{-6}$ | **Identical** |

---

## 3. Cluster Staging & Authentic Datacheck Verification

Both packages were staged to compute cluster scratch using guarded non-interactive SSH (`Invoke-GuardedSsh.ps1`) and qualified interactively with Abaqus 2023 on `mlogin01.cluster`.

### 3.1 Datacheck Execution Summary

| Package | Subproblem Job | Solver & User Subroutine | Memory | Walltime | Exit Code | Authentic Datacheck Banner | Errors |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- | :---: |
| **Package 172** | `P172_MECHANICAL_DC` | Abaqus 2023 + `f42_mixed_uel.for` | 8 GB | ~12 s | **0** | `THE ANALYSIS HAS COMPLETED SUCCESSFULLY` | **0** |
| **Package 172** | `P172_PHASE_DC` | Abaqus 2023 + `f42_mixed_uel.for` | 8 GB | ~14 s | **0** | `THE ANALYSIS HAS COMPLETED SUCCESSFULLY` | **0** |
| **Package 173** | `P173_MECHANICAL_DC` | Abaqus 2023 + `f42_mixed_uel.for` | 8 GB | ~12 s | **0** | `THE ANALYSIS HAS COMPLETED SUCCESSFULLY` | **0** |
| **Package 173** | `P173_PHASE_DC` | Abaqus 2023 + `f42_mixed_uel.for` | 8 GB | ~14 s | **0** | `THE ANALYSIS HAS COMPLETED SUCCESSFULLY` | **0** |

### 3.2 Output File Authentication and Hashes

All datacheck outputs (`.dat`, `.msg`, `.stdout.txt`) were downloaded to local package trees and verified:

- **Package 172 (Arm 1 - Control Old):**
  * `P172_MECHANICAL_DC.inp`: Size = 1,718,632 bytes
  * `P172_MECHANICAL_DC.dat`: Size = 6,956 bytes, SHA-256 = `F8B1562D4766C4A107BCE7DEEB98CD63E8891A5EE87C9999F4219A3A685B0CEE`
  * `P172_MECHANICAL_DC.msg`: Size = 1,183 bytes, SHA-256 = `287476174EDF7A959327A40648A7D750DCD9CA6ED716FA5777DFAD9A678C1386`
  * `P172_PHASE_DC.inp`: Size = 2,556,155 bytes
  * `P172_PHASE_DC.dat`: Size = 6,724 bytes, SHA-256 = `6E8A7EB023A20901B6AD77EE3EEC5612088EC9156607078EC4AFA731E968A36F`
  * `P172_PHASE_DC.msg`: Size = 1,183 bytes, SHA-256 = `553B7AD9F9A3AD5DE829371988D5377382576E0378A2336A8619881331DDC893`

- **Package 173 (Arm 2 - Control Corrected):**
  * `P173_MECHANICAL_DC.inp`: Size = 1,718,638 bytes
  * `P173_MECHANICAL_DC.dat`: Size = 6,956 bytes, SHA-256 = `AE794AC4FC4A9A739176134645D4CDCB350402077A8E5A6E2FA82653A6C23815`
  * `P173_MECHANICAL_DC.msg`: Size = 1,183 bytes, SHA-256 = `FAA0BAF5F2960C368181BBDAF3E2255179EA89093BD469DE556033BB241A8B24`
  * `P173_PHASE_DC.inp`: Size = 2,556,161 bytes
  * `P173_PHASE_DC.dat`: Size = 6,724 bytes, SHA-256 = `174EF0C0EC7CC9E942294C5DA93B27B9C88C342291176EE88085AD0AF4AB2DE9`
  * `P173_PHASE_DC.msg`: Size = 1,183 bytes, SHA-256 = `A4731E500112C63CFCCCFFB53937F9477151E048ED8E340B456B6A9D7605E2E2`

### 3.3 Remote Environment Verification

1. **PBS Submit Script Syntax:**
   * `bash -n submit_M1_C5_P172_OLD_CONTROL.pbs`: **PASS (Exit 0)**
   * `bash -n submit_M1_C5_P173_CORRECTED_CONTROL.pbs`: **PASS (Exit 0)**
2. **Python Import Smoke Test:**
   * Package 172 `python3 smoke_import.py`: `REMOTE_IMPORT_SUCCESS: True`
   * Package 173 `python3 smoke_import.py`: `REMOTE_IMPORT_SUCCESS: True`
   * Verified that `SameMeshControlPDASDriver`, `Mesh2D`, `PDASReEquilibrationSolver`, and reference constants import cleanly without missing dependencies.

---

## 4. Falsifiable Scientific Hypotheses for Paired Solver Execution

With both packages staged and qualified, the paired experiment is positioned to test the following alternative hypotheses:

### Hypothesis $H_1$ (History Transfer is Primary Causal Bottleneck):
- **Prediction:** Arm 1 (Package 172) exhibits severe active-set churning, oscillatory damage increments ($\Delta d$), or early convergence stall due to the 6.35 MPa history perturbation and 34,720 violated Gauss points.
- In contrast, Arm 2 (Package 173) converges rapidly within 10–25 outer iterations, meeting all coupled tolerances ($\Delta d \le 10^{-5}$, $\Delta u \le 10^{-9}$ mm, $\Delta H \le 10^{-4}$ MPa, KKT $\le 10^{-6}$) and passing all physical acceptance gates with $\le 2.0\%$ force/energy drift.
- **Scientific Implication:** Confirms that element-averaged history distortion was the dominant root cause of non-convergence in Packages 171-R7 through R10. Authorizes immediate integration of the hardened isoparametric GP operator into production C6 remeshing (Package 171-R12).

### Hypothesis $H_0$ (History Transfer is Secondary to Coupled Fixed-Point Stagnation):
- **Prediction:** Both Arm 1 and Arm 2 experience similar convergence difficulties or require large numbers of outer iterations, indicating that same-mesh re-equilibration itself struggles under the current staggered coupling formulation regardless of history perturbation.
- **Scientific Implication:** Redirects immediate research focus to the staggered fixed-point operator, relaxation scheme, or initialization procedure rather than mesh transfer interpolation.

---

## 5. Governance and Safety Compliance

- **Zero PBS Production Submissions Maintained:** Exactly 0 PBS production solver jobs were submitted or queued during Task F1622 (`max_new_pbs_submissions: 0` strictly enforced).
- **Frozen UEL Integrity:** UEL hash `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` (29,722 bytes) strictly preserved bitwise across all decks.
- **Artifacts Reconciled:** All deliverables, datacheck receipts, manifests, and scripts are indexed with verified SHA-256 hashes and byte counts in `project_coordination/ARTIFACT_REGISTRY.csv`.

---

## 6. Next Decision Needed

Task F1622 is complete with status `DATACHECKS_PASSED_BOTH_EXIT_0`.

To proceed with testing the falsifiable hypothesis, supervisory authorization is requested to register a successor execution task (`F1623-METHOD-C-SAME-MESH-ABAQUS-CONTROL-EXECUTION`) authorizing:
1. Submission of Job Arm 1 (Package 172): `M1_C5_P172_OLD_CONTROL` (1 CPU serial, 16 GB RAM, 8 hours walltime, queue `entry_imfdfkmq` / `normal_imfdfkmq`).
2. Submission of Job Arm 2 (Package 173): `M1_C5_P173_CORRECTED_CONTROL` (1 CPU serial, 16 GB RAM, 8 hours walltime, queue `entry_imfdfkmq` / `normal_imfdfkmq`).
3. Total PBS submission quota: 2 jobs.
