# 05 Dead code

Telemetry: none. Every claim in this file is provisional. The candidates come from the extractor
(`05a-dead-code-candidates.md`). The three buckets are in `dead-code.json`.

## Unreachable

Nothing. The extractor found no program with no static path and no computed call that could reach it.
Proposed for deletion: none.

| Unit | Reason | Confidence | Evidence |
|---|---|---|---|
| none | No unit qualifies. The only program without a static caller is in the unknown bucket | high | `app/cbl/PGMMAIN.cbl:9` |

## Reachable but dormant

Nothing was flagged, and that result needs care. The extractor flags a program as dormant only when it
has a last-modified date older than five years. Here the tree is not a git checkout, so no program has
a date (`01-inventory.md` lists every date as unknown). The dormant bucket is empty because nothing
could be measured, not because the code is recent. This is inference.

| Unit | Reason | Confidence | Evidence |
|---|---|---|---|
| none | No last-modified date exists for any unit, so dormancy cannot be judged | low | inference |

## Unknown

One program.

| Unit | Reason | Confidence | Evidence |
|---|---|---|---|
| `HIDDEN01` | No JCL step, program or scheduler names it. `PGMMAIN` calls a name it reads with `ACCEPT`, and nothing bounds that name, so `HIDDEN01` could be the target. | low | `app/cbl/HIDDEN01.cbl:1`, `app/cbl/PGMMAIN.cbl:9` |

### Why `HIDDEN01` stays in unknown

It looks like dead code. Nothing calls it and its body only returns (`app/cbl/HIDDEN01.cbl:4`). A tool
that read only static edges would call it unreachable and propose deleting it. That claim would be
wrong to make.

- `PGMMAIN` is reachable. The job runs it (`app/jcl/MAINJOB.jcl:2`).
- `PGMMAIN` calls a program whose name comes from `ACCEPT` (`app/cbl/PGMMAIN.cbl:8`,
  `app/cbl/PGMMAIN.cbl:9`).
- I looked for a way to bound that name: a `VALUE` clause, a literal `MOVE`, a name table. There is
  none (`app/cbl/PGMMAIN.cbl:5`). I cannot bound the call, so I cannot move `HIDDEN01` out of unknown.

Do not delete it. Two ways to settle it, both outside the source:

1. Read the `SYSIN` values the job has run with over at least 12 months, including month-end and
   year-end. If `HIDDEN01` ever appears, it is live.
2. Instrument the call in the ported dispatcher, log every name, and keep `HIDDEN01` until a full
   business cycle has passed with no hit.

A program that has never been named in 12 months of runs can still be named once a year at close.
Silence in the logs is not proof until the log window covers close (inference).

## Computed calls that keep the bucket open

| Caller | Node | Evidence |
|---|---|---|
| `PGMMAIN` | `?dynamic:PGMMAIN:9` | `app/cbl/PGMMAIN.cbl:9` |
