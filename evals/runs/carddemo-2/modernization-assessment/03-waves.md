# 03 Waves

Target state: refactor. Seven waves, cut from the extractor's seed (`modernization-assessment/03a-wave-seed.md`) with 17 recorded deviations. The machine readable plan is `modernization-assessment/waves.json`. Risk scores are in `modernization-assessment/risks.json`.

The seed puts every entry point in one family, in a fixed order, and a unit used by several entry points moves with the earliest family that uses it. I kept that order. I changed it in four places, each for a reason the seed could not see, and I did not cut the largest wave.

## The must-not-break items and where they land

All three items map to units in the tree. The mapping is by job comment and wrapper label, so it is inference the client should confirm.

| Item | Units | Wave | Basis | Confidence | Evidence |
|---|---|---|---|---|---|
| Daily transaction posting | job:POSTTRAN, CBTRN02C. Prerequisites in the same chain: job:TRANBKP, job:TCATBALF, job:TRANIDX, job:DALYREJS, job:CLOSEFIL, job:OPENFIL, wrapper sch:scripts/run_posting.sh | 5 | The job comment says it processes the daily transaction file and updates the transaction master. The wrapper calls it the core processing job. | high | `app/jcl/POSTTRAN.jcl:20`, `scripts/run_posting.sh:25` |
| Account and card master refresh | job:ACCTFILE, job:CARDFILE. Neighbours in the same wrappers: job:XREFFILE, job:CUSTFILE | 5 | The wrapper labels them Refresh Account Master file and Refresh Card Master. | high | `scripts/remote_refresh.sh:16`, `scripts/remote_refresh.sh:19` |
| The transaction report | job:TRANREPT, CBTRN03C, proc:REPROC, proc:TRANREPT, CORPT00C (online trigger). Feeds: job:TRANTYPE, job:TRANCATG, job:TRANEXTR | 5 (feeds in 5 and 7) | The job title is TRANSACTION REPORT, and CORPT00C builds the same job at run time. | high | `app/jcl/TRANREPT.jcl:1`, `app/cbl/CORPT00C.cbl:94` |

Whether XREFFILE and CUSTFILE belong to the master refresh item is an open question. They are in the same wrapper sequence and CBTRN02C validates through the cross reference, so I treated them as in scope for testing.

## Summary

| Wave | Family | Name | Units | Blast radius | Confidence | Evidence |
|---|---|---|---|---|---|---|
| 1 | batch-utility | Environment and utility jobs | 6 | low | medium | `app/app-transaction-type-db2/jcl/CREADB21.jcl:1`, `app/jcl/CBADMCDJ.jcl:1`, +1 more in `modernization-assessment/waves.json` |
| 2 | batch-readonly | Read-only batch extracts | 10 | low | medium | `app/jcl/CBIMPORT.jcl:1`, `app/jcl/READACCT.jcl:1`, +1 more in `modernization-assessment/waves.json` |
| 3 | online-readonly | Sign-on, menu and read-only screens | 8 | high | medium | `app/csd/CARDDEMO.CSD:317`, `app/csd/CARDDEMO.CSD:327`, +1 more in `modernization-assessment/waves.json` |
| 4 | batch-data-jobs | Build and reference-data backup jobs | 10 | low | medium | `app/jcl/DEFGDGD.jcl:39`, `app/jcl/INTRDRJ1.JCL:9`, +1 more in `modernization-assessment/waves.json` |
| 5 | batch-writers | Batch window: posting, master refresh, transaction report, interest, statements | 55 | high | medium | `app/cbl/CBACT04C.cbl:41`, `app/cbl/CBEXPORT.cbl:65`, +5 more in `modernization-assessment/waves.json` |
| 6 | online-writers | Online updates | 9 | high | medium | `app/cbl/COACTUPC.cbl:573`, `app/cbl/COBIL00C.cbl:41`, +1 more in `modernization-assessment/waves.json` |
| 7 | subsystem | Authorization and transaction-type subsystems (IMS, MQ, DB2) | 25 | high | low | `app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:956`, `app/app-authorization-ims-db2-mq/cbl/COPAUS2C.cbl:141`, +2 more in `modernization-assessment/waves.json` |

## Wave 1. Environment and utility jobs

Family: batch-utility. Blast radius: low. Confidence: medium.

**Why this is a wave.** Six one-off jobs that touch no shared dataset and run no application program: CICS resource definitions, stray cluster definitions, an ESDS test copy, an FTP job, a catalog listing and RACF commands. It is a sound first wave because nothing can break in it, and it measures the team's real conversion velocity. Most of these should be retired, not ported (modernization-assessment/risks.json do_not_port). The seed put CLOSEFIL and OPENFIL here and CREADB2 here; both moved, see deviations.

