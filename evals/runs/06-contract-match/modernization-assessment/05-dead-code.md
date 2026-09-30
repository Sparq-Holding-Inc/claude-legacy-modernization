# 05 Dead code

Telemetry: none. Every claim in this file is provisional. Machine-readable form:
`modernization-assessment/dead-code.json`. The extractor's candidate tables are in
`modernization-assessment/05a-dead-code-candidates.md`.

## Result

All three buckets are empty. That is not the same as "nothing is dead".

| Bucket | Count | Meaning here | Evidence |
|---|---|---|---|
| Unreachable | 0 | Both programs are reached from a JCL job (2 of 2 programs reachable) | analysis, field `dead_code_candidates` |
| Unknown | 0 | No computed call exists that could reach an unlisted program | analysis, field `unresolved_dynamic` |
| Dormant | 0, not measured | No last-modified dates exist. The tree is not a git repository, so the dormant rule did not run | analysis, field `warnings` |

## What the empty lists do not tell you

- **Dormant was not computed.** An empty dormant list means not measured. It does not mean every unit was
  changed recently. The nodes carry no last-modified date (`modernization-assessment/01-inventory.md`,
  table Programs, column Last modified, reads `unknown`).
- **Both jobs count as entry points.** With no scheduler parsed, a JCL job is an entry point whether or
  not anything still runs it (`app/jcl/READJOB.jcl:1`, `app/jcl/WRITEJOB.jcl:1`). The field
  `unscheduled_jobs` is empty, but that is because no scheduler exists to leave a job unnamed. It does not
  show that the jobs are scheduled. Whether they still run is an Open Question. Inference.
- **PGMR could be dead in effect.** It reads one record and discards it (`app/cbl/PGMR.cbl:14`). It
  produces no output, so nothing downstream would notice if it stopped. The extractor cannot see this. It
  is a candidate for instrumentation, not deletion. Inference.
- **No telemetry.** Without job history from the last 12 months, no claim here can be firmed up. Ask for
  job logs or SMF records for both jobs.

## Recommendation

Delete nothing. Instrument both jobs. Ask the client for run history for `READJOB` and `WRITEJOB`, and
for the scheduler export that would show whether either is still triggered.
