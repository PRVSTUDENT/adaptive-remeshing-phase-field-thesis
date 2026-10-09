C ======================================================================
C Mode-II Dual-Element Phase-Field UEL with Miehe Spectral Split
C Governing References:
C   1. Pandey & Kumar (2025) CMES, Vol. 144, No. 3, Section 4.2 (pp. 3270-3272)
C   2. Miehe, Hofacker, Welschinger (2010) CMAME, 199(45-48):2765-2778
C   3. Miehe, Welschinger, Hofacker (2010) IJNME, 83(10):1273-1311
C
C Element Architecture (Staggered Dual Formulation):
C   JTYPE = 1: 4-node Quad Phase-Field Element (1 DOF: d)
C   JTYPE = 2: 4-node Quad Mechanical Element (2 DOFs: u_x, u_y)
C   JTYPE = 3: 3-node Tri Phase-Field Element (1 DOF: d)
C   JTYPE = 4: 3-node Tri Mechanical Element (2 DOFs: u_x, u_y)
C   UMAT: Companion Continuum Visualization Element (SDV outputs)
C ======================================================================
      SUBROUTINE UEL(RHS,AMATRX,SVARS,ENERGY,NDOFEL,NRHS,NSVARS,
     1 PROPS,NPROPS,COORDS,MCRD,NNODE,U,DU,V,A,JTYPE,TIME,DTIME,
     2 KSTEP,KINC,JELEM,PARAMS,NDLOAD,JDLTYP,ADLMAG,PREDEF,NPREDF,
     3 LFLAGS,MLVARX,DDLMAG,MDLOAD,PNEWDT,JPROPS,NJPROP,PERIOD)

      INCLUDE 'ABA_PARAM.INC'

      DIMENSION RHS(MLVARX,*),AMATRX(NDOFEL,NDOFEL),PROPS(*),
     1 SVARS(*),ENERGY(8),COORDS(MCRD,NNODE),U(NDOFEL),
     2 DU(MLVARX,*),V(NDOFEL),A(NDOFEL),TIME(2),PARAMS(*),
     3 JDLTYP(MDLOAD,*),ADLMAG(MDLOAD,*),DDLMAG(MDLOAD,*),
     4 PREDEF(2,NPREDF,NNODE),LFLAGS(*),JPROPS(*)

      PARAMETER (MAX_ELEM = 200000)
      PARAMETER (ZERO = 0.0D0, ONE = 1.0D0, TWO = 2.0D0, HALF = 0.5D0)
      PARAMETER (FOUR = 4.0D0, THREE = 3.0D0, SIX = 6.0D0)

      COMMON /CB_STATE_TRANS/ SV_PHASE_TRIAL(MAX_ELEM),
     1                        SV_H_TRIAL(MAX_ELEM, 4),
     2                        SV_PSI_E_TRIAL(MAX_ELEM)

      DIMENSION XI(4), ETA(4), W(4)
      DIMENSION SHP(4), DNDX(2,4), DNDXI(2,4), XJAC(2,2), INVJ(2,2)
      DIMENSION B(3,8), D_MECH(3,3), STRAIN(3), STRESS(3)
      DIMENSION SIG_POS(3), SIG_NEG(3), D_POS(3,3), D_NEG(3,3)
      DIMENSION V1(3), V2(3), V12(3), F_INT(8)

      DIMENSION N_TRI(3), D_NTRI(2,3), B_TRI(3,6), B_PHTRI(2,3)
      DIMENSION XI3(1), ETA3(1), W3(1)

C     ------------------------------------------------------------------
C     Material & Phase-Field Properties
C     ------------------------------------------------------------------
      E_MOD = PROPS(1)
      E_NU  = PROPS(2)
      E_GC  = PROPS(3)
      E_L0  = PROPS(4)
      E_K   = PROPS(5)
      IF (E_K .LE. ZERO) E_K = 1.0D-7

C     Lamé parameters (Plane Strain)
      E_LAM = (E_MOD * E_NU) / ((ONE + E_NU) * (ONE - TWO * E_NU))
      E_MU  = E_MOD / (TWO * (ONE + E_NU))

C     Co-located physical element indexing
      IF (NPROPS .GE. 6) THEN
        N_PHYS = INT(PROPS(6))
      ELSE
        N_PHYS = 22530
      ENDIF

      IF (JTYPE .EQ. 1 .OR. JTYPE .EQ. 3) THEN
        PHYSIDX = JELEM
      ELSE IF (JTYPE .EQ. 2 .OR. JTYPE .EQ. 4) THEN
        PHYSIDX = JELEM - N_PHYS
      ELSE
        PHYSIDX = JELEM
      ENDIF
      IF (PHYSIDX .LT. 1) PHYSIDX = 1
      IF (PHYSIDX .GT. MAX_ELEM) PHYSIDX = MAX_ELEM

