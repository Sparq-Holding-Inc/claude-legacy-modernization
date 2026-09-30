# 05 Dead code

Telemetry: none. Every claim below is provisional. Nobody has told me which programs ran in the last 12 months, so a program that looks dead here may run once a year at close. `dead-code.json` holds the same buckets in machine form.

Three buckets, never two. The extractor computed the candidates (`05a-dead-code-candidates.md`). I added evidence and moved nothing toward unreachable.

## Unreachable

| Unit | Type | Reason | Confidence | Evidence |
|---|---|---|---|---|
| cpy:UNUSED1Y | copybook | No COPY statement in the tree names it, and a copybook cannot be a computed call target. Safe to propose for deletion once the client confirms nobody outside the tree includes it. | high | `app/cpy/UNUSED1Y.cpy:1` |

## Dormant

Empty. Read this as "not found by the rule", not as "everything is in use". The extractor read git dates (`git_dates` is true in `meta`) and no warning says dormancy was not computed. The rule is five years without a change as of 2026-09-30. The oldest last-modified date in the tree is 2022-09-01, which is 4 years and 29 days, so nothing meets it (analysis: `dormant_years` and the node `last_modified` fields). The dates come from the history of a sample repository, not from a production change log. They say little about real use. With no telemetry, dormancy is not measured here.

## Unknown

Not reached by a static edge, and a computed call in reachable code could in principle target it. Do not delete any of these on this evidence. The extractor's reason for all 11 is the same: 28 reachable computed calls. I bounded those calls (`02-coupling.md`): they resolve to online programs with a CSD definition. A batch program or a copybook cannot be reached by them. The validator does not let me move an item to unreachable on that argument, so each stays here and its reason says what I found.

| Unit | Type | What I found | Confidence | Evidence |
|---|---|---|---|---|
| CBPAUP0C | batch, IMS | Run by job CBPAUP0J through the IMS driver PARM. The CA-7 listing triggers CBPAUP0J after CLOSEFIL and CBPAUP0J triggers POSTTRAN. Likely live. | medium | `app/app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl:25`, `app/scheduler/CardDemo.ca7:43` |
| CBTRN01C | batch | No job, CSD entry or caller names it. Its DDs map to no JCL. Its header says "post the records from daily transaction file", the same text as CBTRN02C, so it may be an older version. It reads and writes nothing shared. The strongest dead-code candidate in the tree. Ask if it ever ran. | low | `app/cbl/CBTRN01C.cbl:5` |
| COBTUPDT | batch, DB2 | Not dead. The weekly job MNTTRDB2 runs it from an in-stream DSN card the extractor does not read. | medium | `app/app-transaction-type-db2/jcl/MNTTRDB2.jcl:30`, `app/scheduler/CardDemo.controlm:27` |
| DBUNLDGS | batch, IMS | Run by job UNLDGSAM through the IMS driver PARM. No scheduler in the tree names UNLDGSAM. | medium | `app/app-authorization-ims-db2-mq/jcl/UNLDGSAM.JCL:27` |
| PAUDBLOD | batch, IMS | Run by job LOADPADB through the IMS driver PARM. No scheduler in the tree names LOADPADB. | medium | `app/app-authorization-ims-db2-mq/jcl/LOADPADB.JCL:27` |
| PAUDBUNL | batch, IMS | Run by job UNLDPADB through the IMS driver PARM. No scheduler in the tree names UNLDPADB. | medium | `app/app-authorization-ims-db2-mq/jcl/UNLDPADB.JCL:39` |
| cpy:IMSFUNCS | copybook | Included only by PAUDBLOD and DBUNLDGS. Its status follows theirs. | medium | `app/app-authorization-ims-db2-mq/cbl/PAUDBLOD.CBL:142`, `app/app-authorization-ims-db2-mq/cbl/DBUNLDGS.CBL:136` |
| cpy:PADFLPCB | copybook | Included only by DBUNLDGS. | medium | `app/app-authorization-ims-db2-mq/cbl/DBUNLDGS.CBL:156` |
| cpy:PASFLPCB | copybook | Included only by DBUNLDGS. | medium | `app/app-authorization-ims-db2-mq/cbl/DBUNLDGS.CBL:155` |
| cpy:PAUTBPCB | copybook | Included by PAUDBLOD and DBUNLDGS. | medium | `app/app-authorization-ims-db2-mq/cbl/PAUDBLOD.CBL:161`, `app/app-authorization-ims-db2-mq/cbl/DBUNLDGS.CBL:154` |
| proc:TRANREPT | proc | Run at run time. CORPT00C builds a job that executes PROC=TRANREPT and writes it to the JOBS queue. Live if anyone uses the online report screen. It is the online path of a must-not-break item. | medium | `app/cbl/CORPT00C.cbl:94`, `app/cbl/CORPT00C.cbl:517` |

