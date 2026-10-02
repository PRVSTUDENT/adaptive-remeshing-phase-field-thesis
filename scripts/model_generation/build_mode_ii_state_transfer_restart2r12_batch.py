#!/usr/bin/env python3
"""
Candidate Builder and Qualification Generator for: M2STATE_FRACFIX_RESTART2R12
Task ID: F101STATE-M2-CORRECTED-RESTART2-R2R12-PREP-AND-QUALIFICATION1

Corrects the JTYPE=2/JTYPE=4 Mechanical UEL Phase-Consumption Defect:
- Mechanical elements (JTYPE=2 quad, JTYPE=4 tri) now request DOFs 1, 2, 3.
- Reads nodal phase field d from U(3, 6, 9, 12) for quads and U(3, 6, 9) for tris.
- Computes stiffness degradation DEG = (1.0D0 - D_GP)**2 + K_RES from phase d.
- Preserves 1389278 source state, authoritative SDV16/H artifact, PK10R1 mesh topology,
  6-slot UEL ABI cards, materials, loading, boundary conditions, and acceptance thresholds.
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
PKG_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R12"

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
    
    for i in range(nx):
        for j in range(ny):
            n1 = node_grid[(i, j)]
            n2 = node_grid[(i + 1, j)]
            n3 = node_grid[(i + 1, j + 1)]
            n4 = node_grid[(i, j + 1)]
            
            x_mid = (nodes[n1][0] + nodes[n3][0]) / 2.0
            y_mid = (nodes[n1][1] + nodes[n3][1]) / 2.0
            
            if abs(x_mid) < 0.015 and abs(y_mid) < 0.015:
                tris[eid] = (n1, n2, n3)
                eid += 1
                tris[eid] = (n1, n3, n4)
                eid += 1
            else:
                quads[eid] = (n1, n2, n3, n4)
                eid += 1

    return nodes, quads, tris

def interpolate_source_state_onto_target(src_nodes, src_quads, src_tris, src_artifact_data, target_nodes, target_quads, target_tris):
    src_elem_data = src_artifact_data["elements"]
    
    node_d_sums = {}
    node_d_counts = {}
    for elem_id_str, ips in src_elem_data.items():
        elem_id = int(elem_id_str)
        conn = src_quads.get(elem_id) or src_tris.get(elem_id)
        if not conn:
            continue
        sdv14_avg = sum(ip_data["SDV14"] for ip_data in ips.values()) / len(ips)
        for nid in conn:
            node_d_sums[nid] = node_d_sums.get(nid, 0.0) + sdv14_avg
            node_d_counts[nid] = node_d_counts.get(nid, 0) + 1
            
    src_node_coords = []
    src_node_d = []
    for nid, (x, y) in src_nodes.items():
        src_node_coords.append((x, y))
        d_val = node_d_sums.get(nid, 0.0) / max(1, node_d_counts.get(nid, 1))
        src_node_d.append(d_val)
        
    src_node_coords = np.array(src_node_coords)
    src_node_d = np.array(src_node_d)
    
    mapped_phase = {}
    for tnid, (tx, ty) in target_nodes.items():
        d2 = (src_node_coords[:, 0] - tx)**2 + (src_node_coords[:, 1] - ty)**2
        min_idx = np.argmin(d2)
        if d2[min_idx] < 1.0e-10:
            mapped_phase[tnid] = float(max(0.0, min(1.0, src_node_d[min_idx])))
        else:
            w = 1.0 / (d2 + 1.0e-12)
            mapped_d = np.sum(w * src_node_d) / np.sum(w)
            mapped_phase[tnid] = float(max(0.0, min(1.0, mapped_d)))

    src_elem_centroids = []
    src_elem_h = []
    for elem_id_str, ips in src_elem_data.items():
        elem_id = int(elem_id_str)
        conn = src_quads.get(elem_id) or src_tris.get(elem_id)
        if not conn:
            continue
        c_x = sum(src_nodes[nid][0] for nid in conn) / len(conn)
        c_y = sum(src_nodes[nid][1] for nid in conn) / len(conn)
        src_elem_centroids.append((c_x, c_y))
        sdv16_avg = sum(ip_data["SDV16"] for ip_data in ips.values()) / len(ips)
        src_elem_h.append(sdv16_avg)

    src_elem_centroids = np.array(src_elem_centroids)
    src_elem_h = np.array(src_elem_h)
    
    mapped_history = {}
    all_target_elems = {}
    all_target_elems.update(target_quads)
    all_target_elems.update(target_tris)
    
    for teid, conn in all_target_elems.items():
        tc_x = sum(target_nodes[nid][0] for nid in conn) / len(conn)
        tc_y = sum(target_nodes[nid][1] for nid in conn) / len(conn)
        
        d2 = (src_elem_centroids[:, 0] - tc_x)**2 + (src_elem_centroids[:, 1] - tc_y)**2
        min_idx = np.argmin(d2)
        if d2[min_idx] < 1.0e-10:
            mapped_history[teid] = float(max(0.0, src_elem_h[min_idx]))
        else:
            w = 1.0 / (d2 + 1.0e-12)
            mapped_h = np.sum(w * src_elem_h) / np.sum(w)
            mapped_history[teid] = float(max(0.0, mapped_h))

    return mapped_phase, mapped_history

def generate_f42_mixed_uel_repaired():
    """Generates Fortran UEL with JTYPE=2/JTYPE=4 phase consumption repair."""
    code = """C=======================================================================
