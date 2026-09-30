# 03 Waves

Target state: **refactor**, meaning the same behavior in restructured code, usually as services. The plan is in `modernization-assessment/waves.json`. The seed came from facts alone (`modernization-assessment/03a-wave-seed.md`). I kept the seed's units and order and changed four placements, listed under Deviations. Risk scores are in `modernization-assessment/risks.json`, and the wave field there is filled by `schema.py apply-waves`.

## The plan at a glance

| Wave | Family | Name | Units | Blast | Confidence | Risk quadrants of the scored units | Evidence |
|---|---|---|---|---|---|---|---|
| 1 | batch-utility | Operations utilities | 14 | low | medium | 5 low-high, 3 low-low | `app/jcl/CLOSEFIL.jcl:26`, `app/jcl/OPENFIL.jcl:26`, `scripts/run_posting.sh:13` |
| 2 | batch-readonly | Read-only batch extracts | 15 | low | medium | 2 high-low, 10 low-low | `app/cbl/CBACT01C.cbl:231`, `app/cbl/COBSWAIT.cbl:38`, `app/jcl/READACCT.jcl:32` |
| 3 | online-readonly | Sign-on, menus and read-only screens | 7 | medium | medium | 3 low-high, 4 low-low | `app/csd/CARDDEMO.CSD:317`, `app/cbl/COMEN01C.cbl:156`, `app/cpy/COMEN02Y.cpy:28` |
| 4 | batch-data-jobs | Build and file-transfer support | 11 | low | medium | 8 low-low | `app/jcl/DEFGDGD.jcl:27`, `app/jcl/TXT2PDF1.JCL:33`, `app/jcl/INTRDRJ1.JCL:18` |
| 5 | batch-writers | Nightly batch cycle: refresh, posting, interest, report, statements | 42 | high | medium | 8 high-high, 1 high-low, 17 low-high, 6 low-low | `app/jcl/POSTTRAN.jcl:23`, `app/jcl/TRANREPT.jcl:33`, `scripts/run_full_batch.sh:13` |
| 6 | online-writers | Online writers | 9 | high | medium | 4 high-high, 1 high-low, 3 low-high, 1 low-low | `app/cbl/COACTUPC.cbl:4100`, `app/cbl/COBIL00C.cbl:217`, `app/cbl/COTRN02C.cbl:449` |
| 7 | subsystem | Authorization, DB2 reference and MQ services | 25 | high | low | 15 high-high, 6 high-low, 1 low-low | `app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:668`, `app/app-transaction-type-db2/jcl/TRANEXTR.jcl:19`, `app/scheduler/CardDemo.controlm:28` |

Seven waves. One unit is not placed: CBTRN01C. Wave 5 has 42 units and is not cut. The argument is under wave 5.

## What must not break, and where it lands

The three items came as arguments. Each maps to units in the tree, so none goes to Open Questions as unmapped. The mapping is by name and by the labels in the wrappers, so it is `inference` that a client engineer should confirm.

| Must not break | Units | Wave | Evidence |
|---|---|---|---|
| Daily transaction posting | job:POSTTRAN running CBTRN02C, preceded by job:TRANBKP and job:TCATBALF and followed by job:TRANIDX; job:DALYREJS defines the reject GDG | 5 | `app/jcl/POSTTRAN.jcl:20`, `app/jcl/POSTTRAN.jcl:23`, `scripts/run_posting.sh:26` |
| The account and card master refresh | job:ACCTFILE and job:CARDFILE, with job:XREFFILE and job:CUSTFILE submitted beside them | 5 | `scripts/remote_refresh.sh:16`, `scripts/remote_refresh.sh:17`, `scripts/remote_refresh.sh:20` |
| The transaction report | job:TRANREPT running CBTRN03C; the online route CORPT00C with proc:TRANREPT; reference files from job:TRANTYPE and job:TRANCATG (wave 5) fed by job:TRANEXTR (wave 7) | 5, fed from 7 | `app/jcl/TRANREPT.jcl:1`, `app/cbl/CORPT00C.cbl:94`, `app/app-transaction-type-db2/jcl/TRANEXTR.jcl:19` |

All three sit in wave 5, and the report has an input from wave 7. That is the first place a wrong port is silent, so the harness for waves 1 to 4 has to be ready before wave 5 starts (see `modernization-assessment/06-test-strategy.md`).

