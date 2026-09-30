# 03 Waves

Target state: **refactor** (given as a flag). Refactor means the same behavior in restructured code, usually as services. Machine readable copy: `modernization-assessment/waves.json`. Starting point: `03a-waves-draft.json`, the extractor's cut by family. The risk scores it is checked against are in `modernization-assessment/risks.json`.

## The plan

Seven waves, 123 units (17, 15, 8, 24, 24, 12 and 23), plus one unit not placed. The seed's order of families is kept. Twenty-three units moved, each for a reason the skill allows and each logged in the deviation table below.

| Wave | Family | Name | Units | Blast radius | Confidence | Evidence |
|---|---|---|---|---|---|---|
| 1 | batch-utility | Batch environment and file bracket jobs | 17 | low | medium | `app/jcl/DEFGDGB.jcl:24`, `app/jcl/CLOSEFIL.jcl:26` |
| 2 | batch-readonly | Read only master extracts | 15 | low | medium | `app/jcl/READACCT.jcl:32`, `app/cbl/CBACT01C.cbl:40` |
| 3 | online-readonly | Sign on, menu and read only screens | 8 | medium | medium | `app/cpy/COMEN02Y.cpy:28`, `app/cbl/COSGN00C.cbl:223` |
| 4 | batch-data-jobs | Reference data loads and build tooling | 24 | medium | low | `app/jcl/DISCGRP.jcl:25`, `app/jcl/TRANTYPE.jcl:57` |
| 5 | batch-writers | Daily posting cycle, interest, transaction report and statements | 24 | high | medium | `app/cbl/CBTRN02C.cbl:256`, `app/jcl/POSTTRAN.jcl:23` |
| 6 | online-writers | Online maintenance writers | 12 | high | low | `app/cbl/COACTUPC.cbl:3894`, `app/cbl/COBIL00C.cbl:212` |
| 7 | subsystem | IMS, DB2 and MQ subsystem | 23 | high | low | `app/app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl:25`, `app/app-transaction-type-db2/jcl/MNTTRDB2.jcl:30` |

Wave 4 holds 24 units after the moves, which is under the 25 unit limit, so no cut at an articulation point was needed.

## The must-not-break items and where they land

| Item you named | Units | Wave | Evidence |
|---|---|---|---|
| Daily transaction posting | POSTTRAN, CBTRN02C, and the chain INTCALC, TRANBKP, COMBTRAN, TRANIDX around it | 5 | `app/jcl/POSTTRAN.jcl:23`, `scripts/run_full_batch.sh:47-62` |
| Account and card master refresh | ACCTFILE and XREFFILE (5), CARDFILE (6); the online writers COACTUPC and COCRDUPC (6) | 5 and 6 | `app/jcl/ACCTFILE.jcl:25`, `app/jcl/CARDFILE.jcl:36`, `app/cbl/COACTUPC.cbl:3894` |
| Transaction report | TRANREPT job, proc TRANREPT, CBTRN03C, and the online request CORPT00C | 5 | `app/jcl/TRANREPT.jcl:59`, `app/cbl/CORPT00C.cbl:94` |

The second item is my reading of "account and card master refresh": the reload jobs and the online programs that update those two masters. It is a question for the client in `00-summary.md`.

## High-high units, stated plainly

Thirty-five units score high on both axes (see `risks.json`). None is in waves 1 to 3. Wave 4 holds none after the moves. Waves 5, 6 and 7 hold 16, 5 and 14 of them. Wave 5 is as late as the dependencies allow: waves 6 and 7 read what wave 5 writes. So each must be strangled behind a facade with a shadow run, not ported in one cut. What goes behind a facade:

- **Wave 5 posting cycle.** A data access facade over the account, category balance and transaction masters, and a scheduler shim that starts the ported POSTTRAN when the legacy CBPAUP0J ends (`app/scheduler/CardDemo.ca7:43`, `:70`).
- **Wave 6 online writers.** The menu router from wave 3 hands each option to the legacy CICS program until it is ported.
- **Wave 7.** IMS, DB2 and MQ each behind an adapter; the plugin has not read their schemas.

## Wave by wave

### Wave 1. Batch environment and file bracket jobs (batch-utility)