C     Zero arrays
      DO I = 1, NDOFEL
        RHS(I,1) = ZERO
        DO J = 1, NDOFEL
          AMATRX(I,J) = ZERO
        ENDDO
      ENDDO

C ======================================================================
C JTYPE = 1 : 4-NODE QUADRILATERAL PHASE-FIELD ELEMENT (1 DOF / NODE: d)
C ======================================================================
      IF (JTYPE .EQ. 1) THEN
        XI(1)  = -ONE/SQRT(THREE)
        ETA(1) = -ONE/SQRT(THREE)
        W(1)   =  ONE
        XI(2)  =  ONE/SQRT(THREE)
        ETA(2) = -ONE/SQRT(THREE)
        W(2)   =  ONE
        XI(3)  =  ONE/SQRT(THREE)
        ETA(3) =  ONE/SQRT(THREE)
        W(3)   =  ONE
        XI(4)  = -ONE/SQRT(THREE)
        ETA(4) =  ONE/SQRT(THREE)
        W(4)   =  ONE

        DO KPT = 1, 4
          P_XI  = XI(KPT)
          P_ETA = ETA(KPT)

          SHP(1) = 0.25D0*(ONE - P_XI)*(ONE - P_ETA)
          SHP(2) = 0.25D0*(ONE + P_XI)*(ONE - P_ETA)
          SHP(3) = 0.25D0*(ONE + P_XI)*(ONE + P_ETA)
          SHP(4) = 0.25D0*(ONE - P_XI)*(ONE + P_ETA)

          DNDXI(1,1) = -0.25D0*(ONE - P_ETA)
          DNDXI(1,2) =  0.25D0*(ONE - P_ETA)
          DNDXI(1,3) =  0.25D0*(ONE + P_ETA)
          DNDXI(1,4) = -0.25D0*(ONE + P_ETA)

          DNDXI(2,1) = -0.25D0*(ONE - P_XI)
          DNDXI(2,2) = -0.25D0*(ONE + P_XI)
          DNDXI(2,3) =  0.25D0*(ONE + P_XI)
          DNDXI(2,4) =  0.25D0*(ONE - P_XI)

          XJAC(1,1) = ZERO
          XJAC(1,2) = ZERO
          XJAC(2,1) = ZERO
          XJAC(2,2) = ZERO
          DO I = 1, 4
            XJAC(1,1) = XJAC(1,1) + DNDXI(1,I)*COORDS(1,I)
            XJAC(1,2) = XJAC(1,2) + DNDXI(1,I)*COORDS(2,I)
            XJAC(2,1) = XJAC(2,1) + DNDXI(2,I)*COORDS(1,I)
            XJAC(2,2) = XJAC(2,2) + DNDXI(2,I)*COORDS(2,I)
          ENDDO

          DET = XJAC(1,1)*XJAC(2,2) - XJAC(1,2)*XJAC(2,1)
          IF (DET .LE. ZERO) DET = 1.0D-12
          INVJ(1,1) =  XJAC(2,2)/DET
          INVJ(1,2) = -XJAC(1,2)/DET
          INVJ(2,1) = -XJAC(2,1)/DET
          INVJ(2,2) =  XJAC(1,1)/DET

          DO I = 1, 4
            DNDX(1,I) = INVJ(1,1)*DNDXI(1,I) + INVJ(1,2)*DNDXI(2,I)
            DNDX(2,I) = INVJ(2,1)*DNDXI(1,I) + INVJ(2,2)*DNDXI(2,I)
          ENDDO

          CJAC = DET * W(KPT)
          HIST = SV_H_TRIAL(PHYSIDX, KPT)

          DO I = 1, 4
            DO J = 1, 4
              BDB = DNDX(1,I)*DNDX(1,J) + DNDX(2,I)*DNDX(2,J)
              AMATRX(I,J) = AMATRX(I,J) + CJAC * (
     1          (E_GC * E_L0) * BDB +
     2          (E_GC / E_L0 + TWO * HIST) * SHP(I) * SHP(J))
            ENDDO
            RHS(I,1) = RHS(I,1) + CJAC * TWO * HIST * SHP(I)
          ENDDO
        ENDDO

        DO I = 1, 4
          DO J = 1, 4
            RHS(I,1) = RHS(I,1) - AMATRX(I,J)*U(J)
          ENDDO
        ENDDO

C       Average phase-field damage for companion mechanical element
        D_AVG = 0.25D0 * (U(1) + U(2) + U(3) + U(4))
        SV_PHASE_TRIAL(PHYSIDX) = D_AVG

