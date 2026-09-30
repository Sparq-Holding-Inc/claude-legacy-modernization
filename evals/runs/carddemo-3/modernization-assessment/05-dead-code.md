# 05 Dead code

Telemetry: none. The client gave no run history for the last 12 months, so every claim in this file is provisional. Nothing here is a deletion order. The extractor's candidate list is in `modernization-assessment/05a-dead-code-candidates.md`, and `modernization-assessment/dead-code.json` holds the three buckets. I did not move anything from unknown toward unreachable.

## The three buckets

| Unit | Bucket | Confidence | Reason | Evidence |
|---|---|---|---|---|
| cpy:UNUSED1Y | Unreachable | medium | No program includes it and no computed call could use it. One gap: the assembler macro library is not read. | `app/cpy/UNUSED1Y.cpy:1` |
| CBTRN01C | Unknown | low | Named by no JCL, CSD entry or program. A batch verify-only driver: it reads the daily file and looks up each card and account, and never writes. The computed calls cannot be shown to reach it, but only by inference. | `app/cbl/CBTRN01C.cbl:172` |
| proc:TRANREPT | Unknown | medium | Named only in JCL text inside CORPT00C, which submits it through the JOBS queue. A running program can start it. | `app/cbl/CORPT00C.cbl:94`, `app/csd/CARDDEMO.CSD:499` |

Dormant bucket: empty. See the next section before reading that as good news.

### Why unknown, and not unreachable, for CBTRN01C

The extractor keeps it unknown because 28 computed calls in reachable code could target it (`app/cbl/COACTUPC.cbl:956` is the first). I read those calls (`modernization-assessment/02-coupling.md`). The values come from two menu tables that name 17 programs (`app/cpy/COMEN02Y.cpy:28`, `app/cpy/COADM02Y.cpy:29`), from literal MOVEs, and from the COMMAREA program name of the caller. None names CBTRN01C, and it is a batch program with no CICS commands. I therefore expect it is unused, but the COMMAREA path cannot be proven from source, so it stays in unknown (inference). What would settle it is a search of the client's job logs and SMF records for the program name.

Its header says "Post the records from daily transaction file", yet it posts nothing. Someone may run it by hand as a pre-posting check. Ask.

## Dormant: not measured well

The extractor computed dormancy with a five year threshold as of 2026-09-30. Nothing qualifies, because the oldest last-modified date in the tree is 2022-09-01. The dates are weak input: 99 of the source files share that one date, 83 share 2025-08-03, 5 share 2025-10-16 and one has 2022-10-12. They look like bulk import commits, not real change dates (analysis: node `last_modified` values). An empty dormant list therefore means not measured. It is not evidence that everything was changed recently.

## Jobs that count as entry points and so never show in a bucket

The extractor counts every JCL job as an entry point, so no job can be dead by static analysis. It lists 35 jobs that no parsed scheduler names (analysis: `unscheduled_jobs`). The extractor cannot parse the CA-7 listing (`app/scheduler/CardDemo.ca7:18`), so that count is overstated. The listing names eight of them: CBPAUP0J, CREASTMT, PRTCATBL, READACCT, READCARD, READCUST, READXREF and TXT2PDF1 (inference: `app/scheduler/CardDemo.ca7:43`, `app/scheduler/CardDemo.ca7:340`, `app/scheduler/CardDemo.ca7:468`, `app/scheduler/CardDemo.ca7:537`). Twenty-seven remain that no scheduler artifact in the tree names.

| Jobs still unnamed by any scheduler artifact | Likely nature | Confidence | Evidence |
|---|---|---|---|
| CBADMCDJ, DEFCUST, DEFGDGB, DEFGDGD, DALYREJS, REPTFILE, ESDSRRDS | One time setup and data definition | medium | `app/jcl/CBADMCDJ.jcl:27`, `app/jcl/DEFCUST.jcl:25`, `app/jcl/DEFGDGB.jcl:24` |
| CBEXPORT, CBIMPORT | Branch migration pair, run on demand | medium | `app/cbl/CBEXPORT.cbl:65`, `app/jcl/CBIMPORT.jcl:43` |
| TRANREPT | Report, also submitted by CORPT00C, so probably live | medium | `app/jcl/TRANREPT.jcl:59` |
| CBLDBMS, CICCMP, CIDBCMP, CNJBATMP, IMSMQCMP | Build jobs | high | `samples/jcl/BMSCMP.jcl:1` |
| CREADB2, DBPAUTP0, LOADPADB, UNLDGSAM, UNLDPADB | DB2 and IMS setup, unload and load | low | `app/app-authorization-ims-db2-mq/jcl/LOADPADB.JCL:26` |
| FTPJCLS, INTRDRJ1, INTRDRJ2, LISTFILS, RACFCMDS, REPRTEST, SORTTEST | Demo and sample jobs | medium | `app/jcl/FTPJCL.JCL:33`, `app/jcl/INTRDRJ1.JCL:18` |

These are candidates for instrumentation, not deletion. The build and sample jobs are separately on the `do_not_port` list in `modernization-assessment/risks.json`, because a new pipeline replaces them, not because they are unused.

## Other places where the tree and the definitions disagree

| Finding | Why it matters for dead code | Confidence | Evidence |
|---|---|---|---|
| The CSD defines program COCRDSEC and a developer transaction CDV1 that runs it, and no source for COCRDSEC is in the tree. | Either the source is missing from the tree, or a definition points at nothing. Do not treat it as dead until the client says. | medium | `app/csd/CARDDEMO.CSD:211`, `app/csd/CARDDEMO.CSD:390` |
| The CA-7 listing triggers jobs CLOSEFIL1 and CLOSEFIL2 that have no JCL here. | Either the JCL is elsewhere or the triggers are stale. | medium | `app/scheduler/CardDemo.ca7:216` |
| Clusters AWS.CCDA.CUSTDATA.CLUSTER and AWS.CUSTDATA.CLUSTER appear only in DEFCUST. | The job builds a dataset no program reads. | medium | `app/jcl/DEFCUST.jcl:25`, `app/jcl/DEFCUST.jcl:35` |
| Datasets USRSEC.VSAM.ESDS and USRSEC.VSAM.RRDS appear only in ESDSRRDS. | Copies of the user file no program reads. | medium | `app/jcl/ESDSRRDS.jcl:63`, `app/jcl/ESDSRRDS.jcl:97` |
| CBACT04C has an empty fee routine. | A stub, not dead code by the extractor's rule, but a business rule that may have been removed or never built. | medium | `app/cbl/CBACT04C.cbl:518` |

Nothing here is deleted or ranked for deletion. It is a list of questions.
