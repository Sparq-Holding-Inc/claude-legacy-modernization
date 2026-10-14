# 00 Summary

## Scoping answers

| Question | Answer | Source |
|---|---|---|
| Scope | The current directory | no scope argument |
| Target state | refactor | flag |
| Must not break | "the nightly batch cycle" | flag |
| Telemetry | none | flag |
| Delivery | not given. The estimate shows conventional and AI-assisted side by side | no flag |
| Defaults applied | no defaults applied | all three scoping answers came as flags |

## What is in the tree

Two COBOL programs (`app/cbl/PGMR.cbl`, `app/cbl/PGMW.cbl`), two JCL jobs (`app/jcl/READJOB.jcl`, `app/jcl/WRITEJOB.jcl`), two copybooks, one dataset, 9 nodes and 9 edges (`modernization-assessment/01-inventory.md`). Nothing was left unparsed. There is no scheduler, no CICS definition, no proc, and no git history.

## Plan

**2 waves.** Wave 1 is the reader job (`PGMR`, `job:READJOB`). Wave 2 is the writer job (`PGMW`, `job:WRITEJOB`). Seed accepted with no deviations (`modernization-assessment/03-waves.md`, `modernization-assessment/waves.json`).

Estimate for both waves together: **12 to 24 engineer-days conventional, 10 to 20 AI-assisted** (`modernization-assessment/04-estimate.md`). The cases are close because the code is tiny and most of the time goes to decisions, the oracle and the cutover.

## Single largest risk

**The record layout of `SPARQ.TEST.MASTER` is an undocumented contract held together by convention.** The writer and reader each COPY their own copybook, with different field names (`app/cpy/LAYOUTX.cpy:2`, `app/cpy/LAYOUTY.cpy:2`). By hand reading the byte layout is the same today: `X(10)` then `S9(7)V99 COMP-3` (`app/cpy/LAYOUTX.cpy:3`, `app/cpy/LAYOUTY.cpy:3`). So the extractor's `medium` rating is a name mismatch, not a layout break. But nothing enforces the match, and the real record length lives in a JCL `LRECL=80` that neither program declares (`app/jcl/WRITEJOB.jcl:4`). On top of that, PGMW writes its record without setting any field (`app/cbl/PGMW.cbl:14`), so the source cannot say what the file should hold. A refactor that touches either copybook can break the nightly cycle with no compile or allocation error. Confidence: medium.

## Open Questions for the client's engineers

1. **Which jobs make up "the nightly batch cycle", and in what order?** No scheduler export (Control-M, CA-7, or a wrapper script) is in the tree (`analysis.warnings`). I can't map the must-not-break item to any unit. I assumed `job:READJOB` and `job:WRITEJOB` are the whole cycle. That is inference.
2. **Does anything else read `SPARQ.TEST.MASTER`?** Other jobs, a partner extract, a warehouse load? Only one reader is in the tree (`app/jcl/READJOB.jcl:3`). Any other reader may use the padding after byte 15.
3. **What does PGMW put in the record?** It writes `LAYOUT-REC` with no `MOVE` (`app/cbl/PGMW.cbl:14`). Is this the real program, a stub, or does an earlier version of the source differ? Can you supply real archived copies of the file?
4. **What holds bytes 16 to 80 of each record?** `LRECL=80` is coded on the writer only (`app/jcl/WRITEJOB.jcl:4`) and the layout is 15 bytes (`app/cpy/LAYOUTX.cpy:3`).
5. **How is the dataset cleared before each `WRITEJOB` run?** `DISP=(NEW,CATLG,DELETE)` fails if it exists (`app/jcl/WRITEJOB.jcl:3`). Is there a delete step, a GDG, or a different dataset name each night? None is in the tree.
6. **Which runs first in a night, `READJOB` or `WRITEJOB`?** If `READJOB` can run first, it reads the previous night's data or fails (`app/jcl/READJOB.jcl:3`).
7. **Is anything outside `app/` part of this system?** The extractor read only what is in the working directory (`modernization-assessment/graph.json`, `meta.files_seen`). No procs, no DB2, no CICS, no shell wrappers were present.
8. **Can you supply 12 months of job logs for these two jobs?** Without them every dead-code claim is provisional and the dormant bucket was not computed (`modernization-assessment/05-dead-code.md`).
9. **Is a parallel run possible for wave 2?** It is the strongest oracle (`modernization-assessment/06-test-strategy.md`).

## Extractor limits that touch this system

- No scheduler was parsed, so job order across jobs is unknown.
- Dormancy was not computed. The tree has no git history.
- DCB, LRECL and RECFM are not compared with the copybooks (`modernization-assessment/graph.json`, `meta.limits`). The record length finding is by hand.
- A `high` contract edge would mean shared layout, not proven equal. Ours is `medium`.

## Files

`01-inventory.md`, `02-coupling.md` (with `02a-edge-tables.md`), `03-waves.md` and `waves.json`, `04-estimate.md`, `05-dead-code.md` and `dead-code.json`, `06-test-strategy.md`, `risks.json`, `graph.json`.
