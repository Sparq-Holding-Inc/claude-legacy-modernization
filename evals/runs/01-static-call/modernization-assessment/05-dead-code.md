# 05 Dead code

Telemetry: none. Every claim here is provisional.

The extractor found no entry point, so it proved nothing unreachable. Dormancy was not computed because the tree is not a git repository and has no dates (`modernization-assessment/graph.json:131`). An empty dormant list means not measured.

| Bucket | Unit | Reason | Confidence | Evidence |
|---|---|---|---|---|
| Unreachable | none | Nothing can be proven unreachable without an entry point | high | analysis (`dead_code_candidates.unreachable`) |
| Dormant | none | Not measured | low | analysis (`warnings`) |
| Unknown | PROGA | No job or transaction runs it in this tree. It may be the nightly job's program. | low | app/cbl/PROGA.cbl:2 |
| Unknown | PROGB | Called by PROGA, so it is as live as PROGA | low | app/cbl/PROGA.cbl:6 |

Do not delete either program. Ask the client which job runs PROGA.
