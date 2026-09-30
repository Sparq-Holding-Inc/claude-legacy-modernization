# 05 Dead code

Telemetry: `none`. Every claim in this file is provisional. The candidate table generated from the extractor is in `05a-dead-code-candidates.md`.

## Three buckets

| Bucket | Units | Confidence | Evidence |
|---|---|---|---|
| Unreachable (safe to propose for deletion) | none | high | inference |
| Reachable but dormant (instrument, do not delete) | OLDPGM | medium | `app/cbl/OLDPGM.cbl:1` |
| Unknown (a computed call could reach it) | none. There are no computed calls | high | inference |

Every program in the tree is reachable from `job:MAINJOB` (`app/jcl/MAINJOB.jcl:2`, `app/cbl/PGMMAIN.cbl:4`, `app/cbl/PGMMAIN.cbl:5`). No unit is in the unreachable or the unknown bucket, so nothing in this tree is proposed for deletion.

## OLDPGM: dormant, and probably live

The extractor lists OLDPGM as dormant because it was last modified on 2011-03-04, more than 5 years before 2026-09-30. Dormant means old, not unused. PGMMAIN calls OLDPGM unconditionally as the first thing it does (`app/cbl/PGMMAIN.cbl:4`), and MAINJOB runs PGMMAIN (`app/jcl/MAINJOB.jcl:2`). So it very likely runs on every execution. Deleting it on the date alone would change the call sequence of the nightly run.

The recommendation is to instrument it and to read 12 months of job logs before anyone proposes removing it. The source is only a `GOBACK` (`app/cbl/OLDPGM.cbl:4`), so the call may be a leftover from a replacement by NEWPGM. That is inference from the names and the call order, and someone who knows the system should confirm it.

The dormant list is kept as the extractor computed it. Confidence is `medium` rather than `high` because there is no telemetry.
