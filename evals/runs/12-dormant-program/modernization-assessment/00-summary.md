# 00 Summary

Assessment of the tree in `.` (3 COBOL programs, 1 JCL job, 14 lines of COBOL and 2 of JCL).

## Scoping answers

| Question | Answer | Source |
|---|---|---|
| Target state | refactor | flag `--target refactor` |
| What must not break | the nightly batch cycle | flag `--must-not-break` |
| Runtime telemetry | none | flag `--telemetry none` |

All three came as flags, so no defaults applied. This was a non-interactive run and no question was asked.

## Result

- Waves: 1. The extractor's seed was kept, with no deviations (`modernization-assessment/waves.json`).
  One entry point (`job:MAINJOB`) and one family (batch-readonly) hold all 4 units.
- Single largest risk: removing `OLDPGM` as dead code. It is old by date (last modified 2011-03-04) but
  `PGMMAIN` calls it unconditionally, first, in the only job in the tree, so it very likely runs every
  night. It is proposed for instrumentation, not deletion. Evidence: `app/cbl/PGMMAIN.cbl:4`,
  `app/cbl/OLDPGM.cbl:1`.
- Risk quadrants: `PGMMAIN` and `job:MAINJOB` are low-high, `OLDPGM` and `NEWPGM` are low-low. Port
  difficulty is 1 everywhere because there is no logic in the tree. The work is verification.
- Dead code: 0 unreachable, 0 unknown, 1 dormant (`OLDPGM`). All provisional, since there is no telemetry.
- Estimate: 6 to 13 person-days for wave 1, most of it collecting the oracle and running the harness
  (`04-estimate.md`). It holds only if the tree is the whole nightly cycle.

## Open Questions for the client's engineers

1. `OLDPGM` and `NEWPGM` contain only `GOBACK`, and `PGMMAIN` only two calls. Is this tree a stub, a
   redacted copy, or a fragment? Where is the real business logic? (`app/cbl/OLDPGM.cbl:4`,
   `app/cbl/NEWPGM.cbl:4`)
2. Does `OLDPGM` still do anything the cycle needs? Was `NEWPGM` (changed 2026-05-01) meant to replace it,
   leaving the call to `OLDPGM` behind? Is the order OLDPGM then NEWPGM significant?
   (`app/cbl/PGMMAIN.cbl:4-5`)
3. Is `job:MAINJOB` the nightly batch cycle, and what runs it? No scheduler was parsed, so the schedule,
   predecessors and successors are unknown. Please supply the scheduler export
   (Control-M, CA-7, cron or other). (`app/jcl/MAINJOB.jcl:1`)
4. Can you supply job logs or SMF records for 12 months showing whether `OLDPGM` ran? Without them the
   dormant finding stays provisional. Is the 2011-03-04 date a real last change, or an import date? The
   dates come from a git history of two commits.
5. What does the nightly cycle produce (reports, extracts, partner files, return codes), and are they
   archived? The JCL has no DD statement, so the tree shows no input or output. This is the oracle.
   (`app/jcl/MAINJOB.jcl:2`)
6. Are there other entry points not in this tree (other jobs, CICS transactions, ad hoc submits) that
   run `PGMMAIN` or call these programs? A caller outside the tree would not show in the graph.
7. Does anyone on the team read COBOL, and which compiler options (TRUNC, arithmetic mode) were used?
   These matter for any numeric field in the real logic.

## Files the extractor could not parse

None. `unparsed` is empty (3 COBOL and 1 JCL file seen, `meta.files_seen`).

## Extractor limits that touch this system (`meta.limits`)

| Limit | Why it matters here | Evidence |
|---|---|---|
| Only Control-M XML and shell wrappers are read as schedulers | No scheduler was parsed, so temporal coupling and unscheduled jobs are not assessed | analysis field `warnings` |
| IF/THEN/ELSE and COND= in JCL are not modeled | The job has one step and no COND, but the client's production JCL may | `app/jcl/MAINJOB.jcl:2` |
| A called subprogram gets no DDs from its caller's JCL step | `OLDPGM` and `NEWPGM` may use files the step supplies. The JCL has none. | `app/jcl/MAINJOB.jcl:2` |
| COBOL is read as fixed format | A free-format file would be listed as not parsed. None were. | analysis field `unparsed` |
| DCB, LRECL and RECFM are not read | Any record length on a real DD is not compared with a layout | inference |

The other limits (COPY REPLACING, computed calls, nested PROCs and embedded JCL, CICS RETURN and SEND
MAP, IDCAMS and SORT cards, LINK versus XCTL) do not touch this tree, because it has no copybook, no
computed call, no proc, no CICS and no utility step.

## Files in `modernization-assessment/`

`graph.json`, `01-inventory.md`, `02a-edge-tables.md`, `02-coupling.md`, `03a-wave-seed.md`,
`03a-waves-draft.json`, `03-waves.md`, `waves.json`, `risks.json`, `04-estimate.md`,
`05a-dead-code-candidates.md`, `05-dead-code.md`, `dead-code.json`, `06-test-strategy.md`.
