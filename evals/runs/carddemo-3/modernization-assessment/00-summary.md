# 00 Summary

An assessment of the CardDemo mainframe sample (COBOL, CICS, JCL, VSAM, with DB2, IMS and MQ modules) for modernization. Scope: the whole work folder. Facts come from the extractor (`graph.json`). Judgment is mine, and every claim is cited or labeled inference. I read source, JCL and scheduler files. I did not run anything, so any statement about run-time behavior is inference until the harness in `06-test-strategy.md` confirms it.

## Scoping answers

| Question | Answer | Source |
|---|---|---|
| Target state | refactor | `--target refactor` |
| What must not break | daily transaction posting, the account and card master refresh, and the transaction report | `--must-not-break` |
| Runtime telemetry | none. Every dead-code claim is provisional. | `--telemetry none` |
| Defaults applied | no defaults applied. All three answers came as flags. | non-interactive run |

## What was assessed

44 COBOL programs (25 online, 17 batch, 2 subprograms), 62 copybooks, 55 JCL jobs, 6 procs, 21 BMS maps, 4 CSD files, 9 shell wrappers and one Control-M file. The extractor built 543 nodes and 1,224 edges: 318 call, 62 contract, 235 data, 476 include and 133 temporal. It found 99 entry points and 28 computed calls it could not resolve. Eight groups of files were not parsed (below).

## Wave count

Seven waves. The plan starts from the extractor's seed and deviates from it 18 times, each with a cited reason (`03-waves.md`).

| Wave | Name | Units | Blast radius | Confidence | Evidence |
|---|---|---|---|---|---|
| 1 | Batch brackets, GDG bases and utility definers | 17 | medium | medium | `app/jcl/CLOSEFIL.jcl:26` |
| 2 | Read-only extract and print batch | 15 | low | medium | `app/jcl/READACCT.jcl:32` |
| 3 | Sign-on, menu and read-only online screens | 7 | medium | medium | `app/cbl/COSGN00C.cbl:223` |
| 4 | Master data loaders and reference data jobs | 29 | high | medium | `scripts/remote_refresh.sh:16` |
| 5 | Daily posting, interest, transaction report and statements | 23 | high | medium | `app/jcl/POSTTRAN.jcl:23` |
| 6 | Online writers: accounts, cards, bill payment, transactions, users | 9 | high | medium | `app/cbl/COACTUPC.cbl:4066` |
| 7 | IMS, DB2 and MQ subsystem | 23 | high | low | `app/app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl:25` |

The effort range is 67 to 135 engineer-weeks, and waves 5, 6 and 7 are about three quarters of it (`04-estimate.md`). The estimate is most sensitive to whether a shared data facade is acceptable and to whether the client can supply real archived output.

## The single largest risk

**The daily posting cycle is not one program, and its shared masters are written from both sides of the batch and online split.** CBTRN02C posts the daily file into the account master, the category balances and the transaction master. Four programs write the account master (two batch, two online) and three write the transaction master, and 11 programs read each (`02-coupling.md`). The plan moves the batch writers in wave 5 and the online writers in wave 6, so for a period the same VSAM files have writers on two platforms. The posting program only works because of a protocol nobody wrote down: it opens the transaction master for output, so a separate backup job must empty that file first (`app/cbl/CBTRN02C.cbl:256`, `app/jcl/TRANBKP.jcl:40`). A later job rebuilds it. The account and category updates are zoned decimal with no rounding and no overflow check (`app/cbl/CBTRN02C.cbl:547`), and the CICS files carry no journal and no recovery (`app/csd/CARDDEMO.CSD:9`). A port can be correct line by line and still lose history or corrupt balances, and the failure would surface at the report or at the next statement, not at cutover. The legacy cycle also takes no snapshot of the account or category files before posting. It backs up only the transaction master, so the port has to add one to be able to roll back. The mitigation is one record-level data facade owning those files across waves 5 and 6, a pre-run snapshot, and a parallel run of a production daily file before wave 5 is signed off.

## Other findings for the steering committee

| Finding | Why it matters | Evidence |
|---|---|---|
| CA-7, Control-M and three shell wrappers hold four different orders of the same cycle. The CA-7 listing has an IMS purge job trigger posting. | Wave 5 depends on a wave 7 job, and nobody has said which order is live. | `app/scheduler/CardDemo.ca7:43`, `app/scheduler/CardDemo.ca7:70`, `scripts/run_full_batch.sh:47` |
| The transaction report has an online front (CORPT00C) that submits a job by writing JCL text into a queue. The extractor cannot see it. | The read-only screen is really the report trigger, and I moved it to wave 5. | `app/cbl/CORPT00C.cbl:94`, `app/cbl/CORPT00C.cbl:517` |
| The report loop appears to add the last amount twice and to stop at the first out-of-window record. | Both would change what finance reads. Inference from reading the code. | `app/cbl/CBTRN03C.cbl:197`, `app/cbl/CBTRN03C.cbl:173` |
| Three DB2 jobs and five programs (four IMS, one DB2) are hidden from the extractor in in-stream cards and driver parameters. | The seed filed the jobs as utilities and left the programs unplaced. They are subsystem work. | `app/app-transaction-type-db2/jcl/MNTTRDB2.jcl:30`, `app/app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl:25` |
| The tree holds seed data and no output of any run. GDG bases keep five generations. | The oracle for waves 5 and 6 has to be built or supplied. | `app/jcl/DEFGDGB.jcl:26`, `app/data/ASCII/dailytran.txt:1` |
| The interest job passes a fixed date to its program, which builds transaction ids from it. | Ids can repeat every run. Inference. | `app/jcl/INTCALC.jcl:22`, `app/cbl/CBACT04C.cbl:476` |

