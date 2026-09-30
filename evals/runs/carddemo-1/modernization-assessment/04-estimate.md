# 04 Estimate

Target state: refactor. Telemetry: none. Every range below is provisional and is in person-weeks of engineering effort, with Claude Code doing the mechanical port and a person reviewing it. There is no measured port velocity for this team. Wave 1 is where that gets measured, and the ranges for later waves should be redone after it.

## Method

I did not price lines of code. The weights, heaviest first, come from the skill: the coupling edges that cross a wave boundary, whether a behavioral oracle exists, god modules in the wave, how much logic sits in the database, and whether the team can read the source language. For each wave I took four inputs from the graph and the source, then set a range and named what it is most sensitive to.

| Wave | Programs and lines | JCL jobs and lines | Coupling edges crossing the boundary | Shared datasets | High-high units | Evidence |
|---|---|---|---|---|---|---|
| 1 | 0 | 11 jobs, 342 | 0 | 0 | 0 | analysis: `waves.json` units, `graph.json` node `loc` |
| 2 | 6 programs, 1,097 | 6 jobs, 97 | 7 contract | 5 | 0 | analysis: `edge_counts`; `app/jcl/READACCT.jcl:32` |
| 3 | 8 programs, 2,793 | 0 | 39 (25 call, 14 contract) | 6 | 0 | analysis: `edge_counts`; `app/cpy/COMEN02Y.cpy:28` |
| 4 | 0 | 18 jobs, 574 (5 jobs are build tooling) | 0 | 0 | 0 | analysis: `waves.json` units; `app/jcl/DISCGRP.jcl:25` |
| 5 | 7 programs, 3,556 | 11 jobs, 435 | 29 (26 contract, 3 call) | 6 | 16 | analysis: `edge_counts`; `app/cbl/CBTRN02C.cbl:256` |
| 6 | 9 programs, 7,972 | 1 job, 82 | 51 (33 contract, 18 call) | 7 | 5 | analysis: `edge_counts`; `app/cbl/COACTUPC.cbl:3894` |
| 7 | 13 programs, 7,071 | 8 jobs, 266 | 16 (12 contract, 4 call) | 4 | 14 | analysis: `edge_counts`; `app/app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl:25` |

Line counts are non blank source lines from the extractor. Forty-six of the 62 contract edges cross a wave boundary, which is what the plan pays for: each is a place where one side moves while the other stays.

## Estimate per wave

| Wave | Range (person-weeks) | Most sensitive to | Confidence | Evidence |
|---|---|---|---|---|
| 1 Batch environment and file bracket jobs | 2 to 4 | The new scheduler and deploy path, not the eleven jobs | medium | `app/jcl/DEFGDGB.jcl:24` |
| 2 Read only master extracts | 3 to 6 | Whether the target reads the layouts byte for byte | medium | `app/jcl/READACCT.jcl:35` |
| 3 Sign on, menu and read only screens | 8 to 14 | The router facade and the password decision | medium | `app/cbl/COSGN00C.cbl:223` |
| 4 Reference data loads and build tooling | 3 to 6 | Whether the flat file inputs really arrive as the JCL says | low | `app/jcl/TRANTYPE.jcl:57` |
| 5 Daily posting cycle, interest, report and statements | 16 to 28 | The oracle, the shim for CBPAUP0J, and snapshot rollback | medium | `app/cbl/CBTRN02C.cbl:256` |
| 6 Online maintenance writers | 18 to 32 | Concurrency with batch, and COACTUPC | low | `app/cbl/COACTUPC.cbl:3894` |
| 7 IMS, DB2 and MQ subsystem | 20 to 44 | Schemas the plugin never read | low | `app/app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl:25` |
| Total | 70 to 134 | The three assumptions in the next section | low | inference |

Do not read the total as a plan. It is the sum of seven ranges whose confidence is medium at best, and the width of wave 7 alone is 24 person-weeks.

