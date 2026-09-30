# 04 Estimate

Method: there are 11 lines of COBOL in two programs (`modernization-assessment/graph.json:37-46`).
Lines of code are not what moves this estimate. Per the plugin's method, the estimate follows the coupling
edges that cross the wave boundary, the availability of a behavioral oracle, god modules, logic held in the
database, and who can read COBOL. Here: one internal call edge, no edges crossing the boundary that we can
see, no oracle in the tree, no god module, no database, and unknown staffing. Every figure is inference.

## Wave 1: PROGA and PROGB

| Piece of work | Range | Basis | Evidence |
|---|---|---|---|
| Mechanical port of both programs | 0.5 to 1 person-day | One DISPLAY, one CALL, one STOP RUN, one GOBACK. No files, no arithmetic. | `app/cbl/PROGA.cbl:5-7`, `app/cbl/PROGB.cbl:4` |
| Harness: capture SYSOUT and return code, run legacy and port, diff | 2 to 4 person-days | Small, but the oracle has to be built from job output. No archived output is in the tree. | inference |
| Wiring to the scheduler, JCL or replacement launcher, and rollback switch | 2 to 5 person-days | The starter is not in the tree, so this piece is the least certain. | `modernization-assessment/graph.json:109` |
| Total for wave 1 | 5 to 10 person-days | Sum of the rows above. The wide range is entirely the missing JCL and scheduler. | inference |

Confidence in the total is low.

## The assumptions the range is most sensitive to

1. **Assumes the tree is the whole nightly batch cycle.** If the cycle also has JCL, other programs or
   datasets that were not supplied, this figure covers only a fragment and is a floor, not an estimate
   of the cycle. Each additional program with file I/O adds a harness and a normalization spec.
2. **Assumes PROGB in production is the four-line `GOBACK` in the tree** (`app/cbl/PROGB.cbl:4`). If
   the production load module is larger, the port cost scales with what it does and the harness cost
   roughly doubles.
3. **Assumes nothing downstream reads the `CALL FAILED IF WE GET HERE` line or the return code**
   (`app/cbl/PROGA.cbl:5`). If a scheduler condition or a log scraper depends on either, the harness must
   pin them, and the wiring row moves to the top of its range.

## Where Claude Code helps and where it does not

- **Mechanical port.** Claude Code is strong here. Two trivial programs with no arithmetic are an easy
  transliteration, provided the harness exists first.
- **Intent.** Claude Code is weak at inferring why PROGA prints a failure message before the call
  (`app/cbl/PROGA.cbl:5`). Whether that is a leftover test string or a signal someone relies on must
  come from the client's engineers.
- **Environment.** The launcher, the scheduler and the runtime return code conventions are not in the
  tree. Claude Code cannot infer them.
- **Staffing.** Whether the team has anyone who can read COBOL is unknown. With programs this small, it
  matters little for the port and a lot for the wiring.
