# 05 Dead code

Telemetry: none. Every claim below is provisional. The extractor's candidates are in
`modernization-assessment/05a-dead-code-candidates.md`. The register is in
`modernization-assessment/dead-code.json`.

## Read this first

- **Dormancy was not computed.** The extractor warned: "No last-modified dates exist ... The dormant bucket
  was NOT computed. An empty dormant list means not measured." Every `last_modified` in `graph.json` is
  null, because the work folder is not a git repository. The empty dormant bucket below is not a finding
  that nothing is dormant. `PGMMAIN`, `PGMLIVE` and `job:MAINJOB` are reachable and their age is unknown.
  (analysis: `warnings`)
- **No scheduler was parsed.** The extractor warned that one JCL job is in the tree with no scheduler
  artifact. `analysis.unscheduled_jobs` is empty, and here that means not measured. It does not mean the
  job is scheduled. Ask whether `job:MAINJOB` still runs. (inference)
- **The tree holds one JCL job.** A program that only some other JCL runs would look unreachable here.
  This is why `PGMDEAD` is `medium`, not `high`.

## Unreachable

Proposed for deletion. `PGMDEAD` needs the three confirmations listed under the table first.

| Unit | Reason | Confidence | Evidence |
|---|---|---|---|
| `PGMDEAD` | No JCL step, scheduler entry or program names it. The tree has no computed calls and no JCL text inside a COBOL literal. Its only edge is an outgoing call to `PGMLIVE`. That call does not keep it alive, and `PGMLIVE` stays live through `PGMMAIN`. | medium | `app/cbl/PGMDEAD.cbl:4` |
| `cpy:UNUSED` | None of the three COBOL programs has a `COPY` statement, so nothing includes it. A copybook is bound at compile time, so a computed call cannot reach it. | high | `app/cpy/UNUSED.cpy:1` |

What to confirm before deleting `PGMDEAD`:

1. Twelve months of job logs or SMF records show no run of it, by any job (telemetry).
2. The full JCL library and scheduler export hold no step with `PGM=PGMDEAD`.
3. No operator procedure or TSO command runs it by name. The extractor reads only PARM and RUN cards for
   named programs (`meta.limits`).

## Reachable but dormant

Empty, and not measured. See "Read this first". If the client supplies change dates from the library
manager, rerun the extractor with real dates.

| Unit | Reason | Confidence | Evidence |
|---|---|---|---|
| none computed | Dormancy needs last-modified dates and the tree has none | low | analysis: `dead_code_candidates.dormant` is empty and `warnings` says not computed |

## Unknown

Empty. There are no computed calls, so nothing keeps this bucket open. Nothing was moved toward or away
from unknown.

| Unit | Reason | Confidence | Evidence |
|---|---|---|---|
| none | `unresolved_dynamic` is empty | high | analysis: `unresolved_dynamic` and `dead_code_candidates.unknown` |

## Changes to the extractor's buckets

None. The extractor put `PGMDEAD` and `cpy:UNUSED` in unreachable, and both stay there. I found no
run-time submit, no embedded JCL and no computed call that would move either toward unknown.
