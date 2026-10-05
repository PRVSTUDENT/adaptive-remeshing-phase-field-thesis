C ======================================================================
C USER SUBROUTINE UEL FOR COUPLED PHASE-FIELD FRACTURE (FRACFIX FORMULATION)
C Mixed Quadrilateral (4-Node) and Triangular (3-Node) Staggered Formulation
C Order-Independent COMMON Ingestion and Initial Transfer Ingestion
C Candidate: M2STATE_FRACFIX_RESTART2R9
C Clean 6-Property ABI: PROPS(1..5) = (l0, Gc, E, nu, k), PROPS(6) = NPHYS
C Safe 2x2 Jacobian evaluation and inversion across all JTYPEs (1, 2, 3, 4)
C Consistent Phase-Field Residual: RHS = F_H - K_phase * d (JTYPE 1 and 3)
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
      DOUBLE PRECISION JAC(2,2), INVJ(2,2)

      INTEGER I, J, K, KPT, PHYSIDX, N_PHYS
      DOUBLE PRECISION XI, ETA, WT, CJAC, DETJ
      DOUBLE PRECISION D_AVG, DEG, HIST, HIST_MAX
      DOUBLE PRECISION E_MOD, E_NU, E_L0, E_GC, E_K, D_VAL
      DOUBLE PRECISION E11, E22, E12, TR_E, E_POS, POS_M
      DOUBLE PRECISION C11, C12, C22, C33
      DOUBLE PRECISION F_INT(8)

      E_L0   = PROPS(1)
      E_GC   = PROPS(2)
      E_MOD  = PROPS(3)
      E_NU   = PROPS(4)
      E_K    = PROPS(5)
      IF (NPROPS .GE. 6) THEN
        N_PHYS = INT(PROPS(6))
      ELSE
        N_PHYS = 9876
      ENDIF

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

C ----------------------------------------------------------------------
C Explicit Order-Independent Initial Ingestion from Incoming SVARS
C ----------------------------------------------------------------------
      IF (KSTEP .EQ. 1 .AND. KINC .EQ. 1) THEN
        IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) THEN
          IF (JTYPE .EQ. 1 .OR. JTYPE .EQ. 2) THEN
            DO KPT=1, 4
              IF (SVARS(8+KPT) .GT. SV_H(PHYSIDX, KPT)) THEN
                SV_H(PHYSIDX, KPT) = SVARS(8+KPT)
              ENDIF
            ENDDO
          ELSE IF (JTYPE .EQ. 3 .OR. JTYPE .EQ. 4) THEN
            DO KPT=1, 3
              IF (SVARS(6+KPT) .GT. SV_H(PHYSIDX, KPT)) THEN
                SV_H(PHYSIDX, KPT) = SVARS(6+KPT)
              ENDIF
            ENDDO
          ENDIF
        ENDIF
      ENDIF