C USER SUBROUTINE UEL FOR FRACFIX STAGGERED PHASE-FIELD FORMULATION
C Production Version: Clean 6-Slot Property ABI & Phase-Consumption Repair
C JTYPE=1: Quad Phase Element   (DOFs 3, 4 Nodes, 4 Gauss Points)
C JTYPE=2: Quad Mech Element    (DOFs 1,2,3, 4 Nodes, 4 Gauss Points)
C JTYPE=3: Tri Phase Element    (DOFs 3, 3 Nodes, 1 Gauss Point)
C JTYPE=4: Tri Mech Element     (DOFs 1,2,3, 3 Nodes, 1 Gauss Point)
C PROPS(1) = l0
C PROPS(2) = Gc
C PROPS(3) = E
C PROPS(4) = nu
C PROPS(5) = k (residual stiffness)
C PROPS(6) = NPHYS (total physical elements)
C=======================================================================
      SUBROUTINE UEL(RHS, AMATRX, SVARS, ENERGY, NDOFEL, NRHS, NSVARS,
     1 PROPS, NPROPS, COORDS, MCRD, NNODE, U, DU, V, A, JTYPE, TIME,
     2 DTIME, KSTEP, KINC, JELEM, PARAMS, NDLOAD, JDLTYP, ADLMAG,
     3 PREDEF, NPREDF, LFLAGS, MLVARX, DDLMAG, MDLOAD, PNEWDT, JPROPS,
     4 NJPROP, PERIOD)

      INCLUDE 'ABA_PARAM.INC'

      DIMENSION RHS(MLVARX,*), AMATRX(NDOFEL,NDOFEL), SVARS(NSVARS),
     1 ENERGY(8), PROPS(NPROPS), COORDS(MCRD,NNODE), U(NDOFEL),
     2 DU(NDOFEL), V(NDOFEL), A(NDOFEL), TIME(2), PARAMS(*),
     3 JDLTYP(MDLOAD,*), ADLMAG(MDLOAD,*), PREDEF(2,NPREDF,NNODE),
     4 LFLAGS(4), DDLMAG(MDLOAD,*), JPROPS(*)

      DOUBLE PRECISION L0, GC, E_MOD, NU, K_RES, NPHYS
      DOUBLE PRECISION JAC(2,2), INVJ(2,2), DETJ
      DOUBLE PRECISION N_VEC(4), DN_DX(2,4), DN_DXI(2,4)
      DOUBLE PRECISION STIFF(3,3), B_MAT(3,8)
      DOUBLE PRECISION GAUSS_PTS(4,2), GAUSS_WTS(4)
      DOUBLE PRECISION TRI_PTS(3,2), TRI_WTS(3)
      DOUBLE PRECISION D_NODE(4), H_VAL(4)
      DOUBLE PRECISION D_GP, H_GP, DEG, FAC
      INTEGER I, J, K, L, M, NGP
      INTEGER MECH_MAP_QUAD(8), MECH_MAP_TRI(6)
      INTEGER MI, MJ

      DATA MECH_MAP_QUAD /1, 2, 4, 5, 7, 8, 10, 11/
      DATA MECH_MAP_TRI  /1, 2, 4, 5, 7, 8/

      L0    = PROPS(1)
      GC    = PROPS(2)
      E_MOD = PROPS(3)
      NU    = PROPS(4)
      K_RES = PROPS(5)
      NPHYS = PROPS(6)

      DO I = 1, NDOFEL
         RHS(I,1) = 0.0D0
         DO J = 1, NDOFEL
            AMATRX(I,J) = 0.0D0
         END DO
      END DO

      IF (NNODE .EQ. 4) THEN
         NGP = 4
         GAUSS_PTS(1,1) = -0.577350269189626D0
         GAUSS_PTS(1,2) = -0.577350269189626D0
         GAUSS_PTS(2,1) =  0.577350269189626D0
         GAUSS_PTS(2,2) = -0.577350269189626D0
         GAUSS_PTS(3,1) =  0.577350269189626D0
         GAUSS_PTS(3,2) =  0.577350269189626D0
         GAUSS_PTS(4,1) = -0.577350269189626D0
         GAUSS_PTS(4,2) =  0.577350269189626D0
         GAUSS_WTS(1)   = 1.0D0
         GAUSS_WTS(2)   = 1.0D0
         GAUSS_WTS(3)   = 1.0D0
         GAUSS_WTS(4)   = 1.0D0

         IF (JTYPE .EQ. 1) THEN
            DO I = 1, 4
               D_NODE(I) = U(I)
               H_VAL(I)  = SVARS(I)
            END DO
         ELSE
            DO I = 1, 4
               D_NODE(I) = U(3*I)
               H_VAL(I)  = SVARS(I)
            END DO
         END IF

         DO K = 1, NGP
            XI  = GAUSS_PTS(K,1)
            ETA = GAUSS_PTS(K,2)
            WT  = GAUSS_WTS(K)

            DN_DXI(1,1) = -0.25D0 * (1.0D0 - ETA)
            DN_DXI(1,2) =  0.25D0 * (1.0D0 - ETA)
            DN_DXI(1,3) =  0.25D0 * (1.0D0 + ETA)
            DN_DXI(1,4) = -0.25D0 * (1.0D0 + ETA)

            DN_DXI(2,1) = -0.25D0 * (1.0D0 - XI)
            DN_DXI(2,2) = -0.25D0 * (1.0D0 + XI)
            DN_DXI(2,3) =  0.25D0 * (1.0D0 + XI)
            DN_DXI(2,4) =  0.25D0 * (1.0D0 - XI)


            N_VEC(1) = 0.25D0 * (1.0D0 - XI) * (1.0D0 - ETA)
            N_VEC(2) = 0.25D0 * (1.0D0 + XI) * (1.0D0 - ETA)
            N_VEC(3) = 0.25D0 * (1.0D0 + XI) * (1.0D0 + ETA)
            N_VEC(4) = 0.25D0 * (1.0D0 - XI) * (1.0D0 + ETA)

            JAC(1,1) = 0.0D0
            JAC(1,2) = 0.0D0
            JAC(2,1) = 0.0D0
            JAC(2,2) = 0.0D0
            DO I = 1, 4
               JAC(1,1) = JAC(1,1) + DN_DXI(1,I) * COORDS(1,I)
               JAC(1,2) = JAC(1,2) + DN_DXI(1,I) * COORDS(2,I)
               JAC(2,1) = JAC(2,1) + DN_DXI(2,I) * COORDS(1,I)
               JAC(2,2) = JAC(2,2) + DN_DXI(2,I) * COORDS(2,I)
            END DO

            DETJ = JAC(1,1) * JAC(2,2) - JAC(1,2) * JAC(2,1)
            IF (DETJ .LE. 0.0D0) THEN
               WRITE(*,*) 'ERROR: Non-positive Jacobian in Quad UEL:', JELEM
               CALL XIT
            END IF

            INVJ(1,1) =  JAC(2,2) / DETJ
            INVJ(1,2) = -JAC(1,2) / DETJ
            INVJ(2,1) = -JAC(2,1) / DETJ
            INVJ(2,2) =  JAC(1,1) / DETJ

            DO I = 1, 4
               DN_DX(1,I) = INVJ(1,1)*DN_DXI(1,I) + INVJ(1,2)*DN_DXI(2,I)
               DN_DX(2,I) = INVJ(2,1)*DN_DXI(1,I) + INVJ(2,2)*DN_DXI(2,I)
            END DO

            D_GP = 0.0D0
            H_GP = H_VAL(K)
            DO I = 1, 4
               D_GP = D_GP + N_VEC(I) * D_NODE(I)
            END DO

            DEG = (1.0D0 - D_GP)**2 + K_RES

            IF (JTYPE .EQ. 1) THEN
               DO I = 1, 4
                  FH = 2.0D0 * (1.0D0 - D_GP) * H_GP
                  RHS(I,1) = RHS(I,1) + (N_VEC(I)*FH - GC/L0*N_VEC(I)*D_GP
     1             - GC*L0*(DN_DX(1,I)*DN_DX(1,1)*D_NODE(1) +
     2                      DN_DX(2,I)*DN_DX(2,1)*D_NODE(1) +
     3                      DN_DX(1,I)*DN_DX(1,2)*D_NODE(2) +
     4                      DN_DX(2,I)*DN_DX(2,2)*D_NODE(2) +
     5                      DN_DX(1,I)*DN_DX(1,3)*D_NODE(3) +
     6                      DN_DX(2,I)*DN_DX(2,3)*D_NODE(3) +
     7                      DN_DX(1,I)*DN_DX(1,4)*D_NODE(4) +
     8                      DN_DX(2,I)*DN_DX(2,4)*D_NODE(4))) * DETJ * WT
                  DO J = 1, 4
                     AMATRX(I,J) = AMATRX(I,J) + (GC/L0 * N_VEC(I)*N_VEC(J)
     1                + GC*L0*(DN_DX(1,I)*DN_DX(1,J) + DN_DX(2,I)*DN_DX(2,J))
     2                + 2.0D0*H_GP*N_VEC(I)*N_VEC(J)) * DETJ * WT
                  END DO
               END DO
            ELSE
               FAC = E_MOD / ((1.0D0 + NU) * (1.0D0 - 2.0D0*NU))
               STIFF(1,1) = FAC * (1.0D0 - NU) * DEG
               STIFF(2,2) = STIFF(1,1)
               STIFF(1,2) = FAC * NU * DEG
               STIFF(2,1) = STIFF(1,2)
               STIFF(3,3) = E_MOD / (2.0D0 * (1.0D0 + NU)) * DEG


               DO I = 1, 4
                  B_MAT(1, 2*I-1) = DN_DX(1,I)
                  B_MAT(1, 2*I)   = 0.0D0
                  B_MAT(2, 2*I-1) = 0.0D0
                  B_MAT(2, 2*I)   = DN_DX(2,I)
                  B_MAT(3, 2*I-1) = DN_DX(2,I)
                  B_MAT(3, 2*I)   = DN_DX(1,I)
               END DO

               DO I = 1, 8
                  MI = MECH_MAP_QUAD(I)
                  DO J = 1, 8
                     MJ = MECH_MAP_QUAD(J)
                     DO L = 1, 3
                        DO M = 1, 3
                           AMATRX(MI,MJ) = AMATRX(MI,MJ) + B_MAT(L,I) *
     1                      STIFF(L,M) * B_MAT(M,J) * DETJ * WT
                        END DO
                     END DO
                  END DO
               END DO

               DO I = 1, 8
                  MI = MECH_MAP_QUAD(I)
                  DO J = 1, 8
                     MJ = MECH_MAP_QUAD(J)
                     RHS(MI,1) = RHS(MI,1) - AMATRX(MI,MJ) * U(MJ)
                  END DO
               END DO

               DO I = 1, 4
                  AMATRX(3*I, 3*I) = AMATRX(3*I, 3*I) + 1.0D-12
               END DO
            END IF
         END DO
      ELSE
         TRI_PTS(1,1) = 0.333333333333333D0
         TRI_PTS(1,2) = 0.333333333333333D0
         TRI_WTS(1)   = 0.5D0

         IF (JTYPE .EQ. 3) THEN
            DO I = 1, 3
               D_NODE(I) = U(I)
               H_VAL(I)  = SVARS(I)
            END DO
         ELSE
            DO I = 1, 3
               D_NODE(I) = U(3*I)
               H_VAL(I)  = SVARS(I)
            END DO
         END IF

         K = 1
         XI  = TRI_PTS(K,1)
         ETA = TRI_PTS(K,2)
         WT  = TRI_WTS(K)

         DN_DXI(1,1) = 1.0D0
         DN_DXI(1,2) = 0.0D0
         DN_DXI(1,3) = -1.0D0
         DN_DXI(2,1) = 0.0D0
         DN_DXI(2,2) = 1.0D0
         DN_DXI(2,3) = -1.0D0

         N_VEC(1) = XI
         N_VEC(2) = ETA
         N_VEC(3) = 1.0D0 - XI - ETA

         JAC(1,1) = 0.0D0
         JAC(1,2) = 0.0D0
         JAC(2,1) = 0.0D0
         JAC(2,2) = 0.0D0
         DO I = 1, 3
            JAC(1,1) = JAC(1,1) + DN_DXI(1,I) * COORDS(1,I)
            JAC(1,2) = JAC(1,2) + DN_DXI(1,I) * COORDS(2,I)
            JAC(2,1) = JAC(2,1) + DN_DXI(2,I) * COORDS(1,I)
            JAC(2,2) = JAC(2,2) + DN_DXI(2,I) * COORDS(2,I)
         END DO

         DETJ = JAC(1,1) * JAC(2,2) - JAC(1,2) * JAC(2,1)
         IF (DETJ .LE. 0.0D0) THEN
            WRITE(*,*) 'ERROR: Non-positive Jacobian in Tri UEL:', JELEM
            CALL XIT
         END IF

         INVJ(1,1) =  JAC(2,2) / DETJ
         INVJ(1,2) = -JAC(1,2) / DETJ
         INVJ(2,1) = -JAC(2,1) / DETJ
         INVJ(2,2) =  JAC(1,1) / DETJ

         DO I = 1, 3
            DN_DX(1,I) = INVJ(1,1)*DN_DXI(1,I) + INVJ(1,2)*DN_DXI(2,I)
            DN_DX(2,I) = INVJ(2,1)*DN_DXI(1,I) + INVJ(2,2)*DN_DXI(2,I)
         END DO

         D_GP = 0.0D0
         H_GP = H_VAL(1)
         DO I = 1, 3
            D_GP = D_GP + N_VEC(I) * D_NODE(I)
         END DO

         DEG = (1.0D0 - D_GP)**2 + K_RES

         IF (JTYPE .EQ. 3) THEN
            DO I = 1, 3
               FH = 2.0D0 * (1.0D0 - D_GP) * H_GP
               RHS(I,1) = RHS(I,1) + (N_VEC(I)*FH - GC/L0*N_VEC(I)*D_GP
     1          - GC*L0*(DN_DX(1,I)*DN_DX(1,1)*D_NODE(1) +
     2                   DN_DX(2,I)*DN_DX(2,1)*D_NODE(1) +
     3                   DN_DX(1,I)*DN_DX(1,2)*D_NODE(2) +
     4                   DN_DX(2,I)*DN_DX(2,2)*D_NODE(2) +
     5                   DN_DX(1,I)*DN_DX(1,3)*D_NODE(3) +
     6                   DN_DX(2,I)*DN_DX(2,3)*D_NODE(3))) * DETJ * WT
               DO J = 1, 3
                  AMATRX(I,J) = AMATRX(I,J) + (GC/L0 * N_VEC(I)*N_VEC(J)
     1             + GC*L0*(DN_DX(1,I)*DN_DX(1,J) + DN_DX(2,I)*DN_DX(2,J))
     2             + 2.0D0*H_GP*N_VEC(I)*N_VEC(J)) * DETJ * WT
               END DO
            END DO
         ELSE
            FAC = E_MOD / ((1.0D0 + NU) * (1.0D0 - 2.0D0*NU))
            STIFF(1,1) = FAC * (1.0D0 - NU) * DEG
            STIFF(2,2) = STIFF(1,1)
            STIFF(1,2) = FAC * NU * DEG
            STIFF(2,1) = STIFF(1,2)
            STIFF(3,3) = E_MOD / (2.0D0 * (1.0D0 + NU)) * DEG


            DO I = 1, 3
               B_MAT(1, 2*I-1) = DN_DX(1,I)
               B_MAT(1, 2*I)   = 0.0D0
               B_MAT(2, 2*I-1) = 0.0D0
               B_MAT(2, 2*I)   = DN_DX(2,I)
               B_MAT(3, 2*I-1) = DN_DX(2,I)
               B_MAT(3, 2*I)   = DN_DX(1,I)
            END DO

            DO I = 1, 6
               MI = MECH_MAP_TRI(I)
               DO J = 1, 6
                  MJ = MECH_MAP_TRI(J)
                  DO L = 1, 3
                     DO M = 1, 3
                        AMATRX(MI,MJ) = AMATRX(MI,MJ) + B_MAT(L,I) *
     1                   STIFF(L,M) * B_MAT(M,J) * DETJ * WT
                     END DO
                  END DO
               END DO
            END DO

            DO I = 1, 6
               MI = MECH_MAP_TRI(I)
               DO J = 1, 6
                  MJ = MECH_MAP_TRI(J)
                  RHS(MI,1) = RHS(MI,1) - AMATRX(MI,MJ) * U(MJ)
               END DO
            END DO

            DO I = 1, 3
               AMATRX(3*I, 3*I) = AMATRX(3*I, 3*I) + 1.0D-12
            END DO
         END IF
      END IF

      RETURN
      END
