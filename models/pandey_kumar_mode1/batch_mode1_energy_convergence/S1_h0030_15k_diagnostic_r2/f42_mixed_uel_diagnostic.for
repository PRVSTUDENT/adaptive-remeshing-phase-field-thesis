C ======================================================================
C User Subroutines UEL, UMAT & UEXTERNALDB for Abaqus
C Staggered Transactional Phase-Field Fracture Formulation
C Revision: f42_mixed_uel_diagnostic.for
C 4-Element Support: Quad (JTYPE 1,2) + Triangle (JTYPE 3,4)
C DIAGNOSTIC PASS: Non-invasive runtime logging of discrete coupling terms
C and call-order verification. Zero solver/mechanical perturbation.
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

C     --- NON-INVASIVE DIAGNOSTIC ARRAYS ---
      DOUBLE PRECISION SV_QD_COMMITTED(N_CAPACITY,4)
      DOUBLE PRECISION SV_QD_TRIAL(N_CAPACITY,4)
      DOUBLE PRECISION SV_DK_COMMITTED(N_CAPACITY,4)
      DOUBLE PRECISION SV_DK_TRIAL(N_CAPACITY,4)
      DOUBLE PRECISION SV_PSI0_TRIAL(N_CAPACITY,4)
      DOUBLE PRECISION SV_PSI0P_TRIAL(N_CAPACITY,4)
      DOUBLE PRECISION SV_H_READ_PHASE(N_CAPACITY,4)
      DOUBLE PRECISION SV_T_HIST_ELEM(N_CAPACITY)
      DOUBLE PRECISION SV_T_AVG_ELEM(N_CAPACITY)
      DOUBLE PRECISION SV_T_SPLIT_ELEM(N_CAPACITY)
      DOUBLE PRECISION CUM_T_HIST_COMMITTED
      DOUBLE PRECISION CUM_T_HIST_TRIAL
      DOUBLE PRECISION CUM_T_AVG_COMMITTED
      DOUBLE PRECISION CUM_T_AVG_TRIAL
      DOUBLE PRECISION CUM_T_SPLIT_COMMITTED
      DOUBLE PRECISION CUM_T_SPLIT_TRIAL
      INTEGER N_CALL_COUNT

      COMMON /CB_DIAG_STATE/ SV_QD_COMMITTED, SV_QD_TRIAL,
     1                       SV_DK_COMMITTED, SV_DK_TRIAL,
     2                       SV_PSI0_TRIAL, SV_PSI0P_TRIAL,
     3                       SV_H_READ_PHASE,
     4                       SV_T_HIST_ELEM, SV_T_AVG_ELEM,
     5                       SV_T_SPLIT_ELEM,
     6                       CUM_T_HIST_COMMITTED, CUM_T_HIST_TRIAL,
     7                       CUM_T_AVG_COMMITTED, CUM_T_AVG_TRIAL,
     8                       CUM_T_SPLIT_COMMITTED, CUM_T_SPLIT_TRIAL,
     9                       N_CALL_COUNT

      INTEGER LOP, LRESTART, KSTEP, KINC, I, KPT, N_ACTIVE
      DOUBLE PRECISION TIME(2), DTIME
      DOUBLE PRECISION TOT_E_ELAS, TOT_E_FRAC, TOT_E_INT
      DOUBLE PRECISION TOT_INC_T_HIST, TOT_INC_T_AVG, TOT_INC_T_SPLIT
      DOUBLE PRECISION CUM_T_SUM
      LOGICAL OP_EXISTS

      IF (LOP .EQ. 0) THEN
C       Start of Analysis: Zero committed and trial state & energy arrays
        DO I=1, N_CAPACITY
          SV_PHASE_COMMITTED(I) = 0.D0
          SV_PHASE_TRIAL(I)     = 0.D0
          SV_E_FRAC(I)          = 0.D0
          SV_E_ELAS(I)          = 0.D0
          SV_PSI_F(I)           = 0.D0
          SV_PSI_E(I)           = 0.D0
          SV_T_HIST_ELEM(I)     = 0.D0
          SV_T_AVG_ELEM(I)      = 0.D0
          SV_T_SPLIT_ELEM(I)    = 0.D0
          DO KPT=1, 4
            SV_H_COMMITTED(I, KPT)   = 0.D0
            SV_H_TRIAL(I, KPT)       = 0.D0
            SV_QD_COMMITTED(I, KPT)  = 0.D0
            SV_QD_TRIAL(I, KPT)      = 0.D0
            SV_DK_COMMITTED(I, KPT)  = 0.D0
            SV_DK_TRIAL(I, KPT)      = 0.D0
            SV_PSI0_TRIAL(I, KPT)    = 0.D0
            SV_PSI0P_TRIAL(I, KPT)   = 0.D0
            SV_H_READ_PHASE(I, KPT)  = 0.D0
          ENDDO
        ENDDO

        CUM_T_HIST_COMMITTED  = 0.D0
        CUM_T_HIST_TRIAL      = 0.D0
        CUM_T_AVG_COMMITTED   = 0.D0
        CUM_T_AVG_TRIAL       = 0.D0
        CUM_T_SPLIT_COMMITTED = 0.D0
        CUM_T_SPLIT_TRIAL     = 0.D0
        N_CALL_COUNT          = 0

