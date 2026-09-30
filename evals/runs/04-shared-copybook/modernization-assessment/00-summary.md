# 00 Summary

## Scoping answers

| Question | Answer |
|---|---|
| Target state | refactor |
| What must not break | the nightly batch cycle |
| Runtime telemetry | none. Every dead-code claim is provisional. |
| Defaults applied | no defaults applied. All three came as flags. |
| Scope | `.` (the work folder) |

## What was assessed

Two batch programs, PROGA and PROGB, and one copybook, SHARED01. Together they hold 19 lines (`analysis`, field `node_counts`). The extractor found two edges, both `include` (`analysis`, field `edge_counts`). There is no JCL, no scheduler, no dataset and no CICS definition (`meta.files_seen` in `graph.json`).

## Result

| Item | Finding | Confidence | Evidence |
|---|---|---|---|
| Wave count | 1, and provisional. The seed placed nothing, because the tree has no entry point. One wave was written by hand because the validator rejects an empty plan. | low | `modernization-assessment/waves.json:3` |
| Largest risk | The shared layout SHARED01. Both programs include it, and it carries a packed decimal balance (`S9(9)V99 COMP-3`). A change to it, or a port that turns the balance into a float, reaches both programs and every file with that layout, and it fails silently. The programs must move together. | medium | `app/cbl/PROGA.cbl:5`, `app/cbl/PROGB.cbl:5`, `app/cpy/SHARED01.cpy:3` |
| Largest gap | The nightly batch cycle, the must-not-break item, is not in the tree. It cannot be tied to any program. | low | inference |
| Dead code | Nothing is unreachable. Dormancy was not measured. PROGA, PROGB and SHARED01 are unknown. Nothing is proposed for deletion. | low | analysis, field `dead_code_candidates` |
| Risk scores | PROGA and PROGB both score port difficulty 1 and blast radius 2, low-low, on thin evidence. | low | `modernization-assessment/risks.json:1` |

Files: `01-inventory.md`, `02-coupling.md`, `03-waves.md`, `04-estimate.md`, `05-dead-code.md`, `06-test-strategy.md`, and `graph.json`, `waves.json`, `risks.json`, `dead-code.json`.

## Open Questions

For the client's own engineers.

1. Which JCL job or scheduler entry runs PROGA and PROGB, and are they part of the nightly batch cycle? Without this the tree has no entry point, and nothing is proven live or dead. Nothing was listed as not parsed by the extractor (`analysis`, field `entry_points` is empty).
2. Which scheduler runs the nightly batch cycle? The extractor reads only Control-M XML and shell wrappers that name JCL files (`meta.limits` in `graph.json`). CA-7, TWS or OPC definitions would not be read. They need a converter or a manual list.
3. Which files, reports, extracts or databases carry the SHARED01 layout? The tree shows none, so no contract edge exists in the graph. The extractor does not read DCB, LRECL or RECFM, so a record length would not be checked against the copybook either.
4. What do the values 1 and 2 moved into SH-CUST-ID mean (`app/cbl/PROGA.cbl:7`, `app/cbl/PROGB.cbl:7`)? Is either program a stub, a test driver or a real step?
5. Does anything read SH-BALANCE by offset, such as a partner extract or a regulatory report (`app/cpy/SHARED01.cpy:3`)? If so, the port must keep the packed layout byte for byte.
6. Can the old system stay up for a parallel run of the nightly cycle, and where are the archived outputs (GDG generations, reports, partner extracts) kept?
7. Which programs ran in the last 12 months? Job logs or SMF records would turn the dead-code register from provisional to evidence. The tree is not a git repository, so last-modified dates are missing and dormancy was not computed.
8. Is anything missing from the tree, such as other programs, procs, copybooks with REPLACING, or programs in free format? The extractor reads fixed format only and does not apply COPY REPLACING (`meta.limits` in `graph.json`). Both source files parsed, and neither uses REPLACING (`app/cbl/PROGA.cbl:5`, `app/cbl/PROGB.cbl:5`).

## Limits that touch this system

From `meta.limits` in `graph.json`: fixed-format COBOL only; COPY REPLACING not applied; DCB, LRECL and RECFM not read; only Control-M XML and shell wrappers read as schedulers. The limits on computed calls, called subprograms, JCL IF/THEN/ELSE and COND=, nested PROCs, embedded JCL and CICS RETURN TRANSID do not touch this tree, because it holds none of those constructs (`analysis`, fields `unresolved_dynamic` and `embedded_jcl` are empty).
