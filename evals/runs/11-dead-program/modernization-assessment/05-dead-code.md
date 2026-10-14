# 05 Dead code

Telemetry: none. Every claim here is provisional.

Dormancy was not computed. The tree is not a git repository, so no last-modified dates exist (`analysis.warnings`). The empty dormant list means not measured.

| Unit | Bucket | Reason | Confidence | Evidence |
|---|---|---|---|---|
| `PGMDEAD` | unreachable | No job step runs it and nothing calls it. It calls `PGMLIVE`, which does not make it reachable. The tree has no computed calls. | medium | `app/cbl/PGMDEAD.cbl:4` |
| `cpy:UNUSED` | unreachable | No program includes it. | high | `app/cpy/UNUSED.cpy:1` |

Unknown: empty. Dormant: empty, not measured.

## Before deleting

- `PGMDEAD` is unreachable from `MAINJOB` only. Nothing in the tree says no other job, scheduler or online region starts it. Ask for runtime evidence (SMF or job logs) for 12 months, including fiscal close.
- Propose deleting `cpy:UNUSED` only after the client confirms no other tree includes it.