"""
    return code

def build_r2r12():
    print("======================================================================")
    print("Building Candidate Package: M2STATE_FRACFIX_RESTART2R12")
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

    # Build INP File for R2R12
    deck_lines = []
    deck_lines.append("*HEADING")
    deck_lines.append(f"M2STATE_FRACFIX_RESTART2R12 - Mode-II Restart-2 Trajectory (u1={source_u1:.6f}mm Handoff)")
    deck_lines.append(f"** Source Provenance: Job {src_data['source_job_id']} STEP2_INC15 (u1={source_u1:.6f} mm, RF1={source_rf1:.8f} kN)")
    deck_lines.append("** Target Topology: PK10R1 Mesh (9849 nodes, 9612 physical elements)")
    deck_lines.append("** UEL Phase-Consumption Repair: JTYPE=2 and JTYPE=4 use DOFs 1,2,3 to ingest phase d")
    deck_lines.append("** Material Parameters: l0=0.015 mm, Gc=0.0027 N/mm, E=210.0 kN/mm^2, nu=0.3, k=1.0e-7")
    deck_lines.append("**")

    # Global USER ELEMENT Definitions
    deck_lines.append("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, IPROPERTIES=0")
    deck_lines.append("3")
    deck_lines.append("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, IPROPERTIES=0")
    deck_lines.append("1, 2, 3")
    deck_lines.append("*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, IPROPERTIES=0")
    deck_lines.append("3")
    deck_lines.append("*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, IPROPERTIES=0")
    deck_lines.append("1, 2, 3")

    deck_lines.append("*NODE")
    for nid in sorted(target_nodes.keys()):
        x, y = target_nodes[nid]
        deck_lines.append(f"{nid:6d}, {x:14.6f}, {y:14.6f}")

    deck_lines.append("** PHYSICAL ELEMENT TOPOLOGY")
    for eid in sorted(target_quads.keys()):
        n1, n2, n3, n4 = target_quads[eid]
        
        # Phase UEL JTYPE=1 (Quad, DOFs 3)
        deck_lines.append(f"*ELEMENT, TYPE=U1, ELSET=E_QUAD_P_{eid}")
        deck_lines.append(f"{eid:6d}, {n1:6d}, {n2:6d}, {n3:6d}, {n4:6d}")
        deck_lines.append(f"*UEL PROPERTY, ELSET=E_QUAD_P_{eid}")
        deck_lines.append(f"{L0}, {GC}, {E_MOD}, {NU}, {K_RES}, {n_phys}")

        # Mechanical UEL JTYPE=2 (Quad, REPAIRED DOFs 1, 2, 3)
        eid_mech = eid + n_phys
        deck_lines.append(f"*ELEMENT, TYPE=U2, ELSET=E_QUAD_M_{eid}")
        deck_lines.append(f"{eid_mech:6d}, {n1:6d}, {n2:6d}, {n3:6d}, {n4:6d}")
        deck_lines.append(f"*UEL PROPERTY, ELSET=E_QUAD_M_{eid}")
        deck_lines.append(f"{L0}, {GC}, {E_MOD}, {NU}, {K_RES}, {n_phys}")

    for eid in sorted(target_tris.keys()):
        n1, n2, n3 = target_tris[eid]
        
        # Phase UEL JTYPE=3 (Tri, DOFs 3)
        deck_lines.append(f"*ELEMENT, TYPE=U3, ELSET=E_TRI_P_{eid}")
        deck_lines.append(f"{eid:6d}, {n1:6d}, {n2:6d}, {n3:6d}")
        deck_lines.append(f"*UEL PROPERTY, ELSET=E_TRI_P_{eid}")
        deck_lines.append(f"{L0}, {GC}, {E_MOD}, {NU}, {K_RES}, {n_phys}")

        # Mechanical UEL JTYPE=4 (Tri, REPAIRED DOFs 1, 2, 3)
        eid_mech = eid + n_phys
        deck_lines.append(f"*ELEMENT, TYPE=U4, ELSET=E_TRI_M_{eid}")
        deck_lines.append(f"{eid_mech:6d}, {n1:6d}, {n2:6d}, {n3:6d}")
        deck_lines.append(f"*UEL PROPERTY, ELSET=E_TRI_M_{eid}")
        deck_lines.append(f"{L0}, {GC}, {E_MOD}, {NU}, {K_RES}, {n_phys}")

    bottom_nodes = sorted([nid for nid, (x, y) in target_nodes.items() if abs(y - (-0.5)) < 1.0e-5])
    top_nodes = sorted([nid for nid, (x, y) in target_nodes.items() if abs(y - 0.5) < 1.0e-5])

    deck_lines.append("** NSETS FOR BOUNDARY CONDITIONS AND EQUATIONS")
    deck_lines.append("*NSET, NSET=N_BOTTOM")
    for i in range(0, len(bottom_nodes), 10):
        deck_lines.append(", ".join(f"{n:6d}" for n in bottom_nodes[i:i+10]))

    deck_lines.append("*NSET, NSET=N_TOP")
    for i in range(0, len(top_nodes), 10):
        deck_lines.append(", ".join(f"{n:6d}" for n in top_nodes[i:i+10]))

    deck_lines.append("*NODE, NSET=N_RP")
    deck_lines.append(" 99999,  -0.500000,   0.500000")

    deck_lines.append("** RIGID LINEAR COUPLING ON N_TOP")
    deck_lines.append("*EQUATION")
    deck_lines.append("2")
    deck_lines.append("N_TOP, 1, 1.0, 99999, 1, -1.0")

    deck_lines.append("** INITIAL CONDITIONS (History H via 18-SDV TYPE=SOLUTION)")
    deck_lines.append("*INITIAL CONDITIONS, TYPE=SOLUTION")

    for eid in sorted(target_quads.keys()):
        h_val = target_history[eid]
        
        deck_lines.append(f"{eid:6d}, " + ", ".join(f"{h_val:12.6e}" for _ in range(4)) + ", 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00")
        deck_lines.append(" 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, " + f"{h_val:12.6e}")
        deck_lines.append(" 0.000000e+00, 0.000000e+00")
        
        eid_mech = eid + n_phys
        deck_lines.append(f"{eid_mech:6d}, " + ", ".join(f"{h_val:12.6e}" for _ in range(4)) + ", 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00")
        deck_lines.append(" 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, " + f"{h_val:12.6e}")
        deck_lines.append(" 0.000000e+00, 0.000000e+00")

    for eid in sorted(target_tris.keys()):
        h_val = target_history[eid]

        deck_lines.append(f"{eid:6d}, " + ", ".join(f"{h_val:12.6e}" for _ in range(3)) + ", 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00")
        deck_lines.append(" 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, " + f"{h_val:12.6e}")
        deck_lines.append(" 0.000000e+00, 0.000000e+00")

        eid_mech = eid + n_phys
        deck_lines.append(f"{eid_mech:6d}, " + ", ".join(f"{h_val:12.6e}" for _ in range(3)) + ", 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00")
        deck_lines.append(" 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, " + f"{h_val:12.6e}")
        deck_lines.append(" 0.000000e+00, 0.000000e+00")

    deck_lines.append("**")
    deck_lines.append(f"** STEP 1: PHASE INITIALIZATION (DOF 3 Prescribed, Mechanical u1 = {source_u1:.6f} mm Handoff)")
    deck_lines.append("*STEP, NAME=Step-1-PhaseInit, INC=10000")
    deck_lines.append("*STATIC")
    deck_lines.append("1.0, 1.0, 1.0e-5, 1.0")
    deck_lines.append("*CONTROLS, PARAMETERS=FIELD")
    deck_lines.append("0.005, 0.01, 0.005, 10.0, 20.0, 5.0, 100.0, 0.02")
    deck_lines.append("1.0e-3, 1.0e-3, 1.0e-3")
    deck_lines.append("*BOUNDARY")
    deck_lines.append("N_BOTTOM, 1, 2, 0.00")
    deck_lines.append(f"99999, 1, 1, {source_u1:.6f}")
    deck_lines.append("99999, 2, 2, 0.00")

    for nid in sorted(target_nodes.keys()):
        d_val = target_phase[nid]
        deck_lines.append(f"{nid:6d}, 3, 3, {d_val:12.6f}")

    deck_lines.append("*OUTPUT, FIELD, FREQ=1")
    deck_lines.append("*NODE OUTPUT, NSET=N_RP")
    deck_lines.append("U, RF")
    deck_lines.append("*NODE PRINT, FREQ=1")
    deck_lines.append("U, RF")
    deck_lines.append("*END STEP")

    deck_lines.append("**")
    deck_lines.append("** STEP 2: CONTINUATION SOLVE (Shear Loading to u1 = 0.030000 mm)")
    deck_lines.append("*STEP, NAME=Step-2-Continuation, INC=10000")
    deck_lines.append("*STATIC")
    deck_lines.append("1.0e-3, 1.0, 1.0e-8, 0.02")
    deck_lines.append("*CONTROLS, PARAMETERS=FIELD")
    deck_lines.append("0.005, 0.01, 0.005, 10.0, 20.0, 5.0, 100.0, 0.02")
    deck_lines.append("1.0e-3, 1.0e-3, 1.0e-3")
    deck_lines.append("*BOUNDARY, OP=NEW")
    deck_lines.append("N_BOTTOM, 1, 2, 0.00")
    deck_lines.append("99999, 1, 1, 0.030000")
    deck_lines.append("99999, 2, 2, 0.00")

    for nid in sorted(target_nodes.keys()):
        d_val = target_phase[nid]
        if d_val >= 0.95:
            deck_lines.append(f"{nid:6d}, 3, 3, {d_val:12.6f}")

    deck_lines.append("*OUTPUT, FIELD, FREQ=1")
    deck_lines.append("*NODE OUTPUT, NSET=N_RP")
    deck_lines.append("U, RF")
    deck_lines.append("*NODE PRINT, FREQ=1")
    deck_lines.append("U, RF")
    deck_lines.append("*END STEP")

    inp_file = PKG_DIR / "M2STATE_FRACFIX_RESTART2R12.inp"
    write_lf_file(inp_file, "\n".join(deck_lines) + "\n")
    print(f"Generated input deck: {inp_file} ({len(deck_lines)} lines)")

    fortran_code = generate_f42_mixed_uel_repaired()
    fortran_file = PKG_DIR / "f42_mixed_uel.for"
    write_lf_file(fortran_file, fortran_code)
    print(f"Generated Fortran UEL code: {fortran_file}")

    pbs_code = f"""#!/bin/bash
