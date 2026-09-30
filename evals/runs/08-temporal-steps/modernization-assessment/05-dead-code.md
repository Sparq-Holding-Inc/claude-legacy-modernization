# 05 Dead code

Telemetry: none. Every dead-code claim here is provisional. The candidates are in
`modernization-assessment/05a-dead-code-candidates.md`. The register is `modernization-assessment/dead-code.json`.

| Bucket | Units | Confidence | Evidence |
|---|---|---|---|
| Unreachable | none | high | `analysis` field `dead_code_candidates` |
| Reachable but dormant | none. **Not measured.** | low | `analysis` field `warnings` |
| Unknown | none | high | `analysis` field `unresolved_dynamic` is empty |

## Dormant is not measured

The target is not a git repository, so no unit has a last-modified date. The dormant bucket was NOT
computed (`analysis` field `warnings`). An empty dormant list therefore means not measured. It does not
mean nothing is dormant. The same reading applies to the unreachable bucket only in one direction: an
empty unreachable list is a real result, because all three programs are reached from `job:SEQJOB`
(`app/jcl/SEQJOB.jcl:2`, `app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:4`).

## Jobs that no scheduler names

`job:SEQJOB` counts as an entry point, so it never shows in a bucket. No scheduler artifact was
parsed (`analysis` field `warnings`), so nothing says whether SEQJOB still runs. Ask.

## External program

`ext:IEFBR14` is a system utility that does nothing. It is not in the tree, and it is called at
`app/jcl/SEQJOB.jcl:5`. It is not a candidate for deletion. The step that calls it is a candidate
for review (inference): a step that runs a null program after the last real step adds nothing.
