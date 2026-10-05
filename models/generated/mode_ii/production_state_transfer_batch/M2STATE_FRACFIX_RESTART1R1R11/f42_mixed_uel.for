C ======================================================================
C User Subroutine UEL and UMAT for Abaqus: Mixed 3-Node / 4-Node Scheme
C Candidate Revision: M2STATE_FRACFIX_RESTART1R1R11 (Safe Jacobian Inversion + Clean 6-Property ABI)
C Production Representative Elements (PK5 NPHYS=4894, Total UEL=9788):
C   Quad High Damage: Phase E2292 / Mech E7186
C   Quad Low Damage: Phase E100 / Mech E4994
C   Tri Pair: Phase E4862 / Mech E9756
C Clean 6-Slot Property ABI:
C   PROPS(1) = E_L0  (0.015 mm)
C   PROPS(2) = E_GC  (0.0027 kN/mm)
C   PROPS(3) = E_MOD (210.0 kN/mm^2)
C   PROPS(4) = E_NU  (0.3)
C   PROPS(5) = E_K   (1.0e-07)
C   PROPS(6) = N_PHYS (4894.0)
C ======================================================================
      SUBROUTINE UEL(RHS,AMATRX,SVARS,ENERGY,NDOFEL,NRHS,NSVARS,
     1     PROPS,NPROPS,COORDS,MCRD,NNODE,U,DU,V,A,JTYPE,TIME,DTIME,
     2     KSTEP,KINC,JELEM,PARAMS,NDLOAD,JDLTYP,ADLMAG,PREDEF,
     3     NPREDF,LFLAGS,MLVARX,DDLMAG,MDLOAD,PNEWDT,JPROPS,NJPROP,
     4     PERIOD)
      INCLUDE 'ABA_PARAM.INC'
      PARAMETER(ZERO=0.D0,ONE=1.D0,TWO=2.D0,THREE=3.D0,FOUR=4.D0,
     1 HALF=0.5D0,SIX=6.D0,N_CAPACITY=100000,NSTV=18)

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
      DOUBLE PRECISION BDB, SHAPE_VAL

      INTEGER I, J, K, L, KPT, PHYSIDX, N_PHYS
      DOUBLE PRECISION XI, ETA, WT, CJAC, DETJ, JAC(2,2), INVJ(2,2)
      DOUBLE PRECISION D_AVG, DEG, DEG_D, HIST, HIST_MAX
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

        D_AVG = ZERO
        DO I=1, 4
          D_AVG = D_AVG + U(I)*0.25D0
        ENDDO
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
        XG3(1) = 1.D0/6.D0
        YG3(1) = 1.D0/6.D0
        W3(1)  = 1.D0/6.D0
        XG3(2) = 2.D0/3.D0
        YG3(2) = 1.D0/6.D0
        W3(2)  = 1.D0/6.D0
        XG3(3) = 1.D0/6.D0
        YG3(3) = 2.D0/3.D0
        W3(3)  = 1.D0/6.D0

        D_AVG = (U(1) + U(2) + U(3)) / THREE
        SV_PHASE(PHYSIDX) = D_AVG

        DO KPT=1, 3
          XI  = XG3(KPT)
          ETA = YG3(KPT)
          WT  = W3(KPT)

          N_TRI(1) = ONE - XI - ETA
          N_TRI(2) = XI
          N_TRI(3) = ETA

          D_NTRI(1,1) = -ONE
          D_NTRI(1,2) =  ONE
          D_NTRI(1,3) =  ZERO

          D_NTRI(2,1) = -ONE
          D_NTRI(2,2) =  ZERO
          D_NTRI(2,3) =  ONE

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

          HIST = SV_H(PHYSIDX, KPT)

          DO I=1, 3
            DO J=1, 3
              BDB = B_PHTRI(1,I)*B_PHTRI(1,J) + B_PHTRI(2,I)*B_PHTRI(2,J)
              AMATRX(I,J) = AMATRX(I,J) + CJAC * (
     1          (E_GC*E_L0)*BDB +
     2          (E_GC/E_L0 + TWO*HIST)*N_TRI(I)*N_TRI(J)
     3        )
            ENDDO
            RHS(I,1) = RHS(I,1) + CJAC * TWO * HIST * N_TRI(I)
          ENDDO

          SVARS(KPT)   = D_AVG
          SVARS(3+KPT) = HIST
        ENDDO

        DO I=1, 3
          DO J=1, 3
            RHS(I,1) = RHS(I,1) - AMATRX(I,J)*U(J)
          ENDDO
        ENDDO

        SVARS(7)  = SVARS(1)
        SVARS(8)  = SVARS(2)
        SVARS(9)  = SVARS(3)
        SVARS(10) = SVARS(4)
        SVARS(11) = SVARS(5)
        SVARS(12) = SVARS(6)
        SVARS(13) = SV_H(PHYSIDX, 1)
        SVARS(14) = D_AVG
        SVARS(15) = (ONE - D_AVG)**2 + E_K
        SVARS(16) = SV_H(PHYSIDX, 1)
        SVARS(17) = D_AVG
        SVARS(18) = SV_H(PHYSIDX, 1)

