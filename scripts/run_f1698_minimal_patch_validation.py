"""
scripts/run_f1698_minimal_patch_validation.py

Constructs and executes the minimal patch validation models required by Task F1698:
- Model A: Reference UEL-only mechanical model (single quad element)
- Model B1: UEL + Companion Layer with STRESS = 0, DDSDDE = 1e-11 (Repository baseline)
- Model B2: UEL + Companion Layer with STRESS = sigma_d, DDSDDE = 1e-11 (Attempted simultaneous stress-only feedback)
- Model B3: UEL + Companion Layer with STRESS = sigma_d, DDSDDE = C_d (Attempted simultaneous stress + tangent feedback)
- Model C: Reference independent / sequential recovery model

Tests across 3 physical damage states:
- State 1: Intact elastic (d = 0.0, uy = 0.001 mm)
- State 2: Partially damaged (d = 0.50, uy = 0.005 mm)
- State 3: Strongly damaged (d = 0.95, uy = 0.010 mm)

Evaluates:
- Mechanical passivity: RF_with_companion vs RF_UEL_ref
- Residual norms and solver iterations
- Integration-point stresses: sigma_UMAT vs sigma_UEL
- MISESERI availability and values
"""

import os
import subprocess
import json
import re

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
WORK_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "198_pk_sec43_coupled_validation")
RESULTS_DIR = os.path.join(REPO_ROOT, "results", "validation")
os.makedirs(WORK_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# ------------------------------------------------------------------------------
# 1. Analytical Benchmark Parameters
# ------------------------------------------------------------------------------
# Plane strain unit square: 1.0 x 1.0 x 1.0 mm
E = 210000.0   # MPa
NU = 0.30
GC = 2.7e-3    # kN/mm = 2.7 N/mm
L0 = 0.0075    # mm
K_RES = 1.0e-7

# Plane strain stiffness matrix coefficients (MPa)
C11 = E * (1.0 - NU) / ((1.0 + NU) * (1.0 - 2.0 * NU))   # 282692.3077 MPa
C12 = E * NU / ((1.0 + NU) * (1.0 - 2.0 * NU))           # 121153.8462 MPa
C33 = E / (2.0 * (1.0 + NU))                              # 80769.2308 MPa

STATES = {
    "intact": {"d": 0.0, "uy": 0.001},
    "partially_damaged": {"d": 0.50, "uy": 0.005},
    "strongly_damaged": {"d": 0.95, "uy": 0.010}
}

for name, s in STATES.items():
    d = s["d"]
    uy = s["uy"]
    g_d = (1.0 - d)**2 + K_RES
    # For constrained lateral displacement (ux=0), eps_yy = uy, eps_xx = 0
    sigma_yy = g_d * C11 * uy
    sigma_xx = g_d * C12 * uy
    s["g_d"] = g_d
    s["analytical_sigma_yy"] = sigma_yy
    s["analytical_sigma_xx"] = sigma_xx
    s["analytical_rf_y"] = sigma_yy * 1.0 * 1.0   # Area = 1.0 mm^2
    s["analytical_strain_energy"] = 0.5 * sigma_yy * uy * 1.0  # mJ

print("Analytical State References:")
for name, s in STATES.items():
    print(f"  {name}: d={s['d']}, uy={s['uy']} mm -> g(d)={s['g_d']:.7f}, sigma_yy={s['analytical_sigma_yy']:.4f} MPa, RF_y={s['analytical_rf_y']:.4f} N")

# ------------------------------------------------------------------------------
# 2. Write Fortran Subroutine for Experimental Variants B1, B2, B3
# ------------------------------------------------------------------------------
# We write a clean, dedicated Fortran subroutine for the minimal patch test:
# Subcase B1: STRESS = 0, DDSDDE = 1e-11 (baseline)
# Subcase B2: STRESS = sigma_d, DDSDDE = 1e-11 (stress only)
# Subcase B3: STRESS = sigma_d, DDSDDE = C_d (stress + tangent)

FORTRAN_SUBROUTINE = """! ==============================================================================
! minimal_patch_subroutines.for
! Implements UEL and UMAT for single-element patch testing under F1698
! ==============================================================================

      MODULE PATCH_GLOBAL_STATE
        IMPLICIT NONE
        DOUBLE PRECISION :: PRESCRIBED_D = 0.0D0
        INTEGER :: UMAT_MODE = 1  ! 1=B1(Zero), 2=B2(StressOnly), 3=B3(FullTangent)
      END MODULE PATCH_GLOBAL_STATE

! ------------------------------------------------------------------------------
! UEL Subroutine: 4-node plane strain displacement element
! ------------------------------------------------------------------------------
      SUBROUTINE UEL(RHS,AMATRX,SVARS,ENERGY,NDOFEL,NRHS,NSVARS,
     1 PROPS,NPROPS,COORDS,MCRD,NNODE,U,DU,V,A,JTYPE,TIME,DTIME,
     2 KSTEP,KINC,JELEM,PARAMS,NDLOAD,JDLOD,MDLOAD,PNEWDT,JPROPS,
     3 NJPROP,PERIOD)
      USE PATCH_GLOBAL_STATE
      INCLUDE 'ABA_PARAM.INC'

      DIMENSION RHS(MLVARX,*),AMATRX(NDOFEL,NDOFEL),PROPS(*),
     1 SVARS(*),ENERGY(8),COORDS(MCRD,NNODE),U(NDOFEL),DU(MLVARX,*),
     2 V(NDOFEL),A(NDOFEL),TIME(2),PARAMS(*),JDLOD(MDLOAD,*),
     3 PNEWDT(1),JPROPS(*)

      DOUBLE PRECISION :: E_MOD, NU_VAL, G_D, C11, C12, C33
      DOUBLE PRECISION :: GAUSS_XI(4), GAUSS_ETA(4), GAUSS_WT(4)
      DOUBLE PRECISION :: XI, ETA, WT, DETJ, SHP(3,4), DN(2,4)
      DOUBLE PRECISION :: BMAT(3,8), DB(3,8), STRAN(3), STRESS(3)
      DOUBLE PRECISION :: JAC(2,2), INVJ(2,2), D_VAL
      INTEGER :: I, J, K, L, NINT, INOD

      ! Extract material properties
      ! PROPS: 1=l0, 2=Gc, 3=E, 4=nu, 5=k, 6=prescribed_d
      E_MOD  = PROPS(3)
      NU_VAL = PROPS(4)
      IF (NPROPS .GE. 6) THEN
        D_VAL = PROPS(6)
      ELSE
        D_VAL = PRESCRIBED_D
      ENDIF

      ! Degradation function
      G_D = (1.D0 - D_VAL)**2 + 1.D-7

      ! Plane strain elasticity coefficients
      C11 = G_D * E_MOD * (1.D0 - NU_VAL) / ((1.D0 + NU_VAL) * (1.D0 - 2.D0 * NU_VAL))
      C12 = G_D * E_MOD * NU_VAL / ((1.D0 + NU_VAL) * (1.D0 - 2.D0 * NU_VAL))
      C33 = G_D * E_MOD / (2.D0 * (1.D0 + NU_VAL))

      ! Initialize
      DO I = 1, NDOFEL
        RHS(I,1) = 0.D0
        DO J = 1, NDOFEL
          AMATRX(I,J) = 0.D0
        ENDDO
      ENDDO

      ! 2x2 Gauss integration points
      GAUSS_XI(1)  = -0.577350269189626D0
      GAUSS_ETA(1) = -0.577350269189626D0
      GAUSS_XI(2)  =  0.577350269189626D0
      GAUSS_ETA(2) = -0.577350269189626D0
      GAUSS_XI(3)  =  0.577350269189626D0
      GAUSS_ETA(3) =  0.577350269189626D0
      GAUSS_XI(4)  = -0.577350269189626D0
      GAUSS_ETA(4) =  0.577350269189626D0
      DO I = 1, 4
        GAUSS_WT(I) = 1.D0
      ENDDO

      DO NINT = 1, 4
        XI  = GAUSS_XI(NINT)
        ETA = GAUSS_ETA(NINT)
        WT  = GAUSS_WT(NINT)

        ! Shape function derivatives wrt natural coordinates
        DN(1,1) = -0.25D0 * (1.D0 - ETA)
        DN(1,2) =  0.25D0 * (1.D0 - ETA)
        DN(1,3) =  0.25D0 * (1.D0 + ETA)
        DN(1,4) = -0.25D0 * (1.D0 + ETA)

        DN(2,1) = -0.25D0 * (1.D0 - XI)
        DN(2,2) = -0.25D0 * (1.D0 + XI)
        DN(2,3) =  0.25D0 * (1.D0 + XI)
        DN(2,4) =  0.25D0 * (1.D0 - XI)

        ! Jacobian
        JAC(1,1) = 0.D0; JAC(1,2) = 0.D0
        JAC(2,1) = 0.D0; JAC(2,2) = 0.D0
        DO INOD = 1, 4
          JAC(1,1) = JAC(1,1) + DN(1,INOD) * COORDS(1,INOD)
          JAC(1,2) = JAC(1,2) + DN(1,INOD) * COORDS(2,INOD)
          JAC(2,1) = JAC(2,1) + DN(2,INOD) * COORDS(1,INOD)
          JAC(2,2) = JAC(2,2) + DN(2,INOD) * COORDS(2,INOD)
        ENDDO

        DETJ = JAC(1,1)*JAC(2,2) - JAC(1,2)*JAC(2,1)
        INVJ(1,1) =  JAC(2,2) / DETJ
        INVJ(1,2) = -JAC(1,2) / DETJ
        INVJ(2,1) = -JAC(2,1) / DETJ
        INVJ(2,2) =  JAC(1,1) / DETJ

        ! Shape function derivatives wrt physical coordinates
        DO INOD = 1, 4
          SHP(1,INOD) = INVJ(1,1)*DN(1,INOD) + INVJ(1,2)*DN(2,INOD)
          SHP(2,INOD) = INVJ(2,1)*DN(1,INOD) + INVJ(2,2)*DN(2,INOD)
        ENDDO

        ! B-matrix (3 x 8)
        DO J = 1, 8
          DO I = 1, 3
            BMAT(I,J) = 0.D0
          ENDDO
        ENDDO
        DO INOD = 1, 4
          BMAT(1, 2*INOD-1) = SHP(1,INOD)
          BMAT(2, 2*INOD)   = SHP(2,INOD)
          BMAT(3, 2*INOD-1) = SHP(2,INOD)
          BMAT(3, 2*INOD)   = SHP(1,INOD)
        ENDDO

        ! Strains: STRAN = B * U
        STRAN(1) = 0.D0; STRAN(2) = 0.D0; STRAN(3) = 0.D0
        DO J = 1, 8
          STRAN(1) = STRAN(1) + BMAT(1,J) * U(J)
          STRAN(2) = STRAN(2) + BMAT(2,J) * U(J)
          STRAN(3) = STRAN(3) + BMAT(3,J) * U(J)
        ENDDO

        ! Degraded Stresses: STRESS = C * STRAN
        STRESS(1) = C11 * STRAN(1) + C12 * STRAN(2)
        STRESS(2) = C12 * STRAN(1) + C11 * STRAN(2)
        STRESS(3) = C33 * STRAN(3)

        ! Internal force: F_int = B^T * STRESS * dOmega
        DO J = 1, 8
          RHS(J,1) = RHS(J,1) - (BMAT(1,J)*STRESS(1) + BMAT(2,J)*STRESS(2) + BMAT(3,J)*STRESS(3)) * DETJ * WT
        ENDDO

        ! Tangent stiffness: K = B^T * C * B * dOmega
        DO J = 1, 8
          DB(1,J) = C11 * BMAT(1,J) + C12 * BMAT(2,J)
          DB(2,J) = C12 * BMAT(1,J) + C11 * BMAT(2,J)
          DB(3,J) = C33 * BMAT(3,J)
        ENDDO

        DO I = 1, 8
          DO J = 1, 8
            AMATRX(I,J) = AMATRX(I,J) + (BMAT(1,I)*DB(1,J) + BMAT(2,I)*DB(2,J) + BMAT(3,I)*DB(3,J)) * DETJ * WT
          ENDDO
        ENDDO

      ENDDO ! Gauss points

      ! Save state to SVARS for reference
      SVARS(1) = D_VAL
      SVARS(2) = STRESS(1)
      SVARS(3) = STRESS(2)
      SVARS(4) = STRESS(3)

      RETURN
      END SUBROUTINE UEL

! ------------------------------------------------------------------------------
! UMAT Subroutine for Companion Element Layer
! PROPS: 1=E, 2=nu, 3=d, 4=mode (1=B1 Zero, 2=B2 StressOnly, 3=B3 FullTangent)
! ------------------------------------------------------------------------------
      SUBROUTINE UMAT(STRESS,STATEV,DDSDDE,SSE,SPD,SCD,
     1 RPL,DDSDDT,DRPLDE,DRPLDT,
     2 STRAN,DSTRAN,TIME,DTIME,TEMP,DTEMP,PREDEF,DPRED,CMNAME,
     3 NDI,NDS,NTENS,NSTATV,PROPS,NPROPS,COORDS,DROT,PNEWDT,
     4 CELENT,DFGRD0,DFGRD1,NOEL,NPT,KSLAY,KSPT,KSTEP,KINC)
      USE PATCH_GLOBAL_STATE
      INCLUDE 'ABA_PARAM.INC'

      CHARACTER*80 CMNAME
      DIMENSION STRESS(NTENS),STATEV(NSTATV),
     1 DDSDDE(NTENS,NTENS),DDSDDT(NTENS),DRPLDE(NTENS),
     2 STRAN(NTENS),DSTRAN(NTENS),TIME(2),PREDEF(1),DPRED(1),
     3 PROPS(NPROPS),COORDS(3),DROT(3,3),DFGRD0(3,3),DFGRD1(3,3)

      DOUBLE PRECISION :: E_MOD, NU_VAL, D_VAL, G_D, C11, C12, C33
      INTEGER :: I, J, MODE

      E_MOD  = PROPS(1)
      NU_VAL = PROPS(2)
      D_VAL  = PROPS(3)
      MODE   = INT(PROPS(4))

      G_D = (1.D0 - D_VAL)**2 + 1.D-7

      ! Authentic degraded plane strain elasticity
      C11 = G_D * E_MOD * (1.D0 - NU_VAL) / ((1.D0 + NU_VAL) * (1.D0 - 2.D0 * NU_VAL))
      C12 = G_D * E_MOD * NU_VAL / ((1.D0 + NU_VAL) * (1.D0 - 2.D0 * NU_VAL))
      C33 = G_D * E_MOD / (2.D0 * (1.D0 + NU_VAL))

      ! Initialize tangent matrix
      DO I = 1, NTENS
        DO J = 1, NTENS
          DDSDDE(I,J) = 0.D0
        ENDDO
      ENDDO

      IF (MODE .EQ. 1) THEN
        ! Subcase B1: STRESS = 0, DDSDDE = 1e-11 (Existing repository implementation)
        DO I = 1, NTENS
          STRESS(I) = 0.D0
          DDSDDE(I,I) = 1.D-11
        ENDDO

      ELSE IF (MODE .EQ. 2) THEN
        ! Subcase B2: STRESS = sigma_d, DDSDDE = 1e-11 (Attempted stress-only feedback)
        STRESS(1) = C11 * (STRAN(1) + DSTRAN(1)) + C12 * (STRAN(2) + DSTRAN(2))
        STRESS(2) = C12 * (STRAN(1) + DSTRAN(1)) + C11 * (STRAN(2) + DSTRAN(2))
        STRESS(3) = 0.D0
        STRESS(4) = C33 * (STRAN(4) + DSTRAN(4))
        DO I = 1, NTENS
          DDSDDE(I,I) = 1.D-11
        ENDDO

      ELSE IF (MODE .EQ. 3) THEN
        ! Subcase B3: STRESS = sigma_d, DDSDDE = C_d (Attempted full stiffness feedback)
        STRESS(1) = C11 * (STRAN(1) + DSTRAN(1)) + C12 * (STRAN(2) + DSTRAN(2))
        STRESS(2) = C12 * (STRAN(1) + DSTRAN(1)) + C11 * (STRAN(2) + DSTRAN(2))
        STRESS(3) = 0.D0
        STRESS(4) = C33 * (STRAN(4) + DSTRAN(4))

        DDSDDE(1,1) = C11
        DDSDDE(1,2) = C12
        DDSDDE(2,1) = C12
        DDSDDE(2,2) = C11
        DDSDDE(4,4) = C33
      ENDIF

      ! State variables for output
      STATEV(1) = D_VAL
      STATEV(2) = G_D

      RETURN
      END SUBROUTINE UMAT
"""

fortran_path = os.path.join(WORK_DIR, "patch_subroutines.for")
with open(fortran_path, "w", encoding="utf-8") as f:
    f.write(FORTRAN_SUBROUTINE)
print(f"Wrote {fortran_path}")

# ------------------------------------------------------------------------------
# 3. Input Deck Generators
# ------------------------------------------------------------------------------
def make_model_a_inp(state_name, d_val, uy_val):
    """Model A: Pure UEL reference model (1 quad element, no companion element)."""
    inp = f"""*HEADING
Model A: Pure UEL Reference ({state_name}, d={d_val}, uy={uy_val})
*NODE
1, 0.0, 0.0
2, 1.0, 0.0
3, 1.0, 1.0
4, 0.0, 1.0
*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM
1, 2
*ELEMENT, TYPE=U1, ELSET=UEL_ELEM
1, 1, 2, 3, 4
*UEL PROPERTY, ELSET=UEL_ELEM
{L0}, {GC}, {E}, {NU}, {K_RES}, {d_val}
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
*OUTPUT, FIELD
*NODE OUTPUT
U, RF
*ELEMENT OUTPUT, ELSET=UEL_ELEM
SDV
*END STEP
"""
    return inp


def make_model_b_inp(state_name, d_val, uy_val, mode):
    """Model B: UEL + Companion Layer (Layer 1=UEL, Layer 2=CPE4 with UMAT)."""
    mode_names = {1: "B1_ZeroStress", 2: "B2_StressOnly", 3: "B3_FullTangent"}
    inp = f"""*HEADING
Model {mode_names[mode]}: UEL + Companion Layer ({state_name}, d={d_val}, uy={uy_val})
*NODE
1, 0.0, 0.0
2, 1.0, 0.0
3, 1.0, 1.0
4, 0.0, 1.0
*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM
1, 2
*ELEMENT, TYPE=U1, ELSET=UEL_ELEM
1, 1, 2, 3, 4
*UEL PROPERTY, ELSET=UEL_ELEM
{L0}, {GC}, {E}, {NU}, {K_RES}, {d_val}
*ELEMENT, TYPE=CPE4, ELSET=COMPANION_ELEM
2, 1, 2, 3, 4
*SOLID SECTION, ELSET=COMPANION_ELEM, MATERIAL=MAT_COMPANION
1.0
*MATERIAL, NAME=MAT_COMPANION
*USER MATERIAL, CONSTANTS=4
{E}, {NU}, {d_val}, {float(mode)}
*DEPVAR
5
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
*OUTPUT, FIELD
*NODE OUTPUT
U, RF
*ELEMENT OUTPUT, ELSET=COMPANION_ELEM
MISESERI, MISESAVG, S, E, SDV
*END STEP
"""
    return inp


def make_model_c_inp(state_name, d_val, uy_val):
    """Model C: Reference independent / sequential recovery model (Pure CPE4 with degraded UMAT)."""
    inp = f"""*HEADING
Model C: Sequential Recovery Reference ({state_name}, d={d_val}, uy={uy_val})
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
*USER MATERIAL, CONSTANTS=4
{E}, {NU}, {d_val}, 3.0
*DEPVAR
5
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

# Write input decks for all combinations
job_list = []
for sname, s in STATES.items():
    d_val = s["d"]
    uy_val = s["uy"]

    # Model A
    job_a = f"PATCH_A_{sname.upper()}"
    with open(os.path.join(WORK_DIR, f"{job_a}.inp"), "w") as f:
        f.write(make_model_a_inp(sname, d_val, uy_val))
    job_list.append((job_a, "A", sname, d_val, uy_val))

    # Model B1 (Zero Stress)
    job_b1 = f"PATCH_B1_{sname.upper()}"
    with open(os.path.join(WORK_DIR, f"{job_b1}.inp"), "w") as f:
        f.write(make_model_b_inp(sname, d_val, uy_val, mode=1))
    job_list.append((job_b1, "B1", sname, d_val, uy_val))

    # Model B2 (Stress Only)
    job_b2 = f"PATCH_B2_{sname.upper()}"
    with open(os.path.join(WORK_DIR, f"{job_b2}.inp"), "w") as f:
        f.write(make_model_b_inp(sname, d_val, uy_val, mode=2))
    job_list.append((job_b2, "B2", sname, d_val, uy_val))

    # Model B3 (Full Tangent)
    job_b3 = f"PATCH_B3_{sname.upper()}"
    with open(os.path.join(WORK_DIR, f"{job_b3}.inp"), "w") as f:
        f.write(make_model_b_inp(sname, d_val, uy_val, mode=3))
    job_list.append((job_b3, "B3", sname, d_val, uy_val))

    # Model C (Sequential Recovery)
    job_c = f"PATCH_C_{sname.upper()}"
    with open(os.path.join(WORK_DIR, f"{job_c}.inp"), "w") as f:
        f.write(make_model_c_inp(sname, d_val, uy_val))
    job_list.append((job_c, "C", sname, d_val, uy_val))

print(f"Generated {len(job_list)} input decks in {WORK_DIR}")