# 03 Waves

Target state: `refactor` (given as a flag). The plan is in `modernization-assessment/waves.json`. The
extractor's seed is `03a-wave-seed.md`. I kept it as it was. There are no deviations
(`modernization-assessment/waves.json:25`).

## The plan

| Wave | Family | Units | Blast radius | Confidence | Evidence |
|---|---|---|---|---|---|
| 1 | batch-readonly | `job:MAINJOB`, `PGMMAIN` | high | low | `app/jcl/MAINJOB.jcl:1`, `app/cbl/PGMMAIN.cbl:9` |
| not placed | none | `HIDDEN01` | low | low | `app/cbl/HIDDEN01.cbl:1` |

One wave, because the tree has one entry point (`analysis`, field `entry_points`, lists only
`job:MAINJOB`). No family other than batch-readonly is present. Waves 2 to 7 of the fixed family order
are empty, and I did not invent any.

## Why wave 1 is one wave, and why its confidence is low

Confidence cannot be `high`: `03a-wave-seed.md` lists `PGMMAIN` as holding a computed call. The call
at `app/cbl/PGMMAIN.cbl:9` names a program the source does not show, so the wave could reach any
program. I set `low`, not `medium`, for two further reasons.

1. The family name says read-only. The extractor put the job there because it found no data edge
   (`analysis`, field `data_hubs` is empty). It did not prove that nothing writes. The callee is
   unbounded, and it is where any write would happen. `inference`
2. The tree does not show that `job:MAINJOB` is the nightly batch cycle that must not break. There is
   no scheduler (`analysis`, field `warnings`). `inference`

## The four tests for a valid wave

| Test | Result | Confidence | Evidence |
|---|---|---|---|
| Deploys independently, behind a flag or facade | Yes for the job. Run the legacy job or the port from a switch in the caller. A facade is needed around the computed CALL, because its target set is open | medium | `app/jcl/MAINJOB.jcl:2` |
| Rolls back independently | Yes. Rerun the legacy JCL. Nothing in the tree is written by the job, so there is no state to unwind. Whatever the callee writes is unknown | medium | `app/jcl/MAINJOB.jcl:2` |
| Has a testable boundary | Weak. Neither program writes a file or a report. The only visible output is the job return code. The rest depends on the callee | low | `app/cbl/PGMMAIN.cbl:10` |
| Delivers something a stakeholder can name | Only if `job:MAINJOB` is the nightly batch cycle. The tree does not show it | low | `inference` |

Two of the four tests are met with medium confidence and two are open. Wave 1 is a candidate wave.
It becomes a valid wave when the callee set is named and the boundary has an output to compare.

## What wave 1 unblocks

Nothing inside this tree. No unit calls, reads from or runs after these two: there are no `data`,
`contract` or `temporal` edges (`analysis`, field `edge_counts`). By the skill's own test a wave that
unblocks nothing is a chore, and this is one. Its worth is discovery. It forces the client to say
what `WS-PGM-NAME` holds in production (`app/cbl/PGMMAIN.cbl:8`) and what else the nightly cycle
contains.

## Risk quadrants against the plan

| Unit | Port difficulty | Blast radius | Quadrant | Wave | Confidence | Evidence |
|---|---|---|---|---|---|---|
| `PGMMAIN` | 3 | 4 | high-high | 1 | low | `modernization-assessment/risks.json:13` |
| `job:MAINJOB` | 1 | 4 | low-high | 1 | medium | `modernization-assessment/risks.json:34` |
| `HIDDEN01` | 1 | 2 | low-low | none | medium | `modernization-assessment/risks.json:55` |

`PGMMAIN` is high-high and sits in the first (and only) wave. The skill says a high-high unit goes as
late as dependencies allow. It is already in the last wave there is, so I did not move it. It should
be strangled behind a facade rather than ported wholesale: the facade is the interface the computed
CALL dispatches through, and the port cannot be tested at its edge until that interface lists the
programs it can reach. `inference`

`HIDDEN01` is low-low, which the quadrant rules would put in wave 1. It has no static path from any
entry point, so the seed did not place it. Placing it would assert that it runs, which the tree does
not show. It stays unplaced (`modernization-assessment/waves.json:19`). If the run-time input names
it, it moves with wave 1.

## Not placed

| Unit | Reason | Confidence | Evidence |
|---|---|---|---|
| `HIDDEN01` | No static edge reaches it. The computed CALL could target it. It moves with wave 1 if the run-time input names it | low | `app/cbl/PGMMAIN.cbl:9` |

## Deviations from the seed

None. The seed put both reachable units in wave 1 and `HIDDEN01` in not-placed. None of the four
reasons for a change applies: no must-not-break mapping forces a move, there is no strongly connected
component, the wave holds two units, nothing was unparsed, and there is no embedded JCL
(`analysis`, fields `sccs`, `embedded_jcl`, `runtime_named`). A computed call exists, but it does
not change what a placed unit is. It only makes wave 1 low confidence.