Units: job:CBADMCDJ, job:CLOSEFIL, job:DALYREJS, job:DEFCUST, job:DEFGDGB, job:ESDSRRDS, job:FTPJCLS, job:LISTFILS, job:OPENFIL, job:RACFCMDS, job:REPTFILE, and six scheduler entries for CLOSEFIL and OPENFIL in the daily, monthly and weekly folders. Full list in `waves.json`.

Why it is sound: none of it runs an application program. What it unblocks: the toolchain, the new scheduler and the GDG bases that waves 4 and 5 write into. Beyond that it is a chore, and it says so. CLOSEFIL and OPENFIL cannot be retired here; they stay until wave 6 ends.

Notes: REPTFILE defines the TRANREPT generation group with limit 10 (`app/jcl/REPTFILE.jcl:25-28`) and DEFGDGB defines the same group with limit 5 (`app/jcl/DEFGDGB.jcl:36-40`). Whichever runs first wins. DEFCUST works on cluster names no other job uses (`app/jcl/DEFCUST.jcl:25`, `:35`).

### Wave 2. Read only master extracts (batch-readonly)

Units: CBACT01C, CBACT02C, CBACT03C, CBCUS01C, CBIMPORT, COBSWAIT; jobs READACCT, READCARD, READCUST, READXREF, CBIMPORT, WAITSTEP; three WAITSTEP scheduler entries.

Why it is sound: the programs write nothing that any other entry point uses. What it unblocks: the proof that the target reads the four legacy record layouts, and READACCT's three output copies of the account master as the first oracle files (`app/jcl/READACCT.jcl:35-48`). CBIMPORT cannot open its outputs as written (`app/cbl/CBIMPORT.cbl:63`), so treat it as unproven.

### Wave 3. Sign on, menu and read only screens (online-readonly)

Units: COSGN00C, COMEN01C, COADM01C (one strongly connected component), COTRN00C and COTRN01C (another), COACTVWC, COCRDSLC, CSUTLDTC.

Why it is sound: all eight read and write nothing other entry points use. It is not the first wave because a low-high wave is only safe once the harness is proven. What it unblocks: the router facade that all later online waves plug into, and CSUTLDTC, which CORPT00C (wave 5), COTRN02C and COACTUPC (wave 6) call (`app/cbl/CORPT00C.cbl:392`, `app/cbl/COTRN02C.cbl:393`, `app/cbl/COACTUPC.cbl:4232`). The wave reads masters that later waves write, so it needs a read facade over the legacy VSAM.

### Wave 4. Reference data loads and build tooling (batch-data-jobs)

Units: jobs CUSTFILE, DEFGDGD, DISCGRP, DUSRSECJ, INTRDRJ1, INTRDRJ2, PRTCATBL, REPRTEST, SORTTEST, TRANCATG, TRANFILE, TRANTYPE, TXT2PDF1; the five build jobs CBLDBMS, CICCMP, CIDBCMP, CNJBATMP, IMSMQCMP; the procs BLDCIDB2, BUILDBAT, BUILDBMS, BUILDONL, REPROC; the DISCGRP scheduler entry.

Why it is a weaker wave: every dataset direction comes from DISP, because the control cards are not read. Nine units are compile tooling that the target build replaces (`risks.json`, `do_not_port`). What it unblocks: the rate table that CBACT04C reads (`app/cbl/CBACT04C.cbl:272`) and the type and category tables that CBTRN03C reads (`app/cbl/CBTRN03C.cbl:432`, `:450`). TRANTYPE and TRANCATG reload from files written by the DB2 unload TRANEXTR in wave 7 (`app/app-transaction-type-db2/jcl/TRANEXTR.jcl:73`, `:103`), so the DB2 job has to stay running unchanged.

### Wave 5. Daily posting cycle, interest, transaction report and statements (batch-writers)

Units, 24: CBTRN02C, CBACT04C, CBTRN03C, CBSTM03A, CBSTM03B, CBEXPORT, CORPT00C; jobs POSTTRAN, INTCALC, TRANBKP, COMBTRAN, TRANIDX, TRANREPT, CREASTMT, CBEXPORT, ACCTFILE, TCATBALF, XREFFILE; proc TRANREPT; the scheduler entries for INTCALC, TRANBKP and COMBTRAN; the wrappers run_posting and run_interest_calc.

