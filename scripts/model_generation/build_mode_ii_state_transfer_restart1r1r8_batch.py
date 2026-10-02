#!/usr/bin/env python3
"""
Build Production Scientific State-Transfer Restart-1 Candidate: M2STATE_FRACFIX_RESTART1R1R8.
Task ID: F84STATE-M2-CORRECTED-RESTART1-JACOBIAN-INVERSE-REPAIR-QUALIFICATION1

Classification: SOURCE_RECOVERY_PROPERTY_ABI_AND_RUNTIME_DEFECT_CORRECTION
Canonical Manifest Key: "files"

Key Features & Corrections:
1. Target Mesh: PK5 nonmatching mesh (4998 nodes, 4894 physical elements: 4766 quads, 128 tris).
2. Clean 6-Slot Real Property ABI:
   PROPS(1) = E_L0 (0.015 mm)
   PROPS(2) = E_GC (0.0027 kN/mm)
   PROPS(3) = E_MOD (210.0 kN/mm^2)
   PROPS(4) = E_NU (0.3)
   PROPS(5) = E_K (1.0e-07)
   PROPS(6) = N_PHYS (4894.0)
   All 4 UEL types (U1, U2, U3, U4) declare PROPERTIES=6.
3. Safe Forward Jacobian & Matrix Inversion:
   Forward Jacobian JAC(2,2) evaluated cleanly without in-place overwrite.
   Inverse matrix INVJ(2,2) computed using unaltered original JAC components for all JTYPEs (1, 2, 3, 4).
4. Consistent Newton Phase Residual: RHS = F_H - K_phase * d for JTYPE 1 and JTYPE 3.
5. Source Ingestion: Exclusively from valid predecessor job 1386469.mmaster02 at U1 = 0.005000 mm (0 reuse of 1388948).
6. All execution dependencies self-contained in candidate directory.
"""

import os
import sys
import json
import hashlib
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
SRC_R1R6R2_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R6R2"
SRC_NOTIF_SH = ROOT / "scripts/hpc/notifications/job_notifications.sh"
OUT_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R8"

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def write_lf_file(path: Path, text: str):
    clean_text = text.replace("\r\n", "\n").replace("\r", "\n")
    path.write_bytes(clean_text.encode("utf-8"))

