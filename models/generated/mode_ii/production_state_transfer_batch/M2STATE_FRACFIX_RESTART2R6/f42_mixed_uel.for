C ======================================================================
C USER SUBROUTINE UEL FOR COUPLED PHASE-FIELD FRACTURE (FRACFIX FORMULATION)
C Mixed Quadrilateral (4-Node) and Triangular (3-Node) Staggered Formulation
C Order-Independent COMMON Ingestion and Initial Transfer Ingestion
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

      INTEGER I, J, K, KPT, PHYSIDX
      DOUBLE PRECISION XI, ETA, WT, CJAC, DETJ, INVJ(2,2)
      DOUBLE PRECISION D_AVG, DEG, HIST, HIST_MAX
      DOUBLE PRECISION E_MOD, E_NU, E_L0, E_GC, E_K, D_VAL
      DOUBLE PRECISION E11, E22, E12, TR_E, E_POS, POS_M
      DOUBLE PRECISION C11, C12, C22, C33
      DOUBLE PRECISION F_INT(8)

      E_L0  = PROPS(1)
      E_GC  = PROPS(2)
      E_MOD = PROPS(3)
      E_NU  = PROPS(4)
      E_K   = PROPS(5)

      DO I=1, NDOFEL
        RHS(I,1) = ZERO
        DO J=1, NDOFEL
          AMATRX(I,J) = ZERO
        ENDDO
      ENDDO

      IF (JTYPE .EQ. 1) THEN
        PHYSIDX = JELEM
      ELSE IF (JTYPE .EQ. 2) THEN
        PHYSIDX = JELEM - 9876
      ELSE IF (JTYPE .EQ. 3) THEN
        PHYSIDX = JELEM
      ELSE IF (JTYPE .EQ. 4) THEN
        PHYSIDX = JELEM - 9876
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
          N_VEC(1) = 0.25D0*(ONE-XI)*(ONE-ETA)
          N_VEC(2) = 0.25D0*(ONE+XI)*(ONE-ETA)
          N_VEC(3) = 0.25D0*(ONE+XI)*(ONE+ETA)
          N_VEC(4) = 0.25D0*(ONE-XI)*(ONE+ETA)
          D_N(1,1) = -0.25D0*(ONE-ETA)
          D_N(1,2) =  0.25D0*(ONE-ETA)
          D_N(1,3) =  0.25D0*(ONE+ETA)
          D_N(1,4) = -0.25D0*(ONE+ETA)
          D_N(2,1) = -0.25D0*(ONE-XI)
          D_N(2,2) = -0.25D0*(ONE+XI)
          D_N(2,3) =  0.25D0*(ONE+XI)
          D_N(2,4) =  0.25D0*(ONE-XI)

          DETJ = ((COORDS(1,2)-COORDS(1,1))*(COORDS(2,4)-COORDS(2,1)) -
     1            (COORDS(1,4)-COORDS(1,1))*(COORDS(2,2)-COORDS(2,1)))/FOUR
          IF (DETJ .LE. ZERO) DETJ = 1.0D-6
          CJAC = DETJ * WT

          INVJ(1,1) = (COORDS(2,4)-COORDS(2,1))/(FOUR*DETJ)
          INVJ(1,2) =-(COORDS(2,2)-COORDS(2,1))/(FOUR*DETJ)
          INVJ(2,1) =-(COORDS(1,4)-COORDS(1,1))/(FOUR*DETJ)
          INVJ(2,2) = (COORDS(1,2)-COORDS(1,1))/(FOUR*DETJ)

          DO I=1, 4
            B_PHASE(1,I) = INVJ(1,1)*D_N(1,I) + INVJ(1,2)*D_N(2,I)
            B_PHASE(2,I) = INVJ(2,1)*D_N(1,I) + INVJ(2,2)*D_N(2,I)
          ENDDO

          HIST = SV_H(PHYSIDX, KPT)

          DO I=1, 4
            DO J=1, 4
              AMATRX(I,J) = AMATRX(I,J) + CJAC*(
     1          (E_GC/E_L0 + TWO*HIST)*N_VEC(I)*N_VEC(J) +
     2          E_GC*E_L0*(B_PHASE(1,I)*B_PHASE(1,J) + B_PHASE(2,I)*B_PHASE(2,J)) )
            ENDDO
            RHS(I,1) = RHS(I,1) + CJAC*TWO*HIST*N_VEC(I)
          ENDDO
        ENDDO

        WRITE(7,1002) KSTEP, KINC, TIME(2), JELEM, JTYPE, PHYSIDX,
     1    SV_H(PHYSIDX,1), SV_H(PHYSIDX,2), SV_H(PHYSIDX,3), SV_H(PHYSIDX,4)
 1002   FORMAT('[H_STARTUP_TRACE] KSTEP=',I1,' KINC=',I1,' TIME=',E12.5,
     1         ' JELEM=',I6,' JTYPE=',I1,' PHYSIDX=',I6,
     2         ' H1=',E12.5,' H2=',E12.5,' H3=',E12.5,' H4=',E12.5)

