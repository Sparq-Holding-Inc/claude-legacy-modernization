# 04 Estimate

**Basis: no `--delivery` was given, so both cases are shown, conventional and AI-assisted.** This plugin carries no calibrated productivity data. Every rate below is a planning assumption, not a benchmark. Replace it with measured velocity after the first piece ships.

## Scope that can be estimated

There are no waves (`modernization-assessment/waves.json:3`). What can be sized is the code in the tree: 38 lines of COBOL across four programs (`app/cbl/PROGA.cbl:26`). The estimate covers a refactor of those four programs only. It excludes the nightly batch cycle, which is not in the tree, and every program PROGA can reach through its computed LINK (`app/cbl/PROGA.cbl:16`).

| Term | Conventional | AI-assisted | Does AI shrink it? | Evidence |
|---|---|---|---|---|
| Port of PROGB, PROGC, PROGD | 0.5 to 1 engineer-day total | 0.25 to 0.5 day | Yes. Each is a bare RETURN. Assumes review takes a quarter of the authoring time it replaces. | `app/cbl/PROGB.cbl:4` |
| Port of PROGA | 2 to 4 engineer-days | 1 to 2 days | Partly. The code is trivial. The routing semantics are not. | `app/cbl/PROGA.cbl:12` |
| Resolving the computed LINK | 3 to 10 days, mostly waiting on the client | same | No. It needs the calling transaction, the CSD and someone who knows what goes in the commarea. | `app/cbl/PROGA.cbl:16` |
| Equivalence harness | 3 to 5 days | 2 to 3 days | Partly. Code is quick. Choosing the boundary and capturing commarea values is not. | `app/cbl/PROGA.cbl:9` |
| Oracle, approvals, rehearsal, cutover | 5 to 15 days elapsed | same | No. | inference |

**Range: roughly 2 to 5 engineer-weeks conventional, 1.5 to 4 AI-assisted, of which the largest and least shrinkable part is client availability.** Both figures are inference.

## Assumptions the range is most sensitive to

1. Assumes the commarea is a program name drawn from a short list. If it can name any of dozens of programs, the harness and the scope grow, and the figure could double.
2. Assumes the nightly batch cycle calls none of these four programs. If it does, the batch side is out of scope of this estimate and needs its own assessment.
3. Assumes the second XCTL at line 23 is real, reachable behavior. If it is never reached (`app/cbl/PROGA.cbl:23`), PROGD is dead and one port term disappears.

## Where an AI agent helps and where it does not

Strong: transliterating PROGB to PROGD, and writing a replay harness once the inputs exist. Weak: inferring what the commarea contract means, why PROGA does two XCTLs in a row, and what the "nightly batch cycle" is. Those are undocumented intent, not code.
