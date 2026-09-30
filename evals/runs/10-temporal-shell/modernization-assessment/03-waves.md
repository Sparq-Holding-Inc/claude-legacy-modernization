# 03 Waves

Target state: refactor. The plan is one wave. It is the extractor's seed with no deviation
(`03a-wave-seed.md`, `modernization-assessment/waves.json:1`). The scores that fed it are in
`modernization-assessment/risks.json:1`.

| Wave | Family | Units | Blast radius | Confidence | Evidence |
|---|---|---|---|---|---|
| 1 | batch-utility | job:JOBA, job:JOBB, job:JOBC, sch:scripts/nightly.sh | high | low | `jcl/JOBA.jcl:1`, `jcl/JOBB.jcl:1`, `jcl/JOBC.jcl:1` |

## Wave 1. Nightly batch cycle

**What it holds.** The wrapper `sch:scripts/nightly.sh` and the three jobs. Two jobs are submitted by
the wrapper, JOBA and then JOBB (`scripts/nightly.sh:4`, `scripts/nightly.sh:5`). The third, JOBC, is not.

**Why one wave is the right cut.**

- There is no shared dataset, no contract edge, no call cycle and no articulation point, so no
  structure offers a place to cut (`analysis` fields `sccs`, `data_hubs`, `articulation_points`).
- The wave has four units, far below the 25 that would need a cut.
- Splitting JOBA from JOBB would put the one temporal edge across a wave boundary
  (`scripts/nightly.sh:4`, `scripts/nightly.sh:5`), which is the failure the plan is meant to avoid.
- The nightly cycle is the must-not-break item. It maps to this wave and to nothing else. The mapping
  rests on the wrapper's own comment, "Nightly chain" (`scripts/nightly.sh:2`). It is a match on
  a name, and nothing in the tree confirms that the client means this script (inference).

**The four tests for a valid wave.**

| Test | Result | Confidence | Evidence |
|---|---|---|---|
| Deploys independently, behind a flag or facade | Yes. The new orchestration can run beside the old wrapper, and the old wrapper stays as the fallback. | medium | inference |
| Rolls back independently | Yes. Rollback means running the old wrapper again. This holds only if the jobs have no side effect the old wrapper does not undo, and the tree shows none. | medium | `jcl/JOBA.jcl:2`, `jcl/JOBB.jcl:2` |
| Has a testable boundary | Weak. The tree shows no output. The boundary is job order, return codes and whatever the client says the jobs produce. | low | `jcl/JOBA.jcl:2`, `jcl/JOBB.jcl:2` |
| Delivers something a stakeholder can name | Yes. The nightly cycle runs on the new platform and the shell wrapper is retired. | medium | inference |

**What it unblocks.** Nothing in this tree. No data, contract or call edge reaches these jobs from
another unit (`analysis.fan_in` is empty, analysis). It is a chore in sequencing terms. Its value is the
retirement of the wrapper and an order and return code harness that later additions to the tree can
reuse.

**Order of work inside the wave.** These are steps, not waves.

1. Build the order and return code harness and run it against the legacy wrapper first. Prove it on the old
   system before it judges the new one. This is the low-high rule: the port is easy and the verification
   is the work (`modernization-assessment/risks.json:4`).
2. Port the wrapper's order and stop-on-failure rule (`scripts/nightly.sh:3` through `scripts/nightly.sh:5`)
   into the target orchestration.
3. Move JOBA, then JOBB, behind the harness (`jcl/JOBA.jcl:2`, `jcl/JOBB.jcl:2`).
4. JOBC gets no port work until the client confirms whether it still runs (`scripts/nightly.sh:2`,
   `scripts/nightly.sh:6`).

**Confidence.** `low`. The membership of the wave is certain, because it comes from facts. What the wave
protects is not. Three things are not in the tree: what `submit` does, what JOBA and JOBB do in production
(they run only IEFBR14 here), and whether JOBC is retired. If any of them differs from what the tree
shows, the wave's blast radius and estimate change.

## Deviations from the seed

None. I tested each reason the skill counts as valid.

| Reason | Applies | Confidence | Evidence |
|---|---|---|---|
| Must-not-break item, SCC or facade dependency forces a unit into another wave | No. The must-not-break item is already whole in wave 1. | high | analysis field `wave_seed` |
| A wave over 25 units needs a cut | No. The wave holds 4 units. | high | analysis field `wave_seed` |
| Something the extractor could not see changes what a unit is | Considered for JOBC and rejected. The comment says it is retired, but a comment is not proof, and no other wave exists for it to join. It goes to Open Questions and to `do_not_port` as provisional. | medium | `scripts/nightly.sh:2`, `scripts/nightly.sh:6` |
| A high-high unit is placed early | No unit is high-high. The wrapper is low-high. | high | `modernization-assessment/risks.json:13` |

## Not placed

Nothing. Every unit is placed (`03a-wave-seed.md`). Steps, the external utility `ext:IEFBR14` and the
rest move with their owners.
