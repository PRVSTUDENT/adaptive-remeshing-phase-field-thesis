C ======================================================================
C Experimental Kinematic-Offset User Subroutines UEL & UEXTERNALDB
C Model: Pandey-Kumar Mode-I Phase-Field Fracture
C Architecture: Kinematic-Offset Continuation (u = u_0 + Delta u)
C Implementation: Isolated experimental research branch
C Production UEL f42_mixed_uel.for remains 100% FROZEN.
C
C Key Features:
C   1. Mechanical DOF U(i) represents incremental displacement Delta u.
C      Total displacement: u_tot = u_0 + Delta u.
C   2. Phase-field DOF U(i) represents incremental phase-field Delta d.
C      Total phase-field: d_tot = d_0 + Delta d.
C   3. History field H_0 initialized from committed donor state.
C   4. Offset state (u_0, d_0, H_0) read at LOP=0 from offset_state_table.csv.
C   5. Tangent stiffness AMATRX is invariant: K_uu = K_uu^standard.
C   6. Zero reload work: W_ext(0) = 0.0, avoiding duplicate work.
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

      DOUBLE PRECISION U_OFFSET(N_CAPACITY, 8)
      DOUBLE PRECISION D_OFFSET(N_CAPACITY, 4)
      DOUBLE PRECISION H_OFFSET(N_CAPACITY, 4)
      LOGICAL OFFSET_LOADED

      COMMON /CB_OFFSET_STATE/ U_OFFSET, D_OFFSET, H_OFFSET,
     1                         OFFSET_LOADED

      INTEGER LOP, LRESTART, KSTEP, KINC, I, J, KPT
      DOUBLE PRECISION TIME(2), DTIME
      LOGICAL OP_EXISTS
      CHARACTER*512 OUTDIR_STR, CSV_FULL_PATH, TABLE_PATH
      INTEGER L_OUTDIR, EID_IN
      DOUBLE PRECISION U0_IN(8), D0_IN(4), H0_IN(4)

      IF (LOP .EQ. 0) THEN
C       Zero baseline arrays
        DO I=1, N_CAPACITY
          SV_PHASE_COMMITTED(I) = 0.D0
          SV_PHASE_TRIAL(I)     = 0.D0
          SV_E_FRAC(I)          = 0.D0
          SV_E_ELAS(I)          = 0.D0
          SV_PSI_F(I)           = 0.D0
          SV_PSI_E(I)           = 0.D0
          DO J=1, 8
            U_OFFSET(I, J) = 0.D0
          ENDDO
          DO KPT=1, 4
            D_OFFSET(I, KPT)       = 0.D0
            H_OFFSET(I, KPT)       = 0.D0
            SV_H_COMMITTED(I, KPT) = 0.D0
            SV_H_TRIAL(I, KPT)     = 0.D0
          ENDDO
        ENDDO
        OFFSET_LOADED = .FALSE.

C       Attempt to load offset_state_table.csv
        INQUIRE(FILE='offset_state_table.csv', EXIST=OP_EXISTS)
        IF (.NOT. OP_EXISTS) THEN
          CALL GETOUTDIR(OUTDIR_STR, L_OUTDIR)
          TABLE_PATH = OUTDIR_STR(1:L_OUTDIR) // '/offset_state_table.csv'
          INQUIRE(FILE=TRIM(TABLE_PATH), EXIST=OP_EXISTS)
        ELSE
          TABLE_PATH = 'offset_state_table.csv'
        ENDIF

        IF (OP_EXISTS) THEN
          OPEN(UNIT=106, FILE=TRIM(TABLE_PATH), STATUS='OLD',
     1         ACTION='READ')
C         Read header line
          READ(106, *, END=20)
 15       READ(106, *, END=20) EID_IN,
     1      (U0_IN(J), J=1,8),
     2      (D0_IN(J), J=1,4),
     3      (H0_IN(J), J=1,4)
          IF (EID_IN .GE. 1 .AND. EID_IN .LE. N_CAPACITY) THEN
            DO J=1, 8
              U_OFFSET(EID_IN, J) = U0_IN(J)
            ENDDO
            DO J=1, 4
              D_OFFSET(EID_IN, J) = D0_IN(J)
              H_OFFSET(EID_IN, J) = H0_IN(J)
              SV_H_COMMITTED(EID_IN, J) = H0_IN(J)
              SV_H_TRIAL(EID_IN, J)     = H0_IN(J)
            ENDDO
            SV_PHASE_COMMITTED(EID_IN) = 0.25D0*(D0_IN(1)+D0_IN(2)+
     1                                          D0_IN(3)+D0_IN(4))
            SV_PHASE_TRIAL(EID_IN)     = SV_PHASE_COMMITTED(EID_IN)
          ENDIF
          GOTO 15
 20       CLOSE(106)
          OFFSET_LOADED = .TRUE.
          WRITE(7,*) 'KINEMATIC-OFFSET: Successfully loaded offset ',
     1               'state table from ', TRIM(TABLE_PATH)
        ELSE
          WRITE(7,*) 'KINEMATIC-OFFSET: No offset_state_table.csv found;',
     1               ' running in standard zero-offset reference mode.'
        ENDIF

