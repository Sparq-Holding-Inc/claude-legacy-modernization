# 06 Test strategy

This is the behavioral-equivalence plan for wave 1 (PROGA and PROGB, with `cpy:SHARED01`). The bar is not "it compiles" or "it passes tests the porter wrote". The bar is that the new implementation produces the same outputs as the old one on the inputs this system sees, and every intended difference is written down.

## What the tree gives us as an oracle

Nothing. The tree holds no dataset, no report, no job log, no archived generation, no JCL and no scheduler. `graph.json` has no data edges and no temporal edges. The two programs also produce no output of their own. Each does one `MOVE` into working storage and `GOBACK`, and working storage is discarded on return. Evidence: `app/cbl/PROGA.cbl:7-8`, `app/cbl/PROGB.cbl:7-8`.

So a test at the level of one program proves almost nothing. The observable behavior lives at the job level, in the nightly batch cycle that must not break. That cycle is not in the tree. The oracle has to come from job output, logs and reports the client holds.

## What to ask the client to supply

| # | Ask | Why | Evidence |
|---|---|---|---|
| 1 | The JCL and scheduler definition of the nightly batch cycle, and the step that runs PROGA and PROGB | Gives the entry point, the job order and the datasets. Without it the temporal edges to preserve are unknown. | inference |
| 2 | Archived output for at least 12 months: SYSOUT, return codes, reports, extract files and any GDG generations written by that cycle | Golden masters. They must include month-end and, for anything financial, fiscal year-end. | inference |
| 3 | Any file or message that carries `SHARED-AREA` between programs | The layout looks like a record. Whatever carries it is a contract edge the extractor could not see. | `app/cpy/SHARED01.cpy:1-3` |
| 4 | The compiler and its options for these two programs (for example how uninitialized storage and `COMP-3` are handled, and numeric truncation) | These change the bytes the programs leave in the layout. | inference |
| 5 | Job run history for the two program names | Telemetry for the dead-code register, and proof they run at all. | inference |
| 6 | The list of every other program that includes SHARED01 | Decides the true size of the wave and of the harness. | `app/cbl/PROGA.cbl:5` |

## Oracle for wave 1, in order of preference

1. **Parallel run of the nightly cycle.** Run legacy and ported steps on the same production input and diff the outputs. Ask first whether the client can do this.
2. **Replay of captured production input** across a window that includes month-end and, for anything financial, fiscal year-end.
3. **Golden master from archived output** (ask 2 above).
4. **Characterization tests from the source.** This is the only oracle available today. It is the weakest, because it encodes what the code says, not what it does. Label all coverage from it **provisional**.

Characterization cases available from the tree, all provisional: after PROGA runs, `SH-CUST-ID` holds 1 (`app/cbl/PROGA.cbl:7`). After PROGB runs, it holds 2 (`app/cbl/PROGB.cbl:7`). Both return normally (`app/cbl/PROGA.cbl:8`, `app/cbl/PROGB.cbl:8`).

## Trap specific to this system: the uninitialized packed field

`SH-BALANCE` is `PIC S9(9)V99 COMP-3` and has no `VALUE` clause. Neither program sets it. Evidence: `app/cpy/SHARED01.cpy:3`, `app/cbl/PROGA.cbl:7`, `app/cbl/PROGB.cbl:7`. What the legacy program leaves in those six bytes depends on the compiler and its options (inference). If the legacy leaves bytes that are not valid packed decimal, and a downstream step reads them, the port must reproduce the legacy behavior on that data. It may be neither an error nor a sane number. Decide that on purpose and write it in the deviation register. Do not let the target language default it to 0.00 silently.

## Normalization spec (draft, needs human sign-off)

Each line asserts that a difference does not matter. Each is a place a bug can hide. Keep the list short.

| Item | Rule | Note |
|---|---|---|
| Timestamps, run ids, job numbers, page numbers | Mask in job logs and reports | Confirm none is used as a key downstream |
| Monetary and balance fields | Compare in a decimal type, zero tolerance. No IEEE floats. | `SH-BALANCE` is packed decimal with two implied decimals (`app/cpy/SHARED01.cpy:3`) |
| Numeric display fields | Compare values after code page conversion, not raw bytes | `SH-CUST-ID` is `PIC 9(9)` zoned decimal (`app/cpy/SHARED01.cpy:2`). EBCDIC and ASCII digits differ in bytes. |
| Record order | Compare in the legacy order until a consumer is shown not to depend on it | No dataset in the tree, so unconfirmed |
| Padding and low values | Decide per field. Default: treat as a difference. | Applies to any fixed-width file that carries the layout |
| Return codes | Compare exactly | Both programs `GOBACK` with no explicit return code |

## Targeted cases

- **Boundary values of the layout.** `SH-CUST-ID` at 0 and 999999999. `SH-BALANCE` at 0, the largest positive and negative, and both signs of zero. Include invalid packed sign nibbles if the client's data can hold them.
- **The bad data already in production.** Records that violate the layout's own rules. The port must match the legacy result on them.
- **Empty and enormous.** A run with zero input records, and the largest volume the cycle has processed.
- **Boundary dates.** Month-end, quarter-end, fiscal year-end, leap day. Whether these programs run at close is unknown, so treat them as if they might.
- **Job order.** Once the JCL is supplied, every temporal edge in it becomes a check that the ported step still runs in the same position.

## Exit bar for wave 1

- The replay diff is clean, modulo the normalization spec and the deviation register.
- Every targeted case above passes.
- The harness is under version control and runs in CI.
- The deviation register is signed by someone with authority to sign it.

It is not done when the port compiles, and not when it passes tests written alongside the port.

## Deviation register

Nothing may differ from the legacy behavior without a row here.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact |
|---|---|---|---|---|---|
| (none yet) | | | | | |

## Keep the harness

Keep the comparison harness after cutover. It becomes the regression suite for the modernized system, and it is the only executable specification this system will have.
