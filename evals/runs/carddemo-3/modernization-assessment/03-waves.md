# 03 Waves

Target state: refactor, meaning the same behavior in restructured code, in services, in the same or a new language. Seven waves. The machine-readable plan is `modernization-assessment/waves.json`. It starts from the extractor's seed (`03a-wave-seed.md`) and changes it only for reasons I can cite. There are 18 recorded deviations, listed below. Every unit in the plan is a node in `graph.json`.

## The plan

| Wave | Name | Units | Blast radius | Confidence | Evidence |
|---|---|---|---|---|---|
| 1 | Batch brackets, GDG bases and utility definers | 17 | medium | medium | `app/jcl/CLOSEFIL.jcl:26`, `app/jcl/DEFGDGB.jcl:24`, `app/jcl/DALYREJS.jcl:24` |
| 2 | Read-only extract and print batch | 15 | low | medium | `app/jcl/READACCT.jcl:32`, `app/cbl/CBACT01C.cbl:231` |
| 3 | Sign-on, menu and read-only online screens | 7 | medium | medium | `app/cbl/COSGN00C.cbl:223`, `app/cpy/COMEN02Y.cpy:21` |
| 4 | Master data loaders and reference data jobs | 29 | high | medium | `scripts/remote_refresh.sh:16`, `app/jcl/ACCTFILE.jcl:40`, `app/jcl/CARDFILE.jcl:85` |
| 5 | Daily posting, interest, transaction report and statements | 23 | high | medium | `app/jcl/POSTTRAN.jcl:23`, `app/jcl/TRANREPT.jcl:59`, `app/cbl/CBTRN02C.cbl:256` |
| 6 | Online writers: accounts, cards, bill payment, transactions, users | 9 | high | medium | `app/cbl/COACTUPC.cbl:4066`, `app/cbl/COBIL00C.cbl:212` |
| 7 | IMS, DB2 and MQ subsystem | 23 | high | low | `app/app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl:25`, `app/app-transaction-type-db2/jcl/MNTTRDB2.jcl:30` |

One unit is not placed: CBTRN01C. Nothing in the tree runs it. See `05-dead-code.md`.

The order follows the seed's families: batch with no application program, read-only batch, read-only online, batch data jobs, batch writers, online writers, subsystems. The seed is a sound default for a system where the shared data is the hard part, because it moves readers before writers and leaves the shared stores for last. The extractor cannot see inside in-stream cards, JCL text in COBOL and program names in a PARM, so it mis-filed some units. My own risk scoring moved a few more. Those are the 18 deviations.

## Why each wave passes the four tests

A wave is valid only if it deploys independently, rolls back independently, has a testable boundary and delivers something a stakeholder can name.

| Wave | Deploys behind a flag or facade | Rolls back by | Testable boundary | What a stakeholder can name | Evidence |
|---|---|---|---|---|---|
| 1 | The scheduler runs the ported bracket jobs against the legacy CICS region. | Point the scheduler back at the old JCL. | Return codes and GDG bases created. | "The batch scheduler runs on the new platform." | `app/jcl/CLOSEFIL.jcl:26` |
| 2 | Each program runs beside the legacy one on the same masters. | Stop running the ported job. | Diff of the printed files (the READ jobs write files nobody else reads). | "Master data can be read and printed from the new platform." | `app/jcl/READACCT.jcl:32` |
| 3 | A router in front of the CICS regions sends sign-on, menu and the list and view screens to the new UI and everything else to CICS. | Route back. | Screen contents for a fixed set of user actions against the seed masters. | "Users sign on and browse on the new platform." | `app/cpy/COMEN02Y.cpy:21` |
| 4 | The loaders run against the shared store through the data facade. | Reload from the PS files with the legacy loader. | Record counts and a read-back through the wave 2 print jobs. | "Master data can be refreshed from the new platform." | `scripts/remote_refresh.sh:16` |
| 5 | The posting, interest and report jobs run through the data facade while the online writers stay on CICS. | Restore a pre-run snapshot of ACCTDATA, TCATBALF and the transaction master, and rerun the legacy job. The legacy cycle snapshots only the transaction master (TRANBKP) and reloads the other two from PS files, so the port must add the snapshot. | Daily file in. Masters, DALYREJS and TRANREPT out. | "Daily posting and the transaction report run on the new platform." | `app/jcl/POSTTRAN.jcl:23`, `scripts/run_posting.sh:17`, `scripts/run_posting.sh:23` |
| 6 | The online writers move behind the router. | Route back and restore the masters from backup. | Screen and master contents after a scripted sequence. | "CICS is retired for this application." | `app/cbl/COACTUPC.cbl:4066` |
| 7 | Each subsystem moves with its data store. | Per subsystem. Not assessed here. | Not assessed here. | "The mainframe is retired." | inference: the DB2, IMS and MQ definitions are not parsed |

