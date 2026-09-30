# 00 Summary

## Scoping answers

- Target state: `refactor` (given as a flag).
- Must not break: "the nightly batch cycle" (given as a flag).
- Runtime telemetry: `none` (given as a flag). Every dead-code claim is provisional.
- Scope: `.` (the work folder). It holds 3 source files: `app/jcl/MAINJOB.jcl`, `app/cbl/PGMMAIN.cbl`
  and `app/cbl/HIDDEN01.cbl`.
- Defaults: no defaults applied. All three answers came as flags.

## What the tree shows

| Finding | Confidence | Evidence |
|---|---|---|
| One JCL job, `MAINJOB`, runs one program, `PGMMAIN`, in one step | high | `app/jcl/MAINJOB.jcl:2` |
| `PGMMAIN` reads a program name with `ACCEPT` and calls it | high | `app/cbl/PGMMAIN.cbl:9` |
| `HIDDEN01` has no caller and holds no logic | high | `app/cbl/HIDDEN01.cbl:4` |
| No datasets, copybooks, scheduler, CICS definitions or shared data exist, so there is no data, contract or temporal edge | high | `analysis`, field `edge_counts` |
| No strongly connected component, god module or articulation point exists | high | `analysis`, fields `sccs`, `god_modules`, `articulation_points` |

## Wave count

**One wave**, confidence `low`: `job:MAINJOB` and `PGMMAIN` (`modernization-assessment/waves.json:5`).
It is a candidate wave, not yet a valid one: its boundary has no output to compare and its callee
set is open (`03-waves.md`). It unblocks nothing else in the tree. `HIDDEN01` is not placed. No
deviations from the extractor's seed. Estimate for wave 1: 4 to 11 person-days if outputs are
archived, 6 to 16 if not (`04-estimate.md`, `inference`).

## Largest risk

The computed CALL at `app/cbl/PGMMAIN.cbl:9`. `PGMMAIN` is the only program the only job runs, and the
program it calls is read with `ACCEPT` at run time (`app/cbl/PGMMAIN.cbl:8`) into a field with no
initial value (`app/cbl/PGMMAIN.cbl:5`). The JCL supplies no input (`app/jcl/MAINJOB.jcl:2`). So the
behavior of the whole job cannot be read from the source. A port could pass every test against
`HIDDEN01` and still be wrong for the program that runs each night. The extractor put `HIDDEN01` in
the unknown bucket, and nothing in the tree bounds the call. `PGMMAIN` scores high-high
(`modernization-assessment/risks.json:13`), with `low` confidence.

## Open Questions for the client's engineers

| # | Question | Why it matters | Evidence |
|---|---|---|---|
| 1 | What supplies `WS-PGM-NAME` in production (a `SYSIN` DD, a wrapper, another JCL member), and what values did it hold over the last twelve months? | It decides what the job does, and the extractor resolves a call target only from a `VALUE` clause or a literal `MOVE` in the same program (`meta.limits`, item 3) | `app/cbl/PGMMAIN.cbl:8` |
| 2 | Which programs can `PGMMAIN` call, and are all of them in the source you gave us? Is `HIDDEN01` one of them, or a leftover stub? | The callee set bounds wave 1 and the dead-code register. A program outside the tree makes wave 1 unfinishable | `app/cbl/PGMMAIN.cbl:9` |
| 3 | Which jobs make up "the nightly batch cycle", in what order, and under which scheduler? Is `MAINJOB` one of them? | The tree has one job and no scheduler, so this must-not-break item maps to no unit I can confirm. I did not invent a mapping. Only Control-M XML and shell wrappers are read as schedulers (`meta.limits`, item 10) | `analysis`, field `warnings` |
| 4 | Is the tree a complete extract? Where are the callee programs, copybooks, procs, other jobs, and the datasets the cycle reads and writes? | Nothing in the tree opens a file, and the extractor gives a called subprogram no DDs from its caller's step (`meta.limits`, item 4). The job has no DD at all | `app/jcl/MAINJOB.jcl:2` |
| 5 | What does the legacy job do when no `SYSIN` is present, the name is blank, or the name matches no program? | The `CALL` has no exception handling. The port must reproduce that behavior, and the tree does not show it | `app/cbl/PGMMAIN.cbl:9` |
| 6 | Can you supply job logs or SMF records for `MAINJOB` for twelve months, plus archived outputs of the callee, including a month end and a year end? | It is the oracle for wave 1 and the only telemetry that could firm up the unknown bucket | inference |
| 7 | Can you supply file dates or source control history for the three files? | The tree is not a git repository, so the dormant bucket was not computed. An empty list means not measured | `analysis`, field `warnings` |
| 8 | Does `MAINJOB` still run, and does anyone on the team read COBOL well enough to sign off the equivalence harness? | With no scheduler, `unscheduled_jobs` cannot flag it, and who signs the deviation register affects the estimate | `analysis`, field `unscheduled_jobs` |

**Files not parsed:** none. The extractor listed nothing as skipped (`analysis`, and
`01-inventory.md`, section "Not parsed").

**Limits in `meta.limits` that touch this tree:** items 3 (variable call targets, `PGMMAIN`), 4
(a called subprogram gets no DDs), 7 (`IF/THEN/ELSE` and `COND=` not modeled, and `MAINJOB` has one
step, so no effect here) and 10 (scheduler formats) (`modernization-assessment/graph.json:9`). The
other limits, on copy replacing, in-stream cards, PROCs, CICS transaction chains, DCB and layouts,
and contract edges, touch nothing here because the tree has no copybooks, procs, CICS definitions or
datasets.

## Files in this assessment

`graph.json`, `01-inventory.md`, `02-coupling.md`, `02a-edge-tables.md`, `03-waves.md`, `waves.json`,
`03a-wave-seed.md`, `03a-waves-draft.json`, `04-estimate.md`, `05-dead-code.md`, `dead-code.json`,
`05a-dead-code-candidates.md`, `06-test-strategy.md`, `risks.json`.
