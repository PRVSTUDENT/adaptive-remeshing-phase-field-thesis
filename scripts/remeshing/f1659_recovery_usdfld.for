C=======================================================================
C     AUXILIARY USDFLD USER SUBROUTINE FOR F1659 STRESS RECOVERY PILOT
C     Prescribes material integration-point damage without nodal smearing
C=======================================================================
      SUBROUTINE USDFLD(FIELD,STATEV,PNEWDT,DIRECT,T,CELENT,
     1 TIME,DTIME,CMNAME,ORNAME,NFIELD,NSTATV,NOEL,NPT,LAYER,
     2 KSPT,KSTEP,KINC,NDI,NSHR,COORD,JMAC,JMATYP,MATLAYO,LACCFLA)
      INCLUDE 'ABA_PARAM.INC'
      CHARACTER*80 CMNAME,ORNAME
      CHARACTER*3  FLGRAY(15)
      DIMENSION FIELD(NFIELD),STATEV(NSTATV),DIRECT(3,3),
     1 T(3,3),TIME(2)
      DIMENSION ARRAY(15),JARRAY(15),JMAC(*),JMATYP(*),
     2 COORD(*)

C     Lookup storage: max 5000 elements, 4 IPs each
      INTEGER, PARAMETER :: MAX_ELEM = 5000
      INTEGER, PARAMETER :: MAX_NPT = 4
      REAL*8, SAVE :: LOOKUP_D(MAX_ELEM, MAX_NPT)
      REAL*8, SAVE :: LOOKUP_X(MAX_ELEM, MAX_NPT)
      REAL*8, SAVE :: LOOKUP_Y(MAX_ELEM, MAX_NPT)
      LOGICAL, SAVE :: TABLE_LOADED = .FALSE.
      INTEGER :: IEID, INPT, ISTAT, NUM_LOADED
      REAL*8 :: DX, DY, DIST, XVAL, YVAL, DVAL, GVAL
      CHARACTER*256 :: LINE, FNAME

C     Load table once on first invocation
      IF (.NOT. TABLE_LOADED) THEN
        DO IEID = 1, MAX_ELEM
          DO INPT = 1, MAX_NPT
            LOOKUP_D(IEID, INPT) = -1.0D0
            LOOKUP_X(IEID, INPT) = 0.0D0
            LOOKUP_Y(IEID, INPT) = 0.0D0
          END DO
        END DO

        FNAME = 'D:\Master thesis\Adaptive remeshing\models\' //
     1          'pandey_kumar_mode1\176_method_a_plate_with_hole\' //
     2          'PK_HOLE_F1659_IP_DAMAGE_LOOKUP.txt'
        OPEN(UNIT=105, FILE=TRIM(FNAME), STATUS='OLD', 
     1       ACTION='READ', IOSTAT=ISTAT)
        IF (ISTAT .NE. 0) THEN
          WRITE(6,*) '*** ERROR [USDFLD]: Failed to open lookup file: ', 
     1               TRIM(FNAME)
          CALL XIT
        END IF

        NUM_LOADED = 0
 10     READ(105, '(A)', END=20) LINE
        IF (LINE(1:1) .EQ. '#' .OR. LEN_TRIM(LINE) .EQ. 0) GOTO 10
        READ(LINE, *, IOSTAT=ISTAT) IEID, INPT, XVAL, YVAL, DVAL, GVAL
        IF (ISTAT .EQ. 0) THEN
          IF (IEID .LE. MAX_ELEM .AND. INPT .LE. MAX_NPT) THEN
            LOOKUP_D(IEID, INPT) = DVAL
            LOOKUP_X(IEID, INPT) = XVAL
            LOOKUP_Y(IEID, INPT) = YVAL
            NUM_LOADED = NUM_LOADED + 1
          END IF
        END IF
        GOTO 10
 20     CLOSE(105)
        WRITE(6,*) '*** [USDFLD]: Successfully loaded lookup entries: ', 
     1             NUM_LOADED
        TABLE_LOADED = .TRUE.
      END IF

C     Check NOEL and NPT validity
      IF (NOEL .GT. MAX_ELEM .OR. NPT .GT. MAX_NPT) THEN
        WRITE(6,*) '*** ERROR [USDFLD]: NOEL or NPT exceeds bounds: ',
     1             NOEL, NPT
        CALL XIT
      END IF

      IF (LOOKUP_D(NOEL, NPT) .LT. 0.0D0) THEN
        WRITE(6,*) '*** ERROR [USDFLD]: Missing entry for element/IP: ',
     1             NOEL, NPT
        CALL XIT
      END IF

C     Coordinate verification (fail-closed if distance exceeds 10 um)
      DX = COORD(1) - LOOKUP_X(NOEL, NPT)
      DY = COORD(2) - LOOKUP_Y(NOEL, NPT)
      DIST = SQRT(DX*DX + DY*DY)
      IF (DIST .GT. 1.0D-2) THEN
        WRITE(6,*) '*** ERROR [USDFLD]: Coordinate mismatch for el/ip:'
     1             , NOEL, NPT, ' Dist: ', DIST
        CALL XIT
      END IF

C     Assign field variable 1 directly to material point
      FIELD(1) = LOOKUP_D(NOEL, NPT)

      RETURN
      END