**What it unblocks.** Nothing in a later wave. This wave is a chore: it proves the job conversion toolchain and clears environment jobs. It also forces the client to say who owns the in-stream login lines in app/jcl/FTPJCL.JCL:33-35.

Evidence: `app/app-transaction-type-db2/jcl/CREADB21.jcl:1`, `app/jcl/CBADMCDJ.jcl:1`, `app/jcl/CLOSEFIL.jcl:1`

Units (6): `job:CBADMCDJ`, `job:DEFCUST`, `job:ESDSRRDS`, `job:FTPJCLS`, `job:LISTFILS`, `job:RACFCMDS`

## Wave 2. Read-only batch extracts

Family: batch-readonly. Blast radius: low. Confidence: medium.

**Why this is a wave.** Four display or extract programs and CBIMPORT, with their jobs. They only read the account, card, customer and cross reference masters, so the wave can be deployed and rolled back on its own, and its boundary is testable by diffing the printed output. It is a sound wave because it proves reading the VSAM masters from the new platform before anything writes them. WAITSTEP and COBSWAIT moved out to wave 5, see deviations. CBIMPORT writes a DD that no JCL maps (app/cbl/CBIMPORT.cbl:63), so its target is unknown and the confidence is not high.

**What it unblocks.** The read access layer over ACCTDATA, CARDDATA, CUSTDATA and CARDXREF that wave 3 (online views) and wave 5 (posting reads the same masters) both need, and the CVEXPORT layout that CBEXPORT and CBIMPORT share.

Evidence: `app/jcl/CBIMPORT.jcl:1`, `app/jcl/READACCT.jcl:1`, `app/jcl/READCARD.jcl:1`

Units (10): `CBACT01C`, `CBACT02C`, `CBACT03C`, `CBCUS01C`, `CBIMPORT`, `job:CBIMPORT`, `job:READACCT`, `job:READCARD`, `job:READCUST`, `job:READXREF`

## Wave 3. Sign-on, menu and read-only screens

Family: online-readonly. Blast radius: high. Confidence: medium.

**Why this is a wave.** Online transactions that write nothing: sign-on, the two menus, account view, card view, transaction list and view, and the date check. Readers move before writers, so the new screens read the legacy files through the wave 2 access layer. It is a sound wave only with a routing shim: COSGN00C, COMEN01C and COADM01C form one call cycle that every other online program XCTLs back to (fan-in 12, 12 and 7), and the menu dispatches by table (app/cpy/COMEN02Y.cpy:28-89) to programs in waves 5, 6 and 7 that have not moved. The three move together because they are one strongly connected component, as are COTRN00C and COTRN01C. CORPT00C moved out to wave 5. Six programs make computed calls, so confidence is not high.

**What it unblocks.** The online front door and the routing shim that waves 5 to 7 hang behind, and the replacement of COSGN00C's password check with the target identity service.

Evidence: `app/csd/CARDDEMO.CSD:317`, `app/csd/CARDDEMO.CSD:327`, `app/csd/CARDDEMO.CSD:347`

Units (8): `COACTVWC`, `COADM01C`, `COCRDSLC`, `COMEN01C`, `COSGN00C`, `COTRN00C`, `COTRN01C`, `CSUTLDTC`

## Wave 4. Build and reference-data backup jobs

Family: batch-data-jobs. Blast radius: low. Confidence: medium.

**Why this is a wave.** Ten JCL jobs and procs that run only utilities over shared datasets. Nine are compile jobs, build procs or internal reader demonstrations that the target build pipeline replaces (do_not_port), and DEFGDGD backs up three reference files into generation datasets. As a wave it delivers no business capability and is really retirement work. It is kept as the seed cut it because its only tie to a later wave is that DEFGDGD reads three reference flat files that wave 5 and wave 7 jobs load or unload, and those files stay as they are until then. TXT2PDF1 moved out to wave 5, see deviations.

**What it unblocks.** Nothing. This wave is a chore: retire the build jobs when the target pipeline builds the ported code.

Evidence: `app/jcl/DEFGDGD.jcl:39`, `app/jcl/INTRDRJ1.JCL:9`, `app/jcl/INTRDRJ2.JCL:9`

Units (10): `job:CBLDBMS`, `job:CICCMP`, `job:CNJBATMP`, `job:DEFGDGD`, `job:IMSMQCMP`, `job:INTRDRJ1`, `job:INTRDRJ2`, `proc:BUILDBAT`, `proc:BUILDBMS`, `proc:BUILDONL`

