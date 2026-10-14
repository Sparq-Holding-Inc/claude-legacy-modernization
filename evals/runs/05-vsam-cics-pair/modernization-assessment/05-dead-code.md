# Dead code

Telemetry: none. Every claim here is provisional.

| Bucket | Units | Confidence | Evidence |
|---|---|---|---|
| Unreachable | none | high | analysis: `dead_code_candidates.unreachable` is empty |
| Dormant | none, **not measured** | n/a | analysis: `warnings` says dormancy was not computed |
| Unknown | none | high | analysis: `dead_code_candidates.unknown` is empty |

- Both programs are entry points through the CSD (app/csd/DEMO.CSD:4, app/csd/DEMO.CSD:6), so both are reachable. The copybook is included by both (app/cbl/PROGR.cbl:5, app/cbl/PROGW.cbl:5).
- The dormant list is empty because the tree is not a git repository and no last-modified dates exist. An empty list means not measured. It does not mean nothing is old.
- There are no computed calls (`analysis.unresolved_dynamic` is empty), so no unknown bucket arises from one.
- No scheduler was parsed. Whether the transactions are used in production is unknown. The dataset name contains TEST (app/csd/DEMO.CSD:2), so the whole tree may be a demo region (inference).

Machine form: `dead-code.json`. Extractor candidates: `05a-dead-code-candidates.md`.
