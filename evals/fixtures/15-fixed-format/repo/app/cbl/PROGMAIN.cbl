      * CALL 'GHOSTONE' inside a comment is not a call
      * COPY GHOSTCPY.
      /  CALL 'GHOSTTWO' after a form feed slash
       IDENTIFICATION DIVISION.
       PROGRAM-ID. PROGMAIN.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       COPY REAL1.
       COPY
           REAL2.
       COPY REAL3 REPLACING ==:X:== BY ==WS==.
       PROCEDURE DIVISION.
       MAIN-PARA.
           DISPLAY 'A LONG MESSAGE THAT KEEPS GOING UNTIL COLUMN 72 THEN
      -    ' CALL PROGGHOST FAILED'.
           call 'PROGLOW'.
           CALL 'PROGTWO' USING
               WS-A
               WS-B.
           DISPLAY 'SEQ AREA TRAP'.                                     CALL 'Z'
           GOBACK.
