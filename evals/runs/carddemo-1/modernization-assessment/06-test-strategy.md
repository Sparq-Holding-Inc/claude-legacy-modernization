# 06 Test strategy

"Correct" here means: for the inputs this system actually sees, the new implementation produces the same outputs as the old one, and where it does not, someone decided that on purpose and wrote it down.

The tree holds some datasets, but not a usable oracle. Under `app/data/ASCII/dailytran.txt:1` and `app/data/EBCDIC` there are 300 sample daily transactions and 50 sample accounts, in ASCII and EBCDIC. That is seed data for a demo. It has no archived generations, no reports and no job output. The oracle has to come from the client's system: archived generations, job logs and reports, captured traffic. The list of what to ask for is at the end.

## The oracle for each wave

| Wave | Oracle, strongest first | What to ask the client for | Evidence |
|---|---|---|---|
| 1 Operations utilities | Job logs and return codes from past runs. Weak by nature: these jobs change state (CICS files open or closed, a CSD updated) and produce little output. Characterization tests are provisional | Job logs and SMF records for CLOSEFIL, OPENFIL and the FTP job for the last 12 months | `app/jcl/CLOSEFIL.jcl:26` |
| 2 Read-only batch extracts | Parallel run on a frozen copy of the masters. The programs are deterministic and read-only, so this is cheap | A copy of ACCTDATA, CARDDATA, CARDXREF and CUSTDATA from one date, and the output files from the legacy run on it | `app/jcl/READACCT.jcl:32` |
| 3 Sign-on, menus and read-only screens | Captured screen traffic replayed against both systems. Fallback is characterization tests, marked provisional | CICS journals or terminal logs covering a month | `app/cbl/COSGN00C.cbl:223` |
| 4 Build and file-transfer support | None needed for the retired build jobs. For TXT2PDF1 compare the text to PDF conversion on archived statements | Archived statement text and PDF pairs | `app/jcl/TXT2PDF1.JCL:33` |
| 5 Nightly batch cycle | Parallel run. Both systems process the same daily file and every output is diffed: transaction master, account master, category balances, rejects, interest transactions, report and statements. Then archived generations as golden masters | Copies of DALYTRAN.PS for a month including month-end, and the GDGs TRANSACT.BKUP, DALYREJS, SYSTRAN and TRANREPT | `app/jcl/POSTTRAN.jcl:23` |
| 6 Online writers | Captured production traffic replay, then compare the resulting master records after each replay | CICS journals with inputs and outputs, and a before and after copy of the masters | `app/cbl/COACTUPC.cbl:4100` |
| 7 Authorization, DB2 reference and MQ services | Shadow traffic: replay recorded MQ requests against both and diff the replies. Then unload the IMS database with the existing unload job and compare | MQ message logs for authorizations, an IMS unload, DB2 table extracts | `app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:400` |

Two of these are weaker than the rest and are marked so: wave 1 and the fallback in wave 3. Wave 5 is where a parallel run pays for itself, because the three must-not-break items are there and a wrong number is silent. Ask early whether the legacy system can stay up beside the new one. Teams often assume it cannot.

## Normalization spec

Every line is a claim that a difference does not matter. Each needs a named person to sign it.

| Item | What is ignored or converted | Why it is safe, and what could hide behind it | Evidence |
|---|---|---|---|
| Process timestamp | TRAN-PROC-TS on posted transactions and TRAN-ORIG-TS on interest transactions, taken from the run clock | It changes every run. Compare that the field is a valid DB2-format timestamp, not its value | `app/cbl/CBTRN02C.cbl:692`, `app/cbl/CBACT04C.cbl:613` |
| Interest transaction id | The 16-character id is the PARM date plus a six-digit counter | Not noise. The date is a fixed literal in the job, so treat the id as data, not as a run id | `app/jcl/INTCALC.jcl:22`, `app/cbl/CBACT04C.cbl:476` |
| Report headers and page breaks | Page size is 20 and totals fall on a page break | Compare the line content and the totals. The break position is part of the report and should match | `app/cbl/CBTRN03C.cbl:131`, `app/cbl/CBTRN03C.cbl:282` |
| Money | No tolerance. Compare in a decimal type | Amounts are zoned decimal with two places, and the target must not use floats. A mismatch is a defect | `app/cpy/CVTRA05Y.cpy:10`, `app/cpy/CVACT01Y.cpy:7` |
| Packed fields | COMP-3 counters and amounts compare by value, not by bytes | Counters in the report and amounts in authorization use packed storage | `app/cbl/CBTRN03C.cbl:129`, `app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:62` |
| Record order | Keep KSDS key order. Do not sort in ASCII | A KSDS returns records in EBCDIC key order and downstream programs read by key or in sequence. A port that sorts in ASCII changes order silently | `app/jcl/COMBTRAN.jcl:28`, `app/jcl/TRANREPT.jcl:41` |
| Sort semantics | The report sorts by card number as a zoned decimal and COMBTRAN sorts by id as characters | Confirm whether ties keep input order. A sort that is not stable changes the report | `app/jcl/TRANREPT.jcl:41`, `app/jcl/COMBTRAN.jcl:28` |
| Padding and low values | Trailing spaces and fill bytes in fixed-width records | The reject record is 430 bytes with a trailer, and transaction records carry 20 filler bytes. Decide which fill counts | `app/cbl/CBTRN02C.cbl:83`, `app/cbl/CBTRN02C.cbl:84`, `app/cpy/CVTRA05Y.cpy:18` |
| Code page | EBCDIC to ASCII for text fields | Only characters, not sort order or numeric zone bytes. The sample data exists in both, which lets the converter be tested | `app/data/ASCII/dailytran.txt:1` |
| Generation numbers | GDG generation numbers G0001V00 and so on | Ignore the number. Do not ignore which generation a job reads (0 or +1) | `app/jcl/COMBTRAN.jcl:24` |
| REDEFINES branches | Export records that share bytes | Test every record type. The export layout has a redefined record area | `app/cpy/CVEXPORT.cpy:24` |