C       Initialize CSV files
        OPEN(UNIT=105, FILE='uel_energy_balance.csv',
     1       STATUS='UNKNOWN', ACTION='WRITE')
        WRITE(105, 10) 'Step,Increment,TotalTime,StepTime,' //
     1                 'E_elastic_kNmm,E_fracture_kNmm,E_total_kNmm'
 10     FORMAT(A)

        OPEN(UNIT=106, FILE='uel_discrete_diagnostic.csv',
     1       STATUS='UNKNOWN', ACTION='WRITE')
        WRITE(106, 11) 'Step,Increment,TotalTime,StepTime,' //
     1    'E_elas_kNmm,E_frac_kNmm,E_int_kNmm,' //
     2    'Inc_T_hist_kNmm,Inc_T_avg_kNmm,Inc_T_split_kNmm,' //
     3    'Cum_T_hist_kNmm,Cum_T_avg_kNmm,Cum_T_split_kNmm,' //
     4    'Cum_T_sum_kNmm'
 11     FORMAT(A)

        OPEN(UNIT=107, FILE='uel_call_order_trace.csv',
     1       STATUS='UNKNOWN', ACTION='WRITE')
        WRITE(107, 12) 'Step,Increment,CallCount,JTYPE,NOEL,' //
     1    'PHYSIDX,H_READ,H_BEFORE,H_AFTER,DBAR_READ,DBAR_AFTER'
 12     FORMAT(A)

      ELSE IF (LOP .EQ. 1) THEN
C       Start of Increment (or Retry/Cutback): Restore Trial from Committed
        CUM_T_HIST_TRIAL  = CUM_T_HIST_COMMITTED
        CUM_T_AVG_TRIAL   = CUM_T_AVG_COMMITTED
        CUM_T_SPLIT_TRIAL = CUM_T_SPLIT_COMMITTED

        DO I=1, N_CAPACITY
          SV_PHASE_TRIAL(I)  = SV_PHASE_COMMITTED(I)
          SV_T_HIST_ELEM(I)  = 0.D0
          SV_T_AVG_ELEM(I)   = 0.D0
          SV_T_SPLIT_ELEM(I) = 0.D0
          DO KPT=1, 4
            SV_H_TRIAL(I, KPT)  = SV_H_COMMITTED(I, KPT)
            SV_QD_TRIAL(I, KPT) = SV_QD_COMMITTED(I, KPT)
            SV_DK_TRIAL(I, KPT) = SV_DK_COMMITTED(I, KPT)
          ENDDO
        ENDDO

      ELSE IF (LOP .EQ. 2) THEN
C       End of Accepted Increment: Commit Trial State and Output Energies
        DO I=1, N_CAPACITY
          SV_PHASE_COMMITTED(I) = SV_PHASE_TRIAL(I)
          DO KPT=1, 4
            SV_H_COMMITTED(I, KPT)  = SV_H_TRIAL(I, KPT)
            SV_QD_COMMITTED(I, KPT) = SV_QD_TRIAL(I, KPT)
            SV_DK_COMMITTED(I, KPT) = SV_DK_TRIAL(I, KPT)
          ENDDO
        ENDDO

C       Compute global total energies and discrete diagnostic sums
        TOT_E_ELAS      = 0.D0
        TOT_E_FRAC      = 0.D0
        TOT_INC_T_HIST  = 0.D0
        TOT_INC_T_AVG   = 0.D0
        TOT_INC_T_SPLIT = 0.D0

        DO I=1, N_CAPACITY
          TOT_E_ELAS      = TOT_E_ELAS + SV_E_ELAS(I)
          TOT_E_FRAC      = TOT_E_FRAC + SV_E_FRAC(I)
          TOT_INC_T_HIST  = TOT_INC_T_HIST  + SV_T_HIST_ELEM(I)
          TOT_INC_T_AVG   = TOT_INC_T_AVG   + SV_T_AVG_ELEM(I)
          TOT_INC_T_SPLIT = TOT_INC_T_SPLIT + SV_T_SPLIT_ELEM(I)
        ENDDO
        TOT_E_INT = TOT_E_ELAS + TOT_E_FRAC

        CUM_T_HIST_COMMITTED  = CUM_T_HIST_COMMITTED  + TOT_INC_T_HIST
        CUM_T_AVG_COMMITTED   = CUM_T_AVG_COMMITTED   + TOT_INC_T_AVG
        CUM_T_SPLIT_COMMITTED = CUM_T_SPLIT_COMMITTED + TOT_INC_T_SPLIT
        CUM_T_SUM = CUM_T_HIST_COMMITTED + CUM_T_AVG_COMMITTED +
     1              CUM_T_SPLIT_COMMITTED

        INQUIRE(UNIT=105, OPENED=OP_EXISTS)
        IF (.NOT. OP_EXISTS) THEN
          OPEN(UNIT=105, FILE='uel_energy_balance.csv',
     1         STATUS='UNKNOWN', POSITION='APPEND', ACTION='WRITE')
        ENDIF
        WRITE(105, 20) KSTEP, KINC, TIME(2), TIME(1),
     1                 TOT_E_ELAS, TOT_E_FRAC, TOT_E_INT
 20     FORMAT(I4,',',I6,',',E16.8,',',E16.8,',',E16.8,',',
     1         E16.8,',',E16.8)
        CALL FLUSH(105)

        INQUIRE(UNIT=106, OPENED=OP_EXISTS)
        IF (.NOT. OP_EXISTS) THEN
          OPEN(UNIT=106, FILE='uel_discrete_diagnostic.csv',
     1         STATUS='UNKNOWN', POSITION='APPEND', ACTION='WRITE')
        ENDIF
        WRITE(106, 21) KSTEP, KINC, TIME(2), TIME(1),
     1    TOT_E_ELAS, TOT_E_FRAC, TOT_E_INT,
     2    TOT_INC_T_HIST, TOT_INC_T_AVG, TOT_INC_T_SPLIT,
     3    CUM_T_HIST_COMMITTED, CUM_T_AVG_COMMITTED,
     4    CUM_T_SPLIT_COMMITTED, CUM_T_SUM
 21     FORMAT(I4,',',I6,',',E16.8,',',E16.8,',',E16.8,',',
     1         E16.8,',',E16.8,',',E16.8,',',E16.8,',',E16.8,',',
     2         E16.8,',',E16.8,',',E16.8,',',E16.8)
        CALL FLUSH(106)
        CALL FLUSH(107)

      ELSE IF (LOP .EQ. 3) THEN