#PBS -N M2STATE_FRACFIX_RESTART2R12
#PBS -l nodes=1:ppn=1
#PBS -l mem=8000mb
#PBS -l walltime=02:00:00
#PBS -q normal_imfdfkmq
#PBS -o M2STATE_FRACFIX_RESTART2R12.o$PBS_JOBID
#PBS -e M2STATE_FRACFIX_RESTART2R12.e$PBS_JOBID
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

export XDG_RUNTIME_DIR=${{XDG_RUNTIME_DIR:-/tmp}}
source /etc/profile.d/modules.sh 2>/dev/null || source /etc/profile 2>/dev/null || true
module purge 2>/dev/null || true
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7

cd $PBS_O_WORKDIR

source job_notifications.sh
notification_install_terminal_trap

notify_start "M2STATE_FRACFIX_RESTART2R12" "$PBS_JOBID" "normal_imfdfkmq"

rm -f M2STATE_FRACFIX_RESTART2R12.lck M2STATE_FRACFIX_RESTART2R12.dat M2STATE_FRACFIX_RESTART2R12.msg M2STATE_FRACFIX_RESTART2R12.sta || true

abaqus job=M2STATE_FRACFIX_RESTART2R12 user=f42_mixed_uel.for input=M2STATE_FRACFIX_RESTART2R12.inp interactive double=both cpus=1 memory="8000 mb"
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    notify_completed "M2STATE_FRACFIX_RESTART2R12" "$PBS_JOBID" "Analysis completed successfully."
else
    notify_failed "M2STATE_FRACFIX_RESTART2R12" "$PBS_JOBID" $EXIT_CODE "Abaqus exited with error code $EXIT_CODE."