## Wave 5. Batch window: posting, master refresh, transaction report, interest, statements

Family: batch-writers. Blast radius: high. Confidence: medium.

**Why this is a wave.** Every batch job and program that writes a dataset another entry point also uses. All three must-not-break items are here: daily posting (job:POSTTRAN, CBTRN02C), the account and card master refresh (job:ACCTFILE, job:CARDFILE) and the transaction report (job:TRANREPT, CBTRN03C, proc:REPROC, and after deviation proc:TRANREPT and CORPT00C). CBACT04C, the statements and the export are here too. It has 55 units after the deviations, which is over the 25 unit guide, and it is not cut. One sentence describes it (batch programs and jobs that write shared datasets), and every articulation point inside it (CBTRN02C, CBTRN03C, CBACT04C, CBSTM03A, CBEXPORT) splits off only a private output while the shared masters ACCTDATA, TRANSACT and TCATBALF keep writers on both sides, so a cut would leave two systems writing one dataset. Several high-high units sit here (CBTRN02C, CBTRN03C, CBACT04C, CBSTM03A, CORPT00C, job:TRANBKP, job:COMBTRAN, job:TRANREPT). The first three are must-not-break or on the month-end path, so they cannot be pushed past the datasets they write. Dataset ownership must not flip in this wave: ACCTDATA has four writers and TRANSACT three, and the online writers are in wave 6, so the plan keeps VSAM as the system of record through wave 6 and ports the program logic behind a record level access facade. CLOSEFIL, OPENFIL and WAITSTEP moved in from waves 1 and 2 and TXT2PDF1 from wave 4, see deviations. Inside the wave the order is the wrapper order in scripts/run_full_batch.sh:13-66, and the port order is for the wave N plan.

**What it unblocks.** The batch side of the system of record. With this wave done, the only remaining writers of ACCTDATA, CARDDATA, TRANSACT and USRSEC are the wave 6 online programs, and CLOSEFIL and OPENFIL can be retired.

Evidence: `app/cbl/CBACT04C.cbl:41`, `app/cbl/CBEXPORT.cbl:65`, `app/cbl/CBSTM03A.CBL:39`, `app/cbl/CORPT00C.cbl:94`, `scripts/run_posting.sh:13`, `app/scheduler/CardDemo.controlm:5`, +1 more in `modernization-assessment/waves.json`

Units (55): `CBACT04C`, `CBEXPORT`, `CBSTM03A`, `CBSTM03B`, `CBTRN02C`, `CBTRN03C`, `COBSWAIT`, `CORPT00C`, `job:ACCTFILE`, `job:CARDFILE`, `job:CBEXPORT`, `job:CLOSEFIL`, `job:COMBTRAN`, `job:CREASTMT`, `job:CUSTFILE`, `job:DALYREJS`, `job:DEFGDGB`, `job:DISCGRP`, `job:DUSRSECJ`, `job:INTCALC`, `job:OPENFIL`, `job:POSTTRAN`, `job:PRTCATBL`, `job:REPRTEST`, `job:REPTFILE`, `job:SORTTEST`, `job:TCATBALF`, `job:TRANBKP`, `job:TRANCATG`, `job:TRANFILE`, `job:TRANIDX`, `job:TRANREPT`, `job:TRANTYPE`, `job:TXT2PDF1`, `job:WAITSTEP`, `job:XREFFILE`, `proc:REPROC`, `proc:TRANREPT`, `sch:DAILY-TransactionBackup/CLOSEFIL`, `sch:DAILY-TransactionBackup/OPENFIL`, `sch:DAILY-TransactionBackup/TRANBKP`, `sch:DAILY-TransactionBackup/WAITSTEP`, `sch:MONTHLY-InterestCalculation/CLOSEFIL`, `sch:MONTHLY-InterestCalculation/COMBTRAN`, `sch:MONTHLY-InterestCalculation/INTCALC`, `sch:MONTHLY-InterestCalculation/OPENFIL`, `sch:MONTHLY-InterestCalculation/WAITSTEP`, `sch:WEEKLY-DisclosureGroupsRefresh/CLOSEFIL`, `sch:WEEKLY-DisclosureGroupsRefresh/DISCGRP`, `sch:WEEKLY-DisclosureGroupsRefresh/OPENFIL`, `sch:WEEKLY-DisclosureGroupsRefresh/WAITSTEP`, `sch:scripts/remote_refresh.sh`, `sch:scripts/run_full_batch.sh`, `sch:scripts/run_interest_calc.sh`, `sch:scripts/run_posting.sh`