C       End of Analysis: Close files
        INQUIRE(UNIT=105, OPENED=OP_EXISTS)
        IF (OP_EXISTS) CLOSE(105)
        INQUIRE(UNIT=106, OPENED=OP_EXISTS)
        IF (OP_EXISTS) CLOSE(106)
        INQUIRE(UNIT=107, OPENED=OP_EXISTS)
        IF (OP_EXISTS) CLOSE(107)
      ENDIF

      RETURN
      END

C ======================================================================
C User Subroutine UEL: Transactional 4-Element Phase-Field Formulation
C ======================================================================
      SUBROUTINE UEL(RHS,AMATRX,SVARS,ENERGY,NDOFEL,NRHS,NSVARS,
     1     PROPS,NPROPS,COORDS,MCRD,NNODE,U,DU,V,A,JTYPE,TIME,DTIME,
     2     KSTEP,KINC,JELEM,PARAMS,NDLOAD,JDLTYP,ADLMAG,PREDEF,
     3     NPREDF,LFLAGS,MLVARX,DDLMAG,MDLOAD,PNEWDT,JPROPS,NJPROP,
     4     PERIOD)
      INCLUDE 'ABA_PARAM.INC'
      PARAMETER(ZERO=0.D0,ONE=1.D0,TWO=2.D0,THREE=3.D0,FOUR=4.D0,
     1 HALF=0.5D0,SIX=6.D0,N_CAPACITY=150000)

      DIMENSION RHS(MLVARX,1),AMATRX(NDOFEL,NDOFEL),
     1     SVARS(NSVARS),ENERGY(8),PROPS(NPROPS),
     2     COORDS(MCRD,NNODE),U(NDOFEL),DU(NDOFEL),V(NDOFEL),
     3     A(NDOFEL),TIME(2),PARAMS(*),JDLTYP(MDLOAD,*),
     4     ADLMAG(MDLOAD,*),PREDEF(2,NPREDF,NNODE),
     5     LFLAGS(*),DDLMAG(MDLOAD,*),JPROPS(*)

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

