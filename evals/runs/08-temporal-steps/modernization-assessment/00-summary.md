# 00 Summary

## Scoping answers

| Question | Answer | Where it came from |
|---|---|---|
| Scope | `.` (the work folder) | no scope argument was given |
| Target state | refactor | the `--target refactor` flag |
| Must not break | "the nightly batch cycle" | the `--must-not-break` flag |
| Runtime telemetry | none | the `--telemetry none` flag |

All three answers came as flags, so **no defaults applied**. The run was non-interactive and asked nothing.

Because telemetry is none, every dead-code claim is provisional.

## What the tree is

Three COBOL programs and one JCL job, with no copybook, no dataset, no scheduler and no CICS definition
(`graph.json` field `meta.files_seen`). The extractor found
11 edges: 4 call, 4 include, 3 temporal, and no data or contract edge. There is one entry point,
`job:SEQJOB` (`app/jcl/SEQJOB.jcl:1`). Each program holds only `GOBACK` (`app/cbl/PGMA.cbl:4`,
`app/cbl/PGMB.cbl:4`, `app/cbl/PGMC.cbl:4`). The job runs them in order and then runs IEFBR14
(`app/jcl/SEQJOB.jcl:2`, `app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:4`, `app/jcl/SEQJOB.jcl:5`).

## Waves

**One wave.** It holds `PGMA`, `PGMB`, `PGMC` and `job:SEQJOB`, target state refactor, with no deviation from the
extractor's seed (`modernization-assessment/waves.json:1`). Nothing in the tree gives a reason to cut it. The
argument is in `03-waves.md`.

## The single largest risk

**The only behavior the tree defines is the order of the steps in SEQJOB, and that order is ambiguous.** The step
name STEP2 is used twice: for PGMB on line 3 and for IEFBR14 on line 5, after STEP3
(`app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:5`). The extractor orders the steps by file position and calls the
second one `STEP2#2`, which is its own label. In JCL a step name is meant to be unique, so the job may not run as
written (inference from JCL rules). Any restart at STEP2, or any `COND=` that names it, is ambiguous. The client
named the nightly batch cycle as the thing that must not break, and this job is the only candidate for it. A port
that gets the order or the failure handling wrong would break the cycle, and with no dataset, log or scheduler in
the tree, there is no oracle in it to catch that (`06-test-strategy.md`).

A close second is that the tree may not be the real system. Every program is a four line stand-in, and no
datasets are named. If so, every finding here is void until the client supplies the real source.

## Open Questions for the client's engineers

1. **Which jobs make up "the nightly batch cycle", and is SEQJOB one of them?** Nothing in the tree carries a
   schedule, and the extractor parsed no scheduler (`analysis` field `warnings`). SEQJOB is the only job in the
   tree, so it is the only candidate. I did not treat the mapping as settled. Please send the scheduler export
   (Control-M XML, a calendar, or the shell wrappers) and the job order across jobs.
2. **Is `app/jcl/SEQJOB.jcl` the production JCL? Why is the step name STEP2 used twice?**
   (`app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:5`.) Does the job run as written today? What order do the steps run
   in? Do any restart runbooks, `COND=` cards or other jobs refer to STEP2 by name?
3. **Are PGMA, PGMB and PGMC the real programs?** Each holds only `GOBACK` (`app/cbl/PGMA.cbl:4`,
   `app/cbl/PGMB.cbl:4`, `app/cbl/PGMC.cbl:4`). If they are stand-ins, please send the real source, the copybooks
   they use and the files they read and write. The job has no DD statement at all (`app/jcl/SEQJOB.jcl:2`).
4. **What does the IEFBR14 step do?** It runs last and has no DD statement in this copy
   (`app/jcl/SEQJOB.jcl:5`). What did it allocate or delete, and did anything depend on it?
5. **Can you send run history for SEQJOB for at least 12 months?** Job logs, return codes and step names, with
   month-end and fiscal year-end nights. With telemetry none, the dead-code register is provisional, and this is
   also the oracle for `06-test-strategy.md`.
6. **What outputs does the nightly cycle leave behind, and who reads them?** Archived generations, reports,
   partner files. The tree shows none, so the behavioral oracle has to come from there.
7. **When were these files last changed?** The tree is not a git repository, so no unit has a last-modified date
   and the dormant bucket was not measured (`analysis` field `warnings`). Please send change dates from the source
   library.
8. **Is there JCL logic the extractor cannot see?** It does not model `IF/THEN/ELSE` or `COND=`, and reads step
   order as file order (`meta.limits`). This copy has none (`app/jcl/SEQJOB.jcl:2`), but production may. Are
   there PROCs, INCLUDE members, stored procedures, IMS, DB2 or MQ pieces outside this tree?

## Not parsed, and limits that touch this system

Nothing was listed as not parsed (`unparsed` in `graph.json` is empty). These extractor limits touch this
system (`meta.limits` in `graph.json`):

- `IF/THEN/ELSE` and `COND=` are not modeled, and step order is file order. This touches SEQJOB directly.
- Only Control-M XML and shell wrappers are read as schedulers. None is in the tree, so order across jobs is
  unknown.
- `DCB`, `LRECL` and `RECFM` are not read. No record layout is known.
- `SORT` and most in-stream cards are not read. None is in this job.
- The extractor reads only COBOL, copybooks, JCL, PROCs, CICS definitions, Control-M XML and shell wrappers.
  Anything else is invisible.

The other limits (copy replacing, variable call targets, subprogram DDs, nested PROCs, CICS transaction chains,
LINK and XCTL, free format COBOL) do not touch this tree. It has no copybook, no call between programs, no PROC
and no CICS.

## Files in this assessment

- `01-inventory.md`, `02a-edge-tables.md`, `03a-wave-seed.md`, `05a-dead-code-candidates.md`: generated facts
- `02-coupling.md`, `03-waves.md`, `04-estimate.md`, `05-dead-code.md`, `06-test-strategy.md`: the argument
- `graph.json`, `waves.json`, `risks.json`, `dead-code.json`: the data
