# 00 Summary

Assessment of the CardDemo mainframe system in this folder: 44 COBOL programs, 55 JCL jobs, 6 procs, 62 copybooks, 21 BMS maps, 19 Control-M and wrapper rows, and a CA-7 listing. Extractor output is `modernization-assessment/graph.json`. The plan is in `modernization-assessment/waves.json`, the scores in `modernization-assessment/risks.json`, and the dead-code register in `modernization-assessment/dead-code.json`.

## Scoping answers

- Target state: refactor (given as `--target refactor`).
- Must not break: daily transaction posting, the account and card master refresh, and the transaction report (given as `--must-not-break`).
- Runtime telemetry: none (given as `--telemetry none`). Every dead-code claim is provisional.
- Defaults: no defaults applied. All three answers came as flags, so nothing was assumed.
- The run was non-interactive. I asked no questions.

## Waves

Seven waves, 123 units placed and one unassigned (CBTRN01C). See `modernization-assessment/03-waves.md`.

1. Utilities and plumbing (17 units)
2. Read-only batch readers (15)
3. Sign-on, menus and read-only screens (7)
4. Data load and refresh utilities (26)
5. Posting cycle, interest, statements and the transaction report (26)
6. Online maintenance of the masters (9)
7. Authorization, DB2 and IMS subsystems (23)

I moved 21 unit placements away from the extractor's seed, each with a cited reason. Eleven follow from the must-not-break items, and ten follow from things the extractor cannot read (IDCAMS control cards, the `RUN PROGRAM` and `DFSRRC00` commands, and JCL text inside a COBOL program).

Estimate: 59 to 116 engineer-weeks across the seven waves, with 44 to 86 of them in waves 5, 6 and 7. It is a spread and not a forecast (`modernization-assessment/04-estimate.md`).

## The single largest risk

The accounts and the transaction file are rewritten every day by a cycle whose correctness lives in JCL step order and not in any program, and both masters are written from batch and from online. CBTRN02C opens the transaction file for OUTPUT, and TRANBKP is what backs it up and rebuilds it empty, with a delete step that has no COND, so a failed backup does not stop the delete (`app/cbl/CBTRN02C.cbl:256`, `app/jcl/TRANBKP.jcl:37`, `app/jcl/TRANBKP.jcl:40`). ACCTDATA has four program writers and TRANSACT three, and 46 of the 62 contract edges join programs in different waves. A port that gets the handover of either master wrong is silently wrong on money, and the call graph does not show the rebuild cycle. The cure is a data facade or replica in front of both masters before wave 5, and a harness that runs the whole cycle and not only the program.

## Open questions for the client's engineers

Scheduling and order

1. Which order runs before POSTTRAN in production? The CA-7 listing has CBPAUP0J trigger it (`app/scheduler/CardDemo.ca7:70`). The wrappers run ACCTFILE, TCATBALF and TRANBKP first (`scripts/run_posting.sh:17`, `scripts/run_posting.sh:20`, `scripts/run_posting.sh:23`). Does a failure of the IMS purge hold back daily posting?
2. Is the CA-7 file current? Every job in it shows the same run count and last run date (`app/scheduler/CardDemo.ca7:24`, `app/scheduler/CardDemo.ca7:51`, `app/scheduler/CardDemo.ca7:78`). Please supply the real CA-7 job definitions and 12 months of job logs or SMF records.
3. Two daily chains touch the transaction file: the Control-M folder (`app/scheduler/CardDemo.controlm:3`) and the CA-7 chain. Which is authoritative, and do both run?
4. TRANREPT is scheduled nowhere in the tree. Who runs it, and how often? Which of the other 26 unscheduled jobs still run? The list is in `modernization-assessment/05-dead-code.md`.
5. INTRDRJ1 submits INTRDRJ2 through the internal reader (`app/jcl/INTRDRJ1.JCL:17`), and CORPT00C submits the report through the JOBS TD queue (`app/csd/CARDDEMO.CSD:499`). What else submits jobs this way? The extractor has no edge for either.

Data

