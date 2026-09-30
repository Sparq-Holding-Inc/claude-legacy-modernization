# 03 Waves

Target state: refactor. `waves.json` holds the plan. `03a-wave-seed.md` is the extractor's first cut from facts alone. I kept its seven waves and its order. I moved two units and recorded both as deviations. Every wave says what it unblocks. Two waves are chores, and I say so.

## The plan

| Wave | Name | Family | Units | Blast radius | Confidence | What it unblocks | Evidence |
|---|---|---|---|---|---|---|---|
| 1 | Environment and utility jobs | batch-utility | 6 | low | medium | Nothing directly. It proves the target pipeline. A chore. | `app/jcl/FTPJCL.JCL:33`, `samples/jcl/RACFCMDS.jcl:1` |
| 2 | Read-only master listings and the import job | batch-readonly | 10 | low | medium | The shared record layouts and the first equivalence harness. | `app/jcl/READACCT.jcl:1`, `app/cbl/CBIMPORT.cbl:233` |
| 3 | Read-only online screens and the menu spine | online-readonly | 7 | medium | medium | The routing facade that wave 6 also needs. | `app/cpy/COMEN02Y.cpy:28`, `app/cbl/COSGN00C.cbl:223` |
| 4 | Build and generation group plumbing | batch-data-jobs | 10 | low | medium | The generation retention decision that wave 5 needs. A chore. | `app/jcl/DEFGDGD.jcl:39`, `app/jcl/DEFGDGB.jcl:24` |
| 5 | Nightly batch core: posting, master refresh, interest, backup and reports | batch-writers | 56 | high | medium | Ends the CICS and batch file bracket. Wave 6 needs it. | `app/jcl/POSTTRAN.jcl:23`, `app/jcl/ACCTFILE.jcl:25`, `app/jcl/TRANREPT.jcl:59` |
| 6 | Online writers to the account, card, transaction and user masters | online-writers | 9 | high | low | The masters belong to the new platform. | `app/cbl/COACTUPC.cbl:4100`, `app/cbl/COBIL00C.cbl:212` |
| 7 | Authorization, transaction type and MQ subsystems | subsystem | 25 | high | low | Retires IMS, DB2 and MQ. Owns the reference data feed. | `app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:874`, `app/app-transaction-type-db2/jcl/CREADB21.jcl:19` |

Every wave passes the four tests, with the caveats below. Each can deploy behind a flag or a facade. Each can be rolled back by switching its jobs or its routes back. Each has a testable edge at a dataset, a report or a screen. Waves 1 and 4 fail the last test: no stakeholder can name what they deliver. They are cheap and they are chores.

## Where the risky units land

Counts come from `risks.json` and the wave each unit sits in (`modernization-assessment/risks.json:1`).

| Wave | high-high | high-low | low-high | low-low |
|---|---|---|---|---|
| 1 | 0 | 0 | 0 | 6 |
| 2 | 0 | 1 | 0 | 9 |
| 3 | 0 | 3 | 3 | 1 |
| 4 | 0 | 0 | 0 | 7 |
| 5 | 9 | 0 | 19 | 9 |
| 6 | 4 | 1 | 3 | 1 |
| 7 | 13 | 4 | 2 | 3 |

No high-high unit sits in waves 1 to 4, the first half of the plan. The nine in wave 5 are CBACT04C, CBTRN02C, CBTRN03C, CBSTM03A, CORPT00C, CSUTLDTC, and the jobs CREASTMT, TRANBKP and TRANREPT. Three of those are must-not-break items: CBTRN02C, CBTRN03C and job:TRANREPT. A must-not-break item cannot go last, and wave 5 is where the dependencies put them. Plan them as strangled: run the new version beside the old one on the same inputs and compare, and switch the wrapper only after a clean run. Do not port them in one change.

## Wave 1. Environment and utility jobs

Units: job:CBADMCDJ, job:DEFCUST, job:ESDSRRDS, job:FTPJCLS, job:LISTFILS, job:RACFCMDS.

The seed listed seven. job:CREADB2 moved to wave 7. What is left runs no application program and shares no data. Most of it is replaced with target configuration: CICS resource definitions, RACF commands, a catalog listing. The FTP job holds an address, a user name and a password in the JCL (`app/jcl/FTPJCL.JCL:33`). Rotate that credential before anything is copied. The stale cluster delete points at a different high level qualifier than the rest of the system (`app/jcl/DEFCUST.jcl:25`). This wave is a chore. It proves the build and scheduler path and nothing else.

## Wave 2. Read-only master listings and the import job

Units: CBACT01C, CBACT02C, CBACT03C, CBCUS01C, CBIMPORT, job:CBIMPORT, job:READACCT, job:READCARD, job:READCUST, job:READXREF.

This is the low risk place to build the harness and port the shared layouts. CBACT01C is the effort outlier (variable length and COMP-3 arrays, an assembler call at `app/cbl/CBACT01C.cbl:231`). CBIMPORT opens a file its job never defines (`app/cbl/CBIMPORT.cbl:233`, `app/jcl/CBIMPORT.jcl:33`), so the shipped job cannot have run cleanly.