C ======================================================================
C JTYPE = 1: QUADRILATERAL PHASE-FIELD LAYER (4 Nodes, Active DOF 3)
C ======================================================================
      IF (JTYPE .EQ. 1) THEN
        D_AVG = ZERO
        DO I=1, 4
          D_AVG = D_AVG + U(I) * 0.25D0
        ENDDO

        DO KPT=1, 4
          SVARS(KPT)   = D_AVG
          SVARS(4+KPT) = D_AVG
          IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) THEN
            SVARS(8+KPT) = SV_H(PHYSIDX, KPT)
          ENDIF
        ENDDO
        SVARS(13) = ZERO
        SVARS(14) = D_AVG
        SVARS(15) = D_AVG
        IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) THEN
          SVARS(16) = SV_H(PHYSIDX, 1)
        ENDIF
        SVARS(17) = ZERO
        SVARS(18) = ZERO

        IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) THEN
          SV_PHASE(PHYSIDX) = D_AVG
        ENDIF

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

          JAC(1,1) = ZERO
          JAC(1,2) = ZERO
          JAC(2,1) = ZERO
          JAC(2,2) = ZERO
          DO I=1, 4
            JAC(1,1) = JAC(1,1) + D_N(1,I)*COORDS(1,I)
            JAC(1,2) = JAC(1,2) + D_N(1,I)*COORDS(2,I)
            JAC(2,1) = JAC(2,1) + D_N(2,I)*COORDS(1,I)
            JAC(2,2) = JAC(2,2) + D_N(2,I)*COORDS(2,I)
          ENDDO

          DETJ = JAC(1,1)*JAC(2,2) - JAC(1,2)*JAC(2,1)
          INVJ(1,1) =  JAC(2,2)/DETJ
          INVJ(1,2) = -JAC(1,2)/DETJ
          INVJ(2,1) = -JAC(2,1)/DETJ
          INVJ(2,2) =  JAC(1,1)/DETJ

          DO I=1, 4
            B_PHASE(1,I) = INVJ(1,1)*D_N(1,I) + INVJ(1,2)*D_N(2,I)
            B_PHASE(2,I) = INVJ(2,1)*D_N(1,I) + INVJ(2,2)*D_N(2,I)
          ENDDO

          CJAC = DABS(DETJ)*WT

          IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) THEN
            HIST = SV_H(PHYSIDX, KPT)
          ELSE
            HIST = ZERO
          ENDIF

          DO I=1, 4
            DO J=1, 4
              AMATRX(I,J) = AMATRX(I,J) + CJAC*(
     1          (E_GC/E_L0 + TWO*HIST)*N_VEC(I)*N_VEC(J) +
     2          E_GC*E_L0*(B_PHASE(1,I)*B_PHASE(1,J) +
     3                     B_PHASE(2,I)*B_PHASE(2,J)) )
            ENDDO
            RHS(I,1) = RHS(I,1) + CJAC*(TWO*HIST*N_VEC(I))
          ENDDO
        ENDDO

        DO I=1, 4
          DO J=1, 4
            RHS(I,1) = RHS(I,1) - AMATRX(I,J)*U(J)
          ENDDO
        ENDDO

        WRITE(7,1001) KSTEP, KINC, TIME(2), JELEM, JTYPE, PHYSIDX,
     1    SVARS(14), SVARS(15), SVARS(16),
     2    SV_H(PHYSIDX,1), SV_H(PHYSIDX,2), SV_H(PHYSIDX,3), SV_H(PHYSIDX,4)
 1001   FORMAT('STATE_TRACE ',I3,1X,I4,1X,E14.6,1X,I6,1X,I2,1X,I6,
     1    1X,E14.6,1X,E14.6,1X,E14.6,1X,E14.6,1X,E14.6,1X,E14.6,1X,E14.6)
      ENDIF

