C ======================================================================
C User Subroutine UEL and UMAT for Abaqus: Mixed 3-Node / 4-Node Scheme
C JTYPE = 1: 4-Node Quad Phase-Field UEL (U1)
C JTYPE = 2: 4-Node Quad Displacement UEL (U2)
C JTYPE = 3: 3-Node Triangle Phase-Field UEL (U3)
C JTYPE = 4: 3-Node Triangle Displacement UEL (U4)
C ======================================================================
      SUBROUTINE UEL(RHS,AMATRX,SVARS,ENERGY,NDOFEL,NRHS,NSVARS,
     1     PROPS,NPROPS,COORDS,MCRD,NNODE,U,DU,V,A,JTYPE,TIME,DTIME,
     2     KSTEP,KINC,JELEM,PARAMS,NDLOAD,JDLTYP,ADLMAG,PREDEF,
     3     NPREDF,LFLAGS,MLVARX,DDLMAG,MDLOAD,PNEWDT,JPROPS,NJPROP,
     4     PERIOD)
C     ==================================================================
      INCLUDE 'ABA_PARAM.INC'
C     ==================================================================
      PARAMETER(ZERO=0.D0,ONE=1.D0,TWO=2.D0,THREE=3.D0,
     1 HALF=0.5D0,SIX=6.D0,N_CAPACITY=100000,NSTV=18)
C     ==================================================================
      DIMENSION RHS(MLVARX,1),AMATRX(NDOFEL,NDOFEL),
     1     SVARS(NSVARS),ENERGY(8),PROPS(NPROPS),COORDS(MCRD,NNODE),
     2     U(NDOFEL),DU(MLVARX,1),V(NDOFEL),A(NDOFEL),TIME(2),
     3     PARAMS(3),JDLTYP(MDLOAD,*),ADLMAG(MDLOAD,*),
     4     DDLMAG(MDLOAD,*),PREDEF(2,NPREDF,NNODE),LFLAGS(*),
     5     JPROPS(*)

       INTEGER I,J,L,K,K1,K2,INPT,INODE,NPHYS_VAL,PHYSIDX
       REAL*8 XII_Q(4,2),XI(2),dNdxi_Q(4,2),dNdxi_T(3,2),
     1 VJACOB(2,2),dNdx_Q(4,2),dNdx_T(3,2),VJABOBINV(2,2),
     2 AN_Q(4),AN_T(3),BP_Q(2,4),BP_T(2,3),DP(2),
     3 BB_Q(3,8),BB_T(3,6),CMAT(3,3),EPS(3),STRESS(3),
     4 XII_T(3,2),W_T(3)
       REAL*8 DTM,THCK,HIST,CLPAR,GCPAR,EMOD,ENU,PARK,ENG,PHASE
       REAL*8 EG,EG2,ELAM,DEG,WT_FAC

       COMMON/KUSER/USRVAR(N_CAPACITY,NSTV,4)

C     ==================================================================
C     INITIALIZATION OF RHS AND AMATRX
C     ==================================================================
       DO K1 = 1, NDOFEL
        DO KRHS = 1, NRHS
         RHS(K1,KRHS) = ZERO
        END DO
        DO K2 = 1, NDOFEL
         AMATRX(K2,K1) = ZERO
        END DO
       END DO

