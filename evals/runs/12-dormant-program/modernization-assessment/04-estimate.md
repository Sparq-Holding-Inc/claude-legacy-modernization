# 04 Estimate

Target state: refactor. There is one wave, so there is one estimate.

## Method

This is a judgment, not a model. There is no team velocity and no port history to calibrate against. I weighed the factors that move an estimate, in the order the skill lists them, and priced the work in person-days for the code in the tree. It does not price the rest of the nightly cycle, because the tree does not hold it (Open Question 1 in `00-summary.md`).

| Factor | What the tree shows | Effect on the estimate | Evidence |
|---|---|---|---|
| Coupling edges crossing the wave boundary | None. The wave holds the whole tree, and there are no data, contract or temporal edges. | Pushes the range down | `analysis` (field `edge_counts`) |
| Behavioral oracle | None in the tree. No dataset, report or log is present. | Pushes the range up. The harness is most of the work. | `app/jcl/MAINJOB.jcl:2` |
| God modules in the wave | None. | No effect | `analysis` (field `god_modules`) |
| Business logic in the database | No EXEC SQL, no DB2 table, no dataset node. | No effect here, and unknown for the real cycle | `analysis` (field `node_counts`) |
| Someone who can read the source language | Not known. | Open. Each program is short enough that any reader can check it. | inference |

## Wave 1 estimate: 3 to 8 person-days for the code in the tree

| Piece | Range | Basis | Evidence |
|---|---|---|---|
| Mechanical port of the three programs and the job step | 0.5 to 1 day | 16 lines of source in all. Nothing to translate but two CALLs, two GOBACKs and one EXEC PGM. | `app/cbl/PGMMAIN.cbl:4`, `app/jcl/MAINJOB.jcl:2` |
| Harness and oracle set-up: return codes, step execution, SYSOUT, run against the legacy job | 2 to 5 days | The oracle has to be built from job output and logs, since no dataset is named. The range is wide because the size of the archive we can get is unknown. | inference |
| Cutover and rollback runbook, one job | 0.5 to 2 days | One job is one switch. The range covers scheduler changes we cannot see. | inference |

If the client cannot supply job logs or a parallel run window, add the time to build one. I do not put a number on that, because it depends on the client's run calendar.

## The assumptions the range is most sensitive to

1. **The source is what runs.** This assumes the three programs in `app/cbl` are the deployed logic, and that each does nothing but CALL and GOBACK (`app/cbl/OLDPGM.cbl:4`, `app/cbl/NEWPGM.cbl:4`). If the load modules hold more than the source shows, the port line is void and must be re-estimated from the real source. The other two lines would then grow with it.
2. **The job has no files.** This assumes MAINJOB has no DD statements beyond what we see (`app/jcl/MAINJOB.jcl:2`). If the real job reads or writes datasets, the harness line roughly doubles, and contract edges appear that this plan does not price.
3. **MAINJOB is the whole nightly cycle.** This assumes the cycle is this one job. If it is one job in a chain, this range covers one link. It says nothing about the cycle's order across jobs (`analysis`, field `warnings`).
4. **OLDPGM stays.** This assumes OLDPGM is ported as it is, because PGMMAIN calls it unconditionally (`app/cbl/PGMMAIN.cbl:4`). If the client decides to retire it, remove a few hours from the port line and add a Deviation Register row (`06-test-strategy.md`).

## Where Claude Code can do the port, and where it cannot

| Part | Can Claude Code do it? | Evidence |
|---|---|---|
| Transliterating the two CALLs and the GOBACKs into the target language | Yes, given a working harness. This is mechanical. | `app/cbl/PGMMAIN.cbl:4` |
| Translating the EXEC PGM step into the target scheduler or orchestrator | Yes, once the target is chosen. | `app/jcl/MAINJOB.jcl:2` |
| Building the harness that runs legacy and new and diffs the outputs | Yes for the tooling. The oracle data has to come from the client. | inference |
| Working out why PGMMAIN calls both OLDPGM and NEWPGM, and what each was meant to do | No. The source holds no rule to read. The intent is in people's heads or in change records. | inference |
| Deciding what "break" means for the nightly cycle | No. That is a decision for the client. | inference |
