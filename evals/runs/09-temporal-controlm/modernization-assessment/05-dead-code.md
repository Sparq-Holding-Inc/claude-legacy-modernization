# 05 Dead code

Telemetry: **none**. Every claim here is provisional. Candidates: `05a-dead-code-candidates.md`. Machine-readable: `modernization-assessment/dead-code.json:1`.

| Bucket | Count | Confidence | Evidence |
|---|---|---|---|
| Unreachable | 0 | high that the extractor found none | `analysis` field `dead_code_candidates.unreachable` |
| Reachable but dormant | 0, **not measured** | n/a | `analysis` field `warnings` (no last-modified dates) |
| Unknown | 0 | high that no computed call exists | `analysis` field `unresolved_dynamic` |

- **Unreachable is empty by construction.** Every node in the tree is reachable from an entry point (`analysis` field `reachable_nodes` is 7 of 7). The only units are two jobs and their steps, and each job is an entry point (`app/jcl/JOBA.jcl:1`, `app/jcl/JOBB.jcl:1`).
- **Dormant is not measured, and an empty list does not mean nothing is old.** The target is not a git repository, so there are no last-modified dates. The extractor says the dormant bucket was not computed (`analysis` field `warnings`). Re-run on a clone that has history, or give file dates, to measure it. Confidence: low.
- **Unknown is empty** because there is no computed call anywhere (`analysis` field `unresolved_dynamic` is empty).
- **Unscheduled jobs:** none. Both jobs are named by the scheduler (`app/scheduler/nightly.xml:4`, `app/scheduler/nightly.xml:8`). The reverse question is open: whether other jobs run in the real nightly cycle that this file does not list. `inference`.
- **What would change this.** Job logs or SMF for 12 months would show whether JOBA and JOBB ran at all. Both run IEFBR14 (`app/jcl/JOBA.jcl:2`, `app/jcl/JOBB.jcl:2`), which does nothing, so a run history cannot tell us whether the pair is a live cycle or a leftover. Ask the client.