C       Initialize CSV file for energy tracking
        CALL GETOUTDIR(OUTDIR_STR, L_OUTDIR)
        CSV_FULL_PATH = OUTDIR_STR(1:L_OUTDIR) // '/uel_energy_balance.csv'
        OPEN(UNIT=105, FILE=TRIM(CSV_FULL_PATH),
     1       STATUS='UNKNOWN', ACTION='WRITE')
        WRITE(105, 10) 'Step,Increment,TotalTime,StepTime,' //
     1                 'E_elastic_kNmm,E_fracture_kNmm,E_total_kNmm'
 10     FORMAT(A)

      ELSE IF (LOP .EQ. 1) THEN
C       Start of increment: restore trial from committed
        DO I=1, N_CAPACITY
          SV_PHASE_TRIAL(I) = SV_PHASE_COMMITTED(I)
          DO KPT=1, 4
            SV_H_TRIAL(I, KPT) = SV_H_COMMITTED(I, KPT)
          ENDDO
        ENDDO

      ELSE IF (LOP .EQ. 2) THEN
C       End of increment (converged): commit trial state
        DO I=1, N_CAPACITY
          SV_PHASE_COMMITTED(I) = SV_PHASE_TRIAL(I)
          DO KPT=1, 4
            SV_H_COMMITTED(I, KPT) = SV_H_TRIAL(I, KPT)
          ENDDO
        ENDDO

      ELSE IF (LOP .EQ. 3) THEN
C       End of analysis
        CLOSE(105)
      ENDIF

      RETURN
      END

C ======================================================================
C Subroutine UEL: Mixed Phase-Field & Mechanical Formulation
C With Kinematic Offset Support:
C   u_tot = u_0 + Delta u
C   d_tot = d_0 + Delta d
C ======================================================================
      SUBROUTINE UEL(RHS,AMATRX,SVARS,ENERGY,NDOFEL,NRHS,NSVARS,
     1               PROPS,NPROPS,COORDS,MCRD,NNODE,U,DU,V,A,JTYPE,
     2               TIME,DTIME,KSTEP,KINC,JELEM,PARAMS,NDLOAD,JDLTYP,
     3               ADLMAG,PREDEF,NPREDF,LFLAGS,MLVARX,DDLMAG,MDLOAD,
     4               PNEWDT,JPROPS,NJPROP,PERIOD)
      INCLUDE 'ABA_PARAM.INC'
      PARAMETER(N_CAPACITY=150000)

      DOUBLE PRECISION RHS(MLVARX,*), AMATRX(NDOFEL,NDOFEL)
      DOUBLE PRECISION SVARS(NSVARS), ENERGY(8), PROPS(*)
      DOUBLE PRECISION COORDS(MCRD,NNODE), U(NDOFEL), DU(MLVARX,*)
      DOUBLE PRECISION V(NDOFEL), A(NDOFEL), TIME(2), PARAMS(*)
      DOUBLE PRECISION ADLMAG(MDLOAD,*), DDLMAG(MDLOAD,*)
      DOUBLE PRECISION PREDEF(2,NPREDF,NNODE)
      INTEGER JDLTYP(MDLOAD,*), LFLAGS(*), JPROPS(*)
      INTEGER NDOFEL, NRHS, NSVARS, NPROPS, MCRD, NNODE, JTYPE
      INTEGER KSTEP, KINC, JELEM, NDLOAD, MDLOAD, MLVARX, NPREDF, NJPROP
      DOUBLE PRECISION DTIME, PNEWDT, PERIOD

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

      DOUBLE PRECISION U_OFFSET(N_CAPACITY, 8)
      DOUBLE PRECISION D_OFFSET(N_CAPACITY, 4)
      DOUBLE PRECISION H_OFFSET(N_CAPACITY, 4)
      LOGICAL OFFSET_LOADED

      COMMON /CB_OFFSET_STATE/ U_OFFSET, D_OFFSET, H_OFFSET,
     1                         OFFSET_LOADED

      DOUBLE PRECISION ZERO, ONE, TWO, HALF
      PARAMETER(ZERO=0.D0, ONE=1.D0, TWO=2.D0, HALF=0.5D0)

      DOUBLE PRECISION XG4(4), YG4(4), W4(4)
      DOUBLE PRECISION N_VEC(4), D_N(2,4), B_PHASE(2,4), B(3,8)
      DOUBLE PRECISION STRAIN(3), STRESS(3), D_ELAS(3,3), BDB
      DOUBLE PRECISION U_TOT(8), D_TOT(4)

      INTEGER I, J, K, L, KPT, PHYSIDX, N_PHYS
      DOUBLE PRECISION XI, ETA, WT, CJAC, DETJ, JAC(2,2), INVJ(2,2)
      DOUBLE PRECISION D_AVG, DEG, HIST
      DOUBLE PRECISION E_MOD, E_NU, E_L0, E_GC, E_K, D_VAL
      DOUBLE PRECISION E11, E22, E12, TR_E, E_POS, POS_M
      DOUBLE PRECISION C11_0, C12_0, C22_0, C33_0
      DOUBLE PRECISION C11_MECH, C12_MECH, C22_MECH, C33_MECH
      DOUBLE PRECISION F_INT(8)
      DOUBLE PRECISION D_PT, GRAD_D(2), GRAD_D_SQ, PSI_F_PT
      DOUBLE PRECISION E_FRAC_ELEM, VOL_ELEM, PSI_E_PT, E_ELAS_ELEM

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

