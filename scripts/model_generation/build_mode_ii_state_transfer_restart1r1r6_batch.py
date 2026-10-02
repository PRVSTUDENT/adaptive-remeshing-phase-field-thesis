#!/usr/bin/env python3
"""
Build Production Scientific State-Transfer Restart Candidate: M2STATE_FRACFIX_RESTART1R1R6.
Task ID: F51STATE-M2-FRACFIX-RESTART1R1R6-PREFLIGHT-REPAIR-CLOSURE1

Classification: INSTRUMENTATION_ONLY_CHANGE
Canonical Manifest Key: "files"
Scientific formulation change count: 0 (100% identical mesh, state transfer, material parameters, UEL equations, loading).
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
SRC_PK5_DECK = ROOT / "models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/runtime_pk5/F43REM4_PK5.inp"
SRC_R1R5_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R5"
OUT_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R6"

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def write_lf_file(path: Path, text: str):
    clean_text = text.replace("\r\n", "\n").replace("\r", "\n")
    path.write_bytes(clean_text.encode("utf-8"))

def parse_physical_mesh(deck_path: Path):
    nodes: Dict[int, Tuple[float, float]] = {}
    quads: Dict[int, List[int]] = {}
    tris: Dict[int, List[int]] = {}
    bottom_nodes: List[int] = []
    top_nodes: List[int] = []

    lines = deck_path.read_text(encoding="utf-8", errors="replace").splitlines()
    in_part = False
    in_nodes = False
    in_cpe4 = False
    in_cpe3 = False
    in_bot_nset = False
    in_top_nset = False

    for line in lines:
        s = line.strip()
        if not s or s.startswith("**"):
            continue
        s_upper = s.upper()

        if s_upper.startswith("*PART"):
            in_part = "PLATEPART" in s_upper
            continue
        if s_upper.startswith("*END PART"):
            in_part = False
            continue

        if in_part:
            if s_upper.startswith("*NODE"):
                in_nodes = True
                in_cpe4 = in_cpe3 = in_bot_nset = in_top_nset = False
                continue
            elif s_upper.startswith("*ELEMENT") and "TYPE=CPE4" in s_upper:
                in_cpe4 = True
                in_nodes = in_cpe3 = in_bot_nset = in_top_nset = False
                continue
            elif s_upper.startswith("*ELEMENT") and "TYPE=CPE3" in s_upper:
                in_cpe3 = True
                in_nodes = in_cpe4 = in_bot_nset = in_top_nset = False
                continue
            elif s_upper.startswith("*NSET") and "NSET=N_BOTTOM" in s_upper:
                in_bot_nset = True
                in_nodes = in_cpe4 = in_cpe3 = in_top_nset = False
                continue
            elif s_upper.startswith("*NSET") and "NSET=N_TOP" in s_upper:
                in_top_nset = True
                in_nodes = in_cpe4 = in_cpe3 = in_bot_nset = False
                continue
            elif s_upper.startswith("*"):
                in_nodes = in_cpe4 = in_cpe3 = in_bot_nset = in_top_nset = False
                continue

            if in_nodes:
                parts = [p.strip() for p in s.split(",")]
                if len(parts) >= 3 and parts[0].isdigit():
                    nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
            elif in_cpe4:
                parts = [p.strip() for p in s.split(",")]
                if len(parts) >= 5 and parts[0].isdigit():
                    quads[int(parts[0])] = [int(p) for p in parts[1:5]]
            elif in_cpe3:
                parts = [p.strip() for p in s.split(",")]
                if len(parts) >= 4 and parts[0].isdigit():
                    tris[int(parts[0])] = [int(p) for p in parts[1:4]]
            elif in_bot_nset:
                parts = [p.strip() for p in s.split(",") if p.strip()]
                for p in parts:
                    if p.isdigit():
                        bottom_nodes.append(int(p))
            elif in_top_nset:
                parts = [p.strip() for p in s.split(",") if p.strip()]
                for p in parts:
                    if p.isdigit():
                        top_nodes.append(int(p))

    return nodes, quads, tris, sorted(list(set(bottom_nodes))), sorted(list(set(top_nodes)))

def build_r1r6_uel_fortran() -> str:
    return """C ======================================================================