C ======================================================================
C JTYPE = 2 : 4-NODE QUAD MECHANICAL ELEMENT WITH MIEHE SPECTRAL SPLIT
C ======================================================================
      ELSEIF (JTYPE .EQ. 2) THEN
        XI(1)  = -ONE/SQRT(THREE)
        ETA(1) = -ONE/SQRT(THREE)
        W(1)   =  ONE
        XI(2)  =  ONE/SQRT(THREE)
        ETA(2) = -ONE/SQRT(THREE)
        W(2)   =  ONE
        XI(3)  =  ONE/SQRT(THREE)
        ETA(3) =  ONE/SQRT(THREE)
        W(3)   =  ONE
        XI(4)  = -ONE/SQRT(THREE)
        ETA(4) =  ONE/SQRT(THREE)
        W(4)   =  ONE

        DO I = 1, 8
          F_INT(I) = ZERO
        ENDDO

        D_VAL = SV_PHASE_TRIAL(PHYSIDX)
        IF (D_VAL .LT. ZERO) D_VAL = ZERO
        IF (D_VAL .GT. ONE)  D_VAL = ONE
        DEG   = (ONE - D_VAL)**2 + E_K

        E_ELAS_ELEM = ZERO

        DO KPT = 1, 4
          P_XI  = XI(KPT)
          P_ETA = ETA(KPT)

          DNDXI(1,1) = -0.25D0*(ONE - P_ETA)
          DNDXI(1,2) =  0.25D0*(ONE - P_ETA)
          DNDXI(1,3) =  0.25D0*(ONE + P_ETA)
          DNDXI(1,4) = -0.25D0*(ONE + P_ETA)

          DNDXI(2,1) = -0.25D0*(ONE - P_XI)
          DNDXI(2,2) = -0.25D0*(ONE + P_XI)
          DNDXI(2,3) =  0.25D0*(ONE + P_XI)
          DNDXI(2,4) =  0.25D0*(ONE - P_XI)

          XJAC(1,1) = ZERO
          XJAC(1,2) = ZERO
          XJAC(2,1) = ZERO
          XJAC(2,2) = ZERO
          DO I = 1, 4
            XJAC(1,1) = XJAC(1,1) + DNDXI(1,I)*COORDS(1,I)
            XJAC(1,2) = XJAC(1,2) + DNDXI(1,I)*COORDS(2,I)
            XJAC(2,1) = XJAC(2,1) + DNDXI(2,I)*COORDS(1,I)
            XJAC(2,2) = XJAC(2,2) + DNDXI(2,I)*COORDS(2,I)
          ENDDO

          DET = XJAC(1,1)*XJAC(2,2) - XJAC(1,2)*XJAC(2,1)
          IF (DET .LE. ZERO) DET = 1.0D-12
          INVJ(1,1) =  XJAC(2,2)/DET
          INVJ(1,2) = -XJAC(1,2)/DET
          INVJ(2,1) = -XJAC(2,1)/DET
          INVJ(2,2) =  XJAC(1,1)/DET

          DO I = 1, 4
            DNDX(1,I) = INVJ(1,1)*DNDXI(1,I) + INVJ(1,2)*DNDXI(2,I)
            DNDX(2,I) = INVJ(2,1)*DNDXI(1,I) + INVJ(2,2)*DNDXI(2,I)
          ENDDO

          CJAC = DET * W(KPT)

C         B-matrix (Plane Strain: eps11, eps22, gamma12)
          DO I = 1, 4
            B(1, 2*I-1) = DNDX(1,I)
            B(1, 2*I)   = ZERO
            B(2, 2*I-1) = ZERO
            B(2, 2*I)   = DNDX(2,I)
            B(3, 2*I-1) = DNDX(2,I)
            B(3, 2*I)   = DNDX(1,I)
          ENDDO

C         Compute strains
          STRAIN(1) = ZERO
          STRAIN(2) = ZERO
          STRAIN(3) = ZERO
          DO I = 1, 8
            STRAIN(1) = STRAIN(1) + B(1,I)*U(I)
            STRAIN(2) = STRAIN(2) + B(2,I)*U(I)
            STRAIN(3) = STRAIN(3) + B(3,I)*U(I)
          ENDDO

          EPS11 = STRAIN(1)
          EPS22 = STRAIN(2)
          EPS12 = HALF * STRAIN(3)