Wave 5 is only valid if the VSAM masters are served through one data facade to both the new batch and the legacy online programs. ACCTDATA has four writers and TRANSACT has three across waves 5 and 6 (`02-coupling.md`). Without the facade, wave 5 splits the writers of one file across two platforms and fails the "deploys independently" test. This is what I would put behind a facade so that a high-high unit can move: a record-level access service that owns the ACCTDATA, TRANSACT, TCATBALF, CARDXREF and CUSTDATA files, honors the CLOSEFIL and OPENFIL window, and keeps the 300 and 350 byte layouts.

## What moved and why

These are the changes to the seed. Reason 3 in the skill is "something the extractor could not see changes what a unit is". Reason 1 is a must-not-break item or a dependency. Each row has cited evidence.

| Unit | From | To | Reason | Evidence |
|---|---|---|---|---|
| CORPT00C | 3 | 5 | Embedded JCL. It builds the job that runs the report and writes it to the JOBS queue. It is the online front of the must-not-break report, so it moves with the report. The menu in wave 3 must route to the legacy program until wave 5. | `app/cbl/CORPT00C.cbl:94`, `app/cbl/CORPT00C.cbl:517` |
| proc:TRANREPT | not placed | 5 | The proc that program's embedded JCL runs. | `app/proc/TRANREPT.prc:1` |
| CSUTLDTC | 3 | 5 | The seed moves a shared unit with its earliest user. With CORPT00C in wave 5, nothing in wave 3 calls it. | `app/cbl/CORPT00C.cbl:392`, `app/cbl/COTRN02C.cbl:393` |
| job:TRANIDX | 1 | 5 | IDCAMS cards are not read. It builds the alternate index over the shared transaction master, after POSTTRAN, every cycle. | `app/jcl/TRANIDX.jcl:53`, `scripts/run_posting.sh:30` |
| job:TRANBKP, sch:DAILY-TransactionBackup/TRANBKP | 4 | 5 | It empties the master that CBTRN02C opens OUTPUT. They share one lifecycle. Also high-high in `risks.json`, so it goes to the last wave that keeps the lifecycle inside one boundary. | `app/jcl/TRANBKP.jcl:40`, `app/cbl/CBTRN02C.cbl:256` |
| job:COMBTRAN, sch:MONTHLY-InterestCalculation/COMBTRAN | 4 | 5 | It rebuilds the master from the TRANBKP generation and the INTCALC output. High-high in `risks.json`. | `app/jcl/COMBTRAN.jcl:22`, `app/jcl/INTCALC.jcl:41` |
| job:MNTTRDB2, sch:WEEKLY-TransactionTypesDBRefresh/MNTTRDB2, COBTUPDT | 1, 1, not placed | 7 | An in-stream `RUN PROGRAM(COBTUPDT)` card. It is a DB2 batch program. | `app/app-transaction-type-db2/jcl/MNTTRDB2.jcl:30` |
| job:TRANEXTR, sch:WEEKLY-TransactionTypesDBRefresh/TRANEXTR | 1 | 7 | In-stream DSNTIAUL SQL against the transaction type tables. | `app/app-transaction-type-db2/jcl/TRANEXTR.jcl:65` |
| job:CREADB2 | 1 | 7 | DB2 create and load steps. | `app/app-transaction-type-db2/jcl/CREADB21.jcl:52` |
| CBPAUP0C, DBUNLDGS, PAUDBLOD, PAUDBUNL | not placed | 7 | Named in the IMS driver PARM of jobs in wave 7. | `app/app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl:25`, `app/app-authorization-ims-db2-mq/jcl/UNLDGSAM.JCL:27`, `app/app-authorization-ims-db2-mq/jcl/LOADPADB.JCL:27`, `app/app-authorization-ims-db2-mq/jcl/UNLDPADB.JCL:39` |