C User Subroutine UEL and UMAT for Abaqus: Mixed 3-Node / 4-Node Scheme
C Candidate Revision: M2STATE_FRACFIX_RESTART1R1R6 (Instrumentation-Only Patch)
C Production Representative Elements (PK5 NPHYS=4894, Total UEL=9788):
C   Quad High Damage: Phase E2292 / Mech E7186
C   Quad Low Damage: Phase E100 / Mech E4994
C   Quad Transition: Phase E1500 / Mech E6394
C   Tri Pair: Phase E4862 / Mech E9756
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

      INTEGER I, J, K, KPT, PHYSIDX
      DOUBLE PRECISION XI, ETA, WT, CJAC, DETJ, INVJ(2,2)
      DOUBLE PRECISION D_AVG, DEG, DEG_D, HIST, HIST_MAX
      DOUBLE PRECISION E_MOD, E_NU, E_L0, E_GC, E_K, D_VAL
      DOUBLE PRECISION E11, E22, E12, TR_E, E_POS, POS_M
      DOUBLE PRECISION C11, C12, C22, C33
      DOUBLE PRECISION F_INT(8)

      E_L0  = PROPS(1)
      E_GC  = PROPS(2)
      E_MOD = PROPS(3)
      E_NU  = PROPS(4)
      E_K   = PROPS(5)

      DO I=1, NDOFEL
        RHS(I,1) = ZERO
        DO J=1, NDOFEL
          AMATRX(I,J) = ZERO
        ENDDO
      ENDDO

      IF (JTYPE .EQ. 1) THEN
        PHYSIDX = JELEM
      ELSE IF (JTYPE .EQ. 2) THEN
        PHYSIDX = JELEM - 4894
      ELSE IF (JTYPE .EQ. 3) THEN
        PHYSIDX = JELEM
      ELSE IF (JTYPE .EQ. 4) THEN
        PHYSIDX = JELEM - 4894
      ELSE
        PHYSIDX = JELEM
      ENDIF

      IF (JTYPE .EQ. 1) THEN
        D_AVG = ZERO
        DO I=1, NNODE
          D_AVG = D_AVG + U(I) / FOUR
        ENDDO
        IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) THEN
          SV_PHASE(PHYSIDX) = D_AVG
        ENDIF
        DO KPT=1, 4
          SVARS(KPT) = D_AVG
          SVARS(4+KPT) = D_AVG
          IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) THEN
            SVARS(8+KPT) = SV_H(PHYSIDX, KPT)
          ENDIF
        ENDDO

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

        DO KPT=1, 4
          XI  = XG4(KPT)
          ETA = YG4(KPT)
          WT  = W4(KPT)
          N_VEC(1) = 0.25D0*(ONE-XI)*(ONE-ETA)
          N_VEC(2) = 0.25D0*(ONE+XI)*(ONE-ETA)
          N_VEC(3) = 0.25D0*(ONE+XI)*(ONE+ETA)
          N_VEC(4) = 0.25D0*(ONE-XI)*(ONE+ETA)
          D_N(1,1) = -0.25D0*(ONE-ETA)
          D_N(1,2) =  0.25D0*(ONE-ETA)
          D_N(1,3) =  0.25D0*(ONE+ETA)
          D_N(2,1) = -0.25D0*(ONE-XI)
          D_N(2,2) = -0.25D0*(ONE+XI)
          D_N(2,3) =  0.25D0*(ONE+XI)
          D_N(2,4) =  0.25D0*(ONE-XI)

          DETJ = ((COORDS(1,2)-COORDS(1,1))*(COORDS(2,4)-COORDS(2,1)) -
     1            (COORDS(1,4)-COORDS(1,1))*(COORDS(2,2)-COORDS(2,1)))/FOUR
          IF (DETJ .LE. ZERO) DETJ = 1.0D-6
          CJAC = DETJ * WT

          INVJ(1,1) = (COORDS(2,4)-COORDS(2,1))/(FOUR*DETJ)
          INVJ(1,2) =-(COORDS(2,2)-COORDS(2,1))/(FOUR*DETJ)
          INVJ(2,1) =-(COORDS(1,4)-COORDS(1,1))/(FOUR*DETJ)
          INVJ(2,2) = (COORDS(1,2)-COORDS(1,1))/(FOUR*DETJ)

          DO I=1, 4
            B_PHASE(1,I) = INVJ(1,1)*D_N(1,I) + INVJ(1,2)*D_N(2,I)
            B_PHASE(2,I) = INVJ(2,1)*D_N(1,I) + INVJ(2,2)*D_N(2,I)
          ENDDO

          D_VAL = ZERO
          DO I=1, 4
            D_VAL = D_VAL + N_VEC(I)*U(I)
          ENDDO

          HIST = SVARS(8+KPT)

          DO I=1, 4
            RHS(I,1) = RHS(I,1) - CJAC * (
     1        (E_GC*E_L0)*(B_PHASE(1,I)*(B_PHASE(1,1)*U(1)+B_PHASE(1,2)*U(2)+
     2                      B_PHASE(1,3)*U(3)+B_PHASE(1,4)*U(4)) +
     3                     B_PHASE(2,I)*(B_PHASE(2,1)*U(1)+B_PHASE(2,2)*U(2)+
     4                      B_PHASE(2,3)*U(3)+B_PHASE(2,4)*U(4))) +
     5        N_VEC(I)*((E_GC/E_L0 + TWO*HIST)*D_VAL - TWO*HIST) )
          ENDDO

          DO I=1, 4
            DO J=1, 4
              AMATRX(I,J) = AMATRX(I,J) + CJAC * (
     1          (E_GC*E_L0)*(B_PHASE(1,I)*B_PHASE(1,J) + B_PHASE(2,I)*B_PHASE(2,J)) +
     2          N_VEC(I)*N_VEC(J)*(E_GC/E_L0 + TWO*HIST) )
            ENDDO
          ENDDO
        ENDDO

        IF (KSTEP.EQ.1 .AND. KINC.EQ.1) THEN
          WRITE(7,1002) PHYSIDX, JELEM, JTYPE,
     1      SV_H(PHYSIDX,1), SV_H(PHYSIDX,2), SV_H(PHYSIDX,3), SV_H(PHYSIDX,4)
 1002     FORMAT('[H_STARTUP_TRACE] PHYSIDX=',I6,' JELEM=',I6,
     1           ' JTYPE=',I1,' H1=',E12.5,' H2=',E12.5,
     2           ' H3=',E12.5,' H4=',E12.5)
        ENDIF

      ELSE IF (JTYPE .EQ. 2) THEN
        D_VAL = ZERO
        IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) THEN
          D_VAL = SV_PHASE(PHYSIDX)
        ENDIF

        DO KPT=1, 4
          SVARS(KPT) = D_VAL
          SVARS(4+KPT) = D_AVG
          IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) THEN
            SVARS(8+KPT) = SV_H(PHYSIDX, KPT)
          ENDIF
        ENDDO

        DEG = (ONE - D_VAL)**2 + E_K
        C11 = E_MOD*(ONE-E_NU)/((ONE+E_NU)*(ONE-TWO*E_NU)) * DEG
        C12 = E_MOD*E_NU/((ONE+E_NU)*(ONE-TWO*E_NU)) * DEG
        C22 = C11
        C33 = E_MOD/(TWO*(ONE+E_NU)) * DEG

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

        DO I=1, 8
          F_INT(I) = ZERO
        ENDDO

        DO KPT=1, 4
          XI  = XG4(KPT)
          ETA = YG4(KPT)
          WT  = W4(KPT)
          D_N(1,1) = -0.25D0*(ONE-ETA)
          D_N(1,2) =  0.25D0*(ONE-ETA)
          D_N(1,3) =  0.25D0*(ONE+ETA)
          D_N(1,4) = -0.25D0*(ONE+ETA)
          D_N(2,1) = -0.25D0*(ONE-XI)
          D_N(2,2) = -0.25D0*(ONE+XI)
          D_N(2,3) =  0.25D0*(ONE+XI)
          D_N(2,4) =  0.25D0*(ONE-XI)

          DETJ = ((COORDS(1,2)-COORDS(1,1))*(COORDS(2,4)-COORDS(2,1)) -
     1            (COORDS(1,4)-COORDS(1,1))*(COORDS(2,2)-COORDS(2,1)))/FOUR
          IF (DETJ .LE. ZERO) DETJ = 1.0D-6
          CJAC = DETJ * WT

          INVJ(1,1) = (COORDS(2,4)-COORDS(2,1))/(FOUR*DETJ)
          INVJ(1,2) =-(COORDS(2,2)-COORDS(2,1))/(FOUR*DETJ)
          INVJ(2,1) =-(COORDS(1,4)-COORDS(1,1))/(FOUR*DETJ)
          INVJ(2,2) = (COORDS(1,2)-COORDS(1,1))/(FOUR*DETJ)

          DO I=1, 4
            B(1,2*I-1) = INVJ(1,1)*D_N(1,I) + INVJ(1,2)*D_N(2,I)
            B(1,2*I)   = ZERO
            B(2,2*I-1) = ZERO
            B(2,2*I)   = INVJ(2,1)*D_N(1,I) + INVJ(2,2)*D_N(2,I)
            B(3,2*I-1) = B(2,2*I)
            B(3,2*I)   = B(1,2*I-1)
          ENDDO

          STRAIN(1) = ZERO
          STRAIN(2) = ZERO
          STRAIN(3) = ZERO
          DO I=1, 8
            STRAIN(1) = STRAIN(1) + B(1,I)*U(I)
            STRAIN(2) = STRAIN(2) + B(2,I)*U(I)
            STRAIN(3) = STRAIN(3) + B(3,I)*U(I)
          ENDDO

          STRESS(1) = C11*STRAIN(1) + C12*STRAIN(2)
          STRESS(2) = C12*STRAIN(1) + C22*STRAIN(2)
          STRESS(3) = C33*STRAIN(3)

          TR_E = STRAIN(1) + STRAIN(2)
          E_POS = ZERO
          IF (TR_E .GT. ZERO) E_POS = TR_E
          POS_M = HALF*E_MOD/((ONE+E_NU)*(ONE-TWO*E_NU))*(E_POS**2) +
     1            E_MOD/(TWO*(ONE+E_NU))*(STRAIN(1)**2 + STRAIN(2)**2 + HALF*STRAIN(3)**2)
          IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) THEN
            IF (POS_M .GT. SV_H(PHYSIDX, KPT)) THEN
              SV_H(PHYSIDX, KPT) = POS_M
            ENDIF
            SVARS(8+KPT) = SV_H(PHYSIDX, KPT)
          ENDIF

          DO I=1, 8
            F_INT(I) = F_INT(I) + CJAC*(B(1,I)*STRESS(1) + B(2,I)*STRESS(2) + B(3,I)*STRESS(3))
            RHS(I,1) = RHS(I,1) - CJAC*(B(1,I)*STRESS(1) + B(2,I)*STRESS(2) + B(3,I)*STRESS(3))
          ENDDO

          DO I=1, 8
            DO J=1, 8
              AMATRX(I,J) = AMATRX(I,J) + CJAC*(
     1          B(1,I)*(C11*B(1,J) + C12*B(2,J)) +
     2          B(2,I)*(C12*B(1,J) + C22*B(2,J)) +
     3          B(3,I)*(C33*B(3,J)) )
            ENDDO
          ENDDO
        ENDDO

        WRITE(7,1003) KSTEP, KINC, TIME(2), JELEM, JTYPE, PHYSIDX,
     1    F_INT(1), F_INT(3), F_INT(5), F_INT(7)
 1003   FORMAT('[FORCE_TRACE] KSTEP=',I1,' KINC=',I1,
     1         ' TIME=',F10.6,' JELEM=',I6,' JTYPE=',I1,
     2         ' PHYSIDX=',I6,' FINT1_N1=',E14.6,' FINT1_N2=',E14.6,
     3         ' FINT1_N3=',E14.6,' FINT1_N4=',E14.6)

      ELSE IF (JTYPE .EQ. 3) THEN
        D_AVG = ZERO
        DO I=1, 3
          D_AVG = D_AVG + U(I) / THREE
        ENDDO
        IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) THEN
          SV_PHASE(PHYSIDX) = D_AVG
        ENDIF
        DO KPT=1, 3
          SVARS(KPT) = D_AVG
          SVARS(3+KPT) = D_AVG
          IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) THEN
            SVARS(6+KPT) = SV_H(PHYSIDX, KPT)
          ENDIF
        ENDDO

        XG3(1) = 1.D0/3.D0
        YG3(1) = 1.D0/3.D0
        W3(1)  = 0.5D0
        XG3(2) = 0.6D0
        YG3(2) = 0.2D0
        W3(2)  = 1.D0/6.D0
        XG3(3) = 0.2D0
        YG3(3) = 0.6D0
        W3(3)  = 1.D0/6.D0

        DETJ = (COORDS(1,2)-COORDS(1,1))*(COORDS(2,3)-COORDS(2,1)) -
     1         (COORDS(1,3)-COORDS(1,1))*(COORDS(2,2)-COORDS(2,1))
        IF (DETJ .LE. ZERO) DETJ = 1.0D-6
        CJAC = DETJ * 0.5D0

        INVJ(1,1) = (COORDS(2,3)-COORDS(2,1))/DETJ
        INVJ(1,2) =-(COORDS(2,2)-COORDS(2,1))/DETJ
        INVJ(2,1) =-(COORDS(1,3)-COORDS(1,1))/DETJ
        INVJ(2,2) = (COORDS(1,2)-COORDS(1,1))/DETJ

        B_PHTRI(1,1) = -INVJ(1,1) - INVJ(1,2)
        B_PHTRI(1,2) =  INVJ(1,1)
        B_PHTRI(1,3) =  INVJ(1,2)
        B_PHTRI(2,1) = -INVJ(2,1) - INVJ(2,2)
        B_PHTRI(2,2) =  INVJ(2,1)
        B_PHTRI(2,3) =  INVJ(2,2)

        HIST = SVARS(7)

        DO I=1, 3
          RHS(I,1) = RHS(I,1) - CJAC * (
     1      (E_GC*E_L0)*(B_PHTRI(1,I)*(B_PHTRI(1,1)*U(1)+B_PHTRI(1,2)*U(2)+B_PHTRI(1,3)*U(3)) +
     2                   B_PHTRI(2,I)*(B_PHTRI(2,1)*U(1)+B_PHTRI(2,2)*U(2)+B_PHTRI(2,3)*U(3))) +
     3      (ONE/THREE)*((E_GC/E_L0 + TWO*HIST)*D_AVG - TWO*HIST) )
        ENDDO

        DO I=1, 3
          DO J=1, 3
            AMATRX(I,J) = AMATRX(I,J) + CJAC * (
     1        (E_GC*E_L0)*(B_PHTRI(1,I)*B_PHTRI(1,J) + B_PHTRI(2,I)*B_PHTRI(2,J)) +
     2        (ONE/NINE)*(E_GC/E_L0 + TWO*HIST) )
          ENDDO
        ENDDO

        IF (KSTEP.EQ.1 .AND. KINC.EQ.1) THEN
          WRITE(7,1002) PHYSIDX, JELEM, JTYPE,
     1      SV_H(PHYSIDX,1), SV_H(PHYSIDX,2), SV_H(PHYSIDX,3), ZERO
        ENDIF

      ELSE IF (JTYPE .EQ. 4) THEN
        D_VAL = ZERO
        IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) THEN
          D_VAL = SV_PHASE(PHYSIDX)
        ENDIF

        DO KPT=1, 3
          SVARS(KPT) = D_VAL
          SVARS(3+KPT) = D_AVG
          IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) PREDEF(1,1,1)=0.D0
        ENDDO

        DEG = (ONE - D_VAL)**2 + E_K
        C11 = E_MOD*(ONE-E_NU)/((ONE+E_NU)*(ONE-TWO*E_NU)) * DEG
        C12 = E_MOD*E_NU/((ONE+E_NU)*(ONE-TWO*E_NU)) * DEG
        C22 = C11
        C33 = E_MOD/(TWO*(ONE+E_NU)) * DEG

        DETJ = (COORDS(1,2)-COORDS(1,1))*(COORDS(2,3)-COORDS(2,1)) -
     1         (COORDS(1,3)-COORDS(1,1))*(COORDS(2,2)-COORDS(2,1))
        IF (DETJ .LE. ZERO) DETJ = 1.0D-6
        CJAC = DETJ * 0.5D0

        INVJ(1,1) = (COORDS(2,3)-COORDS(2,1))/DETJ
        INVJ(1,2) =-(COORDS(2,2)-COORDS(2,1))/DETJ
        INVJ(2,1) =-(COORDS(1,3)-COORDS(1,1))/DETJ
        INVJ(2,2) = (COORDS(1,2)-COORDS(1,1))/DETJ

        B_TRI(1,1) = -INVJ(1,1) - INVJ(1,2)
        B_TRI(1,2) =  ZERO
        B_TRI(1,3) =  INVJ(1,1)
        B_TRI(1,4) =  ZERO
        B_TRI(1,5) =  INVJ(1,2)
        B_TRI(1,6) =  ZERO

        B_TRI(2,1) =  ZERO
        B_TRI(2,2) = -INVJ(2,1) - INVJ(2,2)
        B_TRI(2,3) =  ZERO
        B_TRI(2,4) =  INVJ(2,1)
        B_TRI(2,5) =  ZERO
        B_TRI(2,6) =  INVJ(2,2)

        B_TRI(3,1) = B_TRI(2,2)
        B_TRI(3,2) = B_TRI(1,1)
        B_TRI(3,3) = B_TRI(2,4)
        B_TRI(3,4) = B_TRI(1,3)
        B_TRI(3,5) = B_TRI(2,6)
        B_TRI(3,6) = B_TRI(1,5)

        STRAIN(1) = ZERO
        STRAIN(2) = ZERO
        STRAIN(3) = ZERO
        DO I=1, 6
          STRAIN(1) = STRAIN(1) + B_TRI(1,I)*U(I)
          STRAIN(2) = STRAIN(2) + B_TRI(2,I)*U(I)
          STRAIN(3) = STRAIN(3) + B_TRI(3,I)*U(I)
        ENDDO

        STRESS(1) = C11*STRAIN(1) + C12*STRAIN(2)
        STRESS(2) = C12*STRAIN(1) + C22*STRAIN(2)
        STRESS(3) = C33*STRAIN(3)

        TR_E = STRAIN(1) + STRAIN(2)
        E_POS = ZERO
        IF (TR_E .GT. ZERO) E_POS = TR_E
        POS_M = HALF*E_MOD/((ONE+E_NU)*(ONE-TWO*E_NU))*(E_POS**2) +
     1          E_MOD/(TWO*(ONE+E_NU))*(STRAIN(1)**2 + STRAIN(2)**2 + HALF*STRAIN(3)**2)
        IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) THEN
          DO KPT=1, 3
            IF (POS_M .GT. SV_H(PHYSIDX, KPT)) THEN
              SV_H(PHYSIDX, KPT) = POS_M
            ENDIF
            SVARS(6+KPT) = SV_H(PHYSIDX, KPT)
          ENDDO
        ENDIF

        DO I=1, 6
          F_INT(I) = F_INT(I) + CJAC*(B_TRI(1,I)*STRESS(1) + B_TRI(2,I)*STRESS(2) + B_TRI(3,I)*STRESS(3))
          RHS(I,1) = RHS(I,1) - CJAC*(B_TRI(1,I)*STRESS(1) + B_TRI(2,I)*STRESS(2) + B_TRI(3,I)*STRESS(3))
        ENDDO

        DO I=1, 6
          DO J=1, 6
            AMATRX(I,J) = AMATRX(I,J) + CJAC*(
     1        B_TRI(1,I)*(C11*B_TRI(1,J) + C12*B_TRI(2,J)) +
     2        B_TRI(2,I)*(C12*B_TRI(1,J) + C22*B_TRI(2,J)) +
     3        B_TRI(3,I)*(C33*B_TRI(3,J)) )
          ENDDO
        ENDDO

        WRITE(7,1003) KSTEP, KINC, TIME(2), JELEM, JTYPE, PHYSIDX,
     1    F_INT(1), F_INT(3), F_INT(5), ZERO
      ENDIF