## Open Questions for the client's engineers

Numbered so they can be answered by number. Each cites what prompted it.

| # | Question | Evidence |
|---|---|---|
| 1 | Which schedule runs the daily cycle in production? Control-M has CLOSEFIL, TRANBKP, WAITSTEP and OPENFIL but not POSTTRAN. The CA-7 listing has CBPAUP0J triggering POSTTRAN. The wrappers order the jobs differently. Why does an IMS purge gate posting? | `app/scheduler/CardDemo.controlm:5`, `app/scheduler/CardDemo.ca7:70`, `scripts/run_posting.sh:26` |
| 2 | Who produces the daily transaction file, and in what layout? Nothing in the tree writes it. | `app/jcl/POSTTRAN.jcl:30` |
| 3 | Is the transaction master rebuilt every cycle on purpose? TRANBKP backs it up and deletes it before posting, and COMBTRAN reloads it. Is the reload the system of record for transaction history? | `app/jcl/TRANBKP.jcl:40`, `app/jcl/COMBTRAN.jcl:22` |
| 4 | Which path produces the transaction report finance uses: the online screen or the standalone job? The standalone job repeats a step name, fixes a 2022 date window, and is scheduled nowhere. What is in the DATEPARM dataset? | `app/jcl/TRANREPT.jcl:37`, `app/jcl/TRANREPT.jcl:43`, `app/jcl/TRANREPT.jcl:73` |
| 5 | Does finance expect the grand total to include the last transaction twice, and expect the report to stop early if the date windows disagree? If not, is that a known defect? | `app/cbl/CBTRN03C.cbl:200`, `app/cbl/CBTRN03C.cbl:177` |
| 6 | Is the PARM date in the interest job edited on every run? If not, do interest transaction ids repeat and does COMBTRAN drop them? | `app/jcl/INTCALC.jcl:22` |
| 7 | Was RECOVERY(NONE) and JOURNAL(NO) on every CICS file intended? The account update issues a rollback that cannot undo the earlier rewrite on such files. | `app/csd/CARDDEMO.CSD:9`, `app/cbl/COACTUPC.cbl:4100` |
| 8 | What is COCRDSEC? The CSD defines a program and a transaction (CDV1) for it and the tree has no source. | `app/csd/CARDDEMO.CSD:211`, `app/csd/CARDDEMO.CSD:390` |
| 9 | Did CBTRN01C ever run? Its header repeats CBTRN02C's description and nothing runs it. Which of the 27 jobs no scheduler names still run (CBEXPORT, CBIMPORT, TRANREPT and others)? Please supply 12 months of job logs or SMF. | `app/cbl/CBTRN01C.cbl:5`, analysis: `unscheduled_jobs` |
| 10 | Where are the generations older than five? Every GDG base keeps five and scratches the rest. Are there report and reject archives? | `app/jcl/DEFGDGB.jcl:26`, `app/jcl/DALYREJS.jcl:26` |
| 11 | Are the SDSF console commands in CLOSEFIL, OPENFIL, CARDFILE and CUSTFILE the only way the region is told to release the files? What is CICSAWSA in the target world? | `app/jcl/CLOSEFIL.jcl:26`, `app/jcl/CARDFILE.jcl:22` |
| 12 | Sign-on compares the password as plain text against an 8 character stored value. Is that the intended control, and who owns the user file? | `app/cbl/COSGN00C.cbl:223`, `app/cpy/CSUSR01Y.cpy:21` |
| 13 | Who consumes the two MQ programs and the authorization decision, and how fast does it have to answer? | `app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:400`, `app/app-vsam-mq/cbl/COACCT01.cbl:352` |
| 14 | The account master refresh reloads from a PS file. Where does that PS file come from, and does a refresh after a posting run discard posted balances on purpose? | `app/jcl/ACCTFILE.jcl:61`, `scripts/run_posting.sh:17` |

### Files the extractor did not parse

Each of these needs an answer or a hand review before wave 7 and before the estimate is trusted.