C ----------------------------------------------------------------------
C JTYPE = 4: 3-Node Triangular Mechanical Element (DOFs 1, 2)
C ----------------------------------------------------------------------
      ELSE IF (JTYPE .EQ. 4) THEN
        XG3(1) = 1.D0/6.D0
        YG3(1) = 1.D0/6.D0
        W3(1)  = 1.D0/6.D0
        XG3(2) = 2.D0/3.D0
        YG3(2) = 1.D0/6.D0
        W3(2)  = 1.D0/6.D0
        XG3(3) = 1.D0/6.D0
        YG3(3) = 2.D0/3.D0
        W3(3)  = 1.D0/6.D0

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

        DO KPT=1, 3
          XI  = XG3(KPT)
          ETA = YG3(KPT)
          WT  = W3(KPT)

          D_NTRI(1,1) = -ONE
          D_NTRI(1,2) =  ONE
          D_NTRI(1,3) =  ZERO

          D_NTRI(2,1) = -ONE
          D_NTRI(2,2) =  ZERO
          D_NTRI(2,3) =  ONE

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

          HIST = SV_H(PHYSIDX, KPT)
          IF (POS_M .GT. HIST) THEN
            HIST = POS_M
            SV_H(PHYSIDX, KPT) = POS_M
          ENDIF

          SVARS(KPT)   = STRAIN(1)
          SVARS(3+KPT) = STRESS(1)
        ENDDO

        DO I=1, 6
          RHS(I,1) = -F_INT(I)
        ENDDO

        SVARS(7)  = D_VAL
        SVARS(8)  = DEG
        SVARS(9)  = SVARS(1)
        SVARS(10) = SVARS(4)
        SVARS(11) = SV_H(PHYSIDX, 1)
        SVARS(12) = D_VAL
        SVARS(13) = DEG
        SVARS(14) = D_VAL
        SVARS(15) = DEG
        SVARS(16) = SV_H(PHYSIDX, 1)
        SVARS(17) = STRAIN(1)
        SVARS(18) = STRESS(1)

      ENDIF

      RETURN
      END

      SUBROUTINE UMAT(STRESS,STATEV,DDSDDE,SSE,SPD,SCD,
     1 RPL,DDSDDT,DRPLDE,DRPLDT,
     2 STRAN,DSTRAN,TIME,DTIME,TEMP,DTEMP,PREDEF,DPRED,CMNAME,
     3 NDI,NSHR,NTENS,NSTATV,PROPS,NPROPS,COORDS,DROT,PNEWDT,
     4 CELENT,DFGRD0,DFGRD1,NOEL,NPT,LAYER,KSPT,KSTEP,KINC)
      INCLUDE 'ABA_PARAM.INC'
      CHARACTER*80 CMNAME
      DIMENSION STRESS(NTENS),STATEV(NSTATV),
     1 DDSDDE(NTENS,NTENS),DDSDDT(NTENS),DRPLDE(NTENS),
     2 STRAN(NTENS),DSTRAN(NTENS),TIME(2),PREDEF(1),DPRED(1),
     3 PROPS(NPROPS),COORDS(3),DROT(3,3),DFGRD0(3,3),DFGRD1(3,3)
      RETURN
      END
