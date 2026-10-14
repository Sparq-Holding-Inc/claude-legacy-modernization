# 03 Waves

Target state: refactor. The plan is `waves.json`. It has no deviations from the extractor's seed (`03a-wave-seed.md`).

| Wave | Name | Units | Blast radius | Confidence | Evidence |
|---|---|---|---|---|---|
| 1 | Nightly batch cycle | `job:MAINJOB`, `PGMMAIN`, `PGMLIVE` | low | medium | `app/jcl/MAINJOB.jcl:2`, `app/cbl/PGMMAIN.cbl:4` |

## Wave 1. Nightly batch cycle

One entry point, no shared data, no computed calls, so one wave is the honest answer. Splitting three units would create waves that are not independently deployable or testable. It meets the four validity tests: it can sit behind a flag at the job level, roll back by re-running the legacy job, assert equivalence at the job's outputs, and the business can name it as the nightly batch cycle.

Confidence is medium, not high, because the supplied programs contain no logic (`app/cbl/PGMLIVE.cbl:4`) and no scheduler was parsed.

It unblocks the retirement of the legacy runtime and nothing else in this tree.

## Not placed

| Unit | Reason | Evidence |
|---|---|---|
| `PGMDEAD` | Unreachable. Not ported. | `app/cbl/PGMDEAD.cbl:4` |
