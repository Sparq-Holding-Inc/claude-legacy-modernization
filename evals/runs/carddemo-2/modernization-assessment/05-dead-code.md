# 05 Dead code

Telemetry is none, so every claim below is provisional. Nothing here is a reason to delete anything except one copybook, and that only after the client agrees. The candidates come from `modernization-assessment/05a-dead-code-candidates.md`, which the extractor computed. The register is in `modernization-assessment/dead-code.json`.

## Read this first

| Warning | What it means for the buckets | Confidence | Evidence |
|---|---|---|---|
| The CA-7 scheduler file was not parsed | Every job it schedules counts as unscheduled, so the list of 35 unscheduled jobs is overstated. I read the listing by hand. It names eight of the 35 (see below). | high | `app/scheduler/CardDemo.ca7:43`, `app/scheduler/CardDemo.ca7:340`, `app/scheduler/CardDemo.ca7:495` |
| The dormant bucket is empty, and that does not mean nothing is dormant | Dormancy is measured from the last change date in git. Across the programs, copybooks, jobs and procs there are only four distinct dates, and 99 units share 2022-09-01, which is 4 years before the as-of date and under the 5 year line. The dates look like bulk commits, not real change dates. Dormancy was not measured in any useful way. | high | `analysis` (fields `as_of`, `dormant_years` and `dead_code_candidates`), `app/cpy/CVACT01Y.cpy:1` |
| Every job is an entry point | A job no parsed scheduler names is still an entry point, so it never appears in a bucket. Only programs and copybooks can. | high | `analysis` (field `unscheduled_jobs`) |
| The extractor does not read how IMS and DB2 jobs name their programs | Five programs that look uncalled are run by jobs (see the unknown bucket). | high | `app/app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl:25`, `app/app-transaction-type-db2/jcl/MNTTRDB2.jcl:30` |
| The catalog listing is not telemetry | It shows generation counts of five GDGs from a 2022 listing (DALYREJS up to generation 26, SYSTRAN 22, TRANREPT 14). That says the posting, interest and report jobs ran in that environment. It says nothing about production or the last 12 months. | medium | `app/catlg/LISTCAT.txt:696`, `app/catlg/LISTCAT.txt:1112`, `app/catlg/LISTCAT.txt:1541` |

## Bucket 1. Unreachable

No static path from any entry point, and no reachable code makes a computed call that could name it.

| Unit | What it is | Reason | Confidence | Evidence |
|---|---|---|---|---|
| `cpy:UNUSED1Y` | Copybook, 7 lines | No program includes it. It holds a user shaped record with a password field and a 2022 version stamp. A copybook cannot be the target of a computed CALL. Safe to propose for deletion, after the client agrees. | high | `app/cpy/UNUSED1Y.cpy:1` |

## Bucket 2. Reachable but dormant

Empty. See the warning above. Propose instrumentation for any program the client cannot name a caller for, starting with the six programs in the unknown bucket.

## Bucket 3. Unknown

Not reached by a static edge. Do not delete any of these. Five of the six programs are run by IMS or DB2 jobs, which the extractor cannot see, so they very likely run. I kept them here because the skill does not let me move an item out of the extractor's bucket. Each confidence is my confidence that the item is dead, and it is low for all of them.

