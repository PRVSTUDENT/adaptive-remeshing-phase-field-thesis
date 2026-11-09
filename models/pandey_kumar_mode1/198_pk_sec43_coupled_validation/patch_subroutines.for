! ==============================================================================
! minimal_patch_subroutines.for
! Implements UEL and UMAT for single-element patch testing under F1698
! ==============================================================================

      MODULE PATCH_GLOBAL_STATE
        IMPLICIT NONE
        DOUBLE PRECISION :: PRESCRIBED_D = 0.0D0
        INTEGER :: UMAT_MODE = 1  ! 1=B1(Zero), 2=B2(StressOnly), 3=B3(FullTangent)
      END MODULE PATCH_GLOBAL_STATE

! ------------------------------------------------------------------------------
! UEL Subroutine: 4-node plane strain displacement element
! ------------------------------------------------------------------------------
      SUBROUTINE UEL(RHS,AMATRX,SVARS,ENERGY,NDOFEL,NRHS,NSVARS,
     1 PROPS,NPROPS,COORDS,MCRD,NNODE,U,DU,V,A,JTYPE,TIME,DTIME,
     2 KSTEP,KINC,JELEM,PARAMS,NDLOAD,JDLOD,MDLOAD,PNEWDT,JPROPS,
     3 NJPROP,PERIOD)
      USE PATCH_GLOBAL_STATE
      INCLUDE 'ABA_PARAM.INC'

      DIMENSION RHS(MLVARX,*),AMATRX(NDOFEL,NDOFEL),PROPS(*),
     1 SVARS(*),ENERGY(8),COORDS(MCRD,NNODE),U(NDOFEL),DU(MLVARX,*),
     2 V(NDOFEL),A(NDOFEL),TIME(2),PARAMS(*),JDLOD(MDLOAD,*),
     3 PNEWDT(1),JPROPS(*)

      DOUBLE PRECISION :: E_MOD, NU_VAL, G_D, C11, C12, C33
      DOUBLE PRECISION :: GAUSS_XI(4), GAUSS_ETA(4), GAUSS_WT(4)
      DOUBLE PRECISION :: XI, ETA, WT, DETJ, SHP(3,4), DN(2,4)
      DOUBLE PRECISION :: BMAT(3,8), DB(3,8), STRAN(3), STRESS(3)
      DOUBLE PRECISION :: JAC(2,2), INVJ(2,2), D_VAL
      INTEGER :: I, J, K, L, NINT, INOD

      ! Extract material properties
      ! PROPS: 1=l0, 2=Gc, 3=E, 4=nu, 5=k, 6=prescribed_d
      E_MOD  = PROPS(3)
      NU_VAL = PROPS(4)
      IF (NPROPS .GE. 6) THEN
        D_VAL = PROPS(6)
      ELSE
        D_VAL = PRESCRIBED_D
      ENDIF

      ! Degradation function
      G_D = (1.D0 - D_VAL)**2 + 1.D-7

      ! Plane strain elasticity coefficients
      C11 = G_D * E_MOD * (1.D0 - NU_VAL) / ((1.D0 + NU_VAL) * (1.D0 - 2.D0 * NU_VAL))
      C12 = G_D * E_MOD * NU_VAL / ((1.D0 + NU_VAL) * (1.D0 - 2.D0 * NU_VAL))
      C33 = G_D * E_MOD / (2.D0 * (1.D0 + NU_VAL))

      ! Initialize
      DO I = 1, NDOFEL
        RHS(I,1) = 0.D0
        DO J = 1, NDOFEL
          AMATRX(I,J) = 0.D0
        ENDDO
      ENDDO

      ! 2x2 Gauss integration points
      GAUSS_XI(1)  = -0.577350269189626D0
      GAUSS_ETA(1) = -0.577350269189626D0
      GAUSS_XI(2)  =  0.577350269189626D0
      GAUSS_ETA(2) = -0.577350269189626D0
      GAUSS_XI(3)  =  0.577350269189626D0
      GAUSS_ETA(3) =  0.577350269189626D0
      GAUSS_XI(4)  = -0.577350269189626D0
      GAUSS_ETA(4) =  0.577350269189626D0
      DO I = 1, 4
        GAUSS_WT(I) = 1.D0
      ENDDO

      DO NINT = 1, 4
        XI  = GAUSS_XI(NINT)
        ETA = GAUSS_ETA(NINT)
        WT  = GAUSS_WT(NINT)

        ! Shape function derivatives wrt natural coordinates
        DN(1,1) = -0.25D0 * (1.D0 - ETA)
        DN(1,2) =  0.25D0 * (1.D0 - ETA)
        DN(1,3) =  0.25D0 * (1.D0 + ETA)
        DN(1,4) = -0.25D0 * (1.D0 + ETA)

        DN(2,1) = -0.25D0 * (1.D0 - XI)
        DN(2,2) = -0.25D0 * (1.D0 + XI)
        DN(2,3) =  0.25D0 * (1.D0 + XI)
        DN(2,4) =  0.25D0 * (1.D0 - XI)

        ! Jacobian
        JAC(1,1) = 0.D0; JAC(1,2) = 0.D0
        JAC(2,1) = 0.D0; JAC(2,2) = 0.D0
        DO INOD = 1, 4
          JAC(1,1) = JAC(1,1) + DN(1,INOD) * COORDS(1,INOD)
          JAC(1,2) = JAC(1,2) + DN(1,INOD) * COORDS(2,INOD)
          JAC(2,1) = JAC(2,1) + DN(2,INOD) * COORDS(1,INOD)
          JAC(2,2) = JAC(2,2) + DN(2,INOD) * COORDS(2,INOD)
        ENDDO

        DETJ = JAC(1,1)*JAC(2,2) - JAC(1,2)*JAC(2,1)
        INVJ(1,1) =  JAC(2,2) / DETJ
        INVJ(1,2) = -JAC(1,2) / DETJ
        INVJ(2,1) = -JAC(2,1) / DETJ
        INVJ(2,2) =  JAC(1,1) / DETJ

        ! Shape function derivatives wrt physical coordinates
        DO INOD = 1, 4
          SHP(1,INOD) = INVJ(1,1)*DN(1,INOD) + INVJ(1,2)*DN(2,INOD)
          SHP(2,INOD) = INVJ(2,1)*DN(1,INOD) + INVJ(2,2)*DN(2,INOD)
        ENDDO

        ! B-matrix (3 x 8)
        DO J = 1, 8
          DO I = 1, 3
            BMAT(I,J) = 0.D0
          ENDDO
        ENDDO
        DO INOD = 1, 4
          BMAT(1, 2*INOD-1) = SHP(1,INOD)
          BMAT(2, 2*INOD)   = SHP(2,INOD)
          BMAT(3, 2*INOD-1) = SHP(2,INOD)
          BMAT(3, 2*INOD)   = SHP(1,INOD)
        ENDDO

        ! Strains: STRAN = B * U
        STRAN(1) = 0.D0; STRAN(2) = 0.D0; STRAN(3) = 0.D0
        DO J = 1, 8
          STRAN(1) = STRAN(1) + BMAT(1,J) * U(J)
          STRAN(2) = STRAN(2) + BMAT(2,J) * U(J)
          STRAN(3) = STRAN(3) + BMAT(3,J) * U(J)
        ENDDO

        ! Degraded Stresses: STRESS = C * STRAN
        STRESS(1) = C11 * STRAN(1) + C12 * STRAN(2)
        STRESS(2) = C12 * STRAN(1) + C11 * STRAN(2)
        STRESS(3) = C33 * STRAN(3)

        ! Internal force: F_int = B^T * STRESS * dOmega
        DO J = 1, 8
          RHS(J,1) = RHS(J,1) - (BMAT(1,J)*STRESS(1) + BMAT(2,J)*STRESS(2) + BMAT(3,J)*STRESS(3)) * DETJ * WT
        ENDDO

        ! Tangent stiffness: K = B^T * C * B * dOmega
        DO J = 1, 8
          DB(1,J) = C11 * BMAT(1,J) + C12 * BMAT(2,J)
          DB(2,J) = C12 * BMAT(1,J) + C11 * BMAT(2,J)
          DB(3,J) = C33 * BMAT(3,J)
        ENDDO

        DO I = 1, 8
          DO J = 1, 8
            AMATRX(I,J) = AMATRX(I,J) + (BMAT(1,I)*DB(1,J) + BMAT(2,I)*DB(2,J) + BMAT(3,I)*DB(3,J)) * DETJ * WT
          ENDDO
        ENDDO

      ENDDO ! Gauss points

      ! Save state to SVARS for reference
      SVARS(1) = D_VAL
      SVARS(2) = STRESS(1)
      SVARS(3) = STRESS(2)
      SVARS(4) = STRESS(3)

      RETURN
      END SUBROUTINE UEL