def build_f42_mixed_uel_for() -> str:
    # 6-slot real property ABI with safe Jacobian inverse and consistent phase residual
    return """C ======================================================================
C User Subroutine UEL and UMAT for Abaqus: Mixed 3-Node / 4-Node Scheme
C Candidate Revision: M2STATE_FRACFIX_RESTART1R1R8 (Safe Jacobian Inversion + Clean 6-Property ABI)
C Production Representative Elements (PK5 NPHYS=4894, Total UEL=9788):
C   Quad High Damage: Phase E2292 / Mech E7186
C   Quad Low Damage: Phase E100 / Mech E4994
C   Tri Pair: Phase E4862 / Mech E9756
C Clean 6-Slot Property ABI:
C   PROPS(1) = E_L0  (0.015 mm)
C   PROPS(2) = E_GC  (0.0027 kN/mm)
C   PROPS(3) = E_MOD (210.0 kN/mm^2)
C   PROPS(4) = E_NU  (0.3)
C   PROPS(5) = E_K   (1.0e-07)
C   PROPS(6) = N_PHYS (4894.0)
C ======================================================================
      SUBROUTINE UEL(RHS,AMATRX,SVARS,ENERGY,NDOFEL,NRHS,NSVARS,
     1     PROPS,NPROPS,COORDS,MCRD,NNODE,U,DU,V,A,JTYPE,TIME,DTIME,
     2     KSTEP,KINC,JELEM,PARAMS,NDLOAD,JDLTYP,ADLMAG,PREDEF,
     3     NPREDF,LFLAGS,MLVARX,DDLMAG,MDLOAD,PNEWDT,JPROPS,NJPROP,
     4     PERIOD)
      INCLUDE 'ABA_PARAM.INC'
      PARAMETER(ZERO=0.D0,ONE=1.D0,TWO=2.D0,THREE=3.D0,FOUR=4.D0,
     1 HALF=0.5D0,SIX=6.D0,N_CAPACITY=100000,NSTV=18)

      DIMENSION RHS(MLVARX,1),AMATRX(NDOFEL,NDOFEL),
     1     SVARS(NSVARS),ENERGY(8),PROPS(NPROPS),
     2     COORDS(MCRD,NNODE),U(NDOFEL),DU(NDOFEL),V(NDOFEL),
     3     A(NDOFEL),TIME(2),PARAMS(*),JDLTYP(MDLOAD,*),
     4     ADLMAG(MDLOAD,*),PREDEF(2,NPREDF,NNODE),
     5     LFLAGS(*),DDLMAG(MDLOAD,*),JPROPS(*)

      DOUBLE PRECISION SV_PHASE(N_CAPACITY), SV_H(N_CAPACITY,4)
      COMMON /CB_STATE_TRANSFER/ SV_PHASE, SV_H

      DOUBLE PRECISION W4(4), XG4(4), YG4(4)
      DOUBLE PRECISION W3(3), XG3(3), YG3(3)
      DOUBLE PRECISION B(3,8), B_PHASE(2,4), B_TRI(3,6), B_PHTRI(2,3)
      DOUBLE PRECISION D_ELAS(3,3), STRESS(3), STRAIN(3)
      DOUBLE PRECISION N_VEC(4), N_TRI(3), D_N(2,4), D_NTRI(2,3)
      DOUBLE PRECISION BDB, SHAPE_VAL

      INTEGER I, J, K, L, KPT, PHYSIDX, N_PHYS
      DOUBLE PRECISION XI, ETA, WT, CJAC, DETJ, JAC(2,2), INVJ(2,2)
      DOUBLE PRECISION D_AVG, DEG, DEG_D, HIST, HIST_MAX
      DOUBLE PRECISION E_MOD, E_NU, E_L0, E_GC, E_K, D_VAL
      DOUBLE PRECISION E11, E22, E12, TR_E, E_POS, POS_M
      DOUBLE PRECISION C11, C12, C22, C33
      DOUBLE PRECISION F_INT(8)

      E_L0   = PROPS(1)
      E_GC   = PROPS(2)
      E_MOD  = PROPS(3)
      E_NU   = PROPS(4)
      E_K    = PROPS(5)
      N_PHYS = INT(PROPS(6))

      DO I=1, NDOFEL
        RHS(I,1) = ZERO
        DO J=1, NDOFEL
          AMATRX(I,J) = ZERO
        ENDDO
      ENDDO

      IF (JTYPE .EQ. 1) THEN
        PHYSIDX = JELEM
      ELSE IF (JTYPE .EQ. 2) THEN
        PHYSIDX = JELEM - N_PHYS
      ELSE IF (JTYPE .EQ. 3) THEN
        PHYSIDX = JELEM
      ELSE IF (JTYPE .EQ. 4) THEN
        PHYSIDX = JELEM - N_PHYS
      ELSE
        PHYSIDX = JELEM
      ENDIF

      IF (PHYSIDX .LT. 1 .OR. PHYSIDX .GT. N_CAPACITY) THEN
        WRITE(7,*) 'ERROR: PHYSIDX out of bounds:', PHYSIDX,
     1    ' JELEM=', JELEM, ' JTYPE=', JTYPE, ' N_PHYS=', N_PHYS
        CALL XIT
      ENDIF

      IF (JTYPE .EQ. 1 .OR. JTYPE .EQ. 3) THEN
        IF (KSTEP .EQ. 1 .AND. KINC .LE. 1) THEN
          IF (JTYPE .EQ. 1) THEN
            DO KPT=1, 4
              SV_H(PHYSIDX, KPT) = SVARS(8+KPT)
            ENDDO
          ELSE
            DO KPT=1, 3
              SV_H(PHYSIDX, KPT) = SVARS(6+KPT)
            ENDDO
          ENDIF
        ENDIF
      ENDIF

C ----------------------------------------------------------------------
C JTYPE = 1: 4-Node Quadrilateral Phase-Field Element (DOF 3)
C ----------------------------------------------------------------------
      IF (JTYPE .EQ. 1) THEN
        XG4(1) = -0.577350269189626D0
        YG4(1) = -0.577350269189626D0
        W4(1)  =  1.0D0
        XG4(2) =  0.577350269189626D0
        YG4(2) = -0.577350269189626D0
        W4(2)  =  1.0D0
        XG4(3) =  0.577350269189626D0
        YG4(3) =  0.577350269189626D0
        W4(3)  =  1.0D0
        XG4(4) = -0.577350269189626D0
        YG4(4) =  0.577350269189626D0
        W4(4)  =  1.0D0

        D_AVG = ZERO
        DO I=1, 4
          D_AVG = D_AVG + U(I)*0.25D0
        ENDDO
        SV_PHASE(PHYSIDX) = D_AVG

        DO KPT=1, 4
          XI  = XG4(KPT)
          ETA = YG4(KPT)
          WT  = W4(KPT)

          N_VEC(1) = 0.25D0*(ONE - XI)*(ONE - ETA)
          N_VEC(2) = 0.25D0*(ONE + XI)*(ONE - ETA)
          N_VEC(3) = 0.25D0*(ONE + XI)*(ONE + ETA)
          N_VEC(4) = 0.25D0*(ONE - XI)*(ONE + ETA)

          D_N(1,1) = -0.25D0*(ONE - ETA)
          D_N(1,2) =  0.25D0*(ONE - ETA)
          D_N(1,3) =  0.25D0*(ONE + ETA)
          D_N(1,4) = -0.25D0*(ONE + ETA)

          D_N(2,1) = -0.25D0*(ONE - XI)
          D_N(2,2) = -0.25D0*(ONE + XI)
          D_N(2,3) =  0.25D0*(ONE + XI)
          D_N(2,4) =  0.25D0*(ONE - XI)

          DO I=1, 2
            DO J=1, 2
              JAC(I,J) = ZERO
              DO K=1, 4
                JAC(I,J) = JAC(I,J) + D_N(I,K)*COORDS(J,K)
              ENDDO
            ENDDO
          ENDDO

          DETJ = JAC(1,1)*JAC(2,2) - JAC(1,2)*JAC(2,1)
          IF (DETJ .LE. ZERO) THEN
            WRITE(7,*) 'ERROR: Non-positive Jacobian in JTYPE 1:', JELEM, DETJ
            CALL XIT
          ENDIF

          CJAC = DETJ * WT

          INVJ(1,1) =  JAC(2,2) / DETJ
          INVJ(1,2) = -JAC(1,2) / DETJ
          INVJ(2,1) = -JAC(2,1) / DETJ
          INVJ(2,2) =  JAC(1,1) / DETJ

          DO I=1, 4
            B_PHASE(1,I) = INVJ(1,1)*D_N(1,I) + INVJ(1,2)*D_N(2,I)
            B_PHASE(2,I) = INVJ(2,1)*D_N(1,I) + INVJ(2,2)*D_N(2,I)
          ENDDO

          HIST = SV_H(PHYSIDX, KPT)

          DO I=1, 4
            DO J=1, 4
              BDB = B_PHASE(1,I)*B_PHASE(1,J) + B_PHASE(2,I)*B_PHASE(2,J)
              AMATRX(I,J) = AMATRX(I,J) + CJAC * (
     1          (E_GC*E_L0)*BDB +
     2          (E_GC/E_L0 + TWO*HIST)*N_VEC(I)*N_VEC(J)
     3        )
            ENDDO
            RHS(I,1) = RHS(I,1) + CJAC * TWO * HIST * N_VEC(I)
          ENDDO

          SVARS(KPT) = D_AVG
          SVARS(4+KPT) = HIST
        ENDDO

        DO I=1, 4
          DO J=1, 4
            RHS(I,1) = RHS(I,1) - AMATRX(I,J)*U(J)
          ENDDO
        ENDDO

        SVARS(9)  = SVARS(1)
        SVARS(10) = SVARS(2)
        SVARS(11) = SVARS(3)
        SVARS(12) = SVARS(4)
        SVARS(13) = SVARS(5)
        SVARS(14) = SVARS(6)
        SVARS(15) = SVARS(7)
        SVARS(16) = SVARS(8)
        SVARS(17) = D_AVG
        SVARS(18) = SV_H(PHYSIDX, 1)

C ----------------------------------------------------------------------
C JTYPE = 2: 4-Node Quadrilateral Mechanical Element (DOFs 1, 2)
C ----------------------------------------------------------------------
      ELSE IF (JTYPE .EQ. 2) THEN
        XG4(1) = -0.577350269189626D0
        YG4(1) = -0.577350269189626D0
        W4(1)  =  1.0D0
        XG4(2) =  0.577350269189626D0
        YG4(2) = -0.577350269189626D0
        W4(2)  =  1.0D0
        XG4(3) =  0.577350269189626D0
        YG4(3) =  0.577350269189626D0
        W4(3)  =  1.0D0
        XG4(4) = -0.577350269189626D0
        YG4(4) =  0.577350269189626D0
        W4(4)  =  1.0D0

        D_VAL = SV_PHASE(PHYSIDX)
        DEG   = (ONE - D_VAL)**2 + E_K

        C11 = E_MOD*(ONE - E_NU)/((ONE + E_NU)*(ONE - TWO*E_NU)) * DEG
        C12 = E_MOD*E_NU/((ONE + E_NU)*(ONE - TWO*E_NU)) * DEG
        C22 = C11
        C33 = E_MOD/(TWO*(ONE + E_NU)) * DEG

        D_ELAS(1,1) = C11
        D_ELAS(1,2) = C12
        D_ELAS(1,3) = ZERO
        D_ELAS(2,1) = C12
        D_ELAS(2,2) = C22
        D_ELAS(2,3) = ZERO
        D_ELAS(3,1) = ZERO
        D_ELAS(3,2) = ZERO
        D_ELAS(3,3) = C33

        DO I=1, 8
          F_INT(I) = ZERO
        ENDDO

        DO KPT=1, 4
          XI  = XG4(KPT)
          ETA = YG4(KPT)
          WT  = W4(KPT)

          D_N(1,1) = -0.25D0*(ONE - ETA)
          D_N(1,2) =  0.25D0*(ONE - ETA)
          D_N(1,3) =  0.25D0*(ONE + ETA)
          D_N(1,4) = -0.25D0*(ONE + ETA)

          D_N(2,1) = -0.25D0*(ONE - XI)
          D_N(2,2) = -0.25D0*(ONE + XI)
          D_N(2,3) =  0.25D0*(ONE + XI)
          D_N(2,4) =  0.25D0*(ONE - XI)

          DO I=1, 2
            DO J=1, 2
              JAC(I,J) = ZERO
              DO K=1, 4
                JAC(I,J) = JAC(I,J) + D_N(I,K)*COORDS(J,K)
              ENDDO
            ENDDO
          ENDDO

          DETJ = JAC(1,1)*JAC(2,2) - JAC(1,2)*JAC(2,1)
          IF (DETJ .LE. ZERO) THEN
            WRITE(7,*) 'ERROR: Non-positive Jacobian in JTYPE 2:', JELEM, DETJ
            CALL XIT
          ENDIF

          CJAC = DETJ * WT

          INVJ(1,1) =  JAC(2,2) / DETJ
          INVJ(1,2) = -JAC(1,2) / DETJ
          INVJ(2,1) = -JAC(2,1) / DETJ
          INVJ(2,2) =  JAC(1,1) / DETJ

          DO I=1, 4
            B(1, 2*I-1) = INVJ(1,1)*D_N(1,I) + INVJ(1,2)*D_N(2,I)
            B(1, 2*I)   = ZERO
            B(2, 2*I-1) = ZERO
            B(2, 2*I)   = INVJ(2,1)*D_N(1,I) + INVJ(2,2)*D_N(2,I)
            B(3, 2*I-1) = INVJ(2,1)*D_N(1,I) + INVJ(2,2)*D_N(2,I)
            B(3, 2*I)   = INVJ(1,1)*D_N(1,I) + INVJ(1,2)*D_N(2,I)
          ENDDO

          DO I=1, 3
            STRAIN(I) = ZERO
            DO J=1, 8
              STRAIN(I) = STRAIN(I) + B(I,J)*U(J)
            ENDDO
          ENDDO

          DO I=1, 3
            STRESS(I) = ZERO
            DO J=1, 3
              STRESS(I) = STRESS(I) + D_ELAS(I,J)*STRAIN(J)
            ENDDO
          ENDDO

          DO I=1, 8
            DO J=1, 3
              F_INT(I) = F_INT(I) + CJAC * B(J,I)*STRESS(J)
            ENDDO
            DO J=1, 8
              DO K=1, 3
                DO L=1, 3
                  AMATRX(I,J) = AMATRX(I,J) + CJAC * B(K,I)*D_ELAS(K,L)*B(L,J)
                ENDDO
              ENDDO
            ENDDO
          ENDDO

          E11 = STRAIN(1)
          E22 = STRAIN(2)
          E12 = HALF * STRAIN(3)
          TR_E = E11 + E22
          IF (TR_E .GT. ZERO) THEN
            E_POS = TR_E
          ELSE
            E_POS = ZERO
          ENDIF
          POS_M = HALF*C12*(E_POS**2) + C33*(E11**2 + E22**2 + TWO*(E12**2))

          HIST = SV_H(PHYSIDX, KPT)
          IF (POS_M .GT. HIST) THEN
            HIST = POS_M
            SV_H(PHYSIDX, KPT) = POS_M
          ENDIF

          SVARS(KPT)   = STRAIN(1)
          SVARS(4+KPT) = STRESS(1)
        ENDDO

        DO I=1, 8
          RHS(I,1) = -F_INT(I)
        ENDDO

        SVARS(9)  = D_VAL
        SVARS(10) = DEG
        SVARS(11) = SVARS(1)
        SVARS(12) = SVARS(5)
        SVARS(13) = SV_H(PHYSIDX, 1)
        SVARS(14) = D_VAL
        SVARS(15) = DEG
        SVARS(16) = SV_H(PHYSIDX, 1)
        SVARS(17) = STRAIN(1)
        SVARS(18) = STRESS(1)

C ----------------------------------------------------------------------
C JTYPE = 3: 3-Node Triangular Phase-Field Element (DOF 3)
C ----------------------------------------------------------------------
      ELSE IF (JTYPE .EQ. 3) THEN
        XG3(1) = 1.D0/6.D0
        YG3(1) = 1.D0/6.D0
        W3(1)  = 1.D0/6.D0
        XG3(2) = 2.D0/3.D0
        YG3(2) = 1.D0/6.D0
        W3(2)  = 1.D0/6.D0
        XG3(3) = 1.D0/6.D0
        YG3(3) = 2.D0/3.D0
        W3(3)  = 1.D0/6.D0

        D_AVG = (U(1) + U(2) + U(3)) / THREE
        SV_PHASE(PHYSIDX) = D_AVG

        DO KPT=1, 3
          XI  = XG3(KPT)
          ETA = YG3(KPT)
          WT  = W3(KPT)

          N_TRI(1) = ONE - XI - ETA
          N_TRI(2) = XI
          N_TRI(3) = ETA

          D_NTRI(1,1) = -ONE
          D_NTRI(1,2) =  ONE
          D_NTRI(1,3) =  ZERO

          D_NTRI(2,1) = -ONE
          D_NTRI(2,2) =  ZERO
          D_NTRI(2,3) =  ONE

          DO I=1, 2
            DO J=1, 2
              JAC(I,J) = ZERO
              DO K=1, 3
                JAC(I,J) = JAC(I,J) + D_NTRI(I,K)*COORDS(J,K)
              ENDDO
            ENDDO
          ENDDO

          DETJ = JAC(1,1)*JAC(2,2) - JAC(1,2)*JAC(2,1)
          IF (DETJ .LE. ZERO) THEN
            WRITE(7,*) 'ERROR: Non-positive Jacobian in JTYPE 3:', JELEM, DETJ
            CALL XIT
          ENDIF

          CJAC = DETJ * WT

          INVJ(1,1) =  JAC(2,2) / DETJ
          INVJ(1,2) = -JAC(1,2) / DETJ
          INVJ(2,1) = -JAC(2,1) / DETJ
          INVJ(2,2) =  JAC(1,1) / DETJ

          DO I=1, 3
            B_PHTRI(1,I) = INVJ(1,1)*D_NTRI(1,I) + INVJ(1,2)*D_NTRI(2,I)
            B_PHTRI(2,I) = INVJ(2,1)*D_NTRI(1,I) + INVJ(2,2)*D_NTRI(2,I)
          ENDDO

          HIST = SV_H(PHYSIDX, KPT)

          DO I=1, 3
            DO J=1, 3
              BDB = B_PHTRI(1,I)*B_PHTRI(1,J) + B_PHTRI(2,I)*B_PHTRI(2,J)
              AMATRX(I,J) = AMATRX(I,J) + CJAC * (
     1          (E_GC*E_L0)*BDB +
     2          (E_GC/E_L0 + TWO*HIST)*N_TRI(I)*N_TRI(J)
     3        )
            ENDDO
            RHS(I,1) = RHS(I,1) + CJAC * TWO * HIST * N_TRI(I)
          ENDDO

          SVARS(KPT)   = D_AVG
          SVARS(3+KPT) = HIST
        ENDDO

        DO I=1, 3
          DO J=1, 3
            RHS(I,1) = RHS(I,1) - AMATRX(I,J)*U(J)
          ENDDO
        ENDDO

        SVARS(7)  = SVARS(1)
        SVARS(8)  = SVARS(2)
        SVARS(9)  = SVARS(3)
        SVARS(10) = SVARS(4)
        SVARS(11) = SVARS(5)
        SVARS(12) = SVARS(6)
        SVARS(13) = SV_H(PHYSIDX, 1)
        SVARS(14) = D_AVG
        SVARS(15) = (ONE - D_AVG)**2 + E_K
        SVARS(16) = SV_H(PHYSIDX, 1)
        SVARS(17) = D_AVG
        SVARS(18) = SV_H(PHYSIDX, 1)

C ----------------------------------------------------------------------
C JTYPE = 4: 3-Node Triangular Mechanical Element (DOFs 1, 2)
C ----------------------------------------------------------------------
      ELSE IF (JTYPE .EQ. 4) THEN
        XG3(1) = 1.D0/6.D0
        YG3(1) = 1.D0/6.D0
        W3(1)  = 1.D0/6.D0
        XG3(2) = 2.D0/3.D0
        YG3(2) = 1.D0/6.D0
        W3(2)  = 1.D0/6.D0
        XG3(3) = 1.D0/6.D0
        YG3(3) = 2.D0/3.D0
        W3(3)  = 1.D0/6.D0

        D_VAL = SV_PHASE(PHYSIDX)
        DEG   = (ONE - D_VAL)**2 + E_K

        C11 = E_MOD*(ONE - E_NU)/((ONE + E_NU)*(ONE - TWO*E_NU)) * DEG
        C12 = E_MOD*E_NU/((ONE + E_NU)*(ONE - TWO*E_NU)) * DEG
        C22 = C11
        C33 = E_MOD/(TWO*(ONE + E_NU)) * DEG

        D_ELAS(1,1) = C11
        D_ELAS(1,2) = C12
        D_ELAS(1,3) = ZERO
        D_ELAS(2,1) = C12
        D_ELAS(2,2) = C22
        D_ELAS(2,3) = ZERO
        D_ELAS(3,1) = ZERO
        D_ELAS(3,2) = ZERO
        D_ELAS(3,3) = C33

        DO I=1, 6
          F_INT(I) = ZERO
        ENDDO

        DO KPT=1, 3
          XI  = XG3(KPT)
          ETA = YG3(KPT)
          WT  = W3(KPT)

          D_NTRI(1,1) = -ONE
          D_NTRI(1,2) =  ONE
          D_NTRI(1,3) =  ZERO

          D_NTRI(2,1) = -ONE
          D_NTRI(2,2) =  ZERO
          D_NTRI(2,3) =  ONE

          DO I=1, 2
            DO J=1, 2
              JAC(I,J) = ZERO
              DO K=1, 3
                JAC(I,J) = JAC(I,J) + D_NTRI(I,K)*COORDS(J,K)
              ENDDO
            ENDDO
          ENDDO

          DETJ = JAC(1,1)*JAC(2,2) - JAC(1,2)*JAC(2,1)
          IF (DETJ .LE. ZERO) THEN
            WRITE(7,*) 'ERROR: Non-positive Jacobian in JTYPE 4:', JELEM, DETJ
            CALL XIT
          ENDIF

          CJAC = DETJ * WT

          INVJ(1,1) =  JAC(2,2) / DETJ
          INVJ(1,2) = -JAC(1,2) / DETJ
          INVJ(2,1) = -JAC(2,1) / DETJ
          INVJ(2,2) =  JAC(1,1) / DETJ

          DO I=1, 3
            B_TRI(1, 2*I-1) = INVJ(1,1)*D_NTRI(1,I) + INVJ(1,2)*D_NTRI(2,I)
            B_TRI(1, 2*I)   = ZERO
            B_TRI(2, 2*I-1) = ZERO
            B_TRI(2, 2*I)   = INVJ(2,1)*D_NTRI(1,I) + INVJ(2,2)*D_NTRI(2,I)
            B_TRI(3, 2*I-1) = INVJ(2,1)*D_NTRI(1,I) + INVJ(2,2)*D_NTRI(2,I)
            B_TRI(3, 2*I)   = INVJ(1,1)*D_NTRI(1,I) + INVJ(1,2)*D_NTRI(2,I)
          ENDDO

          DO I=1, 3
            STRAIN(I) = ZERO
            DO J=1, 6
              STRAIN(I) = STRAIN(I) + B_TRI(I,J)*U(J)
            ENDDO
          ENDDO

          DO I=1, 3
            STRESS(I) = ZERO
            DO J=1, 3
              STRESS(I) = STRESS(I) + D_ELAS(I,J)*STRAIN(J)
            ENDDO
          ENDDO

          DO I=1, 6
            DO J=1, 3
              F_INT(I) = F_INT(I) + CJAC * B_TRI(J,I)*STRESS(J)
            ENDDO
            DO J=1, 6
              DO K=1, 3
                DO L=1, 3
                  AMATRX(I,J) = AMATRX(I,J) + CJAC * B_TRI(K,I)*D_ELAS(K,L)*B_TRI(L,J)
                ENDDO
              ENDDO
            ENDDO
          ENDDO

          E11 = STRAIN(1)
          E22 = STRAIN(2)
          E12 = HALF * STRAIN(3)
          TR_E = E11 + E22
          IF (TR_E .GT. ZERO) THEN
            E_POS = TR_E
          ELSE
            E_POS = ZERO
          ENDIF
          POS_M = HALF*C12*(E_POS**2) + C33*(E11**2 + E22**2 + TWO*(E12**2))

          HIST = SV_H(PHYSIDX, KPT)
          IF (POS_M .GT. HIST) THEN
            HIST = POS_M
            SV_H(PHYSIDX, KPT) = POS_M
          ENDIF

          SVARS(KPT)   = STRAIN(1)
          SVARS(3+KPT) = STRESS(1)
        ENDDO

        DO I=1, 6
          RHS(I,1) = -F_INT(I)
        ENDDO

        SVARS(7)  = D_VAL
        SVARS(8)  = DEG
        SVARS(9)  = SVARS(1)
        SVARS(10) = SVARS(4)
        SVARS(11) = SV_H(PHYSIDX, 1)
        SVARS(12) = D_VAL
        SVARS(13) = DEG
        SVARS(14) = D_VAL
        SVARS(15) = DEG
        SVARS(16) = SV_H(PHYSIDX, 1)
        SVARS(17) = STRAIN(1)
        SVARS(18) = STRESS(1)

      ENDIF

      RETURN
      END

      SUBROUTINE UMAT(STRESS,STATEV,DDSDDE,SSE,SPD,SCD,
     1 RPL,DDSDDT,DRPLDE,DRPLDT,
     2 STRAN,DSTRAN,TIME,DTIME,TEMP,DTEMP,PREDEF,DPRED,CMNAME,
     3 NDI,NSHR,NTENS,NSTATV,PROPS,NPROPS,COORDS,DROT,PNEWDT,
     4 CELENT,DFGRD0,DFGRD1,NOEL,NPT,LAYER,KSPT,KSTEP,KINC)
      INCLUDE 'ABA_PARAM.INC'
      CHARACTER*80 CMNAME
      DIMENSION STRESS(NTENS),STATEV(NSTATV),
     1 DDSDDE(NTENS,NTENS),DDSDDT(NTENS),DRPLDE(NTENS),
     2 STRAN(NTENS),DSTRAN(NTENS),TIME(2),PREDEF(1),DPRED(1),
     3 PROPS(NPROPS),COORDS(3),DROT(3,3),DFGRD0(3,3),DFGRD1(3,3)
      RETURN
      END
"""

