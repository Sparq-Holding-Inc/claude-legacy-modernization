# 05 Dead code

Telemetry: none. Every claim in this file is provisional. The machine-readable form is
`dead-code.json`. The extractor's own tables are in `05a-dead-code-candidates.md`.

## Two warnings from the extractor

- **No entry points.** No CSD transaction, JCL job, scheduler job or wrapper was found. Nothing can be
  proven unreachable, so every candidate is unknown (`analysis.warnings`).
- **Dormancy was not computed.** No last-modified dates exist, because the tree is not a git
  repository (`meta.git_dates` is false in `graph.json`). The dormant list is empty because it was
  not measured. It does not mean nothing is dormant.

## The three buckets

| Bucket | Units | Confidence | Evidence |
|---|---|---|---|
| Unreachable | none | high | analysis field `dead_code_candidates` |
| Reachable but dormant | none. Not measured. | low | analysis field `warnings` |
| Unknown | PROGA, PROGB | low | `app/cbl/PROGA.cbl:6` |

## Unknown

| Unit | Why it is unknown | Confidence | Evidence |
|---|---|---|---|
| PROGA | No entry point exists in the tree, so nothing reaches it statically. It ends in `STOP RUN`, so it looks like a main program that a job outside the tree starts. It is not a candidate for deletion. | low | `app/cbl/PROGA.cbl:7` |
| PROGB | Same cause. It is statically called by PROGA, so if PROGA runs, PROGB runs. | low | `app/cbl/PROGA.cbl:6` |

No computed call keeps this bucket open (`analysis.unresolved_dynamic` is empty). The bucket is open for
a different reason: the tree has no way to start anything. I moved nothing toward unreachable.

## What to ask before any deletion

- Do the jobs that run PROGA still run? A job that no parsed scheduler names is an entry point. Here
  the extractor has no job to test (`analysis.unscheduled_jobs` is empty).
- Can the client supply 12 months of job history (SMF type 30 or the scheduler run log) for PROGA?
  That turns the unknown bucket into evidence.
- Can the client supply source-control dates for the two files?
