# 05 Dead code

Telemetry is `none`, as given in `--telemetry none`. Every claim in this file is provisional.

The extractor's candidate tables are in `05a-dead-code-candidates.md`. The machine readable register
is `dead-code.json`.

| Bucket | Count | Reason | Evidence |
|---|---|---|---|
| Unreachable | 0 | Both programs are entry points, defined as transactions in the CSD. The copybook is included by both. The dataset is read and written. | `app/csd/DEMO.CSD:4`, `app/csd/DEMO.CSD:6`, `app/cbl/PROGR.cbl:5`, `app/cbl/PROGW.cbl:5` |
| Unknown | 0 | There are no computed calls in reachable code, so nothing could reach an unlisted program. | `app/cbl/PROGR.cbl:6-11`, `app/cbl/PROGW.cbl:6-11` |
| Dormant | 0 | See the caveat below. The empty bucket is not evidence that the code is recent. | `app/csd/DEMO.CSD:4` |

**Caveat on dormant.** The extractor recorded `last_modified` as unknown for every node
(`graph.json` `meta.git_dates` is false, and `01-inventory.md` shows `unknown` for both programs).
The dormancy rule of 5 years needs a date, so it could not fire for any unit. Zero dormant means
"could not tell", not "all recent". Nothing here proposes deletion.

**Not in the tree.** The tree defines no transaction for anything beyond TRNW and TRNR
(`app/csd/DEMO.CSD:4-9`). Any program outside the tree is not classified here. `inference`.

## What would firm this up

12 months of CICS transaction statistics for TRNR and TRNW, and SMF or job logs for the nightly batch
cycle. Without them, no claim in this file is better than static reachability.