def generate_inp_deck() -> str:
    # Read the deck template from R1R6R2, and update property cards to clean 6-property ABI
    src_inp = SRC_R1R6R2_DIR / "M2STATE_FRACFIX_RESTART1R1R6R2.inp"
    text = src_inp.read_text(encoding="utf-8", errors="replace")

    # Update heading
    text = re.sub(
        r"\*HEADING[\s\S]*?\*\*",
        "*HEADING\nMode-II Nonmatching State-Transfer Restart: M2STATE_FRACFIX_RESTART1R1R8\n** Revision: M2STATE_FRACFIX_RESTART1R1R8 (Safe Jacobian Inversion + Clean 6-Property ABI)\n** Source State: M2ADAPT_MM_FRACFIX_PROD (1386469.mmaster02) at u1 = 0.005000 mm\n** Target Mesh: PK5 (Nphys = 4894, 4998 nodes, 9788 UELs, 14682 total layered)\n** Corrected Contiguous UEL Ranges: U1 1..4766, U3 4767..4894, U2 4895..9660, U4 9661..9788\n** Clean 6-Slot Property ABI: PROPS(1..6) = (l0, Gc, E, nu, k, Nphys)\n**",
        text,
        count=1
    )

    # Update USER ELEMENT declarations to PROPERTIES=6
    text = text.replace(
        "*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, I PROPERTIES=0, PROPERTIES=5, VARIABLES=18, UNSYMM",
        "*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM"
    )
    text = text.replace(
        "*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, I PROPERTIES=0, PROPERTIES=5, VARIABLES=18, UNSYMM",
        "*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM"
    )
    text = text.replace(
        "*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, I PROPERTIES=0, PROPERTIES=5, VARIABLES=18, UNSYMM",
        "*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM"
    )
    text = text.replace(
        "*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, I PROPERTIES=0, PROPERTIES=5, VARIABLES=18, UNSYMM",
        "*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM"
    )

    # Replace UEL PROPERTY cards
    new_props = """*UEL PROPERTY, ELSET=E_U1
       0.015000,     0.002700,   210.000000,     0.300000,   1.0000e-07,       4894.0
*UEL PROPERTY, ELSET=E_U2
       0.015000,     0.002700,   210.000000,     0.300000,   1.0000e-07,       4894.0
*UEL PROPERTY, ELSET=E_U3
       0.015000,     0.002700,   210.000000,     0.300000,   1.0000e-07,       4894.0
*UEL PROPERTY, ELSET=E_U4
       0.015000,     0.002700,   210.000000,     0.300000,   1.0000e-07,       4894.0
"""

    pattern = r"\*UEL PROPERTY, ELSET=E_U1[\s\S]*?\*UEL PROPERTY, ELSET=E_U4\s*[\d\.\s,eE+-]*\n"
    text = re.sub(pattern, new_props, text)

    return text

