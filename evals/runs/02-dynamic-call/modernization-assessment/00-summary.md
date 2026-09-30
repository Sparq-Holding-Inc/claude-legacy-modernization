# 00 Summary

Scope: `.` (the work folder). Two COBOL files, 14 lines, no JCL, no scheduler, no copybooks, no datasets (`graph.json` `meta.files_seen`).

## Scoping answers

All three came as flags. No defaults were applied. The run was non-interactive.

| Question | Answer | Source |
|---|---|---|
| Target state | refactor | `--target refactor` |
| What must not break | the nightly batch cycle | `--must-not-break` |
| Runtime telemetry | none. Every dead-code claim is provisional. | `--telemetry none` |

## Result

- **Waves: 1.** Two programs and nothing else. There is nothing to cut, so I did not invent more. See `03-waves.md`.
- **Largest risk: the computed call at `app/cbl/PROGA.cbl:9`.** PROGA ACCEPTs a program name at run time and CALLs it (`app/cbl/PROGA.cbl:8`). The source cannot say what it calls. A port that replaces the CALL with a fixed table silently drops any program missing from the table, and the CALL has no ON EXCEPTION, so today an unknown name abends the job. Confidence: medium. The edge is a fact, its reach is unknown.
- **Nothing is proven dead.** No entry point exists in the tree, so both programs are in the unknown bucket (`05-dead-code.md`).
- **Next step:** get the JCL that runs PROGA, and 12 months of the values fed to its ACCEPT.

## Files

`01-inventory.md`, `02a-edge-tables.md` and `05a-dead-code-candidates.md` are generated. `02-coupling.md`, `03-waves.md`, `04-estimate.md`, `05-dead-code.md` and `06-test-strategy.md` are the argument. `graph.json`, `waves.json`, `dead-code.json` and `risks.json` are the data. The `dependency-cartographer` agent was not run, because there is one open edge. The `migration-risk-assessor` work was done inline.

## Open questions for the client's engineers

1. What job or scheduler entry runs PROGA, and is it part of the nightly batch cycle? Where does the value for its ACCEPT come from, SYSIN or the console? (`app/cbl/PROGA.cbl:8`)
2. Which program names have been supplied to it in the last 12 months, including month-end and fiscal year-end? Where do those programs live, and are they in scope for this assessment? (`app/cbl/PROGA.cbl:9`)
3. Is PROGB a live target or a leftover stub? It only returns (`app/cbl/PROGB.cbl:4`). Does anything else call it?
4. What does operations do today when the name matches no program? The CALL has no ON EXCEPTION, so I expect an abend. Is a restart or fallback procedure attached to it? (`app/cbl/PROGA.cbl:9`)
5. Is this folder the whole system or a slice? Only two source files were seen, and the extractor found no JCL, no scheduler, no copybooks and no datasets (`graph.json` `meta.files_seen`).
6. Do the called programs depend on files from the DD statements of PROGA's job step? The extractor gives a called program no DDs from its caller's step (`graph.json` `meta.limits`).
7. Which scheduler holds the nightly cycle? The extractor reads only Control-M XML and shell wrappers that name JCL files (`graph.json` `meta.limits`). Anything else, such as CA-7 or OPC, was not read and nothing was listed as unparsed.
8. Are there JCL IF/THEN/ELSE or COND= rules around that step? The extractor does not model them (`graph.json` `meta.limits`).

## Limits that touch this system

| Limit | Effect here | Evidence |
|---|---|---|
| A variable call target is resolved only from VALUE clauses and literal MOVEs in the same program | It cannot resolve PROGA's target, which comes from ACCEPT | `app/cbl/PROGA.cbl:8` |
| A called subprogram gets no DDs from its caller's JCL step | The targets' file access is unknown | `app/cbl/PROGA.cbl:9` |
| IF/THEN/ELSE and COND= in JCL are not modeled | The real job is not here to check | inference |
| Only Control-M XML and shell wrappers that name JCL files are read as schedulers | The extractor found no entry point at all | inference |

Files the extractor could not parse: none (`graph.json` `unparsed` is empty).
