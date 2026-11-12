C=======================================================================
C TASK F1721: PANDEY-KUMAR METHOD A STAGGERED OPERATOR-SPLIT COUPLING
C Subroutine: f1721_proposed_staggered_coupling_uel.for
C
C Purpose:
C   Versioned proposed subroutine restoring the authentic staggered
C   operator-split contract (Molnár & Gravouil 2017 Ref. [72];
C   Pandey & Kumar 2025 Sec. 3.2).
C   - Layer 1 (Quad PF, line 397) & Layer 3 (Tri PF, line 661): read SV_H_COMMITTED
C   - Layer 2 (Quad Mech, line 452) & Layer 4 (Tri Mech, line 709): read SV_PHASE_COMMITTED
C   - Eliminates uncoupled intra-increment Picard iteration feedback loop
C   - Preserves trial-state writes (SV_PHASE_TRIAL, SV_H_TRIAL) for LOP=2 commit
C   - Direct UEL-to-UMAT integration-point stress coupling preserved
C   - Canonical and F1720 production UELs remain bitwise untouched
C
C Architecture:
C   - Layer 1 (JTYPE=1 quad, JTYPE=3 tri): Phase-field UEL (DOF 3)
C   - Layer 2 (JTYPE=2 quad, JTYPE=4 tri): Displacement UEL (DOF 1, 2)
C     with Amor et al. (2009) volumetric-deviatoric constitutive split.
C     Computes S11, S22, S12, and out-of-plane S33. Exports stresses to
C     SV_STRESS_TRIAL(PHYSIDX, KPT, 1..4) in COMMON /CB_F1720_STRESS/.
C   - Layer 3 (Standard CPE4/CPE3 with UMAT): Standard continuum elements
C     sharing nodes with Layer 2. Retrieves authentic UEL stress from
C     SV_STRESS_TRIAL according to SCALE_MODE:
C       PROPS(4) = 0.D0: Zero-stress baseline (F1719 production dummy)
C       PROPS(4) = 1.D0: Dummy-scaled coupling (s = 10^-11 / E0)
C       PROPS(4) = 2.D0: Unscaled physical stress, dummy stiffness (DDSDDE=10^-11)
C       PROPS(4) = 3.D0: Full physical stress and physical elastic stiffness
C   - Diagnostic call-order logging in COMMON /CB_F1720_DIAG/ flushed to
C     f1720_call_order.txt in UEXTERNALDB LOP=3.
C=======================================================================

C=======================================================================
C SUBROUTINE UEXTERNALDB
C Manages initialization, history commitment across increments, and
C diagnostic call telemetry flush.
C=======================================================================
      SUBROUTINE UEXTERNALDB(LOP, LRESTART, TIME, DTIME, KSTEP, KINC)
      INCLUDE 'ABA_PARAM.INC'

      INTEGER LOP, LRESTART, KSTEP, KINC
      DOUBLE PRECISION TIME(2), DTIME

      INTEGER, PARAMETER :: N_CAPACITY = 20000

C     --- Common block for phase-field and history variables ---
      DOUBLE PRECISION SV_PHASE_COMMITTED(N_CAPACITY)
      DOUBLE PRECISION SV_PHASE_TRIAL(N_CAPACITY)
      DOUBLE PRECISION SV_H_COMMITTED(N_CAPACITY, 4)
      DOUBLE PRECISION SV_H_TRIAL(N_CAPACITY, 4)
      DOUBLE PRECISION SV_E_FRAC(N_CAPACITY)
      DOUBLE PRECISION SV_E_ELAS(N_CAPACITY)
      DOUBLE PRECISION SV_PSI_F(N_CAPACITY)
      DOUBLE PRECISION SV_PSI_E(N_CAPACITY)

      COMMON /CB_STATE_TRANS/ SV_PHASE_COMMITTED, SV_PHASE_TRIAL,
     1                        SV_H_COMMITTED, SV_H_TRIAL,
     2                        SV_E_FRAC, SV_E_ELAS,
     3                        SV_PSI_F, SV_PSI_E
      SAVE /CB_STATE_TRANS/

C     --- Common block for direct UEL-to-UMAT stress transfer ---
C     Dimensions: (N_CAPACITY, 4 Gauss points, 4 stress components: 11, 22, 33, 12)
      DOUBLE PRECISION SV_STRESS_COMMITTED(N_CAPACITY, 4, 4)
      DOUBLE PRECISION SV_STRESS_TRIAL(N_CAPACITY, 4, 4)

      COMMON /CB_F1720_STRESS/ SV_STRESS_COMMITTED, SV_STRESS_TRIAL
      SAVE /CB_F1720_STRESS/

C     --- Diagnostic call-order logging ---
      INTEGER CALL_LOG_COUNT
      INTEGER CALL_ORDER_LOG(200, 6)
      COMMON /CB_F1720_DIAG/ CALL_LOG_COUNT, CALL_ORDER_LOG
      SAVE /CB_F1720_DIAG/

      INTEGER N_PHYS_GLOBAL
      COMMON /CB_CONFIG/ N_PHYS_GLOBAL
      SAVE /CB_CONFIG/

      INTEGER I, K, C, N_ACTIVE

C     LOP = 0: Start of analysis
      IF (LOP .EQ. 0) THEN
        CALL_LOG_COUNT = 0
        DO I = 1, 200
          DO K = 1, 6
            CALL_ORDER_LOG(I, K) = 0
          ENDDO
        ENDDO

        DO I = 1, N_CAPACITY
          SV_PHASE_COMMITTED(I) = 0.D0
          SV_PHASE_TRIAL(I)     = 0.D0
          SV_E_FRAC(I)          = 0.D0
          SV_E_ELAS(I)          = 0.D0
          SV_PSI_F(I)           = 0.D0
          SV_PSI_E(I)           = 0.D0
          DO K = 1, 4
            SV_H_COMMITTED(I, K) = 0.D0
            SV_H_TRIAL(I, K)     = 0.D0
            DO C = 1, 4
              SV_STRESS_COMMITTED(I, K, C) = 0.D0
              SV_STRESS_TRIAL(I, K, C)     = 0.D0
            ENDDO
          ENDDO
        ENDDO
        N_PHYS_GLOBAL = 0

C     LOP = 1: Start of increment
      ELSE IF (LOP .EQ. 1) THEN
        DO I = 1, N_CAPACITY
          SV_PHASE_TRIAL(I) = SV_PHASE_COMMITTED(I)
          DO K = 1, 4
            SV_H_TRIAL(I, K) = SV_H_COMMITTED(I, K)
            DO C = 1, 4
              SV_STRESS_TRIAL(I, K, C) = SV_STRESS_COMMITTED(I, K, C)
            ENDDO
          ENDDO
        ENDDO

