# 06 Test strategy

The bar for wave 1 is this: for the runs the nightly cycle actually sees, the new implementation
runs the same steps in the same order with the same return codes, and every difference has a row in
the deviation register. Passing tests written alongside the port is not the bar.

**Anchor.** The client said the nightly batch cycle must not break. SEQJOB is the only job in the
tree, so I treat it as that cycle. This is inference and needs the client's confirmation. Evidence:
`app/jcl/SEQJOB.jcl:1`.

## The tree holds no datasets

No DD statement and no file name appears in the job or the programs. Evidence:
`app/jcl/SEQJOB.jcl:2`, `app/cbl/PGMA.cbl:3`. There are no archived generations or extract files to
use as a golden master. The oracle has to come from job output, logs and reports. What to ask the
client for is at the end of this file.

## Oracle for wave 1

| Rank | Oracle | Use it? | Confidence | Evidence |
|---|---|---|---|---|
| 1 | Parallel run. Run legacy SEQJOB and the port on the same nights and diff the step sequence and return codes. The programs write nothing in this tree, so a parallel run looks cheap and safe. Ask whether it is possible before settling for less. | Yes, first choice | low | `app/cbl/PGMB.cbl:4` |
| 2 | Replay from captured job logs. Twelve months of JES job logs and SMF step records for SEQJOB, covering month-end and, if the cycle touches anything financial, fiscal year-end. | Yes, the fallback | low | inference |
| 3 | Golden master from archived outputs. None visible in the tree. | Only if the client supplies reports or extracts the cycle produces | low | inference |
| 4 | Characterization tests from the source. The programs are empty, so this encodes nothing about production. | No. Provisional at best. | high | `app/cbl/PGMA.cbl:4` |

## What the harness asserts

1. **Step order.** PGMA, then PGMB, then PGMC, then the IEFBR14 step. This is the temporal chain in
   `graph.json`, and it is the list of orders the harness must keep. Evidence:
   `app/jcl/SEQJOB.jcl:2`, `app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:4`, `app/jcl/SEQJOB.jcl:5`.
2. **Return codes** for every step, and the job's final condition.
3. **Step identity by position, not by name.** Two steps are named STEP2. A harness that keys on the
   name will merge them or drop one. Evidence: `app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:5`.
4. **Nothing runs that the legacy job did not run,** and nothing is skipped. No IF or COND=
   appears in the job, so a skipped step is a defect. Evidence: `app/jcl/SEQJOB.jcl:2`.

## Normalization spec

Every entry is an assertion that a difference does not matter. Keep it short. A human signs it off.

| Item | Rule | Evidence |
|---|---|---|
| Job number, run timestamps, elapsed time | Ignore. | inference |
| Step names | Compare by position. Do not rely on the name STEP2. | `app/jcl/SEQJOB.jcl:5` |
| Monetary fields | None visible. If the real programs hold any, use a decimal type and zero tolerance. Packed decimal rounds differently from IEEE floats. | inference |
| Record order and collating sequence | None visible. If any sorted output turns up, EBCDIC and ASCII order differ, and downstream readers may depend on it. | inference |
| `REDEFINES`, padding, low values | None visible. Revisit when real record layouts arrive. | `app/cbl/PGMA.cbl:3` |

## Cases to add on purpose

- **Boundary dates.** Run the harness over month-end, quarter-end, fiscal year-end, leap day and a
  DST change. The tree shows no date logic, but the tree is four-line stubs, so this rule guards
  against what the tree does not show. Evidence: `app/cbl/PGMA.cbl:4`.
- **A step that fails.** Force a nonzero return code in PGMB and check what happens to PGMC and the
  last step. No COND= appears in the job, so under JCL defaults a failed step would not by itself stop
  later ones. The client has to say what the cycle is meant to do. Inference. Evidence:
  `app/jcl/SEQJOB.jcl:3`.
- **A restart.** Restart from STEP2 and see which of the two steps is meant. Evidence:
  `app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:5`.
- **The fiscal-close-only path.** Nothing in the tree marks one, but ask. Inference.

## Deviation register

Nothing differs without a row. One row is already proposed. It is not approved.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact |
|---|---|---|---|---|---|
| DEV-001 (proposed) | Two steps share the name STEP2. The second runs IEFBR14, which appears to do nothing (`app/jcl/SEQJOB.jcl:5`). | Not decided. Either give the step a unique name or drop it. | Duplicate step names make restarts and conditions ambiguous. | pending, client engineer | Unknown until the client says what names STEP2. |

## Exit bar for wave 1

- The replay diff is clean, modulo the normalization spec and the deviation register.
- Every boundary and failure case above passes.
- The harness is under version control and runs in CI.
- The deviation register is signed by someone with the authority to sign it.

## What to ask the client to supply

1. Twelve months of job logs and SMF type 30 step records for SEQJOB, with return codes and start times.
2. The scheduler export that starts SEQJOB. The extractor read none.
3. Whether a parallel run is allowed, and for how many nights.
4. Any report, extract or file the nightly cycle produces, with a sample from month-end and year-end.
5. Whether SEQJOB is the nightly batch cycle, or one part of it.
6. What names STEP2: a restart, a condition, a runbook.

## Keep the harness after cutover

The comparison harness becomes the regression suite for the modernized system. Budget to maintain it.
