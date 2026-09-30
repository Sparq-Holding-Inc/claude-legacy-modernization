# 03 Waves

Target state: refactor. The plan is in `modernization-assessment/waves.json`. It starts from the extractor's
seed (`modernization-assessment/03a-wave-seed.md`) and changes nothing. There are no deviations.

## The plan

| Wave | Family | Name | Units | Blast radius | Confidence | Evidence |
|---|---|---|---|---|---|---|
| 1 | batch-readonly | The one batch chain | `job:MAINJOB`, `PGMMAIN`, `PGMLIVE` | medium | medium | `app/jcl/MAINJOB.jcl:1`, `app/jcl/MAINJOB.jcl:2`, `app/cbl/PGMMAIN.cbl:4` |

One wave. The seed's other six families are empty. This tree has one entry point and it touches no shared
data, so there is nothing to sequence. I did not invent waves to fill the families. The only way to get a
second wave would be to cut a three-unit chain that one sentence describes.

## Why wave 1 stands, and where it is weak

The four tests for a valid wave:

| Test | Result | Confidence | Evidence |
|---|---|---|---|
| Deploys independently, behind a flag or facade | Yes. The job is the switch: run the legacy job or the ported job. The switch itself lives in a scheduler the tree does not hold. | medium | `app/jcl/MAINJOB.jcl:2`, analysis: `warnings` names the missing scheduler |
| Rolls back independently | Yes. Nothing else in the tree reads or writes anything this wave produces. | medium | analysis: `data_hubs` and `contract` edges are empty |
| Has a testable boundary | Weakly. The job has no DD statement, so its only observable output is its return code and log. See `modernization-assessment/06-test-strategy.md`. | low | `app/jcl/MAINJOB.jcl:2` |
| Delivers something a stakeholder can name | Only if the client confirms `job:MAINJOB` is the nightly batch cycle. Nothing in the tree says it is nightly. | low | inference |

The plan does not decide the fourth test. It is the first open question for the client.

## What wave 1 unblocks

Nothing inside the tree. No live unit outside the wave depends on it, and the only other caller of `PGMLIVE`
is `PGMDEAD`, which is unreachable (`app/cbl/PGMDEAD.cbl:4`). Until the client confirms the nightly batch
cycle maps to `job:MAINJOB`, wave 1 is a chore. Its value is proving the port toolchain and the
job-level comparison harness. Inference.

## Risk quadrants against the plan

| Unit | Port difficulty | Blast radius | Quadrant | Confidence | Evidence |
|---|---|---|---|---|---|
| `PGMMAIN` | 1 | 2 | low-low | medium | `app/cbl/PGMMAIN.cbl:4` |
| `PGMLIVE` | 1 | 2 | low-low | medium | `app/cbl/PGMLIVE.cbl:4` |
| `job:MAINJOB` | 1 | 3 | low-high | low | `app/jcl/MAINJOB.jcl:1` |

No unit is high-high, so no risk-based move applies. `job:MAINJOB` is low-high: the port is easy and the
verification is the work. That is why the harness is proven inside the wave before the cutover, not after.
Both axes come from `modernization-assessment/risks.json`, which the risk scoring produced. No combined
score exists, by design.

## Not placed

| Unit | Reason | Confidence | Evidence |
|---|---|---|---|
| `PGMDEAD` | Unreachable. No JCL step, scheduler entry or program runs it and the tree has no computed calls. Proposed for deletion, not for a wave. | medium | `app/cbl/PGMDEAD.cbl:4` |
| `cpy:UNUSED` | A copybook with no includer has no owner to move with. It is not a unit. It is in the dead-code register. | high | `app/cpy/UNUSED.cpy:1` |

If `PGMDEAD` turns out to run, it joins wave 1. It only calls `PGMLIVE`, so no other wave would change.

## Deviations from the seed

None. A plan with no deviations is a fine answer here. No must-not-break item, strongly connected component,
facade dependency, computed call or unparsed file forces a unit into another wave
(analysis: `sccs`, `unresolved_dynamic` and `unparsed` are all empty). No wave holds more than 25 units.
