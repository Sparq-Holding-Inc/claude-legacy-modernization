# 05 Dead code

Telemetry: none. Every claim here is provisional. Nothing below is a deletion order. The machine readable version is `modernization-assessment/dead-code.json`, and the extractor's own candidate list is `modernization-assessment/05a-dead-code-candidates.md`.

## The dormant list is empty because it could not be anything else

The extractor's dormant rule is "reachable, and not modified for 5 years as of 2026-09-30". The git history of this tree begins on 2022-08-22 and the oldest file date is 2022-09-01 (analysis `as_of` and `dormant_years`). The cutoff would be 2021-09-30, which is before the history starts, so no file can be dormant by this rule. An empty dormant list here means not measured. It does not mean nothing is dormant. The extractor printed no warning about it. The history is also the vendor's public repository history, not the client's production change history, so file dates say little about what runs.

| Finding | Confidence | Evidence |
|---|---|---|
| 99 nodes carry the date 2022-09-01, the release date, and 87 more carry 2025-08-03. Both are bulk commit dates, not change history. | high | analysis of the `last_modified` field of each node in `modernization-assessment/graph.json` |
| Dormancy needs the client's own change history or telemetry. | inference | inference |

## Unreachable

| Unit | Type | Reason | Confidence | Evidence |
|---|---|---|---|---|
| `cpy:UNUSED1Y` | copybook | No program includes it and no entry point reaches it. Propose for deletion after the client confirms nothing outside the tree copies it. | high | `app/cpy/UNUSED1Y.cpy:1` |

Nothing else is unreachable. I did not add to this bucket. An item can only move toward unknown, never away from it.

## Reachable but dormant

None computed. See above.

## Unknown

| Unit | Type | Reason | Confidence | Evidence |
|---|---|---|---|---|
| `CBTRN01C` | batch program | Not reached by any static edge and no reachable code names it. 28 computed calls could target it. Every literal moved into those targets names an online program, and the menu tables list only online programs, so a call into a batch program that needs six file DDs is unlikely. That is inference. It reads the daily transaction file and the masters and writes nothing. It looks like a check-only twin of CBTRN02C that nobody runs. | low | `app/cbl/CBTRN01C.cbl:29`, `app/cpy/COMEN02Y.cpy:28`, `app/cbl/COMEN01C.cbl:184` |
| `proc:TRANREPT` | proc | Named only in JCL text inside CORPT00C, which submits it through a transient data queue. CORPT00C is reachable (CSD transaction CR00), so the proc very likely runs each time a user asks for the report. It is unknown only because the graph has no edge. | medium | `app/cbl/CORPT00C.cbl:94`, `app/cbl/CORPT00C.cbl:517`, `app/csd/CARDDEMO.CSD:409` |

The 28 computed calls that keep this bucket open are listed in `modernization-assessment/02-coupling.md` with their bounds.

## Jobs that no parsed scheduler names

35 jobs are entry points and never appear in a bucket, because nothing shows them unreachable (analysis `unscheduled_jobs`). The warning says this list is overstated, because the CA-7 listing is not parsed. Reading the CA-7 listing by eye shows eight of them as triggered jobs.

| Job | Where else it appears | Confidence | Evidence |
|---|---|---|---|
| job:CBPAUP0J | Triggered in the CA-7 listing. | medium | `app/scheduler/CardDemo.ca7:43` |
| job:READACCT | Triggered in the CA-7 listing. | medium | `app/scheduler/CardDemo.ca7:340` |
| job:READCARD | Triggered in the CA-7 listing. | medium | `app/scheduler/CardDemo.ca7:367` |
| job:READCUST | Triggered in the CA-7 listing. | medium | `app/scheduler/CardDemo.ca7:394` |
| job:READXREF | Triggered in the CA-7 listing. | medium | `app/scheduler/CardDemo.ca7:421` |
| job:CREASTMT | Triggered in the CA-7 listing. | medium | `app/scheduler/CardDemo.ca7:468` |
| job:TXT2PDF1 | Triggered in the CA-7 listing. | medium | `app/scheduler/CardDemo.ca7:495` |
| job:PRTCATBL | Triggered in the CA-7 listing. | medium | `app/scheduler/CardDemo.ca7:537` |

The other 27 need an answer from the client:

| Group | Jobs | Reading | Confidence | Evidence |
|---|---|---|---|---|
| Build and compile | CBLDBMS, CICCMP, CIDBCMP, CNJBATMP, IMSMQCMP | Build jobs that live in `samples/jcl`. They run at build time, not in production. | medium | `samples/jcl/BMSCMP.jcl:1`, `samples/jcl/IMSMQCMP.jcl:1` |
| Tests and demonstrations | REPRTEST, SORTTEST, LISTFILS, INTRDRJ1, INTRDRJ2, ESDSRRDS, DEFCUST, FTPJCLS | No program reads what they produce. | medium | `samples/jcl/SORTTEST.jcl:1`, `app/jcl/INTRDRJ1.JCL:4` |
| One-off setup | CBADMCDJ, CREADB2, DEFGDGB, DEFGDGD, DALYREJS, REPTFILE, RACFCMDS | Define resources once. Do they run at each environment build? | medium | `app/jcl/DEFGDGB.jcl:19`, `app/jcl/CBADMCDJ.jcl:20` |
| Production candidates | CBEXPORT, CBIMPORT, TRANREPT, DBPAUTP0, LOADPADB, UNLDGSAM, UNLDPADB | Look like real batch. Who runs them and when? TRANREPT is also started by CORPT00C. | low | `app/jcl/CBEXPORT.jcl:1`, `app/jcl/CBIMPORT.jcl:1`, `app/jcl/TRANREPT.jcl:1` |

## What this means for the estimate

If telemetry shows the build, test and demonstration jobs never run in production, the retirement list is about 19 jobs and procs (`modernization-assessment/risks.json` do_not_port). The estimate in `modernization-assessment/04-estimate.md` assumes they are retired, not ported.