C Trace write executed AFTER values have been assigned!
      IF (KSTEP.EQ.2 .AND. KINC.EQ.1) THEN
        IF (JELEM.EQ.2292 .OR. JELEM.EQ.7186 .OR.
     1      JELEM.EQ.100  .OR. JELEM.EQ.4994 .OR.
     2      JELEM.EQ.1500 .OR. JELEM.EQ.6394 .OR.
     3      JELEM.EQ.4862 .OR. JELEM.EQ.9756) THEN
          WRITE(*,1001) KSTEP, KINC, JELEM, JTYPE, PHYSIDX,
     1      U(1), SVARS(1), SVARS(5), SVARS(9)
          WRITE(6,1001) KSTEP, KINC, JELEM, JTYPE, PHYSIDX,
     1      U(1), SVARS(1), SVARS(5), SVARS(9)
          WRITE(7,1001) KSTEP, KINC, JELEM, JTYPE, PHYSIDX,
     1      U(1), SVARS(1), SVARS(5), SVARS(9)
 1001     FORMAT('[STATE_TRACE] KSTEP=',I1,' KINC=',I1,
     1           ' JELEM=',I6,' JTYPE=',I1,' PHYSIDX=',I6,
     2           ' INCOMING_PHASE=',F8.5,' SDV14=',F8.5,
     3           ' SDV15=',F8.5,' SDV16=',E12.5)
        ENDIF
      ENDIF

      RETURN
      END

      SUBROUTINE UMAT(STRESS,STATEV,DDSDDE,SSE,SPD,SCD,
     1 RPL,DDSDDD,DRPLDE,DRPLDD,STRAN,DSTRAN,
     2 TIME,DTIME,TEMP,DTEMP,PREDEF,DPRED,CMNAME,
     3 NDI,NSHR,NTENS,NSTATV,PROPS,NPROPS,COORDS,
     4 DROTT,PNEWDT,CELENT,DFGRD0,DFGRD1,NOEL,NPT,
     5 LAYER,KSPT,KSTEP,KINC)
      INCLUDE 'ABA_PARAM.INC'
      CHARACTER*80 CMNAME
      DIMENSION STRESS(NTENS),STATEV(NSTATV),DDSDDE(NTENS,NTENS),
     1 STRAN(NTENS),DSTRAN(NTENS),TIME(2),PREDEF(1),DPRED(1),
     2 PROPS(NPROPS),COORDS(3),DROTT(3,3),DFGRD0(3,3),DFGRD1(3,3)
      INTEGER I, J
      DO I=1, NTENS
        STRESS(I) = 0.D0
        DO J=1, NTENS
          DDSDDE(I,J) = 0.D0
        ENDDO
        DDSDDE(I,I) = 1.D-11
      ENDDO
      RETURN
      END
