# 05. Dead code

**Telemetry: none** (`modernization-assessment/dead-code.json:2`). The client cannot say which
programs ran in the last 12 months. Every claim below is therefore provisional and rests on static
reachability alone. That said, this is the strongest form static reachability takes — see
"Why these claims are unusually strong" below.

The extractor's candidates are in `05a-dead-code-candidates.md`. The three buckets are in
`dead-code.json`. No item was moved between buckets.

## The three buckets

| Bucket | Count | Items | Evidence | Confidence |
|---|---|---|---|---|
| Unreachable | 2 | `PGMDEAD`, `cpy:UNUSED` | `app/cbl/PGMDEAD.cbl:2`, `app/cpy/UNUSED.cpy:1` | high |
| Reachable but dormant | 0 | — | `analysis.warnings` — **not measured**, see below | n/a |
| Unknown | 0 | — | `analysis` (`unresolved_dynamic`, `embedded_jcl`, `runtime_named` all empty) | high |

## Unreachable — propose for deletion

| Unit | Reason | Evidence | Confidence |
|---|---|---|---|
| `PGMDEAD` | Nothing runs it. No JCL step names it (`app/jcl/MAINJOB.jcl:2` runs `PGMMAIN`, and it is the only step in the only job), no COBOL program calls it, and it is not the target of any computed call because there are none. It is a complete program — it calls `PGMLIVE` and GOBACKs — that no path reaches. | `app/cbl/PGMDEAD.cbl:2`, `app/cbl/PGMDEAD.cbl:4` | high |
| `cpy:UNUSED` | No program includes it. None of the three COBOL programs has a DATA DIVISION, so there is no COPY statement in the tree at all; each goes IDENTIFICATION DIVISION straight to PROCEDURE DIVISION. | `app/cpy/UNUSED.cpy:1`, `app/cbl/PGMMAIN.cbl:3` | high |

### Why these claims are unusually strong

A dead-code claim over a static graph is normally weak because a computed call could reach the
program at run time. Here, every escape hatch the extractor knows how to look for is empty:

| Escape hatch | Present? | Evidence |
|---|---|---|
| Computed call (`CALL WS-PROGRAM`) | none in the tree | `analysis.unresolved_dynamic` = `[]` |
| JCL text inside a COBOL literal, submitted at run time | none | `analysis.embedded_jcl` = `[]` |
| Program named in a PARM or a TSO `RUN PROGRAM` card | none | `analysis.runtime_named` = `[]` |
| Source file the extractor could not parse | none | `modernization-assessment/graph.json:155` (`unparsed` = `[]`); `meta.files_seen` accounts for all 5 files |

So within the supplied tree, the reachability result is not merely the best available guess — it
is complete. That is a genuinely rare position and it should be said plainly.

### What would still make it wrong

One thing, and it is outside the tree: **a caller that was not supplied.** A scheduler could
submit a job that runs `PGMDEAD`; an operator could submit it by hand; a program in a load library
not represented in these five files could CALL it. Nothing in `graph.json` can see any of those.
The extractor also warns that no scheduler artifact was parsed at all
(`analysis.warnings`), so the one artifact class most likely to name `PGMDEAD` is precisely the
one missing.

**Recommendation.** Propose both for deletion, and gate the deletion on two checks a human runs,
not on this document:

1. Search the client's full JCL and scheduler libraries for the string `PGMDEAD`. Not just the
   five files here (`app/cbl/PGMDEAD.cbl:2`).
2. Search their full copybook consumers for `COPY UNUSED` (`app/cpy/UNUSED.cpy:1`).

If both come back empty, delete. If either does not, the unit was never really in this tree's
scope and this assessment was scoped too narrowly — which is itself the finding.

### One sequencing note

`PGMDEAD` contains `CALL 'PGMLIVE'` (`app/cbl/PGMDEAD.cbl:4`). `PGMLIVE` is live and in wave 1
(`modernization-assessment/waves.json:9`). Resolve `PGMDEAD` **before** the wave-1 port touches
`PGMLIVE`, so that a developer grepping for `PGMLIVE`'s callers sees one call site and not two.
This is covered in `03-waves.md`.

## Reachable but dormant — nothing, because nothing was measured

The dormant list is empty, and **empty here means not measured, not "nothing is dormant."** The
extractor reports `git_dates: false` and warns: "No last-modified dates exist (the target is not a
git repository, or `--no-git` was used). The dormant bucket was NOT computed"
(`analysis.warnings`). Every node in `graph.json` carries `last_modified: null`.

The dormancy rule was configured for 5 years against an as-of date of 2026-09-30
(`analysis.dormant_years`, `analysis.as_of`) and then had no dates to apply itself to.

Nothing should be instrumented or retired on the strength of an empty dormant list. If the client
wants a dormancy signal, the tree has to arrive as a git repository, or with mainframe dataset
last-referenced dates supplied separately.

## Unknown — genuinely empty

This is the one bucket that is empty for a good reason rather than a missing input. The unknown
bucket exists to hold programs that static analysis did not reach but a computed call might. There
are no computed calls (`analysis.unresolved_dynamic` = `[]`), so the bucket has nothing to hold.

## Entry points and unscheduled jobs

`analysis.unscheduled_jobs` is empty, but read that alongside the warning that **no scheduler
artifact was parsed at all** (`analysis.warnings`). `job:MAINJOB` is treated as an entry point
because it is a JCL job (`app/jcl/MAINJOB.jcl:1`), not because any scheduler was found naming it.
Whether it still runs — nightly or otherwise — is a question for the client, and it is in
Open Questions.

## Summary for the client

| Claim | Provisional on | Evidence | Confidence |
|---|---|---|---|
| `PGMDEAD` can be deleted | No caller outside the supplied five files | `app/cbl/PGMDEAD.cbl:2` | high, within scope; medium overall |
| `cpy:UNUSED` can be deleted | No consumer outside the supplied five files | `app/cpy/UNUSED.cpy:1` | high, within scope; medium overall |
| Nothing is dormant | **Do not rely on this.** Dormancy was not computed. | `analysis.warnings` | n/a |
| Nothing is unknown | Holds within the tree; no dynamic dispatch exists to create uncertainty | `analysis` | high |
