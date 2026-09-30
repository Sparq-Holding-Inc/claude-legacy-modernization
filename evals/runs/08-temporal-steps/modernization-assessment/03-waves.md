# 03 Waves

Target state: refactor, from the `--target` flag. The plan is in `modernization-assessment/waves.json`. The
risk scores are in `modernization-assessment/risks.json`.

## The plan: one wave

| Wave | Family | Units | Blast radius | Confidence | Unblocks | Evidence |
|---|---|---|---|---|---|---|
| 1 | batch-readonly | `PGMA`, `PGMB`, `PGMC`, `job:SEQJOB` | medium | medium | nothing in the tree | `app/jcl/SEQJOB.jcl:1` |

I kept the extractor's seed as it is (`03a-wave-seed.md`). I made no deviation, and the `deviations` list in
`modernization-assessment/waves.json` is empty. A plan with no deviations is a fine answer.

### Why one wave is the honest answer

- The tree has one entry point (`analysis` field `entry_points`: `job:SEQJOB`). Every program is reached
  only through it (`app/jcl/SEQJOB.jcl:2`, `app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:4`).
- There is no dataset, so nothing is shared. There is no call between programs. There is no strongly
  connected component, no god module and no articulation point (`analysis` fields `sccs`, `god_modules`,
  `articulation_points`).
- The 25 unit rule for a cut does not apply. The wave has four units.
- No must-not-break item, no facade dependency and no computed call moves a unit. There are no computed
  calls (`analysis` field `unresolved_dynamic`). So no reason to change the seed exists that I can cite.
- Splitting the three programs into three waves would be invented waves. Nothing in the tree gives each a
  boundary a test could hold. The only boundary is the job.

### The four wave tests

| Test | Result | Confidence | Evidence |
|---|---|---|---|
| Deploys independently, behind a flag or a facade | Yes, by keeping the old JCL job beside the new one and switching at the job. The step order must be kept. | medium | inference, from `app/jcl/SEQJOB.jcl:2` to `app/jcl/SEQJOB.jcl:5` |
| Rolls back independently | Yes, by running the old job again. Only true if the job writes no data the new one has already changed. The tree shows no data, so this cannot be checked. | low | inference |
| Has a testable boundary | Weakly. The boundary is the job's step order and return codes. The tree holds no dataset, so the output oracle has to come from outside it (`06-test-strategy.md`). | low | `app/jcl/SEQJOB.jcl:2`, `app/jcl/SEQJOB.jcl:5` |
| Delivers something a stakeholder can name | Only if SEQJOB is the nightly batch cycle the client named. Nothing in the tree says it is. | low | inference |

## What the wave holds, and what is odd about it

- `PGMA`, `PGMB` and `PGMC` each hold only `GOBACK` (`app/cbl/PGMA.cbl:4`, `app/cbl/PGMB.cbl:4`,
  `app/cbl/PGMC.cbl:4`). Port difficulty is 1 for each.
- `job:SEQJOB` uses the step name STEP2 twice. The first is PGMB (`app/jcl/SEQJOB.jcl:3`). The second runs
  IEFBR14 after STEP3 (`app/jcl/SEQJOB.jcl:5`). The extractor calls the second one `STEP2#2` and orders it
  last by file order (`app/jcl/SEQJOB.jcl:4`, `app/jcl/SEQJOB.jcl:5`). The port must decide how to handle
  the collision. It is the one real design choice in this wave.
- The IEFBR14 step has no DD statement anywhere in the job (`app/jcl/SEQJOB.jcl:5`), so in this copy it
  does nothing. Whether it did something in production is an open question.
- The family is called `batch-readonly` because the extractor found no shared write. The tree has no DD at
  all, so this is an absence of evidence and not a proof that the job only reads.

## The must-not-break item

The client said the nightly batch cycle must not break. Nothing in the tree carries a schedule, a calendar or
the word nightly, and no scheduler was parsed (`analysis` field `warnings`). SEQJOB is the only job, so it is
the only candidate, and I have not treated the mapping as settled. A cycle is usually several jobs, and one
job cannot be the cycle. It is an open question, and it is item 1 in `00-summary.md`.

## Risk quadrants

| Unit | Port difficulty | Blast radius | Quadrant | Confidence | Evidence |
|---|---|---|---|---|---|
| `PGMA` | 1 | 2 | low-low | medium | `app/cbl/PGMA.cbl:4` |
| `PGMB` | 1 | 2 | low-low | medium | `app/cbl/PGMB.cbl:4` |
| `PGMC` | 1 | 2 | low-low | medium | `app/cbl/PGMC.cbl:4` |
| `job:SEQJOB` | 2 | 3 | low-high | low | `app/jcl/SEQJOB.jcl:5` |

`job:SEQJOB` is low-high. The port is easy and the verification is the work, so it waits for a proven
equivalence harness. It cannot go last, because there is no later wave to hold it. No unit is high-high, so
rule 4 for moving a unit does not apply.

## Do not port

Nothing is listed in `do_not_port`. The IEFBR14 step is a candidate for retirement, since it does nothing in
this copy (`app/jcl/SEQJOB.jcl:5`), but that is for the client to confirm.

## What would change this plan

- The client supplies the real source. If the programs do real work, they will have data, and the plan may
  need several waves.
- The client supplies a scheduler export that shows the rest of the nightly cycle. Other jobs may share data
  with SEQJOB. That would add coupling and could split the plan.
- The client says the repeated step name is a defect in this copy. Then the collision rule is moot.
