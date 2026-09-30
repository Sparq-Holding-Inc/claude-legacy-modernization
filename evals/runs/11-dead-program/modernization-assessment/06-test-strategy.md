# 06 Test strategy

This follows the `behavioral-equivalence` skill. The bar is not "it passes the tests". The bar is that for
the inputs the system actually sees, the ported job gives the same outputs as the legacy one. Where it does
not, someone decided that on purpose and wrote it down.

## What the tree gives us to compare

Nothing but a return code. The tree holds no dataset, no VSAM file and no DB2 table. `job:MAINJOB` has one
step and no DD statement, so it writes no file and no report (`app/jcl/MAINJOB.jcl:2`). `PGMMAIN` calls
`PGMLIVE`, and `PGMLIVE` does `GOBACK` (`app/cbl/PGMMAIN.cbl:4`, `app/cbl/PGMLIVE.cbl:4`).

So the oracle has to come from job output, logs and reports, not from data files. Whatever the nightly
batch cycle does that matters to the business, it does outside this tree.

## Anchor: what must not break

| Must-not-break item | Unit in the tree | Status | Confidence | Evidence |
|---|---|---|---|---|
| "the nightly batch cycle" | `job:MAINJOB` is the only candidate | Not confirmed. The tree has no scheduler and nothing marks the job as nightly or as a cycle. I did not invent the mapping. | low | `app/jcl/MAINJOB.jcl:1` |

## Oracle per wave

| Wave | Oracle, strongest first | Provisional? | Confidence | Evidence |
|---|---|---|---|---|
| 1 | 1. Parallel run of `job:MAINJOB` on the legacy platform and the ported job, compared on return code, step outcome, log messages and position in the cycle. 2. Replay from archived job logs of at least 12 months, which are golden masters with a date on them. 3. A characterization test written from the source, only if 1 and 2 are unavailable. | Yes, if only option 3 exists. That test proves a call returns and nothing more. | low | `app/jcl/MAINJOB.jcl:2` |

Ask whether a parallel run is possible before settling for less. Teams assume it is not and are often
wrong. If the legacy platform stays up during the port, it is possible for a job this small.

## What to ask the client to supply

1. Twelve to twenty-four months of job logs or SMF records for `job:MAINJOB`: return codes, run dates, elapsed
   time. These are also the telemetry the dead-code register needs (`modernization-assessment/05-dead-code.md`).
2. The scheduler definition for the nightly cycle: predecessors, successors, `COND` checks and return
   code rules. The tree has none (analysis: `warnings` names the missing scheduler).
3. Any report, extract or message the cycle sends to another system, and archived copies of it.
4. The compile and link options and the load library. They decide whether `PGMLIVE` is bound statically
   or loaded at run time (inference).
5. Confirmation that the source in the tree is the source behind the production load modules.

## Normalization spec

Every line here asserts that a difference does not matter. Each is a place a real defect can hide. A human
signs off on the list.

| Item | Rule | Why it is safe | Confidence | Evidence |
|---|---|---|---|---|
| Timestamps, JES job numbers, run IDs | Mask before diffing | They differ on every run | high | inference |
| CPU time and elapsed time | Record and trend. Do not diff. | A different platform changes them | high | inference |
| Message ordering in the job log | Compare as a sequence, not as a set | The order may be an implicit contract for a successor | medium | inference |
| Return code | Exact match, no tolerance | It is the only output the tree shows, and a successor may test it | high | `app/jcl/MAINJOB.jcl:2` |

None of the numeric traps apply to what is in the tree. It has no `COMP-3` field, no `REDEFINES`, no
collating sequence and no fixed-width record. The tree has one copybook and nothing includes it
(`app/cpy/UNUSED.cpy:1`). These traps go in the spec when the client's fuller tree arrives:
packed decimal compared in a decimal type with zero tolerance on money, EBCDIC against ASCII sort order,
record padding, and job order taken from the temporal edges.

## Input space

The job takes no input in the tree. The variation is in when it runs. Run the parallel window over:

- month end, quarter end and fiscal year end, because a scheduler may vary what it runs on those dates
  and the tree cannot show that
- a run after a failed prior night, and a run with nothing to do
- any path that only runs at fiscal close (inference: none is visible, and the tree is silent about it)

## Deviation register

Nothing may differ without a row here. It starts empty because none is proposed. If the client wants
`PGMDEAD` and `cpy:UNUSED` deleted, that removal gets a row.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|

## Exit bar for wave 1

Wave 1 is done when all four hold. It is not done when the port compiles.

- The replay diff is clean, modulo the normalization spec and the deviation register.
- Every boundary case above passes.
- The harness is under version control and runs in CI.
- The deviation register is signed by someone with the authority to sign it.

## After cutover

Keep the harness. It becomes the regression suite for the modernized job. It is the only executable
specification this job has had.
