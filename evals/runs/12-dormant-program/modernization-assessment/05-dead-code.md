# Dead code

Telemetry: none. Every claim here is provisional.

## Unreachable

None. Every program is reachable from `job:MAINJOB` (analysis.reachable_programs is 3 of 3).

## Reachable but dormant

| Unit | Reason | Evidence | Confidence |
|---|---|---|---|
| OLDPGM | Last modified 2011-03-04, over 5 years before the as-of date 2026-10-14. `PGMMAIN` calls it unconditionally, so it very likely runs on every execution. Propose it for instrumentation, not deletion. Its body is only GOBACK, so it may be a stub. It still has a caller, so removing it would change `PGMMAIN`. | app/cbl/OLDPGM.cbl:2, app/cbl/PGMMAIN.cbl:4 | low |

The date alone is not a reason to delete. Git dates are from commits whose messages are `x`, so the date says when
a file was last committed. It may reflect a bulk import and not the last real change (inference).

## Unknown

None. There are no computed calls (analysis.unresolved_dynamic is empty) and no embedded JCL
(analysis.embedded_jcl is empty).

## Gaps

- `analysis.unscheduled_jobs` is empty, but no scheduler was parsed, so whether `job:MAINJOB` still runs is
  not established by the tree (inference). Ask for the scheduler export.
