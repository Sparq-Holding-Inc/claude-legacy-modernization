# 05 Dead code

Telemetry is `none`. Every dead-code claim below is provisional.

## Result

| Bucket | Count | Evidence |
|---|---|---|
| Unreachable | 0 | `app/jcl/SEQJOB.jcl:2` |
| Reachable but dormant | 0 | inference |
| Unknown | 0 | `app/cbl/PGMA.cbl:4` |

## Why each bucket is empty

- **Unreachable: 0.** All nine nodes are reachable from the one entry point, `job:SEQJOB`. Each
  program is run by a step of that job. Evidence: `app/jcl/SEQJOB.jcl:2`, `app/jcl/SEQJOB.jcl:3`,
  `app/jcl/SEQJOB.jcl:4`.
- **Unknown: 0.** The tree has no computed call, so no program is held open by one. Evidence:
  `app/cbl/PGMA.cbl:4`, `app/cbl/PGMB.cbl:4`, `app/cbl/PGMC.cbl:4`.
- **Dormant: 0, and this is a gap, not a finding.** Every `last_modified` is null. The work folder
  is not under git, so the extractor had no dates. Dormancy could not be tested. An empty dormant list
  does not mean the code is fresh. Ask for last-change dates from the client's source control.
  Evidence: inference.

## Reachable, but probably does nothing

The last step, on line 5, runs IEFBR14 with no DD statements. IEFBR14 is a system null program, so
this step appears to do nothing. It is reachable, so it is not in any bucket. It is listed under
`do_not_port` in `risks.json` as a candidate, and needs the client to confirm that no restart or
scheduler rule names it. Do not delete on this reading alone. Inference. Evidence:
`app/jcl/SEQJOB.jcl:5`.

## What would change this

- A scheduler export could show SEQJOB is never triggered. That would make the whole tree dormant.
  Evidence: inference.
- Job logs or SMF records for the last 12 months would turn every line above from provisional into
  evidence. Evidence: inference.
