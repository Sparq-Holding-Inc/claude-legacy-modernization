# 05 Dead code

Telemetry: `none`. **Every claim below is provisional.** Dormancy was not computed because the tree is not a git repository and has no last-modified dates (`modernization-assessment/graph.json:153`). The empty dormant list means not measured, not none.

With no entry points (`modernization-assessment/graph.json:154`), nothing can be proven unreachable. Every unit is unknown.

| Bucket | Unit | Confidence | Evidence |
|---|---|---|---|
| Unreachable | none | n/a | `analysis`: `dead_code_candidates.unreachable` is empty |
| Dormant | none (not measured) | n/a | `analysis`: warnings, dormancy not computed |
| Unknown | PROGA | low | `app/cbl/PROGA.cbl:2` |
| Unknown | PROGB | low | `app/cbl/PROGB.cbl:2` |
| Unknown | cpy:SHARED01 | low | `app/cbl/PROGA.cbl:5`, `app/cbl/PROGB.cbl:5` |

Do not delete any of these. They are unknown because the JCL or scheduler that would run them was not supplied. Ask the client whether PROGA and PROGB run in the nightly cycle.

No computed calls exist (`analysis`: `unresolved_dynamic` is empty), so no hidden caller is known. That does not make the programs dead. It means the callers are outside this tree.