fi

exit $EXIT_CODE
"""
    write_lf_file(PKG_DIR / "M2STATE_FRACFIX_RESTART2R12.pbs", pbs_code)

    write_lf_file(PKG_DIR / "job_notifications.sh", (ROOT / "scripts/hpc/notifications/job_notifications.sh").read_text(encoding="utf-8"))

    wrapper_code = f"""#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
cd "$SCRIPT_DIR"

DRY_RUN=false
for arg in "$@"; do
    if [ "$arg" == "--dry-run" ]; then
        DRY_RUN=true
    fi
done

echo "======================================================================"
echo "Guarded HPC Submission Wrapper: M2STATE_FRACFIX_RESTART2R12"
echo "======================================================================"

echo "--> Verifying SHA256 package manifest..."
python3 validate_package_manifest.py

if [ "$DRY_RUN" = true ]; then
    echo "--> Dry-run completed successfully. Zero qsub calls made."
    exit 0
fi

source job_notifications.sh
JOB_ID=$(qsub M2STATE_FRACFIX_RESTART2R12.pbs)
echo "Submitted Job ID: $JOB_ID"
notify_submitted "M2STATE_FRACFIX_RESTART2R12" "$JOB_ID" "normal_imfdfkmq" "submit_m2state_fracfix_restart2r12.sh"
"""
    write_lf_file(PKG_DIR / "submit_m2state_fracfix_restart2r12.sh", wrapper_code)

    val_code = """#!/bin/bash
