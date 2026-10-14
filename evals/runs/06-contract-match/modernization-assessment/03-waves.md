# 03 Waves

Target state: refactor (given as a flag). The plan is the extractor's seed with names and rationale added. There are no deviations (`modernization-assessment/waves.json:36`).

| Wave | Name | Units | Blast radius | Confidence | Unblocks | Evidence |
|---|---|---|---|---|---|---|
| 1 | Master file reader | `PGMR`, `job:READJOB` | low | medium | The LAYOUTX record layout and the first packed-decimal comparison | `app/jcl/READJOB.jcl:1`, `app/cbl/PGMR.cbl:13` |
| 2 | Master file writer | `PGMW`, `job:WRITEJOB` | medium | medium | Retiring the legacy producer of the master file | `app/cbl/PGMW.cbl:6`, `app/jcl/WRITEJOB.jcl:3` |

## Why this order

- Wave 1 is read-only: PGMR opens the file for input and nothing else (`app/cbl/PGMR.cbl:13`). A new reader can be proven against files the legacy writer still produces.
- Wave 2 owns the file's creation (`app/jcl/WRITEJOB.jcl:3`). It is the wave where the byte layout has to be exact, since wave 1's reader depends on it.
- Neither wave has a call cycle, a god module or a computed call (`02-coupling.md`). Dependency does not force any unit out of its seed family, and neither does anything the extractor could not see, so there are no deviations.
- Each wave deploys behind a switch of the job step, rolls back by re-pointing the step to the legacy program, and has a testable boundary at the dataset.

## What the confidence means

Both waves are medium. The structure is simple and fully resolved. What holds the confidence down is that the tree has no scheduler, so the real run order and the "nightly batch cycle" are unconfirmed (`modernization-assessment/graph.json:383`), and the record length question in `02-coupling.md` is open.

## Largest wave risk

The writer wave. A change in how `LR-AMT` is encoded or how a record is padded makes the reader fail on the next run, or worse, read different money values without failing (`app/cpy/LAYOUTX.cpy:3`).
