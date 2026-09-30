# 04 Estimate

There are no waves (`03-waves.md`), so there is no per-wave estimate. Two things can be estimated.
The port of the two source files that are in the tree can be estimated as a range. The nightly batch
cycle around them cannot be estimated, and no number is offered for it.

Every figure below is inference. The tree holds no history of past ports and no measure of team
velocity.

## What is estimated

| Scope | Range | Method | Confidence | Evidence |
|---|---|---|---|---|
| Port PROGA and PROGB, refactor target, source only | 0.5 to 2 engineer-days | Eleven lines of straight-line code with one call and no data access. Most of the time goes to the harness, not the code. | low | inference |
| Build the comparison harness for the two programs (SYSOUT text and return code) | 1 to 3 engineer-days | One captured output and one condition code per run. Range depends on how the client can supply job output. | low | inference |
| The nightly batch cycle | not estimated | No JCL, no scheduler and no dataset exists in the tree. There is nothing to count. | not applicable | `modernization-assessment/waves.json:3` |

## The assumptions the range is most sensitive to

1. **Assumes the deployed PROGB is a no-op like this source.** If a different PROGB is link-edited in
   production, and this stub is a placeholder for it, then PROGB is a program we have not seen and
   the port range is void. Its source is a single `GOBACK` (`app/cbl/PROGB.cbl:4`).
2. **Assumes nothing outside the tree calls PROGA or PROGB.** If other programs call PROGB,
   each caller is a new edge that crosses the boundary, and the count of crossing edges is what moves
   an estimate the most. Nothing in the tree shows a second caller, but the tree may be a fragment.
3. **Assumes the target platform gives the same result for a `CALL` to a subprogram that
   returns at once, and for a default return code.** Neither program sets `RETURN-CODE`. If the
   cycle tests the step's condition code, a port must return the same code. This is inference from
   `app/cbl/PROGA.cbl:1-7`.

## What moves an estimate here

| Driver, in rough order of weight | State in this tree | Evidence |
|---|---|---|
| Coupling edges crossing the wave boundary | One call edge, and it is inside the pair. No other edge is known. | analysis field `edge_counts` |
| A behavioral oracle | None in the tree. No archived outputs, no job logs, no datasets. | analysis field `data_hubs` |
| God modules in the wave | None. | analysis field `god_modules` |
| Business logic in the database | No `EXEC SQL` in either file. | `app/cbl/PROGA.cbl:1-7` |
| Someone who can read the source language | Not known. Ask the client. | inference |

## Where Claude Code can do the port and where it cannot

- **Mechanical.** A transliteration of PROGA and PROGB is well within reach. There is no arithmetic,
  no data layout and no control flow beyond one call.
- **Not inferable from source.** Why PROGB is empty, and what the message text at
  `app/cbl/PROGA.cbl:5` is meant to signal to operators. A port would copy the message verbatim. Whether
  to keep it is a decision for the client, and it belongs in the Deviation Register if it changes.
- **Not possible from this tree.** The nightly batch cycle itself. It needs the JCL and scheduler.
