# 00 Summary

## Scoping answers

| Question | Answer | Source |
|---|---|---|
| Target state | refactor | flag `--target` |
| Must not break | "the nightly batch cycle" | flag `--must-not-break` |
| Telemetry | none | flag `--telemetry` |
| Delivery | not given. The estimate shows conventional and AI-assisted. | flag missing |

No defaults applied. All three scoping answers came as flags.

The scope is the current directory. It holds 3 COBOL programs and 1 JCL job (`modernization-assessment/01-inventory.md:1`).

## Result

- **Waves:** 1 (`modernization-assessment/waves.json:3`). No deviations from the extractor's seed.
- **Mapping of the must-not-break item:** "the nightly batch cycle" maps to `job:SEQJOB` by inference only. The tree has no scheduler and nothing says SEQJOB is nightly.
- **Dead code:** none found. Telemetry is none, so this is provisional. Dormancy was not measured because the tree has no git history.
- **Estimate:** 2.7 to 5.5 weeks conventional, 2.2 to 4.6 weeks AI-assisted, for wave 1 (`modernization-assessment/04-estimate.md:1`).

## Largest risk

`job:SEQJOB` repeats the step name STEP2 on `app/jcl/SEQJOB.jcl:3` and `app/jcl/SEQJOB.jcl:5`. On z/OS this is normally a JCL error. `inference`: the job may be rejected as written, or this file may differ from what runs in production. The nightly batch cycle is the must-not-break item and this is its only visible job, so the boundary of the equivalence harness cannot be defined until this is settled.

## Open Questions

1. Is the repeated STEP2 (`app/jcl/SEQJOB.jcl:5`) a copy error in this extract, or does production run it? What is the real step list?
2. Is `job:SEQJOB` the nightly batch cycle, or only part of it? What other jobs run in that cycle?
3. Can you supply the scheduler export (Control-M or other)? No scheduler artifact was parsed, so the order across jobs is unknown.
4. PGMA, PGMB and PGMC only `GOBACK` (`app/cbl/PGMA.cbl:4`). Are these placeholders, and where is the real source?
5. Can you supply 12 months of job logs and SMF records for SEQJOB, including month-end and year-end runs? This is the oracle and the telemetry for dead code.
6. Does the step order PGMA, PGMB, PGMC carry meaning when no shared dataset links the steps (`app/jcl/SEQJOB.jcl:2`)? Who owns that rule?
7. Is the tree under version control anywhere? Last-modified dates are unknown, so the dormant bucket is not measured.

## Extractor limits that touch this system

- Not parsed: nothing was skipped.
- IF/THEN/ELSE and COND= in JCL are not modeled. Step order is file order, so any restart or conditional logic would be unseen (`app/jcl/SEQJOB.jcl:2`).
- Only Control-M XML and shell wrappers are read as schedulers. Other scheduler formats would need an export.
- DCB, LRECL and RECFM are not read. No DD statements exist in this job (`app/jcl/SEQJOB.jcl:2`).

## Files

`01-inventory.md`, `02-coupling.md`, `03-waves.md`, `04-estimate.md`, `05-dead-code.md`, `06-test-strategy.md`, plus `graph.json`, `waves.json`, `risks.json`, `dead-code.json`.
