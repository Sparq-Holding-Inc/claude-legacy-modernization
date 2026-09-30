# 00 Summary

Assessment of the CardDemo tree (COBOL, CICS, JCL, VSAM, with IMS, DB2 and MQ modules) for modernization. Scope is `.`, the whole work folder. Facts come from `modernization-assessment/graph.json`, written by the extractor. Judgment, and anything I read by hand, is labeled `inference`.

## Scoping answers

- **Target state:** refactor. The same behavior in restructured code, usually as services.
- **What must not break:** "daily transaction posting, the account and card master refresh, and the transaction report." All three map to units in the tree. The map is under "Must-not-break map" below.
- **Telemetry:** none. Every dead-code claim is provisional.
- **Defaults:** no defaults applied. All three answers came as command arguments.

## Result

- **Waves: 7**, from `modernization-assessment/waves.json`, plus one unit not placed (CBTRN01C). 123 units are placed: 43 of the 44 programs, plus JCL jobs, procs and scheduler entries.
- **Effort:** 142 to 244 engineer-weeks, wide because waves 5 to 7 are wide (`modernization-assessment/04-estimate.md`).
- **Dead code:** one unreachable copybook, no dormant units measurable, two unknown (`modernization-assessment/05-dead-code.md`).
- **The plan departs from the seed in four placements**, all with cited reasons (`modernization-assessment/03-waves.md`).

| Wave | Name | Blast | Confidence | Evidence |
|---|---|---|---|---|
| 1 | Operations utilities | low | medium | `app/jcl/CLOSEFIL.jcl:26` |
| 2 | Read-only batch extracts | low | medium | `app/cbl/CBACT01C.cbl:231` |
| 3 | Sign-on, menus and read-only screens | medium | medium | `app/cbl/COMEN01C.cbl:156` |
| 4 | Build and file-transfer support | low | medium | `app/jcl/DEFGDGD.jcl:27` |
| 5 | Nightly batch cycle: refresh, posting, interest, report, statements | high | medium | `app/jcl/POSTTRAN.jcl:23` |
| 6 | Online writers | high | medium | `app/cbl/COACTUPC.cbl:4100` |
| 7 | Authorization, DB2 reference and MQ services | high | low | `app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:668` |

No wave has high confidence. Waves 3, 5, 6 and 7 hold the 28 computed calls. Wave 7 also rests on IMS, DB2 and MQ files the extractor did not read.

## The single largest risk

**The transaction master's only history is one generation of TRANSACT.BKUP, and three routes write that group while the reload job reads whichever generation is newest.**

The backup job unloads the master into a new generation and then deletes and redefines the file empty. The reload job later reads generation (0). The transaction report job unloads the master into a new generation too, and so does the online report screen through the JCL it writes to the internal reader. Any of them running between the backup and the reload hands the reload the wrong generation, and the group keeps only five (`app/jcl/TRANBKP.jcl:33`, `app/jcl/TRANBKP.jcl:40`, `app/jcl/TRANREPT.jcl:33`, `app/cbl/CORPT00C.cbl:94`, `app/jcl/COMBTRAN.jcl:24`, `app/jcl/DEFGDGB.jcl:26`). It touches all three must-not-break items, no edge in the graph shows it whole, and it depends on how the client's scheduler serializes jobs, which is open. The full argument is in `modernization-assessment/02-coupling.md`. The collision itself is `inference`.

The highest-scored unit in `modernization-assessment/risks.json` is CBTRN02C (difficulty 4, blast 5). It is the program the daily posting job runs and it opens the transaction master for output (`app/cbl/CBTRN02C.cbl:256`).

## Must-not-break map

