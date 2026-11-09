"""
scripts/build_and_run_f1698_patch_test.py

Implements Task F1698 Experiment 1: Minimal Patch Validation.
Tests 5 model configurations across 3 damage states:
- State 1: Intact (d = 0.0, uy = 0.001 mm)
- State 2: Partially damaged (d = 0.50, uy = 0.005 mm)
- State 3: Strongly damaged (d = 0.95, uy = 0.010 mm)

Models:
- Model A: Reference UEL-only (Phase U1 + Mech U2, no companion)
- Model B1: UEL + Companion (STRESS = 0, DDSDDE = 1e-11) [Baseline]
- Model B2: UEL + Companion (STRESS = sigma_d, DDSDDE = 1e-11) [Stress-only attempt]
- Model B3: UEL + Companion (STRESS = sigma_d, DDSDDE = C_d) [Full tangent attempt]
- Model C: Sequential Recovery Reference (CPE4 with degraded UMAT)
"""

import os
import sys
import subprocess
import json
import re

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
WORK_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "198_pk_sec43_coupled_validation")
RESULTS_DIR = os.path.join(REPO_ROOT, "results", "validation")
os.makedirs(WORK_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# ------------------------------------------------------------------------------
# 1. Read base production UEL and patch UMAT for Mode 1, 2, 3
# ------------------------------------------------------------------------------
BASE_UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
with open(BASE_UEL_PATH, "r", encoding="utf-8") as f:
    uel_code = f.read()

# Replace SUBROUTINE UMAT with parameterized mode support:
# PROPS: 1=E_MOD, 2=E_NU, 3=N_PHYS, 4=MODE (1=Zero, 2=StressOnly, 3=FullTangent)
old_umat_start = "      SUBROUTINE UMAT(STRESS,STATEV,DDSDDE,SSE,SPD,SCD,"
umat_idx = uel_code.find(old_umat_start)
assert umat_idx != -1, "Could not find SUBROUTINE UMAT in f42_mixed_uel.for"

uel_body_before_umat = uel_code[:umat_idx]

f1698_umat = """      SUBROUTINE UMAT(STRESS,STATEV,DDSDDE,SSE,SPD,SCD,
     1 RPL,DDSDDT,DRPLDE,DRPLDT,
     2 STRAN,DSTRAN,TIME,DTIME,TEMP,DTEMP,PREDEF,DPRED,CMNAME,
     3 NDI,NDS,NTENS,NSTATV,PROPS,NPROPS,COORDS,DROT,PNEWDT,
     4 CELENT,DFGRD0,DFGRD1,NOEL,NPT,KSLAY,KSPT,KSTEP,KINC)
      INCLUDE 'ABA_PARAM.INC'
      PARAMETER(N_CAPACITY=150000)

      CHARACTER*80 CMNAME
      DIMENSION STRESS(NTENS),STATEV(NSTATV),
     1 DDSDDE(NTENS,NTENS),DDSDDT(NTENS),DRPLDE(NTENS),
     2 STRAN(NTENS),DSTRAN(NTENS),TIME(2),PREDEF(1),DPRED(1),
     3 PROPS(NPROPS),COORDS(3),DROT(3,3),DFGRD0(3,3),DFGRD1(3,3)

      DOUBLE PRECISION SV_PHASE_COMMITTED(N_CAPACITY)
      DOUBLE PRECISION SV_PHASE_TRIAL(N_CAPACITY)
      DOUBLE PRECISION SV_H_COMMITTED(N_CAPACITY,4)
      DOUBLE PRECISION SV_H_TRIAL(N_CAPACITY,4)
      DOUBLE PRECISION SV_E_FRAC(N_CAPACITY)
      DOUBLE PRECISION SV_E_ELAS(N_CAPACITY)
      DOUBLE PRECISION SV_PSI_F(N_CAPACITY)
      DOUBLE PRECISION SV_PSI_E(N_CAPACITY)

      COMMON /CB_STATE_TRANS/ SV_PHASE_COMMITTED, SV_PHASE_TRIAL,
     1                        SV_H_COMMITTED, SV_H_TRIAL,
     2                        SV_E_FRAC, SV_E_ELAS,
     3                        SV_PSI_F, SV_PSI_E

      INTEGER I, J, NPHYS_VAL, PHYSIDX, KPT_IDX, MODE_VAL
      DOUBLE PRECISION E_MOD, E_NU, D_VAL, DEG, C11, C12, C33
      DOUBLE PRECISION EPS(4)

      IF (NPROPS .GE. 3 .AND. PROPS(3) .GT. 0.D0) THEN
        NPHYS_VAL = INT(PROPS(3))
      ELSE
        NPHYS_VAL = 1
      ENDIF

      MODE_VAL = 1
      IF (NPROPS .GE. 4 .AND. PROPS(4) .GT. 0.D0) THEN
        MODE_VAL = INT(PROPS(4))
      ENDIF

      E_MOD = PROPS(1)
      E_NU  = PROPS(2)

      PHYSIDX = NOEL - 2 * NPHYS_VAL
      IF (PHYSIDX .LE. 0) PHYSIDX = NOEL

      IF (NPROPS .GE. 5) THEN
        D_VAL = PROPS(5)
      ELSE IF (PHYSIDX .LE. N_CAPACITY .AND. PHYSIDX .GT. 0) THEN
        D_VAL = SV_PHASE_TRIAL(PHYSIDX)
      ELSE
        D_VAL = 0.D0
      ENDIF

      DEG = (1.D0 - D_VAL)**2 + 1.D-7

      ! Plane strain degraded stiffness coefficients
      C11 = DEG * E_MOD * (1.D0 - E_NU) / ((1.D0 + E_NU) * (1.D0 - 2.D0 * E_NU))
      C12 = DEG * E_MOD * E_NU / ((1.D0 + E_NU) * (1.D0 - 2.D0 * E_NU))
      C33 = DEG * E_MOD / (2.D0 * (1.D0 + E_NU))

      DO I=1, NTENS
        STRESS(I) = 0.D0
        DO J=1, NTENS
          DDSDDE(I,J) = 0.D0
        ENDDO
      ENDDO

      IF (MODE_VAL .EQ. 1) THEN
        ! Mode 1: Baseline repository companion UMAT (Zero stress, near-zero tangent)
        DO I=1, NTENS
          DDSDDE(I,I) = 1.D-11
        ENDDO

      ELSE IF (MODE_VAL .EQ. 2) THEN
        ! Mode 2: Stress-only feedback (STRESS = sigma_d, DDSDDE = 1e-11)
        DO I=1, NTENS
          EPS(I) = STRAN(I) + DSTRAN(I)
        ENDDO
        STRESS(1) = C11 * EPS(1) + C12 * EPS(2)
        STRESS(2) = C12 * EPS(1) + C11 * EPS(2)
        STRESS(3) = 0.D0
        STRESS(4) = C33 * EPS(4)
        DO I=1, NTENS
          DDSDDE(I,I) = 1.D-11
        ENDDO

      ELSE IF (MODE_VAL .EQ. 3) THEN
        ! Mode 3: Full stiffness feedback (STRESS = sigma_d, DDSDDE = C_d)
        DO I=1, NTENS
          EPS(I) = STRAN(I) + DSTRAN(I)
        ENDDO
        STRESS(1) = C11 * EPS(1) + C12 * EPS(2)
        STRESS(2) = C12 * EPS(1) + C11 * EPS(2)
        STRESS(3) = 0.D0
        STRESS(4) = C33 * EPS(4)

        DDSDDE(1,1) = C11
        DDSDDE(1,2) = C12
        DDSDDE(2,1) = C12
        DDSDDE(2,2) = C11
        DDSDDE(4,4) = C33
      ENDIF

      SSE = 0.D0
      SPD = 0.D0
      SCD = 0.D0

      IF (NSTATV .GE. 1)  STATEV(1)  = D_VAL
      IF (NSTATV .GE. 15) STATEV(15) = DEG

      RETURN
      END SUBROUTINE UMAT
"""

f1698_patch_for = uel_body_before_umat + f1698_umat
patch_for_path = os.path.join(WORK_DIR, "f1698_patch_uel.for")
with open(patch_for_path, "w", encoding="utf-8") as f:
    f.write(f1698_patch_for)
print(f"Wrote parameterized patch Fortran to {patch_for_path}")

# ------------------------------------------------------------------------------
# 2. Input Deck Templates
# ------------------------------------------------------------------------------
# Geometry: 1.0 x 1.0 mm quad, Nodes 1(0,0), 2(1,0), 3(1,1), 4(0,1)
# N_phys = 1
# Phase UEL: Element 1, DOF 3
# Mech UEL: Element 2, DOFs 1, 2
# Companion CPE4: Element 3, DOFs 1, 2

def build_model_a(job_name, d_val, uy_val):
    """Model A: Pure UEL (Phase E1 + Mech E2), no companion element."""
    inp = f"""*HEADING
Model A: Pure UEL Reference (d={d_val}, uy={uy_val})
*NODE
1, 0.0, 0.0
2, 1.0, 0.0
3, 1.0, 1.0
4, 0.0, 1.0
*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM
3
*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM
1, 2
*ELEMENT, TYPE=U1, ELSET=PHASE_ELEM
1, 1, 2, 3, 4
*ELEMENT, TYPE=U2, ELSET=MECH_ELEM
2, 1, 2, 3, 4
*UEL PROPERTY, ELSET=PHASE_ELEM
0.0075, 0.0027, 210000.0, 0.30, 1.0e-7, 1
*UEL PROPERTY, ELSET=MECH_ELEM
0.0075, 0.0027, 210000.0, 0.30, 1.0e-7, 1
*NSET, NSET=N_ALL
1, 2, 3, 4
*NSET, NSET=N_BOTTOM
1, 2
*NSET, NSET=N_TOP
3, 4
*NSET, NSET=N_LEFT
1, 4
*NSET, NSET=N_RIGHT
2, 3
*STEP, NAME=PULL, NLGEOM=NO
*STATIC
1.0, 1.0, 1.0, 1.0
*BOUNDARY
N_BOTTOM, 2, 2, 0.0
N_LEFT, 1, 1, 0.0
N_RIGHT, 1, 1, 0.0
N_TOP, 2, 2, {uy_val}
N_ALL, 3, 3, {d_val}
*OUTPUT, FIELD
*NODE OUTPUT
U, RF
*ELEMENT OUTPUT, ELSET=MECH_ELEM
SDV
*END STEP
"""
    return inp


def build_model_b(job_name, d_val, uy_val, mode):
    """Model B: UEL + Companion Layer (Phase E1 + Mech E2 + Companion CPE4 E3)."""
    inp = f"""*HEADING
Model B (Mode {mode}): UEL + Companion Layer (d={d_val}, uy={uy_val})
*NODE
1, 0.0, 0.0
2, 1.0, 0.0
3, 1.0, 1.0
4, 0.0, 1.0
*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM
3
*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM
1, 2
*ELEMENT, TYPE=U1, ELSET=PHASE_ELEM
1, 1, 2, 3, 4
*ELEMENT, TYPE=U2, ELSET=MECH_ELEM
2, 1, 2, 3, 4
*UEL PROPERTY, ELSET=PHASE_ELEM
0.0075, 0.0027, 210000.0, 0.30, 1.0e-7, 1
*UEL PROPERTY, ELSET=MECH_ELEM
0.0075, 0.0027, 210000.0, 0.30, 1.0e-7, 1
*ELEMENT, TYPE=CPE4, ELSET=COMPANION_ELEM
3, 1, 2, 3, 4
*SOLID SECTION, ELSET=COMPANION_ELEM, MATERIAL=MAT_COMPANION
1.0
*MATERIAL, NAME=MAT_COMPANION
*USER MATERIAL, CONSTANTS=4
210000.0, 0.30, 1.0, {float(mode)}
*DEPVAR
5
*NSET, NSET=N_ALL
1, 2, 3, 4
*NSET, NSET=N_BOTTOM
1, 2
*NSET, NSET=N_TOP
3, 4
*NSET, NSET=N_LEFT
1, 4
*NSET, NSET=N_RIGHT
2, 3
*STEP, NAME=PULL, NLGEOM=NO
*STATIC
1.0, 1.0, 1.0, 1.0
*BOUNDARY
N_BOTTOM, 2, 2, 0.0
N_LEFT, 1, 1, 0.0
N_RIGHT, 1, 1, 0.0
N_TOP, 2, 2, {uy_val}
N_ALL, 3, 3, {d_val}
*OUTPUT, FIELD
*NODE OUTPUT
U, RF
*ELEMENT OUTPUT, ELSET=COMPANION_ELEM
MISESERI, MISESAVG, S, E, SDV
*END STEP
"""
    return inp


def build_model_c(job_name, d_val, uy_val):
    """Model C: Sequential Recovery Reference (Pure CPE4 with degraded UMAT, Mode 3)."""
    inp = f"""*HEADING
Model C: Sequential Recovery Reference (d={d_val}, uy={uy_val})
*NODE
1, 0.0, 0.0
2, 1.0, 0.0
3, 1.0, 1.0
4, 0.0, 1.0
*ELEMENT, TYPE=CPE4, ELSET=RECOVERY_ELEM
1, 1, 2, 3, 4
*SOLID SECTION, ELSET=RECOVERY_ELEM, MATERIAL=MAT_RECOVERY
1.0
*MATERIAL, NAME=MAT_RECOVERY
*USER MATERIAL, CONSTANTS=5
210000.0, 0.30, 1.0, 3.0, {d_val}
*DEPVAR
5
*NSET, NSET=N_ALL
1, 2, 3, 4
*NSET, NSET=N_BOTTOM
1, 2
*NSET, NSET=N_TOP
3, 4
*NSET, NSET=N_LEFT
1, 4
*NSET, NSET=N_RIGHT
2, 3
*STEP, NAME=RECOVERY, NLGEOM=NO
*STATIC
1.0, 1.0, 1.0, 1.0
*BOUNDARY
N_BOTTOM, 2, 2, 0.0
N_LEFT, 1, 1, 0.0
N_RIGHT, 1, 1, 0.0
N_TOP, 2, 2, {uy_val}
*OUTPUT, FIELD
*NODE OUTPUT
U, RF
*ELEMENT OUTPUT, ELSET=RECOVERY_ELEM
MISESERI, MISESAVG, S, E, SDV
*END STEP
"""
    return inp

# ------------------------------------------------------------------------------
# 3. Build All 15 Input Decks
# ------------------------------------------------------------------------------
test_cases = [
    # (JobPrefix, ModelType, StateName, d_val, uy_val, Mode)
    ("PATCH_A_INTACT", "A", "intact", 0.0, 0.001, None),
    ("PATCH_A_PARTIAL", "A", "partially_damaged", 0.50, 0.005, None),
    ("PATCH_A_STRONG", "A", "strongly_damaged", 0.95, 0.010, None),

    ("PATCH_B1_INTACT", "B1", "intact", 0.0, 0.001, 1),
    ("PATCH_B1_PARTIAL", "B1", "partially_damaged", 0.50, 0.005, 1),
    ("PATCH_B1_STRONG", "B1", "strongly_damaged", 0.95, 0.010, 1),

    ("PATCH_B2_INTACT", "B2", "intact", 0.0, 0.001, 2),
    ("PATCH_B2_PARTIAL", "B2", "partially_damaged", 0.50, 0.005, 2),
    ("PATCH_B2_STRONG", "B2", "strongly_damaged", 0.95, 0.010, 2),

    ("PATCH_B3_INTACT", "B3", "intact", 0.0, 0.001, 3),
    ("PATCH_B3_PARTIAL", "B3", "partially_damaged", 0.50, 0.005, 3),
    ("PATCH_B3_STRONG", "B3", "strongly_damaged", 0.95, 0.010, 3),

    ("PATCH_C_INTACT", "C", "intact", 0.0, 0.001, None),
    ("PATCH_C_PARTIAL", "C", "partially_damaged", 0.50, 0.005, None),
    ("PATCH_C_STRONG", "C", "strongly_damaged", 0.95, 0.010, None),
]

for job_name, mtype, sname, d, uy, mode in test_cases:
    if mtype == "A":
        content = build_model_a(job_name, d, uy)
    elif mtype.startswith("B"):
        content = build_model_b(job_name, d, uy, mode)
    elif mtype == "C":
        content = build_model_c(job_name, d, uy)

    inp_path = os.path.join(WORK_DIR, f"{job_name}.inp")
    with open(inp_path, "w", encoding="utf-8") as f:
        f.write(content)

print(f"Generated all {len(test_cases)} input decks.")

# ------------------------------------------------------------------------------
# 4. Execute All Models with MSVC + oneAPI Abaqus Environment
# ------------------------------------------------------------------------------
MSVC_BAT = r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
ONEAPI_BAT = r"C:\Program Files (x86)\Intel\oneAPI\setvars.bat"

solve_results = {}

for job_name, mtype, sname, d, uy, mode in test_cases:
    print(f"\n========================================================")
    print(f"Executing Job: {job_name} ({mtype}, {sname})")
    print(f"========================================================")

    # Clean old solver files
    for ext in [".odb", ".dat", ".msg", ".sta", ".prt", ".log", ".com", ".lck"]:
        fp = os.path.join(WORK_DIR, f"{job_name}{ext}")
        if os.path.exists(fp):
            try:
                os.remove(fp)
            except Exception:
                pass

    cmd = f'call "{MSVC_BAT}" && call "{ONEAPI_BAT}" intel64 && cd /d "{WORK_DIR}" && abaqus job={job_name} user=f1698_patch_uel.for interactive'
    proc = subprocess.run(f'cmd.exe /c "{cmd}"', shell=True, capture_output=True, text=True)

    print(f"Process return code: {proc.returncode}")

    # Inspect completion in .sta or .msg
    sta_path = os.path.join(WORK_DIR, f"{job_name}.sta")
    msg_path = os.path.join(WORK_DIR, f"{job_name}.msg")
    odb_path = os.path.join(WORK_DIR, f"{job_name}.odb")

    exit_zero = False
    cutbacks = 0
    iterations = 0

    if os.path.exists(sta_path):
        with open(sta_path, "r", encoding="utf-8", errors="ignore") as f:
            sta_content = f.read()
        if "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in sta_content:
            exit_zero = True
            print("Status: COMPLETED SUCCESSFULLY (Exit 0)")

    if os.path.exists(msg_path):
        with open(msg_path, "r", encoding="utf-8", errors="ignore") as f:
            msg_content = f.read()
        cutbacks = len(re.findall(r"CUTBACK", msg_content, re.IGNORECASE))
        iterations = len(re.findall(r"ITERATION SUMMARY", msg_content, re.IGNORECASE))

    solve_results[job_name] = {
        "job_name": job_name,
        "model_type": mtype,
        "state": sname,
        "d_val": d,
        "uy_val": uy,
        "exit_code": 0 if exit_zero else 1,
        "odb_exists": os.path.exists(odb_path),
        "cutbacks": cutbacks,
        "iterations": iterations
    }

print("\nAll solver runs finished. Summary:")
for k, v in solve_results.items():
    print(f"  {k}: Exit={v['exit_code']}, Cutbacks={v['cutbacks']}, Iterations={v['iterations']}")