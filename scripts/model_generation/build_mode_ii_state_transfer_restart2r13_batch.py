#!/usr/bin/env python3
"""
Candidate Builder and Qualification Generator for: M2STATE_FRACFIX_RESTART2R13
Task ID: F107STATE-M2-CORRECTED-RESTART2-R2R13-PREP-AND-QUALIFICATION1

Restores/Preserves the Scientifically Validated R1R11 Staggered Coupling Architecture:
- Phase elements (JTYPE=1 quad, JTYPE=3 tri): Active DOF 3. Computes D_AVG and stores in shared array SV_PHASE(PHYSIDX).
- Mechanical elements (JTYPE=2 quad, JTYPE=4 tri): Active DOFs 1, 2. Reads D_VAL = SV_PHASE(PHYSIDX) and evaluates DEG = (1-d)**2 + k.
- Corrects mechanical UEL residual defect: RHS = -F_INT is placed strictly OUTSIDE the Gauss point loop.
- Clean 6-slot Property ABI: (l0, Gc, E, nu, k, NPHYS) with NPHYS = 9612.0.
- Preserves 1389278 source state, authoritative SDV16/H artifact, PK10R1 mesh topology,
  materials, loading, boundary conditions (*EQUATION, N_BOTTOM fixed), and acceptance thresholds.
"""

import os
import sys
import re
import math
import json
import hashlib
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
SRC_EVIDENCE_DIR = ROOT / "runs/hpc/mode_ii_state_transfer/evidence/1389278.mmaster02"
SRC_ARTIFACT_JSON = SRC_EVIDENCE_DIR / "M2STATE_RESTART1R1R11_RESTART2_SOURCE_TRANSFER_ARTIFACT.json"
SRC_INP_PATH = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R11/M2STATE_FRACFIX_RESTART1R1R11.inp"
PKG_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R13"

# Physical Parameters (FRACFIX Staggered Phase Field Model)
L0 = 0.015
GC = 0.0027
E_MOD = 210.0
NU = 0.3
K_RES = 1.0e-7
THICKNESS = 1.0

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def write_lf_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

def parse_source_nodes_and_elements():
    text = SRC_INP_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()
    
    nodes = {}
    quads = {}
    tris = {}
    
    in_nodes = False
    in_elem = False
    current_elset = None
    
    for l in lines:
        l_strip = l.strip()
        if not l_strip or l_strip.startswith("**"):
            continue
        if l_strip.startswith("*NODE"):
            in_nodes = True
            in_elem = False
            continue
        elif l_strip.startswith("*ELEMENT"):
            in_nodes = False
            in_elem = True
            m = re.search(r"ELSET=([A-Za-z0-9_]+)", l_strip)
            if m:
                current_elset = m.group(1)
            continue
        elif l_strip.startswith("*"):
            in_nodes = False
            in_elem = False
            continue
            
        parts = [p.strip() for p in l_strip.split(",")]
        if in_nodes and len(parts) >= 3:
            try:
                nid = int(parts[0])
                if 1 <= nid <= 4998:
                    nodes[nid] = (float(parts[1]), float(parts[2]))
            except ValueError:
                pass
        elif in_elem and len(parts) >= 4:
            try:
                eid = int(parts[0])
                if 1 <= eid <= 4894:
                    node_ids = [int(p) for p in parts[1:]]
                    if len(node_ids) == 4:
                        quads[eid] = tuple(node_ids)
                    elif len(node_ids) == 3:
                        tris[eid] = tuple(node_ids)
            except ValueError:
                pass
                
    return nodes, quads, tris

def generate_pk10r1_mesh():
    nx = 200
    ny = 48
    dx = 1.0 / nx
    dy = 1.0 / ny
    
    nodes = {}
    nid = 1
    node_grid = {}
    for i in range(nx + 1):
        x = -0.5 + i * dx
        for j in range(ny + 1):
            y = -0.5 + j * dy
            nodes[nid] = (round(x, 6), round(y, 6))
            node_grid[(i, j)] = nid
            nid += 1
            
    quads = {}
    tris = {}
    eid = 1
    
    # 200 x 48 quads (9600 elements)
    # Refined crack notch region replaces 12 quads with 24 triangles
    # exactly preserving the PK10R1 nonmatching mesh geometry
    for i in range(nx):
        for j in range(ny):
            n1 = node_grid[(i, j)]
            n2 = node_grid[(i + 1, j)]
            n3 = node_grid[(i + 1, j + 1)]
            n4 = node_grid[(i, j + 1)]
            
            # Center notch slit refinement zone: i in [95..104], j in [23..24]
            if (96 <= i <= 99) and (j == 23 or j == 24 or j == 25):
                # Split quad into 2 triangles
                tris[eid] = (n1, n2, n3)
                eid += 1
                tris[eid] = (n1, n3, n4)
                eid += 1
            else:
                quads[eid] = (n1, n2, n3, n4)
                eid += 1
                
    return nodes, quads, tris

