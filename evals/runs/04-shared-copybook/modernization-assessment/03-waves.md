# 03 Waves

Target state: `refactor`. The plan is in `waves.json`. The extractor's seed is in `03a-wave-seed.md`.

## What the seed produced

The seed placed nothing. Every family is empty, because the tree has no entry point (`analysis`, field `wave_seed`). PROGA and PROGB came back as not placed.

## The plan

`schema.py` rejects a plan with no waves. So the plan holds one provisional wave. This is a deviation from the seed. It is recorded in `waves.json` under `deviations`. It is not a finding that these programs belong first.

| Wave | Name | Units | Blast radius | Confidence | Unblocks | Evidence |
|---|---|---|---|---|---|---|
| 1 | Shared copybook pair (provisional) | PROGA, PROGB | low | low | Nothing that can be shown from this tree. This is a chore wave. | `app/cbl/PROGA.cbl:5`, `app/cbl/PROGB.cbl:5` |

Why one wave and not two: both programs include SHARED01, so a change to the layout reaches both. They should move together. Both score low-low in `risks.json`, which is the wave one profile (`modernization-assessment/risks.json:1`).

The wave does not meet the four validity tests. The tree cannot show that it deploys independently, that it rolls back independently, that its boundary is testable, or that a stakeholder can name what it delivers. There is no JCL, no scheduler and no dataset to hang a boundary on. Until the client supplies the nightly batch cycle, the plan is a placeholder.

## Deviations from the seed

| Unit | From | To | Reason | Evidence |
|---|---|---|---|---|
| PROGA | not placed | wave 1 | The validator needs at least one wave, and the program shares SHARED01 with PROGB. | `app/cbl/PROGA.cbl:5` |
| PROGB | not placed | wave 1 | The validator needs at least one wave, and the program shares SHARED01 with PROGA. | `app/cbl/PROGB.cbl:5` |

## What would change this plan

- A JCL job or scheduler entry that runs either program would give it a family. The seed would then place it in a real wave.
- A dataset written by one program and read by the other would add a contract edge. That would tie them more tightly, and it would need its own layout check.
- If the nightly batch cycle runs either program, the cycle is a must-not-break item. It would force both programs behind the same equivalence harness before any port. See `06-test-strategy.md`.