| Must not break | Units | Wave | Evidence |
|---|---|---|---|
| Daily transaction posting | job:POSTTRAN with CBTRN02C, preceded by TRANBKP and TCATBALF and followed by TRANIDX in the wrapper | 5 | `app/jcl/POSTTRAN.jcl:23`, `scripts/run_posting.sh:26` |
| The account and card master refresh | job:ACCTFILE and job:CARDFILE | 5 | `scripts/remote_refresh.sh:17`, `scripts/remote_refresh.sh:20` |
| The transaction report | job:TRANREPT with CBTRN03C, and CORPT00C with proc:TRANREPT. Reference data comes from job:TRANEXTR in wave 7 | 5, fed from 7 | `app/jcl/TRANREPT.jcl:1`, `app/cbl/CORPT00C.cbl:94`, `app/app-transaction-type-db2/jcl/TRANEXTR.jcl:19` |

Two facts about scheduling belong here. The master refresh jobs ACCTFILE and CARDFILE are named by no Control-M folder and not by the CA-7 listing. Only the shell wrappers submit them, and those need an FTP tunnel from a workstation, so a person runs them (`inference`; `scripts/remote_refresh.sh:17`, `scripts/run_full_batch.sh:17`, `scripts/remote_refresh.sh:3`). The report job TRANREPT is named by no scheduler at all.

## Where I changed the seed

The seed placed job:CREADB2 in wave 1, CORPT00C and CSUTLDTC in wave 3, and proc:TRANREPT nowhere. I put job:CREADB2 in wave 7 and the other three in wave 5. The reasons are in `modernization-assessment/03-waves.md`. In short: CREADB2 creates DB2 tables through control members the extractor did not read (`app/app-transaction-type-db2/jcl/CREADB21.jcl:52`), and CORPT00C writes JCL text to the internal reader that runs the report proc (`app/cbl/CORPT00C.cbl:94`, `app/cbl/CORPT00C.cbl:517`).

## Open Questions

For the client's engineers. Numbered so they can be answered one by one.

### Files the extractor did not read

The extractor lists eight groups as not parsed. Each needs an owner to supply or explain it.

1. **DB2 DCLGEN and DDL.** `app/app-authorization-ims-db2-mq/dcl/AUTHFRDS.dcl`, `app/app-transaction-type-db2/dcl/DCLTRCAT.dcl`, `app/app-transaction-type-db2/dcl/DCLTRTYP.dcl`, `app/app-authorization-ims-db2-mq/ddl/AUTHFRDS.ddl`, `app/app-authorization-ims-db2-mq/ddl/XAUTHFRD.ddl`, `app/app-transaction-type-db2/ddl/TRNTYCAT.ddl` and three more DDL files. Are there triggers, stored procedures or constraints that hold business rules? The tables are TRANSACTION_TYPE and AUTHFRDS (`app/app-transaction-type-db2/cbl/COBTUPDT.cbl:137`).
2. **IMS DBD and PSB.** `app/app-authorization-ims-db2-mq/ims/DBPAUTP0.dbd`, `app/app-authorization-ims-db2-mq/ims/DBPAUTX0.dbd`, `app/app-authorization-ims-db2-mq/ims/PADFLDBD.DBD`, `app/app-authorization-ims-db2-mq/ims/DLIGSAMP.PSB`, `app/app-authorization-ims-db2-mq/ims/PAUTBUNL.PSB`, `app/app-authorization-ims-db2-mq/ims/PSBPAUTB.psb`. What are the segment layouts and the checkpoint rules for the authorization database?
3. **DB2 control cards.** `app/app-transaction-type-db2/ctl/DB2CREAT.ctl` and seven more (`DB2FREE.ctl`, `DB2LTCAT.ctl`, and others in the same folder). These drive the create and load jobs (`app/app-transaction-type-db2/jcl/CREADB21.jcl:52`).
4. **Assembler source and macros.** `app/asm/COBDATFT.asm`, `app/asm/MVSWAIT.asm`, `app/maclib/ASMWAIT.mac`, `app/maclib/COCDATFT.mac`. They are called at `app/cbl/CBACT01C.cbl:231` and `app/cbl/COBSWAIT.cbl:38`. Are there other assembler modules outside this tree?
5. **The CA-7 scheduler listing.** `app/scheduler/CardDemo.ca7`. I read it by hand. Which scheduler is the real one, and does the tree hold the whole schedule?