## Wave 1. Operations utilities

Family `batch-utility`. Blast radius low. Confidence medium.

Units (14): `job:CBADMCDJ`, `job:CLOSEFIL`, `job:DEFCUST`, `job:ESDSRRDS`, `job:FTPJCLS`, `job:LISTFILS`, `job:OPENFIL`, `job:RACFCMDS`, `sch:DAILY-TransactionBackup/CLOSEFIL`, `sch:DAILY-TransactionBackup/OPENFIL`, `sch:MONTHLY-InterestCalculation/CLOSEFIL`, `sch:MONTHLY-InterestCalculation/OPENFIL`, `sch:WEEKLY-DisclosureGroupsRefresh/CLOSEFIL`, `sch:WEEKLY-DisclosureGroupsRefresh/OPENFIL`

**Why this cut.** Batch jobs that run no application program and touch no shared dataset: CICS file close and open through SDSF, a CSD update, RACF commands, an FTP demo, a catalog listing and an ESDS/RRDS demo. The family is sound as a toolchain proof, because it is the cheapest place to prove batch scheduling, return-code handling and the first harness. It is close to a chore. CLOSEFIL and OPENFIL name CICS region CICSAWSA and five files (app/jcl/CLOSEFIL.jcl:26-30), so they only make sense while a CICS region exists. The Control-M folders that call them also call wave 5 jobs (app/scheduler/CardDemo.controlm:5 and :9), so Control-M stays the orchestrator across waves 1 to 5. job:CREADB2 left this wave because it creates DB2 tables. Five units here score low-high in risks.json (CLOSEFIL, OPENFIL, CBADMCDJ, RACFCMDS, FTPJCLS): the port is easy and the verification is the work, so prove the harness on the low-low utilities first and treat those five as the last step of the wave.

**Unblocks.** The CICS close and open bracket that every wave 5 refresh and posting run needs (scripts/run_posting.sh:13 and :34). Apart from that bracket it unblocks nothing: it is a chore that proves the toolchain.

## Wave 2. Read-only batch extracts

Family `batch-readonly`. Blast radius low. Confidence medium.

Units (15): `CBACT01C`, `CBACT02C`, `CBACT03C`, `CBCUS01C`, `CBIMPORT`, `COBSWAIT`, `job:CBIMPORT`, `job:READACCT`, `job:READCARD`, `job:READCUST`, `job:READXREF`, `job:WAITSTEP`, `sch:DAILY-TransactionBackup/WAITSTEP`, `sch:MONTHLY-InterestCalculation/WAITSTEP`, `sch:WEEKLY-DisclosureGroupsRefresh/WAITSTEP`

**Why this cut.** Batch programs that read a master and write only private output files. Sound as a wave for one reason: it puts the first COBOL programs on the target and forces the two assembler routines the extractor cannot read, COBDATFT (app/cbl/CBACT01C.cbl:231) and MVSWAIT (app/cbl/COBSWAIT.cbl:38), to be reimplemented and tested once. CBIMPORT reads EXPORT.DATA, which CBEXPORT writes in wave 5, so it is tested on a frozen file until then. Confidence stays medium while two assembler sources are unread.

**Unblocks.** Shared file-status and abend handling for batch programs (CEE3ABD is called by 11 batch programs) and the date routine that CBACT01C needs. A business stakeholder gets nothing new from it.

## Wave 3. Sign-on, menus and read-only screens

Family `online-readonly`. Blast radius medium. Confidence medium.

Units (7): `COACTVWC`, `COADM01C`, `COCRDSLC`, `COMEN01C`, `COSGN00C`, `COTRN00C`, `COTRN01C`

**Why this cut.** Seven online programs that write no shared dataset. Sign-on, main menu and admin menu form one call cycle and the transaction list and view form another, so each cycle moves whole (analysis.sccs). Ten of the 28 computed calls are in these programs. All are XCTL to a program name held in a COMMAREA field. The names come from two tables, COMEN02Y (11 names, app/cpy/COMEN02Y.cpy:28-89) and COADM02Y (6 names, app/cpy/COADM02Y.cpy:29-53), and from literal MOVEs, so no computed call here can reach a batch program. That bounds the calls and does not remove them, so confidence is medium. The menu is the router for waves 6 and 7, so it needs a route-to-legacy facade until those waves land. The screens read ACCTDATA, CARDDATA, TRANSACT and USRSEC, which later waves write, so a shared data path is a precondition. CORPT00C and CSUTLDTC left this wave because CORPT00C is not read-only.