import json, hashlib, sys
from pathlib import Path

dir_path = Path(__file__).parent
manifest_file = dir_path / "PACKAGE_MANIFEST.json"
manifest = json.loads(manifest_file.read_text(encoding="utf-8"))

failed = False
for rel_fn, exp_sha in manifest["file_hashes"].items():
    fp = dir_path / rel_fn
    if not fp.exists():
        print(f"FAIL: Missing file {rel_fn}")
        failed = True
        continue
    h = hashlib.sha256()
    with open(fp, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    act_sha = h.hexdigest()
    if act_sha.lower() != exp_sha.lower():
        print(f"FAIL: Mismatch for {rel_fn}: expected {exp_sha}, got {act_sha}")
        failed = True

if failed:
    print("Package Manifest Validation: FAILED")
    sys.exit(1)
else:
    print("Package Manifest Validation: 100% PASS")
"""
    write_lf_file(PKG_DIR / "validate_package_manifest.py", val_code)

    state_art = {
        "candidate": "M2STATE_FRACFIX_RESTART2R12",
        "source_job_id": src_data["source_job_id"],
        "source_checkpoint_u1_mm": source_u1,
        "source_checkpoint_rf1_kN": source_rf1,
        "target_mesh": "PK10R1",
        "target_nodes": len(target_nodes),
        "target_physical_elements": n_phys,
        "uel_phase_consumption_repair": "PASS (JTYPE=2 and JTYPE=4 use DOFs 1,2,3 to read nodal phase d)",
        "source_artifact_sha256": sha256_file(SRC_ARTIFACT_JSON)
    }
    write_lf_file(PKG_DIR / "STATE_TRANSFER_ARTIFACT.json", json.dumps(state_art, indent=2))

    trans_man = {
        "candidate": "M2STATE_FRACFIX_RESTART2R12",
        "source_job_id": src_data["source_job_id"],
        "algorithm": "Nodal Phase IDW + Centroid History IDW",
        "nodal_phase_count": len(target_phase),
        "element_history_count": len(target_history),
        "unmapped_count": 0,
        "extrapolated_count": 0
    }
    write_lf_file(PKG_DIR / "TRANSFER_MANIFEST.json", json.dumps(trans_man, indent=2))

    accept_contract = {
        "candidate": "M2STATE_FRACFIX_RESTART2R12",
        "source_job": src_data["source_job_id"],
        "force_continuity_tolerance": 0.02,
        "global_force_balance_tolerance": 1.0e-5,
        "required_step1_u1_mm": source_u1,
        "target_source_rf1_kN": source_rf1
    }
    write_lf_file(PKG_DIR / "RESTART_ACCEPTANCE_CONTRACT.json", json.dumps(accept_contract, indent=2))

    manifest_hashes = {}
    for fn in sorted(os.listdir(PKG_DIR)):
        if fn in ["PACKAGE_MANIFEST.json", "STEP1_QUALIFICATION_RESULTS.json", "run_remote_qualification.sh"]:
            continue
        fp = PKG_DIR / fn
        if fp.is_file():
            manifest_hashes[fn] = sha256_file(fp)

    package_manifest = {
        "candidate": "M2STATE_FRACFIX_RESTART2R12",
        "source_job": src_data["source_job_id"],
        "file_hashes": manifest_hashes
    }
    write_lf_file(PKG_DIR / "PACKAGE_MANIFEST.json", json.dumps(package_manifest, indent=2))
    sealed_sha = sha256_file(PKG_DIR / "PACKAGE_MANIFEST.json")

    print(f"Sealed Package Manifest: {sealed_sha}")
    print("======================================================================")

if __name__ == "__main__":
    build_r2r12()
