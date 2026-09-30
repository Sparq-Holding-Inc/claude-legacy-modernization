       IDENTIFICATION DIVISION.
       PROGRAM-ID. PROGA.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-IDX                  PIC 9.
       01  TBL-PGM-AREA.
           05  TBL-PGM             PIC X(8) OCCURS 3 TIMES.
       PROCEDURE DIVISION.
           MOVE 'PROGB' TO TBL-PGM(1).
           EXEC CICS LINK
                PROGRAM(TBL-PGM(WS-IDX))
           END-EXEC.
           EXEC CICS RETURN END-EXEC.