Why it is one wave: the cycle is one temporal chain with one test boundary, the three masters after it runs. What it unblocks: the nightly cycle on the target, an end to TRANBKP's delete and redefine of the master, and online writes without CLOSEFIL. Rollback needs a snapshot design: the tree backs up the transaction master (`app/jcl/TRANBKP.jcl:23-33`) and the category balance file (`app/jcl/PRTCATBL.jcl:29-35`), and no job backs up the account master (inference). The old jobs must stay runnable in parallel until the wave exits.

### Wave 6. Online maintenance writers (online-writers)

Units: COACTUPC, COCRDUPC, COBIL00C, COTRN02C, COCRDLIC, COUSR00C, COUSR01C, COUSR02C, COUSR03C; job CARDFILE; the wrappers remote_refresh and run_full_batch.

Why it is a wave: these programs are the last writers of the shared masters. What it unblocks: the end of CICS VSAM and of the close and open bracket. Confidence is low because I read only the write path of COACTUPC (`app/cbl/COACTUPC.cbl:3894-3935`) and a fraction of the others.

### Wave 7. IMS, DB2 and MQ subsystem (subsystem)

Units, 23: COPAUA0C, COPAUS0C, COPAUS1C, COPAUS2C, COACCT01, CODATE01, COTRTLIC, COTRTUPC, COBTUPDT, CBPAUP0C, DBUNLDGS, PAUDBLOD, PAUDBUNL; jobs CBPAUP0J, DBPAUTP0, LOADPADB, UNLDGSAM, UNLDPADB, CREADB2, MNTTRDB2, TRANEXTR; two weekly folder entries.

Why last: nothing else depends on it except two jobs that keep running in legacy meanwhile. The plugin read no DBD, PSB, DDL or DCLGEN, so the least is known here.

## Does each wave meet the four tests?

| Wave | Deployable alone | Rolls back alone | Testable boundary | Stakeholder can name it | Evidence |
|---|---|---|---|---|---|
| 1 | Yes, behind a scheduler flag | Rerun the legacy job | Job return codes and GDG bases exist | New scheduler live | `app/jcl/DEFGDGB.jcl:24` |
| 2 | Yes, new jobs alongside old | Stop the new job; it is read only | Output files match READACCT copies | Extracts run on the target | `app/jcl/READACCT.jcl:35` |
| 3 | Yes, router flag per option | Flip the router back to CICS | Screen scrape diff and read facade | Sign on and views on the target | `app/cpy/COMEN02Y.cpy:28` |
| 4 | Yes, per job | Rerun the old load from the same flat file | Loaded file equals flat file | Reference data current | `app/jcl/DISCGRP.jcl:54` |
| 5 | Yes, but needs the shim and shadow run | Restore snapshots of three masters | Three masters after the cycle | Nightly posting on the target | `app/jcl/POSTTRAN.jcl:23` |
| 6 | Yes, per program behind the router | Flip the router; needs record locks agreed | Master diff after a scripted session | Online maintenance on the target | `app/cbl/COACTUPC.cbl:3894` |
| 7 | Only per adapter | Old subsystems must stay | Not yet defined: inference | Authorizations and DB2 screens on the target | `app/app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl:25` |

## Deviations from the seed

Each row is also in `waves.json` under `deviations`. The reason numbers refer to the four allowed reasons in the skill: 1 dependency, 2 wave size, 3 something the extractor could not see, 4 high-high placed early.

