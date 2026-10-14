# 05 Dead code

Telemetry: none. Every claim here is provisional.

Dormancy was **not measured**. The target is not a git repository, so no unit has a last-modified date (`analysis`: `warnings`). The empty dormant list means not measured, not nothing is old.

## Extractor buckets

| Bucket | Units | Confidence | Evidence |
|---|---|---|---|
| Unreachable | none | high | `analysis`: `dead_code_candidates` |
| Dormant | none (not computed) | low | `analysis`: `warnings` |
| Unknown | none, no computed calls exist | high | `analysis`: `unresolved_dynamic` |

`dead-code.json` has the three keys, all empty.

## The one item worth a decision: JOBC

JOBC never appears in a bucket, because a JCL job counts as an entry point (`analysis`: `entry_points`). The wrapper says it is retired and has its submit commented out, so it is almost certainly dead. I did not add it to `unreachable`, since the validator allows only what the extractor called unreachable.

| Unit | Claim | Confidence | Evidence |
|---|---|---|---|
| `job:JOBC` | Retired from the nightly chain. No parsed scheduler or wrapper names it. | medium (inference that it runs nowhere else) | `scripts/nightly.sh:2`, `scripts/nightly.sh:6` |

JOBC could still be submitted by hand or by a scheduler outside the tree. Ask. Without telemetry the proposal is to instrument it for one business cycle (including month-end), then delete. It is not a deletion on the comment alone.
