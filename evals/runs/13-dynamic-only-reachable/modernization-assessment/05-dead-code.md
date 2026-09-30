# 05 Dead code

Telemetry: none. Every claim here is provisional. Two warnings from `analysis` shape this file:
no last-modified dates exist because the tree is not a git repository, so the dormant bucket was
**not computed** and its empty list means not measured. No scheduler artifact was parsed.

`dead-code.json` holds the same three buckets in machine form.

| Bucket | Units | Confidence | Evidence |
|---|---|---|---|
| Unreachable | none | high | `analysis`, field `dead_code_candidates` |
| Reachable but dormant | none. Not measured, because there are no dates. | low | `analysis`, field `warnings` |
| Unknown | HIDDEN01 | low | `app/cbl/HIDDEN01.cbl:1`, `app/cbl/PGMMAIN.cbl:9` |

## Unknown. HIDDEN01

No static edge reaches HIDDEN01. PGMMAIN is reachable from the only entry point, `job:MAINJOB`
(`app/jcl/MAINJOB.jcl:2`), and PGMMAIN makes a computed call (`app/cbl/PGMMAIN.cbl:9`). HIDDEN01 is
the only other program in the tree, so it is the one program that call can be shown to reach.

The tree cannot say whether that happens. The name comes from ACCEPT (`app/cbl/PGMMAIN.cbl:8`) and
no input is defined for the job. The extractor put it in unknown, and it stays there. Do not propose
it for deletion. A program of four lines that does nothing (`app/cbl/HIDDEN01.cbl:4`) is cheap to
keep and confusing to lose: a deleted callee turns a working dispatch into a failure at run time.

What would settle it: 12 months of job logs for MAINJOB, showing which program names the ACCEPT
received. If HIDDEN01 appears, it moves to the live set and into wave 1. If it never appears and
the input list is closed, it can move toward unreachable, and only then with a client signature.

## Unreachable

Nothing. Every other node is reachable, or is the computed target node itself.

## Dormant

Not computed. Ask for the last change date of each member, from the client's source manager, and
re-run with those dates.

## Unscheduled jobs

`analysis` lists none, because a job that no parsed scheduler names is still an entry point, so
MAINJOB never shows in a bucket. It is the only job and no scheduler was parsed, so whether the job
still runs is a question for the client. See `00-summary.md`.
