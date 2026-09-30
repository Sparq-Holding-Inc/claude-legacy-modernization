# 00 Summary

## Scoping answers

| Question | Answer | Source |
|---|---|---|
| Target state | refactor | flag `--target refactor` |
| What must not break | the nightly batch cycle | flag `--must-not-break` |
| Runtime telemetry | none | flag `--telemetry none` |

All three came as flags. **No defaults applied.**

With no telemetry, every dead-code claim is provisional. Dormancy was not measured at all, because the
tree has no last-modified dates.

## Result

| Finding | Value | Confidence | Evidence |
|---|---|---|---|
| Wave count | 1 | low | `modernization-assessment/waves.json:2` |
| Size of the tree | 3 COBOL programs, 1 JCL job, 0 copybooks, 0 datasets, 0 schedulers | high | `app/jcl/SEQJOB.jcl:1` |
| Dead code | none unreachable, none unknown, dormant not measured | low | `modernization-assessment/dead-code.json:1` |

## Single largest risk

The order of the nightly batch cycle lives only in the file order of `SEQJOB`, and that job uses the
step name STEP2 twice (`app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:5`). A repeated step name is a JCL
error on z/OS (inference), so the job may not run as written, and any restart or condition that names
STEP2 is ambiguous. No scheduler was parsed to say what the real order is. A close second: all three
programs are empty (`app/cbl/PGMA.cbl:4`), so the real logic, if any, is outside this tree.

## Open Questions

For the client's engineers.

1. Is `SEQJOB` the nightly batch cycle? Nothing in the tree names it. Which scheduler runs it, and can you send the export? None was parsed (`analysis` field `warnings`).
2. Line 5 of `SEQJOB` repeats the step name STEP2 and runs IEFBR14 (`app/jcl/SEQJOB.jcl:5`). Is that a copy error? What order do you intend, and does anything restart or test on STEP2?
3. PGMA, PGMB and PGMC each contain only GOBACK (`app/cbl/PGMA.cbl:4`, `app/cbl/PGMB.cbl:4`, `app/cbl/PGMC.cbl:4`). Are these stubs? Where is the real logic, and where are the datasets? The job has no DD statements (`app/jcl/SEQJOB.jcl:2`).
4. Can you supply archived job logs, return codes and SYSOUT for SEQJOB over 13 months or more? This is the oracle (see `modernization-assessment/06-test-strategy.md`). Can the old system stay up for a parallel run?
5. Which programs ran in the last 12 months? With no telemetry and no git dates, dormancy is not measured. Can you send SMF or scheduler history?
6. Does anything outside this tree call these programs or submit SEQJOB, such as a CICS transaction, an operator command or a shell wrapper? The extractor reads only Control-M XML and shell wrappers that name JCL files.
7. Are there PROCs, INCLUDE members, IF/THEN/ELSE or COND rules that did not come with this tree? The extractor does not follow nested PROCs or INCLUDE members, and it does not model COND (`modernization-assessment/graph.json:1`, field `meta.limits`).

## Not parsed, and limits that touch this system

Nothing was skipped: `unparsed` is empty (`analysis` and `modernization-assessment/graph.json:1`). These `meta.limits` touch this system:

- IF/THEN/ELSE and COND= in JCL are not modeled. Step order is file order.
- Only Control-M XML and shell wrappers that name JCL files are read as schedulers. No scheduler was found.
- A called subprogram gets no DDs from its caller's step, and DCB, LRECL and RECFM are not read.
- Nested PROC calls and INCLUDE members are not followed.

## Method notes

I did the `migration-risk-assessor` work inline, and wrote `modernization-assessment/risks.json`. I
skipped the `dependency-cartographer`, since `graph.json` has no unresolved computed call and no low
or medium confidence edge.