C         --------------------------------------------------------------
C         2D Miehe Spectral Decomposition
C         --------------------------------------------------------------
          TR_EPS = EPS11 + EPS22
          IF (TR_EPS .GT. ZERO) THEN
            TR_POS = TR_EPS
            TR_NEG = ZERO
            H_VOL_POS = ONE
            H_VOL_NEG = ZERO
          ELSE
            TR_POS = ZERO
            TR_NEG = TR_EPS
            H_VOL_POS = ZERO
            H_VOL_NEG = ONE
          ENDIF

          EPS_BAR = HALF * (EPS11 + EPS22)
          R_RAD   = SQRT(MAX((HALF*(EPS11 - EPS22))**2 + EPS12**2, ZERO))

          EPS1 = EPS_BAR + R_RAD
          EPS2 = EPS_BAR - R_RAD

          IF (EPS1 .GT. ZERO) THEN
            EPS1_POS  = EPS1
            EPS1_NEG  = ZERO
            H1_POS    = ONE
            H1_NEG    = ZERO
          ELSE
            EPS1_POS  = ZERO
            EPS1_NEG  = EPS1
            H1_POS    = ZERO
            H1_NEG    = ONE
          ENDIF

          IF (EPS2 .GT. ZERO) THEN
            EPS2_POS  = EPS2
            EPS2_NEG  = ZERO
            H2_POS    = ONE
            H2_NEG    = ZERO
          ELSE
            EPS2_POS  = ZERO
            EPS2_NEG  = EPS2
            H2_POS    = ZERO
            H2_NEG    = ONE
          ENDIF

C         Strain Energy Densities
          PSI_0_POS = HALF * E_LAM * (TR_POS**2) +
     1                E_MU * (EPS1_POS**2 + EPS2_POS**2)
          PSI_0_NEG = HALF * E_LAM * (TR_NEG**2) +
     1                E_MU * (EPS1_NEG**2 + EPS2_NEG**2)

C         Update crack driving history variable
          HIST = SV_H_TRIAL(PHYSIDX, KPT)
          IF (PSI_0_POS .GT. HIST) THEN
            HIST = PSI_0_POS
            SV_H_TRIAL(PHYSIDX, KPT) = PSI_0_POS
          ENDIF

C         Projection Tensors v1, v2, v12
          IF (R_RAD .GT. 1.0D-14) THEN
            COS2T = HALF * (EPS11 - EPS22) / R_RAD
            SIN2T = EPS12 / R_RAD
            THETA_POS = (EPS1_POS - EPS2_POS) / (TWO * R_RAD)
            THETA_NEG = (EPS1_NEG - EPS2_NEG) / (TWO * R_RAD)
          ELSE
            COS2T = ONE
            SIN2T = ZERO
            THETA_POS = HALF * (H1_POS + H2_POS)
            THETA_NEG = HALF * (H1_NEG + H2_NEG)
          ENDIF

          V1(1) = HALF * (ONE + COS2T)
          V1(2) = HALF * (ONE - COS2T)
          V1(3) = HALF * SIN2T

          V2(1) = HALF * (ONE - COS2T)
          V2(2) = HALF * (ONE + COS2T)
          V2(3) = -HALF * SIN2T

          V12(1) = -SIN2T
          V12(2) =  SIN2T
          V12(3) =  COS2T

C         Spectral Stresses
          SIG_POS(1) = E_LAM*TR_POS + TWO*E_MU*(EPS1_POS*V1(1) + EPS2_POS*V2(1))
          SIG_POS(2) = E_LAM*TR_POS + TWO*E_MU*(EPS1_POS*V1(2) + EPS2_POS*V2(2))
          SIG_POS(3) = TWO*E_MU*(EPS1_POS*V1(3) + EPS2_POS*V2(3))

          SIG_NEG(1) = E_LAM*TR_NEG + TWO*E_MU*(EPS1_NEG*V1(1) + EPS2_NEG*V2(1))
          SIG_NEG(2) = E_LAM*TR_NEG + TWO*E_MU*(EPS1_NEG*V1(2) + EPS2_NEG*V2(2))
          SIG_NEG(3) = TWO*E_MU*(EPS1_NEG*V1(3) + EPS2_NEG*V2(3))

          STRESS(1) = DEG * SIG_POS(1) + SIG_NEG(1)
          STRESS(2) = DEG * SIG_POS(2) + SIG_NEG(2)
          STRESS(3) = DEG * SIG_POS(3) + SIG_NEG(3)

C         Tangent Stiffness Tensor D_mech
          DO I = 1, 3
            DO J = 1, 3
              D_POS(I,J) = ZERO
              D_NEG(I,J) = ZERO
            ENDDO
          ENDDO

C         Volumetric isotropic projection
          D_POS(1,1) = D_POS(1,1) + E_LAM * H_VOL_POS
          D_POS(1,2) = D_POS(1,2) + E_LAM * H_VOL_POS
          D_POS(2,1) = D_POS(2,1) + E_LAM * H_VOL_POS
          D_POS(2,2) = D_POS(2,2) + E_LAM * H_VOL_POS

          D_NEG(1,1) = D_NEG(1,1) + E_LAM * H_VOL_NEG
          D_NEG(1,2) = D_NEG(1,2) + E_LAM * H_VOL_NEG
          D_NEG(2,1) = D_NEG(2,1) + E_LAM * H_VOL_NEG
          D_NEG(2,2) = D_NEG(2,2) + E_LAM * H_VOL_NEG

