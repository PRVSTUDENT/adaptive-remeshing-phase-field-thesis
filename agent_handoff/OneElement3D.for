C ======================================================================
C User Subroutine UEL for Abaqus: two elements for the split scheme
C  operator phase and displacement problem:
C Type 1: C3P8 phsae-field element
C Type 2: C3D16 displacement element
C G. Molnar and A. Gravouil, 2016
C gmolnar.work@gmail.com
C ======================================================================
C Material properties to be given through the input file (*.inp), are
C
C For Type 1 element (phase field):
C PROPS(1) = Crack scale parameter (lc)
C PROPS(2) = Crack surface energy (Gc)
C PROPS(3) = Epsilon in Penelty function (mu)
C PROPS(4) = Exponent iof Penalty function (n)
C
C For Type 2 element (stress-strain):
C PROPS(1) = Young's modulus (E)
C PROPS(2) = Poisson's ratio (nu)
C PROPS(3) = Parameter k (stabilization of the stiffness matrix)
C
C ---- Used variables ---------------------
C N_ELEM - number of elements used in the model divided
C            by 3 - (N_phase+N_stress+N_UMAT)/3 (to be changed for each model)
Cs
C NSTVTO - solution dependent variables for the phase field element
C            (phase, energy history)
C NSTVTT - solution dependent variables for the strain element
C            (displacements, strains, stresses, elastic stresses,
C             energies, phase)
C NSTV - overall solution dependent variables (NSTVTO+NSTVTT+2), where
C           the additional 2 variables are the: time and iteration number
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
     2 N_ELEM=1,NSTVTO=2,NSTVTT=24,NSTV=28)
C     ==================================================================
C     Initialization for all the element types
C     ==================================================================
      DIMENSION RHS(MLVARX,1),AMATRX(NDOFEL,NDOFEL),
     1     SVARS(NSVARS),ENERGY(8),PROPS(NPROPS),COORDS(MCRD,NNODE),
     2     U(NDOFEL),DU(MLVARX,1),V(NDOFEL),A(NDOFEL),TIME(2),
     3     PARAMS(3),JDLTYP(MDLOAD,*),ADLMAG(MDLOAD,*),
     4     DDLMAG(MDLOAD,*),PREDEF(2,NPREDF,NNODE),LFLAGS(*),
     5     JPROPS(*)
     
       INTEGER I,J,L,K,K1,K2,K3,K4,IX,IY,IZ

       REAL*8 AINTW(NNODE),XII(NNODE,3),XI(3),dNdxi(NNODE,3),
     1 VJACOB(3,3),dNdx(NNODE,3),VJABOBINV(3,3),AN(NNODE),BP(3,NDOFEL),
     2 DP(3),SDV(NSTV),BB(6,NDOFEL),CMAT(6,6),EPS(6),STRESS(6),
     3 VNI(3,NDOFEL),ULOC(3)
     
       REAL*8 DTM,HIST,CLPAR,GCPAR,EMOD,ENU,PARK,ENG
 
       COMMON/KUSER/USRVAR(N_ELEM,NSTV,8)

C     ==================================================================
C     ******************************************************************
C     Constructing elemet TYPE 1 (phase)
C     ******************************************************************
C     ==================================================================
C       
       IF (JTYPE.EQ.ONE) THEN
C     ==================================================================
C     Time an iteration variables
C     ==================================================================
       TIMEZ=USRVAR(JELEM,27,1)
       IF (TIMEZ.LT.TIME(2)) THEN
        USRVAR(JELEM,27,1)=TIME(2)
        USRVAR(JELEM,28,1)=ZERO
       ELSE
        USRVAR(JELEM,28,1)=USRVAR(JELEM,28,1)+ONE
       ENDIF
       STEPITER=USRVAR(JELEM,28,1)
C     ==================================================================
C     Material parameters
C     ==================================================================
       CLPAR=PROPS(1)
       GCPAR =PROPS(2)
