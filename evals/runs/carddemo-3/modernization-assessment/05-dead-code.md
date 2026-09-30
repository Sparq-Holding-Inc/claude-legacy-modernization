# 05 Dead code

Telemetry is `none`. Every claim in this file is provisional. No production run data, job log or SMF record was available, so no unit can be shown to be unused, only unreachable in this tree. The candidate list is `05a-dead-code-candidates.md`. The register is `dead-code.json`.

## Unreachable

Safe to propose for deletion, subject to the provisional status above.

| Unit | Reason | Confidence | Evidence |
|---|---|---|---|
| cpy:UNUSED1Y | No program includes it and no path reaches it. A copybook is compile-time only, so nothing can call it at run time. | high | `app/cpy/UNUSED1Y.cpy:1` |

The extractor also listed `proc:TRANREPT` here. I moved it out. It is live. The online report screen writes a job that runs `EXEC PROC=TRANREPT` to the JOBS queue (`app/cbl/CORPT00C.cbl:94`, `app/cbl/CORPT00C.cbl:517`). The extractor does not follow the internal reader, so it saw no caller. Deleting that proc would break the second route to a must-not-break report. It sits in the unknown bucket below, with the reason.

## Reachable but dormant

None. The rule marks a program dormant when it is reachable and has not been modified for 5 years. The extractor ran with an as-of date of 2026-09-30. The oldest last-modified date in the tree is 2022-09-01, which is 4.1 years earlier, so nothing crosses the line.

Two cautions.

- 15 programs carry the 2022-09-01 date: COACTVWC, COBIL00C, COCRDLIC, COCRDSLC, COCRDUPC, CORPT00C, COSGN00C, COTRN00C, COTRN01C, COTRN02C, COUSR00C, COUSR01C, COUSR02C, COUSR03C and CSUTLDTC. They cross 5 years on 2027-09-01. Do not read that as a deletion signal. Every one is reached from a menu table (`app/cpy/COMEN02Y.cpy:28`, `app/cpy/COADM02Y.cpy:29`), and dormant means old, not unused.
- The dates come from git history of this copy of the tree (`graph.json` records `git_dates: true`). A repository import date says nothing about production activity (inference). With telemetry `none`, treat the dormant list as empty and unproven, not as clean.

## Unknown

Not reached by any static edge in this tree. The extractor says 28 computed calls could reach any of them. Those 28 are CICS transfers between online programs, so they are unlikely to start a batch program (inference; see `02-coupling.md`). The rule still holds: only telemetry moves a program out of this bucket. **Do not delete anything below on the strength of this assessment.**

| Unit | Reason | Confidence | Evidence |
|---|---|---|---|
| proc:TRANREPT | The extractor says unreachable. It is live through CORPT00C and the internal reader. Do not delete. | low | `app/cbl/CORPT00C.cbl:94`, `app/cbl/CORPT00C.cbl:517` |
| CBTRN01C | No JCL step runs it and no program calls it. Its header says it posts daily transactions, which CBTRN02C does. It may be an earlier draft. It reads six files, and none of its DDs is mapped. Ask before deleting. | low | `app/cbl/CBTRN01C.cbl:5` |
| CBPAUP0C | Run by the IMS BMP job CBPAUP0J, which names it in PARM. The extractor does not read PARM. It is live: CA-7 runs CBPAUP0J after CLOSEFIL and before POSTTRAN. | low | `app/app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl:25`, `app/scheduler/CardDemo.ca7:43` |
| DBUNLDGS | Run by UNLDGSAM.JCL, which names it in PARM. No scheduler in the tree names that job. A manual utility. Instrument before any deletion. | low | `app/app-authorization-ims-db2-mq/jcl/UNLDGSAM.JCL:27` |
| PAUDBLOD | Run by LOADPADB.JCL, which names it in PARM. No scheduler in the tree names that job. A manual load utility. Instrument before any deletion. | low | `app/app-authorization-ims-db2-mq/jcl/LOADPADB.JCL:27` |
| PAUDBUNL | Run by UNLDPADB.JCL, which names it in PARM. No scheduler in the tree names that job. A manual unload utility. Instrument before any deletion. | low | `app/app-authorization-ims-db2-mq/jcl/UNLDPADB.JCL:39` |
| COBTUPDT | Run by MNTTRDB2 through a DSN command, and Control-M schedules MNTTRDB2 weekly. It is live. | low | `app/app-transaction-type-db2/jcl/MNTTRDB2.jcl:30`, `app/scheduler/CardDemo.controlm:27` |
| cpy:IMSFUNCS | Included only by DBUNLDGS, PAUDBLOD and PAUDBUNL. Its status follows theirs. | low | `app/app-authorization-ims-db2-mq/cbl/DBUNLDGS.CBL:136` |
| cpy:PADFLPCB | Included only by DBUNLDGS. Its status follows that program. | low | `app/app-authorization-ims-db2-mq/cbl/DBUNLDGS.CBL:156` |
| cpy:PASFLPCB | Included only by DBUNLDGS. Its status follows that program. | low | `app/app-authorization-ims-db2-mq/cbl/DBUNLDGS.CBL:155` |
| cpy:PAUTBPCB | Included by DBUNLDGS, PAUDBLOD and PAUDBUNL. Its status follows theirs. | low | `app/app-authorization-ims-db2-mq/cbl/PAUDBLOD.CBL:161` |

Two of the six programs here (CBPAUP0C and COBTUPDT) are demonstrably live. The extractor put them in the bucket because a `PARM` string and a DSN command are not part of what it reads. That is a blind spot in the tool, not a finding about the code.

## Jobs the extractor calls unscheduled

`analysis.unscheduled_jobs` lists 35 jobs. That list is not evidence of dead jobs, because the extractor did not parse the CA-7 listing. Eight of the 35 are scheduled there: CBPAUP0J (`app/scheduler/CardDemo.ca7:43`), READACCT (`app/scheduler/CardDemo.ca7:340`), READCARD (`app/scheduler/CardDemo.ca7:367`), READCUST (`app/scheduler/CardDemo.ca7:394`), READXREF (`app/scheduler/CardDemo.ca7:421`), CREASTMT (`app/scheduler/CardDemo.ca7:468`), TXT2PDF1 (`app/scheduler/CardDemo.ca7:495`) and PRTCATBL (`app/scheduler/CardDemo.ca7:537`).

The other 27 are not proposed for deletion. Most are setup, build or sample jobs that run by hand, and the plan retires or ports them by what they do (`03-waves.md`). TRANREPT is one of the 27 and is on the must-not-break list, so "unscheduled" only means a person or the online screen submits it.

## What telemetry would change

The client can settle every unknown row with twelve months of job logs or SMF records for these programs and jobs: CBTRN01C, DBUNLDGS, PAUDBLOD, PAUDBUNL and the 27 unscheduled jobs. Until then, treat all of this as a list of questions.
