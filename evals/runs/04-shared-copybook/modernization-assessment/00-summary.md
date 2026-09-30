# 00 Summary

## Scoping answers

| Question | Answer | Source |
|---|---|---|
| Scope | `.` (the work folder) | argument |
| Target state | refactor | `--target refactor` |
| What must not break | "the nightly batch cycle" | `--must-not-break` |
| Runtime telemetry | none | `--telemetry none` |

All three answers came as flags, so no defaults applied.

## What is in the tree

Two batch COBOL programs and one copybook, 19 lines in all. Both programs COPY the same layout copybook (`app/cbl/PROGA.cbl:5`, `app/cbl/PROGB.cbl:5`). There is no JCL, no CSD, no scheduler export, no dataset and no call between the programs. The extractor found 2 edges, both `include` (`modernization-assessment/graph.json` field `analysis.edge_counts`).

## Wave count

**Zero.** The tree has no entry point (`analysis.entry_points` is empty, warning at `modernization-assessment/graph.json:152`). Nothing can be sequenced until the client supplies JCL, a CSD or a scheduler export. `modernization-assessment/waves.json` holds `"waves": []` and both programs in `unassigned`. No wave was invented.

## Single largest risk

The item that must not break, "the nightly batch cycle", maps to no unit in this tree. There is no job or scheduler that names it, so no unit can be tied to it. The assessment cannot say whether PROGA or PROGB belongs to the cycle, and it cannot anchor an equivalence test to the cycle. The mapping was not invented.

The one concrete coupling that will bite a port is the shared layout `app/cpy/SHARED01.cpy:3`, a packed decimal `SH-BALANCE`. Both programs include it and neither uses that field (`app/cbl/PROGA.cbl:7`, `app/cbl/PROGB.cbl:7`). A port that changes the layout, or types the field as a float, changes both programs together.

## Findings

| Finding | Confidence | Evidence |
|---|---|---|
| The tree has no entry point, so no wave, no reachability and no unreachable code can be established | high | analysis (fields `entry_points`, `wave_seed`, `dead_code_candidates`) |
| PROGA and PROGB are coupled only through the layout copybook SHARED01 | high | `app/cbl/PROGA.cbl:5`, `app/cbl/PROGB.cbl:5` |
| SHARED01 holds a packed decimal balance field that neither program reads or writes | high | `app/cpy/SHARED01.cpy:3` |
| Each program moves a literal into `SH-CUST-ID` in its own working storage, and neither produces output | medium (inference from 8-line programs) | `app/cbl/PROGA.cbl:7`, `app/cbl/PROGB.cbl:7` |
| Every dead-code claim is provisional: no telemetry and no last-modified dates | high | analysis (field `warnings`) |
| The must-not-break item maps to no unit in the tree | high | inference |

## Open Questions for the client's engineers

1. Which JCL jobs and which scheduler run PROGA and PROGB? Please supply the JCL library, the CSD if any program is online, and the scheduler export (Control-M XML or the shell wrappers). Without one of these there is no entry point and no wave.
2. What is "the nightly batch cycle"? List its jobs and the programs they run, in order, so each can be mapped to a unit. Today no unit in the tree maps to it.
3. Is this tree the whole system or an excerpt? Two 8-line programs with no file access look like stubs or a slice. If it is an excerpt, which other programs also COPY SHARED01?
4. Does any program outside this tree read or write a record laid out by SHARED01 (`app/cpy/SHARED01.cpy:1-3`)? If a dataset holds that record, the writer to reader layout is an undocumented API and it is not visible here.
5. What do the literals mean, `1` in PROGA and `2` in PROGB (`app/cbl/PROGA.cbl:7`, `app/cbl/PROGB.cbl:7`)? They look like hard coded customer ids. Are they test fixtures, or business rules?
6. Can you supply 12 months of job logs or SMF records for the two programs? With no telemetry, both programs and the copybook stay in the unknown dead-code bucket.
7. Can you supply source control history or last-modified dates? The target is not a git repository, so dormancy was not measured.
8. Is a parallel run of the nightly cycle possible, or are archived generations of its outputs available? That decides the oracle (see `modernization-assessment/06-test-strategy.md`).

## Extractor limits that touch this system

Nothing was listed as not parsed (`modernization-assessment/graph.json` field `unparsed` is empty). These entries of `meta.limits` apply here:

| Limit | Effect here | Evidence |
|---|---|---|
| COBOL is read as fixed format | Both programs read as fixed format. Free format would have been listed as not parsed, and none was | analysis (field `meta.limits`) |
| COPY REPLACING is not applied | Both COPY statements name the member only, so nothing was missed here | `app/cbl/PROGA.cbl:5` |
| DCB, LRECL and RECFM are not read | There is no JCL, so no record length could be compared with the layout | analysis (field `meta.limits`) |
| Only Control-M XML and shell wrappers that name JCL files are read as schedulers | No scheduler was found, and a scheduler in another format would not have been read | analysis (field `meta.limits`) |
| A called subprogram gets no DDs from its caller's JCL step | Not exercised, because no program calls another | analysis (field `meta.limits`) |
| A contract edge is high only when both sides COPY the same layout | No contract edge exists, because no dataset exists | analysis (field `edge_counts`) |

## Files in this assessment

`01-inventory.md`, `02a-edge-tables.md`, `02-coupling.md`, `03a-wave-seed.md`, `03-waves.md`, `04-estimate.md`, `05a-dead-code-candidates.md`, `05-dead-code.md`, `06-test-strategy.md`, plus `graph.json`, `waves.json`, `dead-code.json`, `risks.json`.