C     ==================================================================
C     Initial preparations
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
C     Local coordinates and weights
C     ==================================================================
       XII(1,1) = MONE/THREE**HALF
       XII(1,2) = MONE/THREE**HALF
       XII(1,3) = MONE/THREE**HALF
       XII(2,1) = ONE/THREE**HALF
       XII(2,2) = MONE/THREE**HALF
       XII(2,3) = MONE/THREE**HALF
       XII(3,1) = ONE/THREE**HALF
       XII(3,2) = ONE/THREE**HALF
       XII(3,3) = MONE/THREE**HALF
       XII(4,1) = MONE/THREE**HALF
       XII(4,2) = ONE/THREE**HALF
       XII(4,3) = MONE/THREE**HALF
       XII(5,1) = MONE/THREE**HALF
       XII(5,2) = MONE/THREE**HALF
       XII(5,3) = ONE/THREE**HALF
       XII(6,1) = ONE/THREE**HALF
       XII(6,2) = MONE/THREE**HALF
       XII(6,3) = ONE/THREE**HALF
       XII(7,1) = ONE/THREE**HALF
       XII(7,2) = ONE/THREE**HALF
       XII(7,3) = ONE/THREE**HALF
       XII(8,1) = MONE/THREE**HALF
       XII(8,2) = ONE/THREE**HALF
       XII(8,3) = ONE/THREE**HALF
       DO I=1,NNODE
        AINTW(I) = ONE
       END DO
C     ==================================================================
C     Calculating properties at each integration point
C     ==================================================================
       DO INPT=1,NNODE
C     Initializing solution dependent variables (phase,history)
        DO I=1,NSTVTO
          SDV(I)=SVARS(NSTVTO*(INPT-1)+I)
        END DO
C
C     Local coordinates of the integration point
        XI(1) = XII(INPT,1)
        XI(2) = XII(INPT,2) 
        XI(3) = XII(INPT,3) 
C     Shape functions and local derivatives
        CALL SHAPEFUN(AN,dNdxi,XI)
C     Jacobian
        DO I = 1,3
         DO J = 1,3
          VJACOB(I,J) = ZERO
          DO K = 1,NNODE
           VJACOB(I,J) = VJACOB(I,J) + COORDS(I,K)*dNdxi(K,J)
          END DO
         END DO
        END DO
C        
        DTM = ZERO
        DTM = VJACOB(1,1)*VJACOB(2,2)*VJACOB(3,3)+VJACOB(1,2)*
     1   VJACOB(2,3)*VJACOB(3,1)+VJACOB(1,3)*VJACOB(2,1)*
     2   VJACOB(3,2)-VJACOB(3,1)*VJACOB(2,2)*VJACOB(1,3)-
     3   VJACOB(3,2)*VJACOB(2,3)*VJACOB(1,1)-VJACOB(3,3)*
     4   VJACOB(2,1)*VJACOB(1,2)
C     
        IF (DTM.LT.ZERO) THEN
         WRITE(7,*) 'Negative Jacobian',DTM
         CALL XIT	
        ENDIF

C     Inverse of Jacobian
        VJABOBINV(1,1)=(VJACOB(2,2)*VJACOB(3,3)-VJACOB(2,3)*
     1   VJACOB(3,2))/DTM
        VJABOBINV(1,2)=-(VJACOB(1,2)*VJACOB(3,3)-VJACOB(3,2)*
     1   VJACOB(1,3))/DTM
        VJABOBINV(1,3)=(VJACOB(1,2)*VJACOB(2,3)-VJACOB(1,3)*
     1   VJACOB(2,2))/DTM
        VJABOBINV(2,1)=-(VJACOB(2,1)*VJACOB(3,3)-VJACOB(2,3)*
     1   VJACOB(3,1))/DTM
        VJABOBINV(2,2)=(VJACOB(1,1)*VJACOB(3,3)-VJACOB(1,3)*
     1   VJACOB(3,1))/DTM
        VJABOBINV(2,3)=-(VJACOB(1,1)*VJACOB(2,3)-VJACOB(1,3)*
     1   VJACOB(2,1))/DTM
        VJABOBINV(3,1)=(VJACOB(2,1)*VJACOB(3,2)-VJACOB(2,2)*
     1   VJACOB(3,1))/DTM
        VJABOBINV(3,2)=-(VJACOB(1,1)*VJACOB(3,2)-VJACOB(1,2)*
     1   VJACOB(3,1))/DTM
        VJABOBINV(3,3)=(VJACOB(1,1)*VJACOB(2,2)-VJACOB(1,2)*
     1   VJACOB(2,1))/DTM
C        
C     Derivatives of shape functions respect to global ccordinates
        DO K = 1,NNODE
         DO I = 1,3
          dNdx(K,I) = ZERO
          DO J = 1,3
           dNdx(K,I) = dNdx(K,I) + dNdxi(K,J)*VJABOBINV(J,I)
          END DO
         END DO
        END DO