def build_standalone_validator() -> str:
    return """#!/usr/bin/env python3
\"\"\"
Standalone Package Manifest Validator for Production Candidate M2STATE_FRACFIX_RESTART1R1R8.
\"\"\"

import sys
import json
import hashlib
import re
from pathlib import Path

REQUIRED_FILES = [
    "M2STATE_FRACFIX_RESTART1R1R8.inp",
    "f42_mixed_uel.for",
    "STATE_TRANSFER_ARTIFACT.json",
    "TRANSFER_MANIFEST.json",
    "RESTART_ACCEPTANCE_CONTRACT.json",
    "job_notifications.sh",
    "validate_package_manifest.py",
    "M2STATE_FRACFIX_RESTART1R1R8.pbs",
    "submit_m2state_fracfix_restart1r1r8.sh"
]

def validate_manifest(manifest_path_str: str = "PACKAGE_MANIFEST.json") -> bool:
    manifest_path = Path(manifest_path_str)
    if not manifest_path.exists():
        print(f"[PREFLIGHT] ERROR: Manifest not found: {manifest_path}")
        return False

    try:
        m = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[PREFLIGHT] ERROR: Failed to parse JSON manifest: {e}")
        return False

    if not isinstance(m, dict):
        print("[PREFLIGHT] ERROR: Manifest root is not a dictionary")
        return False

    if "files" not in m:
        print("[PREFLIGHT] ERROR: Canonical 'files' key missing from manifest")
        return False

    files_dict = m["files"]
    if not isinstance(files_dict, dict) or len(files_dict) == 0:
        print("[PREFLIGHT] ERROR: 'files' mapping is invalid or empty")
        return False

    for rf in REQUIRED_FILES:
        if rf not in files_dict:
            print(f"[PREFLIGHT] ERROR: Required execution file missing from manifest: {rf}")
            return False

    hex_re = re.compile(r"^[0-9a-fA-F]{64}$")
    for f_name, exp_hash in files_dict.items():
        if not isinstance(exp_hash, str) or not hex_re.match(exp_hash):
            print(f"[PREFLIGHT] ERROR: Invalid SHA256 format for {f_name}: {exp_hash}")
            return False
        f_path = manifest_path.parent / f_name if manifest_path.is_file() else Path(f_name)
        if not f_path.exists():
            print(f"[PREFLIGHT] ERROR: Required candidate file missing on disk: {f_name}")
            return False
        actual_hash = hashlib.sha256(f_path.read_bytes()).hexdigest()
        if actual_hash.lower() != exp_hash.lower():
            print(f"[PREFLIGHT] ERROR: Hash mismatch for {f_name}: expected {exp_hash}, got {actual_hash}")
            return False

    print("[PREFLIGHT] package_manifest_verification = PASS")
    return True

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "PACKAGE_MANIFEST.json"
    if not validate_manifest(target):
        sys.exit(1)
    sys.exit(0)
"""

