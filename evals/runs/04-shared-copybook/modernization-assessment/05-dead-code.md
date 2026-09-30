# 05 Dead code

Telemetry: `none`. Every claim here is provisional. The candidate list is in `05a-dead-code-candidates.md`. The machine readable version is `dead-code.json`.

## The tree has no entry point

The extractor found no CSD transaction, JCL job, scheduler job or wrapper (`analysis`, field `entry_points` is empty). So nothing can be proven unreachable. Every candidate is unknown. The extractor said so in its warnings (`analysis`, field `warnings`).

## Dormancy was not measured

The tree is not a git repository, so no last-modified date exists (`analysis`, field `warnings`). The dormant bucket was NOT computed. The empty dormant list means not measured. It does not mean nothing is old.

## The three buckets

| Bucket | Units | Confidence | Evidence |
|---|---|---|---|
| Unreachable | none | not applicable | analysis, field `dead_code_candidates` |
| Reachable but dormant | none. Not measured. | not applicable | analysis, field `warnings` |
| Unknown | PROGA | low | `app/cbl/PROGA.cbl:1` |
| Unknown | PROGB | low | `app/cbl/PROGB.cbl:1` |
| Unknown | cpy:SHARED01 | low | `app/cpy/SHARED01.cpy:1` |

The copybook is included by both programs (`app/cbl/PROGA.cbl:5`, `app/cbl/PROGB.cbl:5`). It stays in the unknown bucket for as long as they do.

## What to ask the client

- Does any job, scheduler entry or CICS transaction run PROGA or PROGB? If yes, the missing JCL or scheduler needs to come into the tree, and this file gets redone.
- Which programs ran in the last 12 months? Job logs or SMF records would answer this. See `06-test-strategy.md`.
- Nothing here is a proposal to delete. A program with no entry point in a partial tree may run every night in the part that was not supplied.
