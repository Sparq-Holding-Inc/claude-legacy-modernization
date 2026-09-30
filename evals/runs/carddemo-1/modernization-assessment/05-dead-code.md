# 05 Dead code

Telemetry is `none`. Every claim in this file is provisional. Nothing here is a proposal to delete anything except the one copybook in the first table, and even that waits for the client to confirm. The candidate lists are in `modernization-assessment/05a-dead-code-candidates.md` and the JSON is `modernization-assessment/dead-code.json`.

## The three buckets

| Bucket | Unit | Confidence | Reason | Evidence |
|---|---|---|---|---|
| Unreachable | cpy:UNUSED1Y | high | No program includes it and no unparsed file names it. Its fields are called UNUSED-ID, UNUSED-PWD and so on. With no telemetry it is provisional, and a program outside this tree could still copy it. Propose it for deletion after confirmation | `app/cpy/UNUSED1Y.cpy:1` |
| Dormant | none | not measurable | See below. An empty list here is not evidence that nothing is dormant | analysis, `dormant_years` and `git_dates` |
| Unknown | CBTRN01C | low | No JCL step, scheduler entry or wrapper runs it. Its six DDs map to no JCL. Computed calls do not reach it. It stays unknown | `app/cbl/CBTRN01C.cbl:29` |
| Unknown | proc:TRANREPT | medium | Named only in JCL text inside CORPT00C, which submits it through the JOBS queue. Treat it as live, because it is the online route to a must-not-break report | `app/cbl/CORPT00C.cbl:94`, `app/cbl/CORPT00C.cbl:517` |

## Unreachable: one copybook

cpy:UNUSED1Y is seven lines, dated 2022-09-01, and the extractor found no COPY of it (`analysis.dead_code_candidates`). A search of the tree found no other mention of it. The copybook mirrors the sign-on record layout: an 8-character id, two names, an 8-character password and a type (`app/cpy/UNUSED1Y.cpy:2`, `app/cpy/UNUSED1Y.cpy:5`, `app/cpy/CSUSR01Y.cpy:21`). That looks like an earlier copy of the user record. It is the only unreachable unit in the tree.

## Dormant: not measurable here

The rule is reachable, not modified for five years, and no telemetry. The extractor ran with git dates on and an as-of date of 2026-09-30 (`analysis.as_of`, `meta.git_dates`), so the cut-off is 2021-09-30. The repository history starts in August 2022, about four years before the as-of date, so no file can be older than the cut-off. The empty dormant list therefore means the test could not fire, not that the code is active. The last-modified date on many files is 2022-09-01, which is the import into this repository (`modernization-assessment/01-inventory.md`), so it says nothing about use.

The 2022 files are the online programs and most JCL, and they are the units a client engineer should check first with run history. The list of programs whose last change is 2022-09-01 is in `modernization-assessment/01-inventory.md`.

## Unknown: CBTRN01C

CBTRN01C reads the daily transaction file, the cross reference, the card, customer, account and transaction files, and writes nothing (`app/cbl/CBTRN01C.cbl:29`, `app/cbl/CBTRN01C.cbl:58`). No job in the tree runs it, and the JCL that would map its six DDs is missing.

The extractor put it in unknown because 28 computed calls in reachable code could target it. I read each of them (`modernization-assessment/02-coupling.md`). Every target name comes from the two menu tables, `app/cpy/COMEN02Y.cpy:28` and `app/cpy/COADM02Y.cpy:29`, or from literal MOVEs, and all of those are online programs. So the computed calls do not reach a batch program, and I bound them out. It still cannot move to unreachable. A job outside the tree, or a run by hand, could start it, and the validator does not allow the move. Ask the client whether it is a pre-posting check that someone runs before POSTTRAN. If yes, it belongs with the posting cycle in wave 5. Until then it stays unplaced in `modernization-assessment/waves.json`.

## Unknown: proc:TRANREPT

The proc is named in a JCL literal that CORPT00C writes to the JOBS queue (`app/cbl/CORPT00C.cbl:94`, `app/cbl/CORPT00C.cbl:517`). The queue exists (`app/csd/CARDDEMO.CSD:499`). The extractor cannot draw an edge from JCL text inside a COBOL literal, so the proc looks unreferenced. It is the online route to the transaction report, so I placed it in wave 5 and left it in the unknown bucket in the JSON. The bucket only records how sure the extractor was.

## Jobs no parsed scheduler names

35 jobs are named by no parsed Control-M file or shell wrapper (`analysis.unscheduled_jobs`). Each is an entry point, so none of them can appear in a bucket. The extractor warns that its list is overstated because the CA-7 listing is not parsed (`modernization-assessment/05a-dead-code-candidates.md`). I read the CA-7 file by hand. It names eight of the 35: CBPAUP0J, CREASTMT, PRTCATBL, READACCT, READCARD, READCUST, READXREF and TXT2PDF1 (`app/scheduler/CardDemo.ca7:51`, `app/scheduler/CardDemo.ca7:476`, `app/scheduler/CardDemo.ca7:545`, `app/scheduler/CardDemo.ca7:348`, `app/scheduler/CardDemo.ca7:375`, `app/scheduler/CardDemo.ca7:402`, `app/scheduler/CardDemo.ca7:429`, `app/scheduler/CardDemo.ca7:503`). That is `inference`, from a file the extractor did not read.

The other 27 fall into groups. Ask the client whether each still runs.

| Group | Jobs | What it probably is | Evidence |
|---|---|---|---|
| Report | TRANREPT | The must-not-break report. No scheduler names it, so it is run by hand or through the online screen | `app/jcl/TRANREPT.jcl:1` |
| Install and definition | CBADMCDJ, CREADB2, DEFCUST, DEFGDGB, DEFGDGD, DALYREJS, REPTFILE, ESDSRRDS, DBPAUTP0, LOADPADB, RACFCMDS | One-time setup. DEFGDGB and DALYREJS define generation groups the posting cycle writes, so they are prerequisites, not dead | `app/jcl/DEFGDGB.jcl:24`, `app/jcl/DALYREJS.jcl:24` |
| Build | CBLDBMS, CICCMP, CIDBCMP, CNJBATMP, IMSMQCMP | Legacy compile jobs under samples | `samples/jcl/BMSCMP.jcl:1` |
| Samples | REPRTEST, SORTTEST, LISTFILS | Test jobs under samples | `samples/jcl/SORTTEST.jcl:1` |
| Demos | FTPJCLS, INTRDRJ1, INTRDRJ2 | An FTP demo with credentials in the JCL and an internal reader demo | `app/jcl/FTPJCL.JCL:33`, `app/jcl/INTRDRJ1.JCL:18` |
| Export and IMS unload | CBEXPORT, CBIMPORT, UNLDGSAM, UNLDPADB | Data movement for migration or backup. Who runs them is unknown | `app/jcl/CBEXPORT.jcl:1`, `app/app-authorization-ims-db2-mq/jcl/UNLDPADB.JCL:1` |

None of these is proposed for deletion. The demos and samples are candidates to instrument, and the build jobs go with the legacy build (`modernization-assessment/risks.json`, `do_not_port`).
