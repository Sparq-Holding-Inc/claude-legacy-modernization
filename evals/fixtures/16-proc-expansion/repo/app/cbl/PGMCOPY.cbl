       IDENTIFICATION DIVISION.
       PROGRAM-ID. PGMCOPY.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT IN-F ASSIGN TO INFILE.
           SELECT OUT-F ASSIGN TO OUTFILE.
       DATA DIVISION.
       FILE SECTION.
       FD  IN-F.
       01  IN-REC              PIC X(80).
       FD  OUT-F.
       01  OUT-REC             PIC X(80).
       PROCEDURE DIVISION.
           OPEN INPUT IN-F.
           OPEN OUTPUT OUT-F.
           GOBACK.