C     Calculating B matrix (B=LN)
       DO INODE=1,NNODE
        BP(1,INODE)=dNdx(INODE,1)
        BP(2,INODE)=dNdx(INODE,2)
        BP(3,INODE)=dNdx(INODE,3)
       END DO
                
C     ==================================================================
C     Nodal phase-field
C     ==================================================================
        PHASE=ZERO
        DPHASE=ZERO
        DO I=1,8
         PHASE=PHASE+AN(I)*U(I)
        END DO
        DO I=1,8
         DPHASE=DPHASE+AN(I)*DU(I,1)
        END DO
C        
        IF (STEPITER.EQ.ZERO) THEN
          SDV(1)=PHASE-DPHASE
        ELSE
          SDV(1)=PHASE
        ENDIF
C       
        DO I=1,3
         DP(I)=ZERO
        END DO
        DO I=1,3
         DO J=1,NNODE
          DP(I)=DP(I)+BP(I,J)*U(J)
         END DO
        END DO
C
C     ==================================================================
C     Calculating elastic ENERGY history
C     ==================================================================
        IF (STEPITER.EQ.ZERO) THEN
         ENGN=USRVAR(JELEM,23,INPT)
        ELSE
         ENGN=USRVAR(JELEM,26,INPT)
        ENDIF
        
        HISTN=USRVAR(JELEM,26,INPT)
        IF (ENGN.GT.HISTN) THEN
         HIST=ENGN
        ELSE
         HIST=HISTN
        ENDIF
        SDV(2)=HIST
C     ==================================================================
C     Calculating element stiffness matrix
C     ==================================================================
        DO I=1,NDOFEL
         DO K=1,NDOFEL
          DO J=1,3
           AMATRX(I,K)=AMATRX(I,K)+BP(J,I)*BP(J,K)*DTM*
     1      GCPAR*CLPAR*AINTW(INPT)
          END DO
          AMATRX(I,K)=AMATRX(I,K)+AN(I)*AN(K)*DTM*
     1     AINTW(INPT)*(GCPAR/CLPAR+TWO*HIST)
         END DO
        END DO
C        
C     ==================================================================
C     Internal forces (residual vector)
C     ==================================================================
        DO I=1,NDOFEL
         DO J=1,3
           RHS(I,1)=RHS(I,1)-BP(J,I)*DP(J)*GCPAR*CLPAR*
     1      AINTW(INPT)*DTM
         END DO
         RHS(I,1)=RHS(I,1)-AN(I)*AINTW(INPT)*DTM*
     1    ((GCPAR/CLPAR+TWO*HIST)*PHASE-TWO*HIST)
        END DO

C     ==================================================================
C     Uploading solution dep. variables
C     ==================================================================
        DO I=1,NSTVTO
         SVARS(NSTVTO*(INPT-1)+I)=SDV(I)
         USRVAR(JELEM,I+NSTVTT,INPT)=SVARS(NSTVTO*(INPT-1)+I)
        END DO
       END DO
       
C     ==================================================================
C     ******************************************************************
C     Constructing elemet TYPE 2 (displacement)
C     ******************************************************************
C     ==================================================================
       ELSEIF (JTYPE.EQ.TWO) THEN
       STEPITER=USRVAR(JELEM-N_ELEM,28,1)
C     ==================================================================
C     Material parameters
C     ==================================================================
       EMOD = PROPS(1)
       ENU = PROPS(2)
       PARK = PROPS(3)
C     ==================================================================
C     Initial preparations
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
C     Local coordinates and weights
C     ==================================================================
       XII(1,1) = MONE/THREE**HALF
       XII(1,2) = MONE/THREE**HALF
       XII(1,3) = MONE/THREE**HALF
       XII(2,1) = ONE/THREE**HALF
       XII(2,2) = MONE/THREE**HALF
       XII(2,3) = MONE/THREE**HALF
       XII(3,1) = ONE/THREE**HALF
       XII(3,2) = ONE/THREE**HALF
       XII(3,3) = MONE/THREE**HALF
       XII(4,1) = MONE/THREE**HALF
       XII(4,2) = ONE/THREE**HALF
       XII(4,3) = MONE/THREE**HALF
       XII(5,1) = MONE/THREE**HALF
       XII(5,2) = MONE/THREE**HALF
       XII(5,3) = ONE/THREE**HALF
       XII(6,1) = ONE/THREE**HALF
       XII(6,2) = MONE/THREE**HALF
       XII(6,3) = ONE/THREE**HALF
       XII(7,1) = ONE/THREE**HALF
       XII(7,2) = ONE/THREE**HALF
       XII(7,3) = ONE/THREE**HALF
       XII(8,1) = MONE/THREE**HALF
       XII(8,2) = ONE/THREE**HALF
       XII(8,3) = ONE/THREE**HALF
       DO I=1,NNODE
        AINTW(I) = ONE
       END DO
