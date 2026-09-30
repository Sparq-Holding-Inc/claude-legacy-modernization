# 04. Estimate

Target state: refactor (`modernization-assessment/waves.json:2`).

**Do not take the number in this file to a steering committee as an estimate of the client's
modernization.** It is an estimate of porting five files. The five files on disk total 17 lines of
COBOL and copybook plus a 2-line JCL job (`analysis.node_counts`; per-node `loc` in `graph.json`:
`PGMMAIN` 5, `PGMDEAD` 5, `PGMLIVE` 4, `cpy:UNUSED` 1, `job:MAINJOB` 2). The estimate is small
because the input is small, not because the migration is easy.

## Method

Bottom-up from the coupling edges that cross each wave boundary, not from lines of code. There is
one wave and zero edges cross its boundary, because the wave contains every reachable unit and
there is no second wave to cross to. So the estimate reduces to: stand up a toolchain, transliterate
three programs and one job, prove equivalence at a very thin boundary.

Units are **engineer-days**, one engineer, assuming the target runtime and CI are not yet chosen.

## Wave 1 — The MAINJOB chain

| Activity | Low | High | Driver | Evidence | Confidence |
|---|---|---|---|---|---|
| Choose target runtime, stand up build for one COBOL load module and one job | 3 | 10 | Entirely a platform decision, not a property of this code. The range is wide because nothing in the tree constrains it. | `analysis.node_counts` | low |
| Transliterate `PGMMAIN` and `PGMLIVE` | 0.25 | 0.5 | Nine lines between them, no data division, no I/O, no arithmetic. | `app/cbl/PGMMAIN.cbl:4`, `app/cbl/PGMLIVE.cbl:4` | high |
| Port `job:MAINJOB` to the target scheduler or runner | 0.5 | 2 | One EXEC card, no DDs. High end assumes the target scheduler is new to the team. | `app/jcl/MAINJOB.jcl:2` | medium |
| Build the equivalence harness (return code + SYSOUT diff) | 1 | 3 | There is no data oracle. See `06-test-strategy.md`. High end assumes capturing a baseline run on the source platform is itself a procurement problem. | `app/cbl/PGMMAIN.cbl:3` | medium |
| Cutover, flag, rollback rehearsal | 1 | 2 | No data change to unwind. | `analysis` (`data_hubs` empty) | high |
| Resolve and delete `PGMDEAD` and `cpy:UNUSED` | 0.5 | 2 | High end is waiting for a human to confirm no external caller exists. Mostly calendar time, not effort. | `app/cbl/PGMDEAD.cbl:2`, `app/cpy/UNUSED.cpy:1` | medium |
| **Total** | **6.25** | **19.5** | Sum of the rows above | inference | low |

Call it **1.5 to 4 engineer-weeks**, and note that roughly 70% of the low end and 60% of the high
end is toolchain setup that any first wave of any size would pay once.

## The assumptions the range is most sensitive to

Stated so they can be falsified.

1. **The five files on disk are the entire scope.** If they are a fragment of a real nightly cycle —
   and a 2-line job running two `GOBACK`s almost certainly is — this estimate is wrong by whatever
   multiple the real system is larger. The single most valuable thing the client can do to improve
   this number is supply the rest of the tree. Falsifiable: ask for the JCL library listing and
   count the members. Evidence for the concern: `meta.files_seen` records 3 COBOL files, 1
   copybook, 1 JCL, 0 procs, 0 CSD, 0 Control-M, 0 shell.
2. **`PGMLIVE` and `PGMMAIN` really are no-ops and not stubs awaiting content.** Both procedure
   divisions are two statements (`app/cbl/PGMMAIN.cbl:4-5`, `app/cbl/PGMLIVE.cbl:4`). If these are
   placeholders in a repository whose real logic lives elsewhere — a load library, a copybook
   library not supplied, an include the extractor never saw — then the transliteration lines above
   are meaningless. Falsifiable: ask whether the compiled load modules match these sources.
3. **A baseline run of `MAINJOB` on the source platform can be captured.** The whole harness line
   depends on it. With no datasets, the only oracle is the job's own output
   (`analysis` — no `ds:` nodes exist). If the client cannot run the job and keep its SYSOUT, the
   harness cost goes to zero and the confidence in the port goes with it. Falsifiable: ask for one
   captured run.

## Where Claude Code can do the work and where it cannot

| Task | Claude Code? | Why | Evidence | Confidence |
|---|---|---|---|---|
| Transliterate `PGMMAIN`, `PGMLIVE` | yes, essentially free | Two statements each, no intent to infer. | `app/cbl/PGMMAIN.cbl:4`, `app/cbl/PGMLIVE.cbl:4` | high |
| Convert `job:MAINJOB` to a runner script | yes | One EXEC card, no DDs, no COND. | `app/jcl/MAINJOB.jcl:2` | high |
| Write the return-code/SYSOUT diff harness | yes | Mechanical, given one captured baseline. | `app/jcl/MAINJOB.jcl:1` | high |
| Decide whether `PGMDEAD` may be deleted | **no** | Static reachability says unreachable and there are no computed calls to undermine it (`analysis.unresolved_dynamic` empty), which is unusually strong. But "no caller in this tree" is not "no caller"; an operator-submitted job or a caller outside the supplied files would not appear. This needs a human with access to the scheduler and the JES history. | `app/cbl/PGMDEAD.cbl:2` | medium |
| Decide what the nightly batch cycle actually is | **no** | No artifact in the tree defines it. This is a conversation, not an analysis. | `analysis.warnings` | high |
| Choose the target runtime | **no** | A platform and cost decision with no technical input from this code. | `analysis.node_counts` | high |

The split is stark here because the code is trivial: everything mechanical is free, and everything
that costs money is a question for the client's engineers rather than a task for anyone's compiler.