C     --- NON-INVASIVE DIAGNOSTIC ARRAYS ---
      DOUBLE PRECISION SV_QD_COMMITTED(N_CAPACITY,4)
      DOUBLE PRECISION SV_QD_TRIAL(N_CAPACITY,4)
      DOUBLE PRECISION SV_DK_COMMITTED(N_CAPACITY,4)
      DOUBLE PRECISION SV_DK_TRIAL(N_CAPACITY,4)
      DOUBLE PRECISION SV_PSI0_TRIAL(N_CAPACITY,4)
      DOUBLE PRECISION SV_PSI0P_TRIAL(N_CAPACITY,4)
      DOUBLE PRECISION SV_H_READ_PHASE(N_CAPACITY,4)
      DOUBLE PRECISION SV_T_HIST_ELEM(N_CAPACITY)
      DOUBLE PRECISION SV_T_AVG_ELEM(N_CAPACITY)
      DOUBLE PRECISION SV_T_SPLIT_ELEM(N_CAPACITY)
      DOUBLE PRECISION CUM_T_HIST_COMMITTED
      DOUBLE PRECISION CUM_T_HIST_TRIAL
      DOUBLE PRECISION CUM_T_AVG_COMMITTED
      DOUBLE PRECISION CUM_T_AVG_TRIAL
      DOUBLE PRECISION CUM_T_SPLIT_COMMITTED
      DOUBLE PRECISION CUM_T_SPLIT_TRIAL
      INTEGER N_CALL_COUNT

      COMMON /CB_DIAG_STATE/ SV_QD_COMMITTED, SV_QD_TRIAL,
     1                       SV_DK_COMMITTED, SV_DK_TRIAL,
     2                       SV_PSI0_TRIAL, SV_PSI0P_TRIAL,
     3                       SV_H_READ_PHASE,
     4                       SV_T_HIST_ELEM, SV_T_AVG_ELEM,
     5                       SV_T_SPLIT_ELEM,
     6                       CUM_T_HIST_COMMITTED, CUM_T_HIST_TRIAL,
     7                       CUM_T_AVG_COMMITTED, CUM_T_AVG_TRIAL,
     8                       CUM_T_SPLIT_COMMITTED, CUM_T_SPLIT_TRIAL,
     9                       N_CALL_COUNT

      DOUBLE PRECISION W4(4), XG4(4), YG4(4)
      DOUBLE PRECISION W3(3), XG3(3), YG3(3)
      DOUBLE PRECISION B(3,8), B_PHASE(2,4), B_TRI(3,6), B_PHTRI(2,3)
      DOUBLE PRECISION D_ELAS(3,3), STRESS(3), STRAIN(3)
      DOUBLE PRECISION N_VEC(4), N_TRI(3), D_N(2,4), D_NTRI(2,3)
      DOUBLE PRECISION BDB

      INTEGER I, J, K, L, KPT, PHYSIDX, N_PHYS
      DOUBLE PRECISION XI, ETA, WT, CJAC, DETJ, JAC(2,2), INVJ(2,2)
      DOUBLE PRECISION D_AVG, DEG, HIST, H_BEFORE, H_AFTER, D_BEFORE
      DOUBLE PRECISION E_MOD, E_NU, E_L0, E_GC, E_K, D_VAL
      DOUBLE PRECISION E11, E22, E12, TR_E, E_POS, POS_M, PSI0_PT
      DOUBLE PRECISION C11_0, C12_0, C22_0, C33_0
      DOUBLE PRECISION C11_MECH, C12_MECH, C22_MECH, C33_MECH
      DOUBLE PRECISION F_INT(8)
      DOUBLE PRECISION D_PT, GRAD_D(2), GRAD_D_SQ, PSI_F_PT
      DOUBLE PRECISION E_FRAC_ELEM, VOL_ELEM, PSI_E_PT, E_ELAS_ELEM
      DOUBLE PRECISION D_OLD_PT, DELTA_D_PT, DELTA_DBAR, DBAR_OLD
      DOUBLE PRECISION T_HIST_INC, T_AVG_INC, T_SPLIT_INC

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

      IF (JTYPE .EQ. 1 .OR. JTYPE .EQ. 3) THEN
        IF (KSTEP .EQ. 1 .AND. KINC .LE. 1) THEN
          IF (JTYPE .EQ. 1) THEN
            DO KPT=1, 4
              SV_H_COMMITTED(PHYSIDX, KPT) = SVARS(8+KPT)
              SV_H_TRIAL(PHYSIDX, KPT)     = SVARS(8+KPT)
            ENDDO
          ELSE
            DO KPT=1, 3
              SV_H_COMMITTED(PHYSIDX, KPT) = SVARS(6+KPT)
              SV_H_TRIAL(PHYSIDX, KPT)     = SVARS(6+KPT)
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

        D_BEFORE = SV_PHASE_TRIAL(PHYSIDX)
        D_AVG = 0.25D0 * (U(1) + U(2) + U(3) + U(4))
        SV_PHASE_TRIAL(PHYSIDX) = D_AVG

        DO I=1, 4
          SV_QD_TRIAL(PHYSIDX, I) = U(I)
        ENDDO

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
            B_PHASE(1,I) = INVJ(1,1)*D_N(1,I) + INVJ(1,2)*D_N(2,I)
            B_PHASE(2,I) = INVJ(2,1)*D_N(1,I) + INVJ(2,2)*D_N(2,I)
          ENDDO

          HIST = SV_H_TRIAL(PHYSIDX, KPT)
          SV_H_READ_PHASE(PHYSIDX, KPT) = HIST

          DO I=1, 4
            DO J=1, 4
              BDB = B_PHASE(1,I)*B_PHASE(1,J) +
     1              B_PHASE(2,I)*B_PHASE(2,J)
              AMATRX(I,J) = AMATRX(I,J) + CJAC * (
     1          (E_GC*E_L0)*BDB +
     2          (E_GC/E_L0 + TWO*HIST)*N_VEC(I)*N_VEC(J)
     3        )
            ENDDO
            RHS(I,1) = RHS(I,1) + CJAC * TWO * HIST * N_VEC(I)
          ENDDO

C         Gauss-point phase-field and gradient computation for energy
          D_PT = N_VEC(1)*U(1) + N_VEC(2)*U(2) +
     1           N_VEC(3)*U(3) + N_VEC(4)*U(4)
          GRAD_D(1) = B_PHASE(1,1)*U(1) + B_PHASE(1,2)*U(2) +
     1                B_PHASE(1,3)*U(3) + B_PHASE(1,4)*U(4)
          GRAD_D(2) = B_PHASE(2,1)*U(1) + B_PHASE(2,2)*U(2) +
     1                B_PHASE(2,3)*U(3) + B_PHASE(2,4)*U(4)
          GRAD_D_SQ = GRAD_D(1)**2 + GRAD_D(2)**2
          PSI_F_PT  = E_GC * (HALF * (D_PT**2) / E_L0 +
     1                        HALF * E_L0 * GRAD_D_SQ)
          E_FRAC_ELEM = E_FRAC_ELEM + CJAC * PSI_F_PT
          VOL_ELEM    = VOL_ELEM + CJAC

          SV_DK_TRIAL(PHYSIDX, KPT) = D_PT
          SVARS(KPT)   = D_PT
          SVARS(4+KPT) = HIST
        ENDDO

        DO I=1, 4
          DO J=1, 4
            RHS(I,1) = RHS(I,1) - AMATRX(I,J)*U(J)
          ENDDO
        ENDDO

        ENERGY(7) = E_FRAC_ELEM
        SV_E_FRAC(PHYSIDX) = E_FRAC_ELEM
        IF (VOL_ELEM .GT. ZERO) THEN
          SV_PSI_F(PHYSIDX) = E_FRAC_ELEM / VOL_ELEM
        ELSE
          SV_PSI_F(PHYSIDX) = ZERO
        ENDIF

        SVARS(9)  = SV_H_TRIAL(PHYSIDX, 1)
        SVARS(10) = SV_H_TRIAL(PHYSIDX, 2)
        SVARS(11) = SV_H_TRIAL(PHYSIDX, 3)
        SVARS(12) = SV_H_TRIAL(PHYSIDX, 4)
        SVARS(13) = D_AVG
        SVARS(14) = D_AVG
        SVARS(15) = (ONE - D_AVG)**2 + E_K
        SVARS(16) = SV_H_TRIAL(PHYSIDX, 1)
        IF (NSVARS .GE. 17) SVARS(17) = E_FRAC_ELEM
        IF (NSVARS .GE. 18) SVARS(18) = SV_PSI_F(PHYSIDX)

