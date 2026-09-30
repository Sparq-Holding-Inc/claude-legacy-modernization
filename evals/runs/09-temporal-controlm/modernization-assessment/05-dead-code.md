# 05 Dead code

Telemetry: `none`. Every claim in this file is provisional.

## Result

| Bucket | Count | Confidence | Evidence |
|---|---|---|---|
| Unreachable | 0 | low | `analysis` field `dead_code_candidates` |
| Reachable but dormant | 0, and not measured | low | `analysis` field `warnings` |
| Unknown | 0 | low | `analysis` field `dead_code_candidates` |

## Read this before trusting the empty lists

- **Dormancy was not computed.** The tree is not a git repository, so no unit has a last-modified date. The extractor's warning says an empty dormant list means not measured. An empty list here is not a finding that nothing is old. `analysis` field `warnings`
- **There is nothing to be unreachable.** All four scheduler and JCL units are entry points, and the two steps belong to their jobs (`analysis` field `entry_points`). The tree holds no program, copybook or proc, so no unit lacks a caller.
- **No computed calls exist** (`analysis` field `unresolved_dynamic`), so the unknown bucket is empty for that reason and not because a program was cleared.
- **No unscheduled jobs.** Both JCL jobs are named by a scheduler entry (`analysis` field `unscheduled_jobs`, `app/scheduler/nightly.xml:4`, `app/scheduler/nightly.xml:8`). Whether those entries still run in production is unknown without telemetry. Job history would show it.
- **A condition with no consumer.** JOBB-DONE is posted and no job in the file waits on it. This is not dead code, because a consumer may sit outside the tree. It is worth asking about. `app/scheduler/nightly.xml:11`, inference

## What would firm this up

12 months of job history from the scheduler and from SMF: did JOBA and JOBB run every night, with what return codes. Then the dormant question can be answered for the two jobs.