6. Nothing in the tree writes the daily transaction file that POSTTRAN reads (`app/jcl/POSTTRAN.jcl:31`). Where does it come from, and is the layout exactly CVTRA06Y?
7. What is the system of record for accounts and cards? ACCTFILE deletes and reloads the account master from a flat file (`app/jcl/ACCTFILE.jcl:25`, `app/jcl/ACCTFILE.jcl:61`) and the posting wrapper runs it before every posting (`scripts/run_posting.sh:17`). Is that production behavior, or a test data refresh? If it is production, where do online account updates go?
8. Please confirm the life of the transaction file: reset each cycle, refilled by POSTTRAN, backed up, merged with interest, reloaded (`app/jcl/COMBTRAN.jcl:48`). How much transaction history must be kept, given the backup GDG keeps five generations (`app/jcl/DEFGDGB.jcl:25`)?
9. TRANREPT's GDG is defined with limit 5 in one job and limit 10 in another (`app/jcl/DEFGDGB.jcl:37`, `app/jcl/REPTFILE.jcl:27`). Which is live, and is the report archive a regulatory record?
10. TRANIDX builds an alternate index over the transaction file (`app/jcl/TRANIDX.jcl:25`). No program or CSD entry in the tree reads it. Who uses it?
11. DEFCUST deletes one cluster name and defines a different one (`app/jcl/DEFCUST.jcl:25`, `app/jcl/DEFCUST.jcl:35`). Is it abandoned?

Rules that only the code states

12. When a transaction is both over the limit and after expiry, reject 103 overwrites 102 (`app/cbl/CBTRN02C.cbl:410`, `app/cbl/CBTRN02C.cbl:417`). Is that intended? What should a failed account rewrite do (`app/cbl/CBTRN02C.cbl:556`)?
13. INTCALC gives the run date as a constant (`app/jcl/INTCALC.jcl:22`). How is it changed each month? Interest truncates and never rounds (`app/cbl/CBACT04C.cbl:464`). Is that a rule?
14. The report screen accepts date message 2513 as valid (`app/cbl/CORPT00C.cbl:399`). Why?
15. The batch report job and its proc both carry a fixed 2022 date window (`app/jcl/TRANREPT.jcl:43`, `app/proc/TRANREPT.prc:41`). Is the batch job used at all beyond the online path?

Files the extractor did not parse (each is an open item)

16. The CA-7 listing (`app/scheduler/CardDemo.ca7:1`). Covered by questions 1 to 3.
17. IMS DBD and PSB files, eight in all (`app/app-authorization-ims-db2-mq/ims/DBPAUTP0.dbd:1`, `app/app-authorization-ims-db2-mq/ims/DLIGSAMP.PSB:1`). Please give the segment hierarchy, sizes and any secondary indexes. Wave 7 cannot be tightened without them.
18. DB2 DDL and DCLGEN files, nine in all (`app/app-transaction-type-db2/ddl/TRNTYCAT.ddl:1`, `app/app-authorization-ims-db2-mq/ddl/AUTHFRDS.ddl:1`, `app/app-authorization-ims-db2-mq/dcl/AUTHFRDS.dcl:1`). Are there stored procedures, triggers or views that hold business rules? None are in the tree.
19. DB2 utility control cards, eight in all (`app/app-transaction-type-db2/ctl/DB2CREAT.ctl:1`).
20. Assembler source and macros, four files (`app/asm/COBDATFT.asm:1`, `app/asm/MVSWAIT.asm:1`, `app/maclib/COCDATFT.mac:1`, `app/maclib/ASMWAIT.mac:1`). CBACT01C calls COBDATFT (`app/cbl/CBACT01C.cbl:231`) and COBSWAIT calls MVSWAIT (`app/cbl/COBSWAIT.cbl:37`). What do they do, and who can read them?
21. The catalog listing (`app/catlg/LISTCAT.txt:1`) is not read by the extractor. I used it only to see retained generations. Is it a 2022 snapshot of a demo environment?

Gaps between the tree and the running system

22. COCRDSEC is defined to CICS with no source in the tree (`app/csd/CARDDEMO.CSD:211`). Where is it?
23. The CSD has no PROGRAM definition for COACCT01, CODATE01, COPAUA0C, COPAUS0C, COPAUS1C, COPAUS2C, COTRTLIC or COTRTUPC (`app/csd/CARDDEMO.CSD:173`, `app/csd/CARDDEMO.CSD:299`). Where are they defined, and are they installed?
24. The last change dates in git fall on four dates, and 99 units share one, so they look like bulk commits. Can you supply the real change history? Without it, dormancy is not measured.
25. Passwords and logins are typed into source: a host, user id and password in an FTP job (`app/jcl/FTPJCL.JCL:33`), default user passwords in the user file setup jobs (`app/jcl/ESDSRRDS.jcl:36`, `app/jcl/DUSRSECJ.jcl:35`), and an 8 byte password compared in clear at sign-on (`app/cbl/COSGN00C.cbl:223`). Are these demo values? Which are real and need rotating? RACF rules are outside the tree (`samples/jcl/RACFCMDS.jcl:1`).