C     LOP = 2: End of increment (convergence achieved)
      ELSE IF (LOP .EQ. 2 .OR. LOP .EQ. 3 .OR. LOP .EQ. 4) THEN
        IF (N_PHYS_GLOBAL .GT. 0 .AND.
     1      N_PHYS_GLOBAL .LE. N_CAPACITY) THEN
          N_ACTIVE = N_PHYS_GLOBAL
        ELSE
          N_ACTIVE = N_CAPACITY
        ENDIF

        DO I = 1, N_ACTIVE
          SV_PHASE_COMMITTED(I) = SV_PHASE_TRIAL(I)
          DO K = 1, 4
            SV_H_COMMITTED(I, K) = SV_H_TRIAL(I, K)
            DO C = 1, 4
              SV_STRESS_COMMITTED(I, K, C) = SV_STRESS_TRIAL(I, K, C)
            ENDDO
          ENDDO
        ENDDO

C       Flush diagnostic call-order log
        CALL FLUSH_DIAG_LOG()
      ENDIF

      RETURN
      END

C=======================================================================
C SUBROUTINE FLUSH_DIAG_LOG
C Writes recorded call sequence to f1720_call_order.txt
C=======================================================================
      SUBROUTINE FLUSH_DIAG_LOG()
      INCLUDE 'ABA_PARAM.INC'

      INTEGER CALL_LOG_COUNT
      INTEGER CALL_ORDER_LOG(200, 6)
      COMMON /CB_F1720_DIAG/ CALL_LOG_COUNT, CALL_ORDER_LOG
      SAVE /CB_F1720_DIAG/

      CHARACTER*512 OUTDIR_STR, LOG_PATH
      INTEGER L_OUTDIR, I

      LOG_PATH = 'f1720_call_order.txt'
      CALL GETOUTDIR(OUTDIR_STR, L_OUTDIR)
      IF (L_OUTDIR .GT. 0) THEN
        LOG_PATH = OUTDIR_STR(1:L_OUTDIR) // '/f1720_call_order.txt'
      ENDIF

      OPEN(UNIT=98, FILE=LOG_PATH, STATUS='UNKNOWN')
      WRITE(98,*) '================================================'
      WRITE(98,*) 'F1720 ABAQUS UEL / UMAT CALL ORDER TELEMETRY LOG'
      WRITE(98,*) '================================================'
      WRITE(98,*) 'TOTAL CALLS LOGGED: ', CALL_LOG_COUNT
      WRITE(98, '(A6, 1X, A8, 1X, A8, 1X, A8, 1X, A8, 1X, A8)')
     1  'CALL', 'ROUTINE', 'ELEMENT', 'JTYPE', 'KINC', 'KITER'
      DO I = 1, MIN(CALL_LOG_COUNT, 200)
        IF (CALL_ORDER_LOG(I, 2) .EQ. 1) THEN
          WRITE(98, '(I6, 1X, A8, 1X, I8, 1X, I8, 1X, I8, 1X, I8)')
     1      CALL_ORDER_LOG(I, 1), 'UEL     ',
     2      CALL_ORDER_LOG(I, 3), CALL_ORDER_LOG(I, 4),
     3      CALL_ORDER_LOG(I, 5), CALL_ORDER_LOG(I, 6)
        ELSE
          WRITE(98, '(I6, 1X, A8, 1X, I8, 1X, I8, 1X, I8, 1X, I8)')
     1      CALL_ORDER_LOG(I, 1), 'UMAT    ',
     2      CALL_ORDER_LOG(I, 3), CALL_ORDER_LOG(I, 4),
     3      CALL_ORDER_LOG(I, 5), CALL_ORDER_LOG(I, 6)
        ENDIF
      ENDDO
      CLOSE(98)

      RETURN
      END

