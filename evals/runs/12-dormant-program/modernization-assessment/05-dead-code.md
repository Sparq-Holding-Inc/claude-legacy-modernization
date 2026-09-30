# 05 Dead code

Machine-readable register: `modernization-assessment/dead-code.json:1`. Candidates computed by the extractor: `05a-dead-code-candidates.md`.

Telemetry: none. Every claim below is provisional. The extractor computed dormancy with the default rule, 5 years as of 2026-09-30 (`analysis`, fields `dormant_years` and `as_of`). Git dates were on, so the dormant list was measured, not skipped. An empty bucket here means nothing was found under these rules.

## Three buckets

| Bucket | Units | Confidence | Evidence |
|---|---|---|---|
| Unreachable | none | high | `analysis` (field `dead_code_candidates`) |
| Reachable but dormant | OLDPGM | medium | `app/cbl/OLDPGM.cbl:1`, `app/cbl/PGMMAIN.cbl:4` |
| Unknown | none | low | `analysis` (field `unresolved_dynamic`) |

## Unreachable

None. Every program has a static path from the entry point `job:MAINJOB`: the job runs PGMMAIN, and PGMMAIN calls the other two (`app/jcl/MAINJOB.jcl:2`, `app/cbl/PGMMAIN.cbl:4`, `app/cbl/PGMMAIN.cbl:5`). Nothing is proposed for deletion.

## Reachable but dormant: OLDPGM

The extractor lists OLDPGM: reachable, last modified 2011-03-04, older than 5 years (`analysis`, field `dead_code_reasons`). I keep it in this bucket, and I propose instrumentation, not deletion.

The date is the only sign that it is unused, and the call graph says the opposite. PGMMAIN calls it with a plain CALL and no test around it (`app/cbl/PGMMAIN.cbl:4`). PGMMAIN was added on 2026-05-01, long after OLDPGM, so someone wrote that call recently. A live program that calls a dormant one unconditionally very likely runs it on every run. Dormant means old, not unused.

Two things weaken the date itself:

- It is a git commit date. The history has two commits, both with the message "x", so it may come from an import and not from real edits. This is inference.
- OLDPGM is 4 lines with a GOBACK, so it may be unchanged simply because there is nothing to change (`app/cbl/OLDPGM.cbl:4`).

What would settle it: job logs or SMF step records showing OLDPGM executing over the last 12 months, month end and year end included. If it ran, keep it. If it never ran, the client can ask why PGMMAIN calls it, and only then consider a change.

## Unknown

None. The unknown bucket exists for programs that no static path reaches but a computed call could reach. The tree has no computed call (`analysis`, field `unresolved_dynamic` is empty) and no unreached program. That covers this tree only.

## Jobs and schedulers

The extractor found one JCL job and no scheduler. A job that no parsed scheduler names still counts as an entry point, so `job:MAINJOB` never shows in a bucket. `unscheduled_jobs` is empty, but only because no scheduler was parsed, so it is not evidence that the job is scheduled (`analysis`, fields `unscheduled_jobs` and `warnings`). Does MAINJOB still run? That is Open Question 1 in `00-summary.md`.