C ======================================================================
C JTYPE = 2: QUADRILATERAL MECHANICAL LAYER (4 Nodes, Active DOFs 1, 2)
C ======================================================================
      ELSE IF (JTYPE .EQ. 2) THEN
        D_VAL = ZERO
        IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) THEN
          D_VAL = SV_PHASE(PHYSIDX)
        ENDIF
        IF (D_VAL .EQ. ZERO .AND. KSTEP .EQ. 1 .AND. KINC .EQ. 1) THEN
          D_VAL = SVARS(1)
        ENDIF

        DEG = (ONE - D_VAL)**2 + E_K
        C11 = E_MOD*(ONE-E_NU)/((ONE+E_NU)*(ONE-TWO*E_NU)) * DEG
        C12 = E_MOD*E_NU/((ONE+E_NU)*(ONE-TWO*E_NU)) * DEG
        C22 = C11
        C33 = E_MOD/(TWO*(ONE+E_NU)) * DEG

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
          D_N(1,1) = -0.25D0*(ONE-ETA)
          D_N(1,2) =  0.25D0*(ONE-ETA)
          D_N(1,3) =  0.25D0*(ONE+ETA)
          D_N(1,4) = -0.25D0*(ONE+ETA)
          D_N(2,1) = -0.25D0*(ONE-XI)
          D_N(2,2) = -0.25D0*(ONE+XI)
          D_N(2,3) =  0.25D0*(ONE+XI)
          D_N(2,4) =  0.25D0*(ONE-XI)

          DETJ = ((COORDS(1,2)-COORDS(1,1))*(COORDS(2,4)-COORDS(2,1)) -
     1            (COORDS(1,4)-COORDS(1,1))*(COORDS(2,2)-COORDS(2,1)))/FOUR
          IF (DETJ .LE. ZERO) DETJ = 1.0D-6
          CJAC = DETJ * WT

          INVJ(1,1) = (COORDS(2,4)-COORDS(2,1))/(FOUR*DETJ)
          INVJ(1,2) =-(COORDS(2,2)-COORDS(2,1))/(FOUR*DETJ)
          INVJ(2,1) =-(COORDS(1,4)-COORDS(1,1))/(FOUR*DETJ)
          INVJ(2,2) = (COORDS(1,2)-COORDS(1,1))/(FOUR*DETJ)

          DO I=1, 4
            B(1,2*I-1) = INVJ(1,1)*D_N(1,I) + INVJ(1,2)*D_N(2,I)
            B(1,2*I)   = ZERO
            B(2,2*I-1) = ZERO
            B(2,2*I)   = INVJ(2,1)*D_N(1,I) + INVJ(2,2)*D_N(2,I)
            B(3,2*I-1) = B(2,2*I)
            B(3,2*I)   = B(1,2*I-1)
          ENDDO

          STRAIN(1) = ZERO
          STRAIN(2) = ZERO
          STRAIN(3) = ZERO
          DO I=1, 8
            STRAIN(1) = STRAIN(1) + B(1,I)*U(I)
            STRAIN(2) = STRAIN(2) + B(2,I)*U(I)
            STRAIN(3) = STRAIN(3) + B(3,I)*U(I)
          ENDDO

          STRESS(1) = C11*STRAIN(1) + C12*STRAIN(2)
          STRESS(2) = C12*STRAIN(1) + C22*STRAIN(2)
          STRESS(3) = C33*STRAIN(3)

          TR_E = STRAIN(1) + STRAIN(2)
          E_POS = ZERO
          IF (TR_E .GT. ZERO) E_POS = TR_E
          POS_M = HALF*E_MOD/((ONE+E_NU)*(ONE-TWO*E_NU))*(E_POS**2) +
     1            E_MOD/(TWO*(ONE+E_NU))*(STRAIN(1)**2 + STRAIN(2)**2 + HALF*STRAIN(3)**2)
          IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) THEN
            IF (POS_M .GT. SV_H(PHYSIDX, KPT)) THEN
              SV_H(PHYSIDX, KPT) = POS_M
            ENDIF
            SVARS(8+KPT) = SV_H(PHYSIDX, KPT)
          ENDIF

          DO I=1, 8
            F_INT(I) = F_INT(I) + CJAC*(B(1,I)*STRESS(1) + B(2,I)*STRESS(2) + B(3,I)*STRESS(3))
            RHS(I,1) = RHS(I,1) - CJAC*(B(1,I)*STRESS(1) + B(2,I)*STRESS(2) + B(3,I)*STRESS(3))
          ENDDO

          DO I=1, 8
            DO J=1, 8
              AMATRX(I,J) = AMATRX(I,J) + CJAC*(
     1          B(1,I)*(C11*B(1,J) + C12*B(2,J)) +
     2          B(2,I)*(C12*B(1,J) + C22*B(2,J)) +
     3          B(3,I)*(C33*B(3,J)) )
            ENDDO
          ENDDO
        ENDDO

        WRITE(7,1003) KSTEP, KINC, TIME(2), JELEM, JTYPE, PHYSIDX,
     1    F_INT(1), F_INT(3), F_INT(5), F_INT(7)
 1003   FORMAT('[FORCE_TRACE] KSTEP=',I1,' KINC=',I1,' TIME=',E12.5,
     1         ' JELEM=',I6,' JTYPE=',I1,' PHYSIDX=',I6,
     2         ' FINT1_N1=',E12.5,' FINT1_N2=',E12.5,
     3         ' FINT1_N3=',E12.5,' FINT1_N4=',E12.5)