Judgment call. The CA-7 listing chains READACCT, READCARD, READCUST and READXREF between CLOSEFIL and OPENFIL (`app/scheduler/CardDemo.ca7:340`, `app/scheduler/CardDemo.ca7:453`). The seed's chain rule would then move them to wave 5, because CLOSEFIL and OPENFIL sit there. I kept them in wave 2. The chain brackets a window and carries no data, and the four jobs write only private files. Moving them would empty the one wave that proves the toolchain. The price: while waves 5 and 6 still write the masters, these ported jobs must read the legacy VSAM files or a snapshot.

## Wave 3. Read-only online screens and the menu spine

Units: COACTVWC, COADM01C, COCRDSLC, COMEN01C, COSGN00C, COTRN00C, COTRN01C.

Computed calls in this wave (COACTVWC, COADM01C, COCRDSLC, COMEN01C, COTRN00C, COTRN01C) keep confidence below high. What they can reach, from `02-coupling.md`: the menus reach the 11 and 6 programs in their tables, and the others return to the caller.

The cycle COSGN00C, COMEN01C, COADM01C moves whole, and so do COTRN00C and COTRN01C. Most of what the menus dispatch to is in waves 6 and 7, so this wave needs a router that hands the COMMAREA to programs that are still on the mainframe. That router is the facade, and wave 6 reuses it. Sign on compares a clear text password after upper casing it (`app/cbl/COSGN00C.cbl:132`, `app/cbl/COSGN00C.cbl:223`). Keeping that is a security decision for the deviation register.

## Wave 4. Build and generation group plumbing

Units: job:CBLDBMS, job:CICCMP, job:CNJBATMP, job:DEFGDGD, job:IMSMQCMP, job:INTRDRJ1, job:INTRDRJ2, proc:BUILDBAT, proc:BUILDBMS, proc:BUILDONL.

The compile and link jobs are replaced by the target build. The wave is mostly retirement. It is a chore: it delivers nothing a stakeholder can name. It has one real output, the decision on how the target keeps the last five generations of the transaction backup, the system transactions and the report. Two jobs define the same report group with different limits (`app/jcl/REPTFILE.jcl:27`, `app/jcl/DEFGDGB.jcl:36`). The catalog listing in the tree shows the group at LIMIT 5 with five generations (`app/catlg/LISTCAT.txt:1535`). The seed put job:TXT2PDF1 here and it moved to wave 5.

## Wave 5. Nightly batch core

All three must-not-break items are here. It has 56 units, which is more than 25. Size alone is not a reason to cut, and one sentence describes the wave: batch jobs and programs that write data another entry point also uses. Of the 56, 17 are scheduler and wrapper views of jobs already listed. I did not cut it. The wrappers, the Control-M folders and the CA-7 chains bind most of it (`scripts/run_full_batch.sh:13`, `app/scheduler/CardDemo.controlm:5`), and the seed's chain rule keeps chained jobs together. The wave does have an internal order, and the `--wave 5` plan must follow it.

| Stage | Units | Why this order | Evidence |
|---|---|---|---|
| 5a. Units that only read the masters | CORPT00C, job:TRANREPT, proc:TRANREPT, proc:REPROC, CBTRN03C, CSUTLDTC, CBSTM03A, CBSTM03B, job:CREASTMT, job:TXT2PDF1, CBEXPORT, job:CBEXPORT, job:PRTCATBL | No scheduler chains them, and they can be proved against archived output before any writer moves. Consumers move before producers. CBTRN03C, CBSTM03A and CBEXPORT are the articulation points. | `app/jcl/TRANREPT.jcl:59`, `app/jcl/CREASTMT.JCL:79`, `app/jcl/CBEXPORT.jcl:43` |
| 5b. The chained cycle | job:CLOSEFIL, job:OPENFIL, job:WAITSTEP, COBSWAIT, the refresh jobs, job:TRANBKP, job:POSTTRAN with CBTRN02C, job:INTCALC with CBACT04C, job:COMBTRAN, job:TRANIDX, the Control-M jobs and the four wrappers | Chained by the wrappers. These jobs write the masters. Order inside: refresh, backup, post, interest, combine, index. | `scripts/run_posting.sh:17`, `scripts/remote_refresh.sh:17`, `scripts/run_full_batch.sh:47` |
| 5c. Definitions and tests | job:DEFGDGB, job:DALYREJS, job:REPTFILE, job:SORTTEST, job:REPRTEST | Generation definitions come first in practice. The two test jobs are retired. | `app/jcl/DEFGDGB.jcl:24`, `app/jcl/REPTFILE.jcl:27` |

Dependencies that cross the wave edge:

