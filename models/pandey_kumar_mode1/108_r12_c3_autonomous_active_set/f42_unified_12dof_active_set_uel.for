C ======================================================================
C User Subroutines UEL, UMAT & UEXTERNALDB for Abaqus/Standard
C Candidate Package 108 Revision 11 (R11): Unified 12-DOF Coupled UEL
C Formulation: Monolithic Unsymmetric 4-Node Quadrilateral Coupled UEL
C DOFs per node: 1:ux, 2:uy, 3:d (Total NDOFEL = 12)
C Constitutive Model: Ambati / Pandey-Kumar Mode-I Phase-Field
C Active-Set Inequality Enforcement: Oracle-Constrained Active Set
C ======================================================================

      SUBROUTINE UEXTERNALDB(LOP,LRESTART,TIME,DTIME,KSTEP,KINC)
      INCLUDE 'ABA_PARAM.INC'
      PARAMETER(N_CAPACITY=150000)

      DOUBLE PRECISION SV_H_COMMITTED(N_CAPACITY,4)
      DOUBLE PRECISION SV_H_TRIAL(N_CAPACITY,4)
      DOUBLE PRECISION SV_D_LOWER(N_CAPACITY,4)
      DOUBLE PRECISION SV_E_FRAC(N_CAPACITY)
      DOUBLE PRECISION SV_E_ELAS(N_CAPACITY)

      COMMON /CB_COUPLED_STATE/ SV_H_COMMITTED, SV_H_TRIAL,
     1                          SV_D_LOWER, SV_E_FRAC, SV_E_ELAS

      INTEGER LOP, LRESTART, KSTEP, KINC, EID, KPT
      DOUBLE PRECISION TIME(2), DTIME
      LOGICAL OP_EXISTS
      CHARACTER*512 OUTDIR_STR, CSV_FULL_PATH
      INTEGER L_OUTDIR
      INTEGER EID_IN
      DOUBLE PRECISION D0_1, D0_2, D0_3, D0_4
      DOUBLE PRECISION H0_1, H0_2, H0_3, H0_4
      CHARACTER*256 HEADER_LINE

C --- LOP = 0: Analysis Start -> Initialize State from CSV ---
      IF (LOP .EQ. 0) THEN
        DO EID=1, N_CAPACITY
          SV_E_FRAC(EID) = 0.0D0
          SV_E_ELAS(EID) = 0.0D0
          DO KPT=1, 4
            SV_H_COMMITTED(EID, KPT) = 0.0D0
            SV_H_TRIAL(EID, KPT)     = 0.0D0
            SV_D_LOWER(EID, KPT)     = 0.0D0
          ENDDO
        ENDDO

        INQUIRE(FILE='d_lower_bounds.csv', EXIST=OP_EXISTS)
        IF (.NOT. OP_EXISTS) THEN
          CALL GETOUTDIR(OUTDIR_STR, L_OUTDIR)
          CSV_FULL_PATH = OUTDIR_STR(1:L_OUTDIR) // '/d_lower_bounds.csv'
          INQUIRE(FILE=TRIM(CSV_FULL_PATH), EXIST=OP_EXISTS)
        ELSE
          CSV_FULL_PATH = 'd_lower_bounds.csv'
        ENDIF

        IF (OP_EXISTS) THEN
          OPEN(UNIT=108, FILE=TRIM(CSV_FULL_PATH), STATUS='OLD',
     1         ACTION='READ')
          READ(108, '(A)', END=100) HEADER_LINE
 10       READ(108, *, END=100) EID_IN, D0_1, D0_2, D0_3, D0_4,
     1                          H0_1, H0_2, H0_3, H0_4
          IF (EID_IN .GE. 1 .AND. EID_IN .LE. N_CAPACITY) THEN
            SV_D_LOWER(EID_IN, 1) = D0_1
            SV_D_LOWER(EID_IN, 2) = D0_2
            SV_D_LOWER(EID_IN, 3) = D0_3
            SV_D_LOWER(EID_IN, 4) = D0_4
            SV_H_COMMITTED(EID_IN, 1) = H0_1
            SV_H_COMMITTED(EID_IN, 2) = H0_2
            SV_H_COMMITTED(EID_IN, 3) = H0_3
            SV_H_COMMITTED(EID_IN, 4) = H0_4
            SV_H_TRIAL(EID_IN, 1)     = H0_1
            SV_H_TRIAL(EID_IN, 2)     = H0_2
            SV_H_TRIAL(EID_IN, 3)     = H0_3
            SV_H_TRIAL(EID_IN, 4)     = H0_4
          ENDIF
          GOTO 10
 100      CLOSE(108)
          WRITE(7,*) 'UEXTERNALDB: Loaded d_lower_bounds.csv successfully'
        ELSE
          WRITE(7,*) 'WARNING: d_lower_bounds.csv not found in UEXTERNALDB'
        ENDIF

