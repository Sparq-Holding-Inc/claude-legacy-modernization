# 03 Waves

**No waves can be proposed.** The tree has no entry point: no JCL job, CSD transaction, scheduler job or wrapper (`analysis`: `entry_points` is empty; `meta.files_seen` shows jcl 0, csd 0, controlm 0, shell 0). A wave needs an independent deploy, an independent rollback and a testable boundary. Without a job or transaction there is no boundary to test. Inventing waves would be fiction.

`modernization-assessment/waves.json:1` has `"waves": []` and target state `refactor`. Both programs are in `unassigned`.

| Unit | Reason unplaced | Evidence | Confidence |
|---|---|---|---|
| PROGA | No entry point in the tree | `app/cbl/PROGA.cbl:2` | high |
| PROGB | No entry point in the tree | `app/cbl/PROGB.cbl:2` | high |

## What a plan would look like once the client supplies the missing files

Inference only, to show intent, not a plan:

- PROGA and PROGB share `SHARED01` (`app/cbl/PROGA.cbl:5`, `app/cbl/PROGB.cbl:5`). They should move in the same wave, or the copybook stays frozen until both have moved.
- The nightly batch cycle is the must-not-break anchor. The JCL job stream or scheduler export that defines it decides the wave order. Until we have it, "the nightly batch cycle" maps to no unit.

## Deviations

None. No extractor plan existed to deviate from.