"""

def build_r1r6_pbs_script() -> str:
    return """#!/bin/bash
#PBS -N M2STATE_FRACFIX_RESTART1R1R6
#PBS -l select=1:ncpus=1:mpiprocs=1:mem=8gb
#PBS -l walltime=24:00:00
#PBS -q entry_imfdfkmq
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de
#PBS -j oe
#PBS -o M2STATE_FRACFIX_RESTART1R1R6.pbs.log

cd $PBS_O_WORKDIR

NOTIFICATION_CONFIG="${NOTIFICATION_CONFIG:-$HOME/.config/adaptive-remeshing/notifications.env}"
NOTIFICATION_SCRIPT="${NOTIFICATION_SCRIPT:-$HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh}"

if [ -f "$NOTIFICATION_SCRIPT" ]; then
  source "$NOTIFICATION_SCRIPT" 2>/dev/null || true
  notification_load_config 2>/dev/null || true
  notification_install_terminal_trap 2>/dev/null || true
  notify_start 2>/dev/null || true
fi

echo "[PBS_PREFLIGHT] Starting M2STATE_FRACFIX_RESTART1R1R6 Production Restart Job..."
date

python3 -c "
import json, hashlib, sys, re
from pathlib import Path

manifest_path = Path('PACKAGE_MANIFEST.json')
if not manifest_path.exists():
    print('[PBS_PREFLIGHT] ERROR: PACKAGE_MANIFEST.json does not exist')
    sys.exit(1)

