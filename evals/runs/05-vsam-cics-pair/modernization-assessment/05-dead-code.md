# 05 Dead code

Telemetry: none. **Every dead-code claim here is provisional.** The extractor also could not measure dormancy. No last-modified dates exist because the tree is not a git repository (`modernization-assessment/graph.json:260`). The dormant list is empty because it was not measured. It is not empty because nothing is old.

| Bucket | Units | Reason | Confidence | Evidence |
|---|---|---|---|---|
| Unreachable | none | Both programs are reached from an enabled CSD transaction, and the copybook is included by both. | medium | analysis: `dead_code_candidates` at `modernization-assessment/graph.json:179`; `app/csd/DEMO.CSD:4-7` |
| Reachable but dormant | none, not measured | No dates and no telemetry. | low | analysis: `warnings` at `modernization-assessment/graph.json:259` |
| Unknown | none | No computed calls exist, so nothing is held open. | medium | analysis: `unresolved_dynamic` at `modernization-assessment/graph.json:185` |

Reachable here means only that the CSD defines a transaction for the program and marks it enabled (`app/csd/DEMO.CSD:5`, `app/csd/DEMO.CSD:7`). It does not mean the transaction runs. Nothing is proposed for deletion. Ask for transaction counts for TRNR and TRNW over 12 months, and instrument both until they arrive.

No job is unscheduled, because the tree holds no job (`modernization-assessment/graph.json:206`). The batch cycle is a scheduling and dead-code question the tree cannot answer.