**Unblocks.** Sign-on and the menu router that every online wave uses: COSGN00C and COMEN01C each have 12 callers (analysis.fan_in). A stakeholder can name it: staff sign in and view accounts, cards and transactions on the new platform.

## Wave 4. Build and file-transfer support

Family `batch-data-jobs`. Blast radius low. Confidence medium.

Units (11): `job:CBLDBMS`, `job:CICCMP`, `job:CNJBATMP`, `job:DEFGDGD`, `job:IMSMQCMP`, `job:INTRDRJ1`, `job:INTRDRJ2`, `job:TXT2PDF1`, `proc:BUILDBAT`, `proc:BUILDBMS`, `proc:BUILDONL`

**Why this cut.** The seed puts these here because they read shared libraries or datasets through utilities. In fact they are legacy compile jobs and procs (BMSCMP, CICCMP, BATCMP, IMSMQCMP, BUILDBAT, BUILDBMS, BUILDONL), GDG definitions (DEFGDGD), an internal reader demo (INTRDRJ1, INTRDRJ2) and a text-to-PDF job (TXT2PDF1). The family is not a sound wave: most of it is retired with the legacy build, not ported, and it is a chore. TXT2PDF1 reads STATEMNT.PS, which CREASTMT writes in wave 5, so it runs against a frozen statement format until then.

**Unblocks.** The GDG bases for TRANTYPE.BKUP, TRANCATG.PS.BKUP and DISCGRP.BKUP (app/jcl/DEFGDGD.jcl:27, :50, :73) that reference-file jobs in waves 5 and 7 write to (app/app-transaction-type-db2/jcl/TRANEXTR.jcl:35 and :46). Nothing else. Retiring the build procs waits until wave 7 is done.

## Wave 5. Nightly batch cycle

Family `batch-writers`. Blast radius high. Confidence medium.

Units (42): `CBACT04C`, `CBEXPORT`, `CBSTM03A`, `CBSTM03B`, `CBTRN02C`, `CBTRN03C`, `CORPT00C`, `CSUTLDTC`, `job:ACCTFILE`, `job:CARDFILE`, `job:CBEXPORT`, `job:COMBTRAN`, `job:CREASTMT`, `job:CUSTFILE`, `job:DALYREJS`, `job:DEFGDGB`, `job:DISCGRP`, `job:DUSRSECJ`, `job:INTCALC`, `job:POSTTRAN`, `job:PRTCATBL`, `job:REPRTEST`, `job:REPTFILE`, `job:SORTTEST`, `job:TCATBALF`, `job:TRANBKP`, `job:TRANCATG`, `job:TRANFILE`, `job:TRANIDX`, `job:TRANREPT`, `job:TRANTYPE`, `job:XREFFILE`, `proc:REPROC`, `proc:TRANREPT`, `sch:DAILY-TransactionBackup/TRANBKP`, `sch:MONTHLY-InterestCalculation/COMBTRAN`, `sch:MONTHLY-InterestCalculation/INTCALC`, `sch:WEEKLY-DisclosureGroupsRefresh/DISCGRP`, `sch:scripts/remote_refresh.sh`, `sch:scripts/run_full_batch.sh`, `sch:scripts/run_interest_calc.sh`, `sch:scripts/run_posting.sh`

