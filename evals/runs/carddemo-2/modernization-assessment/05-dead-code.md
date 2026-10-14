# 05 Dead code

Telemetry is `none`. Every claim here is provisional. The extractor's three buckets are kept as they are, and nothing was moved toward unreachable. The candidate list is in `05a-dead-code-candidates.md`.

Dormancy was computed with git dates, as of 2026-10-14 and a 5-year rule. The dormant list is empty. That is a measurement and not a finding of liveness: the programs carry git dates between 2022-09-01 and 2025-10-16 (`modernization-assessment/01-inventory.md:20`), and git dates in a demo repository say when it was uploaded, not when a program last changed in production (inference).

## Unreachable

| Unit | Reason | Confidence | Evidence |
|---|---|---|---|
| cpy:UNUSED1Y | No program includes it, and no computed call can reach a copybook. | medium | `app/cpy/UNUSED1Y.cpy:1` |

Propose for deletion only after the client confirms that no build step outside the tree copies it.

## Reachable but dormant

None.

## Unknown

| Unit | Reason | Confidence | Evidence |
|---|---|---|---|
| CBTRN01C | No JCL step runs it. 28 computed calls in reachable programs could name it. Its DDs are mapped by no JCL in the tree. It reads the daily transaction file, the cross-reference, account, card and customer masters, and the transaction file, like a pre-posting check. | low | `app/cbl/CBTRN01C.cbl:1`, `app/cbl/CBTRN01C.cbl:254`, `app/cbl/COACTUPC.cbl:956` |
| proc:TRANREPT | Named only inside a COBOL literal in CORPT00C, which submits it at run time. It is the online path of the transaction report. | low | `app/proc/TRANREPT.prc:1`, `app/cbl/CORPT00C.cbl:94` |

The 28 computed calls are listed in `05a-dead-code-candidates.md:61`. I did not bound them. Most are in menu and screen programs, and the likely pattern is a transfer to a program name held in a field (inference). The first step is to read the call sites and the program-name tables behind them.

## What this register does not cover

- 35 JCL jobs are named by no parsed scheduler (`modernization-assessment/02a-edge-tables.md:286`). The CA-7 listing `app/scheduler/CardDemo.ca7` is not parsed, so some of them may be scheduled there. Every job counts as an entry point, so none of them appears in a bucket above. Ask the client which still run.
- Several of those jobs are build and compile jobs (CICCMP, CBLDBMS, IMSMQCMP) that have no successor in a refactor. That is a scope decision, not a dead-code finding.
- REPRTEST and SORTTEST look like test jobs by name. I did not move anything because of a name, and the extractor lists both as entry points. TRANREPT, a must-not-break job, is unscheduled in the tree too, but a live online screen submits its procedure (`app/cbl/CORPT00C.cbl:94`), so the absence of a scheduler entry is no sign that it is dead.