Team and method

26. Who on the team can read COBOL, JCL, IMS and DB2? Every estimate depends on the answer.
27. Can the old system stay up for a parallel run? Are the runtime bundles in `samples/m2` a working way to run the legacy off the mainframe?

## Limits of the extractor that touch this system

| Limit (from `meta.limits`) | Does it bite here | Where | Confidence | Evidence |
|---|---|---|---|---|
| COBOL is read as fixed format | No. No file was listed as free format. | All 44 programs were read. | high | `analysis` (field `structure_basis`) |
| COPY REPLACING is not applied | Slightly. The screen attribute copybook is replaced in the two update screens. | COACTUPC | medium | `app/cbl/COACTUPC.cbl:3208` |
| A variable call target resolves only from VALUE clauses and literal MOVEs | Yes. 28 computed calls. I bounded them in the coupling file. | The menu tables and return-to-caller fields | high | `app/cbl/COMEN01C.cbl:156`, `app/cbl/COACTUPC.cbl:956` |
| A called subprogram gets no DDs from its caller's step | Yes. CBSTM03B shows four unmapped DDs. | CREASTMT | high | `app/cbl/CBSTM03B.CBL:31`, `app/jcl/CREASTMT.JCL:83` |
| IDCAMS, SORT and other control cards are not read | Yes, and it changed the plan. TRANIDX, the reloads, and the SORT offsets in the report. | Waves 1, 4 and 5 | high | `app/jcl/TRANIDX.jcl:25`, `app/jcl/TRANREPT.jcl:41` |
| IF/THEN/ELSE and COND are not modeled | Yes. TRANBKP relies on COND for one step and not another. | TRANBKP | high | `app/jcl/TRANBKP.jcl:37`, `app/jcl/TRANBKP.jcl:51` |
| Nested procs are not followed, and JCL text in a COBOL literal makes no edge | Yes. CORPT00C carries the report JCL. | The report | high | `app/cbl/CORPT00C.cbl:94` |
| RETURN TRANSID, START and SEND MAP are not edges | Yes. The online call graph is understated. | All online programs | high | `app/cbl/COSGN00C.cbl:98` |
| Only Control-M XML and shell wrappers are read as schedulers | Yes. CA-7 was not read. | Scheduling | high | `app/scheduler/CardDemo.ca7:70` |
| DCB, LRECL and RECFM are not read | Yes. Record lengths on DDs are not checked against copybooks. The reject file is 430 bytes (`app/jcl/POSTTRAN.jcl:36`) and the transaction record is 350. | POSTTRAN, TRANREPT | medium | `app/jcl/POSTTRAN.jcl:36`, `app/cpy/CVTRA05Y.cpy:1` |
| A high contract edge means a shared layout, not proven equal | Yes, for all 62 edges. | The masters | high | `analysis` (field `edge_counts`) |
| LINK and XCTL are both call edges | Yes. The three components are XCTL ping-pong, not recursion. They still move whole. | The menu and list screens | medium | `app/cbl/COSGN00C.cbl:231` |
| Not stated as a limit, but found | The extractor does not read the PARM of a DFSRRC00 step or the `RUN PROGRAM` command in an IKJEFT01 step, so five programs looked uncalled and three DB2 jobs looked like utilities. | Waves 1 and 7 | high | `app/app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl:25`, `app/app-transaction-type-db2/jcl/MNTTRDB2.jcl:30` |

## Files in this folder

`00-summary.md` (this file), `01-inventory.md`, `02-coupling.md`, `02a-edge-tables.md`, `03-waves.md`, `03a-wave-seed.md`, `03a-waves-draft.json`, `04-estimate.md`, `05-dead-code.md`, `05a-dead-code-candidates.md`, `06-test-strategy.md`, `graph.json`, `waves.json`, `risks.json`, `dead-code.json`. The ones with an `a` in the number are generated. The rest are argument.