C ======================================================================
C JTYPE = 3: TRIANGULAR PHASE-FIELD LAYER (3 Nodes, Active DOF 3)
C ======================================================================
      ELSE IF (JTYPE .EQ. 3) THEN
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

        XG3(1) = 1.D0/3.D0
        YG3(1) = 1.D0/3.D0
        W3(1)  = 0.5D0
        XG3(2) = 0.6D0
        YG3(2) = 0.2D0
        W3(2)  = 1.D0/6.D0
        XG3(3) = 0.2D0
        YG3(3) = 0.6D0
        W3(3)  = 1.D0/6.D0

        DETJ = (COORDS(1,2)-COORDS(1,1))*(COORDS(2,3)-COORDS(2,1)) -
     1         (COORDS(1,3)-COORDS(1,1))*(COORDS(2,2)-COORDS(2,1))
        IF (DETJ .LE. ZERO) DETJ = 1.0D-6

        INVJ(1,1) = (COORDS(2,3)-COORDS(2,1))/DETJ
        INVJ(1,2) =-(COORDS(2,2)-COORDS(2,1))/DETJ
        INVJ(2,1) =-(COORDS(1,3)-COORDS(1,1))/DETJ
        INVJ(2,2) = (COORDS(1,2)-COORDS(1,1))/DETJ

        B_PHTRI(1,1) = -INVJ(1,1) - INVJ(1,2)
        B_PHTRI(1,2) =  INVJ(1,1)
        B_PHTRI(1,3) =  INVJ(1,2)
        B_PHTRI(2,1) = -INVJ(2,1) - INVJ(2,2)
        B_PHTRI(2,2) =  INVJ(2,1)
        B_PHTRI(2,3) =  INVJ(2,2)

        DO KPT=1, 3
          XI  = XG3(KPT)
          ETA = YG3(KPT)
          WT  = W3(KPT)
          CJAC = DETJ * WT
          N_TRI(1) = ONE - XI - ETA
          N_TRI(2) = XI
          N_TRI(3) = ETA

          HIST = SV_H(PHYSIDX, KPT)

          DO I=1, 3
            DO J=1, 3
              AMATRX(I,J) = AMATRX(I,J) + CJAC*(
     1          (E_GC/E_L0 + TWO*HIST)*N_TRI(I)*N_TRI(J) +
     2          E_GC*E_L0*(B_PHTRI(1,I)*B_PHTRI(1,J) + B_PHTRI(2,I)*B_PHTRI(2,J)) )
            ENDDO
            RHS(I,1) = RHS(I,1) + CJAC*TWO*HIST*N_TRI(I)
          ENDDO
        ENDDO

        WRITE(7,1002) KSTEP, KINC, TIME(2), JELEM, JTYPE, PHYSIDX,
     1    SV_H(PHYSIDX,1), SV_H(PHYSIDX,2), SV_H(PHYSIDX,3), ZERO

