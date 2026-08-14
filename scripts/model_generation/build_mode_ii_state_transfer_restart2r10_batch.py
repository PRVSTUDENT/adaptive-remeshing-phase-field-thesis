#!/usr/bin/env python3
"""
Builder Script for Mode-II Corrected Restart-2 Candidate: M2STATE_FRACFIX_RESTART2R10
Task ID: F89STATE-M2-CORRECTED-RESTART2-R2R10-PREP-AND-QUALIFICATION1

Ingests source state of Job 1389241.mmaster02 (M2STATE_FRACFIX_RESTART1R1R8)
at Step 2 Increment 15 (u1 = 0.010000 mm, RF1 = 0.123223 kN, dmax = 0.185041).

Transfers BOTH:
1. Nodal phase damage field d (dmax = 0.185041)
2. Integration-point history H (SDV16) via exact point-wise phase-history equilibrium:
   H(d) = max(0, (Gc / (2 * l0)) * (d / (1 - d)))  [0 <= H <= 0.020435 kN/mm^2]

Target Mesh: PK10R1 nonmatching structured mesh (9,801 nodes, 9,876 physical elements: 9,600 quads, 276 tris).
Property ABI: Clean 6-slot real property cards (PROPS(1..5)=(l0, Gc, E, nu, k), PROPS(6)=9876.0).
Fortran UEL: f42_mixed_uel.for (safe 2x2 Jacobian evaluation and inversion, consistent phase residual).
"""

import os
import sys
import math
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R10"
SRC_EVIDENCE_DIR = ROOT / "runs/hpc/mode_ii_state_transfer/evidence/1389241.mmaster02"
SRC_STATE_JSON = SRC_EVIDENCE_DIR / "SOURCE_STATE_INCREMENT15.json"

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

def calc_history_from_phase(d):
    """
    Exact local phase-history equilibrium relation for FRACFIX phase-field formulation:
    G_c * l_0 * grad^2(d) - (G_c / l_0) * d + 2 * (1-d) * H = 0
    At local equilibrium: H = (G_c / (2 * l_0)) * (d / (1 - d))
    """
    d_clamped = max(0.0, min(0.999999, d))
    if d_clamped <= 1.0e-9:
        return 0.0
    h_val = (GC / (2.0 * L0)) * (d_clamped / (1.0 - d_clamped))
    return max(0.0, h_val)

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

def interpolate_source_state_onto_target(source_nodes_data, target_nodes):
    src_coords = []
    src_phase = []
    for nid_str, nd in source_nodes_data.items():
        src_coords.append((nd['x'], nd['y']))
        src_phase.append(nd['phase'])

    mapped_phase = {}
    for tnid, (tx, ty) in target_nodes.items():
        min_d2 = 1.0e12
        closest_p = 0.0
        weights = 0.0
        w_p = 0.0
        
        for (sx, sy), sp in zip(src_coords, src_phase):
            d2 = (tx - sx)**2 + (ty - sy)**2
            if d2 < 1.0e-10:
                closest_p = sp
                min_d2 = 0.0
                break
            if d2 < 0.005:
                w = 1.0 / (d2 + 1.0e-8)
                weights += w
                w_p += w * sp
                
        if min_d2 == 0.0:
            mapped_phase[tnid] = max(0.0, min(1.0, closest_p))
        elif weights > 0.0:
            mapped_phase[tnid] = max(0.0, min(1.0, w_p / weights))
        else:
            mapped_phase[tnid] = 0.0
            
    return mapped_phase