## The assumptions each range is most sensitive to

Each is written so it can be proven wrong.

1. **Wave 3.** Assumes the menu tables in `app/cpy/COMEN02Y.cpy` and `app/cpy/COADM02Y.cpy` are the only dispatch paths that matter. If any of the 23 XCTL sites that take their target from the COMMAREA reaches a program outside the 17 in those tables, the router facade must cover it and wave 3 grows by about a quarter. Check by listing every move into CDEMO-TO-PROGRAM.
2. **Wave 5.** Assumes at least one month of daily posting files, reject files and transaction master backups can be recovered for replay, including a month end. If only one day exists, the harness needs synthetic month end cases and wave 5 rises by 4 to 6 person-weeks. The tree holds one seeded file of 300 transactions (`app/data/ASCII/dailytran.txt:1`), which is a sample, not production.
3. **Wave 5 and 6 together.** Assumes online and batch never overlap in the target, as CLOSEFIL keeps them apart today (`app/jcl/CLOSEFIL.jcl:26-30`). If online must stay up through the batch window, add 6 to 10 person-weeks for a concurrency design.
4. **Wave 6.** Assumes the 43 REDEFINES in COACTUPC are mostly screen and edit overlays and not type punning. If more than a handful are punning, wave 6 rises by about 30 percent. Check by reading each against its use.
5. **Wave 7.** Assumes the authorization database has only the root and child segments the unload programs read (`app/app-authorization-ims-db2-mq/jcl/UNLDPADB.JCL:33-35`). The DBD is not parsed. If it holds more, wave 7 lands at the top of its range.
6. **All waves.** Assumes no program reads a shared master through a private layout. The 62 contract edges are `high` because both sides copy the same copybook, and the extractor says that is not proof (`meta.limits`). If even three do, waves 5 and 6 each grow 15 to 25 percent.

## Where Claude Code helps and where it does not

Strong, given a working harness:

- Transliterating the plumbing programs: CBACT01C, CBACT02C, CBACT03C, CBCUS01C, and the list and view screens COTRN00C, COTRN01C, COACTVWC and COCRDSLC.
- Turning IDCAMS, REPRO, SORT and IEBGENER jobs into load scripts. The ten reload jobs are the same three steps: delete, define, copy.
- Building the diff harness, the normalization rules and the replay runner, and generating test data from the seeded files in `app/data`.

Weak, because the intent is not written down:

- The rejection rules and the swallowed account rewrite in CBTRN02C (`app/cbl/CBTRN02C.cbl:385-419`, `:554-559`).
- The early exit and the double count at end of file in CBTRN03C (`app/cbl/CBTRN03C.cbl:177`, `:200-203`).
- Interest that truncates instead of rounding (`app/cbl/CBACT04C.cbl:464-465`).
- The hardcoded dates in JCL (`app/jcl/INTCALC.jcl:22`, `app/jcl/TRANREPT.jcl:43-44`).
- ALTER in CBSTM03A (`app/cbl/CBSTM03A.CBL:300-310`).
- Anything that depends on VSAM key order, the meaning of CA-7 entries, or IMS, DB2 and MQ behavior.

## Other inputs to the estimate

| Input | Finding | Evidence |
|---|---|---|
| Behavioral oracle | Sample files only; production replays and archived reports are unknown | `app/data/ASCII/dailytran.txt:1`, `app/catlg/LISTCAT.txt:1` |
| God modules | None by fan-in; COACTUPC is the size risk | analysis: `god_modules` |
| Logic in the database | DB2 holds one reference table; IMS holds authorizations; both schemas unread | analysis: `unparsed` |
| Team that reads COBOL | Not known | inference |
| Build tooling | Nine units are compile jobs and procs the target build replaces (listed in `risks.json` under `do_not_port`) | `samples/jcl/BMSCMP.jcl:1`, `samples/proc/BUILDBAT.prc:1` |
