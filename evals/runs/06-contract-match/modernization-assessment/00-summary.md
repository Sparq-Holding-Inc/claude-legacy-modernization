# 00 Summary

## Scoping answers

| Question | Answer | Source |
|---|---|---|
| Scope | `.` (the work folder) | no scope argument given |
| Target state | `refactor` | `--target refactor` |
| Must not break | "the nightly batch cycle" | `--must-not-break` |
| Runtime telemetry | `none` | `--telemetry none` |

All three answers came as flags: no defaults applied.

Telemetry is `none`, so every dead-code claim is provisional (`modernization-assessment/05-dead-code.md:1`).

## What was assessed

Two COBOL batch programs (`app/cbl/PGMR.cbl:1`, `app/cbl/PGMW.cbl:1`), one copybook
(`app/cpy/LAYOUTX.cpy:1`) and two JCL jobs (`app/jcl/READJOB.jcl:1`, `app/jcl/WRITEJOB.jcl:1`). 8 nodes,
9 edges. No CICS, no scheduler, no DB2, no data files, no tests. Nothing was left unparsed.

## Waves

**2 waves** (`modernization-assessment/waves.json:1`), no deviations from the seed:

| Wave | Units | Blast radius | Confidence | Evidence |
|---|---|---|---|---|
| 1 | PGMR, job:READJOB (reader) | low | medium | `app/jcl/READJOB.jcl:2` |
| 2 | PGMW, job:WRITEJOB (writer) | high | medium | `app/jcl/WRITEJOB.jcl:2` |

Effort range 10 to 26 person-days in total, low confidence (`modernization-assessment/04-estimate.md:1`).

## Single largest risk

The byte level contract of SPARQ.TEST.MASTER is not established, and a port can break it silently. The
writer and reader share one copybook, so the extractor rates the contract edge high (`app/cpy/LAYOUTX.cpy:1`,
`app/cbl/PGMW.cbl:11`, `app/cbl/PGMR.cbl:11`). But that copybook describes a 15 byte record
(`app/cpy/LAYOUTX.cpy:3`), the writer JCL asks for LRECL=80 (`app/jcl/WRITEJOB.jcl:4`), and PGMW writes the
record without setting any field first (`app/cbl/PGMW.cbl:14`). The extractor does not read DCB. Shared
layout is not proven equal layout. This is inference from the source. It is the unit "the nightly batch
cycle" hangs on, and the tree cannot show that cycle.

## Open Questions for the client's engineers

| # | Question | Why it matters | Evidence |
|---|---|---|---|
| 1 | Send the scheduler export (Control-M or other). Which jobs make up the nightly batch cycle, in what order, and does anything delete SPARQ.TEST.MASTER before WRITEJOB creates it? | No scheduler was parsed. Job order across jobs is unknown, and DISP=NEW fails a repeat run. | `analysis` field `warnings`, `app/jcl/WRITEJOB.jcl:3` |
| 2 | Send the catalog entry (LISTCAT) for SPARQ.TEST.MASTER. What are its real RECFM and LRECL: 15 or 80? | The copybook and the JCL disagree. The extractor does not read DCB. | `app/cpy/LAYOUTX.cpy:3`, `app/jcl/WRITEJOB.jcl:4` |
| 3 | Which other programs, jobs or partners read or write SPARQ.TEST.MASTER? Is PGMR the only reader? | The tree shows one writer and one reader. Anything outside it is invisible and doubles wave 2 if it exists. | `analysis` field `data_hubs` |
| 4 | Is SPARQ.TEST.MASTER the production dataset name? Are these the jobs that run in production? | The name says TEST. If production differs, the JCL here is not the JCL to port. | `app/jcl/READJOB.jcl:3` |
| 5 | What should PGMW write? It writes the record without any MOVE. Send an archived copy of what it produced. | The output bytes cannot be derived from the source. | `app/cbl/PGMW.cbl:14` |
| 6 | Send job logs or SMF records for READJOB and WRITEJOB for 12 months. Did they run? | Telemetry is none. Dormant was not computed and both jobs are entry points by default. | `analysis` field `warnings` |
| 7 | Send source control history or file dates for the source. | No last-modified dates exist. The tree is not a git repository. | `analysis` field `warnings` |
| 8 | Can the legacy system stay up for a parallel run of each wave? Is anyone at the client able to read the COBOL and JCL? | The oracle choice and the estimate depend on both. | inference |
| 9 | Does month-end or fiscal-close data pass through this dataset? | Boundary cases in the test plan depend on it. The tree has no date logic. | inference |

## Extractor limits that touch this system

Nothing was listed as not parsed (`modernization-assessment/graph.json:1`, `unparsed` is empty). From
`meta.limits`:

| Limit | Touches this system? | Evidence |
|---|---|---|
| DCB, LRECL and RECFM are not read | Yes. The LRECL=80 on the writer DD was not compared with the 15 byte copybook record. | `app/jcl/WRITEJOB.jcl:4`, `app/cpy/LAYOUTX.cpy:3` |
| A contract edge is high when both sides COPY the same layout | Yes. The one contract edge is high on this basis only. | `app/cbl/PGMR.cbl:11`, `app/cbl/PGMW.cbl:11` |
| Only Control-M XML and shell wrappers are read as schedulers | Yes. None exists in the tree, so no order between the jobs is known. | `analysis` field `warnings` |
| IDCAMS, SORT and other in-stream control cards are not read | Marginally. Neither job has a utility step. | `app/jcl/READJOB.jcl:2`, `app/jcl/WRITEJOB.jcl:2` |
| IF/THEN/ELSE and COND= in JCL are not modeled | Not used in these two jobs. | `app/jcl/WRITEJOB.jcl:2` |
| A called subprogram gets no DDs from its caller's step | Not used. No program calls another. | `app/cbl/PGMR.cbl:12`, `app/cbl/PGMW.cbl:12` |
| COBOL read as fixed format; COPY REPLACING not applied | Both programs are fixed format and the copy has no REPLACING. Nothing lost. | `app/cbl/PGMR.cbl:11`, `app/cbl/PGMW.cbl:11` |
| Variable call targets, embedded JCL, nested PROCs, CICS RETURN, START, SEND MAP, LINK and XCTL | Not used in this tree. | `analysis` fields `unresolved_dynamic`, `embedded_jcl` |
