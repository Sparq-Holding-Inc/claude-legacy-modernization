# 03 Waves

Target state: `refactor` (given as a flag). The plan is `waves.json`. The extractor's seed was kept as it was. No deviations.

## Wave count

One wave.

| Wave | Family | Units | Blast radius | Confidence | Evidence |
|---|---|---|---|---|---|
| 1. Nightly batch cycle (JOBA then JOBB) | batch-utility | `job:JOBA`, `job:JOBB`, `sch:NIGHTLY/JOBA`, `sch:NIGHTLY/JOBB` | high | medium | `app/jcl/JOBA.jcl:1`, `app/jcl/JOBB.jcl:1`, `app/scheduler/nightly.xml:6`, `app/scheduler/nightly.xml:9` |

## Why one wave, and why it is sound

The four tests from the skill, applied to wave 1:

| Test | Result | Evidence |
|---|---|---|
| Deployed independently, behind a flag or facade | Yes, as a unit. Both JCL members and both scheduler entries move together. The tree has no other unit that calls them or shares data with them | `analysis` fields `fan_in` and `data_hubs`, both empty |
| Rolled back independently | Yes. Restore the old scheduler folder and keep the old JCL. Rollback needs the old scheduler to stay reachable, which is `inference` | inference |
| Testable boundary | Yes. The boundary is the condition chain: what starts JOBA, when JOBA-DONE is posted, when JOBB starts, when JOBA-DONE is removed, when JOBB-DONE is posted | `app/scheduler/nightly.xml:5`, `app/scheduler/nightly.xml:6`, `app/scheduler/nightly.xml:9`, `app/scheduler/nightly.xml:10`, `app/scheduler/nightly.xml:11` |
| Delivers something a stakeholder can name | Yes. The must-not-break item, "the nightly batch cycle", runs on the new platform in the same order | `app/scheduler/nightly.xml:3` |

It cannot be cut in two. The order between the jobs exists only as the condition JOBA-DONE (`app/scheduler/nightly.xml:6`, `app/scheduler/nightly.xml:9`). The extractor computed no articulation point (`analysis` field `articulation_points`), and a cut at the condition would need a bridge between two schedulers for a wave that holds two jobs.

## What the wave unblocks

Nothing else in this tree. In dependency terms it is a chore, and the plan says so. Its value is that it proves scheduler semantics (an external input, a posted condition, a consumed and deleted condition) that later waves from the wider estate will reuse. `analysis`

## Units in the wave

| Unit | What it is | Confidence | Evidence |
|---|---|---|---|
| `job:JOBA` | JCL job, one step running IEFBR14 | high | `app/jcl/JOBA.jcl:1` |
| `job:JOBB` | JCL job, one step running IEFBR14 | high | `app/jcl/JOBB.jcl:1` |
| `sch:NIGHTLY/JOBA` | Control-M job. Waits on EXTERNAL-FEED, posts JOBA-DONE | high | `app/scheduler/nightly.xml:4` |
| `sch:NIGHTLY/JOBB` | Control-M job. Waits on JOBA-DONE, deletes it, posts JOBB-DONE | high | `app/scheduler/nightly.xml:8` |

Steps (`step:JOBA.S1`, `step:JOBB.S1`) move with their jobs. `ext:IEFBR14` is a system utility outside the tree and is not a unit.

## Risk quadrant check

`risks.json` puts both jobs in `low-high`: the port is easy and being wrong is costly. The skill says that quadrant is safe early once the equivalence harness is proven. The plan puts it first because it is the only wave. The harness in `06-test-strategy.md` must be in place before this wave ships. `modernization-assessment/risks.json:13`, `modernization-assessment/risks.json:42`

## Deviations from the seed

None. A plan with no deviations is a fine answer here. The seed placed every unit and left none unassigned (`analysis` field `wave_seed`).

## What would change this plan

If the real cycle runs application programs that are not in this tree, this wave is only the scheduling layer of a larger system, and the count above is too low. That is `inference` and is the second open question in `00-summary.md`.