C ======================================================================
C JTYPE = 2: QUADRILATERAL MECHANICAL LAYER (4 Nodes, Active DOFs 1, 2)
C ======================================================================
      IF (JTYPE .EQ. 2) THEN
        IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) THEN
          D_VAL = SV_PHASE(PHYSIDX)
        ELSE
          D_VAL = ZERO
        ENDIF

        IF (D_VAL .LT. ZERO) D_VAL = ZERO
        IF (D_VAL .GT. ONE)  D_VAL = ONE
        DEG = (ONE - D_VAL)**2 + E_K

        C11 = E_MOD*(ONE - E_NU)/((ONE + E_NU)*(ONE - TWO*E_NU))
        C12 = E_MOD*E_NU/((ONE + E_NU)*(ONE - TWO*E_NU))
        C22 = C11
        C33 = E_MOD*HALF/(ONE + E_NU)

        DO KPT=1, 4
          SVARS(KPT)   = D_VAL
          SVARS(4+KPT) = D_VAL
          IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) THEN
            SVARS(8+KPT) = SV_H(PHYSIDX, KPT)
          ENDIF
        ENDDO
        SVARS(13) = ZERO
        SVARS(14) = D_VAL
        SVARS(15) = D_VAL
        IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) THEN
          SVARS(16) = SV_H(PHYSIDX, 1)
        ENDIF
        SVARS(17) = ZERO
        SVARS(18) = ZERO

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

          JAC(1,1) = ZERO
          JAC(1,2) = ZERO
          JAC(2,1) = ZERO
          JAC(2,2) = ZERO
          DO I=1, 4
            JAC(1,1) = JAC(1,1) + D_N(1,I)*COORDS(1,I)
            JAC(1,2) = JAC(1,2) + D_N(1,I)*COORDS(2,I)
            JAC(2,1) = JAC(2,1) + D_N(2,I)*COORDS(1,I)
            JAC(2,2) = JAC(2,2) + D_N(2,I)*COORDS(2,I)
          ENDDO

          DETJ = JAC(1,1)*JAC(2,2) - JAC(1,2)*JAC(2,1)
          INVJ(1,1) =  JAC(2,2)/DETJ
          INVJ(1,2) = -JAC(1,2)/DETJ
          INVJ(2,1) = -JAC(2,1)/DETJ
          INVJ(2,2) =  JAC(1,1)/DETJ

          DO I=1, 4
            DO J=1, 8
              B(1,J) = ZERO
              B(2,J) = ZERO
              B(3,J) = ZERO
            ENDDO
          ENDDO

          DO I=1, 4
            B(1,2*I-1) = INVJ(1,1)*D_N(1,I) + INVJ(1,2)*D_N(2,I)
            B(2,2*I)   = INVJ(2,1)*D_N(1,I) + INVJ(2,2)*D_N(2,I)
            B(3,2*I-1) = B(2,2*I)
            B(3,2*I)   = B(1,2*I-1)
          ENDDO

          CJAC = DABS(DETJ)*WT

          STRAIN(1) = ZERO
          STRAIN(2) = ZERO
          STRAIN(3) = ZERO
          DO I=1, 8
            STRAIN(1) = STRAIN(1) + B(1,I)*U(I)
            STRAIN(2) = STRAIN(2) + B(2,I)*U(I)
            STRAIN(3) = STRAIN(3) + B(3,I)*U(I)
          ENDDO

          STRESS(1) = DEG*(C11*STRAIN(1) + C12*STRAIN(2))
          STRESS(2) = DEG*(C12*STRAIN(1) + C22*STRAIN(2))
          STRESS(3) = DEG*(C33*STRAIN(3))

          E11 = STRAIN(1)
          E22 = STRAIN(2)
          E12 = STRAIN(3)*HALF
          TR_E = E11 + E22
          E_POS = HALF*(TR_E + DSQRT((E11-E22)**2 + FOUR*E12**2))
          IF (E_POS .LT. ZERO) E_POS = ZERO
          POS_M = HALF*C11*E_POS**2

          IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) THEN
            IF (POS_M .GT. SV_H(PHYSIDX, KPT)) THEN
              SV_H(PHYSIDX, KPT) = POS_M
            ENDIF
          ENDIF

          DO I=1, 8
            DO J=1, 8
              AMATRX(I,J) = AMATRX(I,J) + CJAC*DEG*(
     1          B(1,I)*(C11*B(1,J) + C12*B(2,J)) +
     2          B(2,I)*(C12*B(1,J) + C22*B(2,J)) +
     3          B(3,I)*(C33*B(3,J)) )
            ENDDO
            F_INT(I) = F_INT(I) + CJAC*(
     1        B(1,I)*STRESS(1) + B(2,I)*STRESS(2) + B(3,I)*STRESS(3))
          ENDDO
        ENDDO

        DO I=1, 8
          RHS(I,1) = -F_INT(I)
        ENDDO

        WRITE(7,1001) KSTEP, KINC, TIME(2), JELEM, JTYPE, PHYSIDX,
     1    SVARS(14), SVARS(15), SVARS(16),
     2    SV_H(PHYSIDX,1), SV_H(PHYSIDX,2), SV_H(PHYSIDX,3), SV_H(PHYSIDX,4)
      ENDIF

