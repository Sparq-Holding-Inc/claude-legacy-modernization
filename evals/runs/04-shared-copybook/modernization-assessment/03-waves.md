# 03 Waves

Target state: refactor. The machine readable plan is `modernization-assessment/waves.json`.

## Result: no waves

The tree has no entry point: no JCL job, no CSD transaction, no scheduler job and no shell wrapper (`analysis.entry_points` is empty, and `modernization-assessment/03a-wave-seed.md` has an empty wave table). The seed cuts waves from the families of the entry points that use each unit. With no entry point there is no family, so the seed produced no wave. `waves.json` holds `"waves": []`. `unassigned` holds both programs. `deviations` is empty because there was no plan to deviate from.

Nothing can be sequenced until the client supplies JCL, a CSD or a scheduler export.

I did not invent a wave, and I did not group the two programs by their shared copybook as a stand-in. Grouping by a shared copybook is a coupling argument, not a deployable wave, and it fails the four wave tests below.

## Units not placed

| Unit | Reason | Confidence | Evidence |
|---|---|---|---|
| PROGA | No entry point runs it, so no family applies | high | `app/cbl/PROGA.cbl:1` |
| PROGB | No entry point runs it, so no family applies | high | `app/cbl/PROGB.cbl:1` |

`cpy:SHARED01` is not a unit. A copybook moves with its owner. It has two owners, PROGA and PROGB (`app/cbl/PROGA.cbl:5`, `app/cbl/PROGB.cbl:5`), so whichever wave the client's JCL eventually places them in, they should share it. That is an inference from `modernization-assessment/02-coupling.md`, pattern 1.

## Why no wave passes the four tests

| Test | State | Confidence | Evidence |
|---|---|---|---|
| Deployable independently, behind a flag or facade | Cannot be judged. What triggers the programs is unknown | high | analysis (field `entry_points`) |
| Rollback independently | Cannot be judged. Neither the job that submits them nor the output they feed is visible | high | analysis (field `entry_points`) |
| Testable boundary | No boundary exists. The programs open no file and write no output | medium (inference) | `app/cbl/PROGA.cbl:7`, `app/cbl/PROGB.cbl:7` |
| Delivers something a stakeholder can name | Unknown. "The nightly batch cycle" is the one thing named, and it maps to no unit | high | inference |

## What would change this

Once JCL or a scheduler export arrives, re-run the extractor. If a job runs PROGA or PROGB, the seed places it in a family and produces waves. The risk scores in `modernization-assessment/risks.json` already hold both programs as `low-low`, and they carry `low` confidence because the blast radius depends on where the programs sit in the cycle.

## Risk scores in brief

| Unit | Port difficulty | Blast radius | Quadrant | Confidence | Evidence |
|---|---|---|---|---|---|
| PROGA | 1 | 2 | low-low | low | `app/cbl/PROGA.cbl:7` |
| PROGB | 1 | 2 | low-low | low | `app/cbl/PROGB.cbl:7` |

No unit sits in high-high, so no facade dependency forces a move. Both units are scored on thin evidence and the blast radius could rise sharply if the client says either program is a step in the nightly cycle. The two axes are never combined.
