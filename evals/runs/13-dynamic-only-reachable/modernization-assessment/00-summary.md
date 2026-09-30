# 00 Summary

## Scoping answers

| Question | Answer | Source |
|---|---|---|
| Target state | refactor | flag `--target refactor` |
| What must not break | the nightly batch cycle | flag `--must-not-break` |
| Runtime telemetry | none. Every dead-code claim is provisional. | flag `--telemetry none` |

All three came as flags, so **no defaults applied**. The run was non-interactive, and nothing was
asked.

## What was assessed

Two COBOL programs and one JCL job, 16 lines in all (`analysis`, field `node_counts`). One entry
point: `job:MAINJOB` (`app/jcl/MAINJOB.jcl:1`). The extractor read every file. Nothing was left
unparsed (`analysis`, field `unparsed` is empty).

## Wave count

One wave. It holds PGMMAIN and `job:MAINJOB`, in the batch-readonly family, with medium blast radius
and low confidence (`waves.json`). The read-only label is a fact about the edges the extractor saw.
It is not proven, because of the largest risk below. HIDDEN01 is not placed.

## Largest risk

PGMMAIN calls a program whose name is read at run time by ACCEPT, from a field that has no VALUE
clause, and CALL has no ON EXCEPTION clause (`app/cbl/PGMMAIN.cbl:8`, `app/cbl/PGMMAIN.cbl:9`). The
job defines no input (`app/jcl/MAINJOB.jcl:2`). So the whole behavior of this job is decided by a
value that is not in the tree. Any statement about what it reads, writes or breaks is bounded by
that unknown. The only other program, HIDDEN01, has no static caller (`app/cbl/HIDDEN01.cbl:1`) and
is in the unknown dead-code bucket. It must not be deleted on this evidence.

## Open Questions

Addressed to the client's engineers.

1. Where does the value for the ACCEPT at `app/cbl/PGMMAIN.cbl:8` come from in production: a SYSIN in
   a proc, a JCL override, the scheduler, or an operator? MAINJOB defines no input
   (`app/jcl/MAINJOB.jcl:2`).
2. Which program names has PGMMAIN dispatched to in the last 12 months, and are all of them in this
   tree? Is HIDDEN01 one of them?
3. Is MAINJOB part of the nightly batch cycle you named? Which jobs run before and after it? No
   scheduler artifact was parsed, so we cannot say (`analysis`, field `warnings`).
4. Does this copy hold every JCL job, proc and copybook, or were some left out? Only one job exists.
5. What datasets, DB2 tables or queues do the dispatched programs use? MAINJOB has no DD statements.
6. Do you have last-changed dates for each member? The tree is not a git repository, so dormancy was
   not measured (`analysis`, field `warnings`).
7. Are archived outputs for the nightly cycle kept (SYSOUT, reports, GDG generations), and does the
   window include month end and fiscal year end?
8. Who on the team can read COBOL and JCL, and who can sign the deviation register?
9. For the refactor target, where should dispatch by program name live in the new design? A
   registry needs the closed list of names from question 2.

## Limits that touch this system

From `meta.limits` in `graph.json`. There are no files listed as not parsed.

| Limit | How it touches this system | Evidence |
|---|---|---|
| A variable call target is resolved only from VALUE clauses and literal MOVEs in the same program | This is why the call at PGMMAIN line 9 is open. The program has neither. | `app/cbl/PGMMAIN.cbl:9` |
| A called subprogram gets no DDs from its caller's JCL step | Whatever PGMMAIN calls has no DD mapping in the graph. | `app/jcl/MAINJOB.jcl:2` |
| Only Control-M XML and shell wrappers that name JCL files are read as schedulers | No scheduler was read. Job order across jobs is unknown. | `analysis` |
| IF/THEN/ELSE and COND= in JCL are not modeled | MAINJOB has none, so this limit does not change the result. | `app/jcl/MAINJOB.jcl:1` |
| JCL text inside a COBOL literal makes no edge | None was found (`analysis`, field `embedded_jcl` is empty). | `analysis` |

## Files

| File | Content |
|---|---|
| `01-inventory.md`, `02a-edge-tables.md`, `03a-wave-seed.md`, `05a-dead-code-candidates.md` | generated from `graph.json` |
| `02-coupling.md`, `03-waves.md`, `04-estimate.md`, `05-dead-code.md`, `06-test-strategy.md` | the argument |
| `graph.json`, `waves.json`, `dead-code.json`, `risks.json` | machine outputs, all validated |