C     ==================================================================
C     Calculating properties at each integration point
C     ==================================================================
       DO INPT=1,NNODE
C     Initial variables
        DO I=1,NSTVTT
          SDV(I)=SVARS(NSTVTT*(INPT-1)+I)
        END DO
C
C     Local coordinates of the integration point
        XI(1) = XII(INPT,1)
        XI(2) = XII(INPT,2)
        XI(3) = XII(INPT,3) 
C     Shape functions and local derivatives
        CALL SHAPEFUN(AN,dNdxi,XI)
C   Shape functions
        IZ=ZERO
        DO I = 1,NNODE
         IX=IZ+ONE
         IY=IX+ONE
         IZ=IY+ONE
         VNI(1,IX)=AN(I)
         VNI(2,IX)=ZERO
         VNI(3,IX)=ZERO
         VNI(1,IY)=ZERO
         VNI(2,IY)=AN(I)
         VNI(3,IY)=ZERO
         VNI(1,IZ)=ZERO
         VNI(2,IZ)=ZERO
         VNI(3,IZ)=AN(I)
        END DO
C     Jacobian
        DO I = 1,3
         DO J = 1,3
          VJACOB(I,J) = ZERO
          DO K = 1,NNODE
           VJACOB(I,J) = VJACOB(I,J) + COORDS(I,K)*dNdxi(K,J)
          END DO
         END DO
        END DO
C        
        DTM = ZERO
        DTM = VJACOB(1,1)*VJACOB(2,2)*VJACOB(3,3)+VJACOB(1,2)*
     1   VJACOB(2,3)*VJACOB(3,1)+VJACOB(1,3)*VJACOB(2,1)*
     2   VJACOB(3,2)-VJACOB(3,1)*VJACOB(2,2)*VJACOB(1,3)-
     3   VJACOB(3,2)*VJACOB(2,3)*VJACOB(1,1)-VJACOB(3,3)*
     4   VJACOB(2,1)*VJACOB(1,2)
        IF (DTM.LT.ZERO) THEN
         WRITE(7,*) 'Negative Jacobian',DTM
         CALL XIT	
        ENDIF
C
C     Inverse of Jacobian
        VJABOBINV(1,1)=(VJACOB(2,2)*VJACOB(3,3)-VJACOB(2,3)*
     1   VJACOB(3,2))/DTM
        VJABOBINV(1,2)=-(VJACOB(1,2)*VJACOB(3,3)-VJACOB(3,2)*
     1   VJACOB(1,3))/DTM
        VJABOBINV(1,3)=(VJACOB(1,2)*VJACOB(2,3)-VJACOB(1,3)*
     1   VJACOB(2,2))/DTM
        VJABOBINV(2,1)=-(VJACOB(2,1)*VJACOB(3,3)-VJACOB(2,3)*
     1   VJACOB(3,1))/DTM
        VJABOBINV(2,2)=(VJACOB(1,1)*VJACOB(3,3)-VJACOB(1,3)*
     1   VJACOB(3,1))/DTM
        VJABOBINV(2,3)=-(VJACOB(1,1)*VJACOB(2,3)-VJACOB(1,3)*
     1   VJACOB(2,1))/DTM
        VJABOBINV(3,1)=(VJACOB(2,1)*VJACOB(3,2)-VJACOB(2,2)*
     1   VJACOB(3,1))/DTM
        VJABOBINV(3,2)=-(VJACOB(1,1)*VJACOB(3,2)-VJACOB(1,2)*
     1   VJACOB(3,1))/DTM
        VJABOBINV(3,3)=(VJACOB(1,1)*VJACOB(2,2)-VJACOB(1,2)*
     1   VJACOB(2,1))/DTM
                