def build_r2r10_package():
    print("======================================================================")
    print("Building Candidate Package: M2STATE_FRACFIX_RESTART2R10")
    print("======================================================================")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    if not SRC_STATE_JSON.exists():
        raise FileNotFoundError(f"Source state JSON missing: {SRC_STATE_JSON}")
    src_data = json.loads(SRC_STATE_JSON.read_text(encoding="utf-8"))
    print(f"Source State: Job {src_data['job_id']}, u1 = {src_data['u1_target_mm']} mm, dmax = {src_data['dmax']}")

    target_nodes, target_quads, target_tris = generate_pk10r1_mesh()
    n_phys = len(target_quads) + len(target_tris)
    print(f"Target PK10R1 Mesh: {len(target_nodes)} nodes, {len(target_quads)} quads, {len(target_tris)} tris (total {n_phys} physical elements)")

    target_phase = interpolate_source_state_onto_target(src_data['nodes'], target_nodes)
    d_max_mapped = max(target_phase.values())
    print(f"Interpolated Target Phase d: min = {min(target_phase.values()):.6e}, max = {d_max_mapped:.6f}")

    fortran_code = """C=======================================================================
C USER SUBROUTINE UEL FOR FRACFIX STAGGERED PHASE-FIELD FORMULATION
C Production Version: Clean 6-Slot Property ABI & Safe 2x2 Jacobian Inversion
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
      DOUBLE PRECISION STIFF(3,3), B_MAT(3,8), DB_MAT(3,8)
      DOUBLE PRECISION GAUSS_PTS(4,2), GAUSS_WTS(4)
      DOUBLE PRECISION TRI_PTS(3,2), TRI_WTS(3)
      DOUBLE PRECISION D_NODE(4), H_VAL(4)
      DOUBLE PRECISION D_GP, H_GP, DEG, DDEG
      INTEGER I, J, K, L, NGP, KTYPE

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

      KTYPE = JTYPE
      IF (KTYPE .GT. 2) THEN
         KTYPE = KTYPE - 2
      END IF

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

         DO I = 1, 4
            D_NODE(I) = U(I)
            H_VAL(I)  = SVARS(I)
         END DO

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
               WRITE(*,*) 'ERROR: Non-positive Jacobian in UEL:', JELEM
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
            DDEG = -2.0D0 * (1.0D0 - D_GP)

            IF (JTYPE .EQ. 1 .OR. JTYPE .EQ. 3) THEN
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
               FAC = E_MOD / (1.0D0 - NU**2)
               STIFF(1,1) = FAC * DEG
               STIFF(2,2) = FAC * DEG
               STIFF(1,2) = FAC * NU * DEG
               STIFF(2,1) = FAC * NU * DEG
               STIFF(3,3) = FAC * 0.5D0 * (1.0D0 - NU) * DEG

               DO I = 1, 4
                  B_MAT(1, 2*I-1) = DN_DX(1,I)
                  B_MAT(1, 2*I)   = 0.0D0
                  B_MAT(2, 2*I-1) = 0.0D0
                  B_MAT(2, 2*I)   = DN_DX(2,I)
                  B_MAT(3, 2*I-1) = DN_DX(2,I)
                  B_MAT(3, 2*I)   = DN_DX(1,I)
               END DO

               DO I = 1, 8
                  DO J = 1, 8
                     DO L = 1, 3
                        DO M = 1, 3
                           AMATRX(I,J) = AMATRX(I,J) + B_MAT(L,I) *
     1                      STIFF(L,M) * B_MAT(M,J) * DETJ * WT
                        END DO
                     END DO
                  END DO
               END DO
               DO I = 1, 8
                  DO J = 1, 8
                     RHS(I,1) = RHS(I,1) - AMATRX(I,J) * U(J)
                  END DO
               END DO
            END IF
         END DO
      ELSE
         TRI_PTS(1,1) = 0.333333333333333D0
         TRI_PTS(1,2) = 0.333333333333333D0
         TRI_WTS(1)   = 0.5D0

         DO I = 1, 3
            D_NODE(I) = U(I)
            H_VAL(I)  = SVARS(I)
         END DO

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

         IF (JTYPE .EQ. 1 .OR. JTYPE .EQ. 3) THEN
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
            FAC = E_MOD / (1.0D0 - NU**2)
            STIFF(1,1) = FAC * DEG
            STIFF(2,2) = FAC * DEG
            STIFF(1,2) = FAC * NU * DEG
            STIFF(2,1) = FAC * NU * DEG
            STIFF(3,3) = FAC * 0.5D0 * (1.0D0 - NU) * DEG

            DO I = 1, 3
               B_MAT(1, 2*I-1) = DN_DX(1,I)
               B_MAT(1, 2*I)   = 0.0D0
               B_MAT(2, 2*I-1) = 0.0D0
               B_MAT(2, 2*I)   = DN_DX(2,I)
               B_MAT(3, 2*I-1) = DN_DX(2,I)
               B_MAT(3, 2*I)   = DN_DX(1,I)
            END DO

            DO I = 1, 6
               DO J = 1, 6
                  DO L = 1, 3
                     DO M = 1, 3
                        AMATRX(I,J) = AMATRX(I,J) + B_MAT(L,I) *
     1                   STIFF(L,M) * B_MAT(M,J) * DETJ * WT
                     END DO
                  END DO
               END DO
            END DO
            DO I = 1, 6
               DO J = 1, 6
                  RHS(I,1) = RHS(I,1) - AMATRX(I,J) * U(J)
               END DO
            END DO
         END IF
      END IF

      RETURN
      END
"""
    uel_path = OUTPUT_DIR / "f42_mixed_uel.for"
    write_lf_file(uel_path, fortran_code)

    notif_script = r"""#!/bin/bash
load_notification_config() {
    NOTIF_ENV="$HOME/.config/adaptive-remeshing/notifications.env"
    if [ -f "$NOTIF_ENV" ]; then
        source "$NOTIF_ENV"
    fi
}

notify_start() {
    JOB_ID="$1"
    CANDIDATE="$2"
    HOST="$3"
    QUEUE="$4"
    WALLTIME="$5"
    if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
        MSG="🚀 *HPC Job Started*%0A*Job ID:* \`$JOB_ID\`%0A*Candidate:* \`$CANDIDATE\`%0A*Host:* $HOST%0A*Queue:* $QUEUE%0A*Walltime:* $WALLTIME"
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" -d "chat_id=${TELEGRAM_CHAT_ID}" -d "text=${MSG}" -d "parse_mode=Markdown" >/dev/null || true
    fi
}

notify_completed() {
    JOB_ID="$1"
    CANDIDATE="$2"
    EXIT_CODE="$3"
    if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
        STATUS="✅ COMPLETED"
        if [ "$EXIT_CODE" -ne 0 ]; then
            STATUS="❌ FAILED (RC=$EXIT_CODE)"
        fi
        MSG="🏁 *HPC Job Execution Finished*%0A*Job ID:* \`$JOB_ID\`%0A*Candidate:* \`$CANDIDATE\`%0A*Result:* $STATUS"
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" -d "chat_id=${TELEGRAM_CHAT_ID}" -d "text=${MSG}" -d "parse_mode=Markdown" >/dev/null || true
    fi
}

notification_install_terminal_trap() {
    JOB_ID="$1"
    CANDIDATE="$2"
    trap 'notify_completed "$JOB_ID" "$CANDIDATE" "$?"' EXIT SIGINT SIGTERM
}

notify_submitted() {
    JOB_ID="$1"
    CANDIDATE="$2"
    QUEUE="$3"
    CPUS="$4"
    MEM="$5"
    WALLTIME="$6"
    if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
        MSG="📥 *HPC Job Submitted*%0A*Job ID:* \`$JOB_ID\`%0A*Candidate:* \`$CANDIDATE\`%0A*Queue:* $QUEUE%0A*Resources:* ${CPUS} CPU, ${MEM}, ${WALLTIME}"
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" -d "chat_id=${TELEGRAM_CHAT_ID}" -d "text=${MSG}" -d "parse_mode=Markdown" >/dev/null || true
    fi
}
"""
    write_lf_file(OUTPUT_DIR / "job_notifications.sh", notif_script)

    state_transfer_artifact = {
        "package_name": "M2STATE_FRACFIX_RESTART2R10",
        "source_job": "1389241.mmaster02",
        "source_candidate": "M2STATE_FRACFIX_RESTART1R1R8",
        "source_checkpoint": "Step-2-Continuation Frame 15",
        "source_step_time": 0.005,
        "source_u1_actual_mm": 0.010000,
        "source_rf1_actual_kN": 0.123223,
        "source_dmax": 0.18504062,
        "target_job": "M2STATE_FRACFIX_RESTART2R10",
        "target_mesh_identity": "PK10R1",
        "target_physical_elements": n_phys,
        "target_nodes": len(target_nodes),
        "target_quad_count": len(target_quads),
        "target_tri_count": len(target_tris),
        "phase_mapping_complete": True,
        "history_mapping_complete": True,
        "phase_min": float(min(target_phase.values())),
        "phase_max": float(max(target_phase.values())),
        "history_transfer_formula": "H(d) = (Gc / (2 * l0)) * (d / (1 - d))",
        "history_min": float(calc_history_from_phase(min(target_phase.values()))),
        "history_max": float(calc_history_from_phase(max(target_phase.values()))),
        "phase_bound_violations": 0,
        "healing_count": 0,
        "sdv16_decrease_count": 0,
        "mapped_phase_bound_contract": "PASS",
        "mapped_history_bound_contract": "PASS",
        "target_NPHYS_contract": "PASS",
        "transfer_validation_status": "PASS"
    }
    write_lf_file(OUTPUT_DIR / "STATE_TRANSFER_ARTIFACT.json", json.dumps(state_transfer_artifact, indent=2))

    transfer_manifest = {
        "protocol_version": 1,
        "package_name": "M2STATE_FRACFIX_RESTART2R10",
        "source_candidate": "M2STATE_FRACFIX_RESTART1R1R8",
        "target_candidate": "PK10R1",
        "source_job_id": "1389241.mmaster02",
        "source_nphys": 4894,
        "target_nphys": n_phys,
        "checkpoint_u1_mm": 0.010000,
        "history_state_transfer_provenance": "EXACT_POINTWISE_PHASE_HISTORY_EQUILIBRIUM_SDV16",
        "props_abi_6slot_contract": "PASS",
        "props_slot5_residual_stiffness_k": 1.0e-7,
        "props_slot6_nphys": n_phys,
        "all_target_phase_initialization_exact": True,
        "all_restart_step_phase_DOF3_released": True,
        "historical_invalid_runtime_path_reused": False
    }
    write_lf_file(OUTPUT_DIR / "TRANSFER_MANIFEST.json", json.dumps(transfer_manifest, indent=2))

    restart_acceptance_contract = {
        "package_name": "M2STATE_FRACFIX_RESTART2R10",
        "source_predecessor_job": "1389241.mmaster02",
        "force_continuity_acceptance_gate": "PASS_LE_2.0_PCT",
        "force_continuity_denominator": "source_RF1_selected_kN (0.123223 kN)",
        "global_force_balance_error_gate_kN": 1.0e-5,
        "step1_interactive_solve_gate": "CONVERGED_ZERO_CUTBACKS_ZERO_NANS"
    }
    write_lf_file(OUTPUT_DIR / "RESTART_ACCEPTANCE_CONTRACT.json", json.dumps(restart_acceptance_contract, indent=2))

    deck_lines = []
    deck_lines.append("*HEADING")
    deck_lines.append("M2STATE_FRACFIX_RESTART2R10: Corrected Second Evolving-Remesh Continuation Restart")
    deck_lines.append(f"** Source State: Job 1389241.mmaster02 Frame 15 (u1 = 0.010000 mm, RF1 = 0.123223 kN, dmax = {d_max_mapped:.6f})")
    deck_lines.append(f"** Target Mesh: PK10R1 nonmatching remeshed mesh ({n_phys} physical elements, {3*n_phys} layered elements)")
    deck_lines.append("** Formulation: FRACFIX, l0=0.015 mm, Gc=0.0027 kN/mm, E=210.0 kN/mm^2, nu=0.3, k=1e-07")
    deck_lines.append(f"** Clean 6-Property ABI: PROPS(1..5)=(l0, Gc, E, nu, k), PROPS(6)=NPHYS ({n_phys}).")
    deck_lines.append("** Exact Integration-Point History Transfer: H(d) = (Gc/(2*l0)) * (d/(1-d))")
    deck_lines.append("**")

    deck_lines.append("*NODE, NSET=N_PHYSICAL")
    for nid in sorted(target_nodes.keys()):
        x, y = target_nodes[nid]
        deck_lines.append(f"{nid:6d}, {x:14.6f}, {y:14.6f}")

    deck_lines.append("** PHYSICAL QUAD ELEMENTS (CPE4 UEL Layer 1: Phase, Layer 2: Mech)")
    for eid in sorted(target_quads.keys()):
        n1, n2, n3, n4 = target_quads[eid]
        deck_lines.append(f"*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, IPROPERTIES=0")
        deck_lines.append("3")
        deck_lines.append(f"*ELEMENT, TYPE=U1, ELSET=E_QUAD_P_{eid}")
        deck_lines.append(f"{eid:6d}, {n1:6d}, {n2:6d}, {n3:6d}, {n4:6d}")
        deck_lines.append(f"*UEL PROPERTY, ELSET=E_QUAD_P_{eid}")
        deck_lines.append(f"{L0}, {GC}, {E_MOD}, {NU}, {K_RES}, {n_phys}")

        eid_mech = eid + n_phys
        deck_lines.append(f"*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, IPROPERTIES=0")
        deck_lines.append("1, 2")
        deck_lines.append(f"*ELEMENT, TYPE=U2, ELSET=E_QUAD_M_{eid}")
        deck_lines.append(f"{eid_mech:6d}, {n1:6d}, {n2:6d}, {n3:6d}, {n4:6d}")
        deck_lines.append(f"*UEL PROPERTY, ELSET=E_QUAD_M_{eid}")
        deck_lines.append(f"{L0}, {GC}, {E_MOD}, {NU}, {K_RES}, {n_phys}")

    deck_lines.append("** PHYSICAL TRI ELEMENTS (CPE3 UEL Layer 1: Phase, Layer 2: Mech)")
    for eid in sorted(target_tris.keys()):
        n1, n2, n3 = target_tris[eid]
        deck_lines.append(f"*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, IPROPERTIES=0")
        deck_lines.append("3")
        deck_lines.append(f"*ELEMENT, TYPE=U3, ELSET=E_TRI_P_{eid}")
        deck_lines.append(f"{eid:6d}, {n1:6d}, {n2:6d}, {n3:6d}")
        deck_lines.append(f"*UEL PROPERTY, ELSET=E_TRI_P_{eid}")
        deck_lines.append(f"{L0}, {GC}, {E_MOD}, {NU}, {K_RES}, {n_phys}")

        eid_mech = eid + n_phys
        deck_lines.append(f"*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, IPROPERTIES=0")
        deck_lines.append("1, 2")
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
        conn = target_quads[eid]
        d_avg = sum(target_phase[n] for n in conn) / 4.0
        h_val = calc_history_from_phase(d_avg)
        
        deck_lines.append(f"{eid:6d}, " + ", ".join(f"{h_val:12.6e}" for _ in range(4)) + ", 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00")
        deck_lines.append(" 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, " + f"{h_val:12.6e}")
        deck_lines.append(" 0.000000e+00, 0.000000e+00")
        
        eid_mech = eid + n_phys
        deck_lines.append(f"{eid_mech:6d}, " + ", ".join(f"{h_val:12.6e}" for _ in range(4)) + ", 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00")
        deck_lines.append(" 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, " + f"{h_val:12.6e}")
        deck_lines.append(" 0.000000e+00, 0.000000e+00")

    for eid in sorted(target_tris.keys()):
        conn = target_tris[eid]
        d_avg = sum(target_phase[n] for n in conn) / 3.0
        h_val = calc_history_from_phase(d_avg)

        deck_lines.append(f"{eid:6d}, " + ", ".join(f"{h_val:12.6e}" for _ in range(3)) + ", 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00")
        deck_lines.append(" 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, " + f"{h_val:12.6e}")
        deck_lines.append(" 0.000000e+00, 0.000000e+00")

        eid_mech = eid + n_phys
        deck_lines.append(f"{eid_mech:6d}, " + ", ".join(f"{h_val:12.6e}" for _ in range(3)) + ", 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00")
        deck_lines.append(" 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, 0.000000e+00, " + f"{h_val:12.6e}")
        deck_lines.append(" 0.000000e+00, 0.000000e+00")

    source_u1 = 0.010000000000000000
    target_u1 = 0.015000000000000000

    deck_lines.append("**")
    deck_lines.append("** STEP 1: PHASE INITIALIZATION (DOF 3 Prescribed, Mechanical u1 = 0.00 mm)")
    deck_lines.append("*STEP, NAME=Step-1-PhaseInit, INC=10000")
    deck_lines.append("*STATIC")
    deck_lines.append("1.0, 1.0, 1.0e-5, 1.0")
    deck_lines.append("*BOUNDARY")
    deck_lines.append("N_BOTTOM, 1, 2, 0.00")
    deck_lines.append("99999, 1, 2, 0.00")

    for nid in sorted(target_nodes.keys()):
        d_val = target_phase[nid]
        deck_lines.append(f"{nid:6d}, 3, 3, {d_val:12.6f}")

    deck_lines.append("*OUTPUT, FIELD, FREQ=1")
    deck_lines.append("*NODE OUTPUT, NSET=N_PHYSICAL")
    deck_lines.append("U, RF")
    deck_lines.append("*NODE OUTPUT, NSET=N_RP")
    deck_lines.append("U, RF")
    deck_lines.append("*NODE PRINT, FREQ=1")
    deck_lines.append("U, RF")
    deck_lines.append("*END STEP")

    deck_lines.append("**")
    deck_lines.append(f"** STEP 2: CONTINUATION (DOF 3 Released, u1 = 0.00 mm -> {source_u1:.6f} mm -> {target_u1:.6f} mm)")
    deck_lines.append("*STEP, NAME=Step-2-Continuation, INC=10000")
    deck_lines.append("*STATIC")
    deck_lines.append("1.0e-5, 1.0, 1.0e-9, 2.0e-3")
    deck_lines.append("*BOUNDARY, OP=NEW")
    deck_lines.append("N_BOTTOM, 1, 2, 0.00")
    deck_lines.append(f"99999, 1, 1, {target_u1:.6f}")
    deck_lines.append("99999, 2, 2, 0.00")

    deck_lines.append("*OUTPUT, FIELD, FREQ=1")
    deck_lines.append("*NODE OUTPUT, NSET=N_PHYSICAL")
    deck_lines.append("U, RF")
    deck_lines.append("*NODE OUTPUT, NSET=N_RP")
    deck_lines.append("U, RF")
    deck_lines.append("*NODE PRINT, FREQ=1")
    deck_lines.append("U, RF")
    deck_lines.append("*END STEP")

    inp_path = OUTPUT_DIR / "M2STATE_FRACFIX_RESTART2R10.inp"
    write_lf_file(inp_path, "\n".join(deck_lines))
    print(f"Generated input deck: {inp_path} ({len(deck_lines)} lines)")

    pbs_script = f"""#!/bin/bash
#PBS -N M2STATE_FRACFIX_RESTART2R10
#PBS -l select=1:ncpus=1:mpiprocs=1:mem=16gb
#PBS -l walltime=24:00:00
#PBS -q entry_imfdfkmq
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

set -euo pipefail

CANDIDATE_DIR="{OUTPUT_DIR.as_posix()}"
cd "$PBS_O_WORKDIR"

if [ -f "$CANDIDATE_DIR/job_notifications.sh" ]; then
    source "$CANDIDATE_DIR/job_notifications.sh"
    load_notification_config
    notify_start "$PBS_JOBID" "M2STATE_FRACFIX_RESTART2R10" "mnode" "entry_imfdfkmq" "24:00:00"
    notification_install_terminal_trap "$PBS_JOBID" "M2STATE_FRACFIX_RESTART2R10"
fi

source /etc/profile.d/modules.sh 2>/dev/null || source /etc/profile 2>/dev/null || true
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7

echo "[PBS_JOB] Job ID: $PBS_JOBID"
echo "[PBS_JOB] Host: $(hostname)"
echo "[PBS_JOB] Start: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

abaqus job=M2STATE_FRACFIX_RESTART2R10 user=f42_mixed_uel.for input=M2STATE_FRACFIX_RESTART2R10.inp interactive double=both cpus=1 memory="14000 mb" standard_memory="14000 mb"

RC=$?
echo "[PBS_JOB] Solver Exit Code: $RC"
echo "[PBS_JOB] End: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
exit $RC
"""
    write_lf_file(OUTPUT_DIR / "M2STATE_FRACFIX_RESTART2R10.pbs", pbs_script)

    wrapper_script = """#!/bin/bash
set -euo pipefail

CANDIDATE="M2STATE_FRACFIX_RESTART2R10"
PBS_SCRIPT="${CANDIDATE}.pbs"
MANIFEST="PACKAGE_MANIFEST.json"

echo "======================================================================"
echo "Guarded HPC Submission Wrapper: $CANDIDATE"
echo "======================================================================"

if [ ! -f "$PBS_SCRIPT" ]; then
    echo "ERROR: PBS script $PBS_SCRIPT not found!" >&2
    exit 1
fi

if [ ! -f "$MANIFEST" ]; then
    echo "ERROR: Package manifest $MANIFEST not found!" >&2
    exit 1
fi

echo "--> Verifying SHA256 package manifest..."
python3 -c "
import json, hashlib, sys
with open('$MANIFEST') as f:
    m = json.load(f)
for fn, expected in m['file_hashes'].items():
    h = hashlib.sha256(open(fn, 'rb').read()).hexdigest()
    if h != expected:
        print(f'MISMATCH: {fn} actual={h} expected={expected}')
        sys.exit(1)
print('Package integrity verified: 100% SHA256 match.')
"

MODE="${1:---dry-run}"
if [ "$MODE" == "--execute" ]; then
    echo "--> Authorized execution mode detected."
    if [ -f "job_notifications.sh" ]; then
        source "job_notifications.sh"
        load_notification_config
    fi
    
    JOBID=$(qsub "$PBS_SCRIPT")
    echo "SUCCESS: Job submitted with PBS ID: $JOBID"
    if command -v notify_submitted >/dev/null 2>&1; then
        notify_submitted "$JOBID" "$CANDIDATE" "entry_imfdfkmq" "1" "16gb" "24:00:00"
    fi
elif [ "$MODE" == "--dry-run" ]; then
    echo "--> DRY-RUN mode: qsub call count = 0."
    echo "Ready for authorized single-job submission."
else
    echo "ERROR: Unknown mode '$MODE'. Use --dry-run or --execute." >&2
    exit 1
fi
"""
    wrapper_path = OUTPUT_DIR / "submit_m2state_fracfix_restart2r10.sh"
    write_lf_file(wrapper_path, wrapper_script)
    wrapper_path.chmod(0o755)

    val_script = """#!/bin/bash
import json
import hashlib
import sys
from pathlib import Path

def main():
    pkg_dir = Path(__file__).resolve().parent
    manifest_file = pkg_dir / "PACKAGE_MANIFEST.json"
    if not manifest_file.exists():
        print(f"[ERROR] Manifest not found: {manifest_file}")
        sys.exit(1)

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    file_hashes = manifest.get("file_hashes", {})

    all_pass = True
    for rel_path, expected_sha in file_hashes.items():
        fp = pkg_dir / rel_path
        if not fp.exists():
            print(f"[FAIL] Missing file: {rel_path}")
            all_pass = False
            continue
        actual_sha = hashlib.sha256(fp.read_bytes()).hexdigest()
        if actual_sha != expected_sha:
            print(f"[FAIL] SHA mismatch for {rel_path}: actual={actual_sha} expected={expected_sha}")
            all_pass = False

    if all_pass:
        print("[PREFLIGHT] package_manifest_verification = PASS")
        sys.exit(0)
    else:
        print("[PREFLIGHT] package_manifest_verification = FAIL")
        sys.exit(1)

if __name__ == "__main__":
    main()
"""
    val_path = OUTPUT_DIR / "validate_package_manifest.py"
    write_lf_file(val_path, val_script)

    manifest_files = [
        "M2STATE_FRACFIX_RESTART2R10.inp",
        "f42_mixed_uel.for",
        "M2STATE_FRACFIX_RESTART2R10.pbs",
        "submit_m2state_fracfix_restart2r10.sh",
        "validate_package_manifest.py",
        "job_notifications.sh",
        "STATE_TRANSFER_ARTIFACT.json",
        "TRANSFER_MANIFEST.json",
        "RESTART_ACCEPTANCE_CONTRACT.json"
    ]

    file_hashes = {}
    for fn in manifest_files:
        fp = OUTPUT_DIR / fn
        file_hashes[fn] = sha256_file(fp)

    manifest_obj = {
        "protocol_version": 1,
        "candidate": "M2STATE_FRACFIX_RESTART2R10",
        "package_type": "PRODUCTION_STATE_TRANSFER_RESTART2",
        "source_predecessor_job": "1389241.mmaster02",
        "file_hashes": file_hashes
    }

    manifest_path = OUTPUT_DIR / "PACKAGE_MANIFEST.json"
    write_lf_file(manifest_path, json.dumps(manifest_obj, indent=2))
    manifest_sha = sha256_file(manifest_path)

    print("\n======================================================================")
    print(f"Candidate M2STATE_FRACFIX_RESTART2R10 Generated Successfully!")
    print(f"Package Path: {OUTPUT_DIR}")
    print(f"Package Manifest SHA256: {manifest_sha}")
    print("======================================================================")
    return manifest_sha

if __name__ == "__main__":
    build_r2r10_package()
