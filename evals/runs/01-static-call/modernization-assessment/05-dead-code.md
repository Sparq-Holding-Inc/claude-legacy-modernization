# 05 Dead code

Telemetry: `none`, given as a flag. Every claim here is provisional. Machine-readable form:
`modernization-assessment/dead-code.json`. Candidates from the extractor: `05a-dead-code-candidates.md`.

## Result

No unit is unreachable, none is dormant, and both are unknown. The extractor put both there, and the
assessment keeps them there.

| Bucket | Units | Confidence | Evidence |
|---|---|---|---|
| Unreachable | none | not applicable | analysis: `dead_code_candidates.unreachable` is empty |
| Reachable but dormant | none. Not measured, see below | not applicable | analysis: `warnings`, the dormant bucket was not computed |
| Unknown | PROGA | low | `app/cbl/PROGA.cbl:1` |
| Unknown | PROGB | low | `app/cbl/PROGA.cbl:6` |

## Why unknown and not unreachable

The tree has no entry point (analysis: `entry_points` is empty). A program can only be proven unreachable
by a walk from an entry point, so nothing here can be. The tree also does not include the JCL and scheduler
files that would name PROGA. A program outside the tree may start it. Deleting either on this evidence would be
a guess. The validator forbids moving a unit from unknown to unreachable, and this assessment does not.

PROGB is a special case. Its only caller is PROGA, which calls it unconditionally
(`app/cbl/PROGA.cbl:6`). If PROGA runs, PROGB runs. The two share one fate. Inference.

## Dormant was not measured

The work folder is not a git repository, so no last-modified date exists for either program
(`app/cbl/PROGA.cbl:1`, `app/cbl/PROGB.cbl:1`, and the warning in analysis: `warnings`). The empty dormant
list means not measured, not none. To measure it, supply the source-control history or the member-change
dates from the mainframe library.

## Unscheduled jobs

`analysis.unscheduled_jobs` is empty because there are no jobs. That is a gap, not a clean bill. Ask
whether a job runs PROGA (Open Questions in `00-summary.md`).

## What would firm this up

Twelve months of job logs or SMF records that show whether PROGA ran, and a listing of the production load
library that shows whether a PROGB module exists there. Without them every line above stays provisional.
