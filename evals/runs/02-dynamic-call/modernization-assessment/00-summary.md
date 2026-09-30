# 00 Summary

Scope: the whole work folder (`.`). The tree holds two COBOL programs, `app/cbl/PROGA.cbl` and `app/cbl/PROGB.cbl`, 14 lines in all. It holds no JCL, no scheduler file, no CICS definition, no copybook and no dataset. Everything below rests on those two files and the extractor's `graph.json`.

## Scoping answers

| Item | Answer | Source |
|---|---|---|
| Target state | refactor | `--target refactor` flag |
| Must not break | the nightly batch cycle | `--must-not-break` flag |
| Runtime telemetry | none | `--telemetry none` flag |
| Defaults applied | no defaults applied | all three came as flags |

Because telemetry is `none`, every dead-code claim in this assessment is provisional.

## Result

| Finding | Value | Confidence | Evidence |
|---|---|---|---|
| Wave count | 1. The extractor's seed placed no unit (it found no entry point), so the one wave holds both programs by deviation. It is a wave of last resort, not a sound family. See `03-waves.md`. | low | `modernization-assessment/waves.json:5`, analysis field `wave_seed` |
| Coupling edges found | 1 edge in total, a call edge with a computed target | high | `app/cbl/PROGA.cbl:9`, analysis field `edge_counts` |
| Entry points found | 0 | high | analysis field `entry_points` |
| Dead code | 0 unreachable, 0 dormant, 2 unknown. Nothing can be proven unreachable. | low | analysis field `dead_code_candidates` |

## Single largest risk

`PROGA` calls a program whose name it reads from run-time input. The name goes into `WS-PGM-NAME` by `ACCEPT` and is never set anywhere else (`app/cbl/PROGA.cbl:5`, `app/cbl/PROGA.cbl:8`, `app/cbl/PROGA.cbl:9`). The set of programs it can start cannot be bounded from source. Any of them could be a program on the nightly batch cycle, which must not break. A refactor that resolves calls at build time would fail only for the input values that hit a name it did not know about, and nothing in the tree says what those values are. Scored high-high, confidence low (`modernization-assessment/risks.json:5`).

## What the defaults and gaps mean

- The `must-not-break` item, "the nightly batch cycle", cannot be tied to any unit. No job, scheduler entry or dataset in the tree names it. That is a finding: the behavioral-equivalence anchor has to come from the client (`06-test-strategy.md`). Evidence: inference, from analysis fields `entry_points` and `unscheduled_jobs` both being empty.
- Dormancy was not computed. The folder is not a git repository, so no unit has a last-modified date (analysis field `warnings`). An empty dormant list means not measured.

## Open Questions

For the client's engineers.

1. What feeds the `ACCEPT` at `app/cbl/PROGA.cbl:8`: SYSIN in a JCL step, the operator console, or something else? What values did it see over the last 12 months, including month-end and fiscal year-end?
2. Which JCL job, scheduler entry or CICS transaction starts `PROGA`, and is it part of the nightly batch cycle? The tree has none of these files, so no entry point was found.
3. Which programs on the production load library can the `CALL` at `app/cbl/PROGA.cbl:9` reach? Which of them are on the nightly batch cycle, and do any of them lack source?
4. `PROGB` holds only `GOBACK` (`app/cbl/PROGB.cbl:4`). Is it a real no-op, a stub, or a placeholder for a program whose source is somewhere else?
5. Is this tree a complete extract? It has no copybooks, datasets, JCL, PROCs, scheduler XML or shell wrappers. Which of those exist and were left out?
6. What does the nightly batch cycle consist of: job names, order, and the files each job reads and writes? Without that list, the temporal edges are absent from the graph.
7. Is there a version-control history, or any other record of last change, for these two files? Without one, no dormancy claim can be made.
8. Does the site run `CALL` with no `ON EXCEPTION` deliberately? Nothing in `PROGA` handles a missing target (`app/cbl/PROGA.cbl:9`), so behavior on a bad name is whatever the runtime does. That behavior has to be reproduced or changed on purpose.

## Extractor limits that touch this system

| Limit | Why it matters here | Evidence |
|---|---|---|
| A variable call target is resolved only from VALUE clauses and literal MOVEs in the same program | `WS-PGM-NAME` has no VALUE clause and no MOVE, so the call was left unresolved | `app/cbl/PROGA.cbl:5`, `app/cbl/PROGA.cbl:9` |
| Only Control-M XML and shell wrappers that name JCL files are read as schedulers | The tree has neither, so no entry point and no temporal edge exists | analysis field `warnings` |
| COBOL is read as fixed format | Both files read as fixed format. Nothing was listed as not parsed | analysis, `unparsed` is empty |
| JCL text inside a COBOL literal is noticed but makes no edge | None was found in either program | analysis field `embedded_jcl` |

Files the extractor listed as not parsed: none.
