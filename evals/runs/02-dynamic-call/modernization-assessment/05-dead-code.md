# 05 Dead code

Telemetry: none. Every claim here is provisional. Dormancy was not computed, because there are no last-modified dates (`modernization-assessment/graph.json:146`). The empty dormant list means not measured.

| Unit | Bucket | Confidence | Evidence |
|---|---|---|---|
| PROGA | unknown | low | `app/cbl/PROGA.cbl:9` |
| PROGB | unknown | low | `app/cbl/PROGB.cbl:4` |

- **Unreachable:** empty. With no entry points, nothing can be proven unreachable (`modernization-assessment/graph.json:147`).
- **Dormant:** empty, not measured.
- **Unknown:** both programs. PROGA's computed call could reach PROGB (`app/cbl/PROGA.cbl:9`). Do not delete either.
- Unscheduled jobs: none were found, because no JCL was supplied.
