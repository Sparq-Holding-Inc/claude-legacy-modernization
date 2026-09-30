# 05 Dead code

Telemetry: `none`. Every claim below is provisional. The machine-readable register is
`modernization-assessment/dead-code.json:1`.

## Result

| Bucket | Count | Confidence | Evidence |
|---|---|---|---|
| Unreachable | 0 | low | `analysis` field `dead_code_candidates` |
| Reachable but dormant | 0. Not measured. | low | `analysis` field `warnings` |
| Unknown | 0 | low | `analysis` field `unresolved_dynamic` |

The extractor found no candidate in any bucket (`analysis` field `dead_code_candidates`). Every program,
the copybook and the dataset are reachable from one of the two jobs (`analysis` fields
`reachable_nodes` and `reachable_programs`: 7 nodes, 2 programs). PGMR is reached from `job:READJOB`
(`app/jcl/READJOB.jcl:2`). PGMW is reached from `job:WRITEJOB` (`app/jcl/WRITEJOB.jcl:2`). LAYOUTX is
included by both programs (`app/cbl/PGMR.cbl:11`, `app/cbl/PGMW.cbl:11`).

## What an empty list does and does not mean

- **Dormant was not computed.** The extractor warns that no last-modified dates exist, because the
  target is not a git repository (`analysis` field `warnings`). An empty dormant list here means
  not measured. Every node shows `last_modified: null` (`modernization-assessment/graph.json:1`).
  Ask for the source control history or the file dates.
- **Both jobs are entry points only by default.** No scheduler artifact was parsed, so a job that no
  scheduler names still counts as an entry point (`analysis` field `warnings`). That is why the
  tree shows no dead code. It does not show that either job still runs. `analysis` field
  `unscheduled_jobs` is empty because there is no scheduler to compare against.
- **No computed calls.** The unknown bucket is empty because there is nothing that could reach an
  unlisted program (`analysis` field `unresolved_dynamic`). It is an empty result on a 2 program tree.
- **No telemetry.** With no run history, "reachable" means reachable on paper. Ask for job logs or SMF
  records to see whether READJOB and WRITEJOB ran in the last 12 months.

## Items to instrument, not delete

| Unit | Why | Confidence | Evidence |
|---|---|---|---|
| `job:READJOB` | Nothing shows it runs. Its dataset is named TEST. | low | `app/jcl/READJOB.jcl:3`, inference |
| `job:WRITEJOB` | Same. DISP=NEW would fail a repeat run, which suggests something removes the dataset first, or the job runs once. | low | `app/jcl/WRITEJOB.jcl:3`, inference |

These are instrumentation requests for the client, not entries in `dead-code.json`.
