# 03 Waves

Starting point: `modernization-assessment/03a-wave-seed.md` and `modernization-assessment/03a-waves-draft.json`.
Target state: refactor (given as a flag). The plan is in `modernization-assessment/waves.json`.

## Wave count: 1

| Wave | Family | Units | Blast radius | Confidence | Evidence |
|---|---|---|---|---|---|
| 1 | batch-readonly | PGMA, PGMB, PGMC, job:SEQJOB | medium | low | `app/jcl/SEQJOB.jcl:1` |

## Why one wave

The seed placed every unit in one family, and I kept it. There is one entry point, `job:SEQJOB`.
There is no strongly connected component, no articulation point and no dataset that a second entry
point uses (`analysis` fields `sccs`, `articulation_points`, `data_hubs`). No cut can be argued from
the evidence. Splitting the three programs into separate waves would break the step order that ties
them (`app/jcl/SEQJOB.jcl:2`, `app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:4`).

The four tests for a wave:

| Test | Result | Confidence | Evidence |
|---|---|---|---|
| Deployed independently | Yes. It is one job. | medium | `app/jcl/SEQJOB.jcl:1` |
| Rolled back independently | Yes. Keep the old job and switch back. | medium | inference |
| Testable boundary | Yes, but only at step order and return codes, because no dataset exists. | medium | `app/cbl/PGMA.cbl:4` |
| Nameable by a stakeholder | Only if SEQJOB is the nightly batch cycle. Nothing in the tree says so. | low | inference |

## What wave 1 unblocks

Nothing else in this tree. It is the whole system. It proves the toolchain and the job order. Beyond
that it is a chore until the real program bodies and the scheduler export arrive.

## The must-not-break item

The client named "the nightly batch cycle". No job, scheduler entry or comment in the tree carries
that name. I take `job:SEQJOB` to be it because it is the only job and the only entry point. That
is inference, and the first open question asks the client to confirm it.

## Deviations from the seed

None. The plan has no deviation.

## Duplicate step name

`app/jcl/SEQJOB.jcl:3` and `app/jcl/SEQJOB.jcl:5` both declare STEP2. The extractor called the second
`STEP2#2` and put it last. If the job is a real one, a port must decide what STEP2 means. If the
IEFBR14 step is a leftover, it can go. Both readings are inference, so this is a question for the
client's engineers, not a finding.
