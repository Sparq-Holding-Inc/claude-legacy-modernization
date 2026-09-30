# 00 Summary

Scope: the whole work folder (`.`). The tree holds three COBOL programs and one JCL job, 16 lines of source in all.

## Scoping answers

| Question | Answer | Source |
|---|---|---|
| Target state | refactor | given as `--target refactor` |
| What must not break | "the nightly batch cycle" | given as `--must-not-break` |
| Runtime telemetry | none | given as `--telemetry none` |

Defaults: no defaults applied. All three answers came as flags.

Telemetry is none, so every dead-code claim in this assessment is provisional.

## Result

- Waves: 1. The tree has one entry point, `job:MAINJOB`, so the extractor cut one family and one wave. I made no deviations from it. See `03-waves.md`.
- The four units in wave 1 are one call chain: the job runs PGMMAIN, and PGMMAIN calls OLDPGM and NEWPGM.
- No dataset, copybook, proc, scheduler, CICS or DB2 artifact is in the tree. The extractor found no data, contract or temporal edge (`analysis`, field `edge_counts`).

## The single largest risk

OLDPGM looks like the first thing to delete and is the one thing that must not be. It was last modified on 2011-03-04, so the extractor lists it as dormant. But PGMMAIN calls it unconditionally, with no test around the call. PGMMAIN was itself added on 2026-05-01. A cleanup driven by the dormant list, or by file age alone, would break every run of MAINJOB. The call is loud: a CALL to a missing program fails the step. It would be noticed on the first run, but on the nightly batch cycle that is a production failure.

| Risk | Confidence | Evidence |
|---|---|---|
| OLDPGM is old but on the live path of MAINJOB. Deleting it on age alone breaks the job. | medium | `app/cbl/PGMMAIN.cbl:4`, `app/cbl/OLDPGM.cbl:1` |
| The nightly batch cycle maps to no unit with evidence. MAINJOB is the only batch job, so it is a candidate and no more. | low | `app/jcl/MAINJOB.jcl:1` |
| The source may not be the real system. Each program is 4 to 6 lines with no logic, and the job has no DD statements. | low | inference |

## Open Questions

Addressed to the client's engineers.

1. Is `MAINJOB` the nightly batch cycle, or one job inside it? Which scheduler runs it, and when? The tree holds no scheduler export (`analysis`, field `warnings`). The extractor reads only Control-M XML and shell wrappers that name JCL files. If you use CA-7, TWS or another scheduler, send that export. Until then the must-not-break item maps to no unit in the tree, and I have not invented a mapping.
2. Is the source in `app/cbl` the code that actually runs? PGMMAIN, OLDPGM and NEWPGM each hold only a CALL or a GOBACK (`app/cbl/OLDPGM.cbl:4`, `app/cbl/NEWPGM.cbl:4`, `app/cbl/PGMMAIN.cbl:6`). Is the source redacted or stubbed, or does the deployed load module differ from it? Send the compile listing or load module date for each.
3. What does `MAINJOB` read and write? Its only step has no DD statements at all (`app/jcl/MAINJOB.jcl:2`): no input, no output, no SYSOUT, no STEPLIB. Which datasets, GDGs, reports or partner extracts does the cycle produce? These are the oracle for `06-test-strategy.md`.
4. Does OLDPGM still run in production? Send job logs or SMF step records for the last 12 months, month end and year end included. Then the dormant flag can be settled with evidence.
5. Why does a 2026 program call both a 2011 program and a 2026 program, in that order (`app/cbl/PGMMAIN.cbl:4`, `app/cbl/PGMMAIN.cbl:5`)? Is NEWPGM the replacement for OLDPGM, meant to run alongside it for a time, or are both meant to run for good? Does the order matter?
6. Can the git dates be trusted for dormancy? The history has two commits with the message "x" and a one-letter author. Was the repository rebuilt from an export? If so, the 2026-05-01 date says when the files were loaded, not when they last changed.
7. What is the pass mark for "the nightly batch cycle"? Return codes only, run window, downstream jobs that consume its output, or reports that people read? Who signs the Deviation Register?

Files the extractor listed as not parsed: none (`unparsed` is empty in `graph.json`).

## Extractor limits that touch this system

Every limit in `meta.limits` that could change a conclusion here. The rest do not apply, because the tree has no copybook, proc, CICS, IDCAMS, DB2 or shell file (`analysis`, field `node_counts`).

| Limit | Why it touches this tree | Evidence |
|---|---|---|
| Only Control-M XML and shell wrappers are read as schedulers | Any other scheduler is invisible. This is the gap behind Open Question 1. | inference |
| IF/THEN/ELSE and COND= in JCL are not modeled | MAINJOB has one step, so it is harmless in this file. A fuller version of the job could differ. | `app/jcl/MAINJOB.jcl:2` |
| A called subprogram gets no DDs from its caller's JCL step | OLDPGM and NEWPGM are called subprograms. Their files, if any, would belong to step S1. | `app/cbl/PGMMAIN.cbl:4` |
| COBOL is read as fixed format | All three programs parsed as fixed format. A free format file would have been listed as not parsed, and none was. | `app/cbl/PGMMAIN.cbl:1` |
| A variable call target is resolved only from VALUE clauses and literal MOVEs | The two calls are literals, so they resolved. `unresolved_dynamic` is empty. | `app/cbl/PGMMAIN.cbl:4` |

## Method notes

- The dependency-cartographer work was not needed. `graph.json` has no unresolved edge and no edge below high confidence, well under the threshold of about 20 (`analysis`, field `unresolved_dynamic`).
- The migration-risk-assessor work was done inline and wrote `risks.json`. The two blast-radius scores of 3 for `job:MAINJOB` and PGMMAIN rest on the unconfirmed mapping in Open Question 1. Both are labeled inference.
- Files: `01-inventory.md`, `02a-edge-tables.md`, `02-coupling.md`, `03a-wave-seed.md`, `03-waves.md`, `04-estimate.md`, `05a-dead-code-candidates.md`, `05-dead-code.md`, `06-test-strategy.md`, plus `graph.json`, `waves.json`, `dead-code.json` and `risks.json`.