Run order is not normalized. The temporal edges in `modernization-assessment/02a-edge-tables.md` are the orders the harness must keep. The ones that matter most: TRANBKP before POSTTRAN, POSTTRAN before INTCALC, INTCALC before the second TRANBKP, and that before COMBTRAN (`scripts/run_full_batch.sh:47`, `scripts/run_full_batch.sh:51`, `scripts/run_full_batch.sh:55`, `scripts/run_full_batch.sh:58`).

## Cases to add beyond replay

Replay covers the common path. These are the paths that fail at close.

| Case | Why it needs its own test | Evidence |
|---|---|---|
| Month-end interest run with the PARM date used for ids | The interest job takes a fixed date literal. A rerun with the same literal writes ids that can collide with an earlier run when COMBTRAN loads them. Test a second month | `app/jcl/INTCALC.jcl:22`, `app/jcl/COMBTRAN.jcl:26` |
| Interest rate missing for a group | The program falls back to a group named DEFAULT. Test an account whose group has no rate | `app/cbl/CBACT04C.cbl:437` |
| Interest rounding | The divide by 1200 is not rounded. Test balances that leave fractions of a cent | `app/cbl/CBACT04C.cbl:464` |
| Expired account | The expiry check compares dates as text. Test the last day, the day after, and a leap day | `app/cbl/CBTRN02C.cbl:414` |
| Over the limit and expired together | Both codes apply and the second overwrites the first. Test the reject file | `app/cbl/CBTRN02C.cbl:410`, `app/cbl/CBTRN02C.cbl:417` |
| Balance above nine digits | The work balance is narrower than the stored balances. Test 10-digit values | `app/cbl/CBTRN02C.cbl:187` |
| Transaction with no cross-reference entry, no account, or no category balance | Rejects 100 and 101, and the create branch for a missing category balance | `app/cbl/CBTRN02C.cbl:385`, `app/cbl/CBTRN02C.cbl:503` |
| Empty daily file | The posting job on zero records. The return code is 4 only when something is rejected | `app/cbl/CBTRN02C.cbl:230` |
| Card with more than ten transactions, and more than 51 cards | Statements use a table of 51 cards by 10 transactions. What happens on overflow is not known. Find out on the old system first | `app/cbl/CBSTM03A.CBL:226`, `app/cbl/CBSTM03A.CBL:228` |
| Report window | The batch job has a fixed 2022 window and the online screen inserts dates. Test both, including a window with no rows | `app/jcl/TRANREPT.jcl:43`, `app/cbl/CORPT00C.cbl:94` |
| Report run between backup and reload | Run the report between TRANBKP and COMBTRAN and check what COMBTRAN reads | `app/jcl/TRANREPT.jcl:33`, `app/jcl/COMBTRAN.jcl:24` |
| Refresh discards online updates | Update an account online, run the account master refresh, and check what is left | `app/jcl/ACCTFILE.jcl:25`, `app/jcl/ACCTFILE.jcl:61` |
| Bad data already in the masters | Records that break their own rules must behave as they do now, not as a sane system would | `inference` |
| Two people submit the online report at once | Both write a generation. Test the generation numbers and the backup | `app/cbl/CORPT00C.cbl:517` |
| Fiscal year-end | The monthly interest run and the transaction reload at year-end. No year-end special case is visible in the source, so ask whether one exists | `inference` |