C     ==================================================================
C     TYPE 1: 4-Node Quad Phase-Field UEL (U1)
C     ==================================================================
       IF (JTYPE.EQ.1) THEN
        CLPAR=PROPS(1)
        GCPAR=PROPS(2)
        THCK=PROPS(3)
        PHYSIDX=JELEM
        XII_Q(1,1) = -ONE/THREE**HALF
        XII_Q(1,2) = -ONE/THREE**HALF
        XII_Q(2,1) = ONE/THREE**HALF
        XII_Q(2,2) = -ONE/THREE**HALF
        XII_Q(3,1) = ONE/THREE**HALF
        XII_Q(3,2) = ONE/THREE**HALF
        XII_Q(4,1) = -ONE/THREE**HALF
        XII_Q(4,2) = ONE/THREE**HALF
        DO INPT=1,4
         XI(1) = XII_Q(INPT,1)
         XI(2) = XII_Q(INPT,2)
         CALL SHAPEFUN_QUAD(AN_Q,dNdxi_Q,XI)
         DO I = 1,2
          DO J = 1,2
           VJACOB(I,J) = ZERO
           DO K = 1,4
            VJACOB(I,J) = VJACOB(I,J) + COORDS(I,K)*dNdxi_Q(K,J)
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
           dNdx_Q(K,I) = ZERO
           DO J = 1,2
            dNdx_Q(K,I) = dNdx_Q(K,I) + dNdxi_Q(K,J)*VJABOBINV(J,I)
           END DO
          END DO
         END DO
         DO INODE=1,4
          BP_Q(1,INODE)=dNdx_Q(INODE,1)
          BP_Q(2,INODE)=dNdx_Q(INODE,2)
         END DO
         PHASE=ZERO
         DO I=1,4
          PHASE=PHASE+AN_Q(I)*U(I)
         END DO
         DP(1)=ZERO
         DP(2)=ZERO
         DO I=1,2
          DO J=1,4
           DP(I)=DP(I)+BP_Q(I,J)*U(J)
          END DO
         END DO
         HIST=USRVAR(PHYSIDX,13,INPT)
         DO I=1,4
          RHS(I,1)=RHS(I,1)-THCK*DTM*(AN_Q(I)*((TWO*HIST+
     1    GCPAR/CLPAR)*PHASE-TWO*HIST)+GCPAR*CLPAR*
     2    (BP_Q(1,I)*DP(1)+BP_Q(2,I)*DP(2)))
         END DO
         DO I=1,4
          DO J=1,4
           AMATRX(I,J)=AMATRX(I,J)+THCK*DTM*(AN_Q(I)*AN_Q(J)*
     1     (TWO*HIST+GCPAR/CLPAR)+GCPAR*CLPAR*
     2     (BP_Q(1,I)*BP_Q(1,J)+BP_Q(2,I)*BP_Q(2,J)))
          END DO
         END DO
         USRVAR(PHYSIDX,1,INPT)=PHASE
         USRVAR(PHYSIDX,2,INPT)=HIST
         USRVAR(PHYSIDX,14,INPT)=PHASE
         USRVAR(PHYSIDX,15,INPT)=PHASE
         USRVAR(PHYSIDX,16,INPT)=HIST
        END DO
        RETURN
       ENDIF

C     ==================================================================
C     TYPE 2: 4-Node Quad Displacement UEL (U2)
C     ==================================================================
       IF (JTYPE.EQ.2) THEN
        EMOD=PROPS(1)
        ENU=PROPS(2)
        THCK=PROPS(3)
        PARK=PROPS(4)
        NPHYS_VAL = 1
        IF (NPROPS.GE.5) THEN
         NPHYS_VAL = INT(PROPS(5))
        END IF
        PHYSIDX = JELEM - NPHYS_VAL
        IF (PHYSIDX.LE.0) PHYSIDX = JELEM
        EG=EMOD/(TWO*(ONE+ENU))
        EG2=EG*TWO
        ELAM=EG2*ENU/(ONE-TWO*ENU)
        CMAT(1,1)=EG2+ELAM
        CMAT(1,2)=ELAM
        CMAT(1,3)=ZERO
        CMAT(2,1)=ELAM
        CMAT(2,2)=EG2+ELAM
        CMAT(2,3)=ZERO
        CMAT(3,1)=ZERO
        CMAT(3,2)=ZERO
        CMAT(3,3)=EG
        XII_Q(1,1) = -ONE/THREE**HALF
        XII_Q(1,2) = -ONE/THREE**HALF
        XII_Q(2,1) = ONE/THREE**HALF
        XII_Q(2,2) = -ONE/THREE**HALF
        XII_Q(3,1) = ONE/THREE**HALF
        XII_Q(3,2) = ONE/THREE**HALF
        XII_Q(4,1) = -ONE/THREE**HALF
        XII_Q(4,2) = ONE/THREE**HALF
        DO INPT=1,4
         XI(1) = XII_Q(INPT,1)
         XI(2) = XII_Q(INPT,2)
         CALL SHAPEFUN_QUAD(AN_Q,dNdxi_Q,XI)
         DO I = 1,2
          DO J = 1,2
           VJACOB(I,J) = ZERO
           DO K = 1,4
            VJACOB(I,J) = VJACOB(I,J) + COORDS(I,K)*dNdxi_Q(K,J)
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
           dNdx_Q(K,I) = ZERO
           DO J = 1,2
            dNdx_Q(K,I) = dNdx_Q(K,I) + dNdxi_Q(K,J)*VJABOBINV(J,I)
           END DO
          END DO
         END DO
         DO I=1,3
          DO J=1,8
           BB_Q(I,J)=ZERO
          END DO
         END DO
         DO INODE=1,4
          BB_Q(1,2*INODE-1)=dNdx_Q(INODE,1)
          BB_Q(2,2*INODE)  =dNdx_Q(INODE,2)
          BB_Q(3,2*INODE-1)=dNdx_Q(INODE,2)
          BB_Q(3,2*INODE)  =dNdx_Q(INODE,1)
         END DO
         EPS(1)=ZERO
         EPS(2)=ZERO
         EPS(3)=ZERO
         DO I=1,3
          DO J=1,8
           EPS(I)=EPS(I)+BB_Q(I,J)*U(J)
          END DO
         END DO
         PHASE=USRVAR(PHYSIDX,1,INPT)
         DEG=(ONE-PHASE)**TWO + PARK
         DO I=1,3
          STRESS(I)=ZERO
          DO J=1,3
           STRESS(I)=STRESS(I)+DEG*CMAT(I,J)*EPS(J)
          END DO
         END DO
         ENG=HALF*(EPS(1)*(CMAT(1,1)*EPS(1)+CMAT(1,2)*EPS(2))+
     1   EPS(2)*(CMAT(2,1)*EPS(1)+CMAT(2,2)*EPS(2))+
     2   EPS(3)*CMAT(3,3)*EPS(3))
         IF (ENG.GT.USRVAR(PHYSIDX,13,INPT)) THEN
          USRVAR(PHYSIDX,13,INPT)=ENG
         END IF
         DO I=1,8
          DO J=1,3
           RHS(I,1)=RHS(I,1)-THCK*DTM*BB_Q(J,I)*STRESS(J)
          END DO
         END DO
         DO I=1,8
          DO J=1,8
           DO K=1,3
            DO L=1,3
             AMATRX(I,J)=AMATRX(I,J)+THCK*DTM*BB_Q(K,I)*DEG*CMAT(K,L)*
     1       BB_Q(L,J)
            END DO
           END DO
          END DO
         END DO
        END DO
        RETURN
       ENDIF

