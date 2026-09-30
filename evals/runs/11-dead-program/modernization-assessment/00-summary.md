# 00 Summary

Assessment of `.` (the work folder). Extractor output is in `graph.json`. Every claim below carries a `path:line` citation or the word inference.

## Scoping answers

All three answers came in as flags. This was a non-interactive run, and no default was needed.

| Question | Answer | Evidence |
|---|---|---|
| Target state | refactor | `modernization-assessment/waves.json:2` |
| What must not break | "the nightly batch cycle" | inference |
| Runtime telemetry | none. Every dead-code claim is provisional. | `modernization-assessment/dead-code.json:2` |

Linking "the nightly batch cycle" to MAINJOB is inference. The tree has no scheduler artifact and nothing marks MAINJOB as nightly (`app/jcl/MAINJOB.jcl:1`).

## What the tree is

One JCL job with one step, three COBOL programs and one copybook. The live part is a chain: MAINJOB runs PGMMAIN, which calls PGMLIVE (`app/jcl/MAINJOB.jcl:2`, `app/cbl/PGMMAIN.cbl:4`). PGMDEAD and the copybook `cpy:UNUSED` are not reachable from any entry point (`modernization-assessment/graph.json:159`). The extractor found no dataset, no computed call, no cycle and no scheduler (`modernization-assessment/graph.json:171`, `modernization-assessment/graph.json:180`, `modernization-assessment/graph.json:197`).

## Wave count

**One wave.** The whole live tree, `job:MAINJOB`, `PGMMAIN` and `PGMLIVE`, moves together. There is no boundary inside it to cut. The wave and the reasoning are in `03-waves.md`. Nothing is ported for PGMDEAD or `cpy:UNUSED`. They are proposed for deletion, provisionally.

## Largest risk

**The tree cannot define what "correct" is for the nightly cycle.** The job has no DD statement, and neither live program opens a file (`app/jcl/MAINJOB.jcl:2`, `app/cbl/PGMMAIN.cbl:4`). A port could pass every check the tree allows and still break the cycle the client named, through an output, a downstream job or a schedule that lives outside the tree. The port itself scores 1 of 5 on difficulty for all three units. The exposure is the oracle, and the scores show it (`modernization-assessment/risks.json:13`).

The second risk is deleting PGMDEAD on static evidence alone. It is a batch main program with no telemetry and no scheduler read (`app/cbl/PGMDEAD.cbl:2`).

## Open Questions for the client's engineers

1. Is MAINJOB the nightly batch cycle, or one job of several? Please supply the scheduler export (Control-M, CA-7, TWS, Autosys or a wrapper). No scheduler was parsed, so the order jobs run in is unknown (`modernization-assessment/graph.json:197`).
2. Are PGMMAIN and PGMLIVE the production source, or stubs? PGMLIVE only returns and PGMMAIN only calls it (`app/cbl/PGMLIVE.cbl:4`, `app/cbl/PGMMAIN.cbl:4`). What files, DB2 tables or reports does the real cycle touch? MAINJOB has no DD statement (`app/jcl/MAINJOB.jcl:2`).
3. Does any job, scheduler entry or internal-reader submit start PGMDEAD from outside this tree? Please search your other JCL libraries for `EXEC PGM=PGMDEAD` (`app/cbl/PGMDEAD.cbl:2`).
4. Does any program outside this tree include the copybook UNUSED? It is the only include-able unit with no includer (`app/cpy/UNUSED.cpy:1`).
5. Can you supply job logs or SMF records for the last 12 months? That turns the provisional dead-code claims into evidence (`modernization-assessment/dead-code.json:2`).
6. Can you supply source-control history, or dataset last-referenced dates? The extractor found no git history, so every last-modified date is unknown and the dormant rule could not run (`modernization-assessment/graph.json:7`, `modernization-assessment/graph.json:38`).
7. What does the nightly cycle produce, and where are archived generations of it? What return code and completion condition does operations treat as success? This is the oracle for `06-test-strategy.md`.
8. Is a parallel run of the legacy and refactored jobs possible for several nights? It is the strongest oracle (`modernization-assessment/06-test-strategy.md:17`).

## Files the extractor did not parse

None. The unparsed list is empty (`modernization-assessment/graph.json:151`).

## Extractor limits that touch this system

| Limit | Why it touches this system | Evidence |
|---|---|---|
| Only Control-M XML and shell wrappers that name JCL files are read as schedulers | A scheduler in any other product would go unread. The extractor found none. | `modernization-assessment/graph.json:18` |
| Nested PROC calls, INCLUDE members and jobs submitted through the internal reader are not followed | A job outside the tree could start PGMDEAD this way without leaving an edge. | `modernization-assessment/graph.json:16` |
| `IF/THEN/ELSE` and `COND=` in JCL are not modeled | MAINJOB uses neither. Jobs outside the tree might. | `modernization-assessment/graph.json:15` |
| No git history, so `last_modified` is null on every node | The five-year dormancy rule could not run. An empty dormant list means no data. | `modernization-assessment/graph.json:7` |

The other limits do not touch this system: it has no variable call, no `COPY REPLACING`, no utility step, no CICS verb and no free-format source.

## Where the artifacts are

| File | Content |
|---|---|
| `01-inventory.md`, `02a-edge-tables.md`, `05a-dead-code-candidates.md` | Generated fact tables |
| `02-coupling.md` | The coupling argument |
| `03-waves.md`, `waves.json` | The wave plan |
| `04-estimate.md` | Range and assumptions |
| `05-dead-code.md`, `dead-code.json` | Three buckets |
| `06-test-strategy.md` | Oracle and exit bar |
| `risks.json` | Scores on two axes |