C       Call-Order Trace Logging for representative elements
        IF (PHYSIDX .LE. 5 .OR. PHYSIDX .EQ. 33 .OR.
     1      PHYSIDX .EQ. 41) THEN
          N_CALL_COUNT = N_CALL_COUNT + 1
          WRITE(107, 30) KSTEP, KINC, N_CALL_COUNT, JTYPE, JELEM,
     1      PHYSIDX, SV_H_READ_PHASE(PHYSIDX, 1),
     2      SV_H_TRIAL(PHYSIDX, 1), SV_H_TRIAL(PHYSIDX, 1),
     3      D_BEFORE, D_AVG
 30       FORMAT(I4,',',I6,',',I8,',',I2,',',I6,',',I6,',',
     1           E14.6,',',E14.6,',',E14.6,',',E14.6,',',E14.6)
        ENDIF

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

        D_VAL = SV_PHASE_TRIAL(PHYSIDX)
        DEG   = (ONE - D_VAL)**2 + E_K

        C11_0 = E_MOD*(ONE - E_NU)/((ONE + E_NU)*(ONE - TWO*E_NU))
        C12_0 = E_MOD*E_NU/((ONE + E_NU)*(ONE - TWO*E_NU))
        C22_0 = C11_0
        C33_0 = E_MOD/(TWO*(ONE + E_NU))

        C11_MECH = C11_0 * DEG
        C12_MECH = C12_0 * DEG
        C22_MECH = C22_0 * DEG
        C33_MECH = C33_0 * DEG

        D_ELAS(1,1) = C11_MECH
        D_ELAS(1,2) = C12_MECH
        D_ELAS(1,3) = ZERO
        D_ELAS(2,1) = C12_MECH
        D_ELAS(2,2) = C22_MECH
        D_ELAS(2,3) = ZERO
        D_ELAS(3,1) = ZERO
        D_ELAS(3,2) = ZERO
        D_ELAS(3,3) = C33_MECH

        DO I=1, 8
          F_INT(I) = ZERO
        ENDDO

        E_ELAS_ELEM = ZERO
        VOL_ELEM    = ZERO
        T_HIST_INC  = ZERO
        T_AVG_INC   = ZERO
        T_SPLIT_INC = ZERO

        DBAR_OLD   = SV_PHASE_COMMITTED(PHYSIDX)
        DELTA_DBAR = D_VAL - DBAR_OLD

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

          E11 = STRAIN(1)
          E22 = STRAIN(2)
          E12 = HALF * STRAIN(3)
          TR_E = E11 + E22
          IF (TR_E .GT. ZERO) THEN
            E_POS = TR_E
          ELSE
            E_POS = ZERO
          ENDIF

C         UNDEGRADED DRIVING ENERGY COMPUTATIONS:
          PSI0_PT = HALF*C12_0*(TR_E**2) +
     1              C33_0*(E11**2 + E22**2 + TWO*(E12**2))
          POS_M   = HALF*C12_0*(E_POS**2) +
     1              C33_0*(E11**2 + E22**2 + TWO*(E12**2))

          SV_PSI0_TRIAL(PHYSIDX, KPT)  = PSI0_PT
          SV_PSI0P_TRIAL(PHYSIDX, KPT) = POS_M

          H_BEFORE = SV_H_TRIAL(PHYSIDX, KPT)
          HIST     = H_BEFORE
          IF (POS_M .GT. HIST) THEN
            HIST = POS_M
            SV_H_TRIAL(PHYSIDX, KPT) = POS_M
          ENDIF
          H_AFTER = SV_H_TRIAL(PHYSIDX, KPT)

C         Degraded elastic strain energy density at Gauss point
          PSI_E_PT = HALF * (STRESS(1)*STRAIN(1) +
     1                       STRESS(2)*STRAIN(2) +
     2                       STRESS(3)*STRAIN(3))
          E_ELAS_ELEM = E_ELAS_ELEM + CJAC * PSI_E_PT
          VOL_ELEM    = VOL_ELEM + CJAC

