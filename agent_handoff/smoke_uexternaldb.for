C ======================================================================
C Minimal Abaqus/Standard user-subroutine smoke fixture.
C Purpose: exercise compiler/linker/startup only; no physics is modified.
C ======================================================================
      SUBROUTINE UEXTERNALDB(LOP,LRESTART,TIME,DTIME,KSTEP,KINC)
      INCLUDE 'ABA_PARAM.INC'
      DIMENSION TIME(2)
      RETURN
      END
