# 03 Waves

Target state is refactor: the same behavior in restructured code, most likely as services. The plan starts from the extractor's seed (`modernization-assessment/03a-wave-seed.md` and `modernization-assessment/03a-waves-draft.json`), which puts every entry point in one family, in a fixed order, from facts alone. I kept the family order and the wave numbers. I changed the units in a wave only for a reason I can cite, and every change is a row in the deviations table below and a record in `modernization-assessment/waves.json`. The scores come from `modernization-assessment/risks.json`, which is the migration-risk-assessor's work done inline, following `agents/migration-risk-assessor.md`.

Seven waves, 123 units placed and one left unassigned. A unit is a program, a JCL job, a proc or a scheduler job. Steps, copybooks and datasets move with their owner.

## The plan at a glance

| Wave | Name | Family | Units | COBOL lines | Risk quadrants (units scored) | Blast radius | Confidence | Evidence |
|---|---|---|---|---|---|---|---|---|
| 1 | Utilities and plumbing | batch-utility | 17 (11 jobs, 6 scheduler rows) | 0 | 6 low-high, 5 low-low | low | medium | `app/jcl/DEFGDGB.jcl:25`, `app/jcl/CLOSEFIL.jcl:26`, `app/jcl/OPENFIL.jcl:26` |
| 2 | Read-only batch readers | batch-readonly | 15 (6 programs, 6 jobs, 3 scheduler rows) | 1,097 | 2 high-low, 10 low-low | low | medium | `app/cbl/CBACT01C.cbl:29`, `app/cbl/CBACT02C.cbl:29`, `app/cbl/CBACT03C.cbl:29` |
| 3 | Sign-on, menus and read-only screens | online-readonly | 7 (7 programs) | 2,679 | 3 low-high, 4 low-low | medium | medium | `app/cbl/COSGN00C.cbl:223`, `app/cpy/COMEN02Y.cpy:21`, `app/cbl/COMEN01C.cbl:156` |
| 4 | Data load and refresh utilities | batch-data-jobs | 26 (20 jobs, 5 procs, 1 scheduler row) | 0 | 8 low-high, 12 low-low | high | low | `app/jcl/CUSTFILE.jcl:22`, `app/jcl/XREFFILE.jcl:22`, `app/jcl/TCATBALF.jcl:22` |
| 5 | Posting cycle, interest, statements and the transaction report | batch-writers | 26 (8 programs, 10 jobs, 1 proc, 7 scheduler rows) | 3,670 | 6 high-high, 1 high-low, 10 low-high, 1 low-low | high | medium | `app/jcl/POSTTRAN.jcl:23`, `app/cbl/CBTRN02C.cbl:256`, `app/jcl/TRANREPT.jcl:59` |
| 6 | Online maintenance of the masters | online-writers | 9 (9 programs) | 7,972 | 4 high-high, 1 high-low, 3 low-high, 1 low-low | high | medium | `app/cbl/COBIL00C.cbl:212`, `app/cbl/COTRN02C.cbl:444`, `app/cbl/COUSR01C.cbl:39` |
| 7 | Authorization, DB2 and IMS subsystems | subsystem | 23 (13 programs, 8 jobs, 2 scheduler rows) | 7,071 | 8 high-high, 10 high-low, 2 low-high, 1 low-low | high | low | `app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:35`, `app/app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl:25`, `app/app-transaction-type-db2/jcl/MNTTRDB2.jcl:30` |

## The client's must-not-break items

The three items were given as flags. Each maps to units the graph could not tie together on its own.

