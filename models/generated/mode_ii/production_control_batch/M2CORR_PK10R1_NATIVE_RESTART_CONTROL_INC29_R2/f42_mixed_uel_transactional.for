C ======================================================================
C User Subroutines UEL & UEXTERNALDB for Abaqus: Transactional Staggered Phase-Field
C Revision: f42_mixed_uel_transactional.for
C Corrected Undegraded Driving Energy + Transactional (Committed/Trial) State
C
C LOP Operation Codes in UEXTERNALDB:
C   LOP = 0: Start of Analysis        -> Zero committed and trial state
C   LOP = 1: Start of Increment       -> Trial = Committed (Restore on Retry/Cutback)
C   LOP = 2: End of Accepted Increment -> Committed = Trial (Commit Accepted State)
C   LOP = 3: End of Analysis          -> No-op
C ======================================================================
      SUBROUTINE UEXTERNALDB(LOP,LRESTART,TIME,DTIME,KSTEP,KINC)
      INCLUDE 'ABA_PARAM.INC'
      PARAMETER(N_CAPACITY=100000)

      DOUBLE PRECISION SV_PHASE_COMMITTED(N_CAPACITY)
      DOUBLE PRECISION SV_PHASE_TRIAL(N_CAPACITY)
      DOUBLE PRECISION SV_H_COMMITTED(N_CAPACITY,4)
      DOUBLE PRECISION SV_H_TRIAL(N_CAPACITY,4)

      COMMON /CB_STATE_TRANS/ SV_PHASE_COMMITTED, SV_PHASE_TRIAL,
     1                        SV_H_COMMITTED, SV_H_TRIAL

      INTEGER LOP, LRESTART, KSTEP, KINC, I, KPT
      DOUBLE PRECISION TIME(2), DTIME

      IF (LOP .EQ. 0) THEN
        DO I=1, N_CAPACITY
          SV_PHASE_COMMITTED(I) = 0.D0
          SV_PHASE_TRIAL(I)     = 0.D0
          DO KPT=1, 4
            SV_H_COMMITTED(I, KPT) = 0.D0
            SV_H_TRIAL(I, KPT)     = 0.D0
          ENDDO
        ENDDO
      ELSE IF (LOP .EQ. 1) THEN
C       Start of Increment (or Retry/Cutback): Restore Trial from Committed
        DO I=1, N_CAPACITY
          SV_PHASE_TRIAL(I) = SV_PHASE_COMMITTED(I)
          DO KPT=1, 4
            SV_H_TRIAL(I, KPT) = SV_H_COMMITTED(I, KPT)
          ENDDO
        ENDDO
      ELSE IF (LOP .EQ. 2) THEN
C       End of Accepted Increment: Commit Trial State
        DO I=1, N_CAPACITY
          SV_PHASE_COMMITTED(I) = SV_PHASE_TRIAL(I)
          DO KPT=1, 4
            SV_H_COMMITTED(I, KPT) = SV_H_TRIAL(I, KPT)
          ENDDO
        ENDDO
      ENDIF

      RETURN
      END

C ======================================================================
C User Subroutine UEL: Transactional State Phase-Field Formulation
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

      DOUBLE PRECISION SV_PHASE_COMMITTED(N_CAPACITY)
      DOUBLE PRECISION SV_PHASE_TRIAL(N_CAPACITY)
      DOUBLE PRECISION SV_H_COMMITTED(N_CAPACITY,4)
      DOUBLE PRECISION SV_H_TRIAL(N_CAPACITY,4)

      COMMON /CB_STATE_TRANS/ SV_PHASE_COMMITTED, SV_PHASE_TRIAL,
     1                        SV_H_COMMITTED, SV_H_TRIAL

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
      DOUBLE PRECISION C11_0, C12_0, C22_0, C33_0
      DOUBLE PRECISION C11_MECH, C12_MECH, C22_MECH, C33_MECH
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
        WRITE(7,*) 'ERROR: PHYSIDX out of bounds:', PHYSIDX
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

        D_AVG = 0.25D0 * (U(1) + U(2) + U(3) + U(4))
        SV_PHASE_TRIAL(PHYSIDX) = D_AVG

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

          HIST = SV_H_TRIAL(PHYSIDX, KPT)

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
        SVARS(10) = (ONE - SVARS(1))**2 + E_K
        SVARS(11) = ZERO
        SVARS(12) = ZERO
        SVARS(13) = SV_H_TRIAL(PHYSIDX, 1)
        SVARS(14) = SVARS(1)
        SVARS(15) = SVARS(10)
        SVARS(16) = SV_H_TRIAL(PHYSIDX, 1)

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
          
C         REPAIRED UNDEGRADED DRIVING ENERGY COMPUTATION:
          POS_M = HALF*C12_0*(E_POS**2) + C33_0*(E11**2 + E22**2 + TWO*(E12**2))

          HIST = SV_H_TRIAL(PHYSIDX, KPT)
          IF (POS_M .GT. HIST) THEN
            HIST = POS_M
            SV_H_TRIAL(PHYSIDX, KPT) = POS_M
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
        SVARS(13) = SV_H_TRIAL(PHYSIDX, 1)
        SVARS(14) = D_VAL
        SVARS(15) = DEG
        SVARS(16) = SV_H_TRIAL(PHYSIDX, 1)
        SVARS(17) = STRAIN(1)
        SVARS(18) = STRESS(1)
      ENDIF

      RETURN
      END
