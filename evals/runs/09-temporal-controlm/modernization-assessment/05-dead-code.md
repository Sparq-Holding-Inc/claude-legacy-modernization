# 05 Dead code

Telemetry: none. Every dead-code claim in this file is provisional, and here that means the register is empty because nothing
could be tested, not because everything is live. The candidates the extractor computed are in `05a-dead-code-candidates.md`.
The register is in `modernization-assessment/dead-code.json:1-6`.

## The three buckets

| Bucket | Count | Reason | Evidence |
|---|---|---|---|
| Unreachable | 0 | All 7 nodes are reachable from an entry point. Four entry points exist: JOBA, JOBB and their two scheduler entries. | `app/scheduler/nightly.xml:4`, `app/scheduler/nightly.xml:8`, `app/jcl/JOBA.jcl:1`, `app/jcl/JOBB.jcl:1` |
| Reachable but dormant | 0, not measured | The extractor could not read last-modified dates, because the tree is not a git repository. The dormant bucket was not computed. An empty list here means not measured. | analysis: `warnings`, third entry |
| Unknown | 0 | No computed call exists, so nothing can be reached by a computed call. | analysis: `unresolved_dynamic` is empty |

## What this does and does not show

- There is no COBOL in the tree, so there is no program that could be dead (`modernization-assessment/01-inventory.md:14-17`). The only
  program named is IEFBR14, a system utility outside the tree (`app/jcl/JOBA.jcl:2`, `app/jcl/JOBB.jcl:2`).
- Both jobs are named by the scheduler, so neither appears in `unscheduled_jobs` (analysis field, empty). Whether either job still runs in production is a
  separate question. A scheduler entry that exists is not proof that the job runs. That is a question for the client (see the open questions in `00-summary.md`).
- One output has no reader inside the tree: condition JOBB-DONE (`app/scheduler/nightly.xml:11`). It is a condition, not a node, so the extractor
  does not list it as dead. It may feed a folder we were not given (inference).
- Nothing here can be proposed for deletion. With telemetry `none` and no dates, the right next step is to ask for job run history from the scheduler
  (the last 12 months), and only then revisit this register.
