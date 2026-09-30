# 00 Summary: CardDemo modernization assessment

Assessed as of 2026-09-30 with extractor 0.2.0. The full write-up is in files `01` to `06`. This
page is for the steering committee.

## Scoping answers

| Question | Answer | How it was set |
|---|---|---|
| Scope | `.` (the work folder) | No path argument, so the current directory |
| Target state | refactor | `--target refactor` |
| What must not break | daily transaction posting, the account and card master refresh, and the transaction report | `--must-not-break` |
| Runtime telemetry | none | `--telemetry none` |

All three answers came as flags, so no defaults applied. With telemetry `none`, every dead-code
claim in `05-dead-code.md` is provisional.

## What was assessed

The tree holds 44 COBOL programs (17 batch, 25 online transactions, 2 subprograms) with 22,904 lines
of COBOL, 62 copybooks, 21 BMS maps, 55 JCL jobs, 6 procs, 19 scheduler artifacts, 110 datasets and
1,224 extracted edges: 318 call, 62 contract, 235 data, 476 include and 133 temporal (`analysis`,
fields `node_counts` and `edge_counts`). 99 entry points were found and 28 computed calls could not
be resolved by the extractor (`analysis`, fields `entry_points` and `unresolved_dynamic`). I settled
those 28 by reading the source; the result is in `02-coupling.md` and is inference.

## The wave plan

Seven waves. I kept the extractor's seed order and made three logged changes to it.

| Wave | Name | Units | Blast radius | Confidence | Evidence |
|---|---|---|---|---|---|
| 1 | Batch utility jobs and platform readiness | 6 | low | medium | `app/jcl/CBADMCDJ.jcl:1` |
| 2 | Read-only batch over the masters | 10 | low | medium | `app/jcl/READACCT.jcl:1` |
| 3 | Sign-on, menus and read-only online views | 7 | medium | medium | `app/csd/CARDDEMO.CSD:317` |
| 4 | Build tooling, GDG bases and demo jobs | 9 | low | medium | `app/jcl/DEFGDGD.jcl:39` |
| 5 | The nightly batch cycle | 56 | high | medium | `app/jcl/POSTTRAN.jcl:23` |
| 6 | Online writers of the masters | 9 | high | medium | `app/cbl/COACTUPC.cbl:573` |
| 7 | Authorization, IMS, DB2 and MQ subsystem | 26 | high | low | `app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:956` |

Waves 1 and 4 unblock nothing and are mostly replaced, not ported. The order and reasons are in
`03-waves.md`. The estimate is about 70 to 150 engineer-weeks, with wave 5 the largest at 24 to 48
and wave 7 the least certain (`04-estimate.md`).

## Where the three must-not-break items sit

| Item | Units I mapped it to | Basis | Confidence | Evidence |
| --- | --- | --- | --- | --- |
| Daily transaction posting | `job:POSTTRAN`, `CBTRN02C`, and the jobs around it: `TRANBKP`, `COMBTRAN`, `TRANIDX`, `DALYREJS`, `CLOSEFIL`, `OPENFIL` | The wrapper labels the job "Core processing job" | high | `app/jcl/POSTTRAN.jcl:23`, `scripts/run_posting.sh:25` |
| Account and card master refresh | `job:ACCTFILE`, `job:CARDFILE` (and `XREFFILE`, `CUSTFILE` by the same pattern) | The wrappers label them "Refresh Account Master file" and "Refresh Card Master" | medium | `scripts/remote_refresh.sh:16`, `scripts/remote_refresh.sh:19`, `app/jcl/ACCTFILE.jcl:25` |
| Transaction report | `job:TRANREPT`, `proc:TRANREPT`, `CBTRN03C`, and `CORPT00C`, which submits the same proc from a screen | `TRANREPT` runs `CBTRN03C`. `CORPT00C` builds JCL that names the proc | high | `app/jcl/TRANREPT.jcl:59`, `app/cbl/CORPT00C.cbl:94` |

All three land in wave 5 and all three map to units in the tree. Two mappings are judgments and are
in the questions below.

## The single largest risk

The nightly cycle rebuilds the transaction master instead of appending to it, and nothing in the tree
says which order is the real one. `TRANBKP` copies the master and then deletes it
(`app/jcl/TRANBKP.jcl:40`). `POSTTRAN` loads the empty file with OPEN OUTPUT
(`app/cbl/CBTRN02C.cbl:256`). `COMBTRAN` restores history from a relative generation number
(`app/jcl/COMBTRAN.jcl:24`), and the report job writes that same generation
(`app/jcl/TRANREPT.jcl:33`). The two wrapper scripts, the Control-M folder and the CA-7 listing give four
different daily orders (`02-coupling.md`). A port that reproduces every program correctly but gets the
order or the generation rule wrong loses or duplicates history in a master that 11 programs read
(`analysis`, field `data_hubs`). The failure would show as a wrong number on the report or at the next
fiscal close, not as an abend. It touches all three must-not-break items.

