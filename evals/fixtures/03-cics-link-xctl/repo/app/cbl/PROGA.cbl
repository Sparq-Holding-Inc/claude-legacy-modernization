       IDENTIFICATION DIVISION.
       PROGRAM-ID. PROGA.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  LIT-PGM-D               PIC X(8) VALUE 'PROGD'.
       01  WS-NEXT-PGM             PIC X(8).
       01  WS-ANY-PGM              PIC X(8).
       LINKAGE SECTION.
       01  DFHCOMMAREA             PIC X(8).
       PROCEDURE DIVISION.
       MAIN-PARA.
           EXEC CICS LINK
                PROGRAM('PROGB')
           END-EXEC.
           MOVE DFHCOMMAREA TO WS-ANY-PGM.
           EXEC CICS LINK
                PROGRAM(WS-ANY-PGM)
           END-EXEC.
           MOVE 'PROGC' TO WS-NEXT-PGM.
           EXEC CICS XCTL
                PROGRAM(WS-NEXT-PGM)
           END-EXEC.
           EXEC CICS XCTL
                PROGRAM(LIT-PGM-D)
           END-EXEC.
           EXEC CICS RETURN END-EXEC.
