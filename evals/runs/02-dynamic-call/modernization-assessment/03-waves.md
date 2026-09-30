# 03 Waves

Target state: refactor (given as a flag). Risk scores are in `risks.json`. The plan is in `waves.json`.

## The answer: one wave

The tree is two programs and 14 lines, with no job, no dataset and no scheduler entry (`graph.json` `meta.files_seen`). There is nothing to cut. This is one wave. I did not invent a second.

| Wave | Units | Blast radius | Confidence | Unblocks | Evidence |
|---|---|---|---|---|---|
| 1 | PROGB, then PROGA | medium | low | The dispatch mechanism that replaces the computed CALL, which every program PROGA can reach depends on | `app/cbl/PROGA.cbl:9` |

## Order inside the wave

| Step | Unit | Quadrant | Why here | Evidence |
|---|---|---|---|---|
| 1 | PROGB | low-low | One statement. It proves the toolchain and the harness on something that cannot hurt the nightly batch cycle. | `app/cbl/PROGB.cbl:4` |
| 2 | PROGA | low-high | The port is easy. The verification is the work, because its behavior is decided by an input card outside the tree. Do it once the harness is proven on PROGB. | `app/cbl/PROGA.cbl:9` |

## The four tests for a valid wave

| Test | Holds? | Evidence |
|---|---|---|
| Deployed independently behind a flag or facade | Probably. Route the job step to the new module, keep the old load module in place. | inference |
| Rolled back independently | Probably. Repoint the step at the old load module. | inference |
| Testable boundary | Yes, in principle: the step's return code and whatever the named target writes. The outputs are unknown, because the targets and the JCL are not in the tree. | `app/cbl/PROGA.cbl:9` |
| Delivers something a stakeholder can name | Not shown. Nothing in the tree ties either program to the nightly batch cycle, the one thing that must not break. | inference |

The fourth test is the weak one. I keep the wave because there is nothing to merge it into. The plan is provisional until the client supplies the job that runs PROGA.

## If the system were ten times larger

I would cut by dispatch target. The dispatcher and the one or two smallest targets go first, to fix the replacement for the computed CALL and prove the harness. Then one wave per family of targets, ordered by the quadrants in `risks.json`: low-low first, high-low next, low-high once the harness is proven, and high-high last behind a facade. Any target that shares a file with another would move with it. This is inference, because the tree holds no targets.

## Rollback

The old load modules stay deployed. The step's program name is switched back. There is no data to reverse, because neither program touches a dataset (`graph.json` has no `data` edges). Whatever the named target writes is not covered here. It belongs to that target's own wave.