C=======================================================================
C SUBROUTINE UEL
C Handles phase-field and mechanical layers for Quads and Tris.
C In Layer 2 (JTYPE=2) and Layer 4 (JTYPE=4), calculates Amor split
C stresses (S11, S22, S12, S33) and exports to SV_STRESS_TRIAL.
C=======================================================================
      SUBROUTINE UEL(RHS, AMATRX, SVARS, ENERGY, NDOFEL, NRHS, NSVARS,
     1               PROPS, NPROPS, COORDS, MCRD, NNODEF, U, DU, V, A,
     2               JTYPE, TIME, DTIME, KSTEP, KINC, JELEM, PARAMS,
     3               NDLOAD, JDLTYP, ADLMAG, PREDEF, NPREDF, LFLAGS,
     4               MLVARX, DDLMAG, MDLOAD, PNEWDT, JPROPS, NJPROP,
     5               PERIOD)
      INCLUDE 'ABA_PARAM.INC'

      DOUBLE PRECISION RHS(MLVARX,*), AMATRX(NDOFEL,NDOFEL),
     1                 SVARS(*), ENERGY(8), PROPS(*),
     2                 COORDS(MCRD,NNODEF), U(*), DU(MLVARX,*),
     3                 V(MLVARX,*), A(MLVARX,*), TIME(2), PARAMS(*),
     4                 ADLMAG(MDLOAD,*), DDLMAG(MDLOAD,*),
     5                 PREDEF(2,NPREDF,NNODEF)
      INTEGER NDOFEL, NRHS, NSVARS, NPROPS, MCRD, NNODEF, JTYPE,
     1        KSTEP, KINC, JELEM, NDLOAD, JDLTYP(MDLOAD,*), NPREDF,
     2        LFLAGS(*), MLVARX, MDLOAD, JPROPS(*), NJPROP
      DOUBLE PRECISION DTIME, PNEWDT, PERIOD

      INTEGER, PARAMETER :: N_CAPACITY = 20000

      DOUBLE PRECISION SV_PHASE_COMMITTED(N_CAPACITY)
      DOUBLE PRECISION SV_PHASE_TRIAL(N_CAPACITY)
      DOUBLE PRECISION SV_H_COMMITTED(N_CAPACITY, 4)
      DOUBLE PRECISION SV_H_TRIAL(N_CAPACITY, 4)
      DOUBLE PRECISION SV_E_FRAC(N_CAPACITY)
      DOUBLE PRECISION SV_E_ELAS(N_CAPACITY)
      DOUBLE PRECISION SV_PSI_F(N_CAPACITY)
      DOUBLE PRECISION SV_PSI_E(N_CAPACITY)

      COMMON /CB_STATE_TRANS/ SV_PHASE_COMMITTED, SV_PHASE_TRIAL,
     1                        SV_H_COMMITTED, SV_H_TRIAL,
     2                        SV_E_FRAC, SV_E_ELAS,
     3                        SV_PSI_F, SV_PSI_E
      SAVE /CB_STATE_TRANS/

      DOUBLE PRECISION SV_STRESS_COMMITTED(N_CAPACITY, 4, 4)
      DOUBLE PRECISION SV_STRESS_TRIAL(N_CAPACITY, 4, 4)

      COMMON /CB_F1720_STRESS/ SV_STRESS_COMMITTED, SV_STRESS_TRIAL
      SAVE /CB_F1720_STRESS/

      INTEGER CALL_LOG_COUNT
      INTEGER CALL_ORDER_LOG(200, 6)
      COMMON /CB_F1720_DIAG/ CALL_LOG_COUNT, CALL_ORDER_LOG
      SAVE /CB_F1720_DIAG/

      INTEGER N_PHYS_GLOBAL
      COMMON /CB_CONFIG/ N_PHYS_GLOBAL
      SAVE /CB_CONFIG/

      DOUBLE PRECISION XG4(4), YG4(4), W4(4)
      DOUBLE PRECISION N_VEC(4), D_N(2,4), JAC(2,2), INVJ(2,2)
      DOUBLE PRECISION B(3,8), B_GRAD(2,4), STRAIN(3), STRESS(3)
      DOUBLE PRECISION D_ELAS(3,3), F_INT(8)
      DOUBLE PRECISION B_TRI(3,6), B_GRAD_TRI(2,3), F_INT_TRI(6)

      DOUBLE PRECISION E_L0, E_GC, E_MOD, E_NU, E_K
      DOUBLE PRECISION E_MU, E_LAMBDA, E_K_BULK
      DOUBLE PRECISION XI, ETA, DETJ, CJAC, WT, DEG, HIST, POS_M
      DOUBLE PRECISION D_VAL, D_AVG, E11, E22, E12, TR_E, EPS_DEV_SQ
      DOUBLE PRECISION S33_VAL, E_FRAC_ELEM, E_ELAS_ELEM, VOL_ELEM
      DOUBLE PRECISION PSI_F_PT, PSI_E_PT
      INTEGER I, J, K, L, KPT, N_PHYS, PHYSIDX

      DOUBLE PRECISION, PARAMETER :: ZERO = 0.D0
      DOUBLE PRECISION, PARAMETER :: HALF = 0.5D0
      DOUBLE PRECISION, PARAMETER :: ONE  = 1.0D0
      DOUBLE PRECISION, PARAMETER :: TWO  = 2.0D0
      DOUBLE PRECISION, PARAMETER :: THREE= 3.0D0
      DOUBLE PRECISION, PARAMETER :: FOUR = 4.0D0
      DOUBLE PRECISION, PARAMETER :: SIX  = 6.0D0

C     --- Call order logging ---
      IF (CALL_LOG_COUNT .LT. 200) THEN
        CALL_LOG_COUNT = CALL_LOG_COUNT + 1
        CALL_ORDER_LOG(CALL_LOG_COUNT, 1) = CALL_LOG_COUNT
        CALL_ORDER_LOG(CALL_LOG_COUNT, 2) = 1  ! 1 = UEL
        CALL_ORDER_LOG(CALL_LOG_COUNT, 3) = JELEM
        CALL_ORDER_LOG(CALL_LOG_COUNT, 4) = JTYPE
        CALL_ORDER_LOG(CALL_LOG_COUNT, 5) = KINC
        CALL_ORDER_LOG(CALL_LOG_COUNT, 6) = 0
      ENDIF

C     Material parameters from PROPS
      E_L0   = PROPS(1)
      E_GC   = PROPS(2)
      E_MOD  = PROPS(3)
      E_NU   = PROPS(4)
      E_K    = PROPS(5)
      N_PHYS = INT(PROPS(6))

      IF (N_PHYS .GT. N_PHYS_GLOBAL) THEN
        N_PHYS_GLOBAL = N_PHYS
      ENDIF

      E_MU     = E_MOD / (TWO * (ONE + E_NU))
      E_LAMBDA = (E_MOD * E_NU) / ((ONE + E_NU) * (ONE - TWO*E_NU))
      E_K_BULK = E_MOD / (THREE * (ONE - TWO*E_NU))

      DO I=1, NDOFEL
        DO J=1, NDOFEL
          AMATRX(I,J) = ZERO
        ENDDO
      ENDDO

      DO I=1, 8
        ENERGY(I) = ZERO
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

C     ------------------------------------------------------------------
C     JTYPE = 1: 4-Node Quad Phase-Field Element (DOF 3)
C     ------------------------------------------------------------------
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
          D_AVG = D_AVG + 0.25D0*U(I)
        ENDDO
        SV_PHASE_TRIAL(PHYSIDX) = D_AVG

        E_FRAC_ELEM = ZERO
        VOL_ELEM    = ZERO

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
            WRITE(7,*) 'ERROR: Non-positive Jacobian in JTYPE 1:',
     1        JELEM, DETJ
            CALL XIT
          ENDIF

          CJAC = DETJ * WT

          INVJ(1,1) =  JAC(2,2) / DETJ
          INVJ(1,2) = -JAC(1,2) / DETJ
          INVJ(2,1) = -JAC(2,1) / DETJ
          INVJ(2,2) =  JAC(1,1) / DETJ

          DO I=1, 4
            B_GRAD(1,I) = INVJ(1,1)*D_N(1,I) + INVJ(1,2)*D_N(2,I)
            B_GRAD(2,I) = INVJ(2,1)*D_N(1,I) + INVJ(2,2)*D_N(2,I)
          ENDDO

          HIST = SV_H_COMMITTED(PHYSIDX, KPT)

          DO I=1, 4
            DO J=1, 4
              AMATRX(I,J) = AMATRX(I,J) + CJAC * (
     1          (E_GC/E_L0 + TWO*HIST)*N_VEC(I)*N_VEC(J) +
     2          E_GC*E_L0*(B_GRAD(1,I)*B_GRAD(1,J) +
     3                     B_GRAD(2,I)*B_GRAD(2,J)) )
            ENDDO
          ENDDO

          D_VAL = ZERO
          DO I=1, 4
            D_VAL = D_VAL + N_VEC(I)*U(I)
          ENDDO

          DO I=1, 4
            RHS(I,1) = RHS(I,1) - CJAC * (
     1        (E_GC/E_L0 + TWO*HIST)*D_VAL*N_VEC(I) -
     2        TWO*HIST*N_VEC(I) +
     3        E_GC*E_L0*(B_GRAD(1,I)*(B_GRAD(1,1)*U(1) +
     4                                B_GRAD(1,2)*U(2) +
     5                                B_GRAD(1,3)*U(3) +
     6                                B_GRAD(1,4)*U(4)) +
     7                   B_GRAD(2,I)*(B_GRAD(2,1)*U(1) +
     8                                B_GRAD(2,2)*U(2) +
     9                                B_GRAD(2,3)*U(3) +
     1                                B_GRAD(2,4)*U(4))) )
          ENDDO

          PSI_F_PT = HALF*E_GC*( (D_VAL**2)/E_L0 + E_L0*(
     1      (B_GRAD(1,1)*U(1)+B_GRAD(1,2)*U(2)+
     2       B_GRAD(1,3)*U(3)+B_GRAD(1,4)*U(4))**2 +
     3      (B_GRAD(2,1)*U(1)+B_GRAD(2,2)*U(2)+
     4       B_GRAD(2,3)*U(3)+B_GRAD(2,4)*U(4))**2 ) )
          E_FRAC_ELEM = E_FRAC_ELEM + CJAC * PSI_F_PT
          VOL_ELEM    = VOL_ELEM + CJAC

          SVARS(KPT)   = D_VAL
          SVARS(4+KPT) = HIST
        ENDDO

        SV_E_FRAC(PHYSIDX) = E_FRAC_ELEM
        ENERGY(7) = E_FRAC_ELEM
        IF (VOL_ELEM .GT. ZERO) THEN
          SV_PSI_F(PHYSIDX) = E_FRAC_ELEM / VOL_ELEM
        ELSE
          SV_PSI_F(PHYSIDX) = ZERO
        ENDIF