C         Principal projections
          DO I = 1, 3
            DO J = 1, 3
              D_POS(I,J) = D_POS(I,J) + TWO * E_MU * (
     1          H1_POS * V1(I)*V1(J) + H2_POS * V2(I)*V2(J) +
     2          THETA_POS * HALF * V12(I)*V12(J))

              D_NEG(I,J) = D_NEG(I,J) + TWO * E_MU * (
     1          H1_NEG * V1(I)*V1(J) + H2_NEG * V2(I)*V2(J) +
     2          THETA_NEG * HALF * V12(I)*V12(J))
            ENDDO
          ENDDO

          DO I = 1, 3
            DO J = 1, 3
              D_MECH(I,J) = DEG * D_POS(I,J) + D_NEG(I,J)
            ENDDO
          ENDDO

C         Assemble internal force and tangent stiffness
          DO I = 1, 8
            DO J = 1, 3
              F_INT(I) = F_INT(I) + CJAC * B(J,I)*STRESS(J)
            ENDDO
            DO J = 1, 8
              DO K = 1, 3
                DO L = 1, 3
                  AMATRX(I,J) = AMATRX(I,J) +
     1              CJAC * B(K,I)*D_MECH(K,L)*B(L,J)
                ENDDO
              ENDDO
            ENDDO
          ENDDO

C         Degraded elastic strain energy density
          PSI_E_PT = DEG * PSI_0_POS + PSI_0_NEG
          E_ELAS_ELEM = E_ELAS_ELEM + CJAC * PSI_E_PT

          SVARS(KPT)   = STRAIN(1)
          SVARS(4+KPT) = STRESS(1)
        ENDDO

        DO I = 1, 8
          RHS(I,1) = -F_INT(I)
        ENDDO

        SV_PSI_E_TRIAL(PHYSIDX) = E_ELAS_ELEM

C ======================================================================
C JTYPE = 3 : 3-NODE TRIANGULAR PHASE-FIELD ELEMENT (1 DOF / NODE: d)
C ======================================================================
      ELSEIF (JTYPE .EQ. 3) THEN
        N_TRI(1) = ONE/THREE
        N_TRI(2) = ONE/THREE
        N_TRI(3) = ONE/THREE

        D_NTRI(1,1) = -ONE
        D_NTRI(1,2) =  ONE
        D_NTRI(1,3) =  ZERO
        D_NTRI(2,1) = -ONE
        D_NTRI(2,2) =  ZERO
        D_NTRI(2,3) =  ONE

        XJAC(1,1) = ZERO
        XJAC(1,2) = ZERO
        XJAC(2,1) = ZERO
        XJAC(2,2) = ZERO
        DO I = 1, 3
          XJAC(1,1) = XJAC(1,1) + D_NTRI(1,I)*COORDS(1,I)
          XJAC(1,2) = XJAC(1,2) + D_NTRI(1,I)*COORDS(2,I)
          XJAC(2,1) = XJAC(2,1) + D_NTRI(2,I)*COORDS(1,I)
          XJAC(2,2) = XJAC(2,2) + D_NTRI(2,I)*COORDS(2,I)
        ENDDO

        DET = XJAC(1,1)*XJAC(2,2) - XJAC(1,2)*XJAC(2,1)
        IF (DET .LE. ZERO) DET = 1.0D-12
        INVJ(1,1) =  XJAC(2,2)/DET
        INVJ(1,2) = -XJAC(1,2)/DET
        INVJ(2,1) = -XJAC(2,1)/DET
        INVJ(2,2) =  XJAC(1,1)/DET

        DO I = 1, 3
          B_PHTRI(1,I) = INVJ(1,1)*D_NTRI(1,I) + INVJ(1,2)*D_NTRI(2,I)
          B_PHTRI(2,I) = INVJ(2,1)*D_NTRI(1,I) + INVJ(2,2)*D_NTRI(2,I)
        ENDDO

        CJAC = HALF * DET
        HIST = SV_H_TRIAL(PHYSIDX, 1)

        DO I = 1, 3
          DO J = 1, 3
            BDB = B_PHTRI(1,I)*B_PHTRI(1,J) + B_PHTRI(2,I)*B_PHTRI(2,J)
            AMATRX(I,J) = AMATRX(I,J) + CJAC * (
     1        (E_GC * E_L0) * BDB +
     2        (E_GC / E_L0 + TWO * HIST) * N_TRI(I) * N_TRI(J))
          ENDDO
          RHS(I,1) = RHS(I,1) + CJAC * TWO * HIST * N_TRI(I)
        ENDDO

        DO I = 1, 3
          DO J = 1, 3
            RHS(I,1) = RHS(I,1) - AMATRX(I,J)*U(J)
          ENDDO
        ENDDO

        D_AVG = (U(1) + U(2) + U(3)) / THREE
        SV_PHASE_TRIAL(PHYSIDX) = D_AVG

