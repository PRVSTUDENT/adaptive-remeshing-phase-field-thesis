# Mode-II Stage-D 1390439 Virgin-State & Early-Damage Forensic Audit Record

**Task ID**: `F268AUDIT-M2-STAGE-D-1390439-VIRGIN-STATE-AND-EARLY-DAMAGE-AUDIT1`  
**Date**: 18 August 2026  
**Status**: `INGESTION_DEFECT_ISOLATED / HARDCODED_FALLBACK_PATH_IDENTIFIED / EARLY_SATURATION_EXPLAINED / GATES_HELD_CONSERVATIVE`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Root Cause Identification: UEXTERNALDB LOP=0 State Ingestion

Forensic inspection of the submitted Fortran UEL `f44_mixed_uel_restart_stateinit.for` lines 40–46 reveals a hardcoded fallback path:

```fortran
IF (.NOT. FILE_EXISTS) THEN
  FNAME = '/home/pr21vyci/projects/adaptive-remeshing/models/'
1   // 'generated/mode_ii/production_state_transfer_batch/'
2   // 'M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/'
3   // 'STAGE_D_COMMITTED_STATE.bin'
  INQUIRE(FILE=FNAME, EXIST=FILE_EXISTS)
ENDIF
```

### Execution Evidence on Cluster:
- When job `1390439.mmaster02` ran in directory `M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL`, `UEXTERNALDB (LOP=0)` checked for `STAGE_D_COMMITTED_STATE.bin`.
- Because the file was not in the local job directory, the inquiry fell through to the hardcoded path pointing to `M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/STAGE_D_COMMITTED_STATE.bin` (which existed from job `1390279`).
- `INQUIRE` evaluated to `.TRUE.`, and `UEXTERNALDB` read `SV_ELEM_NODAL_PHASE_COM` and `SV_H_COMMITTED` for all 8,836 physical quads.
- **Solver Message Log Verification**: Both `M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.msg` and `.dat` explicitly log:
  ```text
  SUCCESS: Imported restart state from Stage-D state file
  ```
- **Consequence**: `1390439.mmaster02` was **NOT** initialized with virgin state ($d=0, \mathcal{H}=0$). The transferred history variable ($\max \mathcal{H} = 0.848870\text{ MPa}$) was active in the UEL module from the first increment.

---

## 2. Early-Increment Trajectory Reconstruction (Frames 0 to 15)

```text
======================================================================================================================
Frame | Inc   | Step Time    | Phys U1 (mm)   | RP RF1 (kN)    | d_min      | d_max      | N(d<=0)  | N(d>=1)  | Max d Node (x, y)
----------------------------------------------------------------------------------------------------------------------
0     | 0     | 0.000000     | 0.000000       | -0.000000      | 0.000000   | 0.000000   | 9073     | 0        | 1      (-0.500, -0.500)
1     | 1     | 0.001000     | 0.000050       | +0.000601      | 0.000000   | 0.324326   | 70       | 0        | 4513   (+0.000, +0.000)
2     | 2     | 0.001250     | 0.000062       | +0.000739      | 0.000000   | 0.324342   | 70       | 0        | 4513   (+0.000, +0.000)
3     | 3     | 0.001500     | 0.000075       | +0.000887      | 0.000000   | 0.405407   | 56       | 0        | 4513   (+0.000, +0.000)
4     | 4     | 0.001750     | 0.000088       | +0.001019      | 0.000000   | 0.405407   | 56       | 0        | 4513   (+0.000, +0.000)
5     | 5     | 0.002125     | 0.000106       | +0.001237      | 0.000000   | 0.486472   | 51       | 0        | 4513   (+0.000, +0.000)
6     | 6     | 0.002688     | 0.000134       | +0.001526      | 0.000000   | 0.486472   | 51       | 0        | 4513   (+0.000, +0.000)
7     | 7     | 0.003531     | 0.000177       | +0.002005      | 0.000000   | 0.608070   | 43       | 0        | 4513   (+0.000, +0.000)
8     | 8     | 0.004797     | 0.000240       | +0.002612      | 0.000000   | 0.608070   | 43       | 0        | 4513   (+0.000, +0.000)
9     | 9     | 0.006695     | 0.000335       | +0.003645      | 0.000000   | 0.790466   | 35       | 0        | 4513   (+0.000, +0.000)
10    | 10    | 0.009543     | 0.000477       | +0.004838      | 0.000000   | 0.790466   | 35       | 0        | 4513   (+0.000, +0.000)
11    | 11    | 0.013814     | 0.000691       | +0.007003      | 0.000000   | 1.000000   | 23       | 3        | 4418   (+0.000, -0.003)
12    | 12    | 0.020222     | 0.001011       | +0.009307      | 0.000000   | 1.000000   | 23       | 3        | 4418   (+0.000, -0.003)
13    | 13    | 0.029833     | 0.001492       | +0.013730      | 0.000001   | 1.000000   | 16       | 33       | 4227   (-0.003, -0.008)
14    | 14    | 0.044249     | 0.002212       | +0.018022      | 0.000001   | 1.000000   | 16       | 33       | 4227   (-0.003, -0.008)
15    | 15    | 0.064249     | 0.003212       | +0.026168      | 0.000001   | 1.000000   | 7        | 124      | 3846   (-0.005, -0.018)
======================================================================================================================
```