C ======================================================================
C JTYPE = 3: TRIANGULAR PHASE-FIELD LAYER (3 Nodes, Active DOF 3)
C ======================================================================
      IF (JTYPE .EQ. 3) THEN
        D_AVG = ZERO
        DO I=1, 3
          D_AVG = D_AVG + U(I) / THREE
        ENDDO

        DO KPT=1, 3
          SVARS(KPT)   = D_AVG
          SVARS(3+KPT) = D_AVG
          IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) THEN
            SVARS(6+KPT) = SV_H(PHYSIDX, KPT)
          ENDIF
        ENDDO
        SVARS(10) = ZERO
        SVARS(11) = ZERO
        SVARS(12) = ZERO
        SVARS(13) = ZERO
        SVARS(14) = D_AVG
        SVARS(15) = D_AVG
        IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) THEN
          SVARS(16) = SV_H(PHYSIDX, 1)
        ENDIF
        SVARS(17) = ZERO
        SVARS(18) = ZERO

        IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) THEN
          SV_PHASE(PHYSIDX) = D_AVG
        ENDIF

        XG3(1) = 1.D0/6.D0
        YG3(1) = 1.D0/6.D0
        W3(1)  = 1.D0/6.D0
        XG3(2) = 2.D0/3.D0
        YG3(2) = 1.D0/6.D0
        W3(2)  = 1.D0/6.D0
        XG3(3) = 1.D0/6.D0
        YG3(3) = 2.D0/3.D0
        W3(3)  = 1.D0/6.D0

        JAC(1,1) = COORDS(1,2) - COORDS(1,1)
        JAC(1,2) = COORDS(2,2) - COORDS(2,1)
        JAC(2,1) = COORDS(1,3) - COORDS(1,1)
        JAC(2,2) = COORDS(2,3) - COORDS(2,1)

        DETJ = JAC(1,1)*JAC(2,2) - JAC(1,2)*JAC(2,1)
        INVJ(1,1) =  JAC(2,2)/DETJ
        INVJ(1,2) = -JAC(1,2)/DETJ
        INVJ(2,1) = -JAC(2,1)/DETJ
        INVJ(2,2) =  JAC(1,1)/DETJ

        D_NTRI(1,1) = -ONE
        D_NTRI(1,2) =  ONE
        D_NTRI(1,3) =  ZERO
        D_NTRI(2,1) = -ONE
        D_NTRI(2,2) =  ZERO
        D_NTRI(2,3) =  ONE

        DO I=1, 3
          B_PHTRI(1,I) = INVJ(1,1)*D_NTRI(1,I) + INVJ(1,2)*D_NTRI(2,I)
          B_PHTRI(2,I) = INVJ(2,1)*D_NTRI(1,I) + INVJ(2,2)*D_NTRI(2,I)
        ENDDO

        DO KPT=1, 3
          XI  = XG3(KPT)
          ETA = YG3(KPT)
          WT  = W3(KPT)

          N_TRI(1) = ONE - XI - ETA
          N_TRI(2) = XI
          N_TRI(3) = ETA

          CJAC = DABS(DETJ)*WT

          IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) THEN
            HIST = SV_H(PHYSIDX, KPT)
          ELSE
            HIST = ZERO
          ENDIF

          DO I=1, 3
            DO J=1, 3
              AMATRX(I,J) = AMATRX(I,J) + CJAC*(
     1          (E_GC/E_L0 + TWO*HIST)*N_TRI(I)*N_TRI(J) +
     2          E_GC*E_L0*(B_PHTRI(1,I)*B_PHTRI(1,J) +
     3                     B_PHTRI(2,I)*B_PHTRI(2,J)) )
            ENDDO
            RHS(I,1) = RHS(I,1) + CJAC*(TWO*HIST*N_TRI(I))
          ENDDO
        ENDDO

        DO I=1, 3
          DO J=1, 3
            RHS(I,1) = RHS(I,1) - AMATRX(I,J)*U(J)
          ENDDO
        ENDDO

        WRITE(7,1001) KSTEP, KINC, TIME(2), JELEM, JTYPE, PHYSIDX,
     1    SVARS(14), SVARS(15), SVARS(16),
     2    SV_H(PHYSIDX,1), SV_H(PHYSIDX,2), SV_H(PHYSIDX,3), SV_H(PHYSIDX,4)
      ENDIF

