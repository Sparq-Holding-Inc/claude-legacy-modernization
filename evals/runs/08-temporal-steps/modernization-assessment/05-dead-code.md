# 05 Dead code

Telemetry: none. Every claim here is provisional.

| Bucket | Count | Confidence | Evidence |
|---|---|---|---|
| Unreachable | 0 | high | `app/jcl/SEQJOB.jcl:2`, `app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:4` |
| Unknown | 0 | medium | `app/cbl/PGMA.cbl:4` |
| Dormant | 0 (not measured) | low | inference |

- Unreachable is empty because SEQJOB runs PGMA, PGMB and PGMC by name (`app/jcl/SEQJOB.jcl:2`, `app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:4`). All three are reachable.
- Unknown is empty because the tree has no computed call.
- Dormant was NOT computed. The tree is not a git repository, so no last-modified dates exist. An empty list means not measured, not that nothing is old.
- SEQJOB itself is an entry point, since no scheduler names it. Whether it still runs is an open question for the client. `inference`
- A reachable job is not proof that it succeeds. The duplicate step name on `app/jcl/SEQJOB.jcl:5` may stop the job from running at all. If so, PGMA to PGMC are reachable on paper and dead in practice. `inference`