| Files | What they are | Ask | Evidence |
|---|---|---|---|
| 3 DCLGEN files (`app/app-authorization-ims-db2-mq/dcl/AUTHFRDS.dcl` and 2 more) | DB2 host structures | Confirm they match the DB2 tables the programs write. | `app/app-authorization-ims-db2-mq/dcl/AUTHFRDS.dcl:1` |
| 6 DDL files (`app/app-authorization-ims-db2-mq/ddl/AUTHFRDS.ddl` and 5 more) | DB2 table and index definitions | The real schema and any stored logic. | `app/app-authorization-ims-db2-mq/ddl/AUTHFRDS.ddl:1` |
| 4 IMS DBD files (`app/app-authorization-ims-db2-mq/ims/DBPAUTP0.dbd` and 3 more) | The IMS hierarchy | Segment layout and access paths. | `app/app-authorization-ims-db2-mq/ims/DBPAUTP0.dbd:1` |
| 4 IMS PSB files (`app/app-authorization-ims-db2-mq/ims/DLIGSAMP.PSB` and 3 more) | IMS program views | Which programs use which view. | `app/app-authorization-ims-db2-mq/ims/DLIGSAMP.PSB:1` |
| 8 control card files (`app/app-transaction-type-db2/ctl/DB2CREAT.ctl` and 7 more) | DB2 setup and unload control cards | Whether they hold business rules. | `app/app-transaction-type-db2/ctl/DB2CREAT.ctl:1` |
| 2 assembler sources (`app/asm/COBDATFT.asm`, `app/asm/MVSWAIT.asm`) | Date formatting called by CBACT01C, and a wait routine called by COBSWAIT | Behavior of the date routine, for the equivalence spec. | `app/asm/COBDATFT.asm:1`, `app/cbl/CBACT01C.cbl:231` |
| 2 assembler macros (`app/maclib/ASMWAIT.mac`, `app/maclib/COCDATFT.mac`) | Macros used by the assembler | Confirm they add nothing beyond the routines. | `app/maclib/ASMWAIT.mac:1` |
| The CA-7 listing (`app/scheduler/CardDemo.ca7`) | A scheduler the extractor cannot read | Which jobs it really schedules. I read it by hand, and it changes the wave 5 dependency. | `app/scheduler/CardDemo.ca7:43` |

### Extractor limits that touch this system

Each is a line from `meta.limits` in `graph.json`, with the place it bites.

| Limit | Where it bites here | Evidence |
|---|---|---|
| A variable call target is resolved only from VALUE clauses and literal MOVEs in the same program. | 28 computed calls stay open. I bounded them by hand in `02-coupling.md`. | `app/cbl/COMEN01C.cbl:199` |
| A called subprogram gets no DDs from its caller's step. | CBSTM03B shows four unmapped DDs. CREASTMT owns them. | `app/jcl/CREASTMT.JCL:83` |
| IDCAMS, SORT and other in-stream cards are not read. | The record contracts (key and record length, sort offsets, alternate index keys) are outside the graph. | `app/jcl/TRANREPT.jcl:41`, `app/jcl/ACCTFILE.jcl:40` |
| DCB, LRECL and RECFM are not read. | Record lengths on DDs (350, 430, 133) are not checked against copybooks. | `app/jcl/POSTTRAN.jcl:36`, `app/jcl/TRANREPT.jcl:78` |
| IF/THEN/ELSE and COND= in JCL are not modeled. | COND on the TRANBKP define step and on the TRANEXTR steps. | `app/jcl/TRANBKP.jcl:51`, `app/app-transaction-type-db2/jcl/TRANEXTR.jcl:65` |
| Nested PROC calls are not followed. JCL text inside a COBOL literal is noticed but makes no edge. | TRANREPT.prc calls REPROC. CORPT00C builds the report job. | `app/proc/TRANREPT.prc:21`, `app/cbl/CORPT00C.cbl:94` |
| EXEC CICS RETURN TRANSID, START and SEND MAP are not edges. | The sign-on returns with a transaction id chosen at run time. | `app/cbl/COSGN00C.cbl:99` |
| Only Control-M XML and shell wrappers that name JCL files are read as schedulers. | The CA-7 listing is unread. | `app/scheduler/CardDemo.ca7:43` |
| COPY REPLACING is not applied. | COTRTUPC uses it for screen attribute variables. It affects the graph, not the data. | `app/app-transaction-type-db2/cbl/COTRTUPC.cbl:1358` |
| A `high` contract edge means shared layout, not proven equal. LINK and XCTL are both call edges. | All 62 contract edges are `high`. The layout risk is in the cards above, not in these edges. | analysis: `meta.limits` |

## Files in this folder

`00-summary.md` (this file), `01-inventory.md`, `02a-edge-tables.md`, `02-coupling.md`, `03a-wave-seed.md`, `03a-waves-draft.json`, `03-waves.md`, `waves.json`, `04-estimate.md`, `05a-dead-code-candidates.md`, `05-dead-code.md`, `dead-code.json`, `06-test-strategy.md`, `risks.json`, `graph.json`. The `a` files are generated by the extractor's renderer. The others are mine.
