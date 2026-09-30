# 05 Dead code

Telemetry: none. Every claim in this file is provisional.

## Result

The extractor found no dead code candidates: no unreachable, no dormant and no unknown units (`modernization-assessment/graph.json:225`). All three lists in `dead-code.json` are empty. The full candidate tables are in `05a-dead-code-candidates.md`.

That is a weaker statement than it looks. Read the next section.

## Why an empty register is not a clean bill

- **Dormancy could not be tested.** Every node has `last_modified` unknown, and git dates were off (`modernization-assessment/graph.json:7`). The dormant rule needs a date, so it could not fire. An empty dormant list here means no dates, not recently modified code. `inference`
- **There is no unreachable code because there is almost no code.** The four entry points are the two JCL jobs and the two scheduler jobs (`app/scheduler/nightly.xml:4`, `app/scheduler/nightly.xml:8`), and they reach the two steps and IEFBR14. That is the whole tree.
- **There are no computed calls, so the unknown bucket has no reason to exist** (`modernization-assessment/graph.json:231`). It is empty because there is no COBOL to make a computed call, not because the risk was checked.
- **Nothing is proposed for deletion.** With no telemetry, no claim here could support a delete.

## Loose ends that are not dead code

These are conditions with one side missing. They are questions, not candidates. I am not putting them in a bucket, because they are not nodes in `graph.json`.

| Loose end | What is missing | Confidence | Evidence |
|---|---|---|---|
| EXTERNAL-FEED is waited on and never added inside the tree | The producer | low | `app/scheduler/nightly.xml:5` |
| JOBB-DONE is added and never waited on inside the tree | The consumer | low | `app/scheduler/nightly.xml:11` |

## What would firm this up

Twelve months of Control-M job run history for both jobs, and the last-changed date of each member. With those, dormant becomes evidence. Without them, `dead-code.json` stays at `telemetry: none`.
