# 06 Test strategy

The tree holds no datasets, JCL or reports, so no oracle can be named from it. The must-not-break item, "the nightly batch cycle", maps to no unit here (`modernization-assessment/graph.json:86`). It is not mapped by guesswork.

## Oracle, ranked

| Rank | Oracle | Status | Evidence |
|---|---|---|---|
| 1 | Parallel run of the nightly cycle | Ask the client. Preferred. | inference |
| 2 | Replay of captured inputs. The window must include month-end and fiscal year-end. | Ask the client. | inference |
| 3 | Golden master from archived output (GDG generations, reports, partner extracts, job logs, SMF) | Likely available. Ask. | inference |
| 4 | Characterization tests from source | Fallback only, provisional. | `app/cbl/PROGA.cbl:8` |

The oracle has to come from job output, logs and reports. Ask the client for: the JCL and scheduler for the nightly cycle, 12 months of job logs and return codes, archived output generations, and the input to each PROGA run.

## PROGA specifically

PROGA's behavior depends on a name read by `ACCEPT` (`app/cbl/PROGA.cbl:8`) and then called (`app/cbl/PROGA.cbl:9`). The harness must capture that input for each run. Cases:

- every callee name seen in production
- a name that matches no program (the legacy abend behavior must be reproduced or recorded in the register)
- a blank or short name, since `WS-PGM-NAME` is `PIC X(8)` (`app/cbl/PROGA.cbl:5`)

PROGB only returns (`app/cbl/PROGB.cbl:4`), so its equivalence check is a return code and no output.

## Normalization spec (draft, needs human sign-off)

Timestamps and run IDs, page numbers, trailing padding. Money in a decimal type with zero tolerance, and EBCDIC collation kept wherever order is observable. None is proven needed here, since the tree has no data. inference.

## Deviation register

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| none yet | n/a | n/a | n/a | n/a | n/a | inference |

## Exit bar

Replay diff is clean modulo the spec and register. Boundary cases pass, including the fiscal-close path, which no tree evidence covers. The harness is in CI and the register is signed. Keep the harness after cutover.