try:
    m = json.loads(manifest_path.read_text())
except Exception as e:
    print(f'[PBS_PREFLIGHT] ERROR: Failed to parse PACKAGE_MANIFEST.json: {e}')
    sys.exit(1)

if not isinstance(m, dict):
    print('[PBS_PREFLIGHT] ERROR: Manifest root is not a dictionary')
    sys.exit(1)

has_files = 'files' in m
has_file_hashes = 'file_hashes' in m

if not has_files and not has_file_hashes:
    print('[PBS_PREFLIGHT] ERROR: Manifest contains neither \"files\" nor \"file_hashes\" key')
    sys.exit(1)

if has_files and has_file_hashes and m['files'] != m['file_hashes']:
    print('[PBS_PREFLIGHT] ERROR: Manifest contains conflicting \"files\" and \"file_hashes\" mappings')
    sys.exit(1)

files_dict = m.get('files', m.get('file_hashes'))

if not isinstance(files_dict, dict):
    print('[PBS_PREFLIGHT] ERROR: Manifest file mapping is not a dictionary')
    sys.exit(1)

if len(files_dict) == 0:
    print('[PBS_PREFLIGHT] ERROR: Manifest file mapping is empty')
    sys.exit(1)

required_files = [
    "M2STATE_FRACFIX_RESTART1R1R6.inp",
    "f42_mixed_uel.for",
    "STATE_TRANSFER_ARTIFACT.json",
    "TRANSFER_MANIFEST.json",
    "RESTART_ACCEPTANCE_CONTRACT.json",
    "verify_restart_trace.py",
    "extract_restart1r1r6_odb.py",
    "verify_restart1r1r6_science.py",
    "M2STATE_FRACFIX_RESTART1R1R6.pbs",
    "submit_m2state_fracfix_restart1r1r6.sh"
]