High-high units in this wave: `CBACT04C`, `CBSTM03A`, `CBSTM03B`, `CBTRN02C`, `CBTRN03C`, `CORPT00C`, `job:COMBTRAN`, `job:CREASTMT`, `job:TRANBKP`, `job:TRANREPT`. See `modernization-assessment/risks.json` for the scores.

## Wave 6. Online updates

Family: online-writers. Blast radius: high. Confidence: medium.

**Why this is a wave.** Online transactions that write a shared dataset: account update, bill payment, card update, transaction add, user add, update and delete, and the two list screens that XCTL into them. It is a sound wave because every remaining writer of the masters moves together, so the datasets can change owner at its end. COBIL00C and COTRN02C build transaction ids by browsing to the last key and adding 1 (app/cbl/COBIL00C.cbl:212-217, app/cbl/COTRN02C.cbl:444-449), which must be replaced by a sequence that cannot collide with the batch posting. Nine programs make computed calls, so confidence is not high.

**What it unblocks.** Change of ownership of ACCTDATA, CARDDATA, TRANSACT and USRSEC to the target store, and retirement of the CICS file definitions and VSAM for those files.

Evidence: `app/cbl/COACTUPC.cbl:573`, `app/cbl/COBIL00C.cbl:41`, `app/cbl/COCRDUPC.cbl:251`

Units (9): `COACTUPC`, `COBIL00C`, `COCRDLIC`, `COCRDUPC`, `COTRN02C`, `COUSR00C`, `COUSR01C`, `COUSR02C`, `COUSR03C`

High-high units in this wave: `COACTUPC`, `COBIL00C`, `COCRDUPC`, `COTRN02C`. See `modernization-assessment/risks.json` for the scores.

## Wave 7. Authorization and transaction-type subsystems (IMS, MQ, DB2)

Family: subsystem. Blast radius: high. Confidence: low.

**Why this is a wave.** Everything that touches DB2, IMS or MQ: the card authorization path, the DB2 transaction type maintenance, the two MQ services, and their jobs. It goes last because the extractor reads none of the DBD, PSB, DDL, DCLGEN or control card files (five groups of unparsed file types), so its couplings are the least known and the confidence is low. COPAUS0C and COPAUS1C are one component and move together. job:CREADB2 moved in from wave 1, see deviations. The DB2 unload (job:TRANEXTR) feeds the TRANTYPE and TRANCATG files that the wave 5 report reads, so its output layout is a contract with wave 5.

**What it unblocks.** Retirement of CICS, IMS and MQ dependence, and the last removal of legacy runtime.

Evidence: `app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:956`, `app/app-authorization-ims-db2-mq/cbl/COPAUS2C.cbl:141`, `app/app-authorization-ims-db2-mq/cbl/DBUNLDGS.CBL:222`, `app/app-transaction-type-db2/jcl/CREADB21.jcl:40`

Units (25): `CBPAUP0C`, `COACCT01`, `COBTUPDT`, `CODATE01`, `COPAUA0C`, `COPAUS0C`, `COPAUS1C`, `COPAUS2C`, `COTRTLIC`, `COTRTUPC`, `DBUNLDGS`, `PAUDBLOD`, `PAUDBUNL`, `job:CBPAUP0J`, `job:CIDBCMP`, `job:CREADB2`, `job:DBPAUTP0`, `job:LOADPADB`, `job:MNTTRDB2`, `job:TRANEXTR`, `job:UNLDGSAM`, `job:UNLDPADB`, `proc:BLDCIDB2`, `sch:WEEKLY-TransactionTypesDBRefresh/MNTTRDB2`, `sch:WEEKLY-TransactionTypesDBRefresh/TRANEXTR`

High-high units in this wave: `CBPAUP0C`, `COACCT01`, `COBTUPDT`, `COPAUA0C`, `COPAUS0C`, `COPAUS1C`, `COPAUS2C`, `COTRTUPC`, `PAUDBLOD`, `job:CBPAUP0J`, `job:LOADPADB`, `job:MNTTRDB2`, `job:TRANEXTR`. See `modernization-assessment/risks.json` for the scores.

## Deviations from the seed

Each row moves a unit for a reason the extractor could not see or a dependency it does not weigh. The evidence is in `modernization-assessment/waves.json`.

