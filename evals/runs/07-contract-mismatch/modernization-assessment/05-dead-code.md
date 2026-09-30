# 05 Dead code

Telemetry: none. Every claim in this file is provisional. The candidates come from `05a-dead-code-candidates.md`
and `modernization-assessment/dead-code.json`.

## Result

All three buckets are empty.

| Bucket | Count | Confidence | Evidence |
|---|---|---|---|
| Unreachable | 0 | high, as far as the tree goes | analysis: `dead_code_candidates` in `modernization-assessment/graph.json` |
| Reachable but dormant | 0, and this means not measured | none | analysis: `warnings` in `modernization-assessment/graph.json` |
| Unknown | 0 | high, as far as the tree goes | analysis: `unresolved_dynamic` in `modernization-assessment/graph.json` |

## Why each bucket is empty

- **Unreachable.** Both programs are started by a JCL job, and both jobs are entry points. Both copybooks are
  included by a program that a job runs. Evidence: `app/jcl/READJOB.jcl:2`, `app/jcl/WRITEJOB.jcl:2`,
  `app/cbl/PGMR.cbl:11`, `app/cbl/PGMW.cbl:11`. Nothing in the tree is left without a path.
- **Dormant.** This bucket was not computed. The tree is not a git repository, so no unit has a last-modified
  date. An empty dormant list here means not measured, not that nothing is old. Evidence: analysis: `warnings`
  in `modernization-assessment/graph.json`, and the `Last modified` column of `01-inventory.md`. To measure it
  the client would have to supply last-change dates, or run the extractor from a checkout with history.
- **Unknown.** No computed call exists, so no program can hide behind one. Evidence: analysis:
  `unresolved_dynamic` in `modernization-assessment/graph.json`. No embedded JCL was found either. Evidence:
  analysis: `embedded_jcl` in `modernization-assessment/graph.json`.

## What this does not say

- A job that no parsed scheduler names still counts as an entry point, so it never shows in a bucket. No
  scheduler was parsed. Both jobs are therefore reachable only in the sense that they exist. Whether either one
  still runs is not known, and `unscheduled_jobs` is empty only because there was no scheduler to compare
  against. Evidence: analysis: `unscheduled_jobs` and `warnings` in `modernization-assessment/graph.json`.
  This is an open question for the client (see `00-summary.md`).
- With no telemetry, "reachable" means reachable on paper. A job log or SMF extract for the last 12 months
  would show whether `READJOB` and `WRITEJOB` ran. Inference.
- The dataset name contains `TEST`. If this is a test artifact in a system that has a production twin, both jobs
  may be test scaffolding. Inference. Evidence: `app/jcl/WRITEJOB.jcl:3`. It is not proposed as dead code,
  because a name is not evidence.

## Proposal

No deletion is proposed. Instrument both jobs and both programs first, to collect the telemetry that is missing.
Inference. Evidence: `app/jcl/READJOB.jcl:1`, `app/jcl/WRITEJOB.jcl:1`.