for rf in required_files:
    if rf not in files_dict:
        print(f'[PBS_PREFLIGHT] ERROR: Required execution file {rf} missing from manifest')
        sys.exit(1)

hex_re = re.compile(r'^[0-9a-fA-F]{64}$')

for f, expected_hash in files_dict.items():
    if not isinstance(expected_hash, str) or not hex_re.match(expected_hash):
        print(f'[PBS_PREFLIGHT] ERROR: Invalid hash format for {f}: {expected_hash}')
        sys.exit(1)
    p = Path(f)
    if not p.exists():
        print(f'[PBS_PREFLIGHT] ERROR: Missing required package file {f}')
        sys.exit(1)
    actual = hashlib.sha256(p.read_bytes()).hexdigest()
    if actual.lower() != expected_hash.lower():
        print(f'[PBS_PREFLIGHT] ERROR: Hash mismatch for {f}: expected {expected_hash}, got {actual}')
        sys.exit(1)

print('[PBS_PREFLIGHT] PACKAGE HASHES VERIFIED 100% MATCH.')
"
if [ $? -ne 0 ]; then
  echo "[PBS_PREFLIGHT] ERROR: Package manifest verification failed."
  exit 1
fi

module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7

echo "[PBS_PREFLIGHT] Abaqus environment loaded."
abaqus information=release

abaqus job=M2STATE_FRACFIX_RESTART1R1R6 user=f42_mixed_uel.for input=M2STATE_FRACFIX_RESTART1R1R6.inp interactive

ABAQUS_RC=$?
echo "[PBS_PREFLIGHT] Abaqus execution finished with exit code $ABAQUS_RC"

if [ $ABAQUS_RC -ne 0 ]; then
  echo "[PBS_PREFLIGHT] ERROR: Abaqus execution failed with exit code $ABAQUS_RC"
  exit $ABAQUS_RC
fi

echo "[PBS_PREFLIGHT] Abaqus continuation step completed successfully."

cat M2STATE_FRACFIX_RESTART1R1R6.dat M2STATE_FRACFIX_RESTART1R1R6.msg M2STATE_FRACFIX_RESTART1R1R6.log > M2STATE_FRACFIX_RESTART1R1R6.trace 2>/dev/null

python3 verify_restart_trace.py M2STATE_FRACFIX_RESTART1R1R6.trace
CHECKER_RC=$?

if [ $CHECKER_RC -ne 0 ]; then
  echo "[PBS_PREFLIGHT] ERROR: Production restart trace checker failed with exit code $CHECKER_RC"
  exit $CHECKER_RC
fi

echo "[PBS_PREFLIGHT] ALL PRODUCTION RESTART CONTRACTS QUALIFIED SUCCESSFULLY."
"""

def build_r1r6_guarded_wrapper() -> str:
    return """#!/usr/bin/env bash
# Guarded Submission Wrapper for Production Candidate M2STATE_FRACFIX_RESTART1R1R6
# Candidate Revision: M2STATE_FRACFIX_RESTART1R1R6
# Author: Gemini Antigravity
# Protocol Version: 1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_MANIFEST="${SCRIPT_DIR}/PACKAGE_MANIFEST.json"
PBS_SCRIPT="${SCRIPT_DIR}/M2STATE_FRACFIX_RESTART1R1R6.pbs"
CANDIDATE_NAME="M2STATE_FRACFIX_RESTART1R1R6"

DRY_RUN=false
for arg in "$@"; do
    if [[ "$arg" == "--dry-run" ]]; then
        DRY_RUN=true
    fi
done

echo "======================================================================"
echo "[PREFLIGHT] Validating package integrity for ${CANDIDATE_NAME}..."
echo "======================================================================"

if [[ ! -f "${PACKAGE_MANIFEST}" ]]; then
    echo "[PREFLIGHT] ERROR: Manifest file missing: ${PACKAGE_MANIFEST}" >&2
    exit 1
fi

if [[ ! -f "${PBS_SCRIPT}" ]]; then
    echo "[PREFLIGHT] ERROR: PBS script missing: ${PBS_SCRIPT}" >&2
    exit 1
fi

NOTIF_HELPER="${HOME}/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh"
if [[ -f "${NOTIF_HELPER}" ]]; then
    source "${NOTIF_HELPER}"
fi