**Why this cut.** Every batch job that writes a dataset another entry point uses. It holds all three must-not-break items: the account and card master refresh (job:ACCTFILE, job:CARDFILE), daily posting (job:POSTTRAN with CBTRN02C) and the transaction report (job:TRANREPT with CBTRN03C, and the online route CORPT00C with proc:TRANREPT). At 42 units it is over 25, and it is not cut. One argument describes it: the jobs form one chain where each job's output is the next job's input (scripts/run_full_batch.sh:13-66, TRANBKP then POSTTRAN then INTCALC then TRANBKP then COMBTRAN). A cut at an articulation point (CBTRN02C, CBACT04C, CBTRN03C, CBSTM03A, CBEXPORT) would put half a chain on each platform. If the client needs a smaller first step, the least damaging cut is at CBSTM03A, whose only consumer in the tree is TXT2PDF1. CORPT00C brings one computed call into this wave (app/cbl/CORPT00C.cbl:548), so confidence is not high. The wave is high-high for CBTRN02C, CBACT04C, CBTRN03C and CBSTM03A, so it sits in the second half of the plan. Reference data flows in backwards: TRANEXTR (wave 7) writes TRANTYPE.PS and TRANCATG.PS that jobs in this wave reload for the report, so DB2 stays the source for those until wave 7. TRANBKP and TRANREPT each write a new TRANSACT.BKUP generation and COMBTRAN reads generation (0) (app/jcl/TRANBKP.jcl:33, app/jcl/TRANREPT.jcl:33, app/jcl/COMBTRAN.jcl:24), so that versioning must be replaced as one piece.

**Unblocks.** One owner for the account, card, cross reference, category balance and transaction masters, which lets wave 6 move the online writers. A stakeholder can name it: the nightly posting, interest, statement and report cycle runs on the new platform.

## Wave 6. Online writers

Family `online-writers`. Blast radius high. Confidence medium.

Units (9): `COACTUPC`, `COBIL00C`, `COCRDLIC`, `COCRDUPC`, `COTRN02C`, `COUSR00C`, `COUSR01C`, `COUSR02C`, `COUSR03C`

**Why this cut.** Online programs that write a dataset another entry point also uses: account update, card update, bill payment, add transaction, user admin and card list. All nine have computed calls, bounded by the same two menu tables and literal MOVEs, so confidence cannot be high. COACTUPC is 3,368 lines with 43 REDEFINES and a two-file update with rollback (app/cbl/COACTUPC.cbl:4100). COBIL00C and COTRN02C build the next transaction id from the last key plus one (app/cbl/COBIL00C.cbl:217, app/cbl/COTRN02C.cbl:449), which ties them to the id format the batch cycle writes. The wave is sound only after wave 5, because two owners of one master is the failure to avoid.

**Unblocks.** Retires the last legacy writers of ACCTDATA, CARDDATA, TRANSACT and USRSEC, so the VSAM masters can be replaced. A stakeholder can name it: staff update accounts, cards, payments and users on the new platform.

## Wave 7. Authorization, DB2 reference and MQ services

Family `subsystem`. Blast radius high. Confidence low.

Units (25): `CBPAUP0C`, `COACCT01`, `COBTUPDT`, `CODATE01`, `COPAUA0C`, `COPAUS0C`, `COPAUS1C`, `COPAUS2C`, `COTRTLIC`, `COTRTUPC`, `DBUNLDGS`, `PAUDBLOD`, `PAUDBUNL`, `job:CBPAUP0J`, `job:CIDBCMP`, `job:CREADB2`, `job:DBPAUTP0`, `job:LOADPADB`, `job:MNTTRDB2`, `job:TRANEXTR`, `job:UNLDGSAM`, `job:UNLDPADB`, `proc:BLDCIDB2`, `sch:WEEKLY-TransactionTypesDBRefresh/MNTTRDB2`, `sch:WEEKLY-TransactionTypesDBRefresh/TRANEXTR`

**Why this cut.** Everything that touches DB2, IMS or MQ: the real-time authorization subsystem (COPAUA0C and its screens, IMS load and unload jobs), the DB2 transaction-type maintenance (COTRTLIC, COTRTUPC, COBTUPDT) and the two MQ services (COACCT01, CODATE01). It holds 25 units and is described by one sentence, so it is not cut, although it is two subsystems. Confidence is low: the IMS DBD and PSB, the DB2 DDL and DCLGEN and the DB2 control members are not parsed, and four programs make computed calls. COPAUS0C and COPAUS1C form a call cycle and move together. job:CREADB2 joined from wave 1 because it creates the DB2 tables. A Control-M condition makes WEEKLY-TransactionTypesDBRefresh run before the wave 1 CLOSEFIL of the disclosure group folder (app/scheduler/CardDemo.controlm:28 and :34), which is a backward edge from this wave to wave 1.

**Unblocks.** Nothing later. It is last because these objects are the least understood here. It retires the mainframe subsystems. A stakeholder can name it: card authorization runs on the new platform.