C     ------------------------------------------------------------------
C     JTYPE = 2: 4-Node Quad Mechanical Element (DOFs 1, 2)
C     Amor et al. (2009) Volumetric-Deviatoric Split in Plane Strain
C     ------------------------------------------------------------------
      ELSE IF (JTYPE .EQ. 2) THEN
        D_VAL = SV_PHASE_COMMITTED(PHYSIDX)
        IF (D_VAL .NE. D_VAL) THEN
          WRITE(6,*) 'FATAL_NAN_GUARD: NaN phase in JTYPE 2:', JELEM
          PNEWDT = 0.25D0
          RETURN
        ENDIF
        IF (D_VAL .LT. ZERO) D_VAL = ZERO
        IF (D_VAL .GT. ONE)  D_VAL = ONE
        DEG   = (ONE - D_VAL)**2 + E_K

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

        E_ELAS_ELEM = ZERO
        VOL_ELEM    = ZERO

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
            WRITE(7,*) 'ERROR: Non-positive Jacobian in JTYPE 2:',
     1        JELEM, DETJ
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

          E11 = STRAIN(1)
          E22 = STRAIN(2)
          E12 = HALF * STRAIN(3)
          TR_E = E11 + E22

C         AMOR VOLUMETRIC-DEVIATORIC STIFFNESS TENSOR:
          IF (TR_E .GE. ZERO) THEN
C           Volumetric Tension: both bulk and shear degraded by g(d)
            D_ELAS(1,1) = (E_K_BULK + (FOUR/THREE)*E_MU) * DEG
            D_ELAS(1,2) = (E_K_BULK - (TWO/THREE)*E_MU) * DEG
            D_ELAS(1,3) = ZERO
            D_ELAS(2,1) = D_ELAS(1,2)
            D_ELAS(2,2) = D_ELAS(1,1)
            D_ELAS(2,3) = ZERO
            D_ELAS(3,1) = ZERO
            D_ELAS(3,2) = ZERO
            D_ELAS(3,3) = E_MU * DEG
            S33_VAL     = DEG * (E_K_BULK - (TWO/THREE)*E_MU) * TR_E
          ELSE
C           Volumetric Compression: bulk undegraded, shear degraded
            D_ELAS(1,1) = E_K_BULK + (FOUR/THREE)*E_MU * DEG
            D_ELAS(1,2) = E_K_BULK - (TWO/THREE)*E_MU * DEG
            D_ELAS(1,3) = ZERO
            D_ELAS(2,1) = D_ELAS(1,2)
            D_ELAS(2,2) = D_ELAS(1,1)
            D_ELAS(2,3) = ZERO
            D_ELAS(3,1) = ZERO
            D_ELAS(3,2) = ZERO
            D_ELAS(3,3) = E_MU * DEG
            S33_VAL     = E_K_BULK * TR_E - DEG * (TWO/THREE)*E_MU * TR_E
          ENDIF

          DO I=1, 3
            STRESS(I) = ZERO
            DO J=1, 3
              STRESS(I) = STRESS(I) + D_ELAS(I,J)*STRAIN(J)
            ENDDO
          ENDDO

C         --- EXPORT AUTHENTIC UEL STRESS TO DIRECT COUPLING INTERFACE ---
          IF (PHYSIDX .LE. N_CAPACITY .AND. PHYSIDX .GT. 0) THEN
            SV_STRESS_TRIAL(PHYSIDX, KPT, 1) = STRESS(1)  ! S11
            SV_STRESS_TRIAL(PHYSIDX, KPT, 2) = STRESS(2)  ! S22
            SV_STRESS_TRIAL(PHYSIDX, KPT, 3) = S33_VAL    ! S33
            SV_STRESS_TRIAL(PHYSIDX, KPT, 4) = STRESS(3)  ! S12
          ENDIF

          DO I=1, 8
            DO J=1, 3
              F_INT(I) = F_INT(I) + CJAC * B(J,I)*STRESS(J)
            ENDDO
            DO J=1, 8
              DO K=1, 3
                DO L=1, 3
                  AMATRX(I,J) = AMATRX(I,J) +
     1              CJAC * B(K,I)*D_ELAS(K,L)*B(L,J)
                ENDDO
              ENDDO
            ENDDO
          ENDDO