| Unit | From | To | Reason | Evidence |
|---|---|---|---|---|
| `CORPT00C` | 3 | 5 | The seed calls it an online reader. It holds JCL text with EXEC PROC=TRANREPT (app/cbl/CORPT00C.cbl:94) and writes it to the JOBS transient data queue (app/cbl/CORPT00C.cbl:517), so a running program submits the batch report chain, whose REPRO cuts a new TRANSACT.BKUP generation (app/proc/TRANREPT.prc:31). It is the online trigger of a must-not-break item and belongs with the chain it starts. | `app/cbl/CORPT00C.cbl:94`, `app/cbl/CORPT00C.cbl:517`, `app/proc/TRANREPT.prc:31` |
| `proc:TRANREPT` | unassigned | 5 | The seed left it unassigned because only JCL text inside CORPT00C names it. That text is submitted at run time, and the proc is the report chain of the must-not-break transaction report, so it moves with job:TRANREPT and proc:REPROC in wave 5. Its dead-code bucket stays unknown. | `app/cbl/CORPT00C.cbl:94`, `app/cbl/CORPT00C.cbl:517`, `app/proc/TRANREPT.prc:31` |
| `job:CLOSEFIL`, `job:OPENFIL`, `job:WAITSTEP`, `COBSWAIT`, `sch:DAILY-TransactionBackup/CLOSEFIL`, `sch:DAILY-TransactionBackup/OPENFIL`, `sch:MONTHLY-InterestCalculation/CLOSEFIL`, `sch:MONTHLY-InterestCalculation/OPENFIL`, `sch:WEEKLY-DisclosureGroupsRefresh/CLOSEFIL`, `sch:WEEKLY-DisclosureGroupsRefresh/OPENFIL`, `sch:DAILY-TransactionBackup/WAITSTEP`, `sch:MONTHLY-InterestCalculation/WAITSTEP`, `sch:WEEKLY-DisclosureGroupsRefresh/WAITSTEP` | 1/2 | 5 | Temporal parent or child of wave 5 jobs. scripts/run_posting.sh starts with CLOSEFIL and ends with OPENFIL around ACCTFILE, TRANBKP, POSTTRAN and TRANIDX, and the Control-M folders chain CLOSEFIL, the work job, WAITSTEP and OPENFIL. The seed put it in an early wave because it touches no dataset. It cannot be retired before the last batch job that needs exclusive access to the files CICS holds open, so it moves to wave 5. | `scripts/run_posting.sh:13`, `app/jcl/CLOSEFIL.jcl:26` |
| `job:CREADB2` | 1 | 7 | The seed saw no DB2 access because the DB2 steps run IKJEFT01 with control cards (DB2CREAT, DB2LTTYP) that the extractor does not read. The job creates the DB2 database and loads the transaction type tables, so it is a DB2 unit and belongs in the subsystem wave. | `app/app-transaction-type-db2/jcl/CREADB21.jcl:40`, `app/app-transaction-type-db2/jcl/CREADB21.jcl:59`, `app/app-transaction-type-db2/ctl/DB2CREAT.ctl:1` |
| `job:TXT2PDF1` | 4 | 5 | The seed put it in the utility wave. It reads STATEMNT.PS, which CBSTM03A and job:CREASTMT in wave 5 write, and the CA-7 listing shows CREASTMT triggering it. The two halves make one nameable outcome, statement PDFs. Moved earlier it would only ever read stale files, so it moves with its producer. | `app/jcl/TXT2PDF1.JCL:33`, `app/jcl/CREASTMT.JCL:72`, `app/scheduler/CardDemo.ca7:468`, +1 more in `modernization-assessment/waves.json` |

## Not placed

| Unit | Reason | Evidence |
|---|---|---|
| `CBTRN01C` | not reached by any static edge, and 28 reachable computed call(s) could target it, for example at app/cbl/COACTUPC.cbl:956. Nothing in the tree names it: no JCL step, CSD entry, scheduler entry or literal. It stays unknown and is not placed. | `app/cbl/CBTRN01C.cbl:1` |

## Sensitivity of the cut

| Choice | What would change it | Evidence |
|---|---|---|
| Wave 5 is not cut although it has 55 units | If the client can supply a data access service that makes ACCTDATA, TRANSACT and TCATBALF writable from both platforms, wave 5 could be split into the posting cycle, the refresh jobs, and interest with statements. | analysis `data_hubs`, analysis `articulation_points` |
| CLOSEFIL, OPENFIL and WAITSTEP are in wave 5 | If the target keeps a CICS region alive through wave 7, they retire later than wave 5. | `app/jcl/CLOSEFIL.jcl:26`, `scripts/run_posting.sh:13` |
| Sign-on and menu are in wave 3 | Moving them last is the alternative. It avoids a routing shim in front of the menu, and it delays replacing the password check. | `app/cbl/COSGN00C.cbl:223`, `app/cpy/COMEN02Y.cpy:28` |

