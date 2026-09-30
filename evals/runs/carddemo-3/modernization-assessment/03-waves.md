# 03 Waves

Target state: refactor (same behavior, restructured code). The plan starts from the extractor's seed (`modernization-assessment/03a-wave-seed.md`) and changes it in 13 places, each for a reason I can cite. Every change is in `modernization-assessment/waves.json` under `deviations` and repeated below. Scores come from `modernization-assessment/risks.json`.

## The plan at a glance

| Wave | Name | Units | Blast radius | Confidence | Evidence |
|---|---|---|---|---|---|
| 1 | Setup utilities and CICS file fences | 8 | medium | medium | `app/jcl/CLOSEFIL.jcl:26` |
| 2 | Read only batch and the import job | 12 | low | medium | `app/jcl/READACCT.jcl:1` |
| 3 | Sign on, menus and read only screens | 7 | medium | low | `app/csd/CARDDEMO.CSD:317` |
| 4 | Build and demo jobs | 11 | low | medium | `app/jcl/DEFGDGD.jcl:39` |
| 5 | Batch that writes the shared masters | 51 | high | medium | `app/jcl/POSTTRAN.jcl:23` |
| 6 | Online writers | 9 | high | low | `app/cbl/COACTUPC.cbl:573` |
| 7 | IMS, DB2 and MQ subsystems | 25 | high | low | `app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:956` |

One unit is not placed: CBTRN01C, in the unknown dead code bucket (`modernization-assessment/05-dead-code.md`). Waves 3, 6 and 7 hold programs with computed calls, so none of them can be `high` confidence, and none is.

## Do the waves pass the four tests

A wave is valid only if it can be deployed independently, rolled back independently, has a testable boundary, and delivers something a stakeholder can name.

| Wave | Deploy alone | Roll back alone | Testable boundary | Nameable deliverable | Evidence |
|---|---|---|---|---|---|
| 1 | yes | yes | weak: no logic | no. It is a chore. | `app/jcl/CBADMCDJ.jcl:27` |
| 2 | yes | yes, discard the output | yes, file diff | yes: the record layouts and first golden masters | `app/cbl/CBACT01C.cbl:231` |
| 3 | only behind a router facade | yes, route back at the facade | yes, screen and reply diff | yes: browse on the new stack | `app/cbl/COMEN01C.cbl:156` |
| 4 | yes | yes | weak | no. It is a chore. | `app/jcl/TXT2PDF1.JCL:31` |
| 5 | only with a data access facade over the masters | yes, if the legacy job stays runnable on a frozen copy | yes, replay diff | yes: the nightly batch window | `app/jcl/POSTTRAN.jcl:23` |
| 6 | only with the same facade | yes | yes | yes: online maintenance | `app/cbl/COBIL00C.cbl:212` |
| 7 | not until IMS and MQ targets are chosen | unknown | not assessable | yes | inference |

Waves 1 and 4 fail the fourth test and I kept them anyway, because the plan should not invent or merge waves for tidiness. Wave 1 and wave 4 are chores, and the recommendation is to retire most of them and run them alongside wave 2, not before it. Nothing in them proves the port toolchain, so wave 2 is the real first wave.

## Where the plan puts the risk

The plan puts 15 high-high units in wave 5 of 7, 4 in wave 6 and 7 in wave 7. None is in the first half. The three must-not-break items are in wave 5, not last, because the online writers of wave 6 and everything in wave 3 read the datasets they write. They cannot move last. What has to sit behind a facade first is the set of shared VSAM masters (account, card, cross reference, customer, transaction, category balance): a data access service that both the legacy CICS programs and the new batch code call, so that the writer can move without moving every reader. Without it, wave 5 has no safe way to hand the files over.

## Where each must-not-break item lands

| Must not break | Client's words mapped to units | Wave | Confidence | Evidence |
|---|---|---|---|---|
| Daily transaction posting | job:POSTTRAN, CBTRN02C, and the chain job:TRANBKP, job:COMBTRAN, job:TRANIDX around it | 5 | high | `app/jcl/POSTTRAN.jcl:23`, `app/cbl/CBTRN02C.cbl:256` |
| The account and card master refresh | job:ACCTFILE and job:CARDFILE, listed as "Refresh Account Master file" and "Refresh Card Master", with companions job:CUSTFILE and job:XREFFILE. My mapping from the captions, inference. | 5 | medium | `scripts/remote_refresh.sh:16`, `scripts/remote_refresh.sh:19` |
| The transaction report | job:TRANREPT, proc:TRANREPT, CBTRN03C, and the online request CORPT00C | 5 | high | `app/jcl/TRANREPT.jcl:59`, `app/cbl/CORPT00C.cbl:94` |

