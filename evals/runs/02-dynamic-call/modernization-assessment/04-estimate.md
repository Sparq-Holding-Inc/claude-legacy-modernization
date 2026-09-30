# 04 Estimate

Target state: refactor. There is one wave.

## Method

There is no team velocity, no history and no telemetry to calibrate against, so this is a judgment estimate, not a measurement. It is built from what moves an estimate: coupling edges crossing the wave boundary, whether an oracle exists, god modules, logic in the database, and who can read COBOL. On this tree: one unresolved edge, no oracle supplied, no god modules, no database, and the skills of the client team unknown.

## Wave 1 (PROGB and PROGA)

| Item | Estimate | Confidence | Evidence |
|---|---|---|---|
| Port of PROGB and PROGA, 14 lines | under 1 person-day | high | `app/cbl/PROGA.cbl:9` |
| Harness for the wave: capture input cards and job output, normalization spec, diff runner | 2 to 4 person-days | low | inference |
| Replacement for the computed CALL (dispatch table or loader) and the run-time target set | 1 to 3 person-days, and only for the targets that are in scope | low | `app/cbl/PROGA.cbl:8` |
| Total for this wave | 3 to 8 person-days | low | inference |

The total excludes every program PROGA can call that is not in this tree. Those belong to their own waves and are not estimated here. Any estimate for them would be made up.

## What the range is most sensitive to

1. **Assumes the input card names a small set of programs, ten or fewer, over a full business cycle.** If it names dozens, the dispatch table and its harness dominate and this wave roughly doubles. Evidence: `app/cbl/PROGA.cbl:9`.
2. **Assumes the client can supply input cards and job output for at least one month-end, and fiscal year-end if any target is financial.** If they cannot, the oracle falls to characterization tests written from source, coverage is provisional, and I would add 1 to 2 person-days. Evidence: inference.
3. **Assumes the target platform has an equivalent of a run-time named call.** If it does not, the replacement is a redesign of how the batch cycle chooses its next program, and the low end of this range no longer holds. Evidence: inference.

## Where Claude Code helps and where it does not

| Area | Fit | Evidence |
|---|---|---|
| Transliterating PROGA and PROGB with a harness in place | Strong. It is mechanical. | `app/cbl/PROGB.cbl:4` |
| Building the input capture and diff runner | Strong once the client supplies the inputs | inference |
| Learning which programs the card really names, and why | Weak. It lives in the client's job stream and operating procedures, not in the source. | `app/cbl/PROGA.cbl:8` |
| Deciding what the nightly batch cycle needs from PROGA | Weak. It needs the client's engineers. | inference |
