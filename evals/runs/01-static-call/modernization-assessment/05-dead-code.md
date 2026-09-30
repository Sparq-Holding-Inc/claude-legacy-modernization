# 05 Dead code

Telemetry: none. Every claim below is provisional. The candidate tables were generated in
`05a-dead-code-candidates.md`. The machine readable version is `dead-code.json`.

The extractor found no entry point: no CSD transaction, no JCL job, no scheduler job and no wrapper
(`modernization-assessment/graph.json:109`). With no entry point, nothing can be proven unreachable, so
both programs land in the unknown bucket. That is a limit of the tree, not a finding about the code.

## Unreachable

Nothing. No unit can be proven unreachable, and none is proposed for deletion.

| Unit | Reason | Confidence | Evidence |
|---|---|---|---|
| none | No entry point exists in the tree, so no static path can be tested. | high | `modernization-assessment/graph.json:72` |

## Reachable but dormant

Nothing. Dormancy needs a reachable program with a last-modified date older than the 5 year rule. Neither
program has a last-modified date, because no git dates were available to the extractor (`modernization-assessment/graph.json:7`).
No program is reachable from an entry point, because there is none.

| Unit | Reason | Confidence | Evidence |
|---|---|---|---|
| none | No last-modified date is available, and no unit is reachable from an entry point. | high | `modernization-assessment/graph.json:7` |

## Unknown

| Unit | Reason | Confidence | Evidence |
|---|---|---|---|
| PROGA | No entry point in the tree starts it. It is a batch program, so its starter (JCL or a scheduler) is probably outside the tree. Instrument it. Do not delete it. | low | `app/cbl/PROGA.cbl:1` |
| PROGB | No entry point in the tree, but PROGA calls it unconditionally by literal name, so it runs whenever PROGA runs. Instrument it. Do not delete it. | low | `app/cbl/PROGA.cbl:6` |

## Computed calls

There are none (`modernization-assessment/graph.json:86`). The unknown bucket is open only because no
entry point exists, not because a computed call could reach these programs.

## What to do

- Ask the client for the JCL job or scheduler entry that runs PROGA. If one exists, PROGA becomes
  reachable and PROGB follows from the CALL at `app/cbl/PROGA.cbl:6`.
- Ask for 12 months of job logs or SMF records for PROGA. That turns this register from speculation into
  evidence.
