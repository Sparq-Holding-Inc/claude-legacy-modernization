# 00 Summary

Assessment of the tree in `.` (2 COBOL programs, 11 lines, 1 call edge). Facts came from `extract.py`.
Judgment is mine, and it is labeled `inference` where the tree does not show it.

## Scoping answers

| Question | Answer | How it was set |
|---|---|---|
| Target state | refactor | `--target refactor` flag |
| What must not break | the nightly batch cycle | `--must-not-break` flag |
| Runtime telemetry | none | `--telemetry none` flag. Every dead-code claim is provisional. |

All three came as flags, so no defaults were applied and nothing was assumed.

## Result

- **Wave count: 1.** PROGA and PROGB are one deployable unit: one static call, no shared dataset, no
  cycle, no articulation point (`app/cbl/PROGA.cbl:6`, `02-coupling.md`). I did not invent a second wave.
  See `03-waves.md` for what I would cut if the system were ten times larger.
- **Estimate:** 5 to 10 person-days for wave 1, low confidence. The range is driven by the missing JCL and
  scheduler, not by the code (`04-estimate.md`).
- **Dead code:** nothing is unreachable. Both programs are unknown, because the tree has no entry point
  (`modernization-assessment/graph.json:109`). Nothing is proposed for deletion (`05-dead-code.md`).
- **Risk:** both programs score port difficulty 1 and blast radius 2, `low-low` (`risks.json`).
  The `dependency-cartographer` agent was not needed: there are no open edges.

## Single largest risk

The tree holds no JCL, scheduler definition, shell wrapper or dataset
(`modernization-assessment/graph.json:20-29`). Nothing links these two programs to the nightly batch cycle
the client says must not break. The wave is low risk on the evidence, but the evidence is a fragment. The
job order, the return code contract and any downstream reader of PROGA's output are all unseen. Inference.

## Open Questions for the client's engineers

| # | Question | Evidence |
|---|---|---|
| 1 | What job, scheduler entry or other caller starts PROGA, and what runs before and after it in the nightly cycle? The extractor found no entry point. | `modernization-assessment/graph.json:72` |
| 2 | Is "the nightly batch cycle" just these two programs, or is most of it missing from the tree (JCL, procs, other programs, datasets)? | `modernization-assessment/graph.json:20-29` |
| 3 | Does anything read PROGA's console line `CALL FAILED IF WE GET HERE`, and is it intended? It prints on every run, before the call. | `app/cbl/PROGA.cbl:5` |
| 4 | Does any scheduler condition or downstream job depend on PROGA's return code? `STOP RUN` sets none. | `app/cbl/PROGA.cbl:7` |
| 5 | Does the production load module for PROGB match this four-line `GOBACK` source? The CALL is by literal name, so the link-edit decides. | `app/cbl/PROGB.cbl:4` |
| 6 | What does the runtime do if the CALL fails? There is no `ON EXCEPTION` clause. | `app/cbl/PROGA.cbl:6` |
| 7 | Can you supply 12 months of job logs or SMF records for PROGA, including month-end and fiscal year-end? This is the only route to non-provisional dead-code claims and to a replay oracle. | inference |
| 8 | Do you use a scheduler other than Control-M or shell wrappers (for example CA-7 or TWS)? The extractor reads only those two, so such a scheduler would be invisible. | `modernization-assessment/graph.json:18` |

## Files the extractor did not parse

None. `unparsed` is empty (`modernization-assessment/graph.json:68`).

## Extractor limits that touch this system

| Limit | Why it matters here | Evidence |
|---|---|---|
| Only Control-M XML and shell wrappers that name JCL files are read as schedulers. | No scheduler was found. Another scheduler product would be invisible, so temporal coupling is unknown. | `modernization-assessment/graph.json:18` |
| IF/THEN/ELSE and COND= in JCL are not modeled. Nested PROCs, INCLUDE members and jobs submitted through the internal reader are not followed. | No JCL is in the tree. If the cycle's JCL is added, these limits apply to it. | `modernization-assessment/graph.json:15-16` |
| A called subprogram gets no DDs from its caller's JCL step. | Not triggered today, because neither program uses a dataset. It would matter once JCL arrives. | `modernization-assessment/graph.json:13` |
| EXEC CICS RETURN TRANSID, START and SEND MAP are not edges. | Neither source uses CICS, so this does not touch the system today. Inference from a read of both files. | `app/cbl/PROGA.cbl:3-7` |
| COBOL is read as fixed format. Free format files are listed as not parsed. | Both files parsed, so they are fixed format. | `modernization-assessment/graph.json:10` |

## Artifacts

`01-inventory.md`, `02a-edge-tables.md`, `02-coupling.md`, `03-waves.md`, `04-estimate.md`,
`05a-dead-code-candidates.md`, `05-dead-code.md`, `06-test-strategy.md`, `graph.json`, `waves.json`,
`dead-code.json`, `risks.json`.