The "master refresh" mapping is the weakest. The tree has no program or job called refresh. It is named only in the wrapper's comments. It could also mean the READACCT and READCARD listing jobs, or the online update programs COACTUPC and COCRDUPC. That is in Open Questions.

## Wave by wave

### Wave 1. Setup utilities and CICS file fences

Units: job:CBADMCDJ, job:CLOSEFIL, job:DEFCUST, job:ESDSRRDS, job:FTPJCLS, job:LISTFILS, job:OPENFIL, job:RACFCMDS.

- Rationale. These jobs run no application program. CLOSEFIL and OPENFIL send CEMT commands to CICS region CICSAWSA (`app/jcl/CLOSEFIL.jcl:26`) and work unchanged on the mainframe, so they need no port until wave 5. Most of the rest is retirement: `do_not_port` lists FTPJCLS, DEFCUST, ESDSRRDS, LISTFILS, RACFCMDS and CBADMCDJ.
- Port order. Nothing has to be ported. First find and remove the clear text login in `app/jcl/FTPJCL.JCL:33`, and rotate it.
- Test harness. None needed. A pipeline dry run is enough.
- Rollback. The JCL is unchanged. Nothing moves.

### Wave 2. Read only batch and the import job

Units: CBACT01C, CBACT02C, CBACT03C, CBCUS01C, CBIMPORT, COBSWAIT, job:CBIMPORT, job:READACCT, job:READCARD, job:READCUST, job:READXREF, job:WAITSTEP.

- Port order. CBACT02C, CBACT03C, CBCUS01C (plain read and print), then CBACT01C (replace assembler COBDATFT, `app/cbl/CBACT01C.cbl:231`), then COBSWAIT and WAITSTEP (replace the assembler wait with a sleep, and see the note on the 36 second delay in `modernization-assessment/02-coupling.md`), then CBIMPORT once its job has the missing CARDOUT DD (`app/cbl/CBIMPORT.cbl:63`).
- Test harness. Golden master from the sample inputs in `app/data/EBCDIC` and `app/data/ASCII`, run through the legacy programs on the client's emulator (`samples/m2`) to capture SYSOUT. Decimal type with zero tolerance for money fields, following the copybooks `app/cpy/CVACT01Y.cpy:7`.
- Rollback. Run the legacy job. Output is discarded.
- Note. CBCUS01C prints every customer record, including the SSN, to SYSOUT (`app/cbl/CBCUS01C.cbl:78`). Do not copy that into a new logging path.

### Wave 3. Sign on, menus and read only screens

Units: COACTVWC, COADM01C, COCRDSLC, COMEN01C, COSGN00C, COTRN00C, COTRN01C.

- Port order. COTRN00C and COTRN01C as a pair, COACTVWC, COCRDSLC, and last the router component COSGN00C, COMEN01C, COADM01C as one unit behind a facade that can still dispatch by program name to legacy transactions (`app/cpy/COMEN02Y.cpy:28`).
- Test harness. Screen level replay: captured 3270 input and expected map output, or characterization tests marked provisional. The oracle is the weakest of any wave.
- Rollback. Point the router back at the CICS transaction. Sign on is a data change too: COSGN00C compares a clear text password field (`app/cbl/COSGN00C.cbl:223`), and `risks.json` recommends replacing it with an identity provider, not porting it.
- Dependency. These programs read masters that legacy batch still writes, so a read path over the legacy VSAM files, or a replicated copy with a known lag, is required until wave 5.

### Wave 4. Build and demo jobs

Units: job:CBLDBMS, job:CICCMP, job:CNJBATMP, job:DEFGDGD, job:IMSMQCMP, job:INTRDRJ1, job:INTRDRJ2, job:TXT2PDF1, proc:BUILDBAT, proc:BUILDBMS, proc:BUILDONL.

- Port order. Retire the seven build jobs and procs (replace with the new pipeline). Move DEFGDGD (generation bases for reference data backups) and TXT2PDF1 into the wave 5 statement work: TXT2PDF1 needs the REXX exec library at `app/jcl/TXT2PDF1.JCL:31`, which is not in the tree.
- Test harness. None for the build jobs. TXT2PDF1 is diffed with the statement output in wave 5.
- Rollback. Keep the mainframe build until the new pipeline builds wave 7's sources.

### Wave 5. Batch that writes the shared masters

Units: 51, listed in `modernization-assessment/waves.json`. The internal order below is my recommendation, and each step is a sub-deliverable of the one wave. It is not a new wave.