C --- LOP = 2: Increment Converged -> Commit Trial History ---
      ELSE IF (LOP .EQ. 2) THEN
        DO EID=1, N_CAPACITY
          DO KPT=1, 4
            SV_H_COMMITTED(EID, KPT) = SV_H_TRIAL(EID, KPT)
          ENDDO
        ENDDO
      ENDIF

      RETURN
      END

C ======================================================================
C SUBROUTINE UEL: Unified 12-DOF Coupled Quadrilateral User Element
C ======================================================================
      SUBROUTINE UEL(RHS,AMATRX,SVARS,ENERGY,NDOFEL,NRHS,NSVARS,
     1               PROPS,NPROPS,COORDS,MCRD,NNODE,U,DU,V,A,JTYPE,
     2               TIME,DTIME,KSTEP,KINC,JELEM,PARAMS,NDLOAD,JDLTYP,
     3               ADLMAG,PREDEF,NPREDF,LFLAGS,MLVARX,DDLMAG,MDLOAD,
     4               PNEWDT,JPROPS,NJPROP,PERIOD)
      INCLUDE 'ABA_PARAM.INC'
      PARAMETER(N_CAPACITY=150000)

      DOUBLE PRECISION RHS(MLVARX,*), AMATRX(NDOFEL,NDOFEL)
      DOUBLE PRECISION SVARS(*), ENERGY(8), PROPS(*), COORDS(MCRD,NNODE)
      DOUBLE PRECISION U(NDOFEL), DU(MLVARX,*), V(NDOFEL), A(NDOFEL)
      DOUBLE PRECISION TIME(2), DTIME, PARAMS(*), ADLMAG(MDLOAD,*)
      DOUBLE PRECISION DDLMAG(MDLOAD,*), PREDEF(2,NPREDF,NNODE)
      INTEGER LFLAGS(*), JDLTYP(MDLOAD,*), JPROPS(*)
      INTEGER NDOFEL, NRHS, NSVARS, NPROPS, MCRD, NNODE, JTYPE
      INTEGER KSTEP, KINC, JELEM, NDLOAD, NPREDF, MLVARX, MDLOAD
      INTEGER NJPROP

      DOUBLE PRECISION SV_H_COMMITTED(N_CAPACITY,4)
      DOUBLE PRECISION SV_H_TRIAL(N_CAPACITY,4)
      DOUBLE PRECISION SV_D_LOWER(N_CAPACITY,4)
      DOUBLE PRECISION SV_E_FRAC(N_CAPACITY)
      DOUBLE PRECISION SV_E_ELAS(N_CAPACITY)

      COMMON /CB_COUPLED_STATE/ SV_H_COMMITTED, SV_H_TRIAL,
     1                          SV_D_LOWER, SV_E_FRAC, SV_E_ELAS

      DOUBLE PRECISION E_L0, E_GC, E_MOD, E_NU, E_K
      DOUBLE PRECISION C0(3,3), LAMBDA, MU
      DOUBLE PRECISION XG(4), YG(4), WG(4)
      DOUBLE PRECISION XI, ETA, WT, DETJ, CJ
      DOUBLE PRECISION NV(4), DNDXI(4), DNDETA(4)
      DOUBLE PRECISION JAC(2,2), INVJ(2,2), DN(2,4)
      DOUBLE PRECISION UE(8), DE(4), D_AVG, DEG, G_PRIME
      DOUBLE PRECISION BU(3,8), BD(2,4)
      DOUBLE PRECISION EPS(3), TR_E, E_POS, POS_M, S_POS(3)
      DOUBLE PRECISION SIG(3), H_BASE, H_TRIAL_VAL
      DOUBLE PRECISION RU(8), RD(4)
      DOUBLE PRECISION KUU(8,8), KUD(8,4), KDU(4,8), KDD(4,4)
      DOUBLE PRECISION K0_ELEM(8,8)
      DOUBLE PRECISION E_ELAS_ELEM, E_FRAC_ELEM, D_VAL, GRAD_D(2)
      INTEGER A_NODE, B_NODE, I, J, K, KPT, PHYSIDX

      IF (LFLAGS(3) .EQ. 4) THEN
        RETURN
      ENDIF

