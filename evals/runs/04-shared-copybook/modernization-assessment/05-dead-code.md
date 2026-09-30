# 05 Dead code

Telemetry: none. Every claim in this file is provisional. The machine readable register is `modernization-assessment/dead-code.json`. The extractor's candidate tables are in `modernization-assessment/05a-dead-code-candidates.md`.

## Why the register is nearly empty

- The tree has no entry point (`analysis.entry_points` is empty). Nothing can be proven unreachable, because unreachable needs a static path from an entry point and there is none to start from. So the extractor put every candidate in unknown.
- No last-modified dates exist. The target is not a git repository, so the dormant bucket was not computed. The empty dormant list means not measured, not "nothing is dormant" (warning at `modernization-assessment/graph.json:152`).
- No JCL exists, so `analysis.unscheduled_jobs` is empty. That is not evidence that every job is scheduled. There are no jobs.
- There are no computed calls (`analysis.unresolved_dynamic` is empty). The unknown bucket is therefore not open because of a computed call. It is open because no entry point exists.

## Unreachable

None. No claim of unreachable is safe here.

## Reachable but dormant

None, and not measured. Instrument, do not delete, once dates and telemetry exist.

## Unknown

| Unit | Reason | Confidence | Evidence |
|---|---|---|---|
| PROGA | No entry point in the tree runs it. It may run from JCL or a scheduler the client did not supply | low | `app/cbl/PROGA.cbl:1` |
| PROGB | No entry point in the tree runs it. It may run from JCL or a scheduler the client did not supply | low | `app/cbl/PROGB.cbl:1` |
| cpy:SHARED01 | Two programs include it, so it is live if either program runs. It sits in unknown because its owners do | low | `app/cpy/SHARED01.cpy:1`, `app/cbl/PROGA.cbl:5`, `app/cbl/PROGB.cbl:5` |

I did not move any unit from unknown to unreachable, and I add no deletion proposal. A confident dead-code claim over a tree with no entry point is how something that runs once a year at fiscal close gets deleted.

## What would firm this up

| Ask | Effect | Confidence | Evidence |
|---|---|---|---|
| The JCL library, CSD and scheduler export | The extractor can find entry points, and the unknown bucket splits into reachable and unreachable | high | analysis (field `entry_points`) |
| 12 months of job logs or SMF records | Turns dormant and unknown from speculation to evidence, and removes the provisional label | high | inference |
| Source control history or last-modified dates | Lets the extractor compute the dormant bucket | high | analysis (field `warnings`) |