| Step | Units | Why here | Confidence | Evidence |
|---|---|---|---|---|
| 5.0 Data facade and generation bases | A data access service over the VSAM masters. DEFGDGB, DALYREJS, REPTFILE (fix the two limits for TRANREPT first). | Everything after it writes through the facade. The two definitions of TRANREPT disagree on retention. | medium | `app/jcl/DEFGDGB.jcl:38`, `app/jcl/REPTFILE.jcl:27` |
| 5.1 Reference data reloads | TRANTYPE, TRANCATG, DISCGRP, DUSRSECJ | Read only by later steps, so they prove the reload pattern with the lowest blast. DISCGRP feeds the interest rate. | medium | `app/jcl/DISCGRP.jcl:36` |
| 5.2 Master reloads (must-not-break refresh) | XREFFILE, CUSTFILE, ACCTFILE, CARDFILE, TCATBALF, TRANFILE | Order follows the wrapper. Verify the CICS fences per job first. ACCTFILE and XREFFILE have none of their own. | medium | `scripts/remote_refresh.sh:16`, `app/jcl/ACCTFILE.jcl:25` |
| 5.3 Daily posting (must-not-break) | TRANBKP, POSTTRAN with CBTRN02C, COMBTRAN, TRANIDX | Parallel run against production input for at least one month end. Port CBTRN02C alone, keep TRANBKP and COMBTRAN on legacy until posting matches. | medium | `scripts/run_posting.sh:23`, `app/cbl/CBTRN02C.cbl:256` |
| 5.4 Interest | INTCALC with CBACT04C | Needs posting stable first, since it reads the category balances that CBTRN02C updates. | medium | `app/cbl/CBACT04C.cbl:464`, `app/jcl/INTCALC.jcl:22` |
| 5.5 Report (must-not-break) | CSUTLDTC, CBTRN03C, proc TRANREPT, job TRANREPT, CORPT00C, PRTCATBL | The online request and the batch report move together. The date window hard coded in the batch job has to become a parameter. | medium | `app/jcl/TRANREPT.jcl:43`, `app/cbl/CORPT00C.cbl:94` |
| 5.6 Statements and export | CREASTMT, CBSTM03A, CBSTM03B, CBEXPORT, job CBEXPORT | Rewrite CBSTM03A from its behavior (ALTER and control block code), do not transliterate it. | low | `app/cbl/CBSTM03A.CBL:300` |
| 5.7 Scheduler cut over | The nine Control-M entries and four wrapper scripts, one folder at a time | Each folder cuts over as a unit. Bridge the CA-7 trigger from CBPAUP0J to POSTTRAN and the Control-M gate from MNTTRDB2 until wave 7. | low | `app/scheduler/CardDemo.ca7:70`, `app/scheduler/CardDemo.controlm:34` |

- Test harness. See `modernization-assessment/06-test-strategy.md`. Parallel run for 5.3 and 5.4, golden masters from GDG generations for 5.5, byte compare of the reload targets for 5.1 and 5.2.
- Rollback. Keep the legacy job runnable on a frozen copy of each master until parallel runs are clean for a full cycle. Restore from the backup generation: the generation groups keep five generations (`app/jcl/DEFGDGB.jcl:26`), so a rollback point older than five runs does not exist. Say so to the client.
- Do not port: job:REPRTEST and job:SORTTEST are samples that the seed placed here.

### Wave 6. Online writers

Units: COACTUPC, COBIL00C, COCRDLIC, COCRDUPC, COTRN02C, COUSR00C, COUSR01C, COUSR02C, COUSR03C.

- Port order. COUSR00C to COUSR03C first (small, but sign on reads their file), then COTRN02C, COCRDLIC with COCRDUPC, COBIL00C (new transaction id scheme, not read last key plus one: `app/cbl/COBIL00C.cbl:212`), and last COACTUPC (about 4,200 lines, 43 REDEFINES, `app/cbl/COACTUPC.cbl:3888`).
- Test harness. Screen replay plus a database diff of the masters after each scripted scenario. Add concurrency cases for the transaction id.
- Rollback. Router flag back to the CICS transaction, which is only safe while the legacy masters still get every write. That is the reason the facade from wave 5 has to stay until this wave ends.

### Wave 7. IMS, DB2 and MQ subsystems

Units: 25, listed in `modernization-assessment/waves.json`.

