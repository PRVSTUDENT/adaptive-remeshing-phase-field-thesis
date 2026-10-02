C ======================================================================
C User Subroutine UEL: Unified Parallel-Safe Phase-Field Element (Quad)
C Clean, Abaqus-Managed SVARS Architecture (Thread-Safe & MPI-Safe)
C Elimination of COMMON blocks, UEXTERNALDB, and unmanaged global state.
C
C Formulation:
C   4-Node Quadrilateral Plane Strain Element
C   DOFs per node: 1: u_x, 2: u_y, 3: d (Phase-field)
C   Total DOFs per element: NDOFEL = 12
C
C DOF Mapping (Node a = 1..4):
C   M_u(a, 1) = 3*(a-1) + 1  (u_x)
C   M_u(a, 2) = 3*(a-1) + 2  (u_y)
C   M_d(a)    = 3*(a-1) + 3  (d)
C
C State Variables (SVARS): Managed directly per-element by Abaqus:
C   SVARS(1..4): Maximum history driving energy H_kpt at 4 Gauss points
C   SVARS(5..8): Phase-field values d_kpt at 4 Gauss points
C
C Material Properties (PROPS):
C   PROPS(1) = E_L0  (Length scale l_0)
C   PROPS(2) = E_GC  (Critical fracture energy G_c)
C   PROPS(3) = E_MOD (Young's modulus E)
C   PROPS(4) = E_NU  (Poisson's ratio nu)
C   PROPS(5) = E_K   (Residual stiffness parameter k)
C ======================================================================
      SUBROUTINE UEL(RHS,AMATRX,SVARS,ENERGY,NDOFEL,NRHS,NSVARS,
     1     PROPS,NPROPS,COORDS,MCRD,NNODE,U,DU,V,A,JTYPE,TIME,DTIME,
     2     KSTEP,KINC,JELEM,PARAMS,NDLOAD,JDLTYP,ADLMAG,PREDEF,
     3     NPREDF,LFLAGS,MLVARX,DDLMAG,MDLOAD,PNEWDT,JPROPS,NJPROP,
     4     PERIOD)
      INCLUDE 'ABA_PARAM.INC'

      PARAMETER(ZERO=0.D0,ONE=1.D0,TWO=2.D0,HALF=0.5D0)

      DIMENSION RHS(MLVARX,1),AMATRX(NDOFEL,NDOFEL),
     1     SVARS(NSVARS),ENERGY(8),PROPS(NPROPS),
     2     COORDS(MCRD,NNODE),U(NDOFEL),DU(NDOFEL),V(NDOFEL),
     3     A(NDOFEL),TIME(2),PARAMS(*),JDLTYP(MDLOAD,*),
     4     ADLMAG(MDLOAD,*),PREDEF(2,NPREDF,NNODE),
     5     LFLAGS(*),DDLMAG(MDLOAD,*),JPROPS(*)

      DOUBLE PRECISION W4(4), XG4(4), YG4(4)
      DOUBLE PRECISION B_U(3,8), B_D(2,4)
      DOUBLE PRECISION D_ELAS(3,3), STRESS(3), STRAIN(3)
      DOUBLE PRECISION N_VEC(4), D_N(2,4)
      DOUBLE PRECISION U_MECH(8), U_PHASE(4)

      INTEGER I, J, K, L, KPT, A_NODE
      DOUBLE PRECISION XI, ETA, WT, CJAC, DETJ, JAC(2,2), INVJ(2,2)
      DOUBLE PRECISION D_GP, DEG, HIST, POS_M
      DOUBLE PRECISION E_MOD, E_NU, E_L0, E_GC, E_K
      DOUBLE PRECISION E11, E22, E12, TR_E, E_POS
      DOUBLE PRECISION C11_0, C12_0, C22_0, C33_0
      DOUBLE PRECISION BDB

C     Zero residual and tangent matrix
      DO I=1, NDOFEL
        RHS(I,1) = ZERO
        DO J=1, NDOFEL
          AMATRX(I,J) = ZERO
        ENDDO
      ENDDO

C     Material parameters
      E_L0  = PROPS(1)
      E_GC  = PROPS(2)
      E_MOD = PROPS(3)
      E_NU  = PROPS(4)
      E_K   = PROPS(5)

C     Constitutive coefficients (plane strain)
      C11_0 = E_MOD*(ONE - E_NU)/((ONE + E_NU)*(ONE - TWO*E_NU))
      C12_0 = E_MOD*E_NU/((ONE + E_NU)*(ONE - TWO*E_NU))
      C22_0 = C11_0
      C33_0 = E_MOD/(TWO*(ONE + E_NU))

C     Extract nodal displacement and phase components from U
      DO A_NODE=1, 4
        U_MECH(2*A_NODE-1) = U(3*(A_NODE-1) + 1)
        U_MECH(2*A_NODE)   = U(3*(A_NODE-1) + 2)
        U_PHASE(A_NODE)    = U(3*(A_NODE-1) + 3)
      ENDDO

C     2x2 Gauss quadrature points
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

C     Loop over integration points
      DO KPT=1, 4
        XI  = XG4(KPT)
        ETA = YG4(KPT)
        WT  = W4(KPT)

C       Shape functions
        N_VEC(1) = 0.25D0*(ONE - XI)*(ONE - ETA)
        N_VEC(2) = 0.25D0*(ONE + XI)*(ONE - ETA)
        N_VEC(3) = 0.25D0*(ONE + XI)*(ONE + ETA)
        N_VEC(4) = 0.25D0*(ONE - XI)*(ONE + ETA)

C       Shape function natural derivatives
        D_N(1,1) = -0.25D0*(ONE - ETA)
        D_N(1,2) =  0.25D0*(ONE - ETA)
        D_N(1,3) =  0.25D0*(ONE + ETA)
        D_N(1,4) = -0.25D0*(ONE + ETA)

        D_N(2,1) = -0.25D0*(ONE - XI)
        D_N(2,2) = -0.25D0*(ONE + XI)
        D_N(2,3) =  0.25D0*(ONE + XI)
        D_N(2,4) =  0.25D0*(ONE - XI)

C       Jacobian matrix
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
          WRITE(7,*) 'ERROR: Non-positive Jacobian in Unified UEL:',
     1               JELEM, DETJ
          CALL XIT
        ENDIF

        CJAC = DETJ * WT

        INVJ(1,1) =  JAC(2,2) / DETJ
        INVJ(1,2) = -JAC(1,2) / DETJ
        INVJ(2,1) = -JAC(2,1) / DETJ
        INVJ(2,2) =  JAC(1,1) / DETJ

C       Mechanical B matrix (3 x 8)
        DO I=1, 4
          B_U(1, 2*I-1) = INVJ(1,1)*D_N(1,I) + INVJ(1,2)*D_N(2,I)
          B_U(1, 2*I)   = ZERO
          B_U(2, 2*I-1) = ZERO
          B_U(2, 2*I)   = INVJ(2,1)*D_N(1,I) + INVJ(2,2)*D_N(2,I)
          B_U(3, 2*I-1) = INVJ(2,1)*D_N(1,I) + INVJ(2,2)*D_N(2,I)
          B_U(3, 2*I)   = INVJ(1,1)*D_N(1,I) + INVJ(1,2)*D_N(2,I)
        ENDDO

C       Phase B matrix (2 x 4)
        DO I=1, 4
          B_D(1,I) = INVJ(1,1)*D_N(1,I) + INVJ(1,2)*D_N(2,I)
          B_D(2,I) = INVJ(2,1)*D_N(1,I) + INVJ(2,2)*D_N(2,I)
        ENDDO

C       Phase field at Gauss point
        D_GP = ZERO
        DO I=1, 4
          D_GP = D_GP + N_VEC(I)*U_PHASE(I)
        ENDDO
        IF (D_GP .LT. ZERO) D_GP = ZERO
        IF (D_GP .GT. ONE)  D_GP = ONE
        DEG = (ONE - D_GP)**2 + E_K

C       Mechanical strains at Gauss point
        DO I=1, 3
          STRAIN(I) = ZERO
          DO J=1, 8
            STRAIN(I) = STRAIN(I) + B_U(I,J)*U_MECH(J)
          ENDDO
        ENDDO

C       Undegraded driving energy calculation (spectral split / Miehe)
        E11  = STRAIN(1)
        E22  = STRAIN(2)
        E12  = HALF * STRAIN(3)
        TR_E = E11 + E22
        IF (TR_E .GT. ZERO) THEN
          E_POS = TR_E
        ELSE
          E_POS = ZERO
        ENDIF
        POS_M = HALF*C12_0*(E_POS**2) + C33_0*(E11**2+E22**2+TWO*(E12**2))

C       History variable update: Strictly managed in SVARS!
        HIST = SVARS(KPT)
        IF (POS_M .GT. HIST) THEN
          HIST = POS_M
          SVARS(KPT) = HIST
        ENDIF
        SVARS(4+KPT) = D_GP

C       Degraded elastic constitutive matrix
        D_ELAS(1,1) = C11_0 * DEG
        D_ELAS(1,2) = C12_0 * DEG
        D_ELAS(1,3) = ZERO
        D_ELAS(2,1) = C12_0 * DEG
        D_ELAS(2,2) = C22_0 * DEG
        D_ELAS(2,3) = ZERO
        D_ELAS(3,1) = ZERO
        D_ELAS(3,2) = ZERO
        D_ELAS(3,3) = C33_0 * DEG

C       Stresses
        DO I=1, 3
          STRESS(I) = ZERO
          DO J=1, 3
            STRESS(I) = STRESS(I) + D_ELAS(I,J)*STRAIN(J)
          ENDDO
        ENDDO

C       Assemble Mechanical Residual & Tangent
        DO I=1, 4
          DO J=1, 2
            RHS(3*(I-1)+J, 1) = RHS(3*(I-1)+J, 1) -
     1        CJAC * (B_U(1, 2*I-2+J)*STRESS(1) +
     2                B_U(2, 2*I-2+J)*STRESS(2) +
     3                B_U(3, 2*I-2+J)*STRESS(3))
          ENDDO
        ENDDO

        DO I=1, 4
          DO J=1, 2
            DO K=1, 4
              DO L=1, 2
                DO M=1, 3
                  DO N=1, 3
                    AMATRX(3*(I-1)+J, 3*(K-1)+L) =
     1                AMATRX(3*(I-1)+J, 3*(K-1)+L) +
     2                CJAC * B_U(M, 2*I-2+J) * D_ELAS(M,N) *
     3                       B_U(N, 2*K-2+L)
                  ENDDO
                ENDDO
              ENDDO
            ENDDO
          ENDDO
        ENDDO

C       Assemble Phase-Field Residual & Tangent
        DO I=1, 4
          DO J=1, 4
            BDB = B_D(1,I)*B_D(1,J) + B_D(2,I)*B_D(2,J)
            AMATRX(3*(I-1)+3, 3*(J-1)+3) = AMATRX(3*(I-1)+3, 3*(J-1)+3)
     1        + CJAC * ( (E_GC*E_L0)*BDB +
     2                   (E_GC/E_L0 + TWO*HIST)*N_VEC(I)*N_VEC(J) )
          ENDDO
          RHS(3*(I-1)+3, 1) = RHS(3*(I-1)+3, 1) +
     1      CJAC * TWO * HIST * N_VEC(I)
        ENDDO

      ENDDO

C     Subtract internal phase stiffness times current phase DOF from RHS
      DO I=1, 4
        DO J=1, 4
          RHS(3*(I-1)+3, 1) = RHS(3*(I-1)+3, 1) -
     1      AMATRX(3*(I-1)+3, 3*(J-1)+3) * U_PHASE(J)
        ENDDO
      ENDDO

      RETURN
      END
