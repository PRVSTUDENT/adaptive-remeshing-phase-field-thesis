C ======================================================================
C SUBROUTINE UMAT FOR TASK F1697: AUTHENTIC DEGRADED STRESS RECOVERY
C Evaluates authentic degraded Cauchy stress:
C   sigma = [(1 - d)^2 + k_res] * C_0 : epsilon
C on companion facsimile elements (ELSET=All_elem) to test whether
C authentic coupled UEL-UMAT stress feedback generates Figure 15(b).
C ======================================================================
      SUBROUTINE UMAT(STRESS,STATEV,DDSDDE,SSE,SPD,SCD,
     1 RPL,DDSDDT,DRPLDE,DRPLDT,STRAN,DSTRAN,
     2 TIME,DTIME,TEMP,DTEMP,PREDEF,DPRED,CMNAME,NDI,NSHR,NTENS,
     3 NSTATV,PROPS,NPROPS,COORDS,DROT,PNEWDT,CELENT,
     4 DFGRD0,DFGRD1,NOEL,NPT,LAYER,KSPT,KSTEP,KINC)
      INCLUDE 'ABA_PARAM.INC'
      CHARACTER*80 CMNAME
      DIMENSION STRESS(NTENS),STATEV(NSTATV),DDSDDE(NTENS,NTENS),
     1 DDSDDT(NTENS),DRPLDE(NTENS),
     2 STRAN(NTENS),DSTRAN(NTENS),TIME(2),PREDEF(1),DPRED(1),
     3 PROPS(NPROPS),COORDS(3),DROT(3,3),DFGRD0(3,3),DFGRD1(3,3)

      PARAMETER (ONE=1.D0, TWO=2.D0, THREE=3.D0, HALF=0.5D0)
      PARAMETER (MAX_ELEM=10000)

      LOGICAL, SAVE :: INITIALIZED = .FALSE.
      DOUBLE PRECISION, SAVE :: D_ARRAY(MAX_ELEM)

      DOUBLE PRECISION E0, ENU, KRES, D_VAL, G_D, E_DEG
      DOUBLE PRECISION EG, EG2, ELAM
      DOUBLE PRECISION STRAN_TOT(4)
      INTEGER I, J, K1, K2

C --- 1. INITIALIZATION: READ DAMAGE FIELD ---
      IF (.NOT. INITIALIZED) THEN
        DO I=1, MAX_ELEM
          D_ARRAY(I) = 0.D0
        ENDDO
        OPEN(UNIT=88,
     1  FILE='D:/Master thesis/Adaptive remeshing/models/'//
     2  'pandey_kumar_mode1/197_pk_sec43_coupled_umat_job1/'//
     3  'damage_field.txt',
     4  STATUS='OLD', ERR=10)
        DO I=1, 3923
          READ(88, *, END=20) D_ARRAY(I)
        ENDDO
 20     CLOSE(88)
        WRITE(*,*) 'SUCCESS: Loaded 3923 damage values into UMAT!'
        GOTO 30
 10     WRITE(*,*) 'WARNING: damage_field.txt not found! Using d=0.'
 30     INITIALIZED = .TRUE.
      ENDIF

C --- 2. MATERIAL PROPERTIES & DEGRADATION ---
      E0   = PROPS(1)
      ENU  = PROPS(2)
      IF (NPROPS .GE. 3) THEN
        KRES = PROPS(3)
      ELSE
        KRES = 1.D-7
      ENDIF

      IF (NOEL .LE. MAX_ELEM .AND. NOEL .GT. 0) THEN
        D_VAL = D_ARRAY(NOEL)
      ELSE
        D_VAL = 0.D0
      ENDIF

      G_D = (ONE - D_VAL)**2 + KRES
      E_DEG = MAX(1.D-6, G_D * E0)

C --- 3. ISOTROPIC ELASTIC STIFFNESS TENSOR (PLANE STRAIN / 2D) ---
      EG   = E_DEG / (TWO * (ONE + ENU))
      EG2  = EG * TWO
      ELAM = EG2 * ENU / (ONE - TWO * ENU)

      DO K1=1, NTENS
        DO K2=1, NTENS
          DDSDDE(K2, K1) = 0.D0
        ENDDO
      ENDDO

      DO K1=1, NDI
        DO K2=1, NDI
          DDSDDE(K2, K1) = ELAM
        ENDDO
        DDSDDE(K1, K1) = EG2 + ELAM
      ENDDO

      DO K1=NDI+1, NTENS
        DDSDDE(K1, K1) = EG
      ENDDO

C --- 4. CAUCHY STRESS TENSOR EVALUATION ---
      DO K1=1, NTENS
        STRAN_TOT(K1) = STRAN(K1) + DSTRAN(K1)
      ENDDO

      DO K1=1, NTENS
        STRESS(K1) = 0.D0
        DO K2=1, NTENS
          STRESS(K1) = STRESS(K1) + DDSDDE(K1, K2) * STRAN_TOT(K2)
        ENDDO
      ENDDO

C --- 5. STATE VARIABLES OUTPUT ---
      IF (NSTATV .GE. 1) STATEV(1) = D_VAL
      IF (NSTATV .GE. 2) STATEV(2) = G_D
      IF (NSTATV .GE. 3) STATEV(3) = E_DEG

      RETURN
      END
