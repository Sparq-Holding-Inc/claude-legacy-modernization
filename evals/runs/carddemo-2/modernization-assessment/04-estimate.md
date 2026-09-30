# 04 Estimate

Target state: refactor. Unit of effort: engineer-weeks, one engineer working with Claude Code, including building the equivalence harness for the wave. The numbers are ranges from a judgment method, not from measured velocity. Nobody has ported anything in this tree yet, so waves 1 and 2 exist to measure velocity, and this estimate should be redone after wave 2.

## Method

What moves the estimate, in the order I weighted it:

1. Coupling edges that cross the wave boundary, and how many other waves touch the same datasets (not lines of code).
2. Whether a behavioral oracle exists. Here the tree has vendor sample data and a catalog listing, and no production inputs or outputs. See `modernization-assessment/06-test-strategy.md`.
3. God modules and very large programs inside the wave.
4. How much business logic sits in the database or in JCL utility steps rather than in code.
5. Whether the team can read COBOL, JCL, IMS and DB2. I assumed one engineer who can.

Lines of code set the floor only. Every range below is my judgment (inference) from those five factors and the counts in this table.

## Per wave

| Wave | Units | Programs and lines | Boundary edges | Range (engineer-weeks) | Main driver | Confidence | Evidence |
|---|---|---|---|---|---|---|---|
| 1. Environment and utility jobs | 6 | 0 programs | none | 1 to 3 | Most of these are retired, not ported. The FTP job needs its credentials handled. | medium | `app/jcl/FTPJCL.JCL:33`, inference |
| 2. Read-only batch extracts | 10 | 5 programs, 1,084 lines | 7 contract | 4 to 8 | Building the read access layer over the masters, which later waves reuse. CBIMPORT has an unmapped output DD. | medium | `app/cbl/CBIMPORT.cbl:63`, analysis of `modernization-assessment/waves.json` |
| 3. Sign-on, menu and read-only screens | 8 | 8 programs, 2,793 lines | 25 call, 14 contract | 12 to 24 | The routing shim in front of the menu table, replacing the password check, and 7 BMS screens. | medium | `app/cbl/COMEN01C.cbl:184`, `app/cbl/COSGN00C.cbl:223` |
| 4. Build and reference-data backup jobs | 10 | 0 programs | none | 2 to 4 | Retire the build jobs, port DEFGDGD. | medium | `app/jcl/DEFGDGD.jcl:28`, inference |
| 5. Batch window | 55 | 8 programs, 3,569 lines, 47 jobs, procs and wrappers | 26 contract, 3 call, 1 temporal | 30 to 70 | Building the oracle and the decimal and collating sequence handling. The code is only 3,569 lines, but three must-not-break items sit here. | medium | `app/cbl/CBTRN02C.cbl:256`, `app/jcl/TRANBKP.jcl:37` |
| 6. Online updates | 9 | 9 programs, 7,972 lines | 18 call, 33 contract | 30 to 60 | COACTUPC is 3,368 lines with 43 REDEFINES and 51 GO TO. Changing the owner of four masters. | medium | `app/cbl/COACTUPC.cbl:4066` |
| 7. Authorization and transaction-type subsystems | 25 | 13 programs, 7,071 lines, 12 jobs and procs | 12 contract, 4 call, 1 temporal | 35 to 80 | IMS, MQ and DB2 files that the extractor did not read. Least known wave. | low | `app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:35`, inference |
| Total | 123 | 43 programs | | about 115 to 250 | Ranges add, they do not multiply. | low | inference |

Calendar time depends on team size. The dependency order in `modernization-assessment/03-waves.md` allows waves 3 and 4 to overlap with wave 2, and wave 7 to start once wave 5 is done, so a team of three or four could plausibly finish in a third to half of the total engineer-weeks.

## The assumptions the ranges are most sensitive to

Each is a claim that can be checked and that moves an estimate if false.

| Assumption | If it is false | Evidence |
|---|---|---|
| One record level access facade over ACCTDATA, CARDDATA, CUSTDATA, CARDXREF, TRANSACT and USRSEC, built in wave 2, serves waves 3, 5 and 6. ACCTDATA is touched by units in five waves, and CUSTDATA also in five. | If each wave needs its own access path, waves 3, 5 and 6 each add about 4 to 8 weeks. | analysis `data_hubs` |
| The client can supply at least one full business cycle of real daily transaction files and the masters before and after, not only the vendor sample of 300 transactions. | Wave 5 has to be tested from synthetic cases and roughly doubles. | `app/data/ASCII/dailytran.txt:300` |
| The order of the batch window is what the four shell wrappers say. | The CA-7 listing shows POSTTRAN triggered by CBPAUP0J, which no wrapper contains. If production uses another order, the wave 5 harness must be rebuilt from the real schedule, adding 4 to 8 weeks. | `app/scheduler/CardDemo.ca7:43`, `app/scheduler/CardDemo.ca7:70` |
| The client wants the legacy report and posting behavior reproduced, including the last transaction being counted twice in the report totals. | Each behavior the client wants fixed needs a Deviation Register row and a downstream check. Add 1 to 2 weeks per behavior. There are at least four candidates in `modernization-assessment/06-test-strategy.md`. | `app/cbl/CBTRN03C.cbl:198` |
| Someone on the team can read IMS DBD and PSB, DB2 DDL and the control cards. | Wave 7 goes to the top of its range or past it, and its confidence stays low. | `app/app-authorization-ims-db2-mq/ims/DBPAUTP0.dbd:1` |

## Where Claude Code helps and where it does not

Mechanical, with a harness in place:

- The sequential readers CBACT02C, CBACT03C and CBCUS01C, about 130 lines each. They are transliteration. Evidence: `app/cbl/CBACT02C.cbl:1`.
- The small screens: COUSR01C, COUSR02C, COUSR03C, COADM01C and COMEN01C, which are table dispatch and file access. Evidence: `app/cbl/COUSR01C.cbl:1`.
- Copybooks to typed record definitions, IDCAMS DELETE, DEFINE and REPRO jobs to load scripts, and the JCL job graph to an orchestrator definition. Evidence: `app/jcl/ACCTFILE.jcl:25`.
- The SORT and merge steps of COMBTRAN and TRANREPT, once the keys are written down. Evidence: `app/jcl/COMBTRAN.jcl:22`.

Not mechanical, because the intent is in the code and nowhere else:

- The validation order and overwrite in CBTRN02C (reason 103 overwrites 102), the overlimit arithmetic and the string date comparison. Evidence: `app/cbl/CBTRN02C.cbl:403`, `app/cbl/CBTRN02C.cbl:414`.
- Interest with no rounding and the DEFAULT disclosure group fallback in CBACT04C. Evidence: `app/cbl/CBACT04C.cbl:437`, `app/cbl/CBACT04C.cbl:464`.
- The report's date windows (a hardcoded SORT window and a DATEPARM window) and its totals. Evidence: `app/jcl/TRANREPT.jcl:42`, `app/cbl/CBTRN03C.cbl:173`.
- Transaction id generation by browsing to the last key, and the pseudo-conversational state in the COMMAREA. Evidence: `app/cbl/COBIL00C.cbl:212`.
- Record lock and update handling in COACTUPC. Evidence: `app/cbl/COACTUPC.cbl:2607`.
- ALTER and the TIOT walk in CBSTM03A, and everything in IMS and MQ. Evidence: `app/cbl/CBSTM03A.CBL:300`.

## What would change the total most

A production oracle (wave 5) and the real schedule (CA-7) would each remove more uncertainty than any amount of source reading. Ask for both before committing to a number.
