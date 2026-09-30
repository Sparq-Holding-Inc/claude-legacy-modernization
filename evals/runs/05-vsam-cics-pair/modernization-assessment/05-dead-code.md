# 05 Dead code

Telemetry: none. Every dead-code claim in this file is provisional. The register is in `modernization-assessment/dead-code.json`. All three buckets are present and all three are empty.

## The three buckets

| Bucket | Count | Reason | Confidence | Evidence |
|---|---|---|---|---|
| Unreachable | 0 | Both programs are entry points through CSD transactions. The one copybook is included by both. | medium | `app/csd/DEMO.CSD:4-7`, `app/cbl/PROGR.cbl:5`, `app/cbl/PROGW.cbl:5` |
| Reachable but dormant | 0, not measured | The tree is not a git repository, so no last-modified date exists. The dormant bucket was not computed. An empty list here means not measured. | low | analysis field `warnings` |
| Unknown | 0 | The extractor found no computed call, so no unit is held open by one. | medium | analysis field `unresolved_dynamic` |

## Reading the result

- **Reachable means defined, not run.** The extractor treats every CSD transaction as an entry point. It proves TRNR and TRNW are defined in group DEMO. It does not prove the group is installed, or that either transaction ran in the last year. There is no `DEFINE LIST` in the CSD file. Evidence: `app/csd/DEMO.CSD:4-9`, inference.
- **No dormant list is not a clean bill.** Both programs have no last-modified date. Dormancy is not measured, and nothing may be proposed for deletion on that basis. Evidence: analysis field `warnings`.
- **No unscheduled jobs.** `unscheduled_jobs` is empty because the tree has no jobs at all. That is not evidence the batch cycle is gone. Ask whether the jobs that touch ACCTDAT still run. Evidence: analysis field `unscheduled_jobs`, inference.
- **Nothing was moved between buckets.** No evidence contradicts an extractor bucket, and no unit moves from unknown to unreachable.

## What telemetry would change

The client can settle this with twelve months of CICS statistics or SMF records for TRNR and TRNW. That would turn "defined" into "ran N times" and would give the dormant bucket a measured basis. Evidence: inference.
