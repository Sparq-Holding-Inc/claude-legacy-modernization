# 06 Test strategy

The bar: for the inputs this system sees, the new job produces the same outputs as the old one. Where
it does not, someone decided that on purpose and wrote it down in the Deviation Register below.

## What the oracle can be here

The tree holds no datasets. No program opens a file (`app/cbl/PGMA.cbl:4`, `app/cbl/PGMB.cbl:4`,
`app/cbl/PGMC.cbl:4`) and the job has no DD statement (`app/jcl/SEQJOB.jcl:1`). So the oracle has to come from
job output, logs and reports, not from data files. I would ask the client to supply:

- archived job logs and return codes for SEQJOB over at least 13 months, so month-end and year-end are in it
- SMF records or scheduler history that show which steps ran and in what order
- any report, extract or SYSOUT the real programs produce, if their real bodies live elsewhere
- confirmation that the old system can stay up for a parallel run

| Wave | Oracle | Strength | Confidence | Evidence |
|---|---|---|---|---|
| 1 | Parallel run of SEQJOB on both platforms, comparing step order, return codes and SYSOUT. If a parallel run is not possible, replay against archived job logs. | Strongest available, once the client confirms it. Characterization tests from source are provisional. | low | inference |

Characterization tests generated from the source would encode three GOBACK statements. They prove
nothing, so I would not rely on them.

## Normalization spec (for a human to sign)

| Item | Rule | Why it may hide a bug | Evidence |
|---|---|---|---|
| Job number, timestamps, CPU and elapsed time | Ignore | A step that stops running would show as a missing time, so compare the step list too. | inference |
| Step order | Do not normalize. Compare exactly. | The order is the whole contract (`app/jcl/SEQJOB.jcl:2`, `app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:4`). | `app/jcl/SEQJOB.jcl:2` |
| Return codes | Compare exactly per step | A wrong code changes the downstream COND logic. | inference |
| Trailing spaces and padding in SYSOUT | Ignore, with sign-off | Fixed-width padding can carry meaning. | inference |

Mainframe traps that do not apply to this tree today: packed decimal, EBCDIC collating sequence,
REDEFINES and low values (there is no arithmetic, sort or record layout in it). If the real program
bodies turn up, put each into this spec before any diff.

## Order the harness must keep

These are the temporal edges from `modernization-assessment/graph.json`.

| Before | After | Evidence |
|---|---|---|
| step:SEQJOB.STEP1 (PGMA) | step:SEQJOB.STEP2 (PGMB) | `app/jcl/SEQJOB.jcl:2`, `app/jcl/SEQJOB.jcl:3` |
| step:SEQJOB.STEP2 (PGMB) | step:SEQJOB.STEP3 (PGMC) | `app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:4` |
| step:SEQJOB.STEP3 (PGMC) | step:SEQJOB.STEP2#2 (IEFBR14) | `app/jcl/SEQJOB.jcl:4`, `app/jcl/SEQJOB.jcl:5` |

## Cases to add on purpose

| Case | Reason | Evidence |
|---|---|---|
| Run at month end, quarter end and fiscal year end | The job may be date driven in code we have not seen | inference |
| A run where PGMB returns a nonzero code | Shows whether the last step still runs and whether STEP2 refers to line 3 or line 5 | `app/jcl/SEQJOB.jcl:5` |
| A restart from STEP2 | The duplicate step name makes this ambiguous | `app/jcl/SEQJOB.jcl:3` |
| A zero-work night | The empty case | inference |

## Deviation Register

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| D-1 | Job repeats step name STEP2 on two steps | Pending. Decide whether to rename or drop the IEFBR14 step. | Not approved. A repeated step name is a JCL error on z/OS (inference). | pending | Unknown until the scheduler export is seen | `app/jcl/SEQJOB.jcl:5` |

## Exit bar for wave 1

- the diff of step order, return codes and SYSOUT is clean, modulo the normalization spec and the register
- every case above passes
- the harness is under version control and runs in CI
- the register is signed by someone with the authority to sign it

Keep the harness after cutover. It is the only executable specification this job has.
