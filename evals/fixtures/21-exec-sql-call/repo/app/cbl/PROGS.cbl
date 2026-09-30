       IDENTIFICATION DIVISION.
       PROGRAM-ID. PROGS.
       PROCEDURE DIVISION.
           EXEC SQL
               CALL MYPROC(:WS-X)
           END-EXEC.
           GOBACK.