C Zero matrices
      DO I=1, NDOFEL
        DO J=1, NRHS
          RHS(I, J) = 0.0D0
        ENDDO
        DO J=1, NDOFEL
          AMATRX(I, J) = 0.0D0
        ENDDO
      ENDDO

      DO I=1, 8
        RU(I) = 0.0D0
        DO J=1, 8
          KUU(I, J) = 0.0D0
          K0_ELEM(I, J) = 0.0D0
        ENDDO
        DO J=1, 4
          KUD(I, J) = 0.0D0
        ENDDO
      ENDDO

      DO I=1, 4
        RD(I) = 0.0D0
        DO J=1, 4
          KDD(I, J) = 0.0D0
        ENDDO
        DO J=1, 8
          KDU(I, J) = 0.0D0
        ENDDO
      ENDDO

C Properties
      E_L0  = PROPS(1)
      E_GC  = PROPS(2)
      E_MOD = PROPS(3)
      E_NU  = PROPS(4)
      E_K   = PROPS(5)

      LAMBDA = (E_MOD * E_NU) / ((1.0D0 + E_NU) * (1.0D0 - 2.0D0 * E_NU))
      MU     = E_MOD / (2.0D0 * (1.0D0 + E_NU))

      C0(1,1) = LAMBDA + 2.0D0 * MU
      C0(1,2) = LAMBDA
      C0(1,3) = 0.0D0
      C0(2,1) = LAMBDA
      C0(2,2) = LAMBDA + 2.0D0 * MU
      C0(2,3) = 0.0D0
      C0(3,1) = 0.0D0
      C0(3,2) = 0.0D0
      C0(3,3) = MU

C Extract displacements and phase fields
      DO A_NODE=1, 4
        UE(2*A_NODE-1) = U(3*(A_NODE-1)+1)
        UE(2*A_NODE)   = U(3*(A_NODE-1)+2)
        DE(A_NODE)     = U(3*(A_NODE-1)+3)
      ENDDO

      D_AVG = 0.25D0 * (DE(1) + DE(2) + DE(3) + DE(4))
      DEG = (1.0D0 - D_AVG)**2 + E_K
      G_PRIME = -2.0D0 * (1.0D0 - D_AVG)

