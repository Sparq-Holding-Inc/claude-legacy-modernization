# 03 Waves

Target state: `refactor`. It was given as a flag. The seed is in `03a-wave-seed.md` and the plan is in
`modernization-assessment/waves.json`.

## The plan

| Wave | Family | Name | Units | Blast radius | Confidence | Evidence |
|---|---|---|---|---|---|---|
| 1 | batch-utility | Nightly batch cycle and its wrapper | job:JOBA, job:JOBB, job:JOBC, sch:scripts/nightly.sh | medium | low | `jcl/JOBA.jcl:1`, `jcl/JOBB.jcl:1`, `jcl/JOBC.jcl:1` |

One wave. The seed put every entry point in the first family, batch jobs that run no application
program and touch no shared data. Families 2 to 7 are empty. Every unit is placed. There are no
deviations, and that is a fine answer here: no unit had a reason the skill counts as one.

## The four tests

| Test | Result | Evidence |
|---|---|---|
| Deployed independently, behind a flag or facade | Yes. No shared dataset or program ties the wave to anything outside it, because it is the whole tree. The flag is the wrapper: point the nightly trigger at the old or the new chain. | `scripts/nightly.sh:4` |
| Rolled back independently | Yes, by pointing the trigger back at the old wrapper. Inference: it depends on how the client's scheduler starts the wrapper, which is not in the tree. | inference |
| Testable boundary | Yes. Assert job order and return codes at the wrapper edge. See `06-test-strategy.md`. | `scripts/nightly.sh:5` |
| Delivers something a stakeholder can name | Yes: "the nightly batch cycle runs on the target platform in the same order". | `scripts/nightly.sh:2` |

## What the wave unblocks

Nothing else in this tree. It is the whole tree, so this wave is a chore that carries the
must-not-break item. What it proves is that the target scheduler can hold the JOBA-then-JOBB order.
It cannot prove the toolchain on real logic, because the tree holds none.

## Why this family is sound, and where it is not

Sound: the three jobs share no dataset, no copybook and no program, so no call, data or contract edge
crosses the wave boundary. The seed's tests all agree.

Not proven: the tree shows three no-op jobs. If production JCL is richer than the tree, the seed
would put those jobs in later families, and the wave count would change. Inference.

## Must-not-break: the nightly batch cycle

The cycle is the wrapper and the two jobs it submits: `scripts/nightly.sh:4` and `scripts/nightly.sh:5`.
They are the equivalence anchors. The one ordering fact the harness must keep is JOBA before JOBB.

## JOBC

JOBC stays in wave 1 as the seed placed it. The extractor counts every job as an entry point and finds
no scheduler that names it. The wrapper calls it retired at `scripts/nightly.sh:2` and does not submit it at
`scripts/nightly.sh:6`. That is a comment. Telemetry is `none` and only one scheduler was parsed, so I did
not drop JOBC from the plan or call it dead. It is in `do_not_port` in `risks.json` as a provisional
entry: confirm, then retire it. Porting it would cost almost nothing, which makes leaving it in the
safe error.

## Units not placed

None.

## Deviations from the seed

None.
