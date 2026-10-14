# 00 Summary

## Scoping answers

| Question | Answer | Source |
|---|---|---|
| Target state | refactor | `--target refactor` |
| Must not break | "the nightly batch cycle" | `--must-not-break` |
| Telemetry | none | `--telemetry none` |
| Delivery | not given. Estimate shows conventional and AI-assisted | no `--delivery` flag |

No defaults applied. All three scoping answers came as flags.

## Headline

- **Waves: 0.** The tree has two programs and one copybook, and no entry point (`modernization-assessment/graph.json:154`). Nothing can be sequenced until the client supplies JCL, a CSD or a scheduler export. `modernization-assessment/waves.json:3` is empty and both programs are `unassigned`.
- **Dead code: all unknown.** No telemetry and no entry points. Nothing is proven unreachable and dormancy was not measured (`modernization-assessment/graph.json:153`).
- **Estimate: not producible per wave.** See `04-estimate.md`.

## Largest risk

The must-not-break item, "the nightly batch cycle", maps to no unit in this tree. There is no JCL job, scheduler job or wrapper (`modernization-assessment/graph.json:30`). The refactor is being scoped without the thing it must not break. Second, the shared copybook holds a packed-decimal balance (`app/cpy/SHARED01.cpy:3`) used by both programs (`app/cbl/PROGA.cbl:5`, `app/cbl/PROGB.cbl:5`). A float port would be a silent defect. Confidence: high on the first, medium on the second since neither program uses the field today (`app/cbl/PROGA.cbl:7`).

## Open Questions for the client's engineers

1. Where is the JCL, or the scheduler export (Control-M or other), for the nightly batch cycle? Which jobs run PROGA and PROGB, and in what order? Evidence: no JCL or scheduler file exists, `modernization-assessment/graph.json:30`.
2. Is this tree the whole system, or a fragment? Which other programs COPY `SHARED01`? Evidence: `app/cpy/SHARED01.cpy:1`.
3. What datasets, VSAM files or DB2 tables does the cycle read and write? None appear in the tree (`modernization-assessment/graph.json:129`). Which fields carry `SH-BALANCE` between jobs?
4. Do PROGA and PROGB still run? Can you supply 12 months of job logs or SMF records? Telemetry is `none`, so every dead-code claim is provisional (`modernization-assessment/dead-code.json:2`).
5. Which cycle steps run only at month-end or fiscal close? None are visible.
6. Can the old and new systems run in parallel on the same input? If not, which archived generations (GDG), reports and partner extracts exist as golden masters? See `06-test-strategy.md`.
7. Source dates are missing because the tree is not a git repository. Can you supply last-modified dates or the repository history (`modernization-assessment/graph.json:153`)?
8. Are there files the extractor does not read: free-format COBOL, PL/I, assembler, stored procedures, other schedulers, shell wrappers that do not name JCL? Nothing was listed as not parsed, but the extractor only reads COBOL, copybooks, JCL, PROCs, CICS CSD, Control-M XML and some shell wrappers (`modernization-assessment/graph.json:10`).
9. Does either program read the record through a private layout, or does `COPY REPLACING` appear anywhere? The extractor does not apply COPY REPLACING (`modernization-assessment/graph.json:11`).

## Extractor limits that touch this system

- No dates, so no dormancy (`modernization-assessment/graph.json:153`).
- DCB, LRECL and RECFM are not read (`modernization-assessment/graph.json:20`). Record lengths cannot be checked against `SHARED01`.
- Contract edges are high only when both sides COPY the same layout (`modernization-assessment/graph.json:21`).

## Files

`01-inventory.md`, `02-coupling.md`, `03-waves.md`, `04-estimate.md`, `05-dead-code.md`, `06-test-strategy.md`, `graph.json`, `waves.json`, `risks.json`, `dead-code.json`.
