# 03 Waves

## Result: no waves

`modernization-assessment/waves.json` has `"target_state": "refactor"` (line 2) and an empty `waves` list (line 3). All four programs are in `unassigned`. This is deliberate, and it follows the rule for a tree with no entry point.

The extractor found no entry point: no CSD transaction, no JCL job, no scheduler job, no wrapper (analysis: `entry_points`, empty; warning printed by `extract.py`). The wave seed puts every unit in a family by the entry points that use it. With none, it places nothing (`03a-wave-seed.md`). I did not invent a wave, and I made no deviation from the seed (`deviations` is empty, `modernization-assessment/waves.json:10`).

## Units not placed

| Unit | Confidence | Reason | Evidence |
|---|---|---|---|
| PROGA | low | No entry point in the tree. Nothing calls it, and no CSD was supplied to show whether a transaction starts it. It is the hub for the other three. | `app/cbl/PROGA.cbl:1` |
| PROGB | low | No entry point in the tree. Its only caller is PROGA, by a static LINK. | `app/cbl/PROGA.cbl:12` |
| PROGC | low | No entry point in the tree. Its only caller is PROGA, by XCTL. | `app/cbl/PROGA.cbl:20` |
| PROGD | low | No entry point in the tree. Its only caller is PROGA, by an XCTL that follows another XCTL (inference: probably never executed). | `app/cbl/PROGA.cbl:23` |

## What would have to be true to cut waves

Nothing can be sequenced until the client supplies at least one of: a CSD or RDO listing that names the transactions and their initial programs, JCL for the batch jobs, or a scheduler export. Only then does the extractor have entry points to start from.

Once entry points exist, this is what the code already says about how the four units would move:

- PROGA moves with the earliest family that uses it. PROGB, PROGC and PROGD have only PROGA as a caller (analysis: `fan_in`), so they move with it, or before it if PROGA is kept behind a facade that still reaches the old versions.
- PROGA is scored high-high in `risks.json` because of the computed LINK at `app/cbl/PROGA.cbl:16`. High-high units go late and go behind a facade. The facade would have to accept any program name in the COMMAREA and route it to either the old or the new program. That is inference.
- The wave would have to be one that can be rolled back on its own. The four programs write no dataset (no SELECT, OPEN, READ or WRITE appears in `app/cbl/PROGA.cbl:1-26`), so rollback is a routing change, not a data restore. That is inference from a tree that may be a fragment.

## Must-not-break: the nightly batch cycle

The user named the nightly batch cycle as a thing that must not break. It maps to no unit in this tree. There is no JCL, no scheduler definition, no batch program and no dataset. All four programs use EXEC CICS (`app/cbl/PROGA.cbl:12`). I have not mapped it to any of them. It is the first item in Open Questions in `00-summary.md`.
