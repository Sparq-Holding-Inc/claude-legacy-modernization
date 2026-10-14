# 05 Dead code

Telemetry: **none** (given as a flag). Every claim in this file is provisional.

The extractor placed nothing in any bucket (`modernization-assessment/05a-dead-code-candidates.md`; `analysis.dead_code_candidates`).

| Bucket | Count | Reason | Confidence | Evidence |
|---|---|---|---|---|
| Unreachable | 0 | Both programs are reached from a job. `PGMR` from `READJOB`, `PGMW` from `WRITEJOB` | high | `app/jcl/READJOB.jcl:2`, `app/jcl/WRITEJOB.jcl:2` |
| Reachable but dormant | 0, **not measured** | The tree is not a git repository, so no last-modified dates exist. An empty dormant list means not measured | low | `analysis.warnings` |
| Unknown | 0 | No computed calls, no embedded JCL, no run-time named programs | medium | `analysis.unresolved_dynamic`, `analysis.embedded_jcl`, `analysis.runtime_named` |

## What this does not tell you

- **Both copybooks are used.** `LAYOUTX` by PGMW and `LAYOUTY` by PGMR (`app/cbl/PGMW.cbl:11`, `app/cbl/PGMR.cbl:11`). They are not dead. But they describe one record twice (`modernization-assessment/02-coupling.md`), and one of them is redundant once the layout is unified. That is a refactor target, not dead code.
- **Both jobs count as entry points because no scheduler names them.** A job that no parsed scheduler names is still an entry point, so it never shows in a bucket. There is no scheduler in the tree, so I cannot tell whether either job still runs. Ask (`analysis.warnings`).
- **No dormancy test was possible.** Without dates or job history, "all of this runs every night" is unverified. Ask for the last 12 months of job logs for these two jobs.

`modernization-assessment/dead-code.json` has the three keys, all empty.