C     Derivatives of shape functions respect to global ccordinates
        DO K = 1,NNODE
         DO I = 1,3
          dNdx(K,I) = ZERO
          DO J = 1,3
           dNdx(K,I) = dNdx(K,I) + dNdxi(K,J)*VJABOBINV(J,I)
          END DO
         END DO
        END DO

C     Calculating B matrix (B=LN)
       IZ=ZERO
       DO INODE=1,NNODE
        IX=IZ+ONE
        IY=IX+ONE
        IZ=IY+ONE
        BB(1,IX)= dNdx(INODE,1)
        BB(2,IX)= ZERO
        BB(3,IX)= ZERO
        BB(4,IX)= dNdx(INODE,2)
        BB(5,IX)= dNdx(INODE,3)
        BB(6,IX)= ZERO
        BB(1,IY)= ZERO
        BB(2,IY)= dNdx(INODE,2)
        BB(3,IY)= ZERO
        BB(4,IY)= dNdx(INODE,1)
        BB(5,IY)= ZERO
        BB(6,IY)= dNdx(INODE,3)
        BB(1,IZ)= ZERO
        BB(2,IZ)= ZERO
        BB(3,IZ)= dNdx(INODE,3)
        BB(4,IZ)= ZERO
        BB(5,IZ)= dNdx(INODE,1)
        BB(6,IZ)= dNdx(INODE,2)
       END DO
C
C     ==================================================================
C     Calculating materials stiffness matrix (plane strain)
C     ==================================================================
        DO I=1,6
         DO J=1,6
          CMAT(I,J)=ZERO
         END DO
        END DO
C        
        DO I=1,3
         DO J=1,3
          CMAT(I,J)=EMOD/((ONE-ENU*TWO)*(ONE+ENU))*ENU
         END DO
        CMAT(I+3,I+3)=EMOD/((ONE-ENU*TWO)*(ONE+ENU))*(ONE-TWO*ENU)/TWO
        END DO
C
        DO J=1,3
         CMAT(J,J)=EMOD/((ONE-ENU*TWO)*(ONE+ENU))*(ONE-ENU)
        END DO
C     ==================================================================
C     Nodal displacements
C     ==================================================================
        DO J=1,3
         ULOC(J)=ZERO
        END DO
        DO J=1,3
         DO I=1,NDOFEL
          ULOC(J)=ULOC(J)+VNI(J,I)*U(I)
         END DO
        END DO
        DO J=1,3
         SDV(J)=ULOC(J)
        END DO
C   
C     ==================================================================
C     Nodal phase-field
C     ==================================================================
        IF (STEPITER.EQ.ZERO) THEN
         PHASE=USRVAR(JELEM-N_ELEM,25,INPT)
        ELSE
         PHASE=USRVAR(JELEM-N_ELEM,24,INPT)
        ENDIF
C
        IF (PHASE.GT.ONE) THEN
         PHASE=ONE
        ELSEIF (PHASE.LT.ZERO) THEN
         PHASE=ZERO
        ENDIF
        SDV(24)=PHASE
C     ==================================================================
C     Calculating strain
C     ==================================================================
        DO J=1,6
         EPS(J)=ZERO
        END DO
        DO I=1,6
         DO J=1,NDOFEL
          EPS(I)=EPS(I)+BB(I,J)*U(J)    
         END DO
        END DO
        DO J=1,6
         SDV(J+3)=EPS(J)
        END DO
C
C     ==================================================================
C     Calculating stresses
C     ==================================================================
        DO K1=1,6
         STRESS(K1)=ZERO
        END DO
        DO K1=1,6
         DO K2=1,6
          STRESS(K2)=STRESS(K2)+CMAT(K2,K1)*EPS(K1)
         END DO
        END DO
        DO J=1,6
         SDV(J+9)=STRESS(J)*((ONE-PHASE)**TWO+PARK)
        END DO
        DO J=1,6
         SDV(J+15)=STRESS(J)
        END DO
C     ==================================================================
C     Calculating elastic ENERGY
C     ==================================================================
        ENG=ZERO
        DO I=1,6
         ENG=ENG+STRESS(I)*EPS(I)*HALF
        END DO
        SDV(22)=ENG*((ONE-PHASE)**TWO+PARK)
        SDV(23)=ENG
        ENERGY(2)=ENG
