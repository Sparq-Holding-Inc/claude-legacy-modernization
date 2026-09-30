# 00 Summary

Scope: `.` (the work folder). Tree read by the extractor: 2 COBOL programs, 1 copybook, 2 JCL jobs, 8 nodes and 9 edges in `graph.json`.

## Scoping answers

All three came as flags in this non-interactive run. No defaults were applied.

| Question | Answer | Source |
|---|---|---|
| Target state | refactor | `--target refactor` |
| What must not break | the nightly batch cycle | `--must-not-break` |
| Runtime telemetry | none | `--telemetry none` |

Consequences. With telemetry none, every dead-code claim is provisional (`05-dead-code.md`). The nightly batch cycle is not named anywhere in the tree, and no scheduler artifact exists, so I could not map it to units. I assumed both jobs belong to it (inference).

## Result

- **Wave count: 1.** The system is two single step jobs, two programs, one copybook and one dataset. It has no cycle, no god module and no computed call. See `03-waves.md` for what I would cut if it were ten times larger.
- **Estimate: 9 to 20 person-days** for wave 1, low confidence, with four stated assumptions (`04-estimate.md`).
- **Dead code: nothing proposed.** All three buckets are empty, and the dormant bucket is empty only because there are no file dates.
- **Test strategy:** a byte compare of the dataset, with the oracle still to be obtained from the client (`06-test-strategy.md`).

## Largest risk

The record contract on SPARQ.TEST.MASTER between PGMW and PGMR. Both use the same layout copybook, so the extractor rates the edge high confidence (`app/cbl/PGMW.cbl:11`, `app/cbl/PGMR.cbl:11`). But the copybook defines a 15 byte record with a packed decimal amount (`app/cpy/LAYOUTX.cpy:3`), while the only physical format in the tree is `LRECL=80` on the writer DD (`app/jcl/WRITEJOB.jcl:4`). The reader DD has no DCB (`app/jcl/READJOB.jcl:3`). A port that changes the byte encoding, the padding or the record length would break the reader without an abend, and nobody would see it until a report is wrong.

## Findings

| Finding | Confidence | Evidence |
|---|---|---|
| One contract edge, PGMW to PGMR, through SPARQ.TEST.MASTER, high confidence | high | `app/cbl/PGMW.cbl:13`, `app/cbl/PGMR.cbl:13`, `app/cpy/LAYOUTX.cpy:1` |
| Layout is 15 bytes; the writer DD declares FB LRECL=80 | medium | `app/cpy/LAYOUTX.cpy:3`, `app/jcl/WRITEJOB.jcl:4` |
| Writer DD is DISP=(NEW,CATLG,DELETE), so a rerun against an existing dataset fails | medium | `app/jcl/WRITEJOB.jcl:3` |
| PGMW writes LAYOUT-REC with no MOVE | medium | `app/cbl/PGMW.cbl:14` |
| PGMR reads a single record and stops | medium | `app/cbl/PGMR.cbl:14` |
| No scheduler was parsed, so job order is unknown | high | inference |
| No SCC, no god module, no computed call | high | inference |

## Open Questions for the client's engineers

1. Which jobs make up the nightly batch cycle, and where do WRITEJOB and READJOB sit in it? No scheduler export was in the tree. The extractor warned that the order across jobs is unknown.
2. What are the real RECFM and LRECL of SPARQ.TEST.MASTER on disk? The copybook implies 15 bytes (`app/cpy/LAYOUTX.cpy:3`). The writer DD says LRECL=80 (`app/jcl/WRITEJOB.jcl:4`). Which one wins at run time, and does any consumer depend on the padding?
3. Who else reads SPARQ.TEST.MASTER, inside or outside this tree (partner extracts, sort steps, other jobs)? The tree shows one reader (`app/jcl/READJOB.jcl:3`).
4. What does PGMW mean to write when no field is ever set (`app/cbl/PGMW.cbl:14`), and why does PGMR read only one record (`app/cbl/PGMR.cbl:14`)? Are these stubs or real behavior? What is the business function of the pair?
5. How does the writer run more than once, given `DISP=(NEW,CATLG,DELETE)` (`app/jcl/WRITEJOB.jcl:3`)? Is there a delete or rename step, or a generation scheme, outside the tree?
6. Is SPARQ.TEST.MASTER a test dataset name that the real cycle replaces at run time, or is that the production name?
7. Can the old jobs run beside the new ones for a parallel run, and are archived copies of the dataset kept? This decides the oracle (`06-test-strategy.md`).
8. Do the source members have version control or file dates the client can share? The tree is not under git, so no dormancy check could run. Which programs ran in the last 12 months?
9. What runs at month end and year end in the cycle? None of it is visible here.

## Not parsed

Nothing. The extractor reported an empty `unparsed` list. The tree holds no free format COBOL, no PROC, no CICS or BMS definitions, and no scheduler or shell wrapper.

## Extractor limits that touch this system

| Limit | Touches this system | Evidence |
|---|---|---|
| Only Control-M XML and shell wrappers that name JCL files are read as schedulers | Yes. No scheduler was found, so temporal edges are zero and every JCL job is an entry point. | `app/jcl/READJOB.jcl:1`, `app/jcl/WRITEJOB.jcl:1` |
| Nested PROC calls, INCLUDE members and jobs submitted through the internal reader are not followed | Possibly. Anything that submits these jobs, or another consumer of the dataset, would be invisible. | inference |
| IF/THEN/ELSE and COND= in JCL are not modeled | Not in these two jobs. Neither uses them. | `app/jcl/READJOB.jcl:2`, `app/jcl/WRITEJOB.jcl:2` |
| IDCAMS, SORT and in-stream control cards are not read; modes on utility steps come from DISP only | Not in these jobs. Both steps run a COBOL program directly. | `app/jcl/WRITEJOB.jcl:2` |
| A called subprogram gets no DDs from its caller's JCL step | Not applicable. There are no CALLs between programs. | inference |
| COPY REPLACING is not applied | Not applicable. The COPY has no REPLACING. | `app/cbl/PGMR.cbl:11`, `app/cbl/PGMW.cbl:11` |
| A variable call target is resolved only from VALUE clauses and literal MOVEs | Not applicable. There are no computed calls. | inference |
| EXEC CICS RETURN TRANSID, START and SEND MAP are not edges | Not applicable. No CICS in the tree. | inference |
| COBOL is read as fixed format; free format is listed as not parsed | Not applicable. Both programs parsed. | `app/cbl/PGMR.cbl:1`, `app/cbl/PGMW.cbl:1` |

Also: no last modified dates exist because the tree is not under git, so the dormancy rule could not run.
