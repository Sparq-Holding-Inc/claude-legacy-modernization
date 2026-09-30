# 00 Summary

Assessment of the CardDemo tree (COBOL, CICS, JCL, VSAM, with DB2, IMS and MQ modules) for modernization.

## Scoping answers

| Question | Answer | Source |
|---|---|---|
| Target state | refactor | Given as `--target refactor` |
| What must not break | Daily transaction posting, the account and card master refresh, and the transaction report | Given as `--must-not-break` |
| Runtime telemetry | none | Given as `--telemetry none` |

All three came as flags, so no defaults applied.

The three must-not-break items each map to units in the tree. The mapping is by job comment and wrapper label, so it is inference the client should confirm. It is in `modernization-assessment/03-waves.md`.

With telemetry none, every dead-code claim is provisional (`modernization-assessment/05-dead-code.md`).

## Result

- **Waves: 7.** Cut from the extractor's seed with 17 recorded deviations, in four groups: CORPT00C and its proc into the batch window because it submits JCL held inside the COBOL; CLOSEFIL, OPENFIL and WAITSTEP into the batch window because they bracket its jobs; TXT2PDF1 into the batch window because it reads what the statement job writes; and CREADB2 into the DB2 wave. Wave 5, the batch window, has 55 units and is not cut. Evidence: `app/cbl/CORPT00C.cbl:94`, `scripts/run_posting.sh:13`, `app/jcl/TXT2PDF1.JCL:33`, `app/app-transaction-type-db2/jcl/CREADB21.jcl:40`.
- **Estimate:** about 115 to 250 engineer-weeks, as ranges per wave, from judgment and not from measured velocity (`modernization-assessment/04-estimate.md`).
- **The single largest risk:** the correctness of the daily posting chain rests on an order and on destructive steps that live only in shell wrappers and an unparsed CA-7 listing, and nothing in the code enforces it. TRANBKP backs up the transaction master, deletes it and redefines it empty, and its delete step has no COND, so a failed backup does not stop it. CBTRN02C then opens the master for OUTPUT, which only works on the empty file. The wrapper also reloads the account master and the category balances from flat files before posting, and nothing in the tree regenerates those flat files. A port that reorders or replaces these jobs can lose the day's transaction history or silently reset balances, and no error would say so until reconciliation. Evidence: `app/jcl/TRANBKP.jcl:37`, `app/jcl/TRANBKP.jcl:51`, `app/cbl/CBTRN02C.cbl:256`, `scripts/run_posting.sh:16`, `scripts/run_posting.sh:26`.

## Waves at a glance

| Wave | Name | Units | Blast radius | Confidence | Evidence |
|---|---|---|---|---|---|
| 1 | Environment and utility jobs | 6 | low | medium | `app/jcl/CBADMCDJ.jcl:27`, `app/jcl/FTPJCL.JCL:33` |
| 2 | Read-only batch extracts | 10 | low | medium | `app/cbl/CBACT01C.cbl:231`, `app/cbl/CBIMPORT.cbl:63` |
| 3 | Sign-on, menu and read-only screens | 8 | high | medium | `app/cbl/COSGN00C.cbl:223`, `app/cbl/COMEN01C.cbl:184` |
| 4 | Build and reference-data backup jobs | 10 | low | medium | `app/jcl/DEFGDGD.jcl:28`, `app/jcl/INTRDRJ1.JCL:17` |
| 5 | Batch window: posting, master refresh, transaction report, interest, statements | 55 | high | medium | `app/jcl/POSTTRAN.jcl:23`, `app/jcl/ACCTFILE.jcl:25`, `app/jcl/TRANREPT.jcl:23` |
| 6 | Online updates | 9 | high | medium | `app/cbl/COACTUPC.cbl:4066`, `app/cbl/COBIL00C.cbl:212` |
| 7 | Authorization and transaction-type subsystems (IMS, MQ, DB2) | 25 | high | low | `app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:35` |

## Other findings the client should know about

| Finding | Confidence | Evidence |
|---|---|---|
| The report totals look wrong in the code: at end of file the last transaction amount is added again, and the last account total is never written. This is a reading of the code and needs a real report to confirm. | medium | `app/cbl/CBTRN03C.cbl:198`, `app/cbl/CBTRN03C.cbl:181` |
| The batch report job has a fixed 2022 date window, and the interest job a fixed 2022 run date. | high | `app/jcl/TRANREPT.jcl:42`, `app/jcl/INTCALC.jcl:22` |
| The online report request builds JCL text and submits it through a queue, so a batch job is started from an online program. | high | `app/cbl/CORPT00C.cbl:94`, `app/cbl/CORPT00C.cbl:517` |
| The report's type descriptions come from a DB2 table by way of an unload and a load, so a must-not-break output depends on the DB2 wave. | high | `app/app-transaction-type-db2/jcl/TRANEXTR.jcl:72`, `app/jcl/TRANTYPE.jcl:54` |
| One entry point (CSD transaction CDV1) names a program with no source in the tree. | high | `app/csd/CARDDEMO.CSD:388` |
| The extractor's dormancy rule cannot fire on a history that starts in 2022, so the empty dormant list is not a finding. | high | analysis `dormant_years` and `as_of` |
| Sign-on compares a stored password field directly. Replace it, do not port it. | medium | `app/cbl/COSGN00C.cbl:223` |
| An FTP job carries an address and login lines in its input stream. Values are not repeated here. | medium | `app/jcl/FTPJCL.JCL:33` |
| The extractor's god module list (COPAUS0C, COTRN00C, COTRN01C) is a rank artifact of a small graph. The real hubs are the menu and sign-on programs and COACTUPC. | medium | analysis `fan_in`, analysis `god_modules` |

