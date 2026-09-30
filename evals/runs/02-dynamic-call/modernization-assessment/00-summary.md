# 00 Summary

Scope: `.` (the work folder). The tree holds two COBOL programs and 14 lines of source: `PROGA` and
`PROGB` (`app/cbl/PROGA.cbl:1`, `app/cbl/PROGB.cbl:1`). There is no copybook, JCL, CSD, scheduler or
dataset.

## Scoping answers

| Question | Answer | Where it came from |
|---|---|---|
| Target state | refactor | the `--target refactor` flag |
| What must not break | the nightly batch cycle | the `--must-not-break` flag |
| Runtime telemetry | none | the `--telemetry none` flag |

All three came as flags: no defaults applied.

Telemetry is none, so every dead-code claim is provisional (see `05-dead-code.md`).

## Result in one paragraph

Wave count: 0. The tree has no entry point, so nothing can be sequenced. `waves.json` has an empty
`waves` list and both programs sit in `unassigned`. Nothing can be sequenced until the client supplies
JCL, a CSD or a scheduler export. I invented no wave. The one coupling in the system is a computed
call, and it keeps both programs in the unknown dead-code bucket. Nothing is proposed for deletion.

## Largest risk

`PROGA` calls a program whose name it reads at run time. `WS-PGM-NAME` has no `VALUE` clause and is
set only by `ACCEPT`, and the `CALL` has no `ON EXCEPTION` phrase (`app/cbl/PROGA.cbl:5`,
`app/cbl/PROGA.cbl:8`, `app/cbl/PROGA.cbl:9`). The set of programs it can start cannot be bounded from
the source. That means we cannot say what `PROGA` really depends on, we cannot call `PROGB` dead, and we
cannot tie either program to the nightly batch cycle. A port that hard-wires or drops the dispatch
would fail silently. The risk is the unknown target set, and the fix is evidence, not more analysis.

## Findings at a glance

| Finding | Confidence | Evidence |
|---|---|---|
| Wave count is 0. No entry point exists in the tree. | high | analysis (`entry_points` is empty, `wave_seed.waves` is empty) |
| One call edge, and it is computed. No data, include, contract or temporal edge exists. | high | `app/cbl/PROGA.cbl:9` |
| `PROGA` and `PROGB` are both in the unknown bucket. Unreachable is empty and dormant was not measured. | low | `app/cbl/PROGA.cbl:9` |
| The must-not-break item, the nightly batch cycle, maps to no unit in the tree. | high | inference |
| The extractor labels both programs `batch`. That is its default for a program no job runs, not evidence that a batch job runs them. | medium | analysis (`node_counts`) |
| `PROGB` is a stub that only returns. | high | `app/cbl/PROGB.cbl:4` |

## Open Questions

For the client's own engineers.

1. **Where is the nightly batch cycle?** No JCL job, scheduler job or shell wrapper exists in the
   tree, so "the nightly batch cycle" maps to no unit. Which programs and jobs make it up, and does
   `PROGA` or `PROGB` belong to it? I have not assumed either does.
2. **What names does `PROGA` receive?** The `ACCEPT` at `app/cbl/PROGA.cbl:8` fills `WS-PGM-NAME`.
   Where does it read from (SYSIN, console, a job parameter), and what values arrive over a full
   business cycle, including month-end and fiscal year-end?
3. **Which programs can the computed `CALL` at `app/cbl/PROGA.cbl:9` start?** Give us the load
   library or the list of programs it can match, including any that are not in this tree.
4. **Is this tree complete?** It has two programs and no copybook, JCL, CSD or scheduler
   definition, and the extractor skipped nothing (`unparsed` is empty). Is this a fragment of a
   larger system, and where is the rest?
5. **What starts `PROGA`, and does anything call it or `PROGB` from outside the tree?** A CICS
   region, a shell script, a program in another language, or a scheduler we were not given would each
   create an entry point and change the dead-code and wave results.
6. **What happens today when the name matches no program?** `CALL` has no `ON EXCEPTION`
   (`app/cbl/PROGA.cbl:9`). Does the job abend, set a return code, or continue? The port must
   match it.
7. **Can you give us job history?** Job logs or SMF for the last 12 months would show which names were
   started and turn the unknown bucket into evidence. Dormancy was not computed either, because the
   tree has no git dates. Can you supply last-changed dates from source control?
8. **Is `PROGB` a deliberate stub?** It only returns (`app/cbl/PROGB.cbl:4`). Is anything expected to
   happen when it is called, such as a side effect in a place this tree cannot show?

## Extractor gaps that touch this system

Nothing was listed as not parsed: `unparsed` is empty, and both files read as fixed format COBOL. These
limits in `meta.limits` do touch this system:

- A variable call target is resolved only from `VALUE` clauses and literal `MOVE`s in the same
  program. `WS-PGM-NAME` has neither, so the call is unresolved.
- Only Control-M XML and shell wrappers that name JCL files are read as schedulers. None exist here,
  so there is no scheduler ordering. The absence is a gap in what was supplied.
- IF/THEN/ELSE and `COND=` in JCL are not modeled. This matters once the JCL arrives.
- A called subprogram gets no DDs from its caller's JCL step. This matters if `PROGB`, or a program
  `PROGA` starts, uses files.
- `EXEC CICS RETURN TRANSID`, `START` and `SEND MAP` are not edges. If either program runs under CICS,
  that chain is invisible.

## Files in this assessment

`01-inventory.md`, `02a-edge-tables.md`, `02-coupling.md`, `03a-wave-seed.md`, `03-waves.md`,
`04-estimate.md`, `05a-dead-code-candidates.md`, `05-dead-code.md`, `06-test-strategy.md`,
`graph.json`, `waves.json`, `dead-code.json`, `risks.json`.