| Item | Units | Wave | How it is anchored | Confidence | Evidence |
|---|---|---|---|---|---|
| Daily transaction posting | job POSTTRAN, CBTRN02C, and the jobs that rebuild the file around it: TRANBKP, COMBTRAN, TRANIDX | 5 | Parallel run on the daily file, with the TRANSACT rebuild inside the harness. CBTRN02C is high-high and cannot go last. | high | `app/jcl/POSTTRAN.jcl:23`, `app/cbl/CBTRN02C.cbl:256`, `app/jcl/TRANBKP.jcl:40`, `app/jcl/COMBTRAN.jcl:48`, `app/jcl/TRANIDX.jcl:25` |
| Account and card master refresh | job ACCTFILE and job CARDFILE (wave 5). The masters are read by CBACT01C, CBACT02C and the view screens (waves 2 and 3), and written by CBTRN02C, CBACT04C, COACTUPC, COBIL00C and COCRDUPC (waves 5 and 6). | 2 to 6 | The item is not finished until wave 6, because a master is only retired when its last writer moves. The refresh is compared as file content before and after each writer. | medium | `app/jcl/ACCTFILE.jcl:25`, `app/jcl/ACCTFILE.jcl:61`, `app/jcl/CARDFILE.jcl:36`, `app/jcl/CARDFILE.jcl:75`, `scripts/run_posting.sh:17` |
| Transaction report | job TRANREPT, proc TRANREPT, CBTRN03C, CORPT00C, CSUTLDTC (wave 5). The TRANTYPE and TRANCATG label files it reads are wave 4 jobs. | 5 (data in 4) | Golden master from the archived TRANREPT generations, and a run of both the online and the batch path. | medium | `app/jcl/TRANREPT.jcl:59`, `app/cbl/CORPT00C.cbl:94`, `app/proc/TRANREPT.prc:57`, `app/cbl/CBTRN03C.cbl:173` |

## Wave by wave

### Wave 1. Utilities and plumbing

Batch jobs that run no application program and touch no shared data: CICS file close and open, GDG base definitions, RACF and CSD utilities. This is a sound first wave for proving the toolchain and measuring velocity, and it is close to a chore for the business. Six of the 17 units are Control-M rows that only run CLOSEFIL or OPENFIL. Four jobs left it because the extractor could not see what they touch: TRANIDX (an index over the transaction master), and MNTTRDB2, TRANEXTR and CREADB2 (DB2). See deviations. DEFGDGB defines the GDG bases for TRANSACT.BKUP, SYSTRAN and TRANREPT that every later wave writes.

Unblocks: The CICS close and open bracket that every refresh uses, and the GDG bases that POSTTRAN, INTCALC and TRANREPT write. Nothing else waits on it, so it is a toolchain proof more than a deliverable.

Units: `job:CBADMCDJ`, `job:CLOSEFIL`, `job:DALYREJS`, `job:DEFCUST`, `job:DEFGDGB`, `job:ESDSRRDS`, `job:FTPJCLS`, `job:LISTFILS`, `job:OPENFIL`, `job:RACFCMDS`, `job:REPTFILE`, `sch:DAILY-TransactionBackup/CLOSEFIL`, `sch:DAILY-TransactionBackup/OPENFIL`, `sch:MONTHLY-InterestCalculation/CLOSEFIL`, `sch:MONTHLY-InterestCalculation/OPENFIL`, `sch:WEEKLY-DisclosureGroupsRefresh/CLOSEFIL`, `sch:WEEKLY-DisclosureGroupsRefresh/OPENFIL`

### Wave 2. Read-only batch readers

CBACT01C, CBACT02C, CBACT03C and CBCUS01C read one master each and write nothing another entry point uses, so they can be compared against legacy output without risk to any master. CBIMPORT writes work files only. This is a sound wave: it proves the four master layouts (CVACT01Y, CVACT02Y, CVACT03Y, CVCUS01Y) and the comparison harness. The three WAITSTEP scheduler rows and COBSWAIT are a timer, not logic.

Unblocks: The harness and the decimal and record layout conversions for the account, card, cross-reference and customer masters. Waves 3, 5 and 6 reuse both.

Units: `CBACT01C`, `CBACT02C`, `CBACT03C`, `CBCUS01C`, `CBIMPORT`, `COBSWAIT`, `job:CBIMPORT`, `job:READACCT`, `job:READCARD`, `job:READCUST`, `job:READXREF`, `job:WAITSTEP`, `sch:DAILY-TransactionBackup/WAITSTEP`, `sch:MONTHLY-InterestCalculation/WAITSTEP`, `sch:WEEKLY-DisclosureGroupsRefresh/WAITSTEP`

### Wave 3. Sign-on, menus and read-only screens

COSGN00C, COMEN01C and COADM01C are one strongly connected component. They move together, and every screen program XCTLs back into them. COTRN00C and COTRN01C are the other component here. The menu options are a table, so the ported menu still has to reach programs that stay on the old side until waves 5, 6 and 7. That makes the menu the facade for the online side. The read-only views (COACTVWC, COCRDSLC, COTRN00C, COTRN01C) are the first screens a user can see on the new platform. CORPT00C and CSUTLDTC left this wave. See deviations.

