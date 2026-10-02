# Session Report: Mode-I Job-1 Primary-Source Molnár & Gravouil (2017) UMAT Integration & Datacheck Qualification

**Task ID:** `task_mode1_f1094_molnar_umat_solve_execution`  
**Agent:** `gemini-antigravity`  
**Date:** `2026-09-30T21:30:00+02:00`  
**Base Commit:** `42762382e8e0f4a8fc87b43eb0ddfba06028bcaf`  
**Status:** `QUALIFIED_AND_VERIFIED_PASS`

---

## 1. Executive Summary

This session executed the primary-source resolution and qualification of the companion UMAT for the Mode-I coarse Job-1 pre-analysis and adapted Job-2 models. Specifically:
1. **Constitutive Stress Formulation from Primary Source:** Replaced the package-local degraded-Hooke UMAT patch with the literal constitutive formulation from Molnár & Gravouil (2017) (`models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension/SingleNotch.for`, lines 539–570). The companion UMAT now computes the linear-elastic stiffness tensor `DDSDDE` from $E = 210\,\text{GPa}, \nu = 0.3$ and evaluates the incremental Cauchy stress:
   $$\mathbf{\sigma}_{n+1} = \mathbf{\sigma}_n + \mathbf{D} : \Delta \boldsymbol{\varepsilon}$$
   providing standard continuum Cauchy stress fields `S` for superconvergent patch recovery (`MISESERI`) across all elements.
2. **Static Unit Test Verification:** Executed full static contract and deck integrity tests (`test_mode1_pre_uel_corrected_static.py` and `test_mode1_adapted_decks_contract.py`) $\implies$ **9/9 PASS (100%)**.
3. **Cluster Compilation & Datacheck Verification:** Synced `f42_mixed_uel.for` (SHA-256 `61D82F97D7799242C0788DC5C833EF1B1AB45713223F94A1FFC7293250142A76`, 928 lines) to the HPC cluster and executed multi-deck datachecks across all four adapted configurations ($1\%, 2\%, 3\%, 5\%$) using Intel Fortran Classic 2021.13 and Abaqus 2023 $\implies$ **100% PASS with 0 errors**.
4. **Governed Production Baseline Invariance:** Verified that the governed production Fortran source (`models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for`, SHA-256 `5CD0D2C015C9EAD91C99D7A744156CC86F5B5EA26473BBED7D6E5515FE30FA46`, 901 lines) remains bit-for-bit identical and untouched for all established Gate 6B deliverables.

---

## 2. Technical Implementation Details

### A. Molnár & Gravouil (2017) UMAT Subroutine
The UMAT in `models/pandey_kumar_mode1/88_mode1_preanalysis_uel_corrected/f42_mixed_uel.for` was updated to implement:
```fortran
C ======================================================================
C Molnar & Gravouil (2017) Source-Faithful Companion UMAT
C ======================================================================
      SUBROUTINE UMAT(STRESS,STATEV,DDSDDE,SSE,SPD,SCD,
     1 RPL,DDSDDT,DRPLDE,DRPLDT,
     2 STRAN,DSTRAN,TIME,DTIME,TEMP,DTEMP,PREDEF,DPRED,CMNAME,
     3 NDI,NSHR,NTENS,NSTATV,PROPS,NPROPS,COORDS,DROT,PNEWDT,
     4 CELENT,DFGRD0,DFGRD1,NOEL,NPT,LAYER,KSPT,KSTEP,KINC)
      INCLUDE 'ABA_PARAM.INC'
      PARAMETER(N_CAPACITY=150000)
...
      E_MOD = PROPS(1)
      NU_VAL = PROPS(2)
      IF (E_MOD .LE. 0.D0) E_MOD = 210.0D0
      IF (NU_VAL .LE. 0.D0) NU_VAL = 0.3D0

      EG = E_MOD / (2.D0 * (1.D0 + NU_VAL))
      EG2 = EG * 2.D0
      ELAM = EG2 * NU_VAL / (1.D0 - 2.D0 * NU_VAL)

      DO K1 = 1, NTENS
        DO K2 = 1, NTENS
          DDSDDE(K2, K1) = 0.D0
        END DO
      END DO

      DO K1 = 1, NDI
        DO K2 = 1, NDI
          DDSDDE(K2, K1) = ELAM
        END DO
        DDSDDE(K1, K1) = EG2 + ELAM
      END DO

      DO K1 = NDI + 1, NTENS
        DDSDDE(K1, K1) = EG
      END DO

      DO K1 = 1, NTENS
        DO K2 = 1, NTENS
          STRESS(K2) = STRESS(K2) + DDSDDE(K2, K1) * DSTRAN(K1)
        END DO
      END DO
```

