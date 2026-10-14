# 03 Waves

Target state: **refactor** (given as a flag). Plan source: `modernization-assessment/03a-wave-seed.md`, kept without change. Machine form: `modernization-assessment/waves.json`.

## The plan

| Wave | Name | Units | Blast radius | Confidence | Unblocks | Evidence |
|---|---|---|---|---|---|---|
| 1 | Reader job against the legacy file | `PGMR`, `job:READJOB` | low | medium | The pinned layout and record length that wave 2 must meet | `app/jcl/READJOB.jcl:1`, `app/jcl/READJOB.jcl:3`, `app/cbl/PGMR.cbl:13` |
| 2 | Writer job and the single layout | `PGMW`, `job:WRITEJOB` | medium | medium | Merging `LAYOUTX` and `LAYOUTY` into one definition | `app/cbl/PGMW.cbl:6`, `app/cbl/PGMW.cbl:14`, `app/jcl/WRITEJOB.jcl:3` |

Copybooks `cpy:LAYOUTX` and `cpy:LAYOUTY`, the steps, and the dataset `ds:SPARQ.TEST.MASTER` move with their owners and are not listed as units.

## Why this order

The seed placed the read-only job first and the writer second, from facts alone (`modernization-assessment/03a-wave-seed.md`). I checked that against the one dependency in the tree. The reader consumes what the writer produces (`app/jcl/READJOB.jcl:3`, `app/jcl/WRITEJOB.jcl:3`). Two orders are possible:

- **Reader first (the plan).** The new reader is tested on files the legacy writer already made. The legacy writer is untouched, so the thing that defines the file does not change while the reader is being proved. The reader port also forces someone to write down what the file is.
- **Writer first.** The new writer could emit a file that the legacy reader mis-reads without any error, because the two copybooks are separate and a drift between them is silent (`app/cpy/LAYOUTX.cpy:2`, `app/cpy/LAYOUTY.cpy:2`). Producer changes are the harder ones to see.

No cycle, no god module and no computed call forces another order (`analysis.sccs`, `analysis.god_modules`, `analysis.unresolved_dynamic` are all empty). **Deviations from the seed: none.** A plan with no deviations is a fine answer.

## Are the waves valid?

| Test | Wave 1 | Wave 2 |
|---|---|---|
| Deployed independently | Yes. Swap the `EXEC PGM=` target in one job (`app/jcl/READJOB.jcl:2`). | Yes, with the same swap (`app/jcl/WRITEJOB.jcl:2`). |
| Rolled back independently | Yes. Point the step back at the legacy `PGMR`. Nothing it wrote needs undoing. | Yes, but only if the dataset it created is deleted or renamed first. `DISP=(NEW,CATLG,DELETE)` fails on an existing dataset (`app/jcl/WRITEJOB.jcl:3`), so a rollback re-run needs the dataset gone. inference |
| Testable boundary | Yes. The input file is the boundary. | Yes. The output file is the boundary. |
| Something a stakeholder can name | Weak. "The reader step of the nightly cycle is on the new code." | Moderate. "The file the cycle produces is now specified once." |

Wave 1 is close to a chore: it unblocks wave 2 and proves the toolchain, and delivers little on its own. Say so to the steering committee.

## Confidence

Neither wave is `high`. Reasons, each cited:

- The tree holds no scheduler, so the order and membership of the nightly cycle are not known (`analysis.warnings`).
- The one contract edge is `medium` (`app/cbl/PGMR.cbl:11`, `app/cbl/PGMW.cbl:11`; see `modernization-assessment/02-coupling.md`).
- The writer sets no field values before it writes (`app/cbl/PGMW.cbl:14`), so the behavior to preserve is not in the source.

## Must-not-break mapping

"The nightly batch cycle" maps to **no named unit** in the tree. There is no scheduler artifact (`analysis.warnings`), so I cannot show that `job:READJOB` and `job:WRITEJOB` are the cycle, or only part of it. I have treated both jobs as the cycle's members because they are the only batch jobs present, and that is inference. See Open Questions in `modernization-assessment/00-summary.md`.
