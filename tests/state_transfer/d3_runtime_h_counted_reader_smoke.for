      PROGRAM D3HCOUNTEDSMOKE
      IMPLICIT NONE
      INTEGER N_ELEM,NIP,EXPECTED
      PARAMETER (N_ELEM=6400,NIP=4,EXPECTED=25600)
      LOGICAL SEEN
      DIMENSION SEEN(N_ELEM,NIP)
      INTEGER I,J,ELEM,IP,COUNT,IOS,IREC
      INTEGER FIRSTE,FIRSTIP,LASTE,LASTIP,MISSING
      DOUBLE PRECISION HVAL,HMIN,HMAX

      DO I=1,N_ELEM
        DO J=1,NIP
          SEEN(I,J)=.FALSE.
        END DO
      END DO
      COUNT=0
      FIRSTE=-1
      FIRSTIP=-1
      LASTE=-1
      LASTIP=-1
      HMIN=1.0D99
      HMAX=-1.0D99
      OPEN(UNIT=99,FILE='d3_transfer_h.dat',STATUS='OLD',
     1     ACTION='READ',IOSTAT=IOS)
      IF (IOS.NE.0) THEN
        WRITE(*,*) 'open error = true',IOS
        STOP 1
      ENDIF

      DO IREC=1,EXPECTED
        IOS=0
        READ(99,*,IOSTAT=IOS,END=900,ERR=910) ELEM,IP,HVAL
        IF (IOS.NE.0) GOTO 910
        IF (ELEM.LT.1 .OR. ELEM.GT.N_ELEM) THEN
          WRITE(*,*) 'range error = element',IREC,ELEM
          CLOSE(99)
          STOP 4
        ENDIF
        IF (IP.LT.1 .OR. IP.GT.NIP) THEN
          WRITE(*,*) 'range error = ip',IREC,ELEM,IP
          CLOSE(99)
          STOP 5
        ENDIF
        IF (SEEN(ELEM,IP)) THEN
          WRITE(*,*) 'duplicate key = true',IREC,ELEM,IP
          CLOSE(99)
          STOP 6
        ENDIF
        IF (HVAL.LT.0.D0) THEN
          WRITE(*,*) 'negative H = true',IREC,ELEM,IP,HVAL
          CLOSE(99)
          STOP 7
        ENDIF
        IF (COUNT.EQ.0) THEN
          FIRSTE=ELEM
          FIRSTIP=IP
        ENDIF
        LASTE=ELEM
        LASTIP=IP
        HMIN=MIN(HMIN,HVAL)
        HMAX=MAX(HMAX,HVAL)
        SEEN(ELEM,IP)=.TRUE.
        COUNT=COUNT+1
      END DO
      GOTO 920

 900  CONTINUE
      WRITE(*,*) 'premature EOF = true'
      WRITE(*,*) 'records = ',COUNT
      CLOSE(99)
      STOP 2

 910  CONTINUE
      WRITE(*,*) 'read error = true'
      WRITE(*,*) 'iostat = ',IOS
      WRITE(*,*) 'record = ',IREC
      WRITE(*,*) 'records = ',COUNT
      CLOSE(99)
      STOP 3

 920  CONTINUE
      CLOSE(99)
      MISSING=0
      DO I=1,N_ELEM
        DO J=1,NIP
          IF (.NOT.SEEN(I,J)) MISSING=MISSING+1
        END DO
      END DO
      IF (COUNT.NE.EXPECTED) THEN
        WRITE(*,*) 'count mismatch = true'
        WRITE(*,*) 'records = ',COUNT
        STOP 8
      ENDIF
      IF (MISSING.NE.0) THEN
        WRITE(*,*) 'missing keys = ',MISSING
        STOP 9
      ENDIF
      WRITE(*,*) 'records = ',COUNT
      WRITE(*,*) 'first key = ',FIRSTE,FIRSTIP
      WRITE(*,*) 'last key = ',LASTE,LASTIP
      WRITE(*,*) 'H min = ',HMIN
      WRITE(*,*) 'H max = ',HMAX
      WRITE(*,*) 'premature EOF = false'
      WRITE(*,*) 'read error = false'
      WRITE(*,*) 'duplicates = 0'
      WRITE(*,*) 'missing keys = 0'
      END
