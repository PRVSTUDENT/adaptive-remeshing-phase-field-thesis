C=======================================================================
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