C     ==================================================================
C     TYPE 3: 3-Node Triangle Phase-Field UEL (U3) - 3-Point Quadrature
C     ==================================================================
       IF (JTYPE.EQ.3) THEN
        CLPAR=PROPS(1)
        GCPAR=PROPS(2)
        THCK=PROPS(3)
        PHYSIDX=JELEM
        XII_T(1,1) = ONE/SIX
        XII_T(1,2) = ONE/SIX
        XII_T(2,1) = TWO/THREE
        XII_T(2,2) = ONE/SIX
        XII_T(3,1) = ONE/SIX
        XII_T(3,2) = TWO/THREE
        W_T(1) = ONE/SIX
        W_T(2) = ONE/SIX
        W_T(3) = ONE/SIX
        DO INPT=1,3
         XI(1) = XII_T(INPT,1)
         XI(2) = XII_T(INPT,2)
         CALL SHAPEFUN_TRI(AN_T,dNdxi_T,XI)
         DO I = 1,2
          DO J = 1,2
           VJACOB(I,J) = ZERO
           DO K = 1,3
            VJACOB(I,J) = VJACOB(I,J) + COORDS(I,K)*dNdxi_T(K,J)
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
           dNdx_T(K,I) = ZERO
           DO J = 1,2
            dNdx_T(K,I) = dNdx_T(K,I) + dNdxi_T(K,J)*VJABOBINV(J,I)
           END DO
          END DO
         END DO
         DO INODE=1,3
          BP_T(1,INODE)=dNdx_T(INODE,1)
          BP_T(2,INODE)=dNdx_T(INODE,2)
         END DO
         PHASE=ZERO
         DO I=1,3
          PHASE=PHASE+AN_T(I)*U(I)
         END DO
         DP(1)=ZERO
         DP(2)=ZERO
         DO I=1,2
          DO J=1,3
           DP(I)=DP(I)+BP_T(I,J)*U(J)
          END DO
         END DO
         HIST=USRVAR(PHYSIDX,13,INPT)
         WT_FAC=THCK*DTM*W_T(INPT)
         DO I=1,3
          RHS(I,1)=RHS(I,1)-WT_FAC*(AN_T(I)*((TWO*HIST+
     1    GCPAR/CLPAR)*PHASE-TWO*HIST)+GCPAR*CLPAR*
     2    (BP_T(1,I)*DP(1)+BP_T(2,I)*DP(2)))
         END DO
         DO I=1,3
          DO J=1,3
           AMATRX(I,J)=AMATRX(I,J)+WT_FAC*(AN_T(I)*AN_T(J)*
     1     (TWO*HIST+GCPAR/CLPAR)+GCPAR*CLPAR*
     2     (BP_T(1,I)*BP_T(1,J)+BP_T(2,I)*BP_T(2,J)))
          END DO
         END DO
         USRVAR(PHYSIDX,1,INPT)=PHASE
         USRVAR(PHYSIDX,2,INPT)=HIST
         USRVAR(PHYSIDX,14,INPT)=PHASE
         USRVAR(PHYSIDX,15,INPT)=PHASE
         USRVAR(PHYSIDX,16,INPT)=HIST
        END DO
        RETURN
       ENDIF

