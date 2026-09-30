# 00 Summary

Assessment of the CardDemo tree for modernization. Extractor version 0.2.0 read 44 COBOL programs, 62 copybooks, 55 JCL jobs, 6 procs, 21 BMS maps, one Control-M file and 9 shell scripts, and built a graph of 543 nodes and 1,224 edges (analysis field edge_counts).

## Scoping answers

All three answers came as flags, so nothing was asked and no defaults applied.

| Question | Answer | Source | Confidence | Evidence |
|---|---|---|---|---|
| Target state | refactor | flag `--target refactor` | high | inference |
| What must not break | daily transaction posting, the account and card master refresh, and the transaction report | flag `--must-not-break` | high | inference |
| Runtime telemetry | none | flag `--telemetry none` | high | inference |

No defaults applied. With telemetry none, every dead-code claim is provisional (`modernization-assessment/05-dead-code.md`).

Where the three must-not-break items land in the tree:

| Item you named | Units | Wave | Confidence | Evidence |
|---|---|---|---|---|
| Daily transaction posting | job:POSTTRAN, CBTRN02C | 5 | high | `app/jcl/POSTTRAN.jcl:23`, `app/cbl/CBTRN02C.cbl:256` |
| The account and card master refresh | job:ACCTFILE, job:CARDFILE. The refresh wrapper labels them Refresh Account Master file and Refresh Card Master | 5 | medium | `scripts/remote_refresh.sh:16`, `scripts/remote_refresh.sh:19` |
| The transaction report | job:TRANREPT, proc:TRANREPT, CBTRN03C, and CORPT00C which submits the proc from CICS | 5 | medium | `app/jcl/TRANREPT.jcl:1`, `app/cbl/CORPT00C.cbl:94` |

Each maps to a unit. Two map thinly. The tree names the refresh jobs only in developer FTP wrappers, and names TRANREPT in no scheduler at all. Questions 2 and 3 below.

## The plan

Seven waves, in `modernization-assessment/03-waves.md` and `modernization-assessment/waves.json`. The plan keeps the extractor's seven families and makes two changes: job:CREADB2 moves from wave 1 to wave 7 because it runs DB2 DDL, and job:TXT2PDF1 moves from wave 4 to wave 5 because it converts the statement file that wave 5 writes. No wave has high confidence. Waves 1 and 4 are chores, and wave 5 is the largest and least safe: it holds all three must-not-break items and 14 of the 29 high-high units (`modernization-assessment/risks.json:2`).

Estimate: 179 to 312 engineer-weeks, low confidence, all of it inference (`modernization-assessment/04-estimate.md`).

## Largest risk

The definition of correct for the daily posting cycle is not in any one place, and the order of the jobs decides what the transaction master contains. Four artifacts give four different orders: the Control-M daily folder never runs posting, the CA-7 listing runs it after an IMS job and without a backup, and the two wrapper scripts differ from each other (`app/scheduler/CardDemo.controlm:5`, `app/scheduler/CardDemo.ca7:70`, `scripts/run_posting.sh:26`, `scripts/run_full_batch.sh:47`). Depending on which runs, the master is copied and emptied (`app/jcl/TRANBKP.jcl:40`), opened for output and refilled by CBTRN02C (`app/cbl/CBTRN02C.cbl:256`), rebuilt from generation (0) of a backup base (`app/jcl/COMBTRAN.jcl:24`), and the report job writes to that same base (`app/jcl/TRANREPT.jcl:33`). No abend marks a wrong generation, and CBTRN02C itself has arithmetic that truncates and a reject that is set and never written (`app/cbl/CBTRN02C.cbl:187`, `app/cbl/CBTRN02C.cbl:556`). A port that gets every program right can still lose or repeat a day of transactions. The plan mitigates it with a data facade, a scheduler bridge and a generation catalog before wave 5 (`modernization-assessment/03-waves.md`).

## Open Questions

For the client's own engineers. There are nineteen, plus the unparsed files and limits below.