Unblocks: The front door. Sign-on and the menu can route to new or legacy screens from this wave on, which lets waves 5 and 6 cut over one screen at a time.

Units: `COACTVWC`, `COADM01C`, `COCRDSLC`, `COMEN01C`, `COSGN00C`, `COTRN00C`, `COTRN01C`

### Wave 4. Data load and refresh utilities

IDCAMS, SORT and IEBGENER jobs that delete, define and reload master and reference files. The extractor infers their modes from DISP only, so the writes are guesses. The wave holds 26 units and I did not cut it: 11 are toolchain build and sample jobs and procs that are not ported (see risks.json do_not_port), which leaves 15. It is the weakest wave. It runs ahead of the programs that own the data (waves 5 and 6), so until those move, each job runs against a replica, not the master. Seven units left because must-not-break items force them into wave 5. CUSTFILE, DISCGRP, TRANTYPE, DUSRSECJ, XREFFILE and TCATBALF have the same shape and stay here, because the client did not name them.

Unblocks: The reload path for the new platform's master files. It is a chore for the business, and nothing stakeholders name depends on it alone.

Units: `job:CBLDBMS`, `job:CICCMP`, `job:CIDBCMP`, `job:CNJBATMP`, `job:CUSTFILE`, `job:DEFGDGD`, `job:DISCGRP`, `job:DUSRSECJ`, `job:IMSMQCMP`, `job:INTRDRJ1`, `job:INTRDRJ2`, `job:PRTCATBL`, `job:REPRTEST`, `job:SORTTEST`, `job:TCATBALF`, `job:TRANCATG`, `job:TRANFILE`, `job:TRANTYPE`, `job:TXT2PDF1`, `job:XREFFILE`, `proc:BLDCIDB2`, `proc:BUILDBAT`, `proc:BUILDBMS`, `proc:BUILDONL`, `proc:REPROC`, `sch:WEEKLY-DisclosureGroupsRefresh/DISCGRP`

### Wave 5. Posting cycle, interest, statements and the transaction report

The core financial batch. The seed's family is batch jobs that write shared data. I added the jobs the client's must-not-break list forces in: the account and card refresh, the TRANSACT backup, rebuild and index jobs, and the online report entry with the proc it submits. The wave holds 26 units and is not cut. The only cut with a boundary is at CBTRN02C (an articulation point), which would put the read side (report, statements, export) in a later wave. That leaves the new TRANSACT replicated back to legacy readers for a whole wave, so it costs more than it isolates. CBTRN02C is high-high and a must-not-break item, so it cannot go last: the data facade is what sits in front of it. TRANSACT is also written online by COBIL00C and COTRN02C, and ACCTDATA by COACTUPC and COBIL00C, all in wave 6, so waves 5 and 6 have to agree who owns each master.

Unblocks: Daily posting, monthly interest, statements and the transaction report on the new platform. The business can name it, and it is the last wave that has to read the masters as legacy-owned.

Units: `CBACT04C`, `CBEXPORT`, `CBSTM03A`, `CBSTM03B`, `CBTRN02C`, `CBTRN03C`, `job:CBEXPORT`, `job:CREASTMT`, `job:INTCALC`, `job:POSTTRAN`, `job:TRANREPT`, `sch:MONTHLY-InterestCalculation/INTCALC`, `sch:scripts/run_full_batch.sh`, `sch:scripts/run_interest_calc.sh`, `sch:scripts/run_posting.sh`, `job:TRANBKP`, `sch:DAILY-TransactionBackup/TRANBKP`, `job:TRANIDX`, `job:COMBTRAN`, `sch:MONTHLY-InterestCalculation/COMBTRAN`, `job:ACCTFILE`, `job:CARDFILE`, `sch:scripts/remote_refresh.sh`, `CORPT00C`, `proc:TRANREPT`, `CSUTLDTC`

### Wave 6. Online maintenance of the masters

The online programs that write the account, card, customer, transaction and user masters. COACTUPC is 3,368 lines and the hardest single program in the tree. COBIL00C and COTRN02C allocate the next transaction id as the highest key plus one, a second id source next to the ids in the daily transaction file. This wave is sound as the last owner of the masters: when it moves, the legacy VSAM files can be retired. COCRDLIC sits here because it XCTLs to COCRDUPC, which writes the card master.

Unblocks: Retirement of the VSAM masters and the CICS file definitions, and the end of the replica between legacy and new.

