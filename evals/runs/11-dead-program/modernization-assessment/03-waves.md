# 03 Waves

Target state: **refactor** (given by `--target refactor`). The machine-readable plan is `modernization-assessment/waves.json`. It starts from the extractor's seed in `03a-wave-seed.md`.

## The plan

One wave. The extractor put the only entry point, `job:MAINJOB`, in the `batch-readonly` family. That is the first of the seven fixed families, and the others are empty (analysis: `wave_seed`).

| Wave | Family | Units | Blast radius | Confidence | Evidence |
|---|---|---|---|---|---|
| 1 | batch-readonly | `job:MAINJOB`, `PGMMAIN`, `PGMLIVE` | low | medium | `app/jcl/MAINJOB.jcl:1` |

Not placed: `PGMDEAD`. It is unreachable, so it is not ported. See `05-dead-code.md`. The copybook `cpy:UNUSED` is unreferenced and has no owner to move with.

## Why one wave is the honest answer

I did not invent a second wave. A cut needs a reason I can cite, and none of the four reasons in the skill applies.

- **A must-not-break item, a strongly connected component or a facade dependency forces a move.** No strongly connected component exists (analysis: `sccs`). The one must-not-break item, "the nightly batch cycle", cannot be tied to a unit with evidence, since the only job in the tree is `job:MAINJOB` and no scheduler names it. I treat the job as the likely holder of that cycle. That is inference.
- **A wave holds more than 25 units.** It holds three.
- **Something the extractor could not see changes what a unit is.** No computed call and no embedded JCL exist (analysis: `unresolved_dynamic`, `embedded_jcl`).
- **`risks.json` puts a unit in high-high and its family puts it early.** No unit is high-high. The scores are low-low for both programs and low-high for the job (`modernization-assessment/risks.json:2`).

Deviations from the seed: none. A plan with no deviations is a fine answer.

## Wave 1. Nightly batch job, whole tree

| Test | Holds? | Confidence | Evidence |
|---|---|---|---|
| Deploys independently, behind a flag or facade | Yes. The job is the only entry point and touches no shared data, so a second copy of the job can run beside the old one | medium | `app/jcl/MAINJOB.jcl:2` |
| Rolls back independently | Yes. It writes no dataset, so there is nothing to undo | medium | `app/cbl/PGMMAIN.cbl:4` |
| Has a testable boundary | Weakly. There is no dataset to compare, so the boundary is the job return code, the job log and what the real job writes | low | inference |
| Delivers something a stakeholder can name | Only if `job:MAINJOB` is the nightly batch cycle. If it is, the wave is that cycle. If not, it is a toolchain proof | low | inference |

**Unblocks.** Nothing else in the tree depends on this wave. On this evidence it is a chore: it proves the toolchain and the harness. If the real nightly cycle has more jobs than this tree shows, the plan needs a second look, and this wave becomes the first of several.

**Order inside the wave.** Port the leaf first, then its caller, then the job.

1. PGMLIVE (`app/cbl/PGMLIVE.cbl:4`)
2. PGMMAIN (`app/cbl/PGMMAIN.cbl:4`)
3. `job:MAINJOB` step S1 (`app/jcl/MAINJOB.jcl:2`)

**Rollback.** Keep the legacy job. Run the ported job beside it. Switch the scheduler entry for `job:MAINJOB` between the two. Rolling back is a scheduler change. The scheduler export is not in the tree, so this procedure is inference until someone supplies it.

## What I would put behind a facade

Nothing. No unit is high-high, and no god module exists (analysis: `god_modules`).