## Other findings a committee should hear

| Finding | Why it matters | Confidence | Evidence |
| --- | --- | --- | --- |
| Record layouts are also byte offsets in JCL and in a COBOL literal, in ten places | A field change breaks them with no compile error | high | `app/jcl/TRANREPT.jcl:41`, `app/cbl/CORPT00C.cbl:100` |
| The batch and online sides both write the account and transaction masters | Wave 5 and wave 6 cannot have different owners of those masters | high | `app/cbl/CBTRN02C.cbl:256`, `app/cbl/COBIL00C.cbl:234` |
| The report code may double count its last transaction and stop early at a date filter (inference from the source, not run) | Archived reports may already contain the difference | low | `app/cbl/CBTRN03C.cbl:177`, `app/cbl/CBTRN03C.cbl:200` |
| Clear text passwords are stored, compared and seeded in JCL, and an FTP job carries a host, user and password | Security decision needed before any port | high | `app/cbl/COSGN00C.cbl:223`, `app/jcl/FTPJCL.JCL:33` |
| Of 24 high-high units, 14 are in wave 5, and none is in waves 1 to 4 | The plan does not put the hardest work early | medium | `modernization-assessment/risks.json:1` |

## Open Questions for the client's engineers

1. Which order runs production every night: the shell wrappers, the Control-M folders or the CA-7
   listing? The Control-M DAILY folder has no `POSTTRAN` (`app/scheduler/CardDemo.controlm:3`), and
   CA-7 chains `POSTTRAN` after the IMS purge `CBPAUP0J` (`app/scheduler/CardDemo.ca7:70`). Is that
   trigger real, and why does a purge gate posting?
2. Is the account and card master refresh a nightly full replacement in production, or a reset for a
   test region? `ACCTFILE` deletes and reloads the account master from a flat file
   (`app/jcl/ACCTFILE.jcl:25`) and the posting wrapper runs it before `POSTTRAN`
   (`scripts/run_posting.sh:17`). If it is production, who writes the flat file, and does it carry the
   balances posting wrote yesterday?
3. Did "master refresh" mean the reload jobs I chose, or the read-only listing jobs `READACCT` and
   `READCARD` (`app/jcl/READACCT.jcl:32`)? I assumed the reload jobs because the wrappers call them
   refresh.
4. If the backup step in `TRANBKP` ends above return code 4, the delete still runs and the define is
   skipped (`app/jcl/TRANBKP.jcl:51`; inference from the JCL). Has a night ever left the master empty,
   and how was it recovered?
5. Who maintains the `DATEPARM` dataset the batch report reads (`app/jcl/TRANREPT.jcl:73`), and why does
   the SORT card carry a range in 2022 (`app/jcl/TRANREPT.jcl:43`)? Is the batch report used at all, or
   only the screen (`app/cbl/CORPT00C.cbl:94`)?
6. Can you send five or more generations of the report and the matching transaction backups? They let us
   check whether the last transaction is counted twice and whether totals stop early
   (`app/cbl/CBTRN03C.cbl:200`). The catalog shows only five generations kept
   (`app/catlg/LISTCAT.txt:1639`).
7. Is `CBTRN01C` retired? No JCL runs it and no CSD entry defines it (`app/cbl/CBTRN01C.cbl:154`).
8. Does the branch import job run in production? The program opens a card output DD that the job never
   provides (`app/cbl/CBIMPORT.cbl:233`).
9. What do the assembler routines `COBDATFT` and `MVSWAIT` do exactly, and can library calls replace
   them (`app/cbl/CBACT01C.cbl:231`, `app/cbl/COBSWAIT.cbl:38`)?
10. Please supply the REXX exec library behind the PDF step (`app/jcl/TXT2PDF1.JCL:31`).
11. Please supply the IMS DBD and PSB files, the DB2 DDL and DCLGEN and the `.ctl` members for a
    second pass on wave 7. Is the secondary index database used at run time
    (`app/app-authorization-ims-db2-mq/jcl/DBPAUTP0.jcl:32`)?
12. Are the passwords in `DUSRSECJ` and `ESDSRRDS` and the FTP credentials real production values
    (`app/jcl/DUSRSECJ.jcl:35`, `app/jcl/ESDSRRDS.jcl:36`, `app/jcl/FTPJCL.JCL:33`)?
13. What rule keeps transaction ids unique across the three ways they are made: the highest key plus one
    online, the input file in posting, and the PARM date in interest (`app/cbl/COTRN02C.cbl:444`,
    `app/cbl/CBTRN02C.cbl:425`, `app/cbl/CBACT04C.cbl:476`)?