C         DIAGNOSTIC FINITE-INCREMENT CONTRIBUTIONS:
          D_PT       = SV_DK_TRIAL(PHYSIDX, KPT)
          D_OLD_PT   = SV_DK_COMMITTED(PHYSIDX, KPT)
          DELTA_D_PT = D_PT - D_OLD_PT

          T_HIST_INC  = T_HIST_INC + CJAC * TWO * (ONE - D_PT) *
     1                  (SV_H_READ_PHASE(PHYSIDX, KPT) - POS_M) *
     2                  DELTA_D_PT
          T_SPLIT_INC = T_SPLIT_INC + CJAC * TWO * (ONE - D_PT) *
     1                  (PSI0_PT - POS_M) * DELTA_D_PT
          T_AVG_INC   = T_AVG_INC + CJAC * (
     1                  TWO * (ONE - D_VAL) * DELTA_DBAR * PSI0_PT -
     2                  TWO * (ONE - D_PT) * DELTA_D_PT * PSI0_PT
     3                  )

          SVARS(KPT)   = STRAIN(1)
          SVARS(4+KPT) = STRESS(1)
        ENDDO

        DO I=1, 8
          RHS(I,1) = -F_INT(I)
        ENDDO

        ENERGY(2) = E_ELAS_ELEM
        SV_E_ELAS(PHYSIDX) = E_ELAS_ELEM
        IF (VOL_ELEM .GT. ZERO) THEN
          SV_PSI_E(PHYSIDX) = E_ELAS_ELEM / VOL_ELEM
        ELSE
          SV_PSI_E(PHYSIDX) = ZERO
        ENDIF

        SV_T_HIST_ELEM(PHYSIDX)  = T_HIST_INC
        SV_T_AVG_ELEM(PHYSIDX)   = T_AVG_INC
        SV_T_SPLIT_ELEM(PHYSIDX) = T_SPLIT_INC

        SVARS(9)  = D_VAL
        SVARS(10) = DEG
        SVARS(11) = SVARS(1)
        SVARS(12) = SVARS(5)
        SVARS(13) = SV_H_TRIAL(PHYSIDX, 1)
        SVARS(14) = D_VAL
        SVARS(15) = DEG
        SVARS(16) = SV_H_TRIAL(PHYSIDX, 1)
        IF (NSVARS .GE. 17) SVARS(17) = E_ELAS_ELEM
        IF (NSVARS .GE. 18) SVARS(18) = SV_PSI_E(PHYSIDX)

C       Call-Order Trace Logging for representative elements
        IF (PHYSIDX .LE. 5 .OR. PHYSIDX .EQ. 33 .OR.
     1      PHYSIDX .EQ. 41) THEN
          N_CALL_COUNT = N_CALL_COUNT + 1
          WRITE(107, 30) KSTEP, KINC, N_CALL_COUNT, JTYPE, JELEM,
     1      PHYSIDX, SV_H_READ_PHASE(PHYSIDX, 1),
     2      H_BEFORE, H_AFTER, D_VAL, D_VAL
        ENDIF

C ----------------------------------------------------------------------
C JTYPE = 3: 3-Node Triangular Phase-Field Element (DOF 3)
C ----------------------------------------------------------------------
      ELSE IF (JTYPE .EQ. 3) THEN
        XG3(1) = 0.333333333333333D0
        YG3(1) = 0.333333333333333D0
        W3(1)  = 0.5D0

        D_BEFORE = SV_PHASE_TRIAL(PHYSIDX)
        D_AVG = (U(1) + U(2) + U(3)) / THREE
        SV_PHASE_TRIAL(PHYSIDX) = D_AVG

        DO I=1, 3
          SV_QD_TRIAL(PHYSIDX, I) = U(I)
        ENDDO

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
          WRITE(7,*) 'ERROR: Non-positive Jacobian in JTYPE 3:',
     1      JELEM, DETJ
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

        HIST = SV_H_TRIAL(PHYSIDX, 1)
        SV_H_READ_PHASE(PHYSIDX, 1) = HIST

        DO I=1, 3
          DO J=1, 3
            BDB = B_PHTRI(1,I)*B_PHTRI(1,J) +
     1            B_PHTRI(2,I)*B_PHTRI(2,J)
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

C       Triangular element phase-field energy
        D_PT = N_TRI(1)*U(1) + N_TRI(2)*U(2) + N_TRI(3)*U(3)
        GRAD_D(1) = B_PHTRI(1,1)*U(1) + B_PHTRI(1,2)*U(2) +
     1              B_PHTRI(1,3)*U(3)
        GRAD_D(2) = B_PHTRI(2,1)*U(1) + B_PHTRI(2,2)*U(2) +
     1              B_PHTRI(2,3)*U(3)
        GRAD_D_SQ = GRAD_D(1)**2 + GRAD_D(2)**2
        PSI_F_PT  = E_GC * (HALF * (D_PT**2) / E_L0 +
     1                      HALF * E_L0 * GRAD_D_SQ)
        E_FRAC_ELEM = CJAC * PSI_F_PT
        VOL_ELEM    = CJAC

        SV_DK_TRIAL(PHYSIDX, 1) = D_PT

        ENERGY(7) = E_FRAC_ELEM
        SV_E_FRAC(PHYSIDX) = E_FRAC_ELEM
        SV_PSI_F(PHYSIDX)  = PSI_F_PT

        SVARS(7)  = D_AVG
        SVARS(8)  = HIST
        SVARS(9)  = HIST
        SVARS(13) = D_AVG
        SVARS(14) = D_AVG
        SVARS(15) = (ONE - D_AVG)**2 + E_K
        SVARS(16) = HIST
        IF (NSVARS .GE. 17) SVARS(17) = E_FRAC_ELEM
        IF (NSVARS .GE. 18) SVARS(18) = PSI_F_PT

        IF (PHYSIDX .LE. 5) THEN
          N_CALL_COUNT = N_CALL_COUNT + 1
          WRITE(107, 30) KSTEP, KINC, N_CALL_COUNT, JTYPE, JELEM,
     1      PHYSIDX, SV_H_READ_PHASE(PHYSIDX, 1),
     2      SV_H_TRIAL(PHYSIDX, 1), SV_H_TRIAL(PHYSIDX, 1),
     3      D_BEFORE, D_AVG
        ENDIF

