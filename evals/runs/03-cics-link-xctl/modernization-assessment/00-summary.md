# 00 Summary

## Scoping answers

| Question | Answer | Source |
|---|---|---|
| Target state | refactor | flag `--target refactor` |
| Must not break | "the nightly batch cycle" | flag `--must-not-break` |
| Telemetry | none | flag `--telemetry none` |
| Delivery | not given. The estimate shows conventional and AI-assisted. | `--delivery` missing |

No defaults applied.

## What was assessed

Four COBOL programs, 38 lines, in `app/cbl/`. PROGA calls PROGB, PROGC and PROGD, and makes two computed calls (`app/cbl/PROGA.cbl:12`, `app/cbl/PROGA.cbl:16`, `app/cbl/PROGA.cbl:20`, `app/cbl/PROGA.cbl:23`). No JCL, CSD, scheduler, copybook or dataset was supplied (`modernization-assessment/graph.json:24`).

## Wave count: 0

The tree has no entry point, so nothing can be sequenced and no wave is invented. Every unit is in `unassigned` (`modernization-assessment/waves.json:3`). Nothing can be sequenced until the client supplies a CSD, JCL or a scheduler export.

## Largest risk

PROGA links to a program named by its commarea (`app/cbl/PROGA.cbl:15`, `app/cbl/PROGA.cbl:16`). The set of programs it can run is open, and its callers are not in the tree. Any dead-code claim, port order or equivalence test around PROGA is provisional until that set is known. `risks.json` scores PROGA high-high for this reason. Confidence: medium.

## Estimate headline

About 2 to 5 engineer-weeks conventional, 1.5 to 4 AI-assisted, for the four programs only. Planning assumptions, not benchmarks. Mostly waiting on client answers (`modernization-assessment/04-estimate.md:1`).

## Open Questions for the client's engineers

1. What is "the nightly batch cycle"? Every program here is CICS online (`app/cbl/PROGA.cbl:12`), and nothing in the tree is batch. Which, if any, of these four does the cycle touch? Please send its JCL and scheduler export.
2. Which transaction starts PROGA, and what does it put in the commarea? Please send the CSD. The computed LINK at `app/cbl/PROGA.cbl:16` can name any program on the region.
3. What literals can reach `WS-NEXT-PGM`? The extractor found one, `'PROGC'` (`app/cbl/PROGA.cbl:19`), and flagged that there may be others.
4. Is the XCTL to PROGD at line 23 ever reached, given the XCTL to PROGC just before it never returns (`app/cbl/PROGA.cbl:20`)? Is a condition missing from the source supplied?
5. Are PROGB, PROGC and PROGD really bare RETURN programs in production (`app/cbl/PROGB.cbl:4`)? These may be stubs, with the real versions deployed elsewhere.
6. Is there any other caller of these programs outside the tree, such as other CICS regions, MQ triggers or batch calling through DFHXCIS?
7. Can the client supply twelve months of CICS statistics by program and transaction? Without them, all dead-code results are provisional.
8. Is the source under version control? It is not a git repository, so no modification dates exist and dormancy was not measured.

## Limits that touch this system

From `meta.limits` in `modernization-assessment/graph.json:10`: LINK and XCTL both appear as `call` edges and control flow is not modeled (`modernization-assessment/graph.json:22`); a variable call target resolves only from VALUE clauses and literal MOVEs in the same program (`modernization-assessment/graph.json:12`); EXEC CICS RETURN TRANSID and START are not edges (`modernization-assessment/graph.json:18`), so pseudo-conversational chains would be missed. Files not parsed: none (`modernization-assessment/graph.json:178`).

## Files

`01-inventory.md`, `02-coupling.md`, `03-waves.md`, `04-estimate.md`, `05-dead-code.md`, `06-test-strategy.md`, plus `graph.json`, `waves.json`, `risks.json`, `dead-code.json`.
