# 03 Waves

Target state: `refactor`, given as a flag. Machine-readable plan: `modernization-assessment/waves.json`.

## What the extractor cut

Nothing. `03a-wave-seed.md` has no waves. The seed puts every entry point in a family, and the tree has no
entry point: no CSD transaction, JCL job, scheduler job or wrapper (analysis: `entry_points` is empty). Both
programs went to `unassigned`. The seed's stated reason, "a computed call or a submit inside COBOL could
reach it", is not what happened here. The tree has no computed call and no embedded JCL. The real reason is
that nothing starts either program. Inference.

## What this plan does

The wave validator rejects a plan with no waves. To produce a plan that validates, both programs are placed
in one wave by a recorded deviation. This is a placeholder. It is not a finding that a deployable wave exists.

| Wave | Units | Family | Rationale | Blast radius | Confidence | Evidence |
|---|---|---|---|---|---|---|
| 1 | PROGA, PROGB | none (no entry point) | One literal CALL ties them together. They move as a unit or not at all. | low | low | `app/cbl/PROGA.cbl:6` |

The four tests for a valid wave, against what the tree shows:

| Test | Result | Evidence |
|---|---|---|
| Deployable independently, behind a flag or facade | Cannot be judged. No caller, job or transaction is in the tree to put a flag in front of. | inference |
| Rollback independently | Cannot be judged. Nothing shows how the load modules are deployed. | inference |
| Testable boundary | Partly. The boundary is PROGA's DISPLAY output and return code, since neither program touches a dataset. | `app/cbl/PROGA.cbl:5` |
| Delivers something a stakeholder can name | No. Neither program does business work in the tree. | `app/cbl/PROGB.cbl:4` |

## What wave 1 unblocks

Nothing the tree shows. It is a chore wave. No copybook, dataset or other program depends on either unit.

## Deviations from the seed

| Unit | From | To | Reason | Evidence |
|---|---|---|---|---|
| PROGA | not placed | wave 1 | Placed so the plan validates. It is batch-type and may sit in the nightly batch cycle, but no JCL shows that. | `app/cbl/PROGA.cbl:6` |
| PROGB | not placed | wave 1 | Moves with its only caller. | `app/cbl/PROGA.cbl:6` |

## Sequence

Wave 1 holds the whole tree, so there is no sequence to defend. The real sequence question is where these
two programs sit inside the nightly batch cycle, and the tree cannot answer it. See Open Questions in
`00-summary.md`.

## Risk quadrant

Both units score low-low in `modernization-assessment/risks.json`. Low-low is the wave-one slot, which agrees
with the placement. PROGA's blast radius score rests on a guess about the surrounding job stream, so its
confidence is `low`.

| Unit | Port difficulty | Blast radius | Quadrant | Confidence | Evidence |
|---|---|---|---|---|---|
| PROGA | 1 | 2 | low-low | low | `app/cbl/PROGA.cbl:6` |
| PROGB | 1 | 1 | low-low | medium | `app/cbl/PROGB.cbl:4` |