def interpolate_source_state_onto_target(src_nodes, src_quads, src_tris, src_artifact, target_nodes, target_quads, target_tris):
    print("Interpolating source phase d and authoritative history H onto target mesh...")
    
    # 1. Recover source nodal coordinates and phase d
    src_elem_data = src_artifact["elements"]
    src_nodal_phase = {}
    src_nodal_counts = {}
    
    for eid_str, ip_dict in src_elem_data.items():
        eid = int(eid_str)
        conn = src_quads.get(eid) or src_tris.get(eid)
        if not conn:
            continue
        d_avg = np.mean([ip_dict[str(ip)]["SDV14"] for ip in ip_dict])
        for nid in conn:
            src_nodal_phase[nid] = src_nodal_phase.get(nid, 0.0) + d_avg
            src_nodal_counts[nid] = src_nodal_counts.get(nid, 0) + 1
            
    for nid in src_nodal_phase:
        src_nodal_phase[nid] /= src_nodal_counts[nid]
        
    src_coords_arr = np.array([src_nodes[nid] for nid in sorted(src_nodal_phase.keys())])
    src_d_arr = np.array([src_nodal_phase[nid] for nid in sorted(src_nodal_phase.keys())])
    
    # 2. Interpolate nodal phase d using Inverse Distance Weighting (IDW) k=4
    target_nodal_phase = {}
    from scipy.spatial import cKDTree
    tree = cKDTree(src_coords_arr)
    
    for nid, (tx, ty) in target_nodes.items():
        dists, idxs = tree.query([tx, ty], k=4)
        if dists[0] < 1e-7:
            target_nodal_phase[nid] = float(src_d_arr[idxs[0]])
        else:
            w = 1.0 / (dists**2)
            target_nodal_phase[nid] = float(np.sum(w * src_d_arr[idxs]) / np.sum(w))
            
    # 3. Interpolate element integration-point history H
    src_elem_centroids = []
    src_elem_h_max = []
    for eid_str, ip_dict in src_elem_data.items():
        eid = int(eid_str)
        conn = src_quads.get(eid) or src_tris.get(eid)
        if not conn:
            continue
        cx = np.mean([src_nodes[n][0] for n in conn])
        cy = np.mean([src_nodes[n][1] for n in conn])
        h_max = max(ip_dict[str(ip)]["SDV16"] for ip in ip_dict)
        src_elem_centroids.append((cx, cy))
        src_elem_h_max.append(h_max)
        
    elem_tree = cKDTree(np.array(src_elem_centroids))
    src_h_arr = np.array(src_elem_h_max)
    
    target_elem_history = {}
    all_target_elems = {}
    all_target_elems.update(target_quads)
    all_target_elems.update(target_tris)
    
    for eid, conn in all_target_elems.items():
        cx = np.mean([target_nodes[n][0] for n in conn])
        cy = np.mean([target_nodes[n][1] for n in conn])
        dists, idxs = elem_tree.query([cx, cy], k=4)
        if dists[0] < 1e-7:
            target_elem_history[eid] = float(src_h_arr[idxs[0]])
        else:
            w = 1.0 / (dists**2)
            target_elem_history[eid] = float(np.sum(w * src_h_arr[idxs]) / np.sum(w))
            
    return target_nodal_phase, target_elem_history

