# 05 Dead code

Telemetry: none, as given by `--telemetry none`. Every claim below is provisional.
The machine-readable version is `modernization-assessment/dead-code.json`. The generated candidate
list is `05a-dead-code-candidates.md`. The extractor's three buckets were kept as computed.

The extractor computed dormancy as of 2026-09-30 with a 5-year threshold (analysis fields `as_of` and
`dormant_years`). No dormancy warning was raised, so an empty list here would have meant "none found",
and the dormant list is not empty.

| Bucket | Unit | Reason | Confidence | Evidence |
|---|---|---|---|---|
| Unreachable | none | Every program is reachable from `job:MAINJOB` (`reachable_programs` is 3 of 3). | high | analysis field `reachable_programs` |
| Unknown | none | There is no computed call, so nothing is held open. This holds only inside the tree. | medium | analysis field `unresolved_dynamic` |
| Dormant | `OLDPGM` | Last modified 2011-03-04, older than 5 years. Reachable. | low | `app/cbl/OLDPGM.cbl:1` |

## OLDPGM: old is not unused

`PGMMAIN` calls `OLDPGM` unconditionally, as its first statement, and `PGMMAIN` is run by the only
job in the tree. A live program that calls a dormant program unconditionally very likely runs it.
`OLDPGM` is proposed for instrumentation, not deletion. Deleting it on the date alone would drop a
call the nightly cycle very likely makes every run. Evidence: `app/cbl/PGMMAIN.cbl:4`,
`app/jcl/MAINJOB.jcl:2`.

Two things weaken the date itself. The date comes from git, and the history has two commits, so it may
be an import date and not the date of the last real change (inference). And `NEWPGM`, changed
2026-05-01, may have been meant to replace `OLDPGM`, leaving the old call behind. That is a question
for the client's engineers, not something to settle from the tree (inference).

## What the empty parts mean

- The job has no DD statement, and no scheduler was parsed. `unscheduled_jobs` is empty because no
  scheduler was parsed, not because every job is scheduled. Ask whether `job:MAINJOB` still runs and
  when. Evidence: `app/jcl/MAINJOB.jcl:1`.
- Nothing here is a candidate for deletion. `do_not_port` in `modernization-assessment/risks.json` is
  empty for the same reason.
