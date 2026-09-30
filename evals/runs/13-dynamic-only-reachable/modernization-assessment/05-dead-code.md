# 05 Dead code

Telemetry is `none` (given as a flag). Every claim below is provisional. Nothing here is a proposal
to delete. The candidates are in `05a-dead-code-candidates.md` and the register is in
`modernization-assessment/dead-code.json`.

## The three buckets

| Bucket | Units | Confidence | Evidence |
|---|---|---|---|
| Unreachable | none | high | `analysis`, field `dead_code_candidates` |
| Reachable but dormant | none. **Not measured**, see below | low | `analysis`, field `warnings` |
| Unknown | `HIDDEN01` | low | `app/cbl/PGMMAIN.cbl:9` |

## Unknown: `HIDDEN01`

No JCL step, program or scheduler names `HIDDEN01` (`analysis`, field `dead_code_reasons`). The
extractor did not put it in unreachable, because reachable code makes a computed call. `PGMMAIN`
issues `CALL WS-PGM-NAME` (`app/cbl/PGMMAIN.cbl:9`), and the name is read with `ACCEPT`
(`app/cbl/PGMMAIN.cbl:8`) into a field with no `VALUE` clause (`app/cbl/PGMMAIN.cbl:5`). Any program
without a static caller might be the target, and `HIDDEN01` is the only one in the tree.

I did not move it, and I could not bound the call: the value is not in the source. `inference`

`HIDDEN01` holds no logic (`app/cbl/HIDDEN01.cbl:4`). A program that does nothing is a plausible dead
stub. It is equally plausible as a placeholder that a run-time name selects, which is the shape of
something that runs once a year. The source cannot tell those apart. `inference`

## Unreachable: none

With one computed call in reachable code, no program can be called unreachable. The extractor's rule
is that a program is unreachable only when no reachable code makes a computed call
(`05a-dead-code-candidates.md`, first section). While `app/cbl/PGMMAIN.cbl:9` stands, this bucket
stays empty for any program without a caller.

## Dormant: not measured

The tree is not a git repository, so no file has a last-modified date, and the dormant bucket was not
computed (`analysis`, field `warnings`). The empty dormant list means not measured, not that nothing
is dormant. `PGMMAIN` and `job:MAINJOB` are reachable, and their age is unknown
(`01-inventory.md`, Programs table). Ask for the source control history, or file dates from the
client.

## Jobs the scheduler was not asked about

`analysis.unscheduled_jobs` is empty, because with no scheduler artifact the extractor treats every
job as an entry point. `job:MAINJOB` therefore never shows in a bucket (`analysis`, fields
`entry_points` and `unscheduled_jobs`). That does not show that it still runs. It is in the Open
Questions.

## What would firm this up

- Twelve months of job logs or SMF records for `MAINJOB`: which programs ran, and what the
  `ACCEPT` supplied. That single input would settle the unknown bucket for `HIDDEN01`. `inference`
- The `SYSIN` or wrapper that feeds `WS-PGM-NAME`. The JCL in the tree has none
  (`app/jcl/MAINJOB.jcl:2`).
