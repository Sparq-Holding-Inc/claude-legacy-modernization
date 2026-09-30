# 05 Dead code

Telemetry: none. Every claim in this file is provisional. Nobody has told us which programs ran in the last 12 months, so nothing here proves a program never runs. The as-of date is 2026-09-30 and the dormancy rule is 5 years.

The extractor proposed 2 unreachable, 0 dormant and 10 unknown candidates (`05a-dead-code-candidates.md`). After reading the JCL, the online report launcher and the CA-7 listing, the register is:

| Bucket | Extractor | Register |
|---|---|---|
| Unreachable | 2 | 1 |
| Dormant | 0 | 0 |
| Unknown | 10 | 1 |
| Reachable by a route the extractor cannot read | not a bucket | 10 |

Nothing in the register is proposed for deletion on the strength of a date. The machine readable form is `dead-code.json`.

## Unreachable

| Unit | Reason | Confidence | Evidence |
|---|---|---|---|
| cpy:UNUSED1Y | No program includes it and a text search of the tree finds no other file that names it. It defines a user record with a password field that nothing uses | high | `app/cpy/UNUSED1Y.cpy:1` |

## Dormant

Empty, and only for now. The oldest last-modified date in the tree is 2022-09-01, which is 4.1 years before the as-of date, so nothing crosses the 5 year line. On 2027-09-01 that changes. 100 of the 188 dated units (15 of 44 programs) carry a 2022 date, and they start to flip into this bucket. The dates come from git commits in the copy I was given. If the client's history was squashed on import, these dates are import dates and the rule means nothing, so confirm before using it.

Dormant means old, not unused. If a live program calls a dormant program unconditionally, it very likely runs. Instrument these, do not delete them.

## Unknown

| Unit | Reason | Confidence | Evidence |
|---|---|---|---|
| CBTRN01C | No JCL step and no scheduler entry runs it. All 28 computed calls in reachable code are bounded to online programs and none names it (see the table in `02-coupling.md`), but a bounded call does not prove absence and telemetry is none. Its header says it posts the daily file and the code only looks records up. CBTRN02C is the posting program | low | `app/cbl/CBTRN01C.cbl:5`, `app/cbl/CBTRN01C.cbl:23` |

I bounded the computed calls, and I left the program in unknown, because the skill does not let a program move out of unknown on that evidence. Propose it for instrumentation first. If a full year of job logs shows no run, it is a retirement candidate.

## Reachable by a route the extractor cannot read

These ten came out of the extractor's unknown and unreachable buckets. They are not dead. Each is reached through something the extractor does not read: a PARM on a DFSRRC00 step, a TSO RUN PROGRAM card, or JCL held as text inside a COBOL program. The bucket rules give them no home, so `dead-code.json` lists them under a separate key, `reachable_by_a_route_the_extractor_cannot_read`, and the validator does not mind the extra key.

| Unit | Route | Confidence | Evidence |
|---|---|---|---|
| proc:TRANREPT | CORPT00C builds a job that runs PROC=TRANREPT and writes it to the JOBS queue for the internal reader. The extractor called this unreachable. Deleting it would break the online report, one of the three things the client named | high | `app/cbl/CORPT00C.cbl:94`, `app/cbl/CORPT00C.cbl:517`, `app/csd/CARDDEMO.CSD:499` |
| CBPAUP0C | Named in the PARM of a DFSRRC00 step in CBPAUP0J. CA-7 runs CBPAUP0J before POSTTRAN | high | `app/app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl:25`, `app/scheduler/CardDemo.ca7:43` |
| PAUDBLOD | Named in the PARM of a DFSRRC00 step in LOADPADB | high | `app/app-authorization-ims-db2-mq/jcl/LOADPADB.JCL:27` |
| PAUDBUNL | Named in the PARM of a DFSRRC00 step in UNLDPADB | high | `app/app-authorization-ims-db2-mq/jcl/UNLDPADB.JCL:39` |
| DBUNLDGS | Named in the PARM of a DFSRRC00 step in UNLDGSAM | high | `app/app-authorization-ims-db2-mq/jcl/UNLDGSAM.JCL:27` |
| COBTUPDT | Run by RUN PROGRAM(COBTUPDT) in MNTTRDB2, which Control-M runs weekly | high | `app/app-transaction-type-db2/jcl/MNTTRDB2.jcl:30`, `app/scheduler/CardDemo.controlm:27` |
| cpy:IMSFUNCS | Included by PAUDBLOD, PAUDBUNL and DBUNLDGS | high | `app/app-authorization-ims-db2-mq/cbl/DBUNLDGS.CBL:136` |
| cpy:PADFLPCB | Included by DBUNLDGS | high | `app/app-authorization-ims-db2-mq/cbl/DBUNLDGS.CBL:156` |
| cpy:PASFLPCB | Included by DBUNLDGS | high | `app/app-authorization-ims-db2-mq/cbl/DBUNLDGS.CBL:155` |
| cpy:PAUTBPCB | Included by PAUDBLOD, PAUDBUNL and DBUNLDGS | high | `app/app-authorization-ims-db2-mq/cbl/PAUDBLOD.CBL:161` |

"Reachable" here means a static route exists in the source. It does not mean the job runs. With no telemetry, whether the IMS jobs run today is an open question for the client's engineers.

## Jobs nobody schedules

The extractor lists 35 JCL jobs that no parsed scheduler names. Eight of them are named in the CA-7 listing it did not parse: CBPAUP0J, READACCT, READCARD, READCUST, READXREF, CREASTMT, TXT2PDF1 and PRTCATBL (`app/scheduler/CardDemo.ca7:43`, `app/scheduler/CardDemo.ca7:340`, `app/scheduler/CardDemo.ca7:468`, `app/scheduler/CardDemo.ca7:537`). Of the other 27, 15 are build, test, demonstration or setup jobs that the plan does not port (see `03-waves.md`). Twelve remain: five definition jobs (DALYREJS, DEFGDGB, DEFGDGD, REPTFILE and CREADB2), the four IMS jobs, CBEXPORT, CBIMPORT and TRANREPT. Whether CBEXPORT, CBIMPORT and the batch TRANREPT run in production is a question for the client's engineers. TRANREPT hard-codes a 2022 date range (`app/jcl/TRANREPT.jcl:43`).