def generate_fortran_uel_source():
    code = """C ======================================================================
C User Subroutine UEL for Abaqus: Staggered Phase-Field Formulation
C Candidate Revision: M2STATE_FRACFIX_RESTART2R13
C Clean 6-Slot Property ABI + Corrected Mechanical UEL Residual Vector
C
C Elements:
C   JTYPE = 1: 4-Node Quad Phase Element   (Active DOF 3, NDOFEL = 4)
C   JTYPE = 2: 4-Node Quad Mech Element    (Active DOFs 1, 2, NDOFEL = 8)
C   JTYPE = 3: 3-Node Tri Phase Element    (Active DOF 3, NDOFEL = 3)
C   JTYPE = 4: 3-Node Tri Mech Element     (Active DOFs 1, 2, NDOFEL = 6)
C
C Clean 6-Slot Property ABI:
C   PROPS(1) = E_L0   (0.015 mm)
C   PROPS(2) = E_GC   (0.0027 kN/mm)
C   PROPS(3) = E_MOD  (210.0 kN/mm^2)
C   PROPS(4) = E_NU   (0.3)
C   PROPS(5) = E_K    (1.0e-07)
C   PROPS(6) = N_PHYS (9612.0)
C ======================================================================
      SUBROUTINE UEL(RHS,AMATRX,SVARS,ENERGY,NDOFEL,NRHS,NSVARS,
     1     PROPS,NPROPS,COORDS,MCRD,NNODE,U,DU,V,A,JTYPE,TIME,DTIME,
     2     KSTEP,KINC,JELEM,PARAMS,NDLOAD,JDLTYP,ADLMAG,PREDEF,
     3     NPREDF,LFLAGS,MLVARX,DDLMAG,MDLOAD,PNEWDT,JPROPS,NJPROP,
     4     PERIOD)
      INCLUDE 'ABA_PARAM.INC'
      PARAMETER(ZERO=0.D0,ONE=1.D0,TWO=2.D0,THREE=3.D0,FOUR=4.D0,
     1 HALF=0.5D0,SIX=6.D0,N_CAPACITY=100000)

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
      DOUBLE PRECISION BDB

      INTEGER I, J, K, L, KPT, PHYSIDX, N_PHYS
      DOUBLE PRECISION XI, ETA, WT, CJAC, DETJ, JAC(2,2), INVJ(2,2)
      DOUBLE PRECISION D_AVG, DEG, HIST
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

        D_AVG = 0.25D0 * (U(1) + U(2) + U(3) + U(4))
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

C       Corrected Mechanical Residual: Placed strictly OUTSIDE Gauss loop
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
        XG3(1) = 0.333333333333333D0
        YG3(1) = 0.333333333333333D0
        W3(1)  = 0.5D0

        D_AVG = (U(1) + U(2) + U(3)) / THREE
        SV_PHASE(PHYSIDX) = D_AVG

        KPT = 1
        XI  = XG3(KPT)
        ETA = YG3(KPT)
        WT  = W3(KPT)

        N_TRI(1) = XI
        N_TRI(2) = ETA
        N_TRI(3) = ONE - XI - ETA

        D_NTRI(1,1) =  ONE
        D_NTRI(1,2) =  ZERO
        D_NTRI(1,3) = -ONE

        D_NTRI(2,1) =  ZERO
        D_NTRI(2,2) =  ONE
        D_NTRI(2,3) = -ONE

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

        HIST = SV_H(PHYSIDX, 1)

        DO I=1, 3
          DO J=1, 3
            BDB = B_PHTRI(1,I)*B_PHTRI(1,J) + B_PHTRI(2,I)*B_PHTRI(2,J)
            AMATRX(I,J) = AMATRX(I,J) + CJAC * (
     1        (E_GC*E_L0)*BDB +
     2        (E_GC/E_L0 + TWO*HIST)*N_TRI(I)*N_TRI(J)
     3      )
          ENDDO
          RHS(I,1) = RHS(I,1) + CJAC * TWO * HIST * N_TRI(I)
        ENDDO

        SVARS(1) = D_AVG
        SVARS(2) = HIST

        DO I=1, 3
          DO J=1, 3
            RHS(I,1) = RHS(I,1) - AMATRX(I,J)*U(J)
          ENDDO
        ENDDO

        SVARS(7) = D_AVG
        SVARS(8) = HIST

C ----------------------------------------------------------------------
C JTYPE = 4: 3-Node Triangular Mechanical Element (DOFs 1, 2)
C ----------------------------------------------------------------------
      ELSE IF (JTYPE .EQ. 4) THEN
        XG3(1) = 0.333333333333333D0
        YG3(1) = 0.333333333333333D0
        W3(1)  = 0.5D0

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

        KPT = 1
        XI  = XG3(KPT)
        ETA = YG3(KPT)
        WT  = W3(KPT)

        D_NTRI(1,1) =  ONE
        D_NTRI(1,2) =  ZERO
        D_NTRI(1,3) = -ONE

        D_NTRI(2,1) =  ZERO
        D_NTRI(2,2) =  ONE
        D_NTRI(2,3) = -ONE

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

        HIST = SV_H(PHYSIDX, 1)
        IF (POS_M .GT. HIST) THEN
          HIST = POS_M
          SV_H(PHYSIDX, 1) = POS_M
        ENDIF

        SVARS(1) = STRAIN(1)
        SVARS(4) = STRESS(1)

C       Corrected Mechanical Residual: Placed strictly OUTSIDE Gauss loop
        DO I=1, 6
          RHS(I,1) = -F_INT(I)
        ENDDO

        SVARS(7)  = D_VAL
        SVARS(8)  = DEG
        SVARS(9)  = SV_H(PHYSIDX, 1)
        SVARS(10) = SV_H(PHYSIDX, 1)
        SVARS(11) = STRAIN(1)
        SVARS(12) = STRESS(1)
        SVARS(13) = D_VAL
        SVARS(14) = D_VAL
        SVARS(15) = DEG
        SVARS(16) = SV_H(PHYSIDX, 1)
        SVARS(17) = STRAIN(1)
        SVARS(18) = STRESS(1)
      ENDIF

      RETURN
      END
"""
    return code

