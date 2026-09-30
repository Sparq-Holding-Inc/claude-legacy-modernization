# 00 Summary

Modernization assessment of the tree at `.` (two COBOL programs and one copybook). Files: `01-inventory.md`, `02-coupling.md`, `03-waves.md`, `04-estimate.md`, `05-dead-code.md`, `06-test-strategy.md`, plus `graph.json`, `waves.json`, `risks.json` and `dead-code.json`.

## Scoping answers

All three came from command flags. No defaults were used and nothing was assumed. The session was non-interactive, so nothing was asked.

| Question | Answer | Source |
|---|---|---|
| Target state | refactor | `--target refactor` |
| What must not break | "the nightly batch cycle" | `--must-not-break` |
| Runtime telemetry | none. Every dead-code claim is provisional. | `--telemetry none` |

## Result in one paragraph

The tree is small: PROGA and PROGB, 8 lines each, and the copybook SHARED01, 3 lines. Both programs include the copybook and do nothing else (`app/cbl/PROGA.cbl:5`, `app/cbl/PROGB.cbl:5`). The plan has **one wave**. Splitting the pair would put two copies of the shared layout in play, and no other coupling exists to justify a second wave. Both programs score `low-low` on port difficulty and blast radius, with low confidence, because the tree does not show how they run.

## Wave count

1. Evidence: `waves.json`, `app/cbl/PROGA.cbl:5`, `app/cbl/PROGB.cbl:5`.

## Single largest risk

The shared layout `SHARED-AREA` in `app/cpy/SHARED01.cpy:1-3` carries a packed decimal balance (`SH-BALANCE`, `COMP-3`, no `VALUE` clause) and a customer id. Neither program sets the balance, so what the legacy code leaves there depends on the compiler. A port can change that silently, and the tree holds no oracle, no dataset and no job that would expose the change. Nothing in the tree ties either program to "the nightly batch cycle", so the anchor the client named cannot be tested from here. Confidence is low.

## Open Questions for the client's engineers

1. Which JCL job or scheduler entry runs PROGA and PROGB, and are they steps in the nightly batch cycle? The tree has no JCL, scheduler, CSD or wrapper, and the extractor found no entry point (`graph.json` `analysis.entry_points` is empty).
2. Does any file, queue or call carry `SHARED-AREA` between programs? The layout looks like a record, but the tree has no `SELECT`, `FD` or `CALL` (`app/cpy/SHARED01.cpy:1`).
3. What else includes SHARED01 outside this tree? That decides the true size of wave 1.
4. What do the literals 1 and 2 moved into `SH-CUST-ID` mean: test stubs or real customer ids (`app/cbl/PROGA.cbl:7`, `app/cbl/PROGB.cbl:7`)?
5. What does the legacy compiler leave in `SH-BALANCE` when nothing sets it, and does any downstream step read it (`app/cpy/SHARED01.cpy:3`)? Which compiler options apply?
6. Can the client run a parallel run of the nightly cycle, or supply archived job output and GDG generations that cover month-end and fiscal year-end?
7. Can the client supply 12 months of run history for the two program names, so the dead-code register can leave `unknown`?
8. Is the source complete? Only three files were found, none has a last-modified date, and the tree has no git dates.

## Not parsed

Nothing was skipped: `unparsed` in `graph.json` is empty and `meta.files_seen` counts 2 COBOL files and 1 copybook. No JCL, PROC, CSD, BMS, Control-M or shell wrapper was present.

## Extractor limits that touch this system

| Limit (`graph.json` `meta.limits`) | Touches this system? |
|---|---|
| COBOL is read as fixed format. Free format files are listed as not parsed. | Both programs parsed as fixed format. Nothing was listed as unparsed. |
| COPY REPLACING is not applied. | Not used here. Both `COPY SHARED01` statements are plain. |
| A variable call target is resolved only from VALUE clauses and literal MOVEs in the same program. | No calls exist. |
| A called subprogram gets no DDs from its caller's JCL step. | No datasets exist. |
| IDCAMS, SORT and other in-stream control cards are not read. | No JCL in the tree. |
| IF/THEN/ELSE and COND= in JCL are not modeled. Step order is file order. | Yes, indirectly. The nightly cycle's real step logic is unseen. |
| Nested PROC calls, INCLUDE members and jobs submitted through the internal reader are not followed. | Yes, indirectly. A job that starts these programs this way would be invisible. |
| EXEC CICS RETURN TRANSID, START and SEND MAP are not edges. | No CICS in the tree. |
| Only Control-M XML and shell wrappers that name JCL files are read as schedulers. | Yes, indirectly. If the nightly cycle sits in another scheduler format, it would not have been read. |

## Method notes

- The `migration-risk-assessor` and `dependency-cartographer` steps were done inline, by hand. The cartographer had nothing to settle: no computed calls and no `medium` or `low` edges (`graph.json` `analysis.unresolved_dynamic` is empty).
- Facts in `01-inventory.md`, `02a-edge-tables.md` and `05a-dead-code-candidates.md` are generated. Judgment is in the other files, labeled `inference` where it is not cited.
- Estimates in `04-estimate.md` are ranges with stated assumptions and are all inference.