C ======================================================================
C JTYPE = 4: TRIANGULAR MECHANICAL LAYER (3 Nodes, Active DOFs 1, 2)
C ======================================================================
      ELSE IF (JTYPE .EQ. 4) THEN
        D_VAL = ZERO
        IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) THEN
          D_VAL = SV_PHASE(PHYSIDX)
        ENDIF
        IF (D_VAL .EQ. ZERO .AND. KSTEP .EQ. 1 .AND. KINC .EQ. 1) THEN
          D_VAL = SVARS(1)
        ENDIF

        DEG = (ONE - D_VAL)**2 + E_K
        C11 = E_MOD*(ONE-E_NU)/((ONE+E_NU)*(ONE-TWO*E_NU)) * DEG
        C12 = E_MOD*E_NU/((ONE+E_NU)*(ONE-TWO*E_NU)) * DEG
        C22 = C11
        C33 = E_MOD/(TWO*(ONE+E_NU)) * DEG

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

        DETJ = (COORDS(1,2)-COORDS(1,1))*(COORDS(2,3)-COORDS(2,1)) -
     1         (COORDS(1,3)-COORDS(1,1))*(COORDS(2,2)-COORDS(2,1))
        IF (DETJ .LE. ZERO) DETJ = 1.0D-6
        CJAC = DETJ * 0.5D0

        INVJ(1,1) = (COORDS(2,3)-COORDS(2,1))/DETJ
        INVJ(1,2) =-(COORDS(2,2)-COORDS(2,1))/DETJ
        INVJ(2,1) =-(COORDS(1,3)-COORDS(1,1))/DETJ
        INVJ(2,2) = (COORDS(1,2)-COORDS(1,1))/DETJ

        B_TRI(1,1) = -INVJ(1,1) - INVJ(1,2)
        B_TRI(1,2) =  ZERO
        B_TRI(1,3) =  INVJ(1,1)
        B_TRI(1,4) =  ZERO
        B_TRI(1,5) =  INVJ(1,2)
        B_TRI(1,6) =  ZERO

        B_TRI(2,1) =  ZERO
        B_TRI(2,2) = -INVJ(2,1) - INVJ(2,2)
        B_TRI(2,3) =  ZERO
        B_TRI(2,4) =  INVJ(2,1)
        B_TRI(2,5) =  ZERO
        B_TRI(2,6) =  INVJ(2,2)

        B_TRI(3,1) = B_TRI(2,2)
        B_TRI(3,2) = B_TRI(1,1)
        B_TRI(3,3) = B_TRI(2,4)
        B_TRI(3,4) = B_TRI(1,3)
        B_TRI(3,5) = B_TRI(2,6)
        B_TRI(3,6) = B_TRI(1,5)

        STRAIN(1) = ZERO
        STRAIN(2) = ZERO
        STRAIN(3) = ZERO
        DO I=1, 6
          STRAIN(1) = STRAIN(1) + B_TRI(1,I)*U(I)
          STRAIN(2) = STRAIN(2) + B_TRI(2,I)*U(I)
          STRAIN(3) = STRAIN(3) + B_TRI(3,I)*U(I)
        ENDDO

        STRESS(1) = C11*STRAIN(1) + C12*STRAIN(2)
        STRESS(2) = C12*STRAIN(1) + C22*STRAIN(2)
        STRESS(3) = C33*STRAIN(3)

        TR_E = STRAIN(1) + STRAIN(2)
        E_POS = ZERO
        IF (TR_E .GT. ZERO) E_POS = TR_E
        POS_M = HALF*E_MOD/((ONE+E_NU)*(ONE-TWO*E_NU))*(E_POS**2) +
     1          E_MOD/(TWO*(ONE+E_NU))*(STRAIN(1)**2 + STRAIN(2)**2 + HALF*STRAIN(3)**2)
        IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) THEN
          DO KPT=1, 3
            IF (POS_M .GT. SV_H(PHYSIDX, KPT)) THEN
              SV_H(PHYSIDX, KPT) = POS_M
            ENDIF
            SVARS(6+KPT) = SV_H(PHYSIDX, KPT)
          ENDDO
        ENDIF

C Zero internal force accumulation before loop
        DO I=1, 6
          F_INT(I) = ZERO
        ENDDO

        DO I=1, 6
          F_INT(I) = F_INT(I) + CJAC*(B_TRI(1,I)*STRESS(1) + B_TRI(2,I)*STRESS(2) + B_TRI(3,I)*STRESS(3))
          RHS(I,1) = RHS(I,1) - CJAC*(B_TRI(1,I)*STRESS(1) + B_TRI(2,I)*STRESS(2) + B_TRI(3,I)*STRESS(3))
        ENDDO

        DO I=1, 6
          DO J=1, 6
            AMATRX(I,J) = AMATRX(I,J) + CJAC*(
     1        B_TRI(1,I)*(C11*B_TRI(1,J) + C12*B_TRI(2,J)) +
     2        B_TRI(2,I)*(C12*B_TRI(1,J) + C22*B_TRI(2,J)) +
     3        B_TRI(3,I)*(C33*B_TRI(3,J)) )
          ENDDO
        ENDDO

        WRITE(7,1003) KSTEP, KINC, TIME(2), JELEM, JTYPE, PHYSIDX,
     1    F_INT(1), F_INT(3), F_INT(5), ZERO
      ENDIF

