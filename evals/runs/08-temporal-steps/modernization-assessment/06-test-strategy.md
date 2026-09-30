# 06 Test strategy

Definition of correct: for the inputs SEQJOB really sees, the new job runs the same steps in the same order,
ends each step with the same return code, and produces the same outputs as the old one. Where it does not,
someone decided that on purpose and wrote it in the Deviation Register below.

## The oracle has to come from outside the tree

The tree holds no dataset. There is no DD statement (`app/jcl/SEQJOB.jcl:2` to `app/jcl/SEQJOB.jcl:5`), no
file access in any program (`app/cbl/PGMA.cbl:3`, `app/cbl/PGMB.cbl:3`, `app/cbl/PGMC.cbl:3`), no archived
output, no log and no report. So there is nothing to replay and nothing to diff inside the tree. The oracle
must come from job output, logs and reports. The must-not-break item is the nightly batch cycle, so the
oracle is what that cycle leaves behind.

Oracle for wave 1, strongest first:

| Rank | Oracle | Use for wave 1 | Confidence | Evidence |
|---|---|---|---|---|
| 1 | Parallel run: old and new SEQJOB process the same night's input and the outputs are diffed | Ask first. Teams assume this is impossible and are often wrong. It needs the old job to stay up for at least one full cycle including a month-end. | medium | inference |
| 2 | Captured production input and output, replayed against the new job | Needs a capture window that spans month-end and fiscal year-end. Nothing in the tree gives one. | low | inference |
| 3 | Golden master from archived outputs: prior generations of any dataset SEQJOB writes, SYSOUT archives, printed reports, files sent to partners | Probably exists and is probably unused. Ask for it. | low | inference |
| 4 | Characterization tests from the source | The only oracle the tree supports. It asserts that each program returns at once and that the four steps run in file order. That encodes what the code says, not what the job does. Label all of this coverage provisional. | low | `app/cbl/PGMA.cbl:4`, `app/jcl/SEQJOB.jcl:2`, `app/jcl/SEQJOB.jcl:5` |

Wave 1 uses rank 1 or 3 if the client can supply them. If not, rank 4 alone is not enough to sign off, and
the wave exit bar below is not met.

## What to ask the client to supply

- Job logs and run history for SEQJOB for at least 13 months, with step names, return codes, start and end
  times. This is also the telemetry that turns the dead-code register from provisional to evidence.
- Every dataset, report and partner file the nightly cycle writes, and the archived generations of each.
- The scheduler export or calendar that says when SEQJOB runs, what runs before and after it, and what
  happens after a failure.
- The production copy of the JCL, and the real source of the programs, if these are not it.
- Any restart or rerun runbook. It shows which step names operators use.

## Normalization spec, for a human to sign off

Every line is a claim that a difference does not matter. Each is a place a bug can hide. Keep it short.

| Item | Rule | Why | Confidence | Evidence |
|---|---|---|---|---|
| Job number, run id, timestamps, elapsed time | Ignore | They differ on every run | high | inference |
| Page numbers and sequence numbers in printed output | Ignore | They differ on every run | medium | inference |
| Step return codes | Compare exactly | A changed code changes what runs next | high | inference |
| Step order | Compare exactly: PGMA, PGMB, PGMC, then IEFBR14 | The order is the only behavior the tree defines | high | `app/jcl/SEQJOB.jcl:2`, `app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:4`, `app/jcl/SEQJOB.jcl:5` |
| Step names | Match steps by position, not by name, until the client fixes the name STEP2, which is used twice | A name match would pair the wrong steps | medium | `app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:5` |
| Fixed-width padding and trailing blanks in any output | Decide with the client when outputs are known | The tree shows no output layout | low | inference |
| Packed decimal fields | Compare in a decimal type with zero tolerance on money. Never IEEE floats. | Applies once real programs bring money fields. None appear now. | low | inference |
| Collating sequence | Keep the EBCDIC order for any sort or keyed read. Do not sort in ASCII. | Applies once real programs bring keyed files. None appear now. | low | inference |
| `REDEFINES` branches | Test every branch that reads either layout | Applies once real programs bring record layouts. None appear now. | low | inference |

The job-order rule comes from the temporal edges in `graph.json`. They are the list of orders the harness
must keep: STEP1 before STEP2 (`app/jcl/SEQJOB.jcl:2`, `app/jcl/SEQJOB.jcl:3`), STEP2 before STEP3
(`app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:4`), STEP3 before the second STEP2
(`app/jcl/SEQJOB.jcl:4`, `app/jcl/SEQJOB.jcl:5`).

## Cases to add on purpose

| Case | What to check | Confidence | Evidence |
|---|---|---|---|
| Month-end, quarter-end and fiscal year-end nights | The whole job, and any path that runs only at close | low | inference |
| Leap day and the daylight saving changeover | A nightly run may straddle a 23 or 25 hour day. Check dates and elapsed logic in the outputs. | low | inference |
| A step ending with a non-zero return code | No step has `COND=` or `IF` (`app/jcl/SEQJOB.jcl:2` to `app/jcl/SEQJOB.jcl:5`). Under JCL rules the next step then runs after a non-zero code, and a step abend stops the job. A new orchestrator that stops on any failure would differ. Test it. This is inference from JCL rules. | medium | inference |
| Restart after a failure at each step | Restart at the STEP2 name is ambiguous (`app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:5`). Ask operators what they do today. | low | inference |
| Zero input, and the largest night on record | Needs the outputs to be known first | low | inference |
| Bad data already in the inputs | The new job must reproduce the legacy result, even when that is not sane | low | inference |

## Deviation Register

Nothing may differ without a row here. These rows are proposed and none is approved.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| DR-001 | The step name STEP2 is used for two steps. The second runs after STEP3. | Each step gets a unique name. | A repeated step name breaks restart and name based references. | pending | Restart runbooks and any `COND=` that names STEP2 must change. Unknown. | `app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:5` |
| DR-002 | No `COND=` or `IF`, so a step with a non-zero return code does not stop the job. | To be decided. Either keep this or stop on failure. | The target's orchestrator may stop on failure by default. | pending | Later steps may run or not run after a failure. Unknown. | `app/jcl/SEQJOB.jcl:2`, `app/jcl/SEQJOB.jcl:5`. The default behavior is inference from JCL rules. |

## Exit bar for wave 1

Wave 1 is done when:

- the replay or parallel run diff is clean, except for the normalization spec and the Deviation Register
- every case in the table above passes
- the harness is under version control and runs in CI
- the Deviation Register is signed by someone with the authority to sign it

It is not done when the port compiles, and not when it passes tests written beside the port. Those tests
encode the porter's understanding.

## After cutover

Keep the harness. It becomes the regression suite for the modernized job and is the only executable
specification the job will ever have. Budget for maintaining it.