C         AMOR UNDEGRADED CRACK DRIVING ENERGY:
          EPS_DEV_SQ = (TWO/THREE)*(E11**2 - E11*E22 + E22**2) +
     1                 TWO*(E12**2)

          IF (TR_E .GT. ZERO) THEN
            POS_M = HALF * E_K_BULK * (TR_E**2) + E_MU * EPS_DEV_SQ
          ELSE
            POS_M = E_MU * EPS_DEV_SQ
          ENDIF

          HIST = SV_H_COMMITTED(PHYSIDX, KPT)
          IF (POS_M .GT. HIST) THEN
            HIST = POS_M
            SV_H_TRIAL(PHYSIDX, KPT) = POS_M
          ENDIF

          PSI_E_PT = HALF * (STRESS(1)*STRAIN(1) +
     1                       STRESS(2)*STRAIN(2) +
     2                       STRESS(3)*STRAIN(3))
          E_ELAS_ELEM = E_ELAS_ELEM + CJAC * PSI_E_PT
          VOL_ELEM    = VOL_ELEM + CJAC

          SVARS(KPT)   = STRAIN(1)
          SVARS(4+KPT) = STRESS(1)
        ENDDO

        DO I=1, 8
          RHS(I,1) = -F_INT(I)
        ENDDO

        SV_E_ELAS(PHYSIDX) = E_ELAS_ELEM
        ENERGY(2) = E_ELAS_ELEM
        IF (VOL_ELEM .GT. ZERO) THEN
          SV_PSI_E(PHYSIDX) = E_ELAS_ELEM / VOL_ELEM
        ELSE
          SV_PSI_E(PHYSIDX) = ZERO
        ENDIF

C     ------------------------------------------------------------------
C     JTYPE = 3: 3-Node Triangular Phase-Field Element (DOF 3)
C     ------------------------------------------------------------------
      ELSE IF (JTYPE .EQ. 3) THEN
        D_AVG = (U(1) + U(2) + U(3)) / THREE
        SV_PHASE_TRIAL(PHYSIDX) = D_AVG

        DETJ = (COORDS(1,2)-COORDS(1,1))*(COORDS(2,3)-COORDS(2,1)) -
     1         (COORDS(1,3)-COORDS(1,1))*(COORDS(2,2)-COORDS(2,1))
        IF (DETJ .LE. ZERO) THEN
          WRITE(7,*) 'ERROR: Non-positive Jacobian in JTYPE 3:',
     1      JELEM, DETJ
          CALL XIT
        ENDIF

        CJAC = HALF * DETJ
        VOL_ELEM = CJAC

        B_GRAD_TRI(1,1) = (COORDS(2,2) - COORDS(2,3)) / DETJ
        B_GRAD_TRI(1,2) = (COORDS(2,3) - COORDS(2,1)) / DETJ
        B_GRAD_TRI(1,3) = (COORDS(2,1) - COORDS(2,2)) / DETJ

        B_GRAD_TRI(2,1) = (COORDS(1,3) - COORDS(1,2)) / DETJ
        B_GRAD_TRI(2,2) = (COORDS(1,1) - COORDS(1,3)) / DETJ
        B_GRAD_TRI(2,3) = (COORDS(1,2) - COORDS(1,1)) / DETJ

        HIST = SV_H_COMMITTED(PHYSIDX, 1)

        DO I=1, 3
          DO J=1, 3
            IF (I .EQ. J) THEN
              AMATRX(I,J) = CJAC * (
     1          (E_GC/E_L0 + TWO*HIST)/SIX +
     2          E_GC*E_L0*(B_GRAD_TRI(1,I)*B_GRAD_TRI(1,J) +
     3                     B_GRAD_TRI(2,I)*B_GRAD_TRI(2,J)) )
            ELSE
              AMATRX(I,J) = CJAC * (
     1          (E_GC/E_L0 + TWO*HIST)/12.D0 +
     2          E_GC*E_L0*(B_GRAD_TRI(1,I)*B_GRAD_TRI(1,J) +
     3                     B_GRAD_TRI(2,I)*B_GRAD_TRI(2,J)) )
            ENDIF
          ENDDO
        ENDDO

        DO I=1, 3
          RHS(I,1) = -CJAC * (
     1      (E_GC/E_L0 + TWO*HIST)*D_AVG/THREE - TWO*HIST/THREE +
     2      E_GC*E_L0*( B_GRAD_TRI(1,I)*( B_GRAD_TRI(1,1)*U(1) +
     3                                    B_GRAD_TRI(1,2)*U(2) +
     4                                    B_GRAD_TRI(1,3)*U(3) ) +
     5                  B_GRAD_TRI(2,I)*( B_GRAD_TRI(2,1)*U(1) +
     6                                    B_GRAD_TRI(2,2)*U(2) +
     7                                    B_GRAD_TRI(2,3)*U(3) ) ) )
        ENDDO

        PSI_F_PT = HALF*E_GC*( (D_AVG**2)/E_L0 + E_L0*(
     1    (B_GRAD_TRI(1,1)*U(1)+B_GRAD_TRI(1,2)*U(2)+
     2     B_GRAD_TRI(1,3)*U(3))**2 +
     3    (B_GRAD_TRI(2,1)*U(1)+B_GRAD_TRI(2,2)*U(2)+
     4     B_GRAD_TRI(2,3)*U(3))**2 ) )
        E_FRAC_ELEM = CJAC * PSI_F_PT

        SV_E_FRAC(PHYSIDX) = E_FRAC_ELEM
        SV_PSI_F(PHYSIDX)  = PSI_F_PT
        ENERGY(7) = E_FRAC_ELEM

        SVARS(1) = D_AVG
        SVARS(2) = HIST