### About how the system runs

6. **Which order runs the daily cycle?** The wrapper runs close, account refresh, category balance refresh, backup, posting, index and open, with sleeps between submits (`scripts/run_posting.sh:13`, `scripts/run_posting.sh:26`). Control-M has no POSTTRAN (`app/scheduler/CardDemo.controlm:4`). CA-7 runs CLOSEFIL then CBPAUP0J then POSTTRAN (`app/scheduler/CardDemo.ca7:43`, `app/scheduler/CardDemo.ca7:70`). Which one is production, and who serializes the jobs?
7. **Who produces the daily transaction file?** POSTTRAN reads DALYTRAN.PS and nothing in the tree writes it (`app/jcl/POSTTRAN.jcl:31`, `README.md:139`). Where does it come from, and how are rejects handled? POSTTRAN writes rejects to a new generation each run (`app/jcl/POSTTRAN.jcl:38`).
8. **Can a report run land between the backup and the reload?** The online screen lets any signed-on user submit the report at any time (`app/cbl/CORPT00C.cbl:517`). How many generations of TRANSACT.BKUP exist, are they archived beyond the limit of five, and has a reload ever read the wrong one?
9. **Are the date literals edited on every run?** The report window is fixed at January to July 2022 in the job (`app/jcl/TRANREPT.jcl:43`, `app/jcl/TRANREPT.jcl:44`), and the interest job's PARM is the literal 2022071800 (`app/jcl/INTCALC.jcl:22`). That PARM becomes the front of every interest transaction id (`app/cbl/CBACT04C.cbl:476`). Who changes them, and how do ids stay unique across months?
10. **What produces the flat files the master refresh loads from?** ACCTFILE deletes the account master and reloads it from ACCTDATA.PS (`app/jcl/ACCTFILE.jcl:25`, `app/jcl/ACCTFILE.jcl:61`), and CARDFILE does the same for cards (`app/jcl/CARDFILE.jcl:36`). What happens to balances that COACTUPC and COBIL00C changed online since the flat file was cut?
11. **Does TRANEXTR feed the report's reference files?** Its header says so (`app/app-transaction-type-db2/jcl/TRANEXTR.jcl:19`). The extractor has no dataset edge for it because it uses `&HLQ` in dataset names (`app/app-transaction-type-db2/jcl/TRANEXTR.jcl:34`), so I am inferring that TRANTYPE.PS and TRANCATG.PS written there are what jobs TRANTYPE and TRANCATG reload (`app/jcl/TRANTYPE.jcl:56`, `app/jcl/TRANCATG.jcl:56`). Is that right?
12. **Do the 27 jobs no scheduler names still run?** They are listed in `modernization-assessment/05-dead-code.md`, and include the report job TRANREPT. Which are run by hand?
13. **Does CBTRN01C ever run?** No job names it and its six DDs map to no JCL (`app/cbl/CBTRN01C.cbl:29`).
14. **What is the CICS side of a refresh?** CLOSEFIL closes five files in a fixed region, CICSAWSA, and leaves the card and customer masters to their own jobs (`app/jcl/CLOSEFIL.jcl:26`). Are there other regions, and what does the online system do while files are closed?
15. **Who receives the MQ replies and the FTP file?** COACCT01 and CODATE01 answer MQ requests (`app/app-vsam-mq/cbl/COACCT01.cbl:352`, `app/app-vsam-mq/cbl/CODATE01.cbl:301`), COPAUA0C answers authorization requests (`app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:400`), and one job sends a file to an outside host (`app/jcl/FTPJCL.JCL:40`). What are the formats and who depends on them?
16. **What happens when a card has more than ten transactions?** The statement table holds 51 cards of 10 transactions (`app/cbl/CBSTM03A.CBL:226`, `app/cbl/CBSTM03A.CBL:228`).
17. **What are the production volumes?** The demo allocations are one to five cylinders (`app/jcl/ACCTFILE.jcl:37`). There is nothing in the tree on record counts, daily volumes or peak load.
18. **Can the team read COBOL and JCL?** If not, every wave grows (`modernization-assessment/04-estimate.md`).