| Unit | From | To | Reason | Evidence |
|---|---|---|---|---|
| CORPT00C | 3 | 5 | 3 and 1: builds JCL that runs CBTRN03C, a wave 5 unit and a must-not-break item | `app/cbl/CORPT00C.cbl:94`, `app/cbl/CORPT00C.cbl:517` |
| proc:TRANREPT | not placed | 5 | 3: named only inside JCL text in CORPT00C | `app/cbl/CORPT00C.cbl:94`, `app/proc/TRANREPT.prc:57` |
| job:MNTTRDB2 | 1 | 7 | 3: runs COBTUPDT with DB2 through TSO | `app/app-transaction-type-db2/jcl/MNTTRDB2.jcl:30` |
| sch:WEEKLY-TransactionTypesDBRefresh/MNTTRDB2 | 1 | 7 | Follows its job | `app/scheduler/CardDemo.controlm:27` |
| COBTUPDT | not placed | 7 | 3: only run by MNTTRDB2 | `app/app-transaction-type-db2/jcl/MNTTRDB2.jcl:30` |
| job:TRANEXTR | 1 | 7 | 3: DB2 unload; &HLQ hid its datasets | `app/app-transaction-type-db2/jcl/TRANEXTR.jcl:88` |
| sch:WEEKLY-TransactionTypesDBRefresh/TRANEXTR | 1 | 7 | Follows its job | `app/scheduler/CardDemo.controlm:58` |
| job:CREADB2 | 1 | 7 | 3: DB2 DDL through DSNTIAD | `app/app-transaction-type-db2/jcl/CREADB21.jcl:52` |
| CBPAUP0C | not placed | 7 | 3: named in a BMP PARM | `app/app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl:25` |
| DBUNLDGS | not placed | 7 | 3: named in a DLI PARM | `app/app-authorization-ims-db2-mq/jcl/UNLDGSAM.JCL:27` |
| PAUDBLOD | not placed | 7 | 3: named in a BMP PARM | `app/app-authorization-ims-db2-mq/jcl/LOADPADB.JCL:27` |
| PAUDBUNL | not placed | 7 | 3: named in a DLI PARM | `app/app-authorization-ims-db2-mq/jcl/UNLDPADB.JCL:39` |
| job:TRANBKP | 4 | 5 | 1: one chain with POSTTRAN, must-not-break | `scripts/run_full_batch.sh:47`, `scripts/run_full_batch.sh:55` |
| job:COMBTRAN | 4 | 5 | 1: takes INTCALC output, ends the cycle | `scripts/run_full_batch.sh:58`, `app/jcl/COMBTRAN.jcl:24` |
| sch:DAILY-TransactionBackup/TRANBKP | 4 | 5 | Follows its job | `app/scheduler/CardDemo.controlm:8` |
| sch:MONTHLY-InterestCalculation/COMBTRAN | 4 | 5 | Follows its job | `app/scheduler/CardDemo.controlm:75` |
| job:TRANIDX | 1 | 5 | 1 and 3: rebuilds an index TRANBKP deletes; control cards not read | `scripts/run_posting.sh:30`, `app/jcl/TRANBKP.jcl:43` |
| job:ACCTFILE | 4 | 5 | 4: high-high; first writers CBTRN02C and CBACT04C are in wave 5 | `app/cbl/CBTRN02C.cbl:311`, `app/cbl/CBACT04C.cbl:291` |
| job:TCATBALF | 4 | 5 | 4: high-high; CBTRN02C is its first writer | `app/cbl/CBTRN02C.cbl:329` |
| job:XREFFILE | 4 | 5 | 4: high-high; no writer, first dependents in wave 5 | `app/cbl/CBTRN02C.cbl:275`, `app/cbl/CBACT04C.cbl:254` |
| job:CARDFILE | 4 | 6 | 4: high-high; first writer COCRDUPC is in wave 6 | `app/cbl/COCRDUPC.cbl:1478` |
| sch:scripts/remote_refresh.sh | 4 | 6 | Wrapper follows the last wave among its jobs | `scripts/remote_refresh.sh:20` |
| sch:scripts/run_full_batch.sh | 5 | 6 | Wrapper follows the last wave among its jobs | `scripts/run_full_batch.sh:20` |

## Not placed

| Unit | Reason | Evidence |
|---|---|---|
| CBTRN01C | No JCL step names it and it writes nothing. Stays in the unknown bucket. | `app/cbl/CBTRN01C.cbl:254` |

## Placement rule that decides a weak spot

The seed puts TRANREPT in the writers family because SORTTEST, a sample job, also writes TRANSACT.DALY (`samples/jcl/SORTTEST.jcl:31`). If the client confirms the samples never run in production, TRANREPT is a read only report and its family would be wave 2. I left it in wave 5 because it is a must-not-break item and it shares a proc with the online request.
