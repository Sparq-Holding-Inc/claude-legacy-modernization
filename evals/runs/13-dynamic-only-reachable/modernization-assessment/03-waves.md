# 03 Waves

Target state: refactor. The plan was cut from `03a-waves-draft.json`. The result is in
`waves.json`. No unit was moved, so `deviations` is empty.

## Plan

| Wave | Family | Units | Unblocks | Blast radius | Confidence | Evidence |
|---|---|---|---|---|---|---|
| 1 | batch-readonly | PGMMAIN, job:MAINJOB | Nothing the graph shows. A chore that proves the toolchain and the harness, and forces the callee question. | medium | low | `app/jcl/MAINJOB.jcl:1`, `app/cbl/PGMMAIN.cbl:9` |
| not placed | none | HIDDEN01 | It must move with wave 1 if PGMMAIN dispatches to it. | low | low | `app/cbl/HIDDEN01.cbl:1` |

## Wave 1. Program dispatcher batch job

- **Why the family holds.** The extractor found no dataset edge for the job, so the seed put it in
  the read-only batch family. That is a fact about the edges it could see (`analysis`, field
  `wave_seed`).
- **Why the family is weaker than it looks.** PGMMAIN calls a program chosen at run time
  (`app/cbl/PGMMAIN.cbl:9`). What the job really writes depends on that program. The family name is
  a claim the tree cannot support alone. The wave blast radius is therefore set to medium and the
  confidence to low, above what the seed would give. This is inference.
- **What it unblocks.** Nothing that the graph shows. There are no shared datasets, no shared
  copybooks and no callers. It proves the toolchain and the equivalence harness on the smallest
  possible unit, and it forces the answer to what PGMMAIN dispatches to. That answer is what unblocks
  every later wave.
- **The four validity tests.**

| Test | Holds | Evidence |
|---|---|---|
| Deployable independently, behind a flag or facade | Yes for MAINJOB and PGMMAIN as written. A dispatch registry facade is needed for the callees. | `app/cbl/PGMMAIN.cbl:9` |
| Rollback independently | Yes. No writes are visible. The dispatched program may write, so this holds only if it is in the tree or the same wave. | inference |
| Testable boundary | Yes at the job's outputs and return code. It needs the production input for the ACCEPT. | `app/cbl/PGMMAIN.cbl:8` |
| Delivers something a stakeholder can name | Partly. The must-not-break item is "the nightly batch cycle", and nothing in the tree ties MAINJOB to it. | inference |

## Not placed

HIDDEN01 stays in `unassigned`. No static path reaches it (`analysis`, field `dead_code_candidates`),
and the computed call at `app/cbl/PGMMAIN.cbl:9` could. If the client confirms it is a dispatch
target, it moves with wave 1, because a port of PGMMAIN without it breaks the dispatch. Its four
lines are a bare GOBACK (`app/cbl/HIDDEN01.cbl:4`), so moving it costs nearly nothing.

## Deviations

None. A plan with no deviations is a fine answer for a tree this size. The single reason to move
anything would be to place HIDDEN01 in wave 1, and that would assert a call the source does not
prove.

## Waves not needed

One wave holds every placed unit, and there is no SCC or articulation point to cut on. Splitting the
job from its program would be inventing a wave for tidiness.

## Where this plan may be wrong

If PGMMAIN dispatches to programs that are not in this tree, those programs are units that this plan
does not have, and they may write shared data, touch DB2, or run only at fiscal close. Waves 2 and
up would then exist, and wave 1 would be blocked until they were known. This is inference.
