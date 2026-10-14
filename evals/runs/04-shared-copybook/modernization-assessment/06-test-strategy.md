# 06 Test strategy

"Correct" here means: for the inputs the nightly batch cycle actually sees, the refactored programs produce the same outputs as the legacy ones, and any difference is a signed row in the Deviation Register. The tree has no tests, no datasets and no JCL, so the oracle must come from the client.

## Oracle

The tree holds no dataset and no job output (`modernization-assessment/graph.json:129`, `modernization-assessment/graph.json:130`). The oracle has to come from job output, logs and reports. Ask the client for, in this order:

1. **Parallel run** of the nightly batch cycle, old and new on the same input. Ask first whether it is possible.
2. **Captured replay.** Input and output files for the cycle across a window that includes month-end, and fiscal year-end if the data is financial.
3. **Golden master.** Archived generations (GDG) of every file the cycle writes, plus reports and partner extracts.
4. **Characterization tests from source.** Weakest. The source alone shows PROGA sets `SH-CUST-ID` to 1 and PROGB sets it to 2 (`app/cbl/PROGA.cbl:7`, `app/cbl/PROGB.cbl:7`), and nothing else. Any coverage from this is provisional.

Oracle per wave: not assignable. There are no waves (`modernization-assessment/waves.json:2`).

## Mapping the must-not-break item

"The nightly batch cycle" maps to no unit in this tree. There is no JCL job, scheduler job or wrapper (`modernization-assessment/graph.json:154`). I did not invent a mapping. It is an open question in `00-summary.md`.

## Normalization spec (proposed, needs human sign-off)

| Item | Rule | Why | Evidence |
|---|---|---|---|
| `SH-BALANCE` | Compare as decimal, zero tolerance. Target type must be fixed-point, never float. | Packed decimal `S9(9)V99 COMP-3`, money. Float rounding is a real defect. | `app/cpy/SHARED01.cpy:3` |
| `SH-CUST-ID` | Exact match, 9 digits, zero-padded | `PIC 9(9)` unsigned numeric display | `app/cpy/SHARED01.cpy:2` |
| Timestamps, run IDs, page numbers | Mask | Not present in this tree. Add when output is seen. | inference |
| Record order | Keep legacy order until proven incidental | Downstream may depend on it | inference |
| Collating sequence | Test EBCDIC order if any key is sorted | No sort in this tree. Applies once the real cycle is seen. | inference |

## Targeted cases

- `SH-BALANCE`: zero, maximum (999999999.99), minimum (negative), and sign nibble variants of packed data. Confidence in the field's use: low, the programs never touch it (`app/cbl/PROGA.cbl:7`).
- Bad data already in files: unknown. Ask for a sample.
- Boundary dates and fiscal-close paths: no date logic is visible. Ask the client which cycle steps run only at close.
- Zero-record and maximum-size batches: no file I/O in the tree, so no sizing is possible.
- Both programs share one layout (`app/cbl/PROGA.cbl:5`, `app/cbl/PROGB.cbl:5`), so a layout test runs against both.

## Deviation Register

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| none yet | n/a | n/a | n/a | n/a | n/a | inference |

## Exit bar

No wave exists, so no exit bar is set. When waves exist, each is done only when the replay diff is clean modulo this spec and the register, targeted cases pass, the harness is in version control and CI, and the register is signed by someone with authority. The harness stays after cutover as the regression suite.