14. Does anything read the alternate index on the transaction master? I found no reader in the tree
    (inference), and two jobs still build it (`app/jcl/TRANIDX.jcl:27`, `app/jcl/TRANFILE.jcl:84`).

## Not parsed

Every file group the extractor listed as not read. Each one is a gap in the coupling picture.

| Files | Reason | What they may hide | Evidence |
|---|---|---|---|
| 3 DB2 DCLGEN files (`.dcl`) | Not read | Column layouts behind wave 7 | `app/app-authorization-ims-db2-mq/dcl/AUTHFRDS.dcl:1` |
| 6 DB2 DDL files (`.ddl`) | Not read | Tables, keys and indexes for wave 7 | `app/app-authorization-ims-db2-mq/ddl/AUTHFRDS.ddl:1` |
| 4 IMS DBD files (`.dbd`) | Not read | The authorization hierarchy and its secondary index | `app/app-authorization-ims-db2-mq/ims/DBPAUTP0.dbd:1` |
| 4 IMS PSB files (`.psb`) | Not read | Which programs may read or change which segments | `app/app-authorization-ims-db2-mq/ims/DLIGSAMP.PSB:1` |
| 8 control card files (`.ctl`) | Not read | The DB2 commands behind `CREADB2` and the REPRO card behind the report proc | `app/app-transaction-type-db2/ctl/DB2CREAT.ctl:1` |
| 2 assembler sources (`.asm`) | Not read | `COBDATFT` and `MVSWAIT`, called from COBOL | `app/asm/COBDATFT.asm:1` |
| 2 assembler macros (`.mac`) | Not read | Macros for those routines | `app/maclib/ASMWAIT.mac:1` |
| The CA-7 listing | Not Control-M XML, so not parsed | A second daily order and the trigger chain, which I read by hand | `app/scheduler/CardDemo.ca7:1` |

## Extractor limits that touch this system

| Limit in `meta.limits` | How it touches this system | Evidence |
|---|---|---|
| COPY REPLACING is not applied | One wave 7 program uses it | `app/app-transaction-type-db2/cbl/COTRTUPC.cbl:1358` |
| A variable call target is resolved only from VALUE clauses and literal MOVEs in the same program | 28 computed calls stayed open | `app/cbl/COMEN01C.cbl:184` |
| A called subprogram gets no DDs from its caller's JCL step | The statement subprogram's four DDs are mapped by the caller's step | `app/jcl/CREASTMT.JCL:79` |
| SORT and most in-stream control cards are not read | Layout offsets and the report date range live in SORT cards | `app/jcl/TRANREPT.jcl:41` |
| The program a step runs is read only from PARM for DFSRRC00 and from a RUN PROGRAM card for IKJEFT01 | `CREADB2` takes its DB2 commands from an unparsed member | `app/app-transaction-type-db2/jcl/CREADB21.jcl:58` |
| IF/THEN/ELSE and COND= are not modeled | Conditional steps in the backup and statement jobs | `app/jcl/TRANBKP.jcl:51`, `app/jcl/CREASTMT.JCL:79` |
| Nested PROC calls are not followed, and JCL text in a COBOL literal makes no edge | The report proc calls another proc, and `CORPT00C` builds JCL | `app/proc/TRANREPT.prc:21`, `app/cbl/CORPT00C.cbl:94` |
| EXEC CICS RETURN, START and SEND MAP are not edges | Every screen chains to the next this way | `app/cbl/CORPT00C.cbl:199` |
| Only Control-M XML and shell wrappers are read as schedulers | The CA-7 listing is skipped | `app/scheduler/CardDemo.ca7:43` |
| DCB, LRECL and RECFM are not read | I compared the record sizes of four masters and one reject file by hand and they agree | `app/jcl/POSTTRAN.jcl:36`, `app/cbl/CBTRN02C.cbl:177` |
| A contract edge is high when both sides COPY the same layout, which is not proof of equal use | All 62 are high, and the statement job reads a re-sorted copy of the transaction master | `app/jcl/CREASTMT.JCL:53` |
| LINK and XCTL are both call edges and control flow is not modeled | The menus use XCTL, which never returns | `app/cbl/COSGN00C.cbl:231` |

## How the work was split

Scripts extracted the graph and rendered the fact tables (`01`, `02a`, `03a`, `05a`). I cut the waves,
scored the risk and wrote `02`, `03`, `04`, `05`, `06`, `waves.json`, `dead-code.json` and
`risks.json`. The dependency-cartographer and migration-risk-assessor work was done inline by me, in the
same session, following their instruction files, because the agents could not be started here.
