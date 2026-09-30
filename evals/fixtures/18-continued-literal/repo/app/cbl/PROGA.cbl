       IDENTIFICATION DIVISION.
       PROGRAM-ID. PROGA.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-NEXT-PGM             PIC X(8).
       PROCEDURE DIVISION.
       MAIN-PARA.
                                                              MOVE 'PROG
      -    'ONE' TO WS-NEXT-PGM.
           EXEC CICS XCTL
                PROGRAM(WS-NEXT-PGM)
           END-EXEC.