1. Which scheduler runs the daily posting cycle in production: the Control-M daily folder, the CA-7 chain, or the FTP wrapper scripts? They disagree about the order and about whether TRANBKP runs (`app/scheduler/CardDemo.controlm:5`, `app/scheduler/CardDemo.ca7:70`, `scripts/run_full_batch.sh:47`).
2. Is the transaction master meant to hold only one cycle's postings? TRANBKP empties it, CBTRN02C opens it for output and COMBTRAN rebuilds it. Where is transaction history kept (`app/jcl/TRANBKP.jcl:40`, `app/cbl/CBTRN02C.cbl:256`, `app/jcl/COMBTRAN.jcl:48`)?
3. What runs the account and card master refresh and the transaction report in production? The refresh jobs appear only in developer FTP wrappers, TRANREPT in no scheduler. Does the reload of the account master overwrite what online users changed (`scripts/remote_refresh.sh:17`, `app/jcl/TRANREPT.jcl:1`, `app/cbl/COACTUPC.cbl:573`)?
4. Where does the DATEPARM file come from, and can its date range differ from the range the sort step uses? No program or job in the tree writes it (`app/jcl/TRANREPT.jcl:73`, `app/cbl/CBTRN03C.cbl:173`).
5. Does the report job's backup generation ever get read by COMBTRAN as generation (0)? Has that misfired (`app/jcl/TRANREPT.jcl:33`, `app/jcl/COMBTRAN.jcl:24`)?
6. Is the CA-7 listing current and in production? It names two jobs with no JCL in the tree and it runs POSTTRAN after CBPAUP0J (`app/scheduler/CardDemo.ca7:216`, `app/scheduler/CardDemo.ca7:70`).
7. Three writers create keys in the transaction file: the feed id, online highest-plus-one, and the interest date string. What guarantees they never collide (`app/cbl/CBTRN02C.cbl:425`, `app/cbl/COBIL00C.cbl:217`, `app/cbl/CBACT04C.cbl:476`)?
8. Who calls the MQ services COACCT01 and CODATE01, and what must the pending-authorization subsystem keep doing? Should it be ported at all (`app/app-vsam-mq/cbl/COACCT01.cbl:115`, `app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:956`)?
9. What does COBDATFT do for each type code, and is anything else assembler-based (`app/cbl/CBACT01C.cbl:231`, `app/asm/COBDATFT.asm:17`)?
10. Program COCRDSEC, run by CICS transaction CDV1, has no source in the tree. What does it do (`app/csd/CARDDEMO.CSD:388`)?
11. Does CBTRN01C ever run? Nothing in the tree names it (`app/cbl/CBTRN01C.cbl:23`).
12. Does CBIMPORT run? Its program selects a DD its JCL never maps (`app/cbl/CBIMPORT.cbl:63`, `app/jcl/CBIMPORT.jcl:22`).
13. CREASTMT has a corrupt JCL line, and TXT2PDF1 runs a REXX exec that is not in the tree. Do statements run in production (`app/jcl/CREASTMT.JCL:90`, `app/jcl/TXT2PDF1.JCL:31`)?
14. The report base is defined with two different generation limits. Which is live (`app/jcl/DEFGDGB.jcl:37`, `app/jcl/REPTFILE.jcl:27`)?
15. Are the fixed 2022 dates in INTCALC and TRANREPT overridden in production, and how (`app/jcl/INTCALC.jcl:22`, `app/jcl/TRANREPT.jcl:43`)?
16. Sign-on compares a clear-text password, and one FTP job holds a host and login in clear text. Which of these must the port fix, and who owns the authentication design (`app/cbl/COSGN00C.cbl:223`, `app/jcl/FTPJCL.JCL:33`)?
17. The posting limit test stores its sum in nine digits while balances hold ten. Has an over-limit transaction ever been accepted because of it (`app/cbl/CBTRN02C.cbl:187`)?
18. Which of the 27 jobs that no scheduler I could read names are still used, especially DALYREJS and DEFGDGB, which posting depends on (`modernization-assessment/05-dead-code.md`)?
19. COACTUPC and COTRTUPC use COPY with REPLACING, which the extractor does not apply. Does any replaced field change behavior (`app/cbl/COACTUPC.cbl:3208`, `app/app-transaction-type-db2/cbl/COTRTUPC.cbl:1358`)?

## Files the extractor did not parse

Each is an open question. None is a footnote.

| File or group | What it holds | Question | Confidence | Evidence |
|---|---|---|---|---|
| `app/scheduler/CardDemo.ca7` | CA-7 job and trigger listing, 570 lines. I read it by hand | Is it the production scheduler, and is it current? It is the only place CREASTMT, PRTCATBL and the READ jobs are chained, and the only place POSTTRAN follows CBPAUP0J | medium | `app/scheduler/CardDemo.ca7:18` |
| `app/app-authorization-ims-db2-mq/dcl/AUTHFRDS.dcl`, `app/app-transaction-type-db2/dcl/DCLTRCAT.dcl`, `app/app-transaction-type-db2/dcl/DCLTRTYP.dcl` | DB2 DCLGEN members | Do the host variables match the tables | low | inference |
| `app/app-authorization-ims-db2-mq/ddl/AUTHFRDS.ddl`, `app/app-authorization-ims-db2-mq/ddl/XAUTHFRD.ddl`, `app/app-transaction-type-db2/ddl/TRNTYCAT.ddl`, `app/app-transaction-type-db2/ddl/TRNTYPE.ddl`, `app/app-transaction-type-db2/ddl/XTRNTYCAT.ddl`, `app/app-transaction-type-db2/ddl/XTRNTYPE.ddl` | DB2 DDL, six files | What constraints, indexes and keys exist | low | inference |
| `app/app-authorization-ims-db2-mq/ims/DBPAUTP0.dbd`, `app/app-authorization-ims-db2-mq/ims/DBPAUTX0.dbd`, `app/app-authorization-ims-db2-mq/ims/PADFLDBD.DBD`, `app/app-authorization-ims-db2-mq/ims/PASFLDBD.DBD` | IMS database definitions, four files | Segment layout, keys and secondary indexes of the authorization database | low | inference |
| `app/app-authorization-ims-db2-mq/ims/DLIGSAMP.PSB`, `app/app-authorization-ims-db2-mq/ims/PAUTBUNL.PSB`, `app/app-authorization-ims-db2-mq/ims/PSBPAUTB.psb`, `app/app-authorization-ims-db2-mq/ims/PSBPAUTL.psb` | IMS program specification blocks, four files | Which program may read or change which segments | low | inference |
| `app/app-transaction-type-db2/ctl/DB2CREAT.ctl` and six others in that folder, `app/ctl/REPROCT.ctl` | Control cards, eight files. REPROCT is a plain REPRO. The DB2 ones create and load tables | Do the DB2 cards match the DDL | medium | `app/ctl/REPROCT.ctl:15`, `app/app-transaction-type-db2/ctl/DB2CREAT.ctl:35` |
| `app/asm/COBDATFT.asm`, `app/asm/MVSWAIT.asm` | Assembler date formatter and timer | Full behavior, and are there callers I did not see | medium | `app/asm/COBDATFT.asm:17`, `app/asm/MVSWAIT.asm:19` |
| `app/maclib/ASMWAIT.mac`, `app/maclib/COCDATFT.mac` | Assembler macros for the two modules | Same | low | inference |

