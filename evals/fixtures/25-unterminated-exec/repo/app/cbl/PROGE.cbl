      * CALL 'GHOST' in a header comment after a byte order mark
       IDENTIFICATION DIVISION.
       PROGRAM-ID. PROGE.
       PROCEDURE DIVISION.
           CALL 'PROGF'.
           EXEC CICS LINK PROGRAM('LOST')
           GOBACK.
