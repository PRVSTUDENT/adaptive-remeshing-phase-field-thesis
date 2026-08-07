C ======================================================================
C User Subroutine UEL and UMAT for Abaqus: Mixed 3-Node Triangle / 4-Node Quad Scheme
C JTYPE = 1: 4-Node Quad Phase-Field UEL (U11)
C JTYPE = 2: 4-Node Quad Displacement UEL (U12)
C JTYPE = 3: 3-Node Triangle Phase-Field UEL (U21)
C JTYPE = 4: 3-Node Triangle Displacement UEL (U22)
C ======================================================================
      SUBROUTINE UEL(RHS,AMATRX,SVARS,ENERGY,NDOFEL,NRHS,NSVARS,
     1     PROPS,NPROPS,COORDS,MCRD,NNODE,U,DU,V,A,JTYPE,TIME,DTIME,
     2     KSTEP,KINC,JELEM,PARAMS,NDLOAD,JDLTYP,ADLMAG,PREDEF,
     3     NPREDF,LFLAGS,MLVARX,DDLMAG,MDLOAD,PNEWDT,JPROPS,NJPROP,
     4     PERIOD)
C     ==================================================================
      INCLUDE 'ABA_PARAM.INC'
C     ==================================================================
      PARAMETER(ZERO=0.D0,ONE=1.D0,MONE=-1.D0,TWO=2.D0,THREE=3.D0,
     1 TOLER=1.0D-8,FOUR=4.D0,RP25 = 0.25D0,HALF=0.5D0,SIX=6.D0,
     2 N_ELEM=100000,NSTVTO=2,NSTVTT=14,NSTV=18)
C     ==================================================================
      DIMENSION RHS(MLVARX,1),AMATRX(NDOFEL,NDOFEL),
     1     SVARS(NSVARS),ENERGY(8),PROPS(NPROPS),COORDS(MCRD,NNODE),
     2     U(NDOFEL),DU(MLVARX,1),V(NDOFEL),A(NDOFEL),TIME(2),
     3     PARAMS(3),JDLTYP(MDLOAD,*),ADLMAG(MDLOAD,*),
     4     DDLMAG(MDLOAD,*),PREDEF(2,NPREDF,NNODE),LFLAGS(*),
     5     JPROPS(*)

       INTEGER I,J,L,K,K1,K2,K3,K4,IX,IY
       REAL*8 AINTW(4),XII(4,2),XI(2),dNdxi(4,2),
     1 VJACOB(2,2),dNdx(4,2),VJABOBINV(2,2),AN(4),BP(2,8),
     2 DP(2),SDV(NSTV),BB(3,8),CMAT(3,3),EPS(3),STRESS(3),
     3 VNI(2,8),ULOC(2),PHASENOD(4)
       REAL*8 DTM,THCK,HIST,CLPAR,GCPAR,EMOD,ENU,PARK,ENG

       COMMON/KUSER/USRVAR(N_ELEM,NSTV,4)

C     ==================================================================
C     TYPE 1: 4-Node Quad Phase-Field UEL (U11)
C     ==================================================================
       IF (JTYPE.EQ.1) THEN
        CLPAR=PROPS(1)
        GCPAR=PROPS(2)
        THCK=PROPS(3)
        DO K1 = 1, NDOFEL
         DO KRHS = 1, NRHS
          RHS(K1,KRHS) = ZERO
         END DO
         DO K2 = 1, NDOFEL
          AMATRX(K2,K1) = ZERO
         END DO
        END DO
        XII(1,1) = -ONE/THREE**HALF
        XII(1,2) = -ONE/THREE**HALF
        XII(2,1) = ONE/THREE**HALF
        XII(2,2) = -ONE/THREE**HALF
        XII(3,1) = ONE/THREE**HALF
        XII(3,2) = ONE/THREE**HALF
        XII(4,1) = -ONE/THREE**HALF
        XII(4,2) = ONE/THREE**HALF
        DO INPT=1,4
         XI(1) = XII(INPT,1)
         XI(2) = XII(INPT,2)
         CALL SHAPEFUN_QUAD(AN,dNdxi,XI)
         DO I = 1,2
          DO J = 1,2
           VJACOB(I,J) = ZERO
           DO K = 1,4
            VJACOB(I,J) = VJACOB(I,J) + COORDS(I,K)*dNdxi(K,J)
           END DO
          END DO
         END DO
         DTM = VJACOB(1,1)*VJACOB(2,2)-VJACOB(1,2)*VJACOB(2,1)
         VJABOBINV(1,1)=VJACOB(2,2)/DTM
         VJABOBINV(1,2)=-VJACOB(1,2)/DTM
         VJABOBINV(2,1)=-VJACOB(2,1)/DTM
         VJABOBINV(2,2)=VJACOB(1,1)/DTM
         DO K = 1,4
          DO I = 1,2
           dNdx(K,I) = ZERO
           DO J = 1,2
            dNdx(K,I) = dNdx(K,I) + dNdxi(K,J)*VJABOBINV(J,I)
           END DO
          END DO
         END DO
         DO INODE=1,4
          BP(1,INODE)=dNdx(INODE,1)
          BP(2,INODE)=dNdx(INODE,2)
         END DO
         PHASE=ZERO
         DO I=1,4
          PHASE=PHASE+AN(I)*U(I)
         END DO
         DP(1)=ZERO
         DP(2)=ZERO
         DO I=1,2
          DO J=1,4
           DP(I)=DP(I)+BP(I,J)*U(J)
          END DO
         END DO
         HIST=USRVAR(JELEM,13,INPT)
         DO I=1,4
          RHS(I,1)=RHS(I,1)-THCK*DTM*(AN(I)*((GC*CLPAR*TWO*HIST+
     1    GCPAR/CLPAR)*PHASE-GC*CLPAR*TWO*HIST)+GCPAR*CLPAR*
     2    (BP(1,I)*DP(1)+BP(2,I)*DP(2)))
         END DO
         DO I=1,4
          DO J=1,4
           AMATRX(I,J)=AMATRX(I,J)+THCK*DTM*(AN(I)*AN(J)*
     1     (GCPAR*CLPAR*TWO*HIST+GCPAR/CLPAR)+GCPAR*CLPAR*
     2     (BP(1,I)*BP(1,J)+BP(2,I)*BP(2,J)))
          END DO
         END DO
        END DO
        RETURN
       ENDIF

