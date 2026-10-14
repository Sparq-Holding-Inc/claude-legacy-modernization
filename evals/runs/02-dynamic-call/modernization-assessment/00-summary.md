# 00 Summary

## Scoping answers

| Item | Value |
|---|---|
| Target state | refactor (given as a flag) |
| Must not break | "the nightly batch cycle" (given as a flag) |
| Telemetry | none (given as a flag) |
| Delivery | not given, so the estimate shows conventional and AI-assisted |
| Defaults applied | no defaults applied |

## Result

- **Waves: 0.** The tree has no entry point (no JCL, CSD or scheduler), so nothing can be sequenced (`modernization-assessment/graph.json:86`). Both programs are unassigned (`modernization-assessment/waves.json:4`).
- **Size.** Two COBOL programs, 14 lines (`app/cbl/PROGA.cbl:10`, `app/cbl/PROGB.cbl:4`).
- **Largest risk.** PROGA calls a program whose name is read at run time (`app/cbl/PROGA.cbl:8`, `app/cbl/PROGA.cbl:9`). Its real dependencies are unknown, so no dead-code claim and no wave placement is safe. Confidence: low.
- **Must-not-break mapping.** "The nightly batch cycle" maps to no unit in this tree. No mapping is invented.
- **Dead code.** Both programs are unknown. Nothing is unreachable, and dormancy was not computed because there are no last-modified dates (`modernization-assessment/graph.json:146`). All claims are provisional, since telemetry is none.

## Open Questions for the client's engineers

1. Which JCL jobs and scheduler entries make up the nightly batch cycle? None are in this tree, so nothing can be sequenced.
2. What values does `WS-PGM-NAME` take in production, and where does the `ACCEPT` input come from (`app/cbl/PROGA.cbl:8`)?
3. Does PROGA ever load programs that are not in this tree (`app/cbl/PROGA.cbl:9`)? Is PROGB one of its targets?
4. Is the supplied tree complete? The extractor saw 2 COBOL files and 0 copybooks, JCL, PROCs, CSD or scheduler files (`modernization-assessment/graph.json:24`).
5. Can the team supply 12 months of job logs and archived output generations? Without them dead-code claims stay provisional and the oracle is weak (`06-test-strategy.md`).
6. Can the source history be supplied? The tree is not a git repository, so no last-modified dates exist (`modernization-assessment/graph.json:146`).
7. Is a parallel run of the nightly cycle possible?

## Extractor limits that touch this system

- A variable call target is resolved only from VALUE clauses and literal MOVEs in the same program (`modernization-assessment/graph.json:12`). PROGA uses ACCEPT, so it stays unresolved.
- Only Control-M XML and shell wrappers that name JCL files are read as schedulers (`modernization-assessment/graph.json:19`).
- Nothing was listed as not parsed (`modernization-assessment/graph.json:82`).
