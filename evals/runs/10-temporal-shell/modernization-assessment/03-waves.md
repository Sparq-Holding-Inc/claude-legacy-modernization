# 03 Waves

Target state: refactor. The plan is in `modernization-assessment/waves.json`. It holds one wave and no deviations from the extractor's seed.

## Wave table

| Wave | Name | Units | Blast radius | Confidence | Unblocks | Evidence |
|---|---|---|---|---|---|---|
| 1 | Nightly batch cycle | `job:JOBA`, `job:JOBB`, `job:JOBC`, `sch:scripts/nightly.sh` | low | low | Nothing in this tree | `jcl/JOBA.jcl:1`, `jcl/JOBB.jcl:1`, `jcl/JOBC.jcl:1`, `scripts/nightly.sh:4` |

## Why one wave

All four units sit in the family "batch jobs that run no application program and touch no shared data" (`analysis`: `wave_seed`). Each job runs only IEFBR14 (`jcl/JOBA.jcl:2`). One sentence describes the wave, so no cut is warranted. No articulation point exists to cut at (`analysis`: `articulation_points`).

The four validity tests:

| Test | Result | Confidence | Evidence |
|---|---|---|---|
| Deploys independently | Yes, behind the wrapper: swap what `submit` calls for JOBA and JOBB | low (inference) | `scripts/nightly.sh:4`, `scripts/nightly.sh:5` |
| Rolls back independently | Yes, re-point the wrapper at the old JCL | low (inference) | `scripts/nightly.sh:4` |
| Testable boundary | Weak. The jobs write nothing in the tree, so the boundary is return codes and whatever IEFBR14 allocates or deletes. The tree does not show that. | low | `jcl/JOBA.jcl:2` |
| Names a business deliverable | Yes by name only: "the nightly batch cycle" is the must-not-break item. What it produces is not in the tree. | low | `scripts/nightly.sh:2` |

The wave holds a computed-call count of zero (`03a-wave-seed.md`), but confidence is still `low`: the content of the cycle is unknown, not simple.

## What each unit is

| Unit | Treatment | Evidence |
|---|---|---|
| `job:JOBA` | Port first. Submitted first. | `scripts/nightly.sh:4` |
| `job:JOBB` | Port second. Order after JOBA must hold. | `scripts/nightly.sh:5` |
| `sch:scripts/nightly.sh` | The scheduler. It is replaced, and its order and `set -e` behavior become the new scheduler's dependency and failure rules. | `scripts/nightly.sh:3` |
| `job:JOBC` | Do not port. Retire once the client confirms, then delete the file. | `scripts/nightly.sh:2`, `scripts/nightly.sh:6` |

## Deviations from the seed

None.

## Unplaced units

None.
