# 00 Summary

## Scoping answers

| Question | Answer | Source |
|---|---|---|
| Scope | `.` (the work folder) | argument |
| Target state | `refactor` | flag `--target refactor` |
| What must not break | the nightly batch cycle | flag `--must-not-break` |
| Runtime telemetry | `none`. Every dead-code claim is provisional | flag `--telemetry none` |

All three answers came as flags in a non-interactive run, so no defaults were applied.

## What was found

A very small system: one JCL job (MAINJOB), one step that runs PGMMAIN, and two subprograms, OLDPGM and NEWPGM, that PGMMAIN calls in that order (`app/jcl/MAINJOB.jcl:2`, `app/cbl/PGMMAIN.cbl:4`, `app/cbl/PGMMAIN.cbl:5`). It is 16 lines in total. The extractor found no computed calls, no copybooks, no datasets, no strongly connected components and no god modules. Nothing was left unparsed.

| Result | Value | Confidence | Evidence |
|---|---|---|---|
| Wave count | 1. A system this size is one wave. See `03-waves.md` | medium | `app/jcl/MAINJOB.jcl:2` |
| Effort for wave 1 | 5 to 12 person-days, dominated by getting an oracle rather than by code. See `04-estimate.md` | low | inference |
| Dead code | Nothing unreachable, nothing unknown. OLDPGM is dormant (last modified 2011-03-04) but called unconditionally, so it probably runs | medium | `app/cbl/PGMMAIN.cbl:4` |

## Single largest risk

The requirement is that the nightly batch cycle must not break, and this tree cannot show that cycle. It holds one job and no scheduler export, so where MAINJOB sits, what runs before and after it, and which order must hold across jobs are all unknown. The two subprograms are one-statement `GOBACK` programs (`app/cbl/OLDPGM.cbl:4`, `app/cbl/NEWPGM.cbl:4`), so the source also gives no observable behavior to compare a port against. The wave plan and the test strategy are provisional until both gaps are closed. Confidence: low, since it rests on what is absent (inference).

A near second risk: OLDPGM looks dead by age and is not. Deleting it on the date alone would change what the nightly run does (`app/cbl/PGMMAIN.cbl:4`).

## Open Questions

For the client's engineers.

1. Is MAINJOB the nightly batch cycle, or one job in it? Please send the scheduler export. Nothing was parsed, and the extractor warned that cross-job order is unknown (`app/jcl/MAINJOB.jcl:1`).
2. Are the deployed load modules for OLDPGM and NEWPGM built from these four line sources? Both only `GOBACK` (`app/cbl/OLDPGM.cbl:4`, `app/cbl/NEWPGM.cbl:4`). If they hold logic that is not in this tree, the assessment changes a great deal.
3. Does OLDPGM still do anything? It has not changed since 2011 and PGMMAIN still calls it first (`app/cbl/PGMMAIN.cbl:4`). Can you provide 12 months of job logs or SMF records showing whether it runs?
4. Why does PGMMAIN call both OLDPGM and NEWPGM? The names suggest a replacement in progress (inference). Which one is authoritative, and does the order matter (`app/cbl/PGMMAIN.cbl:5`)?
5. The step has no DD statements, and neither program touches a file (`app/jcl/MAINJOB.jcl:2`). Is that right, or are DDs, IF/THEN/ELSE or COND= supplied by a proc, an override or a production copy of the JCL that differs from this one?
6. What does the nightly run produce that anyone reads or that leaves the building (reports, partner files, downstream feeds)? None is visible, and it is the only source of an oracle (`app/jcl/MAINJOB.jcl:2`).
7. Extractor limits that touch this system: JCL IF/THEN/ELSE and COND= are not modeled, nested PROCs and jobs submitted through the internal reader are not followed, and only Control-M XML and shell wrappers are read as schedulers. Is any other scheduler (CA-7, TWS, other) or internal reader submission in use around MAINJOB? (inference)
8. Which environment and toolchain will the refactored code run in, and who on the team can read COBOL? The estimate assumes someone can (inference).

## Files

`01-inventory.md`, `02-coupling.md`, `02a-edge-tables.md`, `03-waves.md`, `04-estimate.md`, `05-dead-code.md`, `05a-dead-code-candidates.md`, `06-test-strategy.md`, and the four JSON files `graph.json`, `waves.json`, `risks.json`, `dead-code.json`.