C ----------------------------------------------------------------------
C JTYPE = 4: 3-Node Triangular Mechanical Element (DOFs 1, 2)
C ----------------------------------------------------------------------
      ELSE IF (JTYPE .EQ. 4) THEN
        XG3(1) = 0.333333333333333D0
        YG3(1) = 0.333333333333333D0
        W3(1)  = 0.5D0

        D_VAL = SV_PHASE_TRIAL(PHYSIDX)
        DEG   = (ONE - D_VAL)**2 + E_K

        C11_0 = E_MOD*(ONE - E_NU)/((ONE + E_NU)*(ONE - TWO*E_NU))
        C12_0 = E_MOD*E_NU/((ONE + E_NU)*(ONE - TWO*E_NU))
        C22_0 = C11_0
        C33_0 = E_MOD/(TWO*(ONE + E_NU))

        C11_MECH = C11_0 * DEG
        C12_MECH = C12_0 * DEG
        C22_MECH = C22_0 * DEG
        C33_MECH = C33_0 * DEG

        D_ELAS(1,1) = C11_MECH
        D_ELAS(1,2) = C12_MECH
        D_ELAS(1,3) = ZERO
        D_ELAS(2,1) = C12_MECH
        D_ELAS(2,2) = C22_MECH
        D_ELAS(2,3) = ZERO
        D_ELAS(3,1) = ZERO
        D_ELAS(3,2) = ZERO
        D_ELAS(3,3) = C33_MECH

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
          WRITE(7,*) 'ERROR: Non-positive Jacobian in JTYPE 4:',
     1      JELEM, DETJ
          CALL XIT
        ENDIF

        CJAC = DETJ * WT

        INVJ(1,1) =  JAC(2,2) / DETJ
        INVJ(1,2) = -JAC(1,2) / DETJ
        INVJ(2,1) = -JAC(2,1) / DETJ
        INVJ(2,2) =  JAC(1,1) / DETJ

        DO I=1, 3
          B_TRI(1, 2*I-1) = INVJ(1,1)*D_NTRI(1,I) +
     1                      INVJ(1,2)*D_NTRI(2,I)
          B_TRI(1, 2*I)   = ZERO
          B_TRI(2, 2*I-1) = ZERO
          B_TRI(2, 2*I)   = INVJ(2,1)*D_NTRI(1,I) +
     1                      INVJ(2,2)*D_NTRI(2,I)
          B_TRI(3, 2*I-1) = INVJ(2,1)*D_NTRI(1,I) +
     1                      INVJ(2,2)*D_NTRI(2,I)
          B_TRI(3, 2*I)   = INVJ(1,1)*D_NTRI(1,I) +
     1                      INVJ(1,2)*D_NTRI(2,I)
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
                AMATRX(I,J) = AMATRX(I,J) +
     1            CJAC * B_TRI(K,I)*D_ELAS(K,L)*B_TRI(L,J)
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

C       UNDEGRADED DRIVING ENERGY COMPUTATIONS:
        PSI0_PT = HALF*C12_0*(TR_E**2) +
     1            C33_0*(E11**2 + E22**2 + TWO*(E12**2))
        POS_M   = HALF*C12_0*(E_POS**2) +
     1            C33_0*(E11**2 + E22**2 + TWO*(E12**2))

        SV_PSI0_TRIAL(PHYSIDX, 1)  = PSI0_PT
        SV_PSI0P_TRIAL(PHYSIDX, 1) = POS_M

        H_BEFORE = SV_H_TRIAL(PHYSIDX, 1)
        HIST     = H_BEFORE
        IF (POS_M .GT. HIST) THEN
          HIST = POS_M
          SV_H_TRIAL(PHYSIDX, 1) = POS_M
        ENDIF
        H_AFTER = SV_H_TRIAL(PHYSIDX, 1)

C       Triangular mechanical element elastic strain energy
        PSI_E_PT = HALF * (STRESS(1)*STRAIN(1) +
     1                     STRESS(2)*STRAIN(2) +
     2                     STRESS(3)*STRAIN(3))
        E_ELAS_ELEM = CJAC * PSI_E_PT
        VOL_ELEM    = CJAC

        DO I=1, 6
          RHS(I,1) = -F_INT(I)
        ENDDO

        ENERGY(2) = E_ELAS_ELEM
        SV_E_ELAS(PHYSIDX) = E_ELAS_ELEM
        SV_PSI_E(PHYSIDX)  = PSI_E_PT

