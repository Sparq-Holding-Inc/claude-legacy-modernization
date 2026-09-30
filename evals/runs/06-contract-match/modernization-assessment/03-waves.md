# 03 Waves

Target state: `refactor` (same behavior in restructured code). The plan is in
`modernization-assessment/waves.json:1`. It is the extractor's seed with names, rationale and blast
radius filled in. I made no deviations.

## Summary

| Wave | Family | Units | Blast radius | Unblocks | Confidence | Evidence |
|---|---|---|---|---|---|---|
| 1 | batch-readonly | `PGMR`, `job:READJOB` | low | The LAYOUTX conversion and a harness that decodes SPARQ.TEST.MASTER on the target | medium | `app/jcl/READJOB.jcl:2`, `app/cbl/PGMR.cbl:13` |
| 2 | batch-writers | `PGMW`, `job:WRITEJOB` | high | Retiring the legacy writer of SPARQ.TEST.MASTER | medium | `app/jcl/WRITEJOB.jcl:2`, `app/cbl/PGMW.cbl:13` |

Every unit in the graph is placed. Steps, the copybook `cpy:LAYOUTX` and the dataset
`ds:SPARQ.TEST.MASTER` move with their owners and are not listed (`analysis` field `wave_seed`, key
`unassigned` is empty). The copybook is included by both programs (`app/cbl/PGMR.cbl:11`,
`app/cbl/PGMW.cbl:11`), so it moves with the earliest family that uses it, wave 1.

## Wave 1. Reader side of the master file

Units: `PGMR`, `job:READJOB`. Port order: `PGMR` first, then `job:READJOB`.

- Why it is a sound wave: it reads the dataset and writes nothing another entry point uses
  (`app/cbl/PGMR.cbl:13`, `app/jcl/READJOB.jcl:3`). It is deployable behind a switch on the job. It
  rolls back by running the legacy job. Nothing calls PGMR, so nothing else must change.
- Its testable boundary is weak. PGMR produces no output (`app/cbl/PGMR.cbl:14`). The assertion is the
  return code plus a decoded copy of the record it reads. Inference: the harness has to read the
  dataset itself, because PGMR shows nothing.
- What a stakeholder can name: very little. This wave is a chore that proves the toolchain and the
  decimal decoding. Say so plainly to the committee.
- Why first: a consumer can be moved while the legacy producer keeps writing the legacy format. The
  reverse would change bytes under a reader nobody has tested.

## Wave 2. Writer of the master file

Units: `PGMW`, `job:WRITEJOB`. Port order: `PGMW` first, then `job:WRITEJOB`.

- Why it is a sound wave: it is the only writer of SPARQ.TEST.MASTER (`analysis` field `data_hubs`,
  `app/cbl/PGMW.cbl:13`) and it comes after the reader is proven against the legacy bytes. It can be
  rolled back by running the legacy writer, as long as the dataset name is not shared with a
  partly migrated reader.
- Its risk quadrant is low-high: an easy port, and the verification is the work
  (`modernization-assessment/risks.json:1`). Facts that make the verification hard:
  the record fields are never set before the WRITE (`app/cbl/PGMW.cbl:14`), and the copybook record is 15
  bytes while the JCL asks for LRECL=80 (`app/cpy/LAYOUTX.cpy:3`, `app/jcl/WRITEJOB.jcl:4`).
  Both are inference from the source.
- It does not break a dependency by being last: PGMR reads what PGMW writes, and wave 1 already
  covers PGMR.
- What a stakeholder can name: the nightly master file is produced by the new code with bytes proven
  equal to the old. That is nameable, if the client confirms the dataset is the real one.

## Deviations from the seed

None. Checked against the four reasons the skill allows:

| Reason | Applies? | Evidence |
|---|---|---|
| A must-not-break item, an SCC or a facade dependency forces a unit into another wave | No. "The nightly batch cycle" is not located in the tree (no scheduler parsed), so it moves no unit. No SCC exists. | `analysis` fields `sccs`, `warnings` |
| A wave holds more than 25 units | No. Each wave holds 2 units. | `modernization-assessment/waves.json:1` |
| Something the extractor could not see changes what a unit is | No computed call, no embedded JCL, no unparsed file. The two inferences above concern record bytes and do not move a unit. | `analysis` fields `unresolved_dynamic`, `embedded_jcl`, `unparsed` |
| `risks.json` puts a unit in high-high and its family puts it early | No unit is high-high. PGMW and job:WRITEJOB are low-high and already in the last wave. | `modernization-assessment/risks.json:1` |

## What would change this plan

- A scheduler export that shows READJOB running before WRITEJOB, or the two in different cycles.
  Temporal edges are the order the harness must keep.
- A third program that reads or writes SPARQ.TEST.MASTER. That program would join the hub, and the
  writer wave would grow.
- Confirmation that production uses a different dataset name from SPARQ.TEST.MASTER.