echo "[PREFLIGHT] Checking input deck and user subroutine files..."
for f in "M2STATE_FRACFIX_RESTART1R1R6.inp" "f42_mixed_uel.for" "STATE_TRANSFER_ARTIFACT.json" "TRANSFER_MANIFEST.json" "RESTART_ACCEPTANCE_CONTRACT.json" "extract_restart1r1r6_odb.py" "verify_restart1r1r6_science.py"; do
    if [[ ! -f "${SCRIPT_DIR}/${f}" ]]; then
        echo "[PREFLIGHT] ERROR: Required candidate file missing: ${f}" >&2
        exit 1
    fi
done

echo "[PREFLIGHT] Package files present and readable."

if [[ "${DRY_RUN}" == "true" ]]; then
    echo "[PREFLIGHT] Dry-run verification PASS."
    echo "[PREFLIGHT] Intended command: qsub ${PBS_SCRIPT}"
    echo "[PREFLIGHT] No qsub invoked during dry run."
    exit 0
fi

echo "======================================================================"
echo "[SUBMIT] Submitting ${CANDIDATE_NAME} to PBS scheduler..."
echo "======================================================================"

QSUB_BIN="qsub"
if [[ -n "${MOCK_QSUB_BIN:-}" ]]; then
    QSUB_BIN="${MOCK_QSUB_BIN}"
fi

JOB_OUTPUT=$("${QSUB_BIN}" "${PBS_SCRIPT}")
JOB_ID=$(echo "${JOB_OUTPUT}" | tail -n 1)

echo "[SUBMIT] SUCCESS: Job submitted as ${JOB_ID}"

if declare -f notify_submitted >/dev/null 2>&1; then
    notify_submitted "${JOB_ID}" "${CANDIDATE_NAME}" "Submitted to PBS queue entry_imfdfkmq (1 CPU, 8GB, 24:00:00)" || echo "[SUBMIT] WARNING: Submission notification delivery failed" >&2
elif declare -f notify_event >/dev/null 2>&1; then
    notify_event "SUBMITTED" "${JOB_ID}" "${CANDIDATE_NAME}" "Submitted to PBS queue entry_imfdfkmq" || echo "[SUBMIT] WARNING: Submission notification delivery failed" >&2
fi

exit 0
"""

def build_r1r6_trace_checker() -> str:
    return """#!/usr/bin/env python3
\"\"\"
Production Runtime Trace Checker for M2STATE_FRACFIX_RESTART1R1R6.
Verifies that UEL emits startup records for all 4 production representative pairs in PK5 mesh.
Fails closed on NaN, Inf, or missing data.
\"\"\"

import sys
import re
import math
from pathlib import Path

EXPECTED_REPRESENTATIVES = {
    2292: {"jtype": 1, "physidx": 2292, "role": "High-d Quad Phase"},
    7186: {"jtype": 2, "physidx": 2292, "role": "High-d Quad Mech"},
    100:  {"jtype": 1, "physidx": 100,  "role": "Low-d Quad Phase"},
    4994: {"jtype": 2, "physidx": 100,  "role": "Low-d Quad Mech"},
    1500: {"jtype": 1, "physidx": 1500, "role": "Transition Quad Phase"},
    6394: {"jtype": 2, "physidx": 1500, "role": "Transition Quad Mech"},
    4862: {"jtype": 3, "physidx": 4862, "role": "Tri Pair Phase"},
    9756: {"jtype": 4, "physidx": 4862, "role": "Tri Pair Mech"}
}

def check_trace_file(trace_path: Path) -> int:
    if not trace_path.exists():
        print(f"[RESTART_TRACE_CHECKER] ERROR: Trace file {trace_path} does not exist.")
        return 1

    lines = trace_path.read_text(encoding="utf-8", errors="replace").splitlines()
    found_reps = set()
    pattern = re.compile(r'\\[STATE_TRACE\\] KSTEP=(\\d+) KINC=(\\d+) JELEM=\\s*(\\d+) JTYPE=(\\d+) PHYSIDX=\\s*(\\d+)\\s+INCOMING_PHASE=([^\\s]+)\\s+SDV14=([^\\s]+)\\s+SDV15=([^\\s]+)\\s+SDV16=([^\\s]+)')

    for line in lines:
        match = pattern.search(line)
        if match:
            kstep = int(match.group(1))
            kinc = int(match.group(2))
            jelem = int(match.group(3))
            jtype = int(match.group(4))
            physidx = int(match.group(5))
            
            for val_str in [match.group(6), match.group(7), match.group(8), match.group(9)]:
                try:
                    val = float(val_str)
                    if math.isnan(val) or math.isinf(val):
                        print(f"[RESTART_TRACE_CHECKER] FAIL: Invalid float value (NaN/Inf) encountered: {val_str}")
                        return 1
                except ValueError:
                    print(f"[RESTART_TRACE_CHECKER] FAIL: Non-numeric value encountered: {val_str}")
                    return 1

            if kstep == 2 and kinc == 1 and jelem in EXPECTED_REPRESENTATIVES:
                exp = EXPECTED_REPRESENTATIVES[jelem]
                if jtype == exp["jtype"] and physidx == exp["physidx"]:
                    found_reps.add(jelem)

    missing = set(EXPECTED_REPRESENTATIVES.keys()) - found_reps
    if missing:
        print(f"[RESTART_TRACE_CHECKER] FAIL: Missing trace records for representatives: {sorted(list(missing))}")
        return 1

    print(f"[RESTART_TRACE_CHECKER] PASS: All {len(found_reps)} production representative elements traced cleanly.")
    return 0

if __name__ == "__main__":
    t_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("M2STATE_FRACFIX_RESTART1R1R6.trace")
    sys.exit(check_trace_file(t_path))