C       DIAGNOSTIC FINITE-INCREMENT CONTRIBUTIONS:
        DBAR_OLD   = SV_PHASE_COMMITTED(PHYSIDX)
        DELTA_DBAR = D_VAL - DBAR_OLD
        D_PT       = SV_DK_TRIAL(PHYSIDX, 1)
        D_OLD_PT   = SV_DK_COMMITTED(PHYSIDX, 1)
        DELTA_D_PT = D_PT - D_OLD_PT

        T_HIST_INC  = CJAC * TWO * (ONE - D_PT) *
     1                (SV_H_READ_PHASE(PHYSIDX, 1) - POS_M) *
     2                DELTA_D_PT
        T_SPLIT_INC = CJAC * TWO * (ONE - D_PT) *
     1                (PSI0_PT - POS_M) * DELTA_D_PT
        T_AVG_INC   = CJAC * (
     1                TWO * (ONE - D_VAL) * DELTA_DBAR * PSI0_PT -
     2                TWO * (ONE - D_PT) * DELTA_D_PT * PSI0_PT
     3                )

        SV_T_HIST_ELEM(PHYSIDX)  = T_HIST_INC
        SV_T_AVG_ELEM(PHYSIDX)   = T_AVG_INC
        SV_T_SPLIT_ELEM(PHYSIDX) = T_SPLIT_INC

        SVARS(1)  = STRAIN(1)
        SVARS(4)  = STRESS(1)
        SVARS(9)  = D_VAL
        SVARS(10) = DEG
        SVARS(11) = SVARS(1)
        SVARS(12) = SVARS(4)
        SVARS(13) = SV_H_TRIAL(PHYSIDX, 1)
        SVARS(14) = D_VAL
        SVARS(15) = DEG
        SVARS(16) = SV_H_TRIAL(PHYSIDX, 1)
        IF (NSVARS .GE. 17) SVARS(17) = E_ELAS_ELEM
        IF (NSVARS .GE. 18) SVARS(18) = PSI_E_PT

        IF (PHYSIDX .LE. 5) THEN
          N_CALL_COUNT = N_CALL_COUNT + 1
          WRITE(107, 30) KSTEP, KINC, N_CALL_COUNT, JTYPE, JELEM,
     1      PHYSIDX, SV_H_READ_PHASE(PHYSIDX, 1),
     2      H_BEFORE, H_AFTER, D_VAL, D_VAL
        ENDIF
      ENDIF

      RETURN
      END

C ======================================================================
C Verified Companion Visualizer UMAT with Common Block State Transfer
C ======================================================================
      SUBROUTINE UMAT(STRESS,STATEV,DDSDDE,SSE,SPD,SCD,
     1 RPL,DDSDDT,DRPLDE,DRPLDT,
     2 STRAN,DSTRAN,TIME,DTIME,TEMP,DTEMP,PREDEF,DPRED,CMNAME,
     3 NDI,NSHR,NTENS,NSTATV,PROPS,NPROPS,COORDS,DROT,PNEWDT,
     4 CELENT,DFGRD0,DFGRD1,NOEL,NPT,LAYER,KSPT,KSTEP,KINC)
      INCLUDE 'ABA_PARAM.INC'
      PARAMETER(N_CAPACITY=150000)
      CHARACTER*80 CMNAME
      DIMENSION STRESS(NTENS),STATEV(NSTATV),DDSDDE(NTENS,NTENS),
     1 STRAN(NTENS),DSTRAN(NTENS),TIME(2),PREDEF(1),DPRED(1),
     2 PROPS(NPROPS),COORDS(3),DROT(3,3),DFGRD0(3,3),DFGRD1(3,3)

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

      INTEGER I, J, NPHYS_VAL, PHYSIDX, KPT_IDX

      IF (NPROPS .GE. 3 .AND. PROPS(3) .GT. 0.D0) THEN
        NPHYS_VAL = INT(PROPS(3))
      ELSE
        NPHYS_VAL = 71320
      ENDIF

      PHYSIDX = NOEL - 2 * NPHYS_VAL
      IF (PHYSIDX .LE. 0) PHYSIDX = NOEL

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

        IF (NSTATV .GE. 1)  STATEV(1)  = SV_PHASE_TRIAL(PHYSIDX)
        IF (NSTATV .GE. 2)  STATEV(2)  = SV_H_TRIAL(PHYSIDX, KPT_IDX)
        IF (NSTATV .GE. 14) STATEV(14) = SV_PHASE_TRIAL(PHYSIDX)
        IF (NSTATV .GE. 15) THEN
          STATEV(15) = (1.D0 - SV_PHASE_TRIAL(PHYSIDX))**2 + 1.D-7
        ENDIF
        IF (NSTATV .GE. 16) STATEV(16) = SV_H_TRIAL(PHYSIDX, KPT_IDX)
        IF (NSTATV .GE. 17) STATEV(17) = SV_E_FRAC(PHYSIDX)
        IF (NSTATV .GE. 18) STATEV(18) = SV_E_ELAS(PHYSIDX)
        IF (NSTATV .GE. 19) STATEV(19) = SV_PSI_F(PHYSIDX)
        IF (NSTATV .GE. 20) STATEV(20) = SV_PSI_E(PHYSIDX)
      ENDIF

      RETURN
      END
