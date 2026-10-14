# 00 Summary

## Scoping answers

| Question | Answer | Source |
|---|---|---|
| Target state | refactor | flag `--target` |
| Must not break | the nightly batch cycle | flag `--must-not-break` |
| Telemetry | none | flag `--telemetry` |
| Delivery | not given. The estimate shows conventional and AI-assisted. | no flag |

No defaults applied.

## Result

- **Waves: 0.** The tree has two COBOL programs and no entry point, so nothing can be sequenced (`modernization-assessment/03-waves.md`). PROGA calls PROGB statically (app/cbl/PROGA.cbl:6).
- **Largest risk:** the must-not-break item, the nightly batch cycle, maps to no unit in the tree. No JCL, scheduler or dataset was supplied, so the assessment cannot say what the cycle runs, in what order, or on what data. Evidence: `modernization-assessment/graph.json:24`.
- **Risk scores:** both programs are low port difficulty (`modernization-assessment/risks.json`). The scoring agent rated PROGA's blast radius at medium confidence because it may drive the cycle.
- **Dead code:** nothing is unreachable or dormant. Both programs are unknown, and telemetry is none, so everything is provisional (`modernization-assessment/05-dead-code.md`).
- **Oddity:** PROGA prints `CALL FAILED IF WE GET HERE` before it calls PROGB (app/cbl/PROGA.cbl:5). It looks like a test fixture (inference).

## Open Questions

1. Which JCL job or scheduler entry runs the nightly batch cycle? None is in the tree.
2. Is PROGA the cycle's driver, or a test fixture? Evidence: app/cbl/PROGA.cbl:5.
3. Why does PROGA print `CALL FAILED IF WE GET HERE` before the call? Does anything read that text? Evidence: app/cbl/PROGA.cbl:5.
4. PROGB only does `GOBACK`. Is it a stub for code that was removed? Evidence: app/cbl/PROGB.cbl:4.
5. Is there more source (copybooks, JCL, PROCs, CICS definitions, Control-M exports) that was not copied? The extractor saw 0 of each (`modernization-assessment/graph.json:24`).
6. Are the programs dated? The tree has no git history, so dormancy was not measured (`modernization-assessment/graph.json:131`).
7. Do archived outputs (GDG generations, SYSOUT, partner extracts) exist for the oracle? See `modernization-assessment/06-test-strategy.md`.
8. Extractor limits that touch this system: COBOL is read as fixed format, and JCL logic such as COND is not modeled (`modernization-assessment/graph.json:10`, `modernization-assessment/graph.json:20`). Nothing was listed as not parsed.
