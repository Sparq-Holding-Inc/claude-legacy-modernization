# 00 Summary

Assessment of the tree in `.` (two JCL jobs and one Control-M file). Generated facts are in `graph.json` and the `01`, `02a`, `03a` and `05a` files. The argument is in `02` to `06`.

## Scoping answers

| Question | Answer | Where it came from |
|---|---|---|
| Target state | refactor | flag `--target refactor` |
| What must not break | "the nightly batch cycle" | flag `--must-not-break` |
| Runtime telemetry | none | flag `--telemetry none` |

All three came as flags: **no defaults applied**.

The must-not-break item maps to the Control-M folder NIGHTLY and its jobs JOBA and JOBB (`app/scheduler/nightly.xml:3`, `app/scheduler/nightly.xml:4`,
`app/scheduler/nightly.xml:8`). The match is by name only, so it is inference. The tree does not say these two jobs are the whole cycle.

Telemetry is none, so every dead-code claim is provisional, and the dormant bucket was not measured, because the tree is not a git repository (analysis: `warnings`).

## What the tree holds

| Fact | Value | Evidence |
|---|---|---|
| Programs | 0. The only program named is IEFBR14, a system utility outside the tree | `app/jcl/JOBA.jcl:2`, `app/jcl/JOBB.jcl:2` |
| JCL jobs | 2, each with one step | `app/jcl/JOBA.jcl:1`, `app/jcl/JOBB.jcl:1` |
| Scheduler | Control-M, one folder, two jobs | `app/scheduler/nightly.xml:3` |
| Datasets | 0. Neither job has a DD card | analysis: `data_hubs` is empty |
| Edges | 7: 4 call, 2 include, 1 temporal | analysis: `edge_counts` |
| Not parsed | Nothing | analysis: `unparsed` is empty |

## Result

- **Wave count: 1.** One wave, the nightly batch cycle (JOBA then JOBB), batch-utility family, 4 units, medium blast radius, medium confidence (`modernization-assessment/waves.json:5`). No deviation from the extractor's seed. See `03-waves.md`.
- **Estimate:** 9 to 22 person-days (inference), driven by three assumptions, the first being that the production members really are one IEFBR14 step each. See `04-estimate.md`.
- **Dead code:** the register is empty in all three buckets. Not proof of no dead code: nothing could be measured. See `05-dead-code.md`.
- **Test strategy:** the tree has no data, so the oracle must come from scheduler history and job logs. Parallel run is the first ask. See `06-test-strategy.md`.

## The single largest risk

The nightly cycle exists only as Control-M conditions, and both ends of it point outside the tree. JOBA waits for EXTERNAL-FEED, which nothing in the tree
sets (`app/scheduler/nightly.xml:5`). JOBB deletes the JOBA-DONE condition it consumed (`app/scheduler/nightly.xml:10`) and sets JOBB-DONE for a consumer we cannot see
(`app/scheduler/nightly.xml:11`). Both jobs run only IEFBR14, which does nothing (`app/jcl/JOBA.jcl:2`, `app/jcl/JOBB.jcl:2`). A refactor that re-creates the jobs but not the conditions would
pass every job-level test and still break the cycle: it could start at the wrong time, run out of order, or never tell the downstream consumer it finished. Nobody would see it until the morning (inference).

## Open Questions for the client's engineers

| # | Question | Why it matters | Evidence |
|---|---|---|---|
| 1 | What sets the condition EXTERNAL-FEED? A file watcher, another folder, another scheduler, or an operator? | It is the real start of the cycle and it is outside the tree we were given. | `app/scheduler/nightly.xml:5` |
| 2 | Who or what waits for JOBB-DONE, and what does it do with it? | It is the only output of the cycle. If it is unread today, tell us, so we can call it dead. | `app/scheduler/nightly.xml:11` |
| 3 | Is IEFBR14 the real content of JOBA and JOBB, or a stand-in for members not supplied? | If real programs exist, the estimate, the risk scores and the wave plan all change. | `app/jcl/JOBA.jcl:2`, `app/jcl/JOBB.jcl:2` |
| 4 | Is the folder NIGHTLY the whole "nightly batch cycle"? Are there other folders, other jobs, or another scheduler (for example CA-7) that we were not given? | The extractor reads only Control-M XML and shell wrappers as schedulers (`meta.limits` in `modernization-assessment/graph.json`). Anything else is invisible to it. | `app/scheduler/nightly.xml:3` |
| 5 | Why does JOBB delete JOBA-DONE, and what do operators do to rerun or restart the pair? Are conditions ever added by hand? | The rerun rule lives in the scheduler, and a port has to reproduce it. | `app/scheduler/nightly.xml:10` |
| 6 | Do month-end, quarter-end or year-end nights run a different folder, calendar or job set? Which Control-M calendars apply? | No calendar is in the tree, and close nights are where a port fails most often. | inference |
| 7 | Can you export 12 or more months of Control-M run history and JES job output for JOBA and JOBB? Do both still run every night? | Telemetry is none, so we cannot tell live from dead. The same export is the test oracle. | inference |
| 8 | Are the ODATE settings on these conditions all "ODAT" in production, and does the cycle ever cross midnight? | Conditions are dated by order date. The extractor does not model it. | `app/scheduler/nightly.xml:5`, `app/scheduler/nightly.xml:9` |
| 9 | What is the change history of these members? | The tree is not a git repository, so no last-modified date exists and the dormant bucket was not computed. | analysis: `warnings`, third entry |

## Limits of the extractor that touch this system

Every entry in `meta.limits` (`modernization-assessment/graph.json`) was checked. These touch this tree:

- **Only Control-M XML and shell wrappers that name JCL files are read as schedulers.** This tree has Control-M XML, so it was read. Any other scheduler is invisible (question 4).
- **IF/THEN/ELSE and COND= in JCL are not modeled.** Neither job has either (`app/jcl/JOBA.jcl:1-2`, `app/jcl/JOBB.jcl:1-2`). The production members may.
- **DCB, LRECL and RECFM are not read.** Neither job has a DD card, so nothing was missed here. Real members may have DDs.
- **Nested PROC calls and INCLUDE members are not followed.** None appear in this tree.

The remaining limits concern COBOL, copybooks, CICS and IMS. This tree has none of them (`modernization-assessment/01-inventory.md:14-17`), so they do not apply.
The extractor's warning that JOBB deletes JOBA-DONE says "that order is not an edge". That is right: the delete is a rerun rule, not an ordering edge.
The ordering edge is the set and wait pair on lines 6 and 9 (`app/scheduler/nightly.xml:6`, `app/scheduler/nightly.xml:9`).