## Deviation register

Nothing differs without a row. These are the candidates I found while reading, and every one is unapproved. "New behavior" is a proposal for the client to decide, not a decision. Rows DR-01 to DR-05 and DR-07 look like defects. The others are changes the client may want. None should be reproduced or changed without a signature.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| DR-01 | The report adds the last transaction amount a second time at end of file and never writes the last account's total line | Totals count each transaction once and every account gets its total | Looks like a defect. Confirm against an archived report before deciding | pending | Report totals, and anyone who reconciles to them | `app/cbl/CBTRN03C.cbl:200`, `app/cbl/CBTRN03C.cbl:206` |
| DR-02 | A transaction dated outside the report window ends the read loop, and totals are not written | Skip the record and keep reading | The sort step already filters the window, so this may never fire. Confirm | pending | Report completeness | `app/cbl/CBTRN03C.cbl:177`, `app/jcl/TRANREPT.jcl:47` |
| DR-03 | When a transaction is both over the limit and after account expiry, only the expiry reason is kept | Keep both reasons, or keep the first | The reject file hides one cause | pending | Anyone reading the reject file | `app/cbl/CBTRN02C.cbl:410`, `app/cbl/CBTRN02C.cbl:417` |
| DR-04 | The work balance is 9 digits before the point and the stored balances are 10 | Use the wider size | High-order digits can be lost in the limit check | pending | Over-limit decisions on very large balances | `app/cbl/CBTRN02C.cbl:187`, `app/cpy/CVACT01Y.cpy:7` |
| DR-05 | An account rewrite that fails sets reason code 109, but the transaction is still written and nothing records the code | Fail the run or write a reject | A posted transaction with no balance update | pending | Account balances against the transaction master | `app/cbl/CBTRN02C.cbl:556` |
| DR-06 | Interest is truncated, never rounded | Reproduce first. Change only if the business wants rounding | Money. Keep the legacy result until approved | pending | Monthly interest on every account | `app/cbl/CBACT04C.cbl:464` |
| DR-07 | The account extract replaces a zero cycle debit with 2525.00 | Pass the real value | Looks like a test artifact left in an extract | pending | Anyone using the account extract output | `app/cbl/CBACT01C.cbl:237` |
| DR-08 | Passwords are 8 characters, stored and compared in clear, and shown back on the screen | Hash and never display | Security | pending | Every sign-on, and the user admin screens | `app/cbl/COSGN00C.cbl:223`, `app/cbl/COUSR02C.cbl:169`, `app/cpy/CSUSR01Y.cpy:21` |
| DR-09 | Each report run writes a new TRANSACT.BKUP generation and the group keeps only five | The report does not touch the backup generations | A read-only report should not change backups | pending | The transaction reload after the backup | `app/jcl/TRANREPT.jcl:33`, `app/jcl/DEFGDGB.jcl:26` |
| DR-10 | An FTP job holds the host, user and password in the JCL | Managed file transfer with a secret store. Rotate the credential | Security. The value is not reproduced here | pending | The one file that job sends | `app/jcl/FTPJCL.JCL:33` |

## Exit bar for each wave

A wave is done when all four hold.

- The replay or parallel-run diff is clean, apart from the normalization spec and the deviation register.
- Every case in the table above that touches the wave passes.
- The harness is under version control and runs in CI.
- The deviation register is signed by someone with the authority to sign it.

Not when the port compiles. Not when it passes tests written beside the port, because those hold the porter's understanding, which is the thing under test.

For waves 5 to 7 add one more condition: the run order of the jobs matches the order the client confirms as production (see Open Questions in `modernization-assessment/00-summary.md`).

## What to ask the client to supply

- **Archived generations.** TRANSACT.BKUP, DALYREJS, SYSTRAN, TRANSACT.COMBINED and TRANREPT, and the daily transaction file for each day. The group limit is five (`app/jcl/DEFGDGB.jcl:26`), so older ones have to come from a backup.
- **Job logs and SMF records** for 12 months. They show which programs ran and their return codes, and they are the telemetry that firms up `modernization-assessment/05-dead-code.md`.
- **Files sent to partners.** The FTP job shows one (`app/jcl/FTPJCL.JCL:40`). Whatever left the building is already a specification of the format.
- **CICS journals and transaction logs** for replay of waves 3 and 6, and MQ message logs for wave 7.
- **Printed reports and statements** the business kept, especially the transaction report and the month-end statements.

## Keep the harness after cutover

The comparison harness becomes the regression suite of the modernized system. Budget for its upkeep. The tests that compare the two systems are the only executable statement of what this system does.