## Open Questions

For the client's engineers. The first three matter most.

1. **Which scheduler and which order run the daily posting in production?** The parsed Control-M file does not contain POSTTRAN. The CA-7 listing, which the extractor could not parse, appears to chain CLOSEFIL, CBPAUP0J, POSTTRAN, WAITSTEP, OPENFIL. Four shell wrappers run different sequences. Is `scripts/run_posting.sh` production or a demo reset? Evidence: `app/scheduler/CardDemo.ca7:70`, `scripts/run_posting.sh:26`, `scripts/run_full_batch.sh:47`.
2. **Where does DALYTRAN.PS come from, and where are ACCTDATA.PS and TCATBALF.PS regenerated?** Nothing in the tree writes DALYTRAN.PS. If the posting flow reloads the account master and category balances from flat files before each run, balances posted yesterday are replaced unless something regenerates the files. Evidence: `app/jcl/POSTTRAN.jcl:30`, `scripts/run_posting.sh:16`, `scripts/run_posting.sh:19`, `app/jcl/ACCTFILE.jcl:57`, `app/jcl/TCATBALF.jcl:57`.
3. **Can you supply an oracle?** One full business cycle of real daily transaction files and the masters before and after, the report, reject and backup generations beyond the last five (the catalog keeps five), and CICS journals or SMF records for 12 months. Evidence: `app/catlg/LISTCAT.txt:1535`, `app/catlg/LISTCAT.txt:1637`.
4. Which report is the must-not-break one, the scheduled batch job (fixed window 2022-01-01 to 2022-07-06) or the on-demand one started by CORPT00C? And does the printed grand total count the last transaction twice? Evidence: `app/jcl/TRANREPT.jcl:42`, `app/cbl/CORPT00C.cbl:220`, `app/cbl/CBTRN03C.cbl:198`.
5. Do TRANREPT and DEFCUST run as written? Both reuse a step name, and the member TRANREPT.prc names its own proc REPROC on its first line and then calls proc REPROC. Evidence: `app/jcl/TRANREPT.jcl:23`, `app/jcl/TRANREPT.jcl:37`, `app/jcl/DEFCUST.jcl:22`, `app/jcl/DEFCUST.jcl:32`, `app/proc/TRANREPT.prc:1`.
6. Who supplies the run date for the monthly interest job? The PARM is fixed at 2022-07-18. Evidence: `app/jcl/INTCALC.jcl:22`, `app/scheduler/CardDemo.controlm:69`.
7. Are XREFFILE and CUSTFILE part of the account and card master refresh? They sit in the same wrapper sequence, and posting validates through the cross reference. Evidence: `scripts/remote_refresh.sh:22`, `scripts/remote_refresh.sh:25`, `app/cbl/CBTRN02C.cbl:380`.
8. Which GDG definition is current? REPTFILE says limit 10, DEFGDGB says limit 5 with SCRATCH, and the catalog snapshot shows limit 5 and, for TRANSACT.BKUP, NOSCRATCH. Evidence: `app/jcl/REPTFILE.jcl:27`, `app/jcl/DEFGDGB.jcl:25`, `app/catlg/LISTCAT.txt:1637`.
9. Is the DB2 table TRANSACTION_TYPE the master of the type data, and does the weekly unload run in production? The DB2 create job is submitted with TYPRUN=SCAN. Evidence: `app/app-transaction-type-db2/jcl/TRANEXTR.jcl:72`, `app/app-transaction-type-db2/jcl/CREADB21.jcl:2`, `app/scheduler/CardDemo.controlm:58`.
10. Which of the 27 unscheduled jobs not in the CA-7 listing still run? Does anything run CBTRN01C? Is proc TRANREPT started only by CORPT00C? Evidence: `app/scheduler/CardDemo.ca7:43`, `app/cbl/CBTRN01C.cbl:29`, `app/cbl/CORPT00C.cbl:94`.
11. What is CSD transaction CDV1, and where is the source of its program COCRDSEC? Evidence: `app/csd/CARDDEMO.CSD:388`, `app/csd/CARDDEMO.CSD:390`.
12. The FTP job holds login lines in the input stream. Who owns them, and have they been rotated? Evidence: `app/jcl/FTPJCL.JCL:33`.

### Files the extractor did not parse

These are gaps, not footnotes. Each needs an answer or a file.