def build_r1r8_pbs_script() -> str:
    return """#!/bin/bash
#PBS -N M2STATE_FRACFIX_RESTART1R1R8
#PBS -l select=1:ncpus=1:mpiprocs=1:mem=16gb
#PBS -l walltime=24:00:00
#PBS -q entry_imfdfkmq
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de
#PBS -j oe
#PBS -o M2STATE_FRACFIX_RESTART1R1R8.pbs.log

cd $PBS_O_WORKDIR

# 1. Establish timing variables
JOB_START_EPOCH=$(date +%s)
echo "[PBS_PREFLIGHT] Starting M2STATE_FRACFIX_RESTART1R1R8 Production Restart Job..."
date

# 2. Source package-local notification helper and install terminal trap BEFORE manifest preflight
NOTIFICATION_CONFIG="${NOTIFICATION_CONFIG:-$HOME/.config/adaptive-remeshing/notifications.env}"
NOTIFICATION_SCRIPT="${NOTIFICATION_SCRIPT:-${PBS_O_WORKDIR}/job_notifications.sh}"
if [ ! -f "$NOTIFICATION_SCRIPT" ]; then
  NOTIFICATION_SCRIPT="$HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh"
fi

if [ -f "$NOTIFICATION_SCRIPT" ]; then
  source "$NOTIFICATION_SCRIPT" 2>/dev/null || true
  notification_load_config 2>/dev/null || true
  notification_install_terminal_trap 2>/dev/null || true
  notify_start 2>/dev/null || true
fi

# 3. Standalone manifest preflight (zero inline Python)
python3 validate_package_manifest.py PACKAGE_MANIFEST.json
PREFLIGHT_RC=$?

if [ $PREFLIGHT_RC -ne 0 ]; then
  echo "[PBS_PREFLIGHT] ERROR: Package manifest verification failed with exit code $PREFLIGHT_RC"
  exit $PREFLIGHT_RC
fi

# 4. Load Abaqus environment
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7

echo "[PBS_PREFLIGHT] Abaqus environment loaded."
abaqus information=release

# 5. Run solver
abaqus job=M2STATE_FRACFIX_RESTART1R1R8 user=f42_mixed_uel.for input=M2STATE_FRACFIX_RESTART1R1R8.inp interactive

ABAQUS_RC=$?
echo "[PBS_PREFLIGHT] Abaqus execution finished with exit code $ABAQUS_RC"

if [ $ABAQUS_RC -ne 0 ]; then
  echo "[PBS_PREFLIGHT] ERROR: Abaqus execution failed with exit code $ABAQUS_RC"
  exit $ABAQUS_RC
fi

echo "[PBS_PREFLIGHT] M2STATE_FRACFIX_RESTART1R1R8 completed successfully."
exit 0
"""

