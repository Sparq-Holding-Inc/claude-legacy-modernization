# 06 Test strategy

The bar: for the inputs this system sees, the ported programs give the same outputs as the legacy ones. Any difference is decided on purpose and written in the deviation register.

## The oracle

The tree holds no datasets and no JCL (`analysis`, field `data_hubs` is empty, and `meta.files_seen` in `graph.json` counts 0 JCL files). PROGA and PROGB write nothing. Each moves one constant into a working-storage field and returns (`app/cbl/PROGA.cbl:7`, `app/cbl/PROGB.cbl:7`). Tests generated from this source would prove only that a constant moves. That is the weakest oracle, and here it is vacuous.

So the oracle has to come from outside the tree. In descending order of strength:

| Oracle | Applies to wave 1 | Confidence | Evidence |
|---|---|---|---|
| Parallel run of the nightly batch cycle, old and new, on the same input | Best case. Ask whether the old system can stay up. | low | inference |
| Replay of captured inputs and outputs across a business cycle, including month-end | Next best. The window must include month-end. | low | inference |
| Golden master from archived outputs (GDG generations, reports, extracts sent to partners) | The likely answer. Most shops have years of these. | low | inference |
| Characterization tests from the source | Provisional only, and nearly empty here. | medium | `app/cbl/PROGA.cbl:7` |

## What to ask the client to supply

- The JCL and scheduler definition of the nightly batch cycle. This is the must-not-break item.
- Job output, sysout and return codes for PROGA and PROGB, if they run in it.
- Archived generations of every file that uses the SHARED01 layout.
- Any downstream report or partner extract that shows SH-CUST-ID or SH-BALANCE.
- Job logs or SMF records for the last 12 months. They give the telemetry the dead-code register lacks.

## Normalization spec

Keep this list short. A human signs it.

| Item | Rule | Confidence | Evidence |
|---|---|---|---|
| SH-BALANCE, `S9(9)V99 COMP-3` | Compare in a decimal type with zero tolerance. No IEEE floats. Sign nibble and scale must survive. | high | `app/cpy/SHARED01.cpy:3` |
| SH-CUST-ID, `PIC 9(9)` | Compare as nine digits with leading zeros kept. Decide if a numeric compare or a text compare is the rule. | high | `app/cpy/SHARED01.cpy:2` |
| Timestamps, run ids, page numbers | Mask. None appear in the tree. The client's real outputs will have them. | low | inference |
| Record order, padding, low values | Unknown until a real file is seen. Confirm the order was incidental before ignoring it. | low | inference |

The traps that do not appear in this tree: there is no REDEFINES, no EBCDIC sort and no KSDS key order. They may appear in the missing files. The copybook has no REDEFINES (`app/cpy/SHARED01.cpy:1-3`).

## Job order

The temporal edges in `graph.json` are the list of orders the harness must keep. There are none (`analysis`, field `edge_counts` holds only `include`). The real order of the nightly cycle is unknown. It goes to the client.

## Boundary cases to add

- Boundary dates: month end, quarter end, fiscal year end, leap day. Applies to any real job that uses these programs.
- The empty batch and the largest batch the old system could take.
- Bad data already in the files. The new code must reproduce legacy behavior on it.
- Paths that run only at fiscal close.
- A layout test on SHARED01: every consumer of the record must read the same bytes after the port.

## Deviation register

Empty by design. Nothing differs yet. Every intended difference gets a row before it ships.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|

## Exit bar for wave 1

- Replay diff is clean, modulo the normalization spec and the deviation register.
- Every boundary case passes.
- The harness is under version control and runs in CI.
- The deviation register is signed by someone with the authority to sign it.
- The harness is kept after cutover as the regression suite.
