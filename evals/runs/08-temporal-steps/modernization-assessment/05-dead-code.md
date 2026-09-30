# 05 Dead code

Telemetry: none, from the `--telemetry` flag. Every claim here is provisional. The register is in
`modernization-assessment/dead-code.json`, and the extractor's candidates are in
`05a-dead-code-candidates.md`.

## The three buckets

| Bucket | Units | Confidence | Evidence |
|---|---|---|---|
| Unreachable | none | medium | `analysis` field `dead_code_candidates` |
| Reachable but dormant | none. The bucket was not measured. | low | `analysis` field `warnings` (dormancy not computed) |
| Unknown | none. There is no computed call that could reach an unplaced unit. | medium | `analysis` field `unresolved_dynamic` |

The register is empty in all three buckets. I did not move any unit between buckets. I found no evidence
that an extractor bucket is wrong, so nothing moved toward unknown.

## What the empty lists do and do not say

- **Unreachable is empty.** All three programs are reached from `job:SEQJOB` (`app/jcl/SEQJOB.jcl:2`,
  `app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:4`). There is no copybook and no proc, so nothing else could be
  unreferenced. That is the extractor's arithmetic, not a finding.
- **Dormant is not measured.** The tree is not a git repository, so no unit has a last-modified date
  (`analysis` field `warnings`). An empty dormant list means not measured. It does not mean nothing is old.
  To fill it, the client must supply change dates from the source library.
- **Unknown is empty** because the tree has no computed call (`analysis` field `unresolved_dynamic`).
- **Reachable on paper only.** Everything is reachable only because the extractor treats SEQJOB as an entry
  point. The extractor also counts any job that no parsed scheduler names as an entry point. It parsed no
  scheduler, so `unscheduled_jobs` is empty because it was not measured (`analysis` field `warnings`). If
  SEQJOB no longer runs, all four units are dead. With no telemetry, there is no way to tell. That is
  inference.
- **The repeated step name.** If SEQJOB cannot run as written because STEP2 appears twice
  (`app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:5`), the three programs may not run at all. That is an open
  question for the client's engineers. It is not evidence for a bucket, so I moved nothing. Inference.

## What to ask for

Job logs or run history for SEQJOB for the last 12 months would settle both the dormant and the unknown
questions and would say whether the job runs. This is the same request as the oracle in `06-test-strategy.md`.
