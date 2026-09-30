# 06 Test strategy

Target state: refactor. Must not break: "the nightly batch cycle". Telemetry: none.

"Correct" here means: for the inputs the nightly cycle actually sees, the refactored code produces the same outputs as the legacy code, and every difference was decided on purpose and written in the Deviation Register below.

## The oracle has to come from outside the tree

The tree holds no dataset, no JCL and no report (`modernization-assessment/graph.json`, fields `analysis.data_hubs` and `analysis.entry_points`, both empty). The two programs open no file and write nothing. They move a literal into working storage and return (`app/cbl/PROGA.cbl:7-8`, `app/cbl/PROGB.cbl:7-8`). There is no output in the tree to diff.

So the oracle must come from job output, logs and reports the client holds. The item that must not break, "the nightly batch cycle", maps to no unit in the tree, so I did not tie any equivalence anchor to a unit. That mapping is an open question (`modernization-assessment/00-summary.md`, question 2).

## Oracle per wave

There are no waves (`modernization-assessment/03-waves.md`). The oracle below is for the two programs and the cycle they may belong to.

| Rank | Oracle | Use here | Confidence | Evidence |
|---|---|---|---|---|
| 1 | Parallel run of the nightly cycle on production inputs, outputs diffed | Ask first. It is the only oracle that covers the item that must not break. Needs the legacy cycle to stay up | low (availability unknown) | inference |
| 2 | Replay of captured production inputs | The capture window must include month end and, for anything financial, fiscal year end | low (availability unknown) | inference |
| 3 | Golden master from archived outputs | Ask for archived generations of the cycle's reports and extracts. They are free test cases | low (availability unknown) | inference |
| 4 | Characterization tests from the source | Weak. For PROGA and PROGB they would assert only that a working-storage field holds 1 or 2 after the MOVE, which nobody observes. Label any such coverage provisional | high | `app/cbl/PROGA.cbl:7`, `app/cbl/PROGB.cbl:7` |

## What to ask the client to supply

1. Archived generations (GDG) of every report, extract and posting file the nightly cycle produces, with their dates.
2. Job logs and SMF records for the cycle: which programs ran, the return codes, the run time. These are also the telemetry the dead-code register needs.
3. Files sent to partners out of the cycle. What left the building is already an executable specification of the format.
4. The JCL and scheduler export for the cycle, so the harness can keep its step order.
5. A list of every program that COPYs SHARED01, and every dataset written with that layout.

## Normalization spec

Every entry is an assertion that a difference does not matter. Keep the list short and have a human sign it off.

| Item | Rule | Confidence | Evidence |
|---|---|---|---|
| `SH-BALANCE`, packed decimal `S9(9)V99` | Compare as a decimal type with zero tolerance. An IEEE float in the target is a defect, not noise | high | `app/cpy/SHARED01.cpy:3` |
| `SH-CUST-ID`, `9(9)` display numeric | Keep the width of nine and leading zeros. Compare as text or as an integer with the width fixed | high | `app/cpy/SHARED01.cpy:2` |
| Timestamps, run ids, sequence numbers, page numbers | Mask. None appear in the tree, so the list is to be filled from the client's real outputs | low | inference |
| Record padding and low values | Decide which differences matter once a real record exists. No fixed width record is in the tree | low | inference |
| Record order | Confirm whether the legacy order was incidental before ignoring it. A KSDS returns key order and EBCDIC sorts differently from ASCII | low | inference |
| `REDEFINES` | None in the tree, so no branch to cover. Check the client's other copybooks | medium | `app/cpy/SHARED01.cpy:1-3` |
| Job order | The temporal edges in `graph.json` are the orders to keep. There are none, because no scheduler was read. Take the order from the client's scheduler export | high | analysis (field `edge_counts`) |

## Targeted cases

The two programs need no input. The cases below are for the cycle, once the client supplies it.

- Boundary dates: month end, quarter end, fiscal year end, leap day, DST transitions.
- Empty and enormous: a zero record run and a run at the largest volume the legacy cycle handled.
- Bad data already in the files: reproduce the legacy behavior on it, not a sane result.
- Paths that run only at fiscal close. This is the most common source of a failure found six months after cutover.
- Both programs give `SH-CUST-ID` a fixed literal (`app/cbl/PROGA.cbl:7`, `app/cbl/PROGB.cbl:7`). Add a case that shows the port keeps those literals and does not treat them as test values. Confidence: low, since their meaning is unknown.

## Deviation Register

Nothing may differ without a row here. It starts empty, because nothing has been compared yet.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|

## Exit bar per wave

A wave is done when all four hold. There are no waves yet, so these apply to whichever waves the client's JCL produces.

- The replay diff is clean, modulo the normalization spec and the Deviation Register.
- Every targeted boundary case passes.
- The harness is under version control and runs in CI.
- The Deviation Register is signed by someone with the authority to sign it.

Not when the port compiles, and not when it passes tests written alongside the port.

## Keep the harness after cutover

The comparison harness becomes the regression suite for the modernized system. Budget for maintaining it. It is the only executable specification the cycle will have.