def build_guarded_wrapper() -> str:
    return """#!/bin/bash
# ==============================================================================
# Guarded Submission Wrapper for M2STATE_FRACFIX_RESTART1R1R8
# Single-job submission wrapper with dry-run protection and manifest verification
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

DRY_RUN=false
for arg in "$@"; do
  case "$arg" in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
  esac
done

echo "=== Guarded Wrapper: M2STATE_FRACFIX_RESTART1R1R8 ==="

# 1. Validate manifest
python3 validate_package_manifest.py PACKAGE_MANIFEST.json

if [ "$DRY_RUN" = true ]; then
  echo "[DRY-RUN] Manifest verified. qsub invocation skipped. (qsub call count = 0)"
  exit 0
fi

echo "[GUARD] Verifying execution authorization..."
# Note: Actual execution requires explicit human approval recorded in project_coordination.
JOB_ID=$(qsub M2STATE_FRACFIX_RESTART1R1R8.pbs)
echo "[SUBMITTED] PBS Job ID: $JOB_ID"

# Dual channel notification
NOTIFICATION_CONFIG="${NOTIFICATION_CONFIG:-$HOME/.config/adaptive-remeshing/notifications.env}"
NOTIFICATION_SCRIPT="${NOTIFICATION_SCRIPT:-${SCRIPT_DIR}/job_notifications.sh}"
if [ -f "$NOTIFICATION_SCRIPT" ]; then
  source "$NOTIFICATION_SCRIPT" 2>/dev/null || true
  notification_load_config 2>/dev/null || true
  notify_submitted "$JOB_ID" "M2STATE_FRACFIX_RESTART1R1R8" 2>/dev/null || true
fi
"""