C Gauss points (2x2)
      XG(1) = -0.577350269189626D0
      YG(1) = -0.577350269189626D0
      WG(1) =  1.0D0
      XG(2) =  0.577350269189626D0
      YG(2) = -0.577350269189626D0
      WG(2) =  1.0D0
      XG(3) =  0.577350269189626D0
      YG(3) =  0.577350269189626D0
      WG(3) =  1.0D0
      XG(4) = -0.577350269189626D0
      YG(4) =  0.577350269189626D0
      WG(4) =  1.0D0

      PHYSIDX = JELEM
      E_FRAC_ELEM = 0.0D0

      DO KPT=1, 4
        XI = XG(KPT)
        ETA = YG(KPT)
        WT = WG(KPT)

        NV(1) = 0.25D0 * (1.0D0 - XI) * (1.0D0 - ETA)
        NV(2) = 0.25D0 * (1.0D0 + XI) * (1.0D0 - ETA)
        NV(3) = 0.25D0 * (1.0D0 + XI) * (1.0D0 + ETA)
        NV(4) = 0.25D0 * (1.0D0 - XI) * (1.0D0 + ETA)

        DNDXI(1) = -0.25D0 * (1.0D0 - ETA)
        DNDXI(2) =  0.25D0 * (1.0D0 - ETA)
        DNDXI(3) =  0.25D0 * (1.0D0 + ETA)
        DNDXI(4) = -0.25D0 * (1.0D0 + ETA)

        DNDETA(1) = -0.25D0 * (1.0D0 - XI)
        DNDETA(2) = -0.25D0 * (1.0D0 + XI)
        DNDETA(3) =  0.25D0 * (1.0D0 + XI)
        DNDETA(4) =  0.25D0 * (1.0D0 - XI)

        JAC(1,1) = 0.0D0
        JAC(1,2) = 0.0D0
        JAC(2,1) = 0.0D0
        JAC(2,2) = 0.0D0
        DO A_NODE=1, 4
          JAC(1,1) = JAC(1,1) + DNDXI(A_NODE)  * COORDS(1, A_NODE)
          JAC(1,2) = JAC(1,2) + DNDXI(A_NODE)  * COORDS(2, A_NODE)
          JAC(2,1) = JAC(2,1) + DNDETA(A_NODE) * COORDS(1, A_NODE)
          JAC(2,2) = JAC(2,2) + DNDETA(A_NODE) * COORDS(2, A_NODE)
        ENDDO

        DETJ = JAC(1,1)*JAC(2,2) - JAC(1,2)*JAC(2,1)
        IF (DETJ .LE. 0.0D0) THEN
          WRITE(7,*) 'ERROR: Non-positive Jacobian in UEL:', JELEM, DETJ
          CALL XIT
        ENDIF

        INVJ(1,1) =  JAC(2,2) / DETJ
        INVJ(1,2) = -JAC(1,2) / DETJ
        INVJ(2,1) = -JAC(2,1) / DETJ
        INVJ(2,2) =  JAC(1,1) / DETJ

        DO A_NODE=1, 4
          DN(1, A_NODE) = INVJ(1,1)*DNDXI(A_NODE) + INVJ(1,2)*DNDETA(A_NODE)
          DN(2, A_NODE) = INVJ(2,1)*DNDXI(A_NODE) + INVJ(2,2)*DNDETA(A_NODE)
        ENDDO

        CJ = DETJ * WT

C Strain B-matrix (3x8)
        DO A_NODE=1, 4
          BU(1, 2*A_NODE-1) = DN(1, A_NODE)
          BU(1, 2*A_NODE)   = 0.0D0
          BU(2, 2*A_NODE-1) = 0.0D0
          BU(2, 2*A_NODE)   = DN(2, A_NODE)
          BU(3, 2*A_NODE-1) = DN(2, A_NODE)
          BU(3, 2*A_NODE)   = DN(1, A_NODE)
        ENDDO

C Mechanical strain
        DO I=1, 3
          EPS(I) = 0.0D0
          DO J=1, 8
            EPS(I) = EPS(I) + BU(I, J) * UE(J)
          ENDDO
        ENDDO

C Positive strain energy psi+
        TR_E = EPS(1) + EPS(2)
        E_POS = MAX(0.0D0, TR_E)
        POS_M = 0.5D0 * LAMBDA * (E_POS**2) +
     1          MU * (EPS(1)**2 + EPS(2)**2 + 0.5D0 * (EPS(3)**2))

        IF (TR_E .GT. 0.0D0) THEN
          S_POS(1) = LAMBDA * TR_E + 2.0D0 * MU * EPS(1)
          S_POS(2) = LAMBDA * TR_E + 2.0D0 * MU * EPS(2)
          S_POS(3) = MU * EPS(3)
        ELSE
          S_POS(1) = 2.0D0 * MU * EPS(1)
          S_POS(2) = 2.0D0 * MU * EPS(2)
          S_POS(3) = MU * EPS(3)
        ENDIF

C History update
        IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) THEN
          H_BASE = SV_H_COMMITTED(PHYSIDX, KPT)
        ELSE
          H_BASE = 0.0D0
        ENDIF
        H_TRIAL_VAL = MAX(H_BASE, POS_M)
        IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) THEN
          SV_H_TRIAL(PHYSIDX, KPT) = H_TRIAL_VAL
        ENDIF

C Degraded mechanical stress
        DO I=1, 3
          SIG(I) = 0.0D0
          DO J=1, 3
            SIG(I) = SIG(I) + DEG * C0(I, J) * EPS(J)
          ENDDO
        ENDDO

C Mechanical residual and Kuu
        DO I=1, 8
          DO J=1, 3
            RU(I) = RU(I) + CJ * BU(J, I) * SIG(J)
          ENDDO
          DO J=1, 8
            DO K=1, 3
              DO A_NODE=1, 3
                KUU(I, J) = KUU(I, J) + CJ * BU(K, I) * (DEG * C0(K, A_NODE)) * BU(A_NODE, J)
                K0_ELEM(I, J) = K0_ELEM(I, J) + CJ * BU(K, I) * C0(K, A_NODE) * BU(A_NODE, J)
              ENDDO
            ENDDO
          ENDDO
        ENDDO

