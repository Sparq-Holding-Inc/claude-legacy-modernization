# 05 Dead code

Telemetry: **none**. There is no record of what ran in the last 12 months, so **every claim in this file is provisional**. Machine readable copy: `modernization-assessment/dead-code.json`. The extractor's candidate list is `05a-dead-code-candidates.md`.

## Result in one paragraph

One item is unreachable, none is dormant, and eleven are unknown. Nothing here is safe to delete on this evidence except the one unused copybook, and even that is a proposal. The eleven unknown items are mostly live: five of the six programs are run by jobs that name them in a PARM or in TSO input, which the extractor does not read as an edge.

## Unreachable

| Unit | Type | Reason | Confidence | Evidence |
|---|---|---|---|---|
| cpy:UNUSED1Y | copybook | No program, copybook or map includes it. It has no run time footprint to measure, so telemetry would not change the answer. | high | `app/cpy/UNUSED1Y.cpy:1` |

## Dormant

Empty. The extractor computed dormancy: the as-of date is 2026-09-30, the threshold is five years, and the oldest last-modified date in the tree is 2022-09-01, about four years. So nothing crosses the line. The dates come from git commits, and 2022-09-01 and 2025-08-03 look like import and refresh dates, not the last change to running code (inference). An empty dormant list therefore means little. Treat every unit as needing telemetry.

## Unknown

Not reached by any static edge, and computed calls could in principle target it, or the extractor cannot see how it is reached. The validator does not let me move any of these to unreachable, and I have not.

| Unit | Type | Reason | Confidence | Evidence |
|---|---|---|---|---|
| CBPAUP0C | batch | Job CBPAUP0J runs it through a BMP PARM. It very likely runs. | medium | `app/app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl:25` |
| COBTUPDT | batch | Job MNTTRDB2 runs it with TSO RUN PROGRAM and DB2 plan CARDDEMO. It very likely runs. | medium | `app/app-transaction-type-db2/jcl/MNTTRDB2.jcl:30` |
| DBUNLDGS | batch | Job UNLDGSAM names it in a DLI PARM. | medium | `app/app-authorization-ims-db2-mq/jcl/UNLDGSAM.JCL:27` |
| PAUDBLOD | batch | Job LOADPADB names it in a BMP PARM. | medium | `app/app-authorization-ims-db2-mq/jcl/LOADPADB.JCL:27` |
| PAUDBUNL | batch | Job UNLDPADB names it in a DLI PARM. | medium | `app/app-authorization-ims-db2-mq/jcl/UNLDPADB.JCL:39` |
| CBTRN01C | batch | No JCL step and no program names it, and none of its six DDs is mapped. It only verifies daily transactions and writes nothing. It is the one real retirement candidate; confirm with telemetry first. | low | `app/cbl/CBTRN01C.cbl:254` |
| cpy:IMSFUNCS | copybook | Included only by DBUNLDGS, PAUDBLOD and PAUDBUNL. Live if they are. | medium | `app/app-authorization-ims-db2-mq/cbl/DBUNLDGS.CBL:136` |
| cpy:PADFLPCB | copybook | Included only by DBUNLDGS. | medium | `app/app-authorization-ims-db2-mq/cbl/DBUNLDGS.CBL:156` |
| cpy:PASFLPCB | copybook | Included only by DBUNLDGS. | medium | `app/app-authorization-ims-db2-mq/cbl/DBUNLDGS.CBL:155` |
| cpy:PAUTBPCB | copybook | Included by DBUNLDGS, PAUDBLOD and PAUDBUNL. | medium | `app/app-authorization-ims-db2-mq/cbl/DBUNLDGS.CBL:154` |
| proc:TRANREPT | proc | Named in JCL text inside CORPT00C, which writes it to the JOBS queue. It is the online path of the transaction report, a must-not-break item. Treat as live. | high | `app/cbl/CORPT00C.cbl:94` |

What the computed calls can and cannot reach. All 28 are `EXEC CICS XCTL` sites. Three take their target from the menu tables, which list 17 online programs and no batch program (`app/cpy/COMEN02Y.cpy:28`, `app/cpy/COADM02Y.cpy:29`). Two, in COCRDLIC, are bounded by literals in that program. The other 23 take it from the COMMAREA, which source alone cannot bound. I read none of the batch programs above as a likely target, but I leave every one in unknown, as the rules require.

## Jobs no parsed scheduler runs

The extractor counts 35 JCL jobs as unscheduled and treats every one as an entry point, so none of them can appear in a dead code bucket. The list is overstated: the CA-7 listing, which it cannot parse, names eight of them. That leaves 27 to ask about.

| Group | Jobs | What to ask | Evidence |
|---|---|---|---|
| Named in CA-7 (not parsed) | CBPAUP0J, CREASTMT, PRTCATBL, READACCT, READCARD, READCUST, READXREF, TXT2PDF1 | Whether CA-7 really submits them; the listing marks jobs as maintenance only | `app/scheduler/CardDemo.ca7:43`, `app/scheduler/CardDemo.ca7:28` |
| Build and test | CBLDBMS, CICCMP, CIDBCMP, CNJBATMP, IMSMQCMP, REPRTEST, SORTTEST, LISTFILS, INTRDRJ1, INTRDRJ2 | Whether any runs in production; most are compile or test jobs | `samples/jcl/SORTTEST.jcl:31`, `app/jcl/INTRDRJ1.JCL:14` |
| One time setup | DEFGDGB, DEFGDGD, DALYREJS, REPTFILE, DEFCUST, ESDSRRDS, RACFCMDS, CBADMCDJ, CREADB2 | When each last ran; DEFCUST and ESDSRRDS work on names nothing else uses | `app/jcl/DEFCUST.jcl:25`, `app/jcl/ESDSRRDS.jcl:26` |
| IMS | DBPAUTP0, LOADPADB, UNLDGSAM, UNLDPADB | Who runs the unload and load and how often | `app/app-authorization-ims-db2-mq/jcl/UNLDPADB.JCL:39` |
| Export and import | CBEXPORT, CBIMPORT | Whether the branch migration export is in use; CBIMPORT cannot open its outputs | `app/jcl/CBIMPORT.jcl:33` |
| Other | FTPJCLS | Where it ships | `app/jcl/FTPJCL.JCL:30` |
| Report | TRANREPT | Who runs the batch report; no scheduler names it and the online path builds its own job | `app/jcl/TRANREPT.jcl:59` |

## Other artifacts that no static path reaches

| Item | Finding | Evidence |
|---|---|---|
| Alternate index on TRANSACT | TRANIDX builds it and TRANBKP deletes it each cycle, but no program in the tree reads it | `app/jcl/TRANIDX.jcl:25`, `app/jcl/TRANBKP.jcl:43` |
| USRSEC ESDS and RRDS | ESDSRRDS builds them; nothing reads them | `app/jcl/ESDSRRDS.jcl:26` |
| Program COCRDSEC | Transaction CDV1 points to it and there is no source | `app/csd/CARDDEMO.CSD:388` |

Nothing here is a proposal to delete. Each is a question for the client.