C ======================================================================
C JTYPE = 4 : 3-NODE TRI MECHANICAL ELEMENT WITH MIEHE SPECTRAL SPLIT
C ======================================================================
      ELSEIF (JTYPE .EQ. 4) THEN
        DO I = 1, 6
          F_INT(I) = ZERO
        ENDDO

        D_NTRI(1,1) = -ONE
        D_NTRI(1,2) =  ONE
        D_NTRI(1,3) =  ZERO
        D_NTRI(2,1) = -ONE
        D_NTRI(2,2) =  ZERO
        D_NTRI(2,3) =  ONE

        XJAC(1,1) = ZERO
        XJAC(1,2) = ZERO
        XJAC(2,1) = ZERO
        XJAC(2,2) = ZERO
        DO I = 1, 3
          XJAC(1,1) = XJAC(1,1) + D_NTRI(1,I)*COORDS(1,I)
          XJAC(1,2) = XJAC(1,2) + D_NTRI(1,I)*COORDS(2,I)
          XJAC(2,1) = XJAC(2,1) + D_NTRI(2,I)*COORDS(1,I)
          XJAC(2,2) = XJAC(2,2) + D_NTRI(2,I)*COORDS(2,I)
        ENDDO

        DET = XJAC(1,1)*XJAC(2,2) - XJAC(1,2)*XJAC(2,1)
        IF (DET .LE. ZERO) DET = 1.0D-12
        INVJ(1,1) =  XJAC(2,2)/DET
        INVJ(1,2) = -XJAC(1,2)/DET
        INVJ(2,1) = -XJAC(2,1)/DET
        INVJ(2,2) =  XJAC(1,1)/DET

        DO I = 1, 3
          DNDX(1,I) = INVJ(1,1)*D_NTRI(1,I) + INVJ(1,2)*D_NTRI(2,I)
          DNDX(2,I) = INVJ(2,1)*D_NTRI(1,I) + INVJ(2,2)*D_NTRI(2,I)
        ENDDO

        CJAC = HALF * DET

        DO I = 1, 3
          B_TRI(1, 2*I-1) = DNDX(1,I)
          B_TRI(1, 2*I)   = ZERO
          B_TRI(2, 2*I-1) = ZERO
          B_TRI(2, 2*I)   = DNDX(2,I)
          B_TRI(3, 2*I-1) = DNDX(2,I)
          B_TRI(3, 2*I)   = DNDX(1,I)
        ENDDO

        STRAIN(1) = ZERO
        STRAIN(2) = ZERO
        STRAIN(3) = ZERO
        DO I = 1, 6
          STRAIN(1) = STRAIN(1) + B_TRI(1,I)*U(I)
          STRAIN(2) = STRAIN(2) + B_TRI(2,I)*U(I)
          STRAIN(3) = STRAIN(3) + B_TRI(3,I)*U(I)
        ENDDO

        EPS11 = STRAIN(1)
        EPS22 = STRAIN(2)
        EPS12 = HALF * STRAIN(3)

        D_VAL = SV_PHASE_TRIAL(PHYSIDX)
        IF (D_VAL .LT. ZERO) D_VAL = ZERO
        IF (D_VAL .GT. ONE)  D_VAL = ONE
        DEG   = (ONE - D_VAL)**2 + E_K