C ======================================================================
C JTYPE = 4: TRIANGULAR MECHANICAL LAYER (3 Nodes, Active DOFs 1, 2)
C ======================================================================
      IF (JTYPE .EQ. 4) THEN
        IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) THEN
          D_VAL = SV_PHASE(PHYSIDX)
        ELSE
          D_VAL = ZERO
        ENDIF

        IF (D_VAL .LT. ZERO) D_VAL = ZERO
        IF (D_VAL .GT. ONE)  D_VAL = ONE
        DEG = (ONE - D_VAL)**2 + E_K

        C11 = E_MOD*(ONE - E_NU)/((ONE + E_NU)*(ONE - TWO*E_NU))
        C12 = E_MOD*E_NU/((ONE + E_NU)*(ONE - TWO*E_NU))
        C22 = C11
        C33 = E_MOD*HALF/(ONE + E_NU)

        DO KPT=1, 3
          SVARS(KPT)   = D_VAL
          SVARS(3+KPT) = D_VAL
          IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) THEN
            SVARS(6+KPT) = SV_H(PHYSIDX, KPT)
          ENDIF
        ENDDO
        SVARS(10) = ZERO
        SVARS(11) = ZERO
        SVARS(12) = ZERO
        SVARS(13) = ZERO
        SVARS(14) = D_VAL
        SVARS(15) = D_VAL
        IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) THEN
          SVARS(16) = SV_H(PHYSIDX, 1)
        ENDIF
        SVARS(17) = ZERO
        SVARS(18) = ZERO

        XG3(1) = 1.D0/6.D0
        YG3(1) = 1.D0/6.D0
        W3(1)  = 1.D0/6.D0
        XG3(2) = 2.D0/3.D0
        YG3(2) = 1.D0/6.D0
        W3(2)  = 1.D0/6.D0
        XG3(3) = 1.D0/6.D0
        YG3(3) = 2.D0/3.D0
        W3(3)  = 1.D0/6.D0

        JAC(1,1) = COORDS(1,2) - COORDS(1,1)
        JAC(1,2) = COORDS(2,2) - COORDS(2,1)
        JAC(2,1) = COORDS(1,3) - COORDS(1,1)
        JAC(2,2) = COORDS(2,3) - COORDS(2,1)

        DETJ = JAC(1,1)*JAC(2,2) - JAC(1,2)*JAC(2,1)
        INVJ(1,1) =  JAC(2,2)/DETJ
        INVJ(1,2) = -JAC(1,2)/DETJ
        INVJ(2,1) = -JAC(2,1)/DETJ
        INVJ(2,2) =  JAC(1,1)/DETJ

        D_NTRI(1,1) = -ONE
        D_NTRI(1,2) =  ONE
        D_NTRI(1,3) =  ZERO
        D_NTRI(2,1) = -ONE
        D_NTRI(2,2) =  ZERO
        D_NTRI(2,3) =  ONE

        DO I=1, 3
          DO J=1, 6
            B_TRI(I,J) = ZERO
          ENDDO
        ENDDO

        DO I=1, 3
          B_TRI(1,2*I-1) = INVJ(1,1)*D_NTRI(1,I) + INVJ(1,2)*D_NTRI(2,I)
          B_TRI(2,2*I)   = INVJ(2,1)*D_NTRI(1,I) + INVJ(2,2)*D_NTRI(2,I)
          B_TRI(3,2*I-1) = B_TRI(2,2*I)
          B_TRI(3,2*I)   = B_TRI(1,2*I-1)
        ENDDO

        DO I=1, 6
          F_INT(I) = ZERO
        ENDDO

        DO KPT=1, 3
          WT  = W3(KPT)
          CJAC = DABS(DETJ)*WT

          STRAIN(1) = ZERO
          STRAIN(2) = ZERO
          STRAIN(3) = ZERO
          DO I=1, 6
            STRAIN(1) = STRAIN(1) + B_TRI(1,I)*U(I)
            STRAIN(2) = STRAIN(2) + B_TRI(2,I)*U(I)
            STRAIN(3) = STRAIN(3) + B_TRI(3,I)*U(I)
          ENDDO

          STRESS(1) = DEG*(C11*STRAIN(1) + C12*STRAIN(2))
          STRESS(2) = DEG*(C12*STRAIN(1) + C22*STRAIN(2))
          STRESS(3) = DEG*(C33*STRAIN(3))

          E11 = STRAIN(1)
          E22 = STRAIN(2)
          E12 = STRAIN(3)*HALF
          TR_E = E11 + E22
          E_POS = HALF*(TR_E + DSQRT((E11-E22)**2 + FOUR*E12**2))
          IF (E_POS .LT. ZERO) E_POS = ZERO
          POS_M = HALF*C11*E_POS**2

          IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) THEN
            IF (POS_M .GT. SV_H(PHYSIDX, KPT)) THEN
              SV_H(PHYSIDX, KPT) = POS_M
            ENDIF
          ENDIF

          DO I=1, 6
            DO J=1, 6
              AMATRX(I,J) = AMATRX(I,J) + CJAC*DEG*(
     1          B_TRI(1,I)*(C11*B_TRI(1,J) + C12*B_TRI(2,J)) +
     2          B_TRI(2,I)*(C12*B_TRI(1,J) + C22*B_TRI(2,J)) +
     3          B_TRI(3,I)*(C33*B_TRI(3,J)) )
            ENDDO
            F_INT(I) = F_INT(I) + CJAC*(
     1        B_TRI(1,I)*STRESS(1) + B_TRI(2,I)*STRESS(2) + B_TRI(3,I)*STRESS(3))
          ENDDO
        ENDDO

        DO I=1, 6
          RHS(I,1) = -F_INT(I)
        ENDDO

        WRITE(7,1001) KSTEP, KINC, TIME(2), JELEM, JTYPE, PHYSIDX,
     1    SVARS(14), SVARS(15), SVARS(16),
     2    SV_H(PHYSIDX,1), SV_H(PHYSIDX,2), SV_H(PHYSIDX,3), SV_H(PHYSIDX,4)
      ENDIF

      RETURN
      END
