       IDENTIFICATION DIVISION.
       PROGRAM-ID. PROGSQL.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
           EXEC SQL INCLUDE SQLCA END-EXEC.
           EXEC SQL INCLUDE DCLCUST END-EXEC.
       PROCEDURE DIVISION.
       MAIN-PARA.
           EXEC SQL
               SELECT CUST_NAME
                 INTO :WS-NAME
                 FROM CUSTOMER
                WHERE CUST_ID = :WS-ID
           END-EXEC.
           EXEC SQL
               UPDATE ORDERS
                  SET STATUS = 'X'
                WHERE ORDER_ID = :WS-OID
           END-EXEC.
           EXEC SQL
               INSERT INTO AUDIT_LOG (EVT) VALUES ('DONE')
           END-EXEC.
           EXEC SQL
               DELETE FROM STAGING WHERE BATCH_ID = :WS-BID
           END-EXEC.
           GOBACK.