C       ----------------------------------------------------------------
C       2D Miehe Spectral Decomposition for Tri
C       ----------------------------------------------------------------
        TR_EPS = EPS11 + EPS22
        IF (TR_EPS .GT. ZERO) THEN
          TR_POS = TR_EPS
          TR_NEG = ZERO
          H_VOL_POS = ONE
          H_VOL_NEG = ZERO
        ELSE
          TR_POS = ZERO
          TR_NEG = TR_EPS
          H_VOL_POS = ZERO
          H_VOL_NEG = ONE
        ENDIF

        EPS_BAR = HALF * (EPS11 + EPS22)
        R_RAD   = SQRT(MAX((HALF*(EPS11 - EPS22))**2 + EPS12**2, ZERO))

        EPS1 = EPS_BAR + R_RAD
        EPS2 = EPS_BAR - R_RAD

        IF (EPS1 .GT. ZERO) THEN
          EPS1_POS  = EPS1
          EPS1_NEG  = ZERO
          H1_POS    = ONE
          H1_NEG    = ZERO
        ELSE
          EPS1_POS  = ZERO
          EPS1_NEG  = EPS1
          H1_POS    = ZERO
          H1_NEG    = ONE
        ENDIF

        IF (EPS2 .GT. ZERO) THEN
          EPS2_POS  = EPS2
          EPS2_NEG  = ZERO
          H2_POS    = ONE
          H2_NEG    = ZERO
        ELSE
          EPS2_POS  = ZERO
          EPS2_NEG  = EPS2
          H2_POS    = ZERO
          H2_NEG    = ONE
        ENDIF

        PSI_0_POS = HALF * E_LAM * (TR_POS**2) +
     1              E_MU * (EPS1_POS**2 + EPS2_POS**2)
        PSI_0_NEG = HALF * E_LAM * (TR_NEG**2) +
     1              E_MU * (EPS1_NEG**2 + EPS2_NEG**2)

        HIST = SV_H_TRIAL(PHYSIDX, 1)
        IF (PSI_0_POS .GT. HIST) THEN
          HIST = PSI_0_POS
          SV_H_TRIAL(PHYSIDX, 1) = PSI_0_POS
        ENDIF

        IF (R_RAD .GT. 1.0D-14) THEN
          COS2T = HALF * (EPS11 - EPS22) / R_RAD
          SIN2T = EPS12 / R_RAD
          THETA_POS = (EPS1_POS - EPS2_POS) / (TWO * R_RAD)
          THETA_NEG = (EPS1_NEG - EPS2_NEG) / (TWO * R_RAD)
        ELSE
          COS2T = ONE
          SIN2T = ZERO
          THETA_POS = HALF * (H1_POS + H2_POS)
          THETA_NEG = HALF * (H1_NEG + H2_NEG)
        ENDIF

        V1(1) = HALF * (ONE + COS2T)
        V1(2) = HALF * (ONE - COS2T)
        V1(3) = HALF * SIN2T

        V2(1) = HALF * (ONE - COS2T)
        V2(2) = HALF * (ONE + COS2T)
        V2(3) = -HALF * SIN2T

        V12(1) = -SIN2T
        V12(2) =  SIN2T
        V12(3) =  COS2T

        SIG_POS(1) = E_LAM*TR_POS + TWO*E_MU*(EPS1_POS*V1(1) + EPS2_POS*V2(1))
        SIG_POS(2) = E_LAM*TR_POS + TWO*E_MU*(EPS1_POS*V1(2) + EPS2_POS*V2(2))
        SIG_POS(3) = TWO*E_MU*(EPS1_POS*V1(3) + EPS2_POS*V2(3))

        SIG_NEG(1) = E_LAM*TR_NEG + TWO*E_MU*(EPS1_NEG*V1(1) + EPS2_NEG*V2(1))
        SIG_NEG(2) = E_LAM*TR_NEG + TWO*E_MU*(EPS1_NEG*V1(2) + EPS2_NEG*V2(2))
        SIG_NEG(3) = TWO*E_MU*(EPS1_NEG*V1(3) + EPS2_NEG*V2(3))

        STRESS(1) = DEG * SIG_POS(1) + SIG_NEG(1)
        STRESS(2) = DEG * SIG_POS(2) + SIG_NEG(2)
        STRESS(3) = DEG * SIG_POS(3) + SIG_NEG(3)

        DO I = 1, 3
          DO J = 1, 3
            D_POS(I,J) = ZERO
            D_NEG(I,J) = ZERO
          ENDDO
        ENDDO

        D_POS(1,1) = D_POS(1,1) + E_LAM * H_VOL_POS
        D_POS(1,2) = D_POS(1,2) + E_LAM * H_VOL_POS
        D_POS(2,1) = D_POS(2,1) + E_LAM * H_VOL_POS
        D_POS(2,2) = D_POS(2,2) + E_LAM * H_VOL_POS

        D_NEG(1,1) = D_NEG(1,1) + E_LAM * H_VOL_NEG
        D_NEG(1,2) = D_NEG(1,2) + E_LAM * H_VOL_NEG
        D_NEG(2,1) = D_NEG(2,1) + E_LAM * H_VOL_NEG
        D_NEG(2,2) = D_NEG(2,2) + E_LAM * H_VOL_NEG

        DO I = 1, 3
          DO J = 1, 3
            D_POS(I,J) = D_POS(I,J) + TWO * E_MU * (
     1        H1_POS * V1(I)*V1(J) + H2_POS * V2(I)*V2(J) +
     2        THETA_POS * HALF * V12(I)*V12(J))

            D_NEG(I,J) = D_NEG(I,J) + TWO * E_MU * (
     1        H1_NEG * V1(I)*V1(J) + H2_NEG * V2(I)*V2(J) +
     2        THETA_NEG * HALF * V12(I)*V12(J))
          ENDDO
        ENDDO

        DO I = 1, 3
          DO J = 1, 3
            D_MECH(I,J) = DEG * D_POS(I,J) + D_NEG(I,J)
          ENDDO
        ENDDO

        DO I = 1, 6
          DO J = 1, 3
            F_INT(I) = F_INT(I) + CJAC * B_TRI(J,I)*STRESS(J)
          ENDDO
          DO J = 1, 6
            DO K = 1, 3
              DO L = 1, 3
                AMATRX(I,J) = AMATRX(I,J) +
     1            CJAC * B_TRI(K,I)*D_MECH(K,L)*B_TRI(L,J)
              ENDDO
            ENDDO
          ENDDO
        ENDDO

        DO I = 1, 6
          RHS(I,1) = -F_INT(I)
        ENDDO

        PSI_E_PT = DEG * PSI_0_POS + PSI_0_NEG
        SV_PSI_E_TRIAL(PHYSIDX) = CJAC * PSI_E_PT

        SVARS(1)  = STRAIN(1)
        SVARS(4)  = STRESS(1)
        SVARS(9)  = D_VAL
        SVARS(10) = DEG
      ENDIF

      RETURN
      END