Units: `COACTUPC`, `COBIL00C`, `COCRDLIC`, `COCRDUPC`, `COTRN02C`, `COUSR00C`, `COUSR01C`, `COUSR02C`, `COUSR03C`

### Wave 7. Authorization, DB2 and IMS subsystems

Everything that touches DB2, IMS or MQ: the authorization decision program COPAUA0C, its IMS screens and batch load and unload jobs, the transaction-type DB2 screens and the DB2 utility jobs. Five batch programs and three DB2 jobs joined it because the extractor could not see how they are run (DFSRRC00 PARM and DSN RUN PROGRAM). This wave is last on purpose: IMS, DB2 and MQ are outside what the extractor reads, and the DBD, PSB and DDL files are among the files it did not parse. COPAUS0C and COPAUS1C are one strongly connected component and move together.

Unblocks: Retirement of IMS, DB2 and MQ on the mainframe. It also removes the CBPAUP0J trigger ahead of POSTTRAN in the CA-7 listing.

Units: `COACCT01`, `CODATE01`, `COPAUA0C`, `COPAUS0C`, `COPAUS1C`, `COPAUS2C`, `COTRTLIC`, `COTRTUPC`, `job:CBPAUP0J`, `job:DBPAUTP0`, `job:LOADPADB`, `job:UNLDGSAM`, `job:UNLDPADB`, `job:MNTTRDB2`, `sch:WEEKLY-TransactionTypesDBRefresh/MNTTRDB2`, `job:TRANEXTR`, `sch:WEEKLY-TransactionTypesDBRefresh/TRANEXTR`, `job:CREADB2`, `COBTUPDT`, `CBPAUP0C`, `DBUNLDGS`, `PAUDBLOD`, `PAUDBUNL`

## Deviations from the seed

Every row is also in `deviations` in `modernization-assessment/waves.json`. Group A follows from the must-not-break items and their dependencies. Group B follows from things the extractor could not see (JCL command text it does not read). A blank From means the seed left the unit unplaced.

