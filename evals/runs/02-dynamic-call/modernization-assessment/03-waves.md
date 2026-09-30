# 03 Waves

Target state: refactor. The plan is in `modernization-assessment/waves.json`.

## What the seed gave

The extractor's seed put no unit in any wave. The tree has no JCL job, scheduler job, CSD transaction or shell wrapper, so there is no entry point, and the seed places a unit only by the family of the entry points that use it (`03a-wave-seed.md`). Both programs came back as not placed, because a computed call could reach them (analysis field `wave_seed`, `app/cbl/PROGA.cbl:9`).

## The plan

| Wave | Units | Family | Blast radius | Confidence | Evidence |
|---|---|---|---|---|---|
| 1 | PROGA, PROGB | none. The seed placed nothing. | high | low | `modernization-assessment/waves.json:5`, `app/cbl/PROGA.cbl:9`. Inference: the grouping is forced, not derived from a family. |

One wave. I did not cut more, because nothing in the graph supports a cut: no strongly connected component, no articulation point and no god module (`02-coupling.md`).

Why the wave exists at all: `schema.py` rejects a `waves.json` with an empty `waves` list, so a plan that placed no unit could not pass validation. The two programs are put together in one wave as a deviation, not because a family says so. This is a limit of the plan, not a finding about the system. A real wave plan needs the JCL and scheduler files that the tree lacks.

The four tests for a valid wave, for wave 1:

| Test | Holds? | Evidence |
|---|---|---|
| Deployable independently, behind a flag or a facade | Yes, if a program registry sits in front of the dynamic `CALL` | `app/cbl/PROGA.cbl:9`. Inference. |
| Rollback independently | Yes, since neither program writes data | inference |
| Testable boundary | Only once the `ACCEPT` input and the called program's output are captured. Not shown in the tree. | `app/cbl/PROGA.cbl:8`. Inference. |
| Delivers something a stakeholder can name | No. Nothing in the tree ties to the nightly batch cycle. This wave is a chore until the real cycle is supplied. | inference |

## What the wave unblocks

Nothing that can be shown from this tree. Its value is that the registry list it produces (every program name the input can carry) is the first input the rest of the wave plan needs. Inference.

## Where the risk quadrant and the plan disagree

`PROGA` is high-high (port difficulty 3, blast radius 4, `modernization-assessment/risks.json:5`) and it is in the only wave, so it is in the first half by default. I did not move it, because there is nowhere later to put it. Stated plainly: a high-high unit is in the first wave. What would have to sit behind a facade first is a registry that maps the run-time program name to a known target, and refuses any name not on the list. `PROGB` is low-low.

## Deviations

| Unit | From wave | To wave | Reason | Evidence |
|---|---|---|---|---|
| PROGA | not placed | 1 | The seed placed nothing because the tree has no entry point. Placed only so the plan has a wave. | `app/cbl/PROGA.cbl:9`. Inference. |
| PROGB | not placed | 1 | Kept with PROGA because the computed call could name it, so the two cannot be proven independent. | `app/cbl/PROGB.cbl:4`, `app/cbl/PROGA.cbl:9` |

## Not placed

Nothing is left in `unassigned` (`modernization-assessment/waves.json:29`).
