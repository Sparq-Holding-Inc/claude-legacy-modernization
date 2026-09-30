# 06 Test strategy

This follows the `behavioral-equivalence` skill. The bar is not that the port compiles or passes tests
written next to it. The bar is that, for the inputs this system actually sees, the port produces the same
outputs as the legacy programs, and any difference is recorded on purpose.

Anchor from the scoping answers: **the nightly batch cycle must not break** (`--must-not-break`).
Telemetry: none.

## The tree holds no datasets

There are no datasets, no VSAM files and no DB2 tables in the graph (`modernization-assessment/graph.json:99`),
and neither program opens a file (`app/cbl/PROGA.cbl:3-7`, `app/cbl/PROGB.cbl:3-4`). There are no JCL
jobs to read job order from (`modernization-assessment/graph.json:26`). So the oracle cannot come from
data files. It has to come from job output, logs and reports. The only observable outputs the source
shows are the console text at `app/cbl/PROGA.cbl:5` and the process return code at `app/cbl/PROGA.cbl:7`.

## Oracle for wave 1

| Rank | Oracle | Available? | Evidence |
|---|---|---|---|
| 1 | Parallel run: run legacy and port on the same night, diff the outputs | Ask. Unknown. Cheap here because the programs do no I/O. | inference |
| 2 | Captured production replay | Ask for job logs covering month-end and fiscal year-end. | inference |
| 3 | Golden master from archived outputs | Ask for archived SYSOUT and job logs of the nightly cycle. | inference |
| 4 | Characterization tests from source | Available now. Provisional only, because it encodes what the code says, not what it does. | `app/cbl/PROGA.cbl:5-7` |

Chosen oracle: rank 4 for the first pass, because nothing else is in the tree, then upgrade to rank 1 or
2 as soon as the client supplies job logs or a parallel run slot. Label all coverage from rank 4 provisional.

## What to ask the client to supply

- The JCL job, proc or scheduler entry that runs PROGA, and the jobs before and after it in the nightly
  cycle.
- SYSOUT and return codes for PROGA for at least 12 months, including month-end and fiscal year-end.
- The link-edit or load library listing that shows which module PROGB resolves to in production.
- Anything downstream that reads PROGA's console output or its condition code.

## Normalization spec (for a human to sign off)

| Item | Proposal | Why it might hide a bug | Evidence |
|---|---|---|---|
| Timestamps, job numbers, page numbers in SYSOUT | Mask | Low risk here: neither program writes any. | inference |
| The text `CALL FAILED IF WE GET HERE` | Do not mask. Compare it exactly. | It prints on every run, before the call, whether or not the call fails. Removing it is a behavior change. | `app/cbl/PROGA.cbl:5` |
| Return code | Compare exactly. | `STOP RUN` sets no code, so the value comes from the runtime. A port to another runtime may return a different default. | `app/cbl/PROGA.cbl:7` |
| Trailing whitespace and padding in the console line | Compare bytes, then decide with a human. | Fixed width padding can differ between runtimes. | inference |
| Packed decimal and collating sequence | Not applicable now. | Neither program has numeric fields or sorts. If the nightly cycle adds programs that do, put both in the spec. | `app/cbl/PROGB.cbl:3` |

## Cases to cover deliberately

- **The normal run.** PROGA prints, calls PROGB, PROGB returns, PROGA ends. Assert the console text and the
  return code (`app/cbl/PROGA.cbl:5-7`).
- **The call fails.** The CALL has no `ON EXCEPTION` and no `USING` (`app/cbl/PROGA.cbl:6`). What the runtime
  does when PROGB is missing decides whether the job abends or continues. Test that in the target
  runtime and record the difference in the Deviation Register.
- **The message ordering.** The message prints before the call. If the port buffers output differently, the
  order of the message and any output from PROGB can change. PROGB prints nothing in this source
  (`app/cbl/PROGB.cbl:4`).
- **Boundary dates.** Month-end, quarter-end and fiscal year-end runs. Neither program reads a date. Inference:
  the programs behave the same on those dates, but the schedule may not, so test the schedule.
- **Job order.** No temporal edges are in the graph, because no scheduler was found
  (`modernization-assessment/graph.json:100`). The harness must keep whatever order the client's
  scheduler enforces once we are given it.
- **Zero-record and maximum-size inputs.** Not applicable. The programs take no input.

## Deviation Register

One proposed entry so far. Every intentional difference gets a row before it ships.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact |
|---|---|---|---|---|---|
| D-001 | Console message `CALL FAILED IF WE GET HERE` prints on every run (`app/cbl/PROGA.cbl:5`) | Proposed only: decide with the client whether to keep it | Message text says failure, but it prints before the call and on success | Pending | Unknown: anything that scrapes the console output |

## Exit bar for wave 1

Wave 1 is done when:

- the replay or parallel run diff is clean, modulo the normalization spec and the Deviation Register
- the cases above pass, including the failed-CALL case
- the harness is under version control and runs in CI
- the Deviation Register is signed by someone with authority to sign it

Keep the harness after cutover. It is the only executable specification this system will have.
