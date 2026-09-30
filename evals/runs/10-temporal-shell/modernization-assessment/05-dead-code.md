# 05 Dead code

Telemetry: none. Every claim here is provisional. Machine-readable version: `dead-code.json`. Extractor candidates: `05a-dead-code-candidates.md`.

## What the extractor found

All three candidate lists are empty. That does not mean nothing is dead. The extractor keeps any job that no scheduler names as an entry point, because such a job might be run by hand, so `job:JOBC` is treated as reachable and never reaches a bucket. The source says otherwise, so I placed it by hand.

## Buckets

| Bucket | Unit | Confidence | Reason | Evidence |
|---|---|---|---|---|
| Unreachable | `job:JOBC` | medium | The wrapper comment calls it retired and the submit line is commented out. No other parsed scheduler names it. Provisional, because there is no telemetry and an unparsed scheduler or an operator could still submit it. | `scripts/nightly.sh:2`, `scripts/nightly.sh:6`, `jcl/JOBC.jcl:1` |
| Dormant | none | not applicable | No dates are available. The tree is not under git, so no last-modified date exists to compute dormancy from. | inference |
| Unknown | none | not applicable | The extractor found 0 computed calls, so no program could be the hidden target of one. There are also no application programs. | inference |

## What to do with `job:JOBC`

Do not delete it on this evidence alone. A comment saying "retired" is a person's statement, not proof that nothing runs the job. Ask the client to confirm from job history that JOBC has not run since the comment was written, and that no other scheduler or operator submits it. If both hold, delete `jcl/JOBC.jcl` and the commented line at `scripts/nightly.sh:6`. Until then it stays in the plan as `unassigned` in `waves.json` and as `do_not_port` in `risks.json`.

## What this register cannot see

- Any scheduler other than shell wrappers that name JCL files and Control-M XML is not parsed, so a job named only in another scheduler looks unscheduled.
- The `IEFBR14` step in each job is a system utility (`jcl/JOBA.jcl:2`). It is external to the tree and is not a dead-code candidate.
