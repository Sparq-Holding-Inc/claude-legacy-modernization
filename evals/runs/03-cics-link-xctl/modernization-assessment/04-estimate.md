# 04 Estimate

Method: judgment from the coupling in `graph.json`, not from lines of code, and not from measured
port velocity. There is no velocity data yet. The ranges below are for effort by one engineer who can read
COBOL and CICS. They are not a delivery date.

## What drives the number

| Driver | Value in this tree | Evidence |
|---|---|---|
| Coupling edges crossing the wave boundary | 0 data, 0 contract, 0 temporal, 1 unbounded computed call | `app/cbl/PROGA.cbl:16` |
| Behavioral oracle | None on file. Needs captured COMMAREA traffic or CICS logs from the client | inference |
| God modules | None | inference |
| Business logic in the database | None visible. No SQL in any program | `app/cbl/PROGA.cbl:1-26` |
| LOC | 26 for PROGA and 4 each for the other three | `app/cbl/PROGA.cbl:1-26` |
| Nightly batch cycle | Not in the tree, so not estimated | inference |

## Wave 1: CICS routing chain

| Scenario | Range | Assumptions | Confidence | Evidence |
|---|---|---|---|---|
| Low | 3 to 5 person days | The four files are the real production source. The COMMAREA names are a short known list. Captured traffic exists | low | inference |
| Expected | 5 to 10 person days | As low, but the list has to be recovered from the callers and a harness built | low | inference |
| High | 15 to 25 person days | The computed LINK is open ended, so the facade must be a general dispatcher, and there is no oracle beyond characterization tests | low | inference |

The transliteration is a small part of that. Most of the range is recovering the dispatch contract and
building the harness.

## The assumptions the range is most sensitive to

1. **The computed LINK reaches a short, known list of programs.** If the callers send fewer than about ten
   distinct names and the client can list them, the facade is a lookup table and the expected range holds.
   If the name is free text from outside, the facade is a general dispatcher, and the wave moves toward
   the high range or roughly doubles, because every reachable program then joins the test surface
   (`app/cbl/PROGA.cbl:15-16`).
2. **PROGB, PROGC and PROGD are the real source and not stubs.** Each is a bare RETURN
   (`app/cbl/PROGB.cbl:4`, `app/cbl/PROGC.cbl:4`, `app/cbl/PROGD.cbl:4`). If production versions hold logic,
   the tree is not the system, and this estimate does not apply.
3. **A captured COMMAREA sample can be had from CICS journals or SMF records.** If not, the harness falls
   back to characterization tests written from this source. That adds roughly two to three days, and the
   coverage is provisional (see `06-test-strategy.md`).

## Where Claude Code helps and where it does not

| Task | Claude Code | Confidence | Evidence |
|---|---|---|---|
| Transliterating PROGB, PROGC and PROGD | Strong. Trivial with a harness | high | `app/cbl/PROGB.cbl:4` |
| Transliterating PROGA's control flow | Strong, if the XCTL "does not return" rule is written into the harness first | medium | `app/cbl/PROGA.cbl:12-26` |
| Inferring which programs the computed LINK is meant to reach | Weak. That is intent held by the callers, not by this source | high | `app/cbl/PROGA.cbl:15-16` |
| Knowing whether the code after the first XCTL is dead or is a fall back the client relies on | Weak. Needs the client | medium | `app/cbl/PROGA.cbl:20-26` |
| Building the replay harness and the normalization spec | Strong, once traffic is supplied | medium | inference |

## Not in this estimate

The nightly batch cycle. No JCL, batch program, scheduler or dataset came with the tree. It cannot be sized,
and the ranges above must not be read as covering it.