C     ==================================================================
C     TYPE 3: 3-Node Triangle Phase-Field UEL (U21)
C     ==================================================================
       IF (JTYPE.EQ.3) THEN
        CLPAR=PROPS(1)
        GCPAR=PROPS(2)
        THCK=PROPS(3)
        DO K1 = 1, 3
         DO KRHS = 1, NRHS
          RHS(K1,KRHS) = ZERO
         END DO
         DO K2 = 1, 3
          AMATRX(K2,K1) = ZERO
         END DO
        END DO
        XI(1) = ONE/THREE
        XI(2) = ONE/THREE
        CALL SHAPEFUN_TRI(AN,dNdxi,XI)
        DO I = 1,2
         DO J = 1,2
          VJACOB(I,J) = ZERO
          DO K = 1,3
           VJACOB(I,J) = VJACOB(I,J) + COORDS(I,K)*dNdxi(K,J)
          END DO
         END DO
        END DO
        DTM = VJACOB(1,1)*VJACOB(2,2)-VJACOB(1,2)*VJACOB(2,1)
        VJABOBINV(1,1)=VJACOB(2,2)/DTM
        VJABOBINV(1,2)=-VJACOB(1,2)/DTM
        VJABOBINV(2,1)=-VJACOB(2,1)/DTM
        VJABOBINV(2,2)=VJACOB(1,1)/DTM
        DO K = 1,3
         DO I = 1,2
          dNdx(K,I) = ZERO
          DO J = 1,2
           dNdx(K,I) = dNdx(K,I) + dNdxi(K,J)*VJABOBINV(J,I)
          END DO
         END DO
        END DO
        DO INODE=1,3
         BP(1,INODE)=dNdx(INODE,1)
         BP(2,INODE)=dNdx(INODE,2)
        END DO
        PHASE=ZERO
        DO I=1,3
         PHASE=PHASE+AN(I)*U(I)
        END DO
        DP(1)=ZERO
        DP(2)=ZERO
        DO I=1,2
         DO J=1,3
          DP(I)=DP(I)+BP(I,J)*U(J)
         END DO
        END DO
        HIST=USRVAR(JELEM,13,1)
        DO I=1,3
         RHS(I,1)=RHS(I,1)-THCK*HALF*DTM*(AN(I)*((GC*CLPAR*TWO*HIST+
     1   GCPAR/CLPAR)*PHASE-GC*CLPAR*TWO*HIST)+GCPAR*CLPAR*
     2   (BP(1,I)*DP(1)+BP(2,I)*DP(2)))
        END DO
        DO I=1,3
         DO J=1,3
          AMATRX(I,J)=AMATRX(I,J)+THCK*HALF*DTM*(AN(I)*AN(J)*
     1    (GCPAR*CLPAR*TWO*HIST+GCPAR/CLPAR)+GCPAR*CLPAR*
     2    (BP(1,I)*BP(1,J)+BP(2,I)*BP(2,J)))
         END DO
        END DO
        RETURN
       ENDIF

       RETURN
       END