- Port order. Decide the target for IMS, DB2 and MQ first. Then DB2 (COTRTLIC, COTRTUPC, COBTUPDT, CREADB2, MNTTRDB2, TRANEXTR), then the IMS unload and load utilities, then the authorization decision COPAUA0C with its viewers (COPAUS0C and COPAUS1C move together), then MQ services COACCT01 and CODATE01.
- Test harness. Not assessable from this tree: DBD, PSB, DDL and MQ definitions are not read. Ask for them.
- Rollback. Unknown.

## Changes to the extractor's seed

| Unit | From | To | Reason | Evidence |
|---|---|---|---|---|
| CORPT00C | 3 | 5 | Must-not-break transaction report. The online request builds JCL for proc TRANREPT and writes it to an internal reader queue. Porting it early builds a bridge to legacy JCL that wave 5 throws away. | `app/cbl/CORPT00C.cbl:94`, `app/cbl/CORPT00C.cbl:517`, `app/csd/CARDDEMO.CSD:499` |
| proc:TRANREPT | not placed | 5 | Named only in JCL text inside COBOL, so the seed left it out. It runs CBTRN03C for the report. | `app/cbl/CORPT00C.cbl:94`, `app/proc/TRANREPT.prc:1` |
| CSUTLDTC | 3 | 5 | A callee moves with the earliest family of its callers. After CORPT00C moved, the callers are in waves 5 and 6. Also high-high in `risks.json`. | `app/cbl/CORPT00C.cbl:392`, `app/cbl/COTRN02C.cbl:393`, `app/cbl/COACTUPC.cbl:4232` |
| job:CREADB2 | 1 | 7 | The steps are DB2 utilities driven by control members that the extractor does not read, so the seed saw no DB2 use. | `app/app-transaction-type-db2/jcl/CREADB21.jcl:52`, `app/app-transaction-type-db2/jcl/CREADB21.jcl:65` |
| sch:DAILY-TransactionBackup/CLOSEFIL | 1 | 5 | The folder is one high confidence chain ending in wave 5 job TRANBKP. A chain split across waves cannot be cut over as a unit. | `app/scheduler/CardDemo.controlm:5`, `app/scheduler/CardDemo.controlm:9` |
| sch:DAILY-TransactionBackup/WAITSTEP | 2 | 5 | Same chain. | `app/scheduler/CardDemo.controlm:11`, `app/scheduler/CardDemo.controlm:15` |
| sch:DAILY-TransactionBackup/OPENFIL | 1 | 5 | Same chain. | `app/scheduler/CardDemo.controlm:17`, `app/scheduler/CardDemo.controlm:21` |
| sch:MONTHLY-InterestCalculation/CLOSEFIL | 1 | 5 | Chain ending in wave 5 jobs INTCALC and COMBTRAN. | `app/scheduler/CardDemo.controlm:66`, `app/scheduler/CardDemo.controlm:70` |
| sch:MONTHLY-InterestCalculation/WAITSTEP | 2 | 5 | Same chain. | `app/scheduler/CardDemo.controlm:78`, `app/scheduler/CardDemo.controlm:82` |
| sch:MONTHLY-InterestCalculation/OPENFIL | 1 | 5 | Same chain. | `app/scheduler/CardDemo.controlm:84`, `app/scheduler/CardDemo.controlm:88` |
| sch:WEEKLY-DisclosureGroupsRefresh/CLOSEFIL | 1 | 5 | Chain ending in wave 5 job DISCGRP. It also waits for a wave 7 condition (MNTTRDB2), which needs a bridge, and I left that as a dependency, not a move. | `app/scheduler/CardDemo.controlm:35`, `app/scheduler/CardDemo.controlm:34` |
| sch:WEEKLY-DisclosureGroupsRefresh/WAITSTEP | 2 | 5 | Same chain. | `app/scheduler/CardDemo.controlm:41`, `app/scheduler/CardDemo.controlm:45` |
| sch:WEEKLY-DisclosureGroupsRefresh/OPENFIL | 1 | 5 | Same chain. | `app/scheduler/CardDemo.controlm:47`, `app/scheduler/CardDemo.controlm:51` |

The JCL jobs CLOSEFIL, OPENFIL and WAITSTEP stay in waves 1 and 2, because a job definition can be ported ahead of the schedule that uses it. I did not move any unit because of its name, and I did not merge or cut waves. Wave 5 has 51 units and one argument describes it, so it needs no cut (see the rule in the skill), but the order inside it matters more than the wave boundary.

## What could not be sequenced

| Unit | Reason | Evidence |
|---|---|---|
| CBTRN01C | Not reached by any static edge. Named by no JCL, CSD or program. Bounded computed calls do not name it, but that is inference, so it stays unknown. Ask whether someone runs it by hand. | `app/cbl/CBTRN01C.cbl:1` |