## Extractor limits that touch this system

From `meta.limits` in `graph.json`. Each says what the extractor could not see, and where it bites here.

| Limit | Touches this system | Confidence | Evidence |
|---|---|---|---|
| COBOL is read as fixed format. Free format is not parsed | No. Every source file parsed | high | analysis field meta.files_seen |
| COPY REPLACING is not applied | Yes. COACTUPC uses it seven times and COTRTUPC once | high | `app/cbl/COACTUPC.cbl:3208`, `app/app-transaction-type-db2/cbl/COTRTUPC.cbl:1358` |
| A variable call target resolves only from VALUE clauses and literal MOVEs in the same program | Yes. 28 computed calls, bounded by hand | high | `app/cbl/COMEN01C.cbl:185`, `modernization-assessment/02-coupling.md:101` |
| A called subprogram gets no DDs from its caller's step | Yes. CBSTM03B has four unmapped DDs | high | `app/cbl/CBSTM03B.CBL:31` |
| SORT and most in-stream cards are not read | Yes. The report, statement, category listing and combine jobs use fixed offsets | high | `app/jcl/TRANREPT.jcl:41`, `app/jcl/CREASTMT.JCL:53`, `app/jcl/COMBTRAN.jcl:28` |
| The program a step runs is read only from PARM for DFSRRC00 and from RUN PROGRAM for IKJEFT01 | Yes. TXT2PDF1 runs a REXX exec under IKJEFT1B | high | `app/jcl/TXT2PDF1.JCL:24` |
| IF, THEN, ELSE and COND= are not modeled | Yes. TRANBKP's define step is skipped if an earlier step ends with a code above 4 | high | `app/jcl/TRANBKP.jcl:51` |
| Nested PROC calls and JCL inside a COBOL literal make no edge | Yes. TRANREPT calls REPROC, CORPT00C embeds a job | high | `app/proc/TRANREPT.prc:21`, `app/cbl/CORPT00C.cbl:94` |
| RETURN TRANSID, START and SEND MAP are not edges | Yes. All online flows | high | `app/cbl/COSGN00C.cbl:99` |
| Only Control-M XML and shell wrappers are read as schedulers | Yes. CA-7 is not read | high | `app/scheduler/CardDemo.ca7:18` |
| DCB, LRECL and RECFM are not read | Yes. A report line of 133 and a reject record of 430 are not compared with the layouts | high | `app/jcl/TRANREPT.jcl:78`, `app/jcl/POSTTRAN.jcl:36` |
| A contract edge is high when both sides copy one layout | Yes. CBTRN03C copies CVTRA05Y and reads through a private split | high | `app/cbl/CBTRN03C.cbl:63` |
| LINK and XCTL are both call edges and control flow is not modeled | Yes. XCTL never returns, which matters for the menu cycle | high | `app/cbl/COMEN01C.cbl:185` |

## What else is in this folder

| File | Holds |
|---|---|
| `modernization-assessment/01-inventory.md` | Inventory, generated |
| `modernization-assessment/02-coupling.md` | Coupling argument and the computed calls |
| `modernization-assessment/02a-edge-tables.md` | Every edge, generated |
| `modernization-assessment/03-waves.md`, `modernization-assessment/waves.json` | The wave plan |
| `modernization-assessment/03a-wave-seed.md`, `modernization-assessment/03a-waves-draft.json` | The extractor's seed, generated |
| `modernization-assessment/04-estimate.md` | Estimate |
| `modernization-assessment/05-dead-code.md`, `modernization-assessment/dead-code.json` | Dead code register |
| `modernization-assessment/05a-dead-code-candidates.md` | The extractor's candidates, generated |
| `modernization-assessment/06-test-strategy.md` | Oracle, normalization, deviation register |
| `modernization-assessment/risks.json` | Two-axis scores for 99 units |
| `modernization-assessment/graph.json` | The facts |
