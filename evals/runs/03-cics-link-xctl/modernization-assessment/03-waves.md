# 03 Waves

**Wave count: 0.** No wave is proposed, and that is the correct answer from this tree. `modernization-assessment/waves.json:3` holds `"waves": []`.

## Why

The tree has no entry point. There is no CSD transaction, JCL job, scheduler job or wrapper (`analysis` field `entry_points` is empty; `analysis` field `warnings`). The wave method sorts entry points into families (batch, read-only online, write online, DB2). With none, every unit is unknown and nothing can be sequenced. Inventing a wave would be a guess about who calls PROGA.

| Unit | Status | Reason | Evidence | Confidence |
|---|---|---|---|---|
| PROGA | unassigned | No transaction or job names it. Its two computed calls are open. | `app/cbl/PROGA.cbl:16` | low |
| PROGB | unassigned | Reached only from PROGA by LINK. | `app/cbl/PROGA.cbl:12` | low |
| PROGC | unassigned | Reached only from PROGA by XCTL. | `app/cbl/PROGA.cbl:20` | low |
| PROGD | unassigned | Reached only from PROGA by XCTL. | `app/cbl/PROGA.cbl:23` | low |

## The must-not-break item

"The nightly batch cycle" maps to no unit here. All four programs are CICS online programs: they use EXEC CICS and the extractor typed them `online_txn` (`app/cbl/PROGA.cbl:12`). There is no JCL, no batch program and no dataset in the tree. Either the batch cycle is in code that was not supplied, or it does not call these programs. Both readings are open questions in `00-summary.md`.

## If the missing inputs arrive

inference: the likely order is PROGB, PROGC and PROGD first (leaves, 4 lines each, no data), then PROGA behind a facade, because PROGA is the articulation point. This needs the CSD to confirm. It is not a plan.

No deviations from the seed (`modernization-assessment/waves.json:10`).