C     ------------------------------------------------------------------
C     JTYPE = 4: 3-Node Triangular Mechanical Element (DOFs 1, 2)
C     Amor et al. (2009) Volumetric-Deviatoric Split in Plane Strain
C     ------------------------------------------------------------------
      ELSE IF (JTYPE .EQ. 4) THEN
        D_VAL = SV_PHASE_COMMITTED(PHYSIDX)
        IF (D_VAL .NE. D_VAL) THEN
          WRITE(6,*) 'FATAL_NAN_GUARD: NaN phase in JTYPE 4:', JELEM
          PNEWDT = 0.25D0
          RETURN
        ENDIF
        IF (D_VAL .LT. ZERO) D_VAL = ZERO
        IF (D_VAL .GT. ONE)  D_VAL = ONE
        DEG   = (ONE - D_VAL)**2 + E_K

        DETJ = (COORDS(1,2)-COORDS(1,1))*(COORDS(2,3)-COORDS(2,1)) -
     1         (COORDS(1,3)-COORDS(1,1))*(COORDS(2,2)-COORDS(2,1))
        IF (DETJ .LE. ZERO) THEN
          WRITE(7,*) 'ERROR: Non-positive Jacobian in JTYPE 4:',
     1      JELEM, DETJ
          CALL XIT
        ENDIF

        CJAC = HALF * DETJ
        VOL_ELEM = CJAC

        B_TRI(1,1) = (COORDS(2,2) - COORDS(2,3)) / DETJ
        B_TRI(1,2) = ZERO
        B_TRI(1,3) = (COORDS(2,3) - COORDS(2,1)) / DETJ
        B_TRI(1,4) = ZERO
        B_TRI(1,5) = (COORDS(2,1) - COORDS(2,2)) / DETJ
        B_TRI(1,6) = ZERO

        B_TRI(2,1) = ZERO
        B_TRI(2,2) = (COORDS(1,3) - COORDS(1,2)) / DETJ
        B_TRI(2,3) = ZERO
        B_TRI(2,4) = (COORDS(1,1) - COORDS(1,3)) / DETJ
        B_TRI(2,5) = ZERO
        B_TRI(2,6) = (COORDS(1,2) - COORDS(1,1)) / DETJ

        B_TRI(3,1) = (COORDS(1,3) - COORDS(1,2)) / DETJ
        B_TRI(3,2) = (COORDS(2,2) - COORDS(2,3)) / DETJ
        B_TRI(3,3) = (COORDS(1,1) - COORDS(1,3)) / DETJ
        B_TRI(3,4) = (COORDS(2,3) - COORDS(2,1)) / DETJ
        B_TRI(3,5) = (COORDS(1,2) - COORDS(1,1)) / DETJ
        B_TRI(3,6) = (COORDS(2,1) - COORDS(2,2)) / DETJ

        DO I=1, 3
          STRAIN(I) = ZERO
          DO J=1, 6
            STRAIN(I) = STRAIN(I) + B_TRI(I,J)*U(J)
          ENDDO
        ENDDO

        E11 = STRAIN(1)
        E22 = STRAIN(2)
        E12 = HALF * STRAIN(3)
        TR_E = E11 + E22

C       AMOR VOLUMETRIC-DEVIATORIC STIFFNESS TENSOR (TRI):
        IF (TR_E .GE. ZERO) THEN
          D_ELAS(1,1) = (E_K_BULK + (FOUR/THREE)*E_MU) * DEG
          D_ELAS(1,2) = (E_K_BULK - (TWO/THREE)*E_MU) * DEG
          D_ELAS(1,3) = ZERO
          D_ELAS(2,1) = D_ELAS(1,2)
          D_ELAS(2,2) = D_ELAS(1,1)
          D_ELAS(2,3) = ZERO
          D_ELAS(3,1) = ZERO
          D_ELAS(3,2) = ZERO
          D_ELAS(3,3) = E_MU * DEG
          S33_VAL     = DEG * (E_K_BULK - (TWO/THREE)*E_MU) * TR_E
        ELSE
          D_ELAS(1,1) = E_K_BULK + (FOUR/THREE)*E_MU * DEG
          D_ELAS(1,2) = E_K_BULK - (TWO/THREE)*E_MU * DEG
          D_ELAS(1,3) = ZERO
          D_ELAS(2,1) = D_ELAS(1,2)
          D_ELAS(2,2) = D_ELAS(1,1)
          D_ELAS(2,3) = ZERO
          D_ELAS(3,1) = ZERO
          D_ELAS(3,2) = ZERO
          D_ELAS(3,3) = E_MU * DEG
          S33_VAL     = E_K_BULK * TR_E - DEG * (TWO/THREE)*E_MU * TR_E
        ENDIF

        DO I=1, 3
          STRESS(I) = ZERO
          DO J=1, 3
            STRESS(I) = STRESS(I) + D_ELAS(I,J)*STRAIN(J)
          ENDDO
        ENDDO

C       --- EXPORT AUTHENTIC UEL STRESS (TRI) ---
        IF (PHYSIDX .LE. N_CAPACITY .AND. PHYSIDX .GT. 0) THEN
          SV_STRESS_TRIAL(PHYSIDX, 1, 1) = STRESS(1)  ! S11
          SV_STRESS_TRIAL(PHYSIDX, 1, 2) = STRESS(2)  ! S22
          SV_STRESS_TRIAL(PHYSIDX, 1, 3) = S33_VAL    ! S33
          SV_STRESS_TRIAL(PHYSIDX, 1, 4) = STRESS(3)  ! S12
        ENDIF

        DO I=1, 6
          F_INT_TRI(I) = ZERO
          DO J=1, 3
            F_INT_TRI(I) = F_INT_TRI(I) + CJAC * B_TRI(J,I)*STRESS(J)
          ENDDO
          DO J=1, 6
            DO K=1, 3
              DO L=1, 3
                AMATRX(I,J) = AMATRX(I,J) +
     1            CJAC * B_TRI(K,I)*D_ELAS(K,L)*B_TRI(L,J)
              ENDDO
            ENDDO
          ENDDO
        ENDDO

        DO I=1, 6
          RHS(I,1) = -F_INT_TRI(I)
        ENDDO

C       AMOR UNDEGRADED CRACK DRIVING ENERGY (TRI):
        EPS_DEV_SQ = (TWO/THREE)*(E11**2 - E11*E22 + E22**2) +
     1               TWO*(E12**2)

        IF (TR_E .GT. ZERO) THEN
          POS_M = HALF * E_K_BULK * (TR_E**2) + E_MU * EPS_DEV_SQ
        ELSE
          POS_M = E_MU * EPS_DEV_SQ
        ENDIF

        HIST = SV_H_COMMITTED(PHYSIDX, 1)
        IF (POS_M .GT. HIST) THEN
          HIST = POS_M
          SV_H_TRIAL(PHYSIDX, 1) = POS_M
        ENDIF

        PSI_E_PT = HALF * (STRESS(1)*STRAIN(1) +
     1                     STRESS(2)*STRAIN(2) +
     2                     STRESS(3)*STRAIN(3))
        E_ELAS_ELEM = CJAC * PSI_E_PT

        SV_E_ELAS(PHYSIDX) = E_ELAS_ELEM
        ENERGY(2) = E_ELAS_ELEM
        SV_PSI_E(PHYSIDX) = PSI_E_PT

        SVARS(1) = STRAIN(1)
        SVARS(2) = STRESS(1)
      ENDIF

      RETURN
      END

