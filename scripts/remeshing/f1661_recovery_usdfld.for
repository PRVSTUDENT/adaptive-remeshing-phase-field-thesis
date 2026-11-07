C=======================================================================
C     AUXILIARY USDFLD USER SUBROUTINE FOR F1661 STRESS RECOVERY
C     - Directly assigns material-point FIELD(1) from lookup table
C     - Strict runtime coordinate verification with 10 nm fail-closed check
C     - Logs runtime coordinates encountered during execution to file
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
      LOGICAL, SAVE :: LOG_OPENED = .FALSE.
      LOGICAL, SAVE :: LOGGED(MAX_ELEM, MAX_NPT)
      INTEGER, SAVE :: LOG_COUNT = 0
      REAL*8, SAVE :: RUNTIME_MAX_DIST = 0.0D0
      INTEGER :: IEID, INPT, ISTAT, NUM_LOADED
      REAL*8 :: DX, DY, DIST, XVAL, YVAL, DVAL, GVAL
      CHARACTER*256 :: LINE, FNAME, LOGNAME

C     Load table once on first invocation
      IF (.NOT. TABLE_LOADED) THEN
        DO IEID = 1, MAX_ELEM
          DO INPT = 1, MAX_NPT
            LOOKUP_D(IEID, INPT) = -1.0D0
            LOOKUP_X(IEID, INPT) = 0.0D0
            LOOKUP_Y(IEID, INPT) = 0.0D0
            LOGGED(IEID, INPT) = .FALSE.
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

C       Open runtime coordinate log
        LOGNAME = 'D:\Master thesis\Adaptive remeshing\models\' //
     1            'pandey_kumar_mode1\176_method_a_plate_with_hole\' //
     2            'PK_HOLE_F1661_RUNTIME_COORDS.txt'
        OPEN(UNIT=106, FILE=TRIM(LOGNAME), STATUS='REPLACE',
     1       ACTION='WRITE', IOSTAT=ISTAT)
        IF (ISTAT .EQ. 0) THEN
          WRITE(106, '(A)') '# NOEL NPT RUNTIME_X RUNTIME_Y ' //
     1                      'LOOKUP_X LOOKUP_Y DIST_MM'
          LOG_OPENED = .TRUE.
        END IF
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

C     Coordinate verification: STRICT 10 nm (1.0e-5 mm) FAIL-CLOSED CHECK
      DX = COORD(1) - LOOKUP_X(NOEL, NPT)
      DY = COORD(2) - LOOKUP_Y(NOEL, NPT)
      DIST = SQRT(DX*DX + DY*DY)
      IF (DIST .GT. 1.0D-5) THEN
        WRITE(6,*) '*** ERROR [USDFLD]: Coordinate mismatch for el/ip:'
     1             , NOEL, NPT, ' Dist: ', DIST
        CALL XIT
      END IF

      IF (DIST .GT. RUNTIME_MAX_DIST) THEN
        RUNTIME_MAX_DIST = DIST
      END IF

C     Log runtime coordinates (first encounter of each IP)
      IF (LOG_OPENED .AND. .NOT. LOGGED(NOEL, NPT)) THEN
        LOGGED(NOEL, NPT) = .TRUE.
        LOG_COUNT = LOG_COUNT + 1
        WRITE(106, '(I6,1X,I2,1X,E20.12,1X,E20.12,1X,E20.12,1X,E20.12,'
     1             // '1X,E14.6)') 
     2        NOEL, NPT, COORD(1), COORD(2),
     3        LOOKUP_X(NOEL, NPT), LOOKUP_Y(NOEL, NPT), DIST
        IF (LOG_COUNT .EQ. 11452) THEN
          WRITE(106, '(A,E14.6)') '# RUNTIME_MAX_DIST_MM = ', 
     1          RUNTIME_MAX_DIST
          FLUSH(106)
          CLOSE(106)
          LOG_OPENED = .FALSE.
          WRITE(6,*) '*** [USDFLD]: Logged all 11452 runtime IPs. ' //
     1               'Max Dist = ', RUNTIME_MAX_DIST
        END IF
      END IF

C     Assign field variable 1 directly to material point
      FIELD(1) = LOOKUP_D(NOEL, NPT)

      RETURN
      END