| Unit | From | To | Reason | Confidence | Evidence |
|---|---|---|---|---|---|
| `job:TRANBKP` | 4 | 5 | Must-not-break daily posting. CBTRN02C opens the TRANSACT KSDS for OUTPUT, and TRANBKP is the job that backs the file up to a GDG generation and then deletes and redefines it empty, so POSTTRAN is only correct behind it. The wrappers run TRANBKP before POSTTRAN and again after INTCALC. They cut over together. | high | `app/cbl/CBTRN02C.cbl:256`, `app/jcl/TRANBKP.jcl:40`, `app/jcl/TRANBKP.jcl:54`, `scripts/run_posting.sh:23`, `scripts/run_posting.sh:26`, `scripts/run_full_batch.sh:55` |
| `sch:DAILY-TransactionBackup/TRANBKP` | 4 | 5 | Follows job:TRANBKP. The Control-M row only runs that job. | medium | `app/scheduler/CardDemo.controlm:8` |
| `job:TRANIDX` | 1 | 5 | The extractor does not read IDCAMS control cards, so it saw a utility with no data. TRANIDX defines and builds an alternate index over the TRANSACT KSDS, which 11 programs read. TRANBKP deletes that index and TRANIDX rebuilds it after POSTTRAN in every wrapper. It belongs with the posting cycle. | high | `app/jcl/TRANIDX.jcl:25`, `app/jcl/TRANIDX.jcl:26`, `app/jcl/TRANIDX.jcl:52`, `app/jcl/TRANBKP.jcl:43`, `scripts/run_posting.sh:30` |
| `job:COMBTRAN` | 4 | 5 | Part of the posting and interest cycle. COMBTRAN merges the TRANSACT backup with the SYSTRAN file that INTCALC writes, then REPROs the result back into the TRANSACT KSDS. Wave 4 would put it between TRANBKP and TRANIDX, which are both wave 5. | medium | `app/jcl/COMBTRAN.jcl:24`, `app/jcl/COMBTRAN.jcl:26`, `app/jcl/COMBTRAN.jcl:48`, `scripts/run_full_batch.sh:55`, `scripts/run_full_batch.sh:58`, `scripts/run_full_batch.sh:62` |
| `sch:MONTHLY-InterestCalculation/COMBTRAN` | 4 | 5 | Follows job:COMBTRAN. | medium | `app/scheduler/CardDemo.controlm:75` |
| `job:ACCTFILE` | 4 | 5 | Must-not-break account master refresh. The job deletes and redefines the account master and reloads it from a flat file. run_posting.sh runs it directly before POSTTRAN, so the refreshed master is what CBTRN02C reads and rewrites. The master has four program writers, two in wave 5 and two in wave 6. | medium | `app/jcl/ACCTFILE.jcl:25`, `app/jcl/ACCTFILE.jcl:61`, `scripts/run_posting.sh:17`, `scripts/run_posting.sh:26`, `app/cbl/CBTRN02C.cbl:547` |
| `job:CARDFILE` | 4 | 5 | Must-not-break card master refresh. Same shape as ACCTFILE: delete, define, reload, rebuild the alternate index, and it closes and opens the CICS files around itself. run_full_batch.sh runs it ahead of POSTTRAN. | medium | `app/jcl/CARDFILE.jcl:36`, `app/jcl/CARDFILE.jcl:75`, `app/jcl/CARDFILE.jcl:26`, `scripts/run_full_batch.sh:20`, `scripts/run_full_batch.sh:47` |
| `sch:scripts/remote_refresh.sh` | 4 | 5 | A wrapper moves with the last family among the jobs it runs. remote_refresh.sh now runs ACCTFILE and CARDFILE, which are wave 5. | medium | `scripts/remote_refresh.sh:17`, `scripts/remote_refresh.sh:20` |
| `CORPT00C` | 3 | 5 | Must-not-break transaction report. The seed calls it read-only because the extractor sees no data edge. The program builds JCL text that runs PROC=TRANREPT and writes it to the JOBS TD queue, which CICS turns into a submitted job. A port cannot come before the report job it submits. | high | `app/cbl/CORPT00C.cbl:94`, `app/cbl/CORPT00C.cbl:518`, `app/csd/CARDDEMO.CSD:499` |
| `proc:TRANREPT` |  | 5 | Not placed by the seed: the only thing that names it is JCL text inside CORPT00C, so it has no edge. It holds the report steps, including CBTRN03C. It moves with CORPT00C and with the batch job that carries a copy of the same steps. | medium | `app/cbl/CORPT00C.cbl:94`, `app/proc/TRANREPT.prc:57`, `app/jcl/TRANREPT.jcl:59` |
| `CSUTLDTC` | 3 | 5 | Dependency after CORPT00C moved. Its first caller is now CORPT00C in wave 5, so the seed rule (earliest family that uses it) puts it there. It stays a shared subprogram called by COACTUPC and COTRN02C in wave 6. | medium | `app/cbl/CORPT00C.cbl:392`, `app/cbl/CORPT00C.cbl:412`, `app/cbl/COTRN02C.cbl:393` |
| `job:MNTTRDB2` | 1 | 7 | The extractor does not read the DSN RUN PROGRAM command inside an IKJEFT01 step, so it saw a utility. The step runs COBTUPDT, which writes the DB2 TRANSACTION_TYPE table. That is DB2 work, the seventh family. | high | `app/app-transaction-type-db2/jcl/MNTTRDB2.jcl:30`, `app/app-transaction-type-db2/cbl/COBTUPDT.cbl:137` |
| `sch:WEEKLY-TransactionTypesDBRefresh/MNTTRDB2` | 1 | 7 | The extractor does not read the DSN RUN PROGRAM command inside an IKJEFT01 step, so it saw a utility. The step runs COBTUPDT, which writes the DB2 TRANSACTION_TYPE table. That is DB2 work, the seventh family. | medium | `app/app-transaction-type-db2/jcl/MNTTRDB2.jcl:30`, `app/app-transaction-type-db2/cbl/COBTUPDT.cbl:137` |
| `job:TRANEXTR` | 1 | 7 | The job unloads DB2 tables with DSNTIAUL under IKJEFT01. The extractor sees no DB2 access in a JCL step, so it placed the job as a utility. | high | `app/app-transaction-type-db2/jcl/TRANEXTR.jcl:88`, `app/app-transaction-type-db2/jcl/TRANEXTR.jcl:27` |
| `sch:WEEKLY-TransactionTypesDBRefresh/TRANEXTR` | 1 | 7 | The job unloads DB2 tables with DSNTIAUL under IKJEFT01. The extractor sees no DB2 access in a JCL step, so it placed the job as a utility. | medium | `app/app-transaction-type-db2/jcl/TRANEXTR.jcl:88`, `app/app-transaction-type-db2/jcl/TRANEXTR.jcl:27` |
| `job:CREADB2` | 1 | 7 | The job creates and loads the DB2 objects through IKJEFT01 steps. It is DB2 work, and its DDL and control files are among the files the extractor did not read. | medium | `app/app-transaction-type-db2/jcl/CREADB21.jcl:52`, `app/app-transaction-type-db2/jcl/CREADB21.jcl:65` |
| `COBTUPDT` |  | 7 | Not placed by the seed. The extractor does not read the RUN PROGRAM command that MNTTRDB2 uses, so no step calls it. MNTTRDB2 does, and README lists the pair. | high | `app/app-transaction-type-db2/jcl/MNTTRDB2.jcl:30` |
| `CBPAUP0C` |  | 7 | Not placed by the seed. The extractor does not read the PARM of a DFSRRC00 step. CBPAUP0J runs this program as an IMS BMP. | high | `app/app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl:25` |
| `DBUNLDGS` |  | 7 | Not placed by the seed. UNLDGSAM runs it under DFSRRC00, and the extractor does not read that PARM. | high | `app/app-authorization-ims-db2-mq/jcl/UNLDGSAM.JCL:27` |
| `PAUDBLOD` |  | 7 | Not placed by the seed. LOADPADB runs it as an IMS BMP under DFSRRC00, and the extractor does not read that PARM. | high | `app/app-authorization-ims-db2-mq/jcl/LOADPADB.JCL:27` |
| `PAUDBUNL` |  | 7 | Not placed by the seed. UNLDPADB runs it under DFSRRC00, and the extractor does not read that PARM. | high | `app/app-authorization-ims-db2-mq/jcl/UNLDPADB.JCL:39` |