### Security items to act on now, whatever the migration

19. **Credentials in clear.** The sign-on file holds 8-character passwords in clear and the sign-on program compares them as typed (`app/cpy/CSUSR01Y.cpy:21`, `app/cbl/COSGN00C.cbl:223`). An FTP job holds a host, a user and a password in its cards (`app/jcl/FTPJCL.JCL:33`). Rotate the credential and confirm the host is not live. The values are not reproduced in this folder.

### Extractor limits that touch this system

These come from `meta.limits` in `modernization-assessment/graph.json`. They matter here for the reasons given.

- Variable call targets resolve only from VALUE clauses and literal MOVEs in the same program. That is why there are 28 computed calls. I bounded them by hand (`modernization-assessment/02-coupling.md`).
- COPY REPLACING is not applied. COACTUPC copies one member 39 times with REPLACING (`app/cbl/COACTUPC.cbl:3208`), and five other programs use it, so their field lists are incomplete in the graph.
- A called subprogram gets no DDs from its caller's step. CBSTM03B's four files show as unmapped (`app/cbl/CBSTM03B.CBL:31`).
- SORT and most in-stream control cards are not read. The report sort, the reload sort and the statement sort carry the date window and the ordering (`app/jcl/TRANREPT.jcl:47`, `app/jcl/COMBTRAN.jcl:28`).
- IF/THEN/ELSE and COND= in JCL are not modeled. Step conditions decide whether a redefine runs (`app/jcl/TRANBKP.jcl:51`, `app/app-transaction-type-db2/jcl/TRANEXTR.jcl:42`).
- Nested procs are not followed, and JCL text inside COBOL makes no edge. Proc TRANREPT calls proc REPROC (`app/proc/TRANREPT.prc:21`), and CORPT00C submits proc TRANREPT from a literal.
- EXEC CICS RETURN TRANSID, START and SEND MAP are not edges. The online chains between transactions are not in the graph.
- Only Control-M XML and shell wrappers that name JCL files are read as schedulers. That excludes the CA-7 listing.
- DCB, LRECL and RECFM are not read, so record length on a DD is never compared with a copybook. Every one of the 62 contract edges is `high` because both sides copy a layout. That is not proof the record is read the same way. The reject record length was checked by hand (`app/jcl/POSTTRAN.jcl:36`, `app/cbl/CBTRN02C.cbl:83`, `app/cbl/CBTRN02C.cbl:84`) and matches at 430 bytes. Nothing else was.
- LINK and XCTL are both call edges and control flow is not modeled.

## How this folder is organized

- `modernization-assessment/01-inventory.md`, `modernization-assessment/02a-edge-tables.md`, `modernization-assessment/03a-wave-seed.md`, `modernization-assessment/05a-dead-code-candidates.md` and `modernization-assessment/graph.json` are generated.
- `modernization-assessment/02-coupling.md`, `modernization-assessment/03-waves.md`, `modernization-assessment/04-estimate.md`, `modernization-assessment/05-dead-code.md` and `modernization-assessment/06-test-strategy.md` are the argument.
- `modernization-assessment/waves.json`, `modernization-assessment/dead-code.json` and `modernization-assessment/risks.json` are checked by `schema.py`.
- Risk scores are `modernization-assessment/risks.json`. Most program scores rest on a read of the cited lines. Scores for units I did not read line by line have confidence `low`.