C ======================================================================
C SUBROUTINE UMAT: Companion Continuum Visualization Element
C ======================================================================
      SUBROUTINE UMAT(STRESS,STATEV,DDSDDE,SSE,SPD,SCD,
     1 RPL,DDSDDT,DRPLDE,DRPLDT,
     2 STRAN,DSTRAN,TIME,DTIME,TEMP,DTEMP,PREDEF,DPRED,CMNAME,
     3 NDI,NDSHR,NTENS,NSTATV,PROPS,NPROPS,COORDS,DROT,PNEWDT,
     4 CELENT,DFGRD0,DFGRD1,NOEL,NPT,KSLPT,KSTEP,KINC)

      INCLUDE 'ABA_PARAM.INC'

      CHARACTER*80 CMNAME
      DIMENSION STRESS(NTENS),STATEV(NSTATV),DDSDDE(NTENS,NTENS),
     1 STRAN(NTENS),DSTRAN(NTENS),TIME(2),PREDEF(1),DPRED(1),
     2 PROPS(NPROPS),COORDS(3),DROT(3,3),DFGRD0(3,3),DFGRD1(3,3)

      PARAMETER (MAX_ELEM = 200000)
      PARAMETER (ZERO = 0.0D0, ONE = 1.0D0, TWO = 2.0D0, HALF = 0.5D0)

      COMMON /CB_STATE_TRANS/ SV_PHASE_TRIAL(MAX_ELEM),
     1                        SV_H_TRIAL(MAX_ELEM, 4),
     2                        SV_PSI_E_TRIAL(MAX_ELEM)

      E_MOD = PROPS(1)
      E_NU  = PROPS(2)

      E_LAM = (E_MOD * E_NU) / ((ONE + E_NU) * (ONE - TWO * E_NU))
      E_MU  = E_MOD / (TWO * (ONE + E_NU))

      DO I = 1, NTENS
        DO J = 1, NTENS
          DDSDDE(I,J) = ZERO
        ENDDO
      ENDDO

      DDSDDE(1,1) = E_LAM + TWO * E_MU
      DDSDDE(2,2) = E_LAM + TWO * E_MU
      DDSDDE(3,3) = E_LAM + TWO * E_MU
      DDSDDE(1,2) = E_LAM
      DDSDDE(2,1) = E_LAM
      DDSDDE(1,3) = E_LAM
      DDSDDE(3,1) = E_LAM
      DDSDDE(2,3) = E_LAM
      DDSDDE(3,2) = E_LAM
      IF (NTENS .GE. 4) DDSDDE(4,4) = E_MU

      DO K1 = 1, NTENS
        DO K2 = 1, NTENS
          STRESS(K2) = STRESS(K2) + DDSDDE(K2, K1) * DSTRAN(K1)
        ENDDO
      ENDDO

      IF (NPROPS .GE. 3) THEN
        N_PHYS = INT(PROPS(3))
      ELSE
        N_PHYS = 22530
      ENDIF

      PHYSIDX = NOEL - 2 * N_PHYS
      IF (PHYSIDX .LE. 0) PHYSIDX = NOEL
      IF (PHYSIDX .LT. 1) PHYSIDX = 1
      IF (PHYSIDX .GT. MAX_ELEM) PHYSIDX = MAX_ELEM

      D_VAL = SV_PHASE_TRIAL(PHYSIDX)
      IF (D_VAL .LT. ZERO) D_VAL = ZERO
      IF (D_VAL .GT. ONE)  D_VAL = ONE

      HIST_VAL = SV_H_TRIAL(PHYSIDX, 1)
      IF (NPT .GE. 1 .AND. NPT .LE. 4) THEN
        HIST_VAL = SV_H_TRIAL(PHYSIDX, NPT)
      ENDIF

      PSI_E_VAL = SV_PSI_E_TRIAL(PHYSIDX)

      IF (NSTATV .GE. 1)  STATEV(1)  = D_VAL
      IF (NSTATV .GE. 14) STATEV(14) = D_VAL
      IF (NSTATV .GE. 15) STATEV(15) = HIST_VAL
      IF (NSTATV .GE. 16) STATEV(16) = PSI_E_VAL

      RETURN
      END