C ======================================================================
C Shape Function Subroutine for 4-Node Quadrilateral
C ======================================================================
      SUBROUTINE SHAPEFUN_QUAD(AN,dNdxi,xi)
      INCLUDE 'ABA_PARAM.INC'
      Real*8 AN(4),dNdxi(4,2),XI(2)
      PARAMETER(ZERO=0.D0,ONE=1.D0,MONE=-1.D0,FOUR=4.D0)
      AN(1) = ONE/FOUR*(ONE-XI(1))*(ONE-XI(2))
      AN(2) = ONE/FOUR*(ONE+XI(1))*(ONE-XI(2))
      AN(3) = ONE/FOUR*(ONE+XI(1))*(ONE+XI(2))
      AN(4) = ONE/FOUR*(ONE-XI(1))*(ONE+XI(2))
      dNdxi(1,1) = MONE/FOUR*(ONE-XI(2))
      dNdxi(1,2) = MONE/FOUR*(ONE-XI(1))
      dNdxi(2,1) = ONE/FOUR*(ONE-XI(2))
      dNdxi(2,2) = MONE/FOUR*(ONE+XI(1))
      dNdxi(3,1) = ONE/FOUR*(ONE+XI(2))
      dNdxi(3,2) = ONE/FOUR*(ONE+XI(1))
      dNdxi(4,1) = MONE/FOUR*(ONE+XI(2))
      dNdxi(4,2) = ONE/FOUR*(ONE-XI(1))
      RETURN
      END

C ======================================================================
C Shape Function Subroutine for 3-Node Linear Triangle
C ======================================================================
      SUBROUTINE SHAPEFUN_TRI(AN,dNdxi,xi)
      INCLUDE 'ABA_PARAM.INC'
      Real*8 AN(3),dNdxi(3,2),XI(2)
      PARAMETER(ZERO=0.D0,ONE=1.D0,MONE=-1.D0)
      AN(1) = ONE - XI(1) - XI(2)
      AN(2) = XI(1)
      AN(3) = XI(2)
      dNdxi(1,1) = MONE
      dNdxi(1,2) = MONE
      dNdxi(2,1) = ONE
      dNdxi(2,2) = ZERO
      dNdxi(3,1) = ZERO
      dNdxi(3,2) = ONE
      RETURN
      END

C ======================================================================
C Subroutine UMAT: Facsimile Post-Processing & Error Indicator Layer
C ======================================================================
       SUBROUTINE UMAT(STRESS,STATEV,DDSDDE,SSE,SPD,SCD,
     1 RPL,DDSDDT,DRPLDE,DRPLDT,STRAN,DSTRAN,
     2 TIME,DTIME,TEMP,DTEMP,PREDEF,DPRED,MATERL,NDI,NSHR,NTENS,
     3 NSTATV,PROPS,NPROPS,COORDS,DROT,PNEWDT,CELENT,
     4 DFGRD0,DFGRD1,NOEL,NPT,KSLAY,KSPT,KSTEP,KINC)
      INCLUDE 'ABA_PARAM.INC'
      DIMENSION STRESS(NTENS),STATEV(NSTATV),DDSDDE(NTENS,NTENS),
     1 PROPS(NPROPS),COORDS(3),DSTRAN(NTENS)
      REAL*8 EMOD,ENU,EG,EG2,ELAM
      PARAMETER(ZERO=0.D0,ONE=1.D0,TWO=2.D0,N_ELEM=100000)
      COMMON/KUSER/USRVAR(N_ELEM,18,4)

      EMOD=PROPS(1)
      ENU=PROPS(2)
      EG=EMOD/(TWO*(ONE+ENU))
      EG2=EG*TWO
      ELAM=EG2*ENU/(ONE-TWO*ENU)
      DO K1=1, NTENS
       DO K2=1, NTENS
        DDSDDE(K2, K1)=ZERO
       END DO
      END DO
      DO K1=1, NDI
       DO K2=1, NDI
        DDSDDE(K2, K1)=ELAM
       END DO
       DDSDDE(K1, K1)=EG2+ELAM
      END DO
      DO K1=NDI+1, NTENS
       DDSDDE(K1, K1)=EG
      END DO
      DO K1=1, NTENS
       DO K2=1, NTENS
        STRESS(K2)=STRESS(K2)+DDSDDE(K2, K1)*DSTRAN(K1)
       END DO
      END DO
      NELEMAN=NOEL
      IF (NELEMAN.GT.TWO*N_ELEM) THEN
       NELEMAN=NELEMAN-TWO*N_ELEM
      ENDIF
      NPT_IDX=NPT
      IF (NPT_IDX.GT.4) NPT_IDX=4
      DO I=1,NSTATV
       STATEV(I)=USRVAR(NELEMAN,I,NPT_IDX)
      END DO
      RETURN
      END