- **First Nonzero Damage Increment**: Increment 1 ($U_1 = 0.000050\text{ mm}$, $d_{\max} = 0.324326$ at notch-tip Node 4513).
- **First Upper-Bound Saturation ($d=1.0$)**: Increment 11 ($U_1 = 0.000691\text{ mm}$, 3 nodes saturated at $x=0.000, y=-0.003\text{ mm}$).
- **Mechanism of Rapid Saturation**: The initial step began at virgin mechanical displacement ($U_1=0$) while possessing full handoff history ($\mathcal{H} = 0.849\text{ MPa}$) without the prescribed handoff displacement boundary conditions. The resulting unbalanced phase field residual instantly solved to $d = 0.324326$ in Increment 1 and rapidly propagated under subsequent continuous shearing.

---

## 3. Comparison with Canonical H1 Continuous Baseline (1389686.mmaster02)

```text
================================================================================
Frame | Inc   | Phys U1 (mm)   | 1390439 d_max  | 1389686 (H1) d_max | Observation
--------------------------------------------------------------------------------
0     | 0     | 0.000000       | 0.000000       | 0.000000           | Initial deck state
1     | 1     | 0.000050       | 0.324326       | 0.000003           | Ingestion defect in 1390439
4     | 4     | 0.000088       | 0.405407       | 0.000007           | Microscopic in H1
7     | 7     | 0.000177       | 0.608070       | 0.000103           | Microscopic in H1
11    | 11    | 0.000691       | 1.000000       | 0.001250           | Saturated in 1390439 vs virgin in H1
================================================================================
```

- In true virgin continuous H1 (1389686), damage onset ($d > 0.01$) does not occur until $U_1 \approx 0.005\text{ mm}$, and upper bound saturation ($d=1.0$) is strictly a post-peak localization phenomenon ($U_1 > 0.015\text{ mm}$).
- The early saturation in `1390439` is solely attributable to unintended state file ingestion via the hardcoded path.

---

## 4. Scientific Verdict & Gate Status

- **Scientific Verdict**: `1390439.mmaster02` did **not** execute as a virgin continuous control. It executed as an un-equilibrated transferred-state restart without boundary clamping. Consequently, it **cannot** be used to accept or reject the Stage-D target mesh discretization hypothesis.
- **Terminal Solver Status**: Preserved as technical completion (`Exit_status = 0`, 62 increments), not scientific validation.
- **Gates Preserved**:
  - `stage_d_nonmatching_transfer_validation` = `UNDER_FORENSIC_REVIEW`
  - `nonmatching_transfer_algorithm_scientifically_unblocked` = `false`
  - `production_adaptive_accuracy_validation_scientifically_unblocked` = `false`
