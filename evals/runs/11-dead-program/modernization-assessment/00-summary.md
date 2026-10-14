# 00 Summary

## Scoping answers

| Item | Answer | Source |
|---|---|---|
| Scope | `.` (current directory) | no scope argument |
| Target state | refactor | `--target refactor` |
| Must not break | "the nightly batch cycle" | `--must-not-break` |
| Telemetry | none | `--telemetry none` |
| Delivery | not given. The estimate shows conventional and AI-assisted. | no `--delivery` |

No defaults applied.

## Result

- Tree: 3 COBOL programs, 1 copybook, 1 JCL job (`modernization-assessment/graph.json:24`).
- Waves: 1. The only entry point is `MAINJOB` (`app/jcl/MAINJOB.jcl:2`), and nothing is shared (`modernization-assessment/waves.json:2`).
- Must-not-break mapping: "the nightly batch cycle" most likely maps to `job:MAINJOB`. It is the only job, but no scheduler was parsed, so this is inference.
- Largest risk: the supplied programs hold no logic or I/O (`app/cbl/PGMLIVE.cbl:4`), so there is no output to use as an oracle. Either the tree is an excerpt or the cycle does nothing observable. Equivalence cannot be defined until the client supplies archived job output.
- Dead code: `PGMDEAD` (`app/cbl/PGMDEAD.cbl:4`) and `cpy:UNUSED` (`app/cpy/UNUSED.cpy:1`) are unreachable. Provisional, with no telemetry. Dormancy was not measured, because there are no git dates.
- Estimate: 3 to 4.5 weeks conventional, 2.5 to 3 weeks AI-assisted, for this tree only (`04-estimate.md`).

## Open Questions

1. Is `MAINJOB` the nightly batch cycle? If the cycle has other jobs, where are they? (`app/jcl/MAINJOB.jcl:1`)
2. Are `PGMMAIN` and `PGMLIVE` the real programs, or stubs? Neither reads or writes anything (`app/cbl/PGMLIVE.cbl:4`).
3. Does anything outside this tree run `PGMDEAD` or include `cpy:UNUSED`? Can you supply 12 months of job logs or SMF records, including fiscal close?
4. Can you supply the scheduler export (Control-M, CA-7 or similar)? No scheduler was parsed, so cross-job order is unknown.
5. Can you supply archived output, with return codes, of `MAINJOB` for month-end and year-end, and say whether a parallel run is possible?
6. The extractor lists no files as not parsed. Are there PROCs, DB2 objects, CICS definitions or shell wrappers outside this tree?

## Limits that touch this system

COBOL is read as fixed format only, and free format files would have been listed as not parsed. Nested PROCs, JCL IF/THEN and COND= are not modeled. Only Control-M XML and shell wrappers are read as schedulers (`modernization-assessment/graph.json:10`).
