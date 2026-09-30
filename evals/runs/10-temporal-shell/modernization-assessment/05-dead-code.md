# 05 Dead code

Telemetry is `none`. Every claim here is provisional.

## Buckets

The extractor put nothing in any of the three buckets, and I kept it that way. `dead-code.json` has
all three keys, each empty, with `telemetry` set to `none`.

| Bucket | Count | Note | Evidence |
|---|---|---|---|
| Unreachable | 0 | Every node is reachable from an entry point. | analysis (`dead_code_candidates.unreachable`) |
| Dormant | 0, not measured | The tree is not a git repository, so no unit has a last-modified date. The dormant bucket was NOT computed. An empty list means not measured. | analysis (`warnings`) |
| Unknown | 0 | No computed call exists that could hide a target. | analysis (`unresolved_dynamic`) |

## JOBC

| Unit | What the source shows | Status | Confidence | Evidence |
|---|---|---|---|---|
| job:JOBC | The wrapper comment says JOBC is retired and its submit line is commented out. No parsed scheduler names it. | Not in any bucket, by design. A job no parsed scheduler names is still an entry point. Retirement candidate, unconfirmed. | low | `scripts/nightly.sh:2`, `scripts/nightly.sh:6` |

The extractor lists JOBC under `unscheduled_jobs`. It is not called dead, for these reasons:

- A comment says the job is retired. It does not prove the job never runs. Someone may still submit it by
  hand, or another scheduler that this scan did not read may still run it. That is inference.
- With telemetry `none`, nothing shows whether JOBC ran in the last 12 months.
- Its one step runs `IEFBR14` (`jcl/JOBC.jcl:2`), so keeping it costs almost nothing. Deleting it on a
  comment costs more than keeping it.

I moved nothing from one bucket to another and added nothing to `dead-code.json`. JOBC is in
`do_not_port` in `risks.json` as a provisional entry: confirm, then retire it.

## What would firm this up

- A year of job history or scheduler logs showing whether JOBC ran.
- The owner's answer to whether anything outside `scripts/nightly.sh` submits it.
- Last-modified dates for the three JCL members, from source control the tree does not carry.