Of the 11, only CBTRN01C is a plausible deletion candidate. Five programs are run by jobs the extractor cannot see into, four are copybooks of those, and one is the report proc. The extractor's rule is right to keep them out of the unreachable bucket. In the plan (`03-waves.md`) all of them except CBTRN01C sit in a wave with the job that runs them.

## Jobs that no scheduler names

The extractor found 35 JCL jobs that no parsed scheduler or wrapper names. Every job counts as an entry point, so none appears in a bucket. One warning matters: the CA-7 listing `app/scheduler/CardDemo.ca7` cannot be parsed, so the list is overstated (`analysis: warnings`). I read the listing by hand.

| Group | Jobs | Evidence |
|---|---|---|
| Named in the CA-7 listing (8 of the 35) | CBPAUP0J, READACCT, READCARD, READCUST, READXREF, CREASTMT, TXT2PDF1, PRTCATBL | `app/scheduler/CardDemo.ca7:43`, `app/scheduler/CardDemo.ca7:340`, `app/scheduler/CardDemo.ca7:468`, `app/scheduler/CardDemo.ca7:537` |
| Still unnamed by anything I can read (27) | CBADMCDJ, CBEXPORT, CBIMPORT, CBLDBMS, CICCMP, CIDBCMP, CNJBATMP, CREADB2, DALYREJS, DBPAUTP0, DEFCUST, DEFGDGB, DEFGDGD, ESDSRRDS, FTPJCLS, IMSMQCMP, INTRDRJ1, INTRDRJ2, LISTFILS, LOADPADB, RACFCMDS, REPRTEST, REPTFILE, SORTTEST, TRANREPT, UNLDGSAM, UNLDPADB | analysis: `unscheduled_jobs` in `graph.json`, minus the row above |
| The one that matters: TRANREPT, the must-not-break report job | Not scheduled anywhere in the tree. The standalone job repeats a step name and carries a fixed date window, so it may not be the path that runs. The online path (CORPT00C to PROC=TRANREPT) may be the only live one. Ask. | `app/jcl/TRANREPT.jcl:37`, `app/jcl/TRANREPT.jcl:43` |
| One-time definers (likely run once at install) | DALYREJS, DEFGDGB, REPTFILE, DEFGDGD, ESDSRRDS, DEFCUST | `app/jcl/DEFGDGB.jcl:24`, `app/jcl/DALYREJS.jcl:24` |
| Build and test tooling | CBLDBMS, CICCMP, CIDBCMP, CNJBATMP, IMSMQCMP, REPRTEST, SORTTEST, LISTFILS | `samples/jcl/BMSCMP.jcl:38` |

## What changes with telemetry

With 12 months of job logs or SMF data, three things firm up. First, CBTRN01C and the four IMS programs move to unreachable or out of unknown on evidence. Second, the 27 unnamed jobs split into "runs on request" (CBEXPORT, CBIMPORT, TRANREPT) and "never runs". Third, the dormant list becomes a real measure. Until then, the plan treats a unit named by a job as live.