| File or group | Reason | Effect here | Evidence |
|---|---|---|---|
| `app/app-authorization-ims-db2-mq/dcl/AUTHFRDS.dcl` and 2 more DCLGEN files | Not read | DB2 column layouts for wave 7 are unknown. | `app/app-authorization-ims-db2-mq/dcl/AUTHFRDS.dcl:1` |
| `app/app-authorization-ims-db2-mq/ddl/AUTHFRDS.ddl` and 5 more DDL files | Not read | DB2 table definitions for wave 7 are unknown. | `app/app-authorization-ims-db2-mq/ddl/AUTHFRDS.ddl:1` |
| `app/app-authorization-ims-db2-mq/ims/DBPAUTP0.dbd` and 3 more DBD files | Not read | The IMS database structure is unknown. | `app/app-authorization-ims-db2-mq/ims/DBPAUTP0.dbd:1` |
| `app/app-authorization-ims-db2-mq/ims/DLIGSAMP.PSB` and 3 more PSB files | Not read | The IMS program views are unknown. | `app/app-authorization-ims-db2-mq/ims/DLIGSAMP.PSB:1` |
| `app/app-transaction-type-db2/ctl/DB2CREAT.ctl` and 7 more control card files | Not read | The REPRO statement used by TRANBKP, TRANREPT and PRTCATBL is in one of them. The DB2 create and load steps are in the others. | `app/ctl/REPROCT.ctl:15`, `app/app-transaction-type-db2/ctl/DB2CREAT.ctl:1` |
| `app/asm/COBDATFT.asm` and `app/asm/MVSWAIT.asm` | Not read | CBACT01C calls COBDATFT and COBSWAIT calls MVSWAIT. | `app/cbl/CBACT01C.cbl:231`, `app/cbl/COBSWAIT.cbl:38` |
| `app/maclib/ASMWAIT.mac` and `app/maclib/COCDATFT.mac` | Not read | Macros for the two assembler routines. | `app/maclib/ASMWAIT.mac:1` |
| `app/scheduler/CardDemo.ca7` | CA-7 listing, not Control-M XML, not parsed | The schedule of POSTTRAN and 7 other jobs is in it. | `app/scheduler/CardDemo.ca7:70` |
| `app/catlg/LISTCAT.txt` and `app/data/` | Not listed as parsed or unparsed | Not read by the extractor at all. I used them by hand for the oracle. | `app/catlg/LISTCAT.txt:1528` |

### Extractor limits that touch this system

| Limit (from `meta.limits`) | How it bites here | Evidence |
|---|---|---|
| A variable call target is resolved only from VALUE clauses and literal MOVEs in the same program. | 28 computed calls stay open, and 25 of them return to a menu or a caller. | analysis `unresolved_dynamic`, `app/cbl/COMEN01C.cbl:184` |
| A called subprogram gets no DDs from its caller's JCL step. | CBSTM03B looks as if its four files are unmapped. | `app/cbl/CBSTM03B.CBL:31` |
| SORT and most in-stream control cards are not read. | The report chain and COMBTRAN order by byte offsets that the extractor does not see. | `app/jcl/TRANREPT.jcl:41`, `app/jcl/COMBTRAN.jcl:28` |
| The program a step runs is read only for DFSRRC00 and for IKJEFT01 with a RUN PROGRAM card. | CREADB2 looks like a job with no DB2 access. | `app/app-transaction-type-db2/jcl/CREADB21.jcl:40` |
| IF/THEN/ELSE and COND are not modeled. | TRANBKP's unguarded delete is invisible. | `app/jcl/TRANBKP.jcl:37`, `app/jcl/TRANBKP.jcl:51` |
| Nested PROC calls are not followed, and JCL text inside a COBOL literal makes no edge. | The report proc calls REPROC, and CORPT00C submits a batch job. | `app/proc/TRANREPT.prc:21`, `app/cbl/CORPT00C.cbl:94` |
| RETURN TRANSID, START and SEND MAP are not edges. | Screen to screen flow is only partly visible. | `app/cbl/COMEN01C.cbl:184` |
| Only Control-M XML and shell wrappers are read as schedulers. | The CA-7 listing is not parsed. | `app/scheduler/CardDemo.ca7:1` |
| DCB, LRECL and RECFM are not read. | Record lengths on DDs are not compared with copybooks. | `app/jcl/POSTTRAN.jcl:36` |
| A contract edge is high when both sides COPY the same layout. | All 62 are high, and that is shared copybook, not proven equal. | analysis `edge_counts` |

## The files

| File | What it holds |
|---|---|
| `modernization-assessment/01-inventory.md` | Generated inventory |
| `modernization-assessment/02-coupling.md` | Coupling argument and the dependency-cartographer pass |
| `modernization-assessment/02a-edge-tables.md` | Generated edge tables |
| `modernization-assessment/03-waves.md` and `modernization-assessment/waves.json` | The wave plan |
| `modernization-assessment/04-estimate.md` | The estimate |
| `modernization-assessment/05-dead-code.md` and `modernization-assessment/dead-code.json` | Dead code, three buckets |
| `modernization-assessment/06-test-strategy.md` | Equivalence strategy and Deviation Register |
| `modernization-assessment/risks.json` | Scores on two axes for 99 units |
| `modernization-assessment/graph.json` | The extracted graph |
