# 03 Waves

Target state: refactor. The plan is in `modernization-assessment/waves.json`. It starts from the extractor's seed (`03a-wave-seed.md`) and I changed nothing in it. The deviation list is empty.

## The plan

| Wave | Family | Units | Blast radius | Confidence | Unblocks | Evidence |
|---|---|---|---|---|---|---|
| 1 | batch-readonly | `PGMR`, `job:READJOB` | medium | medium | Little. Proves the toolchain. Close to a chore. | `app/jcl/READJOB.jcl:1` |
| 2 | batch-writers | `PGMW`, `job:WRITEJOB` | high | medium | Retires the legacy writer. Lets LAYOUTX and LAYOUTY become one layout. | `app/cbl/PGMW.cbl:6` |

The seed placed every unit, and no unit is unassigned.

## Why these two waves

**Wave 1, the reader.** READJOB runs PGMR (`app/jcl/READJOB.jcl:2`). PGMR reads the dataset and writes nothing (`app/cbl/PGMR.cbl:13`, `app/cbl/PGMR.cbl:14`). That makes it the batch-readonly family. It meets the four tests for a wave:

- It deploys independently: swap the one EXEC step.
- It rolls back independently: swap the step back. The reader changes no data, so nothing needs undoing.
- It has a testable boundary: the input is the SPARQ.TEST.MASTER file as the legacy writer produces it.
- It delivers something a stakeholder can name: the reader step of the nightly cycle runs on the new platform. That is thin. I say so in `unblocks`.

The reader is scored `low-high` in `risks.json`. The skill says low-high work is safe to do early once the harness is proven. Here the harness is built in this wave, and the wave is two programs of 16 lines each, so the wave can be the place the harness is proven. The condition is that the harness for wave 1 must include a golden copy of the legacy writer's output. Without one, the ported reader has no real input.

**Wave 2, the writer.** WRITEJOB runs PGMW (`app/jcl/WRITEJOB.jcl:2`). PGMW writes SPARQ.TEST.MASTER (`app/cbl/PGMW.cbl:13`, `app/cbl/PGMW.cbl:14`), and every other unit depends on that layout. This is the batch-writers family. It comes second because its boundary test is a byte comparison of the dataset it produces, and that test needs the wave 1 harness. The scores are `low-high`, driven by blast radius, not by port difficulty. The port is easy. The verification is the work.

## Why I did not change the seed

The rules allow a deviation for a must-not-break item, a strongly connected component, a facade dependency, a computed call or a high-high unit. I checked each.

- **Must-not-break.** The user's item, the nightly batch cycle, holds both waves. It does not force a unit from one wave to the other. The tree has no scheduler and no schedule, so I cannot show that the cycle is ordered any other way than writer then reader (`analysis.warnings`).
- **Strongly connected component.** None (`analysis`, field `sccs`).
- **Facade dependency.** None. There are no calls between the programs.
- **Computed call, unparsed file, embedded JCL.** None (`analysis`, fields `unresolved_dynamic`, `embedded_jcl`; and `unparsed` is empty).
- **High-high unit.** None. All four units score `low-high` (`modernization-assessment/risks.json:13`).
- **The medium contract edge.** I considered whether it should force the writer into wave 1, or both units into one wave. It does not, because the two layouts are 15 bytes each by their PIC clauses (`app/cpy/LAYOUTX.cpy:3`, `app/cpy/LAYOUTY.cpy:3`). The reader can be ported against the layout the legacy writer produces. Merging the waves for tidiness is not allowed.

## What would change the plan

Each of these is a falsifiable claim, and each is an open question in `00-summary.md`.

- If the LRECL of 80 on the output DD (`app/jcl/WRITEJOB.jcl:4`) means the file really holds 80 byte records, the reader in wave 1 must be ported against an 80 byte record, and the two copybooks do not describe it. The contract edge is then a real mismatch. Inference: it would move the writer up to wave 1, because the record layout would have to be settled first.
- If another program outside this tree reads SPARQ.TEST.MASTER, the writer has more than one consumer, and wave 2 has a bigger blast radius than the source shows.
- If a scheduler runs the jobs in a different order, or runs READJOB from a copy of the dataset, the temporal edge changes.

## Scoring, for reference

| Unit | Port difficulty | Blast radius | Quadrant | Wave | Evidence |
|---|---|---|---|---|---|
| `PGMR` | 1 | 3 | low-high | 1 | `app/cbl/PGMR.cbl:11` |
| `job:READJOB` | 1 | 3 | low-high | 1 | `app/jcl/READJOB.jcl:3` |
| `PGMW` | 2 | 4 | low-high | 2 | `app/cbl/PGMW.cbl:11` |
| `job:WRITEJOB` | 2 | 4 | low-high | 2 | `app/jcl/WRITEJOB.jcl:4` |

The scores are on two axes and are not combined. The reasons for each are in `modernization-assessment/risks.json`.