C     ==================================================================
C     Calculating element stiffness matrix
C     ==================================================================
C
        DO K=1,NDOFEL
         DO L=1,NDOFEL
          DO I=1,6
           DO J=1,6
            AMATRX(K,L)=AMATRX(K,L)+AINTW(INPT)*BB(I,K)*CMAT(I,J)*
     1       BB(J,L)*DTM*((ONE-PHASE)**TWO+PARK)
           END DO
          END DO
         END DO
        END DO
C       
C     ==================================================================
C     Internal forces (residual vector)
C     ==================================================================
        DO K1=1,NDOFEL
         DO K4=1,6
           RHS(K1,1)=RHS(K1,1)-AINTW(INPT)*BB(K4,K1)*STRESS(K4)*DTM*
     1      ((ONE-PHASE)**TWO+PARK)
         END DO
        END DO
C
C     ==================================================================
C     Uploading solution dep. variables
C     ==================================================================
        DO I=1,NSTVTT
         SVARS(NSTVTT*(INPT-1)+I)=SDV(I)
         USRVAR(JELEM-N_ELEM,I,INPT)=SVARS(NSTVTT*(INPT-1)+I)
        END DO
       END DO
      ENDIF
      
      RETURN
      END
C
      SUBROUTINE SHAPEFUN(AN,dNdxi,XI)
      INCLUDE 'ABA_PARAM.INC'
      REAL*8 AN(8),dNdxi(8,3)
      REAL*8 XI(3)
      PARAMETER(ZERO=0.D0,ONE=1.D0,MONE=-1.D0,FOUR=4.D0,EIGHT=8.D0)

C     Values of shape functions as a function of local coord.
      AN(1) = ONE/EIGHT*(ONE-XI(1))*(ONE-XI(2))*(ONE-XI(3))
      AN(2) = ONE/EIGHT*(ONE+XI(1))*(ONE-XI(2))*(ONE-XI(3))
      AN(3) = ONE/EIGHT*(ONE+XI(1))*(ONE+XI(2))*(ONE-XI(3))
      AN(4) = ONE/EIGHT*(ONE-XI(1))*(ONE+XI(2))*(ONE-XI(3))
      AN(5) = ONE/EIGHT*(ONE-XI(1))*(ONE-XI(2))*(ONE+XI(3))
      AN(6) = ONE/EIGHT*(ONE+XI(1))*(ONE-XI(2))*(ONE+XI(3))
      AN(7) = ONE/EIGHT*(ONE+XI(1))*(ONE+XI(2))*(ONE+XI(3))
      AN(8) = ONE/EIGHT*(ONE-XI(1))*(ONE+XI(2))*(ONE+XI(3))
      
C     Derivatives of shape functions respect to local coordinates
      DO I=1,8
        DO J=1,3
            dNdxi(I,J) =  ZERO
        END DO
      END DO
      dNdxi(1,1) =  MONE/EIGHT*(ONE-XI(2))*(ONE-XI(3))
      dNdxi(1,2) =  MONE/EIGHT*(ONE-XI(1))*(ONE-XI(3))
      dNdxi(1,3) =  MONE/EIGHT*(ONE-XI(1))*(ONE-XI(2))
      dNdxi(2,1) =  ONE/EIGHT*(ONE-XI(2))*(ONE-XI(3))
      dNdxi(2,2) =  MONE/EIGHT*(ONE+XI(1))*(ONE-XI(3))
      dNdxi(2,3) =  MONE/EIGHT*(ONE+XI(1))*(ONE-XI(2))
      dNdxi(3,1) =  ONE/EIGHT*(ONE+XI(2))*(ONE-XI(3))
      dNdxi(3,2) =  ONE/EIGHT*(ONE+XI(1))*(ONE-XI(3))
      dNdxi(3,3) =  MONE/EIGHT*(ONE+XI(1))*(ONE+XI(2))
      dNdxi(4,1) =  MONE/EIGHT*(ONE+XI(2))*(ONE-XI(3))
      dNdxi(4,2) =  ONE/EIGHT*(ONE-XI(1))*(ONE-XI(3))
      dNdxi(4,3) =  MONE/EIGHT*(ONE-XI(1))*(ONE+XI(2))
      dNdxi(5,1) =  MONE/EIGHT*(ONE-XI(2))*(ONE+XI(3))
      dNdxi(5,2) =  MONE/EIGHT*(ONE-XI(1))*(ONE+XI(3))
      dNdxi(5,3) =  ONE/EIGHT*(ONE-XI(1))*(ONE-XI(2))
      dNdxi(6,1) =  ONE/EIGHT*(ONE-XI(2))*(ONE+XI(3))
      dNdxi(6,2) =  MONE/EIGHT*(ONE+XI(1))*(ONE+XI(3))
      dNdxi(6,3) =  ONE/EIGHT*(ONE+XI(1))*(ONE-XI(2))
      dNdxi(7,1) =  ONE/EIGHT*(ONE+XI(2))*(ONE+XI(3))
      dNdxi(7,2) =  ONE/EIGHT*(ONE+XI(1))*(ONE+XI(3))
      dNdxi(7,3) =  ONE/EIGHT*(ONE+XI(1))*(ONE+XI(2))
      dNdxi(8,1) =  MONE/EIGHT*(ONE+XI(2))*(ONE+XI(3))
      dNdxi(8,2) =  ONE/EIGHT*(ONE-XI(1))*(ONE+XI(3))
      dNdxi(8,3) =  ONE/EIGHT*(ONE-XI(1))*(ONE+XI(2))
      
      RETURN
      END