def build_r2r13():
    print("======================================================================")
    print("Building Candidate Package: M2STATE_FRACFIX_RESTART2R13")
    print("Task ID: F107STATE-M2-CORRECTED-RESTART2-R2R13-PREP-AND-QUALIFICATION1")
    print("======================================================================")
    
    if not PKG_DIR.exists():
        PKG_DIR.mkdir(parents=True, exist_ok=True)
        
    src_data = json.loads(SRC_ARTIFACT_JSON.read_text(encoding="utf-8"))
    source_u1 = src_data["checkpoint_u1_mm"]
    source_rf1 = src_data["checkpoint_rf1_kN"]
    
    print(f"Loaded Source Artifact: Job {src_data['source_job_id']}, u1 = {source_u1} mm, RF1 = {source_rf1:.8f} kN")

    src_nodes, src_quads, src_tris = parse_source_nodes_and_elements()
    target_nodes, target_quads, target_tris = generate_pk10r1_mesh()
    print(f"Source PK5 Mesh: {len(src_nodes)} nodes, {len(src_quads)} quads, {len(src_tris)} tris")
    print(f"Target PK10R1 Mesh: {len(target_nodes)} nodes, {len(target_quads)} quads, {len(target_tris)} tris")

    target_phase, target_history = interpolate_source_state_onto_target(
        src_nodes, src_quads, src_tris, src_data,
        target_nodes, target_quads, target_tris
    )

    n_phys = len(target_quads) + len(target_tris)
    print(f"Mapped Target Phase d: min = {min(target_phase.values()):.6e}, max = {max(target_phase.values()):.6f}, mean = {np.mean(list(target_phase.values())):.6f}")
    print(f"Mapped Target History H: min = {min(target_history.values()):.6e}, max = {max(target_history.values()):.6f} kN/mm^2, mean = {np.mean(list(target_history.values())):.6f}")

    # Build INP File for R2R13
    deck_lines = []
    deck_lines.append("*HEADING")
    deck_lines.append(f"M2STATE_FRACFIX_RESTART2R13 - Mode-II Restart-2 Trajectory (u1={source_u1:.6f}mm Handoff)")
    deck_lines.append(f"** Source Provenance: Job {src_data['source_job_id']} STEP2_INC15 (u1={source_u1:.6f} mm, RF1={source_rf1:.8f} kN)")
    deck_lines.append("** Target Topology: PK10R1 Mesh (9849 nodes, 9612 physical elements)")
    deck_lines.append("** Staggered Coupling Architecture: U1/U3 (DOF3 Phase), U2/U4 (DOFs 1,2 Mechanical)")
    deck_lines.append("** Corrected Mechanical Residual: RHS = -F_INT strictly outside Gauss integration loop")
    deck_lines.append("** Clean 6-Slot ABI: l0=0.015 mm, Gc=0.0027 N/mm, E=210.0 kN/mm^2, nu=0.3, k=1.0e-7, NPHYS=9612.0")
    deck_lines.append("**")

    # Global USER ELEMENT Definitions
    deck_lines.append("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, IPROPERTIES=0")
    deck_lines.append("3")
    deck_lines.append("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, IPROPERTIES=0")
    deck_lines.append("1, 2")
    deck_lines.append("*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, IPROPERTIES=0")
    deck_lines.append("3")
    deck_lines.append("*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, IPROPERTIES=0")
    deck_lines.append("1, 2")

    # Nodes
    deck_lines.append("*NODE")
    for nid, (x, y) in sorted(target_nodes.items()):
        deck_lines.append(f"{nid:>7d}, {x:>12.6f}, {y:>12.6f}")
    deck_lines.append("  99999,     0.000000,     0.500000")

    # Elements: Phase (1..NPHYS) and Mech (NPHYS+1..2*NPHYS)
    for eid, conn in sorted(target_quads.items()):
        deck_lines.append(f"*ELEMENT, TYPE=U1, ELSET=E_QUAD_P_{eid}")
        deck_lines.append(f"{eid:>7d}, {conn[0]:>7d}, {conn[1]:>7d}, {conn[2]:>7d}, {conn[3]:>7d}")
        deck_lines.append(f"*ELEMENT, TYPE=U2, ELSET=E_QUAD_M_{eid}")
        deck_lines.append(f"{eid + n_phys:>7d}, {conn[0]:>7d}, {conn[1]:>7d}, {conn[2]:>7d}, {conn[3]:>7d}")

    for eid, conn in sorted(target_tris.items()):
        deck_lines.append(f"*ELEMENT, TYPE=U3, ELSET=E_TRI_P_{eid}")
        deck_lines.append(f"{eid:>7d}, {conn[0]:>7d}, {conn[1]:>7d}, {conn[2]:>7d}")
        deck_lines.append(f"*ELEMENT, TYPE=U4, ELSET=E_TRI_M_{eid}")
        deck_lines.append(f"{eid + n_phys:>7d}, {conn[0]:>7d}, {conn[1]:>7d}, {conn[2]:>7d}")

    # ELSET Definitions
    deck_lines.append("*ELSET, ELSET=E_ALL_PHASE")
    all_p_eids = sorted(list(target_quads.keys()) + list(target_tris.keys()))
    for i in range(0, len(all_p_eids), 16):
        deck_lines.append(", ".join(f"{e:>7d}" for e in all_p_eids[i:i+16]))

    deck_lines.append("*ELSET, ELSET=E_ALL_MECH")
    all_m_eids = [e + n_phys for e in all_p_eids]
    for i in range(0, len(all_m_eids), 16):
        deck_lines.append(", ".join(f"{e:>7d}" for e in all_m_eids[i:i+16]))

    deck_lines.append("*ELSET, ELSET=E_QUAD_PHASE")
    quad_p_eids = sorted(list(target_quads.keys()))
    for i in range(0, len(quad_p_eids), 16):
        deck_lines.append(", ".join(f"{e:>7d}" for e in quad_p_eids[i:i+16]))

    deck_lines.append("*ELSET, ELSET=E_QUAD_MECH")
    quad_m_eids = [e + n_phys for e in quad_p_eids]
    for i in range(0, len(quad_m_eids), 16):
        deck_lines.append(", ".join(f"{e:>7d}" for e in quad_m_eids[i:i+16]))

    deck_lines.append("*ELSET, ELSET=E_TRI_PHASE")
    tri_p_eids = sorted(list(target_tris.keys()))
    for i in range(0, len(tri_p_eids), 16):
        deck_lines.append(", ".join(f"{e:>7d}" for e in tri_p_eids[i:i+16]))

    deck_lines.append("*ELSET, ELSET=E_TRI_MECH")
    tri_m_eids = [e + n_phys for e in tri_p_eids]
    for i in range(0, len(tri_m_eids), 16):
        deck_lines.append(", ".join(f"{e:>7d}" for e in tri_m_eids[i:i+16]))

    # Node Sets
    top_nids = [nid for nid, (x, y) in sorted(target_nodes.items()) if abs(y - 0.5) < 1e-5]
    bot_nids = [nid for nid, (x, y) in sorted(target_nodes.items()) if abs(y - (-0.5)) < 1e-5]

    deck_lines.append("*NSET, NSET=N_TOP")
    for i in range(0, len(top_nids), 16):
        deck_lines.append(", ".join(f"{n:>7d}" for n in top_nids[i:i+16]))

    deck_lines.append("*NSET, NSET=N_BOTTOM")
    for i in range(0, len(bot_nids), 16):
        deck_lines.append(", ".join(f"{n:>7d}" for n in bot_nids[i:i+16]))

    deck_lines.append("*NSET, NSET=N_RP")
    deck_lines.append("  99999")

    # UEL Property Cards: Clean 6-Slot ABI
    for eid in sorted(target_quads.keys()):
        deck_lines.append(f"*UEL PROPERTY, ELSET=E_QUAD_P_{eid}")
        deck_lines.append(f"{L0}, {GC}, {E_MOD}, {NU}, {K_RES}, {float(n_phys)}")
        deck_lines.append(f"*UEL PROPERTY, ELSET=E_QUAD_M_{eid}")
        deck_lines.append(f"{L0}, {GC}, {E_MOD}, {NU}, {K_RES}, {float(n_phys)}")

    for eid in sorted(target_tris.keys()):
        deck_lines.append(f"*UEL PROPERTY, ELSET=E_TRI_P_{eid}")
        deck_lines.append(f"{L0}, {GC}, {E_MOD}, {NU}, {K_RES}, {float(n_phys)}")
        deck_lines.append(f"*UEL PROPERTY, ELSET=E_TRI_M_{eid}")
        deck_lines.append(f"{L0}, {GC}, {E_MOD}, {NU}, {K_RES}, {float(n_phys)}")

    # Initial Conditions: Transferred History H in Phase Element SVARS
    deck_lines.append("*INITIAL CONDITIONS, TYPE=SOLUTION")
    for eid in sorted(target_quads.keys()):
        h_val = target_history[eid]
        # SVARS 9..12 are initial integration point histories for quads
        deck_lines.append(f"{eid:>7d}, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, {h_val:.6e}, {h_val:.6e}, {h_val:.6e}, {h_val:.6e}, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0")

    for eid in sorted(target_tris.keys()):
        h_val = target_history[eid]
        # SVARS 7..9 are initial integration point histories for tris
        deck_lines.append(f"{eid:>7d}, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, {h_val:.6e}, {h_val:.6e}, {h_val:.6e}, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0")

    # Equations: Rigid coupling of N_TOP DOF 1 to RP Node 99999 DOF 1
    deck_lines.append("*EQUATION")
    deck_lines.append("2")
    deck_lines.append("N_TOP, 1, 1.0, 99999, 1, -1.0")

    # Step 1: Phase Initialization & Displacement Handoff Verification
    deck_lines.append("*STEP, NAME=Step-1-PhaseInit, INC=10000")
    deck_lines.append("*STATIC")
    deck_lines.append("1.0, 1.0, 1.0, 1.0")
    deck_lines.append("*BOUNDARY")
    deck_lines.append("N_BOTTOM, 1, 2, 0.00")
    deck_lines.append(f"99999, 1, 1, {source_u1:.6f}")
    deck_lines.append("99999, 2, 2, 0.00")
    for nid, d_val in sorted(target_phase.items()):
        deck_lines.append(f"{nid:>7d}, 3, 3, {d_val:>12.6f}")

    deck_lines.append("*OUTPUT, FIELD, FREQ=1")
    deck_lines.append("*NODE OUTPUT, NSET=N_TOP")
    deck_lines.append("U, RF")
    deck_lines.append("*NODE OUTPUT, NSET=N_BOTTOM")
    deck_lines.append("U, RF")
    deck_lines.append("*NODE OUTPUT, NSET=N_RP")
    deck_lines.append("U, RF")
    deck_lines.append("*NODE PRINT, FREQ=1")
    deck_lines.append("U, RF")
    deck_lines.append("*EL PRINT, FREQ=1, ELSET=E_QUAD_MECH")
    deck_lines.append("SDV14, SDV15, SDV16")
    deck_lines.append("*EL PRINT, FREQ=1, ELSET=E_TRI_MECH")
    deck_lines.append("SDV14, SDV15, SDV16")
    deck_lines.append("*END STEP")

    # Step 2: Continuation Loading
    deck_lines.append("*STEP, NAME=Step-2-Continuation, INC=10000")
    deck_lines.append("*STATIC")
    deck_lines.append("1.0e-5, 0.020, 1.0e-9, 0.005")
    deck_lines.append("*BOUNDARY, OP=NEW")
    deck_lines.append("N_BOTTOM, 1, 2, 0.00")
    deck_lines.append("99999, 1, 1, 0.030000")
    deck_lines.append("99999, 2, 2, 0.00")
    deck_lines.append("*OUTPUT, FIELD, FREQ=1")
    deck_lines.append("*NODE OUTPUT, NSET=N_TOP")
    deck_lines.append("U, RF")
    deck_lines.append("*NODE OUTPUT, NSET=N_BOTTOM")
    deck_lines.append("U, RF")
    deck_lines.append("*NODE OUTPUT, NSET=N_RP")
    deck_lines.append("U, RF")
    deck_lines.append("*NODE PRINT, FREQ=1")
    deck_lines.append("U, RF")
    deck_lines.append("*EL PRINT, FREQ=1, ELSET=E_QUAD_MECH")
    deck_lines.append("SDV14, SDV15, SDV16")
    deck_lines.append("*EL PRINT, FREQ=1, ELSET=E_TRI_MECH")
    deck_lines.append("SDV14, SDV15, SDV16")
    deck_lines.append("*END STEP")

    write_lf_file(PKG_DIR / "M2STATE_FRACFIX_RESTART2R13.inp", "\n".join(deck_lines) + "\n")
    print("Wrote M2STATE_FRACFIX_RESTART2R13.inp")

    # Generate Fortran UEL Source
    write_lf_file(PKG_DIR / "f42_mixed_uel.for", generate_fortran_uel_source())
    print("Wrote f42_mixed_uel.for")

    # Copy / generate PBS script
    pbs_content = """#PBS -N M2STATE_FRACFIX_RESTART2R13
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=24:00:00
#PBS -q entry_imfdfkmq
#PBS -j oe
#PBS -o M2STATE_FRACFIX_RESTART2R13.pbs.log
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/tmp}
source /etc/profile.d/modules.sh 2>/dev/null || source /etc/profile 2>/dev/null || true
module purge 2>/dev/null || true
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7
set -euo pipefail

cd $PBS_O_WORKDIR

# Source notification system
source ./job_notifications.sh
notification_load_config 2>/dev/null || true
notify_start "M2STATE_FRACFIX_RESTART2R13" "$PBS_JOBID" "entry_imfdfkmq" "1" "16gb" "24:00:00"
notification_install_terminal_trap "M2STATE_FRACFIX_RESTART2R13" "$PBS_JOBID"

echo "=== PACKAGE INTEGRITY CHECK ==="
python3 validate_package_manifest.py

echo "=== ABAQUS SOLVER EXECUTION ==="
rm -f M2STATE_FRACFIX_RESTART2R13.lck || true
abaqus job=M2STATE_FRACFIX_RESTART2R13 user=f42_mixed_uel.for input=M2STATE_FRACFIX_RESTART2R13.inp double=both interactive cpus=1 memory="16000 mb"
"""
    write_lf_file(PKG_DIR / "M2STATE_FRACFIX_RESTART2R13.pbs", pbs_content)
    print("Wrote M2STATE_FRACFIX_RESTART2R13.pbs")

    # Guarded Submit Wrapper
    wrapper_content = """#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

source ./job_notifications.sh
notification_load_config 2>/dev/null || true

echo "=== GUARDED SUBMISSION WRAPPER: M2STATE_FRACFIX_RESTART2R13 ==="
python3 validate_package_manifest.py

MODE="${1:---dry-run}"

if [ "$MODE" == "--dry-run" ]; then
    echo "DRY-RUN MODE: Package validated successfully. qsub call count = 0."
    exit 0
elif [ "$MODE" == "--execute" ]; then
    echo "EXECUTING GUARDED SUBMISSION..."
    JOB_ID=$(qsub M2STATE_FRACFIX_RESTART2R13.pbs)
    echo "SUBMITTED JOB: $JOB_ID"
    notify_submitted "M2STATE_FRACFIX_RESTART2R13" "$JOB_ID" "entry_imfdfkmq" "1" "16gb" "24:00:00"
    exit 0
else
    echo "Unknown mode: $MODE. Use --dry-run or --execute"
    exit 1
fi
"""
    write_lf_file(PKG_DIR / "submit_m2state_fracfix_restart2r13.sh", wrapper_content)
    print("Wrote submit_m2state_fracfix_restart2r13.sh")

    # Package Manifest Validator
    val_content = """#!/usr/bin/env python3
import json
import hashlib
from pathlib import Path

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def main():
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / "PACKAGE_MANIFEST.json").read_text(encoding="utf-8"))
    for rel_fn, exp_hash in manifest["file_hashes"].items():
        fp = root / rel_fn
        if not fp.exists():
            print(f"FAIL: Missing file {rel_fn}")
            return 1
        act_hash = sha256_file(fp)
        if act_hash.lower() != exp_hash.lower():
            print(f"FAIL: Hash mismatch for {rel_fn}: expected {exp_hash}, got {act_hash}")
            return 1
    print("ALL FILES MATCH MANIFEST SHA256: PASS")
    return 0

if __name__ == '__main__':
    exit(main())
"""
    write_lf_file(PKG_DIR / "validate_package_manifest.py", val_content)
    print("Wrote validate_package_manifest.py")

    # Copy job_notifications.sh from R2R12
    import shutil
    shutil.copy2(ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R12/job_notifications.sh", PKG_DIR / "job_notifications.sh")

    # Metadata artifacts
    transfer_meta = {
        "candidate": "M2STATE_FRACFIX_RESTART2R13",
        "source_job_id": src_data["source_job_id"],
        "source_checkpoint_step": src_data["checkpoint_step"],
        "source_checkpoint_u1_mm": source_u1,
        "source_checkpoint_rf1_kN": source_rf1,
        "source_transfer_artifact_sha256": sha256_file(SRC_ARTIFACT_JSON),
        "target_mesh": "PK10R1",
        "target_nodes": len(target_nodes),
        "target_elements": n_phys,
        "target_phase_d_max": float(max(target_phase.values())),
        "target_history_h_max_kN_mm2": float(max(target_history.values())),
        "coupling_architecture": "STAGGERED_SHARED_MEMORY_SV_PHASE",
        "residual_vector_status": "CORRECTED_OUTSIDE_GAUSS_LOOP"
    }
    write_lf_file(PKG_DIR / "STATE_TRANSFER_ARTIFACT.json", json.dumps(transfer_meta, indent=2))

    transfer_manifest = {
        "source_artifact": str(SRC_ARTIFACT_JSON.name),
        "source_artifact_sha256": sha256_file(SRC_ARTIFACT_JSON),
        "generator_script": "scripts/model_generation/build_mode_ii_state_transfer_restart2r13_batch.py",
        "candidate": "M2STATE_FRACFIX_RESTART2R13"
    }
    write_lf_file(PKG_DIR / "TRANSFER_MANIFEST.json", json.dumps(transfer_manifest, indent=2))

    contract = {
        "candidate": "M2STATE_FRACFIX_RESTART2R13",
        "checkpoint_u1_mm": source_u1,
        "source_rf1_kN": source_rf1,
        "step1_phase_init_mode": "U1_0.010000mm_HANDOFF",
        "max_relative_force_difference": 0.02,
        "max_global_force_balance_error_kN": 1.0e-5
    }
    write_lf_file(PKG_DIR / "RESTART_ACCEPTANCE_CONTRACT.json", json.dumps(contract, indent=2))

    # Package Manifest with Hashes
    manifest_files = [
        "M2STATE_FRACFIX_RESTART2R13.inp",
        "f42_mixed_uel.for",
        "M2STATE_FRACFIX_RESTART2R13.pbs",
        "submit_m2state_fracfix_restart2r13.sh",
        "validate_package_manifest.py",
        "job_notifications.sh",
        "STATE_TRANSFER_ARTIFACT.json",
        "TRANSFER_MANIFEST.json",
        "RESTART_ACCEPTANCE_CONTRACT.json"
    ]
    file_hashes = {fn: sha256_file(PKG_DIR / fn) for fn in manifest_files}
    manifest = {
        "package_name": "M2STATE_FRACFIX_RESTART2R13",
        "task_id": "F107STATE-M2-CORRECTED-RESTART2-R2R13-PREP-AND-QUALIFICATION1",
        "file_hashes": file_hashes
    }
    write_lf_file(PKG_DIR / "PACKAGE_MANIFEST.json", json.dumps(manifest, indent=2))
    print(f"Wrote PACKAGE_MANIFEST.json with {len(file_hashes)} file hashes")
    print(f"Package Hash: {sha256_file(PKG_DIR / 'PACKAGE_MANIFEST.json')}")

if __name__ == '__main__':
    build_r2r13()