## What I checked and left alone

| Question | Decision | Evidence |
|---|---|---|
| Wave 4 holds 29 units, above the 25 unit line. Does an argument need it cut? | No. Eleven of the 29 are mainframe build and test tooling (five sample compile jobs, four build procs, REPRTEST, SORTTEST) and are retired, not ported. That leaves 18 to move. Two more (INTRDRJ1 and INTRDRJ2) are provisional retirements. No cut and no articulation point is needed. | `samples/jcl/BMSCMP.jcl:38`, analysis: `do_not_port` in `risks.json` |
| Should the wave 4 loaders go later, since a loader is not needed by wave 2 or 3 readers? | No. The loaders are how the seed data gets reloaded before every wave 5 and wave 6 test run, and the client named the refresh as must-not-break. | `scripts/remote_refresh.sh:16`, `scripts/remote_refresh.sh:20` |
| CARDFILE is high-high and sits at wave 4. Rule: move it to the last wave that breaks no dependency. | It stays. ACCTFILE and CARDFILE are the two halves of one must-not-break item, and splitting that item across waves 4 and 5 is worse than one high-high unit at the middle of the plan. It is a loader with a bounded blast radius (card master only) and a read-back check in wave 2. Dependency and the must-not-break item win over the quadrant. | `scripts/remote_refresh.sh:16`, `scripts/remote_refresh.sh:20` |
| XREFFILE and TRANFILE were first scored high-high. | Rescored to 2 for port difficulty. They are the same delete, define and REPRO pattern as ACCTFILE, plus an alternate index. The offsets in the alternate index are still a contract, and the test strategy covers them. | `app/jcl/TRANFILE.jcl:82`, `app/jcl/CARDFILE.jcl:85` |
| Any high-high unit in the first half (waves 1 to 3)? | None. Waves 1 to 3 hold only low-low, low-high and high-low units. | analysis: `quadrant` in `risks.json` |
| Is any strongly connected component split? | No. The validator checks it. | analysis: `sccs` in `graph.json` |
| Wave 7 is the last wave and holds most of the high-high units. Is that a problem? | It is the plan. COPAUA0C (real-time card authorization) scores 5 and 5 and should be strangled behind a facade, not ported. The wave is the least certain because none of DB2, IMS or MQ is parsed here. | `app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:400` |

## Units retired instead of ported

These are in `do_not_port` in `risks.json`. A team that ports them pays for them twice. Five are the mainframe compile jobs and four are the build procs they use, all under `samples/`. REPRTEST, SORTTEST and LISTFILS are test and listing jobs. RACFCMDS holds RACF definitions that should be translated into the target identity service, not ported as code. UNUSED1Y is a copybook nothing includes. DEFCUST, INTRDRJ1 and INTRDRJ2 are provisional: ask the client first.

## What the plan does not settle

Three items outside the plan that will change it.

| Item | Why it can change the plan | Evidence |
|---|---|---|
| The CA-7 listing says CBPAUP0J triggers POSTTRAN. If that is the live schedule, wave 5 depends on a wave 7 job. | The scheduler must keep running across platforms, or the trigger is re-cut. | `app/scheduler/CardDemo.ca7:43`, `app/scheduler/CardDemo.ca7:70` |
| Telemetry is none. Any unit I placed as live because a job names it may not run. | A unit that never runs drops out of its wave. | inference |
| DB2, IMS and MQ definitions are not parsed. | Wave 7 grows or splits once someone reads them. | inference |
