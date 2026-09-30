# 05 Dead code

Telemetry: none. Every claim in this file is provisional.

Two warnings from the extractor shape everything below, and both are gaps, not details.

- No entry points were found. The tree has no JCL job, CSD transaction, scheduler job or wrapper. So
  nothing can be proven unreachable, and every candidate is unknown (analysis `warnings`).
- No last-modified dates exist. The tree is not a git repository. The dormant bucket was not computed.
  The empty dormant list below means not measured. It does not mean nothing is dormant (analysis
  `warnings`).

Two facts about the code sit behind the unknown bucket: `PROGA` makes a computed call at
`app/cbl/PROGA.cbl:9`, and the name it calls is read at run time by `ACCEPT` at
`app/cbl/PROGA.cbl:8`. So the target set cannot be bounded. Any program with no static caller could be
the target, and that means both programs in the tree.

## The three buckets

| Bucket | Unit | Reason | Confidence | Evidence |
|---|---|---|---|---|
| Unreachable | none | Not computed as a finding. With no entry point, nothing can be proven unreachable. The validator also forbids moving a program from unknown to unreachable. | high | analysis (`dead_code_candidates.unreachable` is empty) |
| Reachable but dormant | none, not measured | Needs git dates or telemetry. Neither exists in the tree or was supplied. | high that it was not measured | analysis (`warnings`, "dormant bucket was NOT computed") |
| Unknown | `PROGA` | No entry point names it, and it has no static caller. Not shown to be dead. Do not delete. | low | `app/cbl/PROGA.cbl:9` |
| Unknown | `PROGB` | No static caller. `PROGA`'s computed call could name it, and cannot be shown to exclude it. Do not delete. | low | `app/cbl/PROGB.cbl:1`, `app/cbl/PROGA.cbl:9` |

## What I did not do

- I did not call `PROGB` dead because it does nothing. A program that only does `GOBACK`
  (`app/cbl/PROGB.cbl:4`) may be a deliberate stub that a caller names. Being trivial is not being
  unreachable. That is inference.
- I did not call `PROGA` an entry point. It looks like a driver because it reads a name and calls it,
  but nothing in the tree runs it. That is inference from `app/cbl/PROGA.cbl:8`.
- I did not propose deletion of anything. Instrumentation is the proposal: log the name PROGA
  receives on every run for a full business cycle including month-end and fiscal year-end. That log
  is the telemetry that would turn the unknown bucket into evidence.

## What would change this file

- JCL naming `PROGA` gives an entry point, and then `PROGB` is either shown reachable through the
  computed call or stays unknown while the call stays open.
- Job history or SYSIN capture from production. With the names it holds, the unknown bucket
  can be firmed up. Even then, a name that appears only at year-end needs a window that includes it.
- Source control dates for the two files, so the dormant rule can run.
