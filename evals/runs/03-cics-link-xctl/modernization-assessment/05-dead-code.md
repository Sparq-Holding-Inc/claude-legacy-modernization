# 05 Dead code

**Telemetry: none. Every claim here is provisional.**

Two warnings from the extractor change what these buckets mean (`analysis` field `warnings`):

- No entry points exist, so nothing can be proven unreachable.
- No last-modified dates exist (not a git repository). The dormant bucket was **not computed**. An empty dormant list means not measured, not that nothing is old.

| Unit | Bucket | Reason | Confidence | Evidence |
|---|---|---|---|---|
| PROGA | unknown | No entry points. Its callers were not supplied. | low | `app/cbl/PROGA.cbl:2` |
| PROGB | unknown | Linked from PROGA only. | low | `app/cbl/PROGA.cbl:12` |
| PROGC | unknown | XCTL target of PROGA. | low | `app/cbl/PROGA.cbl:20` |
| PROGD | unknown | XCTL target of PROGA. | low | `app/cbl/PROGA.cbl:23` |

Unreachable: none. Dormant: not measured.

## What would change this

A CSD or transaction list would make PROGA an entry point and PROGB to PROGD reachable. That moves them out of unknown. Twelve months of CICS statistics (transaction counts by program) would settle whether any of them runs. Until then the computed LINK at `app/cbl/PROGA.cbl:16` means any program on the region could be a target, so no program should be proposed for deletion.

One inference to check: PROGD is reached by the XCTL at line 23, which follows an XCTL that never returns (`app/cbl/PROGA.cbl:20`). If control leaves at line 20, PROGD may never run. This is not enough to call it dead. inference.