C      
C Subroutine UMAT  : 
C Dummy material
C
C ==============================================================
C !!! NOTE: N_ELEM has to be changed according to the UEL !!!!!
C ==============================================================
C
       SUBROUTINE UMAT(STRESS,STATEV,DDSDDE,SSE,SPD,SCD,
     1 RPL,DDSDDT,DRPLDE,DRPLDT,STRAN,DSTRAN,
     2 TIME,DTIME,TEMP,DTEMP,PREDEF,DPRED,MATERL,NDI,NSHR,NTENS,
     3 NSTATV,PROPS,NPROPS,COORDS,DROT,PNEWDT,CELENT,
     4 DFGRD0,DFGRD1,NOEL,NPT,KSLAY,KSPT,KSTEP,KINC)
C
      INCLUDE 'ABA_PARAM.INC'
C
       CHARACTER*80 CMNAME
       DIMENSION STRESS(NTENS),STATEV(NSTATV),
     1 DDSDDE(NTENS,NTENS),
     2 DDSDDT(NTENS),DRPLDE(NTENS),
     3 STRAN(NTENS),DSTRAN(NTENS),TIME(2),PREDEF(1),DPRED(1),
     4 PROPS(NPROPS),COORDS(3),DROT(3,3),DFGRD0(3,3),DFGRD1(3,3)
C 
       PARAMETER (ONE=1.0,TWO=2.0,THREE=3.0,SIX=6.0, HALF=0.5,
     1 N_ELEM=1,NSTV=28)
       DATA NEWTON,TOLER/40,1.D-6/ 
C       
       COMMON/KUSER/USRVAR(N_ELEM,NSTV,8)
C 
C ----------------------------------------------------------- 
C          Material properties
C ----------------------------------------------------------- 
C          PROPS(1) - Young's modulus 
C          PROPS(2) - Poisson ratio 
C ----------------------------------------------------------- 
C
C	Elastic properties
C
       EMOD=PROPS(1)
       ENU=PROPS(2)
       EG=EMOD/(TWO*(ONE+ENU))
       EG2=EG*TWO
       ELAM=EG2*ENU/(ONE-TWO*ENU)
C
C	Stiffness tensor
C
       DO K1=1, NTENS
        DO K2=1, NTENS
         DDSDDE(K2, K1)=0.0
        END DO
       END DO
C
       DO K1=1, NDI
        DO K2=1, NDI
         DDSDDE(K2, K1)=ELAM
        END DO
        DDSDDE(K1, K1)=EG2+ELAM
       END DO
C
       DO K1=NDI+1, NTENS
        DDSDDE(K1, K1)=EG
       END DO
C
C	Calculate Stresses
C
       DO K1=1, NTENS
        DO K2=1, NTENS
         STRESS(K2)=STRESS(K2)+DDSDDE(K2, K1)*DSTRAN(K1)
        END DO
       END DO
C
       NELEMAN=NOEL-TWO*N_ELEM
       IF (NPT.EQ.3) THEN
        NPT=4
       ELSEIF (NPT.EQ.4) THEN
        NPT=3
       ENDIF
       IF (NPT.EQ.7) THEN
        NPT=8
       ELSEIF (NPT.EQ.8) THEN
        NPT=7
       ENDIF
       
       DO I=1,NSTATV
        STATEV(I)=USRVAR(NELEMAN,I,NPT)
       END DO
       
       RETURN
       END      
      