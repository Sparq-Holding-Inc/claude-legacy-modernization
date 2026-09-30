# 05 Dead code

Machine-readable register: `dead-code.json`. Candidate tables: `05a-dead-code-candidates.md`. Telemetry: **none**, from the `--telemetry none` flag. Every claim here is provisional.

## The result

| Bucket | Units | Confidence | Evidence |
|---|---|---|---|
| Unreachable | none | high | inference |
| Dormant | none. `last_modified` is unknown for all three files because no git dates were available (`meta.git_dates` is false). | low | inference |
| Unknown | PROGA, PROGB, `cpy:SHARED01` | low | `app/cbl/PROGA.cbl:1`, `app/cbl/PROGB.cbl:1`, `app/cpy/SHARED01.cpy:1` |

Nothing is proposed for deletion.

## Why everything is unknown

The extractor found no entry point: no JCL job, no scheduler job, no CICS transaction, no wrapper script (`analysis.entry_points` is empty, `reachable_count` is 0). Without an entry point nothing can be shown to be reachable, and nothing can be shown to be unreachable either. The extractor placed all three units in the unknown bucket, and the validator forbids moving them to unreachable.

This is not the usual reason for unknown. The usual reason is a computed call in reachable code. Here there are no computed calls (`analysis.unresolved_dynamic` is empty). The bucket is open because the tree is incomplete, not because of dynamic dispatch.

## Notes on each unit

- **PROGA and PROGB.** Eight lines each. Neither is called from anywhere in the tree. A program that sits in a source tree with no job that names it is often a job's target from JCL kept elsewhere. Do not read the absence of a caller as evidence that it is dead. Ask for the JCL. Evidence: `app/cbl/PROGA.cbl:2`, `app/cbl/PROGB.cbl:2`.
- **cpy:SHARED01.** Both programs include it, so it is live whenever either is. It is not a deletion candidate whatever the answer for the programs. Evidence: `app/cbl/PROGA.cbl:5`, `app/cbl/PROGB.cbl:5`.
- **Tie to the must-not-break item.** The nightly batch cycle is the anchor. If either program is a step in it, then it is live by definition and belongs in no dead-code bucket. That is checkable in one look at the client's scheduler.

## What would firm this up

12 months of job-run history (SMF or scheduler logs) for these two program names. Without it, every entry above stays provisional.