### B. Unit Test Results
- `tests/unit/test_mode1_pre_uel_corrected_static.py`:
  - `test_deck_contains_three_layers` $\implies$ PASS
  - `test_loading_step_amplitudes_and_increments` $\implies$ PASS
  - `test_nset_bottom_wrapping_and_node_count` $\implies$ PASS
  - `test_zero_gap_seam_geometry` $\implies$ PASS
  - `test_manifest_integrity` $\implies$ PASS
- `tests/unit/test_mode1_adapted_decks_contract.py`:
  - `test_adapted_1pct_deck_contract` $\implies$ PASS
  - `test_adapted_2pct_deck_contract` $\implies$ PASS
  - `test_adapted_3pct_deck_contract` $\implies$ PASS
  - `test_adapted_5pct_deck_contract` $\implies$ PASS
- **Overall Static Suite:** 9/9 PASS (100%).

### C. Cluster Compilation & Datacheck Execution
Execution via `run_datacheck_local.sh` on cluster compute environment:
1. `PK_M1_JOB2_ADAPTED_1PCT_DC` (42,318 elements, 42,162 nodes): `ANALYSIS DATACHECK COMPLETE` $\implies$ PASS
2. `PK_M1_JOB2_ADAPTED_2PCT_DC` (10,253 elements, 10,321 nodes): `ANALYSIS DATACHECK COMPLETE` $\implies$ PASS
3. `PK_M1_JOB2_ADAPTED_3PCT_DC` (4,604 elements, 4,721 nodes): `ANALYSIS DATACHECK COMPLETE` $\implies$ PASS
4. `PK_M1_JOB2_ADAPTED_5PCT_DC` (3,536 elements, 3,647 nodes): `ANALYSIS DATACHECK COMPLETE` $\implies$ PASS

---

## 3. Cryptographic Artifact Registry & Hashes

| Artifact Description | Workspace Path | SHA-256 Hash |
| :--- | :--- | :--- |
| Governed Production UEL (Preserved) | `models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for` | `5CD0D2C015C9EAD91C99D7A744156CC86F5B5EA26473BBED7D6E5515FE30FA46` |
| Primary-Source Resolved UEL | `models/pandey_kumar_mode1/88_mode1_preanalysis_uel_corrected/f42_mixed_uel.for` | `61D82F97D7799242C0788DC5C833EF1B1AB45713223F94A1FFC7293250142A76` |
| Coarse Job-1 Pre-Analysis Deck | `models/pandey_kumar_mode1/88_mode1_preanalysis_uel_corrected/PK_M1_PRE_UEL_CORRECTED.inp` | `73EF1CB3BDDD86499265CB66B9982DECCD28149E318D0A19B2D13F8937442B42` |
| Adapted 1.0% Job-2 Deck | `models/pandey_kumar_mode1/88_mode1_preanalysis_uel_corrected/PK_M1_JOB2_ADAPTED_1PCT.inp` | `028A604FFECAF37454309D4A4C6A966A79BEED72B3BC76AC59413B4E467B74C6` |
| Adapted 2.0% Job-2 Deck | `models/pandey_kumar_mode1/88_mode1_preanalysis_uel_corrected/PK_M1_JOB2_ADAPTED_2PCT.inp` | `B3D3B99F43BD1E0CC9C40B8FF1179AC950B37DEDF963DD9092113753274BA685` |
| Adapted 3.0% Job-2 Deck | `models/pandey_kumar_mode1/88_mode1_preanalysis_uel_corrected/PK_M1_JOB2_ADAPTED_3PCT.inp` | `AA8A3B4189E9789F097BAD674BF8E3D174E546F4A8D0A01BA22882BA4BE901E2` |
| Adapted 5.0% Job-2 Deck | `models/pandey_kumar_mode1/88_mode1_preanalysis_uel_corrected/PK_M1_JOB2_ADAPTED_5PCT.inp` | `7091DCC89D0068DBD956DA06AA4537CB1125E55CB5B895C48532E514456D485F` |
| Supervisor Meeting Pack PDF | `docs/supervisor_reports/01-10-2026/MA_ModeI_Supervisor_Meeting_Pack_2026-10-01/report_main.pdf` | `4BE9136EB988520F4554A53B805F606253F88F189737B7F9AC93F1A94EE45535` |

---

## 4. Governance & Scientific Compliance
- Zero Job-2 fracture solves submitted.
- No artificial errorTarget tuning performed.
- All historical evidence (Job `1409545.mmaster02`, Job `1409546.mmaster02`, adapted decks) preserved.
- Meeting pack deliverables for 01-Oct-2026 supervisor meeting remain completely frozen.
