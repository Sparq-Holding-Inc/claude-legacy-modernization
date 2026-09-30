# 05 Dead code

Telemetry: none. Every claim in this file is provisional. The register is in `modernization-assessment/dead-code.json`.

## Result

All three buckets are empty. The extractor's candidates are in `05a-dead-code-candidates.md`, and I kept them as they are.

| Bucket | Units | Reason | Confidence | Evidence |
|---|---|---|---|---|
| Unreachable | none | Every unit is reached from `job:READJOB` or `job:WRITEJOB`. Both jobs are entry points (`analysis`, field `entry_points`). | medium | `app/jcl/READJOB.jcl:2`, `app/jcl/WRITEJOB.jcl:2` |
| Reachable but dormant | none. Not measured. | No last-modified dates exist, because the work folder is not a git repository. The extractor did not compute this bucket. An empty list here means not measured. | low | analysis (field `warnings`) |
| Unknown | none | The extractor found no computed call, so no reachable code could reach an unlisted program (`analysis`, field `unresolved_dynamic`). | medium | analysis (field `unresolved_dynamic`) |

## What is not proved

- **Dormancy was not measured.** With no git history and no telemetry, I cannot say whether either job still runs. Nothing here proposes deletion on a date.
- **No scheduler was parsed.** A job that no parsed scheduler names still counts as an entry point, so it never shows in a bucket (`analysis.warnings`). I cannot tell whether WRITEJOB and READJOB still run in the nightly cycle. That is a question for the client (`00-summary.md`).
- **The dataset name says TEST.** SPARQ.TEST.MASTER (`app/jcl/WRITEJOB.jcl:3`) may be a test fixture. If the whole pair is a test harness that nobody runs, the assessment describes dead code. Only the client can say so, and that would be a finding of its own.

## Copybooks

Both copybooks are included by a reachable program (`app/cbl/PGMW.cbl:11`, `app/cbl/PGMR.cbl:11`), so neither is unreachable. They duplicate one layout (see `02-coupling.md`). That is a consolidation candidate for wave 2, and it is not dead code.