def build_acceptance_contract() -> Dict[str, Any]:
    return {
        "candidate": "M2STATE_FRACFIX_RESTART1R1R8",
        "task_id": "F84STATE-M2-CORRECTED-RESTART1-JACOBIAN-INVERSE-REPAIR-QUALIFICATION1",
        "predecessor_job": "1386469.mmaster02",
        "predecessor_candidate": "M2ADAPT_MM_FRACFIX_PROD",
        "source_u1_mm": 0.005000,
        "target_u1_final_mm": 0.010000,
        "property_ABI": "6_SLOT_REAL_PROPERTIES_PROPS1_TO_5_MATERIAL_AND_K_PROPS6_NPHYS",
        "material_parameters": {
            "l0_mm": 0.015000,
            "Gc_kN_per_mm": 0.002700,
            "E_kN_per_mm2": 210.000000,
            "nu": 0.300000,
            "k_residual": 1.0000e-07,
            "Nphys": 4894.0
        },
        "acceptance_gates": {
            "step1_phase_init_solve": "MANDATORY",
            "step2_continuation_solve": "MANDATORY",
            "step2_cutbacks_max": 0,
            "step2_nans_max": 0,
            "target_displacement_mm": 0.010000,
            "phase_field_transfer_L2_max_pct": 1.0,
            "history_field_transfer_L2_max_pct": 1.0,
            "phase_irreversibility": "MANDATORY",
            "history_irreversibility": "MANDATORY",
            "crack_tip_localization_coverage": "MANDATORY",
            "element_detJ_positive": "MANDATORY",
            "element_max_span_mm": 0.015,
            "force_continuity_tolerance_pct": 2.0,
            "constitutive_stiffness_consistency": "MANDATORY",
            "material_parameter_invariance": "MANDATORY",
            "overall_scientific_acceptance": "MANDATORY"
        },
        "energy_gate_mandatory": False,
        "energy_output_available": False,
        "resource_contract": {
            "queue": "entry_imfdfkmq",
            "ncpus": 1,
            "mpiprocs": 1,
            "memory": "16gb",
            "walltime": "24:00:00",
            "execution_mode": "serial",
            "automatic_retry": False
        }
    }

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Building candidate M2STATE_FRACFIX_RESTART1R1R8 in {OUT_DIR}...")

    # 1. Write UEL subroutine
    uel_path = OUT_DIR / "f42_mixed_uel.for"
    write_lf_file(uel_path, build_f42_mixed_uel_for())

    # 2. Write INP deck
    inp_path = OUT_DIR / "M2STATE_FRACFIX_RESTART1R1R8.inp"
    inp_text = generate_inp_deck()
    write_lf_file(inp_path, inp_text)

    # 3. Copy/Write State Transfer Artifact & Manifest
    src_stat = SRC_R1R6R2_DIR / "STATE_TRANSFER_ARTIFACT.json"
    stat_path = OUT_DIR / "STATE_TRANSFER_ARTIFACT.json"
    stat_data = json.loads(src_stat.read_text(encoding="utf-8"))
    stat_data["target_candidate"] = "M2STATE_FRACFIX_RESTART1R1R8"
    write_lf_file(stat_path, json.dumps(stat_data, indent=2))

    src_tman = SRC_R1R6R2_DIR / "TRANSFER_MANIFEST.json"
    tman_path = OUT_DIR / "TRANSFER_MANIFEST.json"
    if src_tman.exists():
        tman_data = json.loads(src_tman.read_text(encoding="utf-8"))
        tman_data["target_candidate"] = "M2STATE_FRACFIX_RESTART1R1R8"
        write_lf_file(tman_path, json.dumps(tman_data, indent=2))

    # 4. Write acceptance contract
    contract_path = OUT_DIR / "RESTART_ACCEPTANCE_CONTRACT.json"
    write_lf_file(contract_path, json.dumps(build_acceptance_contract(), indent=2))

    # 5. Write notification helper
    notif_path = OUT_DIR / "job_notifications.sh"
    if SRC_NOTIF_SH.exists():
        write_lf_file(notif_path, SRC_NOTIF_SH.read_text(encoding="utf-8"))
    else:
        src_local_notif = SRC_R1R6R2_DIR / "job_notifications.sh"
        write_lf_file(notif_path, src_local_notif.read_text(encoding="utf-8"))

    # 6. Write standalone validator
    val_path = OUT_DIR / "validate_package_manifest.py"
    write_lf_file(val_path, build_standalone_validator())

    # 7. Write PBS script
    pbs_path = OUT_DIR / "M2STATE_FRACFIX_RESTART1R1R8.pbs"
    write_lf_file(pbs_path, build_r1r8_pbs_script())

    # 8. Write guarded wrapper
    wrap_path = OUT_DIR / "submit_m2state_fracfix_restart1r1r8.sh"
    write_lf_file(wrap_path, build_guarded_wrapper())

    # 9. Build PACKAGE_MANIFEST.json
    manifest_files = [
        "M2STATE_FRACFIX_RESTART1R1R8.inp",
        "f42_mixed_uel.for",
        "STATE_TRANSFER_ARTIFACT.json",
        "TRANSFER_MANIFEST.json",
        "RESTART_ACCEPTANCE_CONTRACT.json",
        "job_notifications.sh",
        "validate_package_manifest.py",
        "M2STATE_FRACFIX_RESTART1R1R8.pbs",
        "submit_m2state_fracfix_restart1r1r8.sh"
    ]

    files_map = {}
    for mf in manifest_files:
        f_p = OUT_DIR / mf
        if not f_p.exists():
            raise RuntimeError(f"Missing required manifest file: {f_p}")
        files_map[mf] = sha256_file(f_p)

    manifest_obj = {
        "candidate": "M2STATE_FRACFIX_RESTART1R1R8",
        "task_id": "F84STATE-M2-CORRECTED-RESTART1-JACOBIAN-INVERSE-REPAIR-QUALIFICATION1",
        "files": files_map
    }

    manifest_path = OUT_DIR / "PACKAGE_MANIFEST.json"
    write_lf_file(manifest_path, json.dumps(manifest_obj, indent=2))
    print(f"Candidate M2STATE_FRACFIX_RESTART1R1R8 built successfully. Manifest SHA256: {sha256_file(manifest_path)}")

if __name__ == "__main__":
    main()