C=======================================================================
C SUBROUTINE UMAT
C Standard continuum overlay elements (Layer 3: CPE4, CPE3).
C Retrieves authentic UEL stress from SV_STRESS_TRIAL via COMMON block
C according to SCALE_MODE:
C   PROPS(1) = E0
C   PROPS(2) = NU
C   PROPS(3) = N_PHYS
C   PROPS(4) = SCALE_MODE:
C     0.D0 = Zero-stress baseline (F1719 canonical dummy visualizer)
C     1.D0 = Dummy-scaled coupling (s = 10^-11 / E0)
C     2.D0 = Unscaled physical stress, dummy stiffness (DDSDDE=10^-11)
C     3.D0 = Full physical stress and physical isotropic elasticity
C=======================================================================
      SUBROUTINE UMAT(STRESS, STATEV, DDSDDE, SSE, SPD, SCD,
     1                RPL, DDSDDT, DRPLDE, DRPLDT,
     2                STRAN, DSTRAN, TIME, DTIME, TEMP, DTEMP, PREDEF,
     3                DPRED, CMNAME, NDI, NSHR, NTENS, NSTATV, PROPS,
     4                NPROPS, COORDS, DROT, PNEWDT, CELENT, DFGRD0,
     5                DFGRD1, NOEL, NPT, KSLIP, KINC)
      INCLUDE 'ABA_PARAM.INC'

      CHARACTER*80 CMNAME
      INTEGER NDI, NSHR, NTENS, NSTATV, NPROPS, NOEL, NPT, KSLIP, KINC
      DOUBLE PRECISION STRESS(NTENS), STATEV(NSTATV),
     1                 DDSDDE(NTENS, NTENS), DDSDDT(NTENS),
     2                 DRPLDE(NTENS), STRAN(NTENS), DSTRAN(NTENS),
     3                 TIME(2), PREDEF(1), DPRED(1), PROPS(NPROPS),
     4                 COORDS(3), DROT(3,3), DFGRD0(3,3), DFGRD1(3,3)
      DOUBLE PRECISION SSE, SPD, SCD, RPL, DRPLDT, DTIME, TEMP, DTEMP,
     1                 PNEWDT, CELENT

      INTEGER, PARAMETER :: N_CAPACITY = 20000

      DOUBLE PRECISION SV_PHASE_COMMITTED(N_CAPACITY)
      DOUBLE PRECISION SV_PHASE_TRIAL(N_CAPACITY)
      DOUBLE PRECISION SV_H_COMMITTED(N_CAPACITY, 4)
      DOUBLE PRECISION SV_H_TRIAL(N_CAPACITY, 4)
      DOUBLE PRECISION SV_E_FRAC(N_CAPACITY)
      DOUBLE PRECISION SV_E_ELAS(N_CAPACITY)
      DOUBLE PRECISION SV_PSI_F(N_CAPACITY)
      DOUBLE PRECISION SV_PSI_E(N_CAPACITY)

      COMMON /CB_STATE_TRANS/ SV_PHASE_COMMITTED, SV_PHASE_TRIAL,
     1                        SV_H_COMMITTED, SV_H_TRIAL,
     2                        SV_E_FRAC, SV_E_ELAS,
     3                        SV_PSI_F, SV_PSI_E
      SAVE /CB_STATE_TRANS/

      DOUBLE PRECISION SV_STRESS_COMMITTED(N_CAPACITY, 4, 4)
      DOUBLE PRECISION SV_STRESS_TRIAL(N_CAPACITY, 4, 4)

      COMMON /CB_F1720_STRESS/ SV_STRESS_COMMITTED, SV_STRESS_TRIAL
      SAVE /CB_F1720_STRESS/

      INTEGER CALL_LOG_COUNT
      INTEGER CALL_ORDER_LOG(200, 6)
      COMMON /CB_F1720_DIAG/ CALL_LOG_COUNT, CALL_ORDER_LOG
      SAVE /CB_F1720_DIAG/

      INTEGER N_PHYS_GLOBAL
      COMMON /CB_CONFIG/ N_PHYS_GLOBAL
      SAVE /CB_CONFIG/

      INTEGER I, J, NPHYS_VAL, PHYSIDX, KPT_IDX
      DOUBLE PRECISION D_VAL, H_VAL, DEG_VAL, SCALE_MODE, SCALE_FACTOR
      DOUBLE PRECISION S11_U, S22_U, S33_U, S12_U, SVM_U
      DOUBLE PRECISION E_MOD, E_NU, E_LAM, E_G

C     --- Call order logging ---
      IF (CALL_LOG_COUNT .LT. 200) THEN
        CALL_LOG_COUNT = CALL_LOG_COUNT + 1
        CALL_ORDER_LOG(CALL_LOG_COUNT, 1) = CALL_LOG_COUNT
        CALL_ORDER_LOG(CALL_LOG_COUNT, 2) = 2  ! 2 = UMAT
        CALL_ORDER_LOG(CALL_LOG_COUNT, 3) = NOEL
        CALL_ORDER_LOG(CALL_LOG_COUNT, 4) = 0
        CALL_ORDER_LOG(CALL_LOG_COUNT, 5) = KINC
        CALL_ORDER_LOG(CALL_LOG_COUNT, 6) = NPT
      ENDIF

      IF (NPROPS .GE. 3 .AND. PROPS(3) .GT. 0.D0) THEN
        NPHYS_VAL = INT(PROPS(3))
      ELSE IF (N_PHYS_GLOBAL .GT. 0) THEN
        NPHYS_VAL = N_PHYS_GLOBAL
      ELSE
        NPHYS_VAL = 13034
      ENDIF

      SCALE_MODE = 0.D0
      IF (NPROPS .GE. 4) THEN
        SCALE_MODE = PROPS(4)
      ENDIF

      PHYSIDX = NOEL - 2 * NPHYS_VAL
      IF (PHYSIDX .LE. 0) PHYSIDX = NOEL

      KPT_IDX = NPT
      IF (KPT_IDX .GT. 4) KPT_IDX = 4
      IF (KPT_IDX .LT. 1) KPT_IDX = 1

C     Default / zero initialization
      DO I=1, NTENS
        DO J=1, NTENS
          DDSDDE(I,J) = 0.D0
        ENDDO
      ENDDO

      SSE = 0.D0
      SPD = 0.D0
      SCD = 0.D0

C     Fetch authentic UEL stress from trial interface
      IF (PHYSIDX .LE. N_CAPACITY .AND. PHYSIDX .GT. 0) THEN
        S11_U = SV_STRESS_TRIAL(PHYSIDX, KPT_IDX, 1)
        S22_U = SV_STRESS_TRIAL(PHYSIDX, KPT_IDX, 2)
        S33_U = SV_STRESS_TRIAL(PHYSIDX, KPT_IDX, 3)
        S12_U = SV_STRESS_TRIAL(PHYSIDX, KPT_IDX, 4)
      ELSE
        S11_U = 0.D0
        S22_U = 0.D0
        S33_U = 0.D0
        S12_U = 0.D0
      ENDIF

