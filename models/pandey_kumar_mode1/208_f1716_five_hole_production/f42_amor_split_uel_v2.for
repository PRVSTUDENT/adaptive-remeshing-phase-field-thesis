C ======================================================================
C User Subroutines UEL, UMAT & UEXTERNALDB for Abaqus
C Staggered Transactional Phase-Field Fracture Formulation
C Revision: f42_amor_split_uel_v2.for (Task F1716 Governed Production)
C Formulation: Amor et al. (2009) Volumetric-Deviatoric Split
C Support: Plane Strain, Quad (JTYPE 1,2) + Triangle (JTYPE 3,4)
C Specimen: Pandey & Kumar (2025) Section 4.5 Five-Hole Benchmark
C
C Key Improvements over v1 (f42_amor_split_uel.for):
C   1. Layer 3 UMAT restored to canonical dummy visualizer
C      (DDSDDE=1.D-11, STRESS=0). Eliminates duplicate stiffness
C      and unphysical MPC condensation NaNs.
C   2. COMMON /CB_STATE_TRANS/ and /CB_CONFIG/ reinforced with
C      Fortran SAVE attribute for shared library persistence.
C   3. Bounded capacity energy integration in UEXTERNALDB LOP=2
C      (1 .. N_ACTIVE). Prevents unvisited slot NaN corruption.
C   4. Strict bounds clamping and IEEE NaN sanitization for STATEVs.
C
C Elements:
C   JTYPE = 1: 4-Node Quad Phase Element (Active DOF 3, NDOFEL = 4)
C   JTYPE = 2: 4-Node Quad Mech Element  (Active DOFs 1, 2, NDOFEL = 8)
C   JTYPE = 3: 3-Node Tri Phase Element  (Active DOF 3, NDOFEL = 3)
C   JTYPE = 4: 3-Node Tri Mech Element   (Active DOFs 1, 2, NDOFEL = 6)
C
C UEL Property ABI:
C   PROPS(1) = E_L0   (Phase-field length scale, mm)
C   PROPS(2) = E_GC   (Critical fracture energy release rate, kN/mm)
C   PROPS(3) = E_MOD  (Young's modulus, kN/mm^2)
C   PROPS(4) = E_NU   (Poisson's ratio)
C   PROPS(5) = E_K    (Residual stiffness parameter, e.g. 1.0e-7)
C   PROPS(6) = N_PHYS (Number of finite elements / physical elements)
C
C Visualizer UMAT Property ABI:
C   PROPS(1) = E_MOD
C   PROPS(2) = E_NU
C   PROPS(3) = N_PHYS
C ======================================================================

      SUBROUTINE UEXTERNALDB(LOP,LRESTART,TIME,DTIME,KSTEP,KINC)
      INCLUDE 'ABA_PARAM.INC'
      PARAMETER(N_CAPACITY=150000)

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
      SAVE /CB_STATE_TRANS/

      INTEGER N_PHYS_GLOBAL
      COMMON /CB_CONFIG/ N_PHYS_GLOBAL
      SAVE /CB_CONFIG/

      INTEGER LOP, LRESTART, KSTEP, KINC, I, KPT, N_ACTIVE
      DOUBLE PRECISION TIME(2), DTIME
      DOUBLE PRECISION TOT_E_ELAS, TOT_E_FRAC, TOT_E_INT
      LOGICAL OP_EXISTS
      CHARACTER*512 OUTDIR_STR, CSV_FULL_PATH
      INTEGER L_OUTDIR

      IF (LOP .EQ. 0) THEN
C       Start of Analysis: Zero committed and trial arrays
        N_PHYS_GLOBAL = 0
        DO I=1, N_CAPACITY
          SV_PHASE_COMMITTED(I) = 0.D0
          SV_PHASE_TRIAL(I)     = 0.D0
          SV_E_FRAC(I)          = 0.D0
          SV_E_ELAS(I)          = 0.D0
          SV_PSI_F(I)           = 0.D0
          SV_PSI_E(I)           = 0.D0
          DO KPT=1, 4
            SV_H_COMMITTED(I, KPT) = 0.D0
            SV_H_TRIAL(I, KPT)     = 0.D0
          ENDDO
        ENDDO

C       Initialize CSV instrumentation file
        CSV_FULL_PATH = 'uel_energy_balance.csv'
        CALL GETOUTDIR(OUTDIR_STR, L_OUTDIR)
        IF (L_OUTDIR .GT. 0) THEN
          CSV_FULL_PATH = OUTDIR_STR(1:L_OUTDIR) //
     1                    '/uel_energy_balance.csv'
        ENDIF

        INQUIRE(FILE=CSV_FULL_PATH, EXIST=OP_EXISTS)
        IF (.NOT. OP_EXISTS) THEN
          OPEN(UNIT=108, FILE=CSV_FULL_PATH, STATUS='NEW',
     1         ACTION='WRITE')
          WRITE(108,1001) 'Step', 'Inc', 'TotalTime', 'StepTime',
     1                    'E_elas_J', 'E_frac_J', 'E_total_J'
 1001     FORMAT(A6, ',', A6, ',', A16, ',', A16, ',',
     1           A18, ',', A18, ',', A18)
          CLOSE(108)
        ENDIF

      ELSE IF (LOP .EQ. 1) THEN
C       Start of Increment or Cutback Retry:
C       Rollback trial state arrays from committed state arrays
        N_ACTIVE = N_PHYS_GLOBAL
        IF (N_ACTIVE .LE. 0 .OR. N_ACTIVE .GT. N_CAPACITY) THEN
          N_ACTIVE = N_CAPACITY
        ENDIF

        DO I=1, N_ACTIVE
          SV_PHASE_TRIAL(I) = SV_PHASE_COMMITTED(I)
          DO KPT=1, 4
            SV_H_TRIAL(I, KPT) = SV_H_COMMITTED(I, KPT)
          ENDDO
        ENDDO

      ELSE IF (LOP .EQ. 2) THEN
C       Successful Increment Convergence:
C       Commit trial state arrays into committed state arrays
        N_ACTIVE = N_PHYS_GLOBAL
        IF (N_ACTIVE .LE. 0 .OR. N_ACTIVE .GT. N_CAPACITY) THEN
          N_ACTIVE = N_CAPACITY
        ENDIF

        DO I=1, N_ACTIVE
          SV_PHASE_COMMITTED(I) = SV_PHASE_TRIAL(I)
          DO KPT=1, 4
            SV_H_COMMITTED(I, KPT) = SV_H_TRIAL(I, KPT)
          ENDDO
        ENDDO

C       Sum domain energies across active elements with NaN detection
        TOT_E_ELAS = 0.D0
        TOT_E_FRAC = 0.D0
        DO I=1, N_ACTIVE
          IF (SV_E_ELAS(I) .NE. SV_E_ELAS(I)) THEN
            WRITE(6,*) 'FATAL_NAN_GUARD: NaN E_ELAS in element', I
            TOT_E_ELAS = -999.D0
          ELSE IF (TOT_E_ELAS .GE. 0.D0) THEN
            TOT_E_ELAS = TOT_E_ELAS + SV_E_ELAS(I)
          ENDIF
          IF (SV_E_FRAC(I) .NE. SV_E_FRAC(I)) THEN
            WRITE(6,*) 'FATAL_NAN_GUARD: NaN E_FRAC in element', I
            TOT_E_FRAC = -999.D0
          ELSE IF (TOT_E_FRAC .GE. 0.D0) THEN
            TOT_E_FRAC = TOT_E_FRAC + SV_E_FRAC(I)
          ENDIF
        ENDDO
        TOT_E_INT = TOT_E_ELAS + TOT_E_FRAC

        CSV_FULL_PATH = 'uel_energy_balance.csv'
        CALL GETOUTDIR(OUTDIR_STR, L_OUTDIR)
        IF (L_OUTDIR .GT. 0) THEN
          CSV_FULL_PATH = OUTDIR_STR(1:L_OUTDIR) //
     1                    '/uel_energy_balance.csv'
        ENDIF

        OPEN(UNIT=108, FILE=CSV_FULL_PATH, STATUS='OLD',
     1       POSITION='APPEND', ACTION='WRITE')
        WRITE(108,1002) KSTEP, KINC, TIME(2), TIME(1),
     1                  TOT_E_ELAS, TOT_E_FRAC, TOT_E_INT
 1002   FORMAT(I6, ',', I6, ',', E16.8, ',', E16.8, ',',
     1         E18.8, ',', E18.8, ',', E18.8)
        CLOSE(108)

      ENDIF

      RETURN
      END

C ======================================================================
C SUBROUTINE UEL (Amor et al. 2009 Volumetric-Deviatoric Split)
C ======================================================================
      SUBROUTINE UEL(RHS,AMATRX,SVARS,ENERGY,NDOFEL,NRHS,NSVARS,
     1     PROPS,NPROPS,COORDS,MCRD,NNODE,U,DU,V,A,JTYPE,TIME,DTIME,
     2     KSTEP,KINC,JELEM,PARAMS,NDLOAD,JDLTYP,ADLMAG,PREDEF,
     3     NPREDF,LFLAGS,MLVARX,DDLMAG,MDLOAD,PNEWDT,JPROPS,NJPROP,
     4     PERIOD)
      INCLUDE 'ABA_PARAM.INC'
      PARAMETER(N_CAPACITY=150000)

      DIMENSION RHS(MLVARX,*),AMATRX(NDOFEL,NDOFEL),PROPS(*),
     1     SVARS(NSVARS),ENERGY(8),COORDS(MCRD,NNODE),U(NDOFEL),
     2     DU(MLVARX,*),V(NDOFEL),A(NDOFEL),TIME(2),PARAMS(*),
     3     JDLTYP(MDLOAD,*),ADLMAG(MDLOAD,*),DDLMAG(MDLOAD,*),
     4     PREDEF(2,NPREDF,NNODE),LFLAGS(*),JPROPS(*)

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
      SAVE /CB_STATE_TRANS/

      INTEGER N_PHYS_GLOBAL
      COMMON /CB_CONFIG/ N_PHYS_GLOBAL
      SAVE /CB_CONFIG/

      DOUBLE PRECISION E_L0, E_GC, E_MOD, E_NU, E_K, E_MU, E_LAMBDA
      DOUBLE PRECISION E_K_BULK
      DOUBLE PRECISION DEG, HIST, POS_M, D_VAL, D_AVG
      DOUBLE PRECISION ZERO, ONE, TWO, THREE, FOUR, SIX, HALF
      DOUBLE PRECISION XI, ETA, WT, DETJ, CJAC
      DOUBLE PRECISION XG4(4), YG4(4), W4(4)
      DOUBLE PRECISION N_VEC(4), D_N(2,4), JAC(2,2), INVJ(2,2)
      DOUBLE PRECISION B_GRAD(2,4), B(3,8), STRAIN(3), STRESS(3)
      DOUBLE PRECISION D_ELAS(3,3), F_INT(8)
      DOUBLE PRECISION E11, E22, E12, TR_E, EPS_DEV_SQ
      DOUBLE PRECISION E_ELAS_ELEM, E_FRAC_ELEM, VOL_ELEM
      DOUBLE PRECISION PSI_E_PT, PSI_F_PT
      DOUBLE PRECISION B_GRAD_TRI(2,3), B_TRI(3,6), F_INT_TRI(6)

      INTEGER I, J, K, L, KPT, PHYSIDX, N_PHYS

      PARAMETER(ZERO=0.D0, ONE=1.D0, TWO=2.D0, THREE=3.D0, FOUR=4.D0,
     1          SIX=6.D0, HALF=0.5D0)

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

          HIST = SV_H_TRIAL(PHYSIDX, KPT)

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
     1        (E_GC/E_L0 + TWO*HIST)*N_VEC(I)*D_VAL - TWO*HIST*N_VEC(I)
     2        + E_GC*E_L0*( B_GRAD(1,I)*(B_GRAD(1,1)*U(1)+
     3                                  B_GRAD(1,2)*U(2)+
     4                                  B_GRAD(1,3)*U(3)+
     5                                  B_GRAD(1,4)*U(4)) +
     6                      B_GRAD(2,I)*(B_GRAD(2,1)*U(1)+
     7                                  B_GRAD(2,2)*U(2)+
     8                                  B_GRAD(2,3)*U(3)+
     9                                  B_GRAD(2,4)*U(4)) ) )
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

        D_VAL = SV_PHASE_TRIAL(PHYSIDX)
        IF (D_VAL .NE. D_VAL) THEN
          WRITE(6,*) 'FATAL_NAN_GUARD: NaN phase in JTYPE 2:', NOEL
          PNEWDT = 0.25D0
          RETURN
        ENDIF
        IF (D_VAL .LT. ZERO) D_VAL = ZERO
        IF (D_VAL .GT. ONE)  D_VAL = ONE
        DEG   = (ONE - D_VAL)**2 + E_K

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
          ENDIF

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
                  AMATRX(I,J) = AMATRX(I,J) +
     1              CJAC * B(K,I)*D_ELAS(K,L)*B(L,J)
                ENDDO
              ENDDO
            ENDDO
          ENDDO

C         AMOR UNDEGRADED CRACK DRIVING ENERGY:
C         psi_0^+ = 1/2 * K * <tr(eps)>_+^2 + mu * (eps_dev : eps_dev)
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

        HIST = SV_H_TRIAL(PHYSIDX, 1)

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
        D_VAL = SV_PHASE_TRIAL(PHYSIDX)
        IF (D_VAL .NE. D_VAL) THEN
          WRITE(6,*) 'FATAL_NAN_GUARD: NaN phase in JTYPE 4:', NOEL
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
        ENDIF

        DO I=1, 3
          STRESS(I) = ZERO
          DO J=1, 3
            STRESS(I) = STRESS(I) + D_ELAS(I,J)*STRAIN(J)
          ENDDO
        ENDDO

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
        SV_PSI_E(PHYSIDX)  = PSI_E_PT
        ENERGY(2) = E_ELAS_ELEM

        SVARS(1) = STRAIN(1)
        SVARS(2) = STRAIN(2)
        SVARS(3) = STRAIN(3)
        SVARS(4) = STRESS(1)
        SVARS(5) = STRESS(2)
        SVARS(6) = STRESS(3)
      ENDIF

      RETURN
      END

C ======================================================================
C SUBROUTINE UMAT (Pure Dummy Visualizer Layer)
C Matches canonical f42_mixed_uel.for architecture:
C   - DDSDDE(I,I) = 1.D-11 (negligible dummy stiffness)
C   - STRESS(I) = 0.D0
C   - Copies UEL state variables to STATEV(1..20) for ODB visualization
C   - Clamps d in [0, 1] and H >= 0 with IEEE NaN protection
C ======================================================================
      SUBROUTINE UMAT(STRESS,STATEV,DDSDDE,SSE,SPD,SCD,
     1     RPL,DDSDDT,DRPLDE,DRPLDT,STRAN,DSTRAN,
     2     TIME,DTIME,TEMP,DTEMP,PREDEF,DPRED,CMNAME,
     3     NDI,NSHR,NTENS,NSTATV,PROPS,NPROPS,
     4     COORDS,DROT,PNEWDT,CELENT,DFGRD0,DFGRD1,
     5     NOEL,NPT,KSLAY,KSPT,KSTEP,KINC)
      INCLUDE 'ABA_PARAM.INC'
      PARAMETER(N_CAPACITY=150000)

      CHARACTER*80 CMNAME
      DIMENSION STRESS(NTENS),STATEV(NSTATV),DDSDDE(NTENS,NTENS),
     1     DDSDDT(NTENS),DRPLDE(NTENS),STRAN(NTENS),DSTRAN(NTENS),
     2     TIME(2),PREDEF(1),DPRED(1),PROPS(NPROPS),COORDS(3),
     3     DROT(3,3),DFGRD0(3,3),DFGRD1(3,3)

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
      SAVE /CB_STATE_TRANS/

      INTEGER N_PHYS_GLOBAL
      COMMON /CB_CONFIG/ N_PHYS_GLOBAL
      SAVE /CB_CONFIG/

      INTEGER I, J, NPHYS_VAL, PHYSIDX, KPT_IDX
      DOUBLE PRECISION D_VAL, H_VAL, DEG_VAL

      IF (NPROPS .GE. 3 .AND. PROPS(3) .GT. 0.D0) THEN
        NPHYS_VAL = INT(PROPS(3))
      ELSE IF (N_PHYS_GLOBAL .GT. 0) THEN
        NPHYS_VAL = N_PHYS_GLOBAL
      ELSE
        NPHYS_VAL = 13034
      ENDIF

      PHYSIDX = NOEL - 2 * NPHYS_VAL
      IF (PHYSIDX .LE. 0) PHYSIDX = NOEL

C     Pure dummy visualizer stiffness matrix (canonical architecture)
      DO I=1, NTENS
        STRESS(I) = 0.D0
        DO J=1, NTENS
          DDSDDE(I,J) = 0.D0
        ENDDO
        DDSDDE(I,I) = 1.D-11
      ENDDO

      SSE = 0.D0
      SPD = 0.D0
      SCD = 0.D0

      IF (PHYSIDX .LE. N_CAPACITY .AND. PHYSIDX .GT. 0) THEN
        KPT_IDX = NPT
        IF (KPT_IDX .GT. 4) KPT_IDX = 4
        IF (KPT_IDX .LT. 1) KPT_IDX = 1

        D_VAL = SV_PHASE_TRIAL(PHYSIDX)
        IF (D_VAL .NE. D_VAL) THEN
          WRITE(6,*) 'FATAL_NAN_GUARD: NaN phase in UMAT:', NOEL
          PNEWDT = 0.25D0
          D_VAL = -999.D0
        ELSE
          IF (D_VAL .LT. 0.D0) D_VAL = 0.D0
          IF (D_VAL .GT. 1.D0) D_VAL = 1.D0
        ENDIF

        H_VAL = SV_H_TRIAL(PHYSIDX, KPT_IDX)
        IF (H_VAL .NE. H_VAL) THEN
          WRITE(6,*) 'FATAL_NAN_GUARD: NaN history in UMAT:', NOEL
          PNEWDT = 0.25D0
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
