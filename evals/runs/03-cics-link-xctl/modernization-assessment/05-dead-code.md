# 05 Dead code

Telemetry: `none`. Every claim here is provisional. Nothing was measured at run time.

Two gaps decide the result:

- **No entry point exists in the tree.** There is no CSD transaction, JCL job or scheduler job. Nothing can be proven unreachable, so every candidate is unknown (analysis: `dead_code_candidates`, `dead_code_reasons`, and the warning in `05a-dead-code-candidates.md`).
- **The dormant bucket was not computed.** The tree is not a git repository, so no last-modified date exists (analysis: `warnings`). An empty dormant list here means not measured. It does not mean nothing is dormant.

`05a-dead-code-candidates.md` holds the extractor's list. The machine-readable result is `modernization-assessment/dead-code.json`.

## Unreachable

None. I may not move a program from unknown to unreachable, and the extractor put all four in unknown. The computed LINK at `app/cbl/PROGA.cbl:16` would block the move even if an entry point existed.

## Dormant

None computed. Not measured.

## Unknown

| Unit | Confidence | Reason | Evidence |
|---|---|---|---|
| PROGA | low | No entry point in the tree. Nothing in the tree calls it, but a CSD transaction may start it. Keep it and find out. | `app/cbl/PROGA.cbl:1` |
| PROGB | low | Statically linked from PROGA, whose own reachability is unknown. | `app/cbl/PROGA.cbl:12` |
| PROGC | low | The XCTL target of PROGA after a literal move. It is the program PROGA hands over to on its normal path, so it is the one most likely to run. The computed LINK could also name it. | `app/cbl/PROGA.cbl:19`, `app/cbl/PROGA.cbl:20` |
| PROGD | low | Its only static edge, an XCTL, follows an unconditional XCTL to PROGC, so it looks unreachable by control flow (inference). The computed LINK at line 16 could still name it. Instrument it before anyone proposes deletion. | `app/cbl/PROGA.cbl:16`, `app/cbl/PROGA.cbl:23` |

## Bounding the computed calls

- The LINK at `app/cbl/PROGA.cbl:16` takes its target from the COMMAREA (`app/cbl/PROGA.cbl:15`). I could not bound it. It keeps all of PROGB, PROGC and PROGD in unknown.
- The XCTL at `app/cbl/PROGA.cbl:20` is bounded to PROGC by the literal MOVE at line 19 (inference from reading PROGA). That does not change any bucket. It cannot move a program out of unknown, and no program is in the bucket because of that call alone.

## Instrumentation to propose

Count program-level invocations of PROGB, PROGC and PROGD for twelve months, and log the COMMAREA program name that PROGA moves at `app/cbl/PROGA.cbl:15`. That turns this list from provisional to measured, and it answers whether PROGD is ever reached by way of the computed LINK.