C     Compute equivalent Von Mises stress from UEL components
      SVM_U = SQRT(MAX(0.D0, 0.5D0 * ( (S11_U - S22_U)**2 +
     1                                  (S22_U - S33_U)**2 +
     2                                  (S33_U - S11_U)**2 +
     3                                  6.D0 * (S12_U**2) ) ))

C     --- SCALE_MODE BRANCHING ---
      IF (SCALE_MODE .EQ. 0.D0) THEN
C       Configuration A: Zero-stress baseline (F1719 production dummy)
        DO I=1, NTENS
          STRESS(I)   = 0.D0
          DDSDDE(I,I) = 1.D-11
        ENDDO

      ELSE IF (SCALE_MODE .EQ. 1.D0) THEN
C       Configuration B: Dummy-scaled direct coupling (s = 10^-11 / E0)
        IF (PROPS(1) .GT. 0.D0) THEN
          SCALE_FACTOR = 1.D-11 / PROPS(1)
        ELSE
          SCALE_FACTOR = 1.D-11 / 210.D0
        ENDIF

        STRESS(1) = SCALE_FACTOR * S11_U
        STRESS(2) = SCALE_FACTOR * S22_U
        IF (NTENS .GE. 3) STRESS(3) = SCALE_FACTOR * S33_U
        IF (NTENS .GE. 4) STRESS(4) = SCALE_FACTOR * S12_U

        DO I=1, NTENS
          DDSDDE(I,I) = 1.D-11
        ENDDO

      ELSE IF (SCALE_MODE .EQ. 2.D0) THEN
C       Configuration C: Unscaled physical stress with dummy stiffness
        STRESS(1) = S11_U
        STRESS(2) = S22_U
        IF (NTENS .GE. 3) STRESS(3) = S33_U
        IF (NTENS .GE. 4) STRESS(4) = S12_U

        DO I=1, NTENS
          DDSDDE(I,I) = 1.D-11
        ENDDO

      ELSE IF (SCALE_MODE .EQ. 3.D0) THEN
C       Configuration D: Full physical stress and physical isotropic elasticity
        E_MOD = PROPS(1)
        E_NU  = PROPS(2)
        E_LAM = (E_MOD * E_NU) / ((1.D0 + E_NU) * (1.D0 - 2.D0*E_NU))
        E_G   = E_MOD / (2.D0 * (1.D0 + E_NU))

        STRESS(1) = S11_U
        STRESS(2) = S22_U
        IF (NTENS .GE. 3) STRESS(3) = S33_U
        IF (NTENS .GE. 4) STRESS(4) = S12_U

C       Plane strain isotropic elasticity matrix (NDI=3, NSHR=1, NTENS=4)
        DDSDDE(1,1) = E_LAM + 2.D0*E_G
        DDSDDE(1,2) = E_LAM
        DDSDDE(1,3) = E_LAM
        DDSDDE(2,1) = E_LAM
        DDSDDE(2,2) = E_LAM + 2.D0*E_G
        DDSDDE(2,3) = E_LAM
        DDSDDE(3,1) = E_LAM
        DDSDDE(3,2) = E_LAM
        DDSDDE(3,3) = E_LAM + 2.D0*E_G
        DDSDDE(4,4) = E_G
      ENDIF

C     --- SDV Output Mapping ---
      IF (PHYSIDX .LE. N_CAPACITY .AND. PHYSIDX .GT. 0) THEN
        D_VAL = SV_PHASE_TRIAL(PHYSIDX)
        IF (D_VAL .NE. D_VAL) THEN
          D_VAL = -999.D0
        ELSE
          IF (D_VAL .LT. 0.D0) D_VAL = 0.D0
          IF (D_VAL .GT. 1.D0) D_VAL = 1.D0
        ENDIF

        H_VAL = SV_H_TRIAL(PHYSIDX, KPT_IDX)
        IF (H_VAL .NE. H_VAL) THEN
          H_VAL = -999.D0
        ELSE
          IF (H_VAL .LT. 0.D0) H_VAL = 0.D0
        ENDIF

        IF (D_VAL .GE. 0.D0) THEN
          DEG_VAL = (1.D0 - D_VAL)**2 + 1.D-7
        ELSE
          DEG_VAL = -999.D0
        ENDIF

        IF (NSTATV .GE. 1)  STATEV(1)  = D_VAL
        IF (NSTATV .GE. 2)  STATEV(2)  = H_VAL
        IF (NSTATV .GE. 3)  STATEV(3)  = S11_U
        IF (NSTATV .GE. 4)  STATEV(4)  = S22_U
        IF (NSTATV .GE. 5)  STATEV(5)  = S33_U
        IF (NSTATV .GE. 6)  STATEV(6)  = S12_U
        IF (NSTATV .GE. 7)  STATEV(7)  = SVM_U
        IF (NSTATV .GE. 14) STATEV(14) = D_VAL
        IF (NSTATV .GE. 15) STATEV(15) = DEG_VAL
        IF (NSTATV .GE. 16) STATEV(16) = H_VAL

        IF (NSTATV .GE. 17) THEN
          IF (SV_E_FRAC(PHYSIDX) .EQ. SV_E_FRAC(PHYSIDX)) THEN
            STATEV(17) = SV_E_FRAC(PHYSIDX)
          ELSE
            STATEV(17) = -999.D0
          ENDIF
        ENDIF

        IF (NSTATV .GE. 18) THEN
          IF (SV_E_ELAS(PHYSIDX) .EQ. SV_E_ELAS(PHYSIDX)) THEN
            STATEV(18) = SV_E_ELAS(PHYSIDX)
          ELSE
            STATEV(18) = -999.D0
          ENDIF
        ENDIF

        IF (NSTATV .GE. 19) THEN
          IF (SV_PSI_F(PHYSIDX) .EQ. SV_PSI_F(PHYSIDX)) THEN
            STATEV(19) = SV_PSI_F(PHYSIDX)
          ELSE
            STATEV(19) = -999.D0
          ENDIF
        ENDIF

        IF (NSTATV .GE. 20) THEN
          IF (SV_PSI_E(PHYSIDX) .EQ. SV_PSI_E(PHYSIDX)) THEN
            STATEV(20) = SV_PSI_E(PHYSIDX)
          ELSE
            STATEV(20) = -999.D0
          ENDIF
        ENDIF
      ENDIF

      RETURN
      END