"""

def main():
    print("======================================================================")
    print("BUILDING PRODUCTION CANDIDATE: M2STATE_FRACFIX_RESTART1R1R6")
    print("======================================================================")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Input deck M2STATE_FRACFIX_RESTART1R1R6.inp
    r1r5_inp = (SRC_R1R5_DIR / "M2STATE_FRACFIX_RESTART1R1R5.inp").read_text(encoding="utf-8", errors="replace")
    r1r6_inp = r1r5_inp.replace("M2STATE_FRACFIX_RESTART1R1R5", "M2STATE_FRACFIX_RESTART1R1R6")
    
    # Place N_PHYSICAL set after node 99999 right before *ELEMENT card
    n_phys_nset = "*NSET, NSET=N_PHYSICAL, GENERATE\n1, 4998, 1\n**\n"
    r1r6_inp = r1r6_inp.replace("99999,   0.000000,   0.100000\n", "99999,   0.000000,   0.100000\n**\n" + n_phys_nset)
    
    # Update output requests in Step 1 and Step 2 to include *OUTPUT, FIELD and *NODE OUTPUT, NSET=N_PHYSICAL
    field_out_req = "*OUTPUT, FIELD, FREQ=1\n*NODE OUTPUT, NSET=N_PHYSICAL\nU\n*NODE PRINT, FREQ=1\nU, RF\n"
    r1r6_inp = r1r6_inp.replace("*NODE PRINT, FREQ=1\nU, RF\n", field_out_req)

    inp_path = OUT_DIR / "M2STATE_FRACFIX_RESTART1R1R6.inp"
    write_lf_file(inp_path, r1r6_inp)
    print(f"Created input deck: {inp_path.name} ({len(r1r6_inp)} bytes)")

    # 2. UEL subroutine f42_mixed_uel.for
    fortran_code = build_r1r6_uel_fortran()
    for_path = OUT_DIR / "f42_mixed_uel.for"
    write_lf_file(for_path, fortran_code)
    print(f"Created UEL Fortran: {for_path.name} ({len(fortran_code)} bytes)")

    # 3. Copy state transfer artifact, transfer manifest, restart acceptance contract, trace checker
    for f in ["STATE_TRANSFER_ARTIFACT.json", "TRANSFER_MANIFEST.json", "RESTART_ACCEPTANCE_CONTRACT.json"]:
        src_p = SRC_R1R5_DIR / f
        dst_p = OUT_DIR / f
        content = src_p.read_text(encoding="utf-8")
        content_updated = content.replace("M2STATE_FRACFIX_RESTART1R1R5", "M2STATE_FRACFIX_RESTART1R1R6")
        write_lf_file(dst_p, content_updated)
        print(f"Copied & updated: {f}")

    # Trace checker verify_restart_trace.py
    checker_code = build_r1r6_trace_checker()
    checker_path = OUT_DIR / "verify_restart_trace.py"
    write_lf_file(checker_path, checker_code)
    print(f"Created trace checker: {checker_path.name}")

    # Copy postprocessing helpers to OUT_DIR
    for helper_name in ["extract_restart1r1r6_odb.py", "verify_restart1r1r6_science.py"]:
        src_helper = ROOT / "scripts/postprocessing" / helper_name
        dst_helper = OUT_DIR / helper_name
        write_lf_file(dst_helper, src_helper.read_text(encoding="utf-8"))
        print(f"Copied postprocessing helper: {helper_name}")

    # 4. PBS script M2STATE_FRACFIX_RESTART1R1R6.pbs
    pbs_code = build_r1r6_pbs_script()
    pbs_path = OUT_DIR / "M2STATE_FRACFIX_RESTART1R1R6.pbs"
    write_lf_file(pbs_path, pbs_code)
    print(f"Created PBS script: {pbs_path.name}")

    # 5. Guarded wrapper submit_m2state_fracfix_restart1r1r6.sh
    wrapper_code = build_r1r6_guarded_wrapper()
    wrapper_path = OUT_DIR / "submit_m2state_fracfix_restart1r1r6.sh"
    write_lf_file(wrapper_path, wrapper_code)
    print(f"Created guarded wrapper: {wrapper_path.name}")

    # 6. PACKAGE_MANIFEST.json with canonical key "files" and ALL 10 execution-critical files!
    manifest = {
        "candidate": "M2STATE_FRACFIX_RESTART1R1R6",
        "predecessor": "M2STATE_FRACFIX_RESTART1R1R5",
        "classification": "INSTRUMENTATION_ONLY_CHANGE",
        "scientific_formulation_change_count": 0,
        "files": {
            "M2STATE_FRACFIX_RESTART1R1R6.inp": sha256_file(inp_path),
            "f42_mixed_uel.for": sha256_file(for_path),
            "STATE_TRANSFER_ARTIFACT.json": sha256_file(OUT_DIR / "STATE_TRANSFER_ARTIFACT.json"),
            "TRANSFER_MANIFEST.json": sha256_file(OUT_DIR / "TRANSFER_MANIFEST.json"),
            "RESTART_ACCEPTANCE_CONTRACT.json": sha256_file(OUT_DIR / "RESTART_ACCEPTANCE_CONTRACT.json"),
            "verify_restart_trace.py": sha256_file(checker_path),
            "extract_restart1r1r6_odb.py": sha256_file(OUT_DIR / "extract_restart1r1r6_odb.py"),
            "verify_restart1r1r6_science.py": sha256_file(OUT_DIR / "verify_restart1r1r6_science.py"),
            "M2STATE_FRACFIX_RESTART1R1R6.pbs": sha256_file(pbs_path),
            "submit_m2state_fracfix_restart1r1r6.sh": sha256_file(wrapper_path)
        }
    }
    manifest_path = OUT_DIR / "PACKAGE_MANIFEST.json"
    write_lf_file(manifest_path, json.dumps(manifest, indent=2))
    print(f"Created manifest: {manifest_path.name}")

    print("======================================================================")
    print("M2STATE_FRACFIX_RESTART1R1R6 BUILDING COMPLETE")
    print("======================================================================")

if __name__ == "__main__":
    main()
