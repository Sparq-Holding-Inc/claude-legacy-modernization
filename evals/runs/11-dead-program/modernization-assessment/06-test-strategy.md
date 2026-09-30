# 06 Test strategy

Built with the `behavioral-equivalence` skill. The bar is that for the inputs the nightly batch cycle sees, the ported job produces the same outputs as the legacy job. Where it does not, someone decided that on purpose and wrote it down.

## The oracle problem in this tree

The tree holds no dataset. The step has no DD statement (`app/jcl/MAINJOB.jcl:2`), and the two programs open no file (`app/cbl/PGMMAIN.cbl:4`, `app/cbl/PGMLIVE.cbl:4`). No archived output, no report and no job log came with it. Telemetry is `none`. So the oracle cannot come from data on file. It has to come from job output, job logs, return codes and reports that the client supplies. That is inference.

## Oracle per wave

| Wave | Oracle, strongest first | Provisional? | Confidence | Evidence |
|---|---|---|---|---|
| 1. Nightly batch job | 1. Parallel run: run the legacy and the ported `job:MAINJOB` on the same night and diff return code, job log and outputs. 2. Replay of captured input and output across a window that spans month-end and, for financial content, year-end. 3. Golden master from archived job output and reports. 4. Characterization tests from source, only if 1 to 3 fail | Levels 1 to 3 are not provisional. Level 4 is | low | inference |

Ask whether a parallel run is possible before settling for less. This job writes no dataset as far as the tree shows, so running both copies side by side costs little. Teams assume it cannot be done and are often wrong.

## What to ask the client to supply

- Job logs for `job:MAINJOB` over at least 12 months: return codes, step condition codes, elapsed times. The same records are the telemetry for the dead-code register (`05-dead-code.md`).
- The scheduler export that defines the nightly batch cycle, with predecessors and successors of `job:MAINJOB`. The tree has none (analysis: `warnings`).
- The real DD list of the production job, and any GDG generations it produced.
- Files and reports the cycle sends to partners or archives.
- Any CICS journal or transaction log, if online work feeds or reads the cycle.

## The characterization fallback

If levels 1 to 3 are unavailable, write characterization tests from the source. They encode what the code says, not what it does, so label the coverage provisional.

- Running PGMMAIN calls PGMLIVE exactly once and returns (`app/cbl/PGMMAIN.cbl:4`).
- Running PGMLIVE returns to its caller without any effect (`app/cbl/PGMLIVE.cbl:4`).
- Running `job:MAINJOB` executes step S1 once and ends with the same condition code as the legacy job (`app/jcl/MAINJOB.jcl:2`).

These tests are trivial because the code is trivial. They do not prove the nightly cycle is right.

## Normalization spec

Every entry is a claim that a difference does not matter. Keep the list short. A human signs it.

| Field | Rule | Confidence | Evidence |
|---|---|---|---|
| JES job number, run id, submit and end timestamps in the job log | Mask | medium | inference |
| Page numbers and run dates printed on reports | Mask | medium | inference |
| Condition code of each step | Compare exactly | high | `app/jcl/MAINJOB.jcl:2` |
| Any monetary field the real job writes | Compare in a decimal type at zero tolerance. Never IEEE floats | medium | inference |
| Record order in any output file | Do not assume it is incidental. Confirm with downstream readers first | medium | inference |
| Fixed-width padding, spaces against low values | Decide and record. Not decided yet | low | inference |

The tree holds no packed decimal, no `REDEFINES` and no KSDS, so none of the mainframe traps apply to what is here. They all apply to the real cycle if it holds them. EBCDIC against ASCII collating order matters for any sorted or keyed output.

## Cover the input space deliberately

- **Boundary dates.** Run the cycle across month-end, quarter-end, fiscal year-end, a leap day and a DST change.
- **The empty and the enormous.** A night with no input, and a night at the maximum volume the legacy job ever handled.
- **Bad data already in there.** Legacy data breaks its own rules. The port must reproduce what the legacy job does with it.
- **Fiscal-close paths.** The single most common source of a failure found six months after cutover. This tree shows no date logic (`app/cbl/PGMMAIN.cbl:4`), so any such path lives in code the tree does not contain. Ask for it.

## Job order

The temporal edges in `graph.json` are the list of orders the harness must keep. There are none, and no scheduler was parsed (analysis: `edge_counts`, `warnings`). The order in which the nightly cycle runs `job:MAINJOB` against its neighbours is unknown. It is a gap the harness cannot close alone.

## Deviation register

Nothing may differ without a row here. It opens empty.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| none yet | Not applicable | Not applicable | Not applicable | Not applicable | Not applicable | inference |

## Exit bar for wave 1

Wave 1 is done when all of these hold:

- the diff of job output against the legacy job is clean, modulo the normalization spec and the deviation register
- every boundary case above passes, including a run across a month-end
- the harness is under version control and runs in CI
- the deviation register is signed by someone with the authority to sign it

It is not done when the port compiles, or when it passes tests written beside the port. Those encode the porter's understanding, which is the thing under test.

## Keep the harness after cutover

The comparison harness becomes the regression suite for the modernized system. Budget for maintaining it. It is the only executable specification the nightly cycle will have.
