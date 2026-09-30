# 05 Dead code

Telemetry: none. Every claim below is provisional. `05a-dead-code-candidates.md` holds the extractor's
candidate list. `dead-code.json` holds the classification.

## Result

Unreachable: none. Dormant: none. Unknown: all four programs.

The extractor found no entry point, because the tree holds no CSD, JCL job, scheduler job or wrapper. With no
entry point, nothing can be proven unreachable, and I may not move a program out of unknown. Nothing is
proposed for deletion.

## Unknown

| Unit | Why it is unknown | Read of the source | Confidence | Evidence |
|---|---|---|---|---|
| PROGA | No entry point in the tree. No static caller | Probably a transaction entry. The CSD that would say so is not here | low | `app/cbl/PROGA.cbl:1` |
| PROGB | No entry point in the tree | LINKed unconditionally as PROGA's first statement, so likely live whenever PROGA runs | medium | `app/cbl/PROGA.cbl:12` |
| PROGC | No entry point in the tree | Target of the XCTL at line 20. `WS-NEXT-PGM` is set only at line 19. Likely live whenever PROGA gets that far | medium | inference, `app/cbl/PROGA.cbl:19-20` |
| PROGD | No entry point in the tree | Named only by the XCTL at line 23, after an XCTL that does not return, so that path looks dead. The computed LINK at line 16 could still target it. Instrument. Do not delete | low | inference, `app/cbl/PROGA.cbl:20-23` |

## The computed calls that keep the bucket open

| Computed call | Effect on the buckets | Confidence | Evidence |
|---|---|---|---|
| LINK on `WS-ANY-PGM` from the COMMAREA | Any program in the region could be a target. This alone forbids an unreachable claim on any program | high | `app/cbl/PROGA.cbl:15-16` |
| XCTL on `WS-NEXT-PGM` | Settled by reading: the target is PROGC only. It does not keep the bucket open | high | inference, `app/cbl/PROGA.cbl:19-20` |

I cannot bound the LINK at line 16. There is no table to read. The value is supplied by the caller.

## Dormant

Empty, and empty for a weak reason. The extractor found no last-modified date for any file, because there
is no git history in the tree (`meta.git_dates` is false in `graph.json`). The dormancy rule has nothing to
work on. Dormancy is not shown to be absent. It is not measured.

## What would firm this up

- The CSD, or a list of transaction IDs mapped to programs. That would give the entry points.
- Twelve months of CICS statistics or SMF 110 records showing which of the four programs ran, and which
  names went into the COMMAREA at line 15.
- Commit or file dates for the four sources.
