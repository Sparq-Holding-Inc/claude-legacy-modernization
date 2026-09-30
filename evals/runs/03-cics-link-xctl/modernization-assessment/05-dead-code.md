# 05 Dead code

Telemetry: none. Every claim below is provisional. Machine form: `modernization-assessment/dead-code.json`.
The extractor's candidate list is in `05a-dead-code-candidates.md`. I kept its buckets and did not move
anything toward unreachable.

## What was not measured

- **Dormant was not computed.** The tree is not a git repository, so no unit has a last-modified date
  (analysis: `warnings`, `meta.git_dates`). An empty dormant list means not measured. It does not mean
  nothing is dormant.
- **No entry point was found**, so nothing can be proven unreachable. The extractor put every candidate in
  unknown (analysis: `dead_code_candidates`, `warnings`).
- **No unscheduled jobs and no JCL inside COBOL literals** were found, because the tree holds no JCL and
  no COBOL literal that looks like JCL (analysis: `unscheduled_jobs`, `embedded_jcl`).

## The three buckets

| Unit | Bucket | Reason | Confidence | Evidence |
|---|---|---|---|---|
| none | Unreachable | Empty. With no entry point and two open computed calls, nothing can be proven unreachable. The validator also forbids it. | high | analysis: `dead_code_candidates` |
| none | Dormant | Empty and not measured. No last-modified dates exist. | high | analysis: `warnings` |
| PROGA | Unknown | No entry point and no caller in the tree. It has a COMMAREA, so it is probably a transaction entry program defined outside this tree. Its own LINK can reach any program. | low | `app/cbl/PROGA.cbl:9`, `app/cbl/PROGA.cbl:16` |
| PROGB | Unknown | Linked from PROGA at line 12, but PROGA itself has no proven entry point. | low | `app/cbl/PROGA.cbl:12` |
| PROGC | Unknown | Transferred to from PROGA at line 20. The computed target there is bounded to PROGC by the one assignment at line 19, but PROGA has no proven entry point. | low | `app/cbl/PROGA.cbl:19`, `app/cbl/PROGA.cbl:20` |
| PROGD | Unknown | Its only static edge, the XCTL at line 23, follows an XCTL that never returns, so PROGA probably never reaches it that way. The COMMAREA-driven LINK could still reach it. Not dead. | low | inference: `app/cbl/PROGA.cbl:20`, `app/cbl/PROGA.cbl:23` |

## Dead code inside a program

This is not a bucket of the register, because it is code within a live unit. It is worth a decision.

| Where | What | Confidence | Evidence |
|---|---|---|---|
| PROGA, lines 23 to 26 | An XCTL to PROGD and a RETURN that cannot run after the unconditional XCTL at line 20. No RESP or NOHANDLE is present, so a failed XCTL abends and does not fall through. | medium | inference: `app/cbl/PROGA.cbl:20`, `app/cbl/PROGA.cbl:23-26` |

Do not propose deleting PROGD on this basis. The port must decide whether to keep these lines. That choice
goes in the Deviation Register in `06-test-strategy.md`.

## What would firm this up

12 months of CICS program usage statistics, or SMF 110 records, for these four programs and for the
region. With them, unknown can split into "ran" and "did not run". Without them, none of these four is a
candidate for deletion, and none is a candidate for instrumentation on dormancy grounds either, because
dormancy was not measured.