- **Wave 7 feeds the report.** TRANTYPE.PS and TRANCATG.PS, which the report reads, are unloaded from DB2 by TRANEXTR (`app/app-transaction-type-db2/jcl/TRANEXTR.jcl:72`, `app/app-transaction-type-db2/jcl/TRANEXTR.jcl:102`). The file is the contract, so wave 5 goes first. TRANEXTR's own comment says it exists for the report (`app/app-transaction-type-db2/jcl/TRANEXTR.jcl:19`).
- **A Control-M condition crosses into wave 7.** The weekly disclosure group folder waits for MNTTRDB2 (`app/scheduler/CardDemo.controlm:34`). Moving the folder needs a condition that both schedulers can see.
- **Wave 6 writes what wave 5 rebuilds.** The online writers write ACCTDATA, TRANSACT and CARDDATA. Wave 5 has to own those masters first, or CICS and the new batch will hold the same file.
- **Confidence cannot be high.** CORPT00C makes a computed call (`app/cbl/CORPT00C.cbl:548`), and the CA-7 listing that binds part of the wave is not parsed.

The must-not-break mapping is in `00-summary.md`.

## Wave 6. Online writers

Units: COACTUPC, COBIL00C, COCRDLIC, COCRDUPC, COTRN02C, COUSR00C, COUSR01C, COUSR02C, COUSR03C.

Four are high difficulty and high blast: COACTUPC, COBIL00C, COCRDUPC and COTRN02C. COCRDLIC and COUSR00C are list screens that sit here because they can transfer into an update screen. They are read only themselves, and they could go with wave 3 if the router hides the transfer. The plan keeps the seed's grouping. Every unit makes a computed call and none of the return targets is fully bounded, so confidence is low. Strangle these behind the wave 3 router, one screen at a time. COBIL00C and COTRN02C take the next transaction key from the last key (`app/cbl/COBIL00C.cbl:212`, `app/cbl/COTRN02C.cbl:444`), so during any overlap with the batch writers the key spaces have to be split.

## Wave 7. Subsystems

Units: the 13 programs that use DB2, IMS or MQ, their jobs, and the DB2 scheduler jobs. job:CREADB2 joined from wave 1.

This wave is last because the plugin has no analysis for DB2, IMS or MQ. It is also the easiest to sequence. The authorization option is optional: the menu checks that COPAUS0C is installed before it transfers (`app/cbl/COMEN01C.cbl:148`), so wave 7 can wait. COPAUS0C and COPAUS1C move together. Four programs make computed calls, so confidence is low. The size is the hard part: the database definition and layout files are not read, and there is no way to size this wave from what the extractor saw.

## Deviations

| Unit | From | To | Reason | Evidence |
|---|---|---|---|---|
| job:CREADB2 | 1 | 7 | The seed put it in the utility family because it runs no application program. Its steps run DB2 utilities that create the database and load two tables. The SQL is in `.ctl` members the extractor does not read. Anything that touches DB2 belongs with the subsystem family. | `app/app-transaction-type-db2/jcl/CREADB21.jcl:19`, `app/app-transaction-type-db2/jcl/CREADB21.jcl:58`, `app/app-transaction-type-db2/ctl/DB2CREAT.ctl:1` |
| job:TXT2PDF1 | 4 | 5 | It reads the statement file that job:CREASTMT writes, and the CA-7 listing has CREASTMT trigger it. The seed put the consumer in wave 4 and its only producer in wave 5. A wave 4 unit whose only input comes from a wave 5 job has no testable edge. Chained jobs move together, in the later family. | `app/jcl/CREASTMT.JCL:91`, `app/jcl/TXT2PDF1.JCL:33`, `app/scheduler/CardDemo.ca7:495` |

## What I considered and did not do

| Option | Why not | Evidence |
|---|---|---|
| Cut wave 5 at CBTRN03C, CBSTM03A and CBEXPORT | Size alone is not a reason, and the wave has one description. The internal stages 5a and 5b give the same protection without renumbering the 34 units in waves 6 and 7. I would cut it if the client cannot stage inside one wave. | `analysis` field `articulation_points` |
| Move READACCT, READCARD, READCUST and READXREF to wave 5 | The CA-7 chain would pull them there. It is a window, not a data flow, and it would empty wave 2. | `app/scheduler/CardDemo.ca7:340` |
| Move the menu cycle to the last online wave | It is low difficulty and high blast. It is a hub that every other online program returns to (`analysis` field `fan_in`), so it cannot go last without a bridge from the mainframe menu into new programs, which is the same facade in the other direction. | `app/cbl/COMEN01C.cbl:156` |
| Place CBTRN01C in a wave | It is not reached by any static edge and no job runs it. It stays unassigned and in the unknown dead code bucket. | `app/cbl/CBTRN01C.cbl:254` |

## Not placed

| Unit | Reason | Evidence |
|---|---|---|
| CBTRN01C | Not reached by any static edge, and 28 reachable computed calls could target it. The option tables do not list it, the CSD defines no program for it, no JCL runs it, and it opens all six files INPUT. Ask the client whether anyone runs it by hand. | `app/cbl/CBTRN01C.cbl:254`, `app/cpy/COMEN02Y.cpy:28` |