## Decisions worth defending

**Dependency over quadrant.** CBTRN02C is high-high and a must-not-break item, and the account, category balance and transaction masters it writes are read by programs in waves 2, 3, 6 and 7. It cannot go last. It goes in wave 5 of 7, and the thing that has to sit in front of it first is a data facade over ACCTDATA, TCATBAL and TRANSACT, plus a scheduler adapter that lets the new POSTTRAN be triggered by the legacy CA-7 chain (`app/scheduler/CardDemo.ca7:70`). CORPT00C is high-high and also a must-not-break item, and it goes with the batch report it submits, not before it.

**No high-high unit in the first three waves.** `modernization-assessment/risks.json` puts no high-high unit in waves 1 to 3, so the fourth reason for a move, an early high-high unit, did not arise. Wave 5 holds six high-high units, wave 6 four and wave 7 eight.

**Wave 5 is not cut.** It holds 26 units, one over the 25 unit line. The only cut with a boundary is at CBTRN02C (an articulation point in `analysis.articulation_points`). Splitting there puts the report, statements and export in a later wave than the posting writes, and leaves the new TRANSACT replicated back to legacy readers for that whole wave. That costs more than it isolates. If the client's team cannot staff 26 units at once, cut there.

**Wave 4 is not cut.** It holds 26 units, but 11 are build and sample jobs and procs listed in `do_not_port`, so the porting scope is 15 units.

**Left as the seed had them, on purpose.** XREFFILE, TCATBALF, CUSTFILE, DISCGRP, TRANTYPE and DUSRSECJ reload files that CBTRN02C or CBACT04C read, and they have the same shape as the refresh jobs I moved. I moved only what the client named or what a named item forces, because a plan that moves units for their shape alone is moving them because of their name. They run against legacy-owned files through the scheduler facade until wave 5. COCRDLIC stays in wave 6 because it XCTLs to COCRDUPC, which writes the card master.

**Unassigned.** CBTRN01C. No step, wrapper or scheduler entry runs it (`app/cbl/CBTRN01C.cbl:29`). It stays in the unknown dead-code bucket until someone at the client says what it was for.

**Facade list.** These are the things that have to exist before the waves that need them: the menu routing table in wave 3 (`app/cpy/COMEN02Y.cpy:28`), the data facade or replica for ACCTDATA and TRANSACT before wave 5, a scheduler adapter for the CA-7, Control-M and wrapper chains during waves 4 to 7, and the JOBS TD queue adapter for CORPT00C (`app/csd/CARDDEMO.CSD:499`).