## Deviations from the seed

Four placements changed. Everything else is the seed as written.

| Unit | From wave | To wave | Reason | Evidence |
|---|---|---|---|---|
| `job:CREADB2` | 1 | 7 | The seed treated it as a utility that touches no shared data. It creates the DB2 transaction-type tables and loads them with DSNTIAD and DSNTEP4, driven by control members (DB2CREAT, DB2LTTYP, DB2LTCAT) that the extractor lists as not parsed. That makes it a DB2 job, and DB2 jobs are family 7. | `app/app-transaction-type-db2/jcl/CREADB21.jcl:52`, `app/app-transaction-type-db2/jcl/CREADB21.jcl:59`, `app/app-transaction-type-db2/jcl/CREADB21.jcl:72` |
| `CORPT00C` | 3 | 5 | The seed treated it as a read-only online screen. It holds JCL text and writes it to the JOBS queue (internal reader), which runs proc:TRANREPT. That proc unloads TRANSACT into a new TRANSACT.BKUP generation and runs CBTRN03C, so it writes a dataset the batch cycle also uses. It is also the online route to a must-not-break item. It moves to the wave that owns the report so the report path is ported and tested as one piece. | `app/cbl/CORPT00C.cbl:94`, `app/cbl/CORPT00C.cbl:517`, `app/csd/CARDDEMO.CSD:499`, `app/proc/TRANREPT.prc:31` |
| `proc:TRANREPT` | not placed | 5 | The seed left it unplaced because only JCL text inside COBOL names it. That text is what CORPT00C submits for the transaction report, a must-not-break item, so it is live. It joins the wave of CORPT00C and job:TRANREPT. | `app/cbl/CORPT00C.cbl:94`, `app/proc/TRANREPT.prc:1` |
| `CSUTLDTC` | 3 | 5 | The seed places a shared unit with the earliest family that uses it. Its callers are CORPT00C, COACTUPC and COTRN02C. CORPT00C moved to wave 5, so the earliest caller is now in wave 5. | `app/cbl/CORPT00C.cbl:392`, `app/cbl/COACTUPC.cbl:4232`, `app/cbl/COTRN02C.cbl:393` |

I considered and did not make these changes. The seed's rule 4 (a high-high unit placed early) did not fire: no high-high unit is in waves 1 to 4 after CORPT00C moved. TXT2PDF1 (wave 4) reads the statement file that CREASTMT (wave 5) writes, and CBIMPORT (wave 2) reads the file CBEXPORT (wave 5) writes. Both are consumers ahead of their producers, which is safe if the file format stays frozen, so I did not move them. Wave 5 is over 25 units and I did not cut it. The chain in `scripts/run_full_batch.sh:47` to `scripts/run_full_batch.sh:66` passes each job's output to the next, so one sentence describes it.

## Not placed

| Unit | Reason | Evidence |
|---|---|---|
| `CBTRN01C` | Not reached by any static edge. No job, scheduler or wrapper in the tree runs it and its six DDs are unmapped (app/cbl/CBTRN01C.cbl:29-58). The 28 computed calls are bounded by the COMEN02Y and COADM02Y tables and literal MOVEs, and none names a batch program, so they do not reach it. Whether it runs from JCL outside the tree is a question for the client. | `app/cbl/CBTRN01C.cbl:29` |

## What a wave still needs that the plan does not give it

- **A data path for wave 3.** Its screens read ACCTDATA, CARDDATA, TRANSACT and USRSEC, which legacy programs keep writing until waves 5 and 6. Whether that is replication, a shared store or a read facade is a client decision. `inference`, from the reader and writer counts in `analysis.data_hubs`.

- **A route-to-legacy facade in the menu.** COMEN01C names its target from a table. Options that point at programs in later waves must still reach the legacy program. Evidence: `app/cbl/COMEN01C.cbl:184`, `app/cpy/COMEN02Y.cpy:28`.

- **One scheduler.** Control-M conditions cross the wave 1 and wave 5 boundary and the wave 7 to wave 1 boundary (`app/scheduler/CardDemo.controlm:5`, `app/scheduler/CardDemo.controlm:28`), so the scheduler stays the orchestrator until wave 7 ends. Which scheduler that is remains open.