C ======================================================================
C STATE_TRACE Audit (Representative Quads and Triangles)
C ======================================================================
      IF (KSTEP.EQ.2 .AND. KINC.EQ.1) THEN
        IF (PHYSIDX.EQ.2292 .OR. PHYSIDX.EQ.7186 .OR.
     1      PHYSIDX.EQ.100  .OR. PHYSIDX.EQ.4994 .OR.
     2      PHYSIDX.EQ.1500 .OR. PHYSIDX.EQ.6394 .OR.
     3      PHYSIDX.EQ.4862 .OR. PHYSIDX.EQ.9756) THEN
          IF (JTYPE.EQ.2 .OR. JTYPE.EQ.4) THEN
            WRITE(*,1001) KSTEP, KINC, JELEM, JTYPE, PHYSIDX,
     1        D_VAL, SVARS(14), SVARS(15), SVARS(16)
            WRITE(6,1001) KSTEP, KINC, JELEM, JTYPE, PHYSIDX,
     1        D_VAL, SVARS(14), SVARS(15), SVARS(16)
            WRITE(7,1001) KSTEP, KINC, JELEM, JTYPE, PHYSIDX,
     1        D_VAL, SVARS(14), SVARS(15), SVARS(16)
 1001       FORMAT('[STATE_TRACE] KSTEP=',I1,' KINC=',I1,
     1             ' JELEM=',I6,' JTYPE=',I1,' PHYSIDX=',I6,
     2             ' INCOMING_PHASE=',F8.5,' SDV14=',F8.5,
     3             ' SDV15=',F8.5,' SDV16=',E12.5)
          ELSE IF (JTYPE.EQ.1 .OR. JTYPE.EQ.3) THEN
            WRITE(*,1004) KSTEP, KINC, JELEM, JTYPE, PHYSIDX,
     1        D_AVG, SVARS(14), SVARS(15), SVARS(16)
            WRITE(6,1004) KSTEP, KINC, JELEM, JTYPE, PHYSIDX,
     1        D_AVG, SVARS(14), SVARS(15), SVARS(16)
            WRITE(7,1004) KSTEP, KINC, JELEM, JTYPE, PHYSIDX,
     1        D_AVG, SVARS(14), SVARS(15), SVARS(16)
 1004       FORMAT('[STATE_TRACE] KSTEP=',I1,' KINC=',I1,
     1             ' JELEM=',I6,' JTYPE=',I1,' PHYSIDX=',I6,
     2             ' INCOMING_PHASE=',F8.5,' SDV14=',F8.5,
     3             ' SDV15=',F8.5,' SDV16=',E12.5)
          ENDIF
        ENDIF
      ENDIF

      RETURN
      END

      SUBROUTINE UMAT(STRESS,STATEV,DDSDDE,SSE,SPD,SCD,
     1 RPL,DDSDDD,DRPLDE,DRPLDD,STRAN,DSTRAN,
     2 TIME,DTIME,TEMP,DTEMP,PREDEF,DPRED,CMNAME,
     3 NDI,NSHR,NTENS,NSTATV,PROPS,NPROPS,COORDS,
     4 DROTT,PNEWDT,CELENT,DFGRD0,DFGRD1,NOEL,NPT,
     5 LAYER,KSPT,KSTEP,KINC)
      INCLUDE 'ABA_PARAM.INC'
      CHARACTER*80 CMNAME
      DIMENSION STRESS(NTENS),STATEV(NSTATV),DDSDDE(NTENS,NTENS),
     1 STRAN(NTENS),DSTRAN(NTENS),TIME(2),PREDEF(1),DPRED(1),
     2 PROPS(NPROPS),COORDS(3),DROTT(3,3),DFGRD0(3,3),DFGRD1(3,3)
      INTEGER I, J
      DO I=1, NTENS
        STRESS(I) = 0.D0
        DO J=1, NTENS
          DDSDDE(I,J) = 0.D0
        ENDDO
        DDSDDE(I,I) = 1.D-11
      ENDDO
      RETURN
      END