C     ==================================================================
C     TYPE 4: 3-Node Triangle Displacement UEL (U4) - 3-Point Quadrature
C     ==================================================================
       IF (JTYPE.EQ.4) THEN
        EMOD=PROPS(1)
        ENU=PROPS(2)
        THCK=PROPS(3)
        PARK=PROPS(4)
        NPHYS_VAL = 1
        IF (NPROPS.GE.5) THEN
         NPHYS_VAL = INT(PROPS(5))
        END IF
        PHYSIDX = JELEM - NPHYS_VAL
        IF (PHYSIDX.LE.0) PHYSIDX = JELEM
        EG=EMOD/(TWO*(ONE+ENU))
        EG2=EG*TWO
        ELAM=EG2*ENU/(ONE-TWO*ENU)
        CMAT(1,1)=EG2+ELAM
        CMAT(1,2)=ELAM
        CMAT(1,3)=ZERO
        CMAT(2,1)=ELAM
        CMAT(2,2)=EG2+ELAM
        CMAT(2,3)=ZERO
        CMAT(3,1)=ZERO
        CMAT(3,2)=ZERO
        CMAT(3,3)=EG
        XII_T(1,1) = ONE/SIX
        XII_T(1,2) = ONE/SIX
        XII_T(2,1) = TWO/THREE
        XII_T(2,2) = ONE/SIX
        XII_T(3,1) = ONE/SIX
        XII_T(3,2) = TWO/THREE
        W_T(1) = ONE/SIX
        W_T(2) = ONE/SIX
        W_T(3) = ONE/SIX
        DO INPT=1,3
         XI(1) = XII_T(INPT,1)
         XI(2) = XII_T(INPT,2)
         CALL SHAPEFUN_TRI(AN_T,dNdxi_T,XI)
         DO I = 1,2
          DO J = 1,2
           VJACOB(I,J) = ZERO
           DO K = 1,3
            VJACOB(I,J) = VJACOB(I,J) + COORDS(I,K)*dNdxi_T(K,J)
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
           dNdx_T(K,I) = ZERO
           DO J = 1,2
            dNdx_T(K,I) = dNdx_T(K,I) + dNdxi_T(K,J)*VJABOBINV(J,I)
           END DO
          END DO
         END DO
         DO I=1,3
          DO J=1,6
           BB_T(I,J)=ZERO
          END DO
         END DO
         DO INODE=1,3
          BB_T(1,2*INODE-1)=dNdx_T(INODE,1)
          BB_T(2,2*INODE)  =dNdx_T(INODE,2)
          BB_T(3,2*INODE-1)=dNdx_T(INODE,2)
          BB_T(3,2*INODE)  =dNdx_T(INODE,1)
         END DO
         EPS(1)=ZERO
         EPS(2)=ZERO
         EPS(3)=ZERO
         DO I=1,3
          DO J=1,6
           EPS(I)=EPS(I)+BB_T(I,J)*U(J)
          END DO
         END DO
         PHASE=USRVAR(PHYSIDX,1,INPT)
         DEG=(ONE-PHASE)**TWO + PARK
         DO I=1,3
          STRESS(I)=ZERO
          DO J=1,3
           STRESS(I)=STRESS(I)+DEG*CMAT(I,J)*EPS(J)
          END DO
         END DO
         ENG=HALF*(EPS(1)*(CMAT(1,1)*EPS(1)+CMAT(1,2)*EPS(2))+
     1   EPS(2)*(CMAT(2,1)*EPS(1)+CMAT(2,2)*EPS(2))+
     2   EPS(3)*CMAT(3,3)*EPS(3))
         IF (ENG.GT.USRVAR(PHYSIDX,13,INPT)) THEN
          USRVAR(PHYSIDX,13,INPT)=ENG
         END IF
         WT_FAC=THCK*DTM*W_T(INPT)
         DO I=1,6
          DO J=1,3
           RHS(I,1)=RHS(I,1)-WT_FAC*BB_T(J,I)*STRESS(J)
          END DO
         END DO
         DO I=1,6
          DO J=1,6
           DO K=1,3
            DO L=1,3
             AMATRX(I,J)=AMATRX(I,J)+WT_FAC*BB_T(K,I)*DEG*CMAT(K,L)*
     1       BB_T(L,J)
            END DO
           END DO
          END DO
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
      PARAMETER(ZERO=0.D0,ONE=1.D0,TWO=2.D0,N_CAPACITY=100000)
      COMMON/KUSER/USRVAR(N_CAPACITY,18,4)

      EMOD=PROPS(1)
      ENU=PROPS(2)
      NPHYS_VAL = 1
      IF (NPROPS.GE.3) THEN
       NPHYS_VAL = INT(PROPS(3))
      END IF
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
      PHYSIDX=NOEL - TWO*NPHYS_VAL
      IF (PHYSIDX.LE.0) PHYSIDX=NOEL
      NPT_IDX=NPT
      IF (NPT_IDX.GT.4) NPT_IDX=4
      DO I=1,NSTATV
       STATEV(I)=USRVAR(PHYSIDX,I,NPT_IDX)
      END DO
      RETURN
      END