| Unit | What it is | Reason | Confidence | Evidence |
|---|---|---|---|---|
| `CBPAUP0C` | IMS batch purge of expired authorizations | Run as an IMS BMP by job CBPAUP0J. The CA-7 listing chains CBPAUP0J ahead of POSTTRAN. Very likely live. | low | `app/app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl:25`, `app/scheduler/CardDemo.ca7:70` |
| `CBTRN01C` | Batch, 415 lines, six files | No JCL, wrapper or scheduler entry runs it. Its six DDs map to nothing. The computed calls cannot reach it because they are CICS XCTLs to programs in the CSD, and it is not defined there, but the bucket stays open. The only program with no sign of a caller. | low | `app/cbl/CBTRN01C.cbl:29`, `app/csd/CARDDEMO.CSD:173` |
| `COBTUPDT` | DB2 batch maintenance of the transaction type table | Run by job MNTTRDB2 through `RUN PROGRAM`, which the extractor does not read. Named in README. The weekly Control-M folder runs MNTTRDB2. | low | `app/app-transaction-type-db2/jcl/MNTTRDB2.jcl:30`, `app/scheduler/CardDemo.controlm:27` |
| `DBUNLDGS` | IMS unload to GSAM | Run by job UNLDGSAM under DFSRRC00. No scheduler names UNLDGSAM. | low | `app/app-authorization-ims-db2-mq/jcl/UNLDGSAM.JCL:27` |
| `PAUDBLOD` | IMS load of the authorization database | Run as a BMP by job LOADPADB. No scheduler names LOADPADB. | low | `app/app-authorization-ims-db2-mq/jcl/LOADPADB.JCL:27` |
| `PAUDBUNL` | IMS unload to two flat files | Run by job UNLDPADB under DFSRRC00. No scheduler names UNLDPADB. | low | `app/app-authorization-ims-db2-mq/jcl/UNLDPADB.JCL:39` |
| `cpy:IMSFUNCS`, `cpy:PADFLPCB`, `cpy:PASFLPCB`, `cpy:PAUTBPCB` | IMS PCB and function copybooks | Included only by DBUNLDGS, PAUDBLOD and PAUDBUNL. They follow those programs. | low | `app/app-authorization-ims-db2-mq/cbl/DBUNLDGS.CBL:136`, `app/app-authorization-ims-db2-mq/cbl/PAUDBLOD.CBL:161`, `app/app-authorization-ims-db2-mq/cbl/PAUDBUNL.CBL:150` |
| `proc:TRANREPT` | Proc that holds the report steps | Named only in JCL text inside CORPT00C, which writes it to the JOBS TD queue for submission. It has no edge, so it is unknown and not unreachable. It is the proc the online report runs. The batch job TRANREPT does not call it and carries a copy of the same steps. Must-not-break, so never delete. | low | `app/cbl/CORPT00C.cbl:94`, `app/cbl/CORPT00C.cbl:518`, `app/csd/CARDDEMO.CSD:499`, `app/proc/TRANREPT.prc:57` |

The extractor gives 28 reachable computed calls as the reason for most of the unknown bucket. All 28 are XCTL to a CICS program, and I bounded them in `modernization-assessment/02-coupling.md`. That does not change the bucket.

## Jobs nobody in the tree schedules

The extractor lists 35 jobs no parsed scheduler names. The CA-7 listing names eight of them, so they are scheduled, not orphaned.

| Job | Where the CA-7 listing names it | Confidence | Evidence |
|---|---|---|---|
| CBPAUP0J | Triggered by CLOSEFIL, and it triggers POSTTRAN | high | `app/scheduler/CardDemo.ca7:43`, `app/scheduler/CardDemo.ca7:70` |
| READACCT, READCARD, READCUST, READXREF | A chain after CLOSEFIL | high | `app/scheduler/CardDemo.ca7:340`, `app/scheduler/CardDemo.ca7:367`, `app/scheduler/CardDemo.ca7:394`, `app/scheduler/CardDemo.ca7:421` |
| CREASTMT, TXT2PDF1 | A chain after CLOSEFIL | high | `app/scheduler/CardDemo.ca7:468`, `app/scheduler/CardDemo.ca7:495` |
| PRTCATBL | Triggered by the second CLOSEFIL block | high | `app/scheduler/CardDemo.ca7:537` |

The remaining 27 are named in no scheduler, wrapper or listing I have. Ask whether they still run: CBADMCDJ, CBEXPORT, CBIMPORT, CBLDBMS, CICCMP, CIDBCMP, CNJBATMP, CREADB2, DALYREJS, DBPAUTP0, DEFCUST, DEFGDGB, DEFGDGD, ESDSRRDS, FTPJCLS, IMSMQCMP, INTRDRJ1, INTRDRJ2, LISTFILS, LOADPADB, RACFCMDS, REPRTEST, REPTFILE, SORTTEST, TRANREPT, UNLDGSAM and UNLDPADB. Several are one-off setup jobs that would run once, such as the GDG definitions (`app/jcl/DEFGDGB.jcl:25`), the compile jobs, and the sample tests. TRANREPT is the one that matters. It is a must-not-break item and nothing schedules it. It runs on demand, from the menu (`app/cbl/CORPT00C.cbl:94`) or by hand.

## What to instrument first

1. The six programs above: a one-line counter or a job log search for the last 12 months (job logs and SMF records show which programs ran).
2. CBTRN01C, because nothing names it.
3. The 27 unscheduled jobs, by job log.
4. CORPT00C, to see whether the monthly, yearly and custom report paths are all used, since the port has to cover all three (`app/cbl/CORPT00C.cbl:230`, `app/cbl/CORPT00C.cbl:250`).
