# 05 Dead code

Telemetry: none. Every claim below is provisional.

| Bucket | Count | Confidence | Evidence |
|---|---|---|---|
| Unreachable | 0 | high | `analysis.dead_code_candidates.unreachable` in `modernization-assessment/graph.json:297` |
| Reachable but dormant | 0, **not measured** | low | `modernization-assessment/graph.json:382` |
| Unknown | 0 | medium | `analysis.dead_code_candidates.unknown` in `modernization-assessment/graph.json:299` |

- **Unreachable and unknown are empty because both programs are reached.** Each is called from a JCL step of an entry-point job (`app/jcl/READJOB.jcl:2`, `app/jcl/WRITEJOB.jcl:2`), and the tree has no computed call that could reach anything else (`modernization-assessment/graph.json:302`).
- **The dormant list is empty because it was not computed.** The target is not a git repository, so no last-modified date exists (`modernization-assessment/graph.json:382`). An empty list here means not measured. It does not mean both programs are recently touched.
- **Unscheduled jobs.** The extractor lists none (`modernization-assessment/graph.json:323`), but only because no scheduler was parsed at all, so a job is not unscheduled relative to anything (`modernization-assessment/graph.json:383`). Whether READJOB and WRITEJOB still run is a question for the client. The dataset name `SPARQ.TEST.MASTER` suggests test data (inference), and it is worth asking whether this pair is a live cycle or a test fixture.
- **Deletion is not proposed for anything.** Run history for the last 12 months would turn these claims into evidence.