C Phase field at Gauss point
        D_VAL = 0.0D0
        GRAD_D(1) = 0.0D0
        GRAD_D(2) = 0.0D0
        DO A_NODE=1, 4
          D_VAL = D_VAL + NV(A_NODE) * DE(A_NODE)
          GRAD_D(1) = GRAD_D(1) + DN(1, A_NODE) * DE(A_NODE)
          GRAD_D(2) = GRAD_D(2) + DN(2, A_NODE) * DE(A_NODE)
        ENDDO

C Phase residual Rd and Kdd
        DO A_NODE=1, 4
          RD(A_NODE) = RD(A_NODE) + CJ * (
     1      ( (E_GC / E_L0) * D_VAL + 2.0D0 * (1.0D0 - D_VAL) * H_TRIAL_VAL ) * NV(A_NODE) +
     2      E_GC * E_L0 * (DN(1, A_NODE)*GRAD_D(1) + DN(2, A_NODE)*GRAD_D(2)) )

          DO B_NODE=1, 4
            KDD(A_NODE, B_NODE) = KDD(A_NODE, B_NODE) + CJ * (
     1        ( (E_GC / E_L0) - 2.0D0 * H_TRIAL_VAL ) * NV(A_NODE) * NV(B_NODE) +
     2        E_GC * E_L0 * (DN(1, A_NODE)*DN(1, B_NODE) + DN(2, A_NODE)*DN(2, B_NODE)) )
          ENDDO
        ENDDO

C Phase-displacement cross-coupling Kdu (active only when psi+ > H_base)
        IF (POS_M .GT. H_BASE) THEN
          DO A_NODE=1, 4
            DO J=1, 8
              DO K=1, 3
                KDU(A_NODE, J) = KDU(A_NODE, J) -
     1            CJ * 2.0D0 * (1.0D0 - D_VAL) * NV(A_NODE) * S_POS(K) * BU(K, J)
              ENDDO
            ENDDO
          ENDDO
        ENDIF

C Element fracture energy
        E_FRAC_ELEM = E_FRAC_ELEM + CJ * (
     1    (E_GC / (2.0D0 * E_L0)) * (D_VAL**2) +
     2    0.5D0 * E_GC * E_L0 * (GRAD_D(1)**2 + GRAD_D(2)**2) )

      ENDDO