! ------------------------------------------------------------------------------
! UMAT Subroutine for Companion Element Layer
! PROPS: 1=E, 2=nu, 3=d, 4=mode (1=B1 Zero, 2=B2 StressOnly, 3=B3 FullTangent)
! ------------------------------------------------------------------------------
      SUBROUTINE UMAT(STRESS,STATEV,DDSDDE,SSE,SPD,SCD,
     1 RPL,DDSDDT,DRPLDE,DRPLDT,
     2 STRAN,DSTRAN,TIME,DTIME,TEMP,DTEMP,PREDEF,DPRED,CMNAME,
     3 NDI,NDS,NTENS,NSTATV,PROPS,NPROPS,COORDS,DROT,PNEWDT,
     4 CELENT,DFGRD0,DFGRD1,NOEL,NPT,KSLAY,KSPT,KSTEP,KINC)
      USE PATCH_GLOBAL_STATE
      INCLUDE 'ABA_PARAM.INC'

      CHARACTER*80 CMNAME
      DIMENSION STRESS(NTENS),STATEV(NSTATV),
     1 DDSDDE(NTENS,NTENS),DDSDDT(NTENS),DRPLDE(NTENS),
     2 STRAN(NTENS),DSTRAN(NTENS),TIME(2),PREDEF(1),DPRED(1),
     3 PROPS(NPROPS),COORDS(3),DROT(3,3),DFGRD0(3,3),DFGRD1(3,3)

      DOUBLE PRECISION :: E_MOD, NU_VAL, D_VAL, G_D, C11, C12, C33
      INTEGER :: I, J, MODE

      E_MOD  = PROPS(1)
      NU_VAL = PROPS(2)
      D_VAL  = PROPS(3)
      MODE   = INT(PROPS(4))

      G_D = (1.D0 - D_VAL)**2 + 1.D-7

      ! Authentic degraded plane strain elasticity
      C11 = G_D * E_MOD * (1.D0 - NU_VAL) / ((1.D0 + NU_VAL) * (1.D0 - 2.D0 * NU_VAL))
      C12 = G_D * E_MOD * NU_VAL / ((1.D0 + NU_VAL) * (1.D0 - 2.D0 * NU_VAL))
      C33 = G_D * E_MOD / (2.D0 * (1.D0 + NU_VAL))

      ! Initialize tangent matrix
      DO I = 1, NTENS
        DO J = 1, NTENS
          DDSDDE(I,J) = 0.D0
        ENDDO
      ENDDO

      IF (MODE .EQ. 1) THEN
        ! Subcase B1: STRESS = 0, DDSDDE = 1e-11 (Existing repository implementation)
        DO I = 1, NTENS
          STRESS(I) = 0.D0
          DDSDDE(I,I) = 1.D-11
        ENDDO

      ELSE IF (MODE .EQ. 2) THEN
        ! Subcase B2: STRESS = sigma_d, DDSDDE = 1e-11 (Attempted stress-only feedback)
        STRESS(1) = C11 * (STRAN(1) + DSTRAN(1)) + C12 * (STRAN(2) + DSTRAN(2))
        STRESS(2) = C12 * (STRAN(1) + DSTRAN(1)) + C11 * (STRAN(2) + DSTRAN(2))
        STRESS(3) = 0.D0
        STRESS(4) = C33 * (STRAN(4) + DSTRAN(4))
        DO I = 1, NTENS
          DDSDDE(I,I) = 1.D-11
        ENDDO

      ELSE IF (MODE .EQ. 3) THEN
        ! Subcase B3: STRESS = sigma_d, DDSDDE = C_d (Attempted full stiffness feedback)
        STRESS(1) = C11 * (STRAN(1) + DSTRAN(1)) + C12 * (STRAN(2) + DSTRAN(2))
        STRESS(2) = C12 * (STRAN(1) + DSTRAN(1)) + C11 * (STRAN(2) + DSTRAN(2))
        STRESS(3) = 0.D0
        STRESS(4) = C33 * (STRAN(4) + DSTRAN(4))

        DDSDDE(1,1) = C11
        DDSDDE(1,2) = C12
        DDSDDE(2,1) = C12
        DDSDDE(2,2) = C11
        DDSDDE(4,4) = C33
      ENDIF

      ! State variables for output
      STATEV(1) = D_VAL
      STATEV(2) = G_D

      RETURN
      END SUBROUTINE UMAT
