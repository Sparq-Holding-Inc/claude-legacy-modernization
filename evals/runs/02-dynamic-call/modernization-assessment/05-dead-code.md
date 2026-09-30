# 05 Dead code

Telemetry is `none`, so every claim here is provisional. Two warnings from the extractor apply, and both change what an empty bucket means (analysis field `warnings`):

- No last-modified dates exist. The tree is not a git repository. The dormant bucket was not computed. An empty dormant list means not measured, not "nothing is dormant".
- No entry points were found. Nothing can be proven unreachable, so every candidate is unknown.

## Unreachable

Empty. Nothing can be proven unreachable, because `PROGA` makes a computed call that could name any program (`app/cbl/PROGA.cbl:9`) and there are no entry points to trace from (analysis field `entry_points`).

## Reachable but dormant

Empty, and not measured. No unit has a last-modified date (analysis field `warnings`).

## Unknown

| Unit | Type | Reason | Confidence | Evidence |
|---|---|---|---|---|
| PROGA | batch | No entry point in the tree names it. It has no LINKAGE SECTION and ends with `STOP RUN`, so it reads as a main program that some job or operator starts, but no such job is in the tree. Do not delete. | low | `app/cbl/PROGA.cbl:10`. Inference on the main-program reading. |
| PROGB | batch | No static caller. `PROGA` reads a program name from `ACCEPT` and calls it, so `PROGB` could be the target. It holds only `GOBACK`. Do not delete on this evidence. | low | `app/cbl/PROGB.cbl:4`, `app/cbl/PROGA.cbl:9` |

I did not move either program out of unknown, and could not bound the computed call: `WS-PGM-NAME` has no value in the source, so the target set is not something the code states (`app/cbl/PROGA.cbl:5`, `app/cbl/PROGA.cbl:8`).

## Jobs no scheduler names

There are no jobs of any kind in the tree (analysis field `unscheduled_jobs` is empty). That is not a sign that all jobs are scheduled. It is a sign that no JCL was supplied. Open question for the client: which jobs run `PROGA`, and do they still run?

## What would firm this up

Twelve months of job logs or SMF records showing which programs ran, and the values `PROGA` read at its `ACCEPT`. With those, `PROGB` and any other callee can be moved to evidence-based buckets. Without them, all of this stays provisional.