C Displacement-phase cross-coupling Kud = (g'/4) * K0 * ue
      DO I=1, 8
        DO B_NODE=1, 4
          DO J=1, 8
            KUD(I, B_NODE) = KUD(I, B_NODE) + 0.25D0 * G_PRIME * K0_ELEM(I, J) * UE(J)
          ENDDO
        ENDDO
      ENDDO

C Elastic strain energy
      E_ELAS_ELEM = 0.0D0
      DO I=1, 8
        DO J=1, 8
          E_ELAS_ELEM = E_ELAS_ELEM + 0.5D0 * UE(I) * KUU(I, J) * UE(J)
        ENDDO
      ENDDO

C Interleave into 12-vector RHS and 12x12 AMATRX
C Abaqus convention: RHS = - Residual
      DO A_NODE=1, 4
        RHS(3*(A_NODE-1)+1, 1) = - RU(2*A_NODE-1)
        RHS(3*(A_NODE-1)+2, 1) = - RU(2*A_NODE)
        RHS(3*(A_NODE-1)+3, 1) = - RD(A_NODE)
      ENDDO

      DO A_NODE=1, 4
        DO B_NODE=1, 4
C Kuu block (2x2)
          AMATRX(3*(A_NODE-1)+1, 3*(B_NODE-1)+1) = KUU(2*A_NODE-1, 2*B_NODE-1)
          AMATRX(3*(A_NODE-1)+1, 3*(B_NODE-1)+2) = KUU(2*A_NODE-1, 2*B_NODE)
          AMATRX(3*(A_NODE-1)+2, 3*(B_NODE-1)+1) = KUU(2*A_NODE,   2*B_NODE-1)
          AMATRX(3*(A_NODE-1)+2, 3*(B_NODE-1)+2) = KUU(2*A_NODE,   2*B_NODE)

C Kud block (2x1)
          AMATRX(3*(A_NODE-1)+1, 3*(B_NODE-1)+3) = KUD(2*A_NODE-1, B_NODE)
          AMATRX(3*(A_NODE-1)+2, 3*(B_NODE-1)+3) = KUD(2*A_NODE,   B_NODE)

C Kdu block (1x2)
          AMATRX(3*(A_NODE-1)+3, 3*(B_NODE-1)+1) = KDU(A_NODE,     2*B_NODE-1)
          AMATRX(3*(A_NODE-1)+3, 3*(B_NODE-1)+2) = KDU(A_NODE,     2*B_NODE)

C Kdd block (1x1)
          AMATRX(3*(A_NODE-1)+3, 3*(B_NODE-1)+3) = KDD(A_NODE,     B_NODE)
        ENDDO
      ENDDO

C Energy outputs for Abaqus accounting
      ENERGY(2) = E_ELAS_ELEM
      ENERGY(7) = E_FRAC_ELEM

      IF (PHYSIDX .GE. 1 .AND. PHYSIDX .LE. N_CAPACITY) THEN
        SV_E_ELAS(PHYSIDX) = E_ELAS_ELEM
        SV_E_FRAC(PHYSIDX) = E_FRAC_ELEM
      ENDIF

C State variables
      IF (NSVARS .GE. 8) THEN
        DO KPT=1, 4
          SVARS(KPT) = SV_H_TRIAL(PHYSIDX, KPT)
        ENDDO
        SVARS(5) = E_ELAS_ELEM
        SVARS(6) = E_FRAC_ELEM
        SVARS(7) = D_AVG
        SVARS(8) = DEG
      ENDIF

      RETURN
      END

C ======================================================================
C SUBROUTINE UMAT: Visualizer Material for Companion Mesh
C ======================================================================
      SUBROUTINE UMAT(STRESS,STATEV,DDSDDE,SSE,SPD,SCD,
     1                RPL,DDSDDT,DRPLDE,DRPLDT,
     2                STRAN,DSTRAN,TIME,DTIME,TEMP,DTEMP,PREDEF,DPRED,
     3                CMNAME,NDI,NSHR,NTENS,NSTATV,PROPS,NPROPS,
     4                COORDS,DROT,PNEWDT,CELENT,DFGRD0,DFGRD1,
     5                NOEL,NPT,KSLPT,KSTEP,KINC)
      INCLUDE 'ABA_PARAM.INC'
      CHARACTER*80 CMNAME
      DOUBLE PRECISION STRESS(NTENS), STATEV(NSTATV), DDSDDE(NTENS,NTENS)
      DOUBLE PRECISION STRAN(NTENS), DSTRAN(NTENS), PROPS(NPROPS)
      DOUBLE PRECISION COORDS(3), TIME(2), DTIME
      INTEGER NDI, NSHR, NTENS, NSTATV, NPROPS, NOEL, NPT, KSLPT, KSTEP, KINC

      DOUBLE PRECISION E_MOD, E_NU, LAMBDA, MU, TR_EPS
      INTEGER I, J

      E_MOD = PROPS(1)
      E_NU  = PROPS(2)

      LAMBDA = (E_MOD * E_NU) / ((1.0D0 + E_NU) * (1.0D0 - 2.0D0 * E_NU))
      MU     = E_MOD / (2.0D0 * (1.0D0 + E_NU))

      DO I=1, NTENS
        DO J=1, NTENS
          DDSDDE(I, J) = 0.0D0
        ENDDO
      ENDDO

      DDSDDE(1,1) = LAMBDA + 2.0D0 * MU
      DDSDDE(1,2) = LAMBDA
      DDSDDE(2,1) = LAMBDA
      DDSDDE(2,2) = LAMBDA + 2.0D0 * MU
      DDSDDE(3,3) = MU

      TR_EPS = STRAN(1) + DSTRAN(1) + STRAN(2) + DSTRAN(2)
      STRESS(1) = LAMBDA * TR_EPS + 2.0D0 * MU * (STRAN(1) + DSTRAN(1))
      STRESS(2) = LAMBDA * TR_EPS + 2.0D0 * MU * (STRAN(2) + DSTRAN(2))
      STRESS(3) = MU * (STRAN(3) + DSTRAN(3))

      RETURN
      END
