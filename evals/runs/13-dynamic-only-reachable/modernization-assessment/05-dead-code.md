# 05 Dead code

Telemetry: none. Every claim here is provisional. Machine-readable: `modernization-assessment/dead-code.json`.

> Dormancy was not computed. The tree is not a git repository and has no last-modified dates (`analysis` field `warnings`). The empty dormant list means not measured.

| Bucket | Unit | Reason | Confidence | Evidence |
|---|---|---|---|---|
| Unreachable | none | The extractor found none, and with a computed call in reachable code it could not safely call anything unreachable. | medium | `analysis` field `dead_code_candidates` |
| Dormant | none | Not measured. | low | `analysis` field `warnings` |
| Unknown | HIDDEN01 | No JCL step or static call reaches it. PGMMAIN calls a run-time name, so it could run. | low | `app/cbl/HIDDEN01.cbl:1`, `app/cbl/PGMMAIN.cbl:9` |

## HIDDEN01

Do not delete it. The name suggests a program kept out of the static graph on purpose, but the name is not evidence and I have not used it as one. It does nothing (`app/cbl/HIDDEN01.cbl:3` is only `GOBACK`), so it could be a stub, a test target or a placeholder for dispatch. Instrument the call in PGMMAIN to log every value of `WS-PGM-NAME` for one full business cycle, then decide. That is the evidence that would move it.

The computed call could not be bounded: there is no table of names in the source (`app/cbl/PGMMAIN.cbl:5`).

## Unscheduled jobs

The extractor lists none (`analysis` field `unscheduled_jobs`), but that is only because no scheduler was parsed. MAINJOB's run schedule is unknown (`analysis` field `warnings`).