C       Total phase field = offset + incremental solver DOF
        DO I=1, 4
          D_TOT(I) = D_OFFSET(PHYSIDX, I) + U(I)
        ENDDO

        D_AVG = 0.25D0 * (D_TOT(1) + D_TOT(2) + D_TOT(3) + D_TOT(4))
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
              BDB = B_PHASE(1,I)*B_PHASE(1,J) +
     1              B_PHASE(2,I)*B_PHASE(2,J)
              AMATRX(I,J) = AMATRX(I,J) + CJAC * (
     1          (E_GC*E_L0)*BDB +
     2          (E_GC/E_L0 + TWO*HIST)*N_VEC(I)*N_VEC(J)
     3        )
            ENDDO
            RHS(I,1) = RHS(I,1) + CJAC * TWO * HIST * N_VEC(I)
          ENDDO

          D_PT = N_VEC(1)*D_TOT(1) + N_VEC(2)*D_TOT(2) +
     1           N_VEC(3)*D_TOT(3) + N_VEC(4)*D_TOT(4)
          GRAD_D(1) = B_PHASE(1,1)*D_TOT(1) + B_PHASE(1,2)*D_TOT(2) +
     1                B_PHASE(1,3)*D_TOT(3) + B_PHASE(1,4)*D_TOT(4)
          GRAD_D(2) = B_PHASE(2,1)*D_TOT(1) + B_PHASE(2,2)*D_TOT(2) +
     1                B_PHASE(2,3)*D_TOT(3) + B_PHASE(2,4)*D_TOT(4)
          GRAD_D_SQ = GRAD_D(1)**2 + GRAD_D(2)**2
          PSI_F_PT  = E_GC * (HALF * (D_PT**2) / E_L0 +
     1                        HALF * E_L0 * GRAD_D_SQ)
          E_FRAC_ELEM = E_FRAC_ELEM + CJAC * PSI_F_PT
          VOL_ELEM    = VOL_ELEM + CJAC

          SVARS(KPT)   = D_PT
          SVARS(4+KPT) = HIST
        ENDDO

C       Residual: RHS = F_ext - K * D_TOT
        DO I=1, 4
          DO J=1, 4
            RHS(I,1) = RHS(I,1) - AMATRX(I,J)*D_TOT(J)
          ENDDO
        ENDDO

        ENERGY(7) = E_FRAC_ELEM
        SV_E_FRAC(PHYSIDX) = E_FRAC_ELEM
        IF (VOL_ELEM .GT. ZERO) THEN
          SV_PSI_F(PHYSIDX) = E_FRAC_ELEM / VOL_ELEM
        ELSE
          SV_PSI_F(PHYSIDX) = ZERO
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

C       Total displacement = offset + incremental solver DOF
        DO I=1, 8
          U_TOT(I) = U_OFFSET(PHYSIDX, I) + U(I)
        ENDDO

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

C         Strain from total displacement
          DO I=1, 3
            STRAIN(I) = ZERO
            DO J=1, 8
              STRAIN(I) = STRAIN(I) + B(I,J)*U_TOT(J)
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
          POS_M = HALF * ( (E11 - E22)**2 + FOUR * (E12**2) )
          IF (POS_M .GT. ZERO) THEN
            POS_M = SQRT(POS_M)
          ELSE
            POS_M = ZERO
          ENDIF
          PSI_E_PT = HALF * C11_0 * (E_POS**2) +
     1               HALF * C33_0 * (POS_M**2)

          IF (PSI_E_PT .GT. SV_H_TRIAL(PHYSIDX, KPT)) THEN
            SV_H_TRIAL(PHYSIDX, KPT) = PSI_E_PT
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

        ENERGY(2) = E_ELAS_ELEM
        SV_E_ELAS(PHYSIDX) = E_ELAS_ELEM
        IF (VOL_ELEM .GT. ZERO) THEN
          SV_PSI_E(PHYSIDX) = E_ELAS_ELEM / VOL_ELEM
        ELSE
          SV_PSI_E(PHYSIDX) = ZERO
        ENDIF

      ENDIF

      RETURN
      END
