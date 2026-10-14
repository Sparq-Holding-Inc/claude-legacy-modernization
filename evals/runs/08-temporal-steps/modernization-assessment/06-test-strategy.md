# 06 Test strategy

The bar is: for the inputs the nightly batch cycle sees, the new job produces the same outputs as the old one, or a person decided otherwise and wrote it down.

## What exists in the tree

No dataset, DD statement or file I/O exists (`app/jcl/SEQJOB.jcl:2`, `app/cbl/PGMA.cbl:3`). The oracle has to come from job output, logs and reports. The client should supply the items in the next section.

## Oracle for wave 1

| Rank | Oracle | Use here | Evidence |
|---|---|---|---|
| 1 | Parallel run of old and new SEQJOB on the same night | Preferred. Ask whether it is possible. | inference |
| 2 | Replayed production inputs | Needs input files. None are in the tree. | inference |
| 3 | Golden master from archived job logs and SYSOUT | Likely the real choice: step order and return codes per night. | inference |
| 4 | Characterization tests from source | Weakest. The programs only `GOBACK`, so they would assert nothing. | `app/cbl/PGMA.cbl:4` |

## What to ask the client to supply

- 12 months of job logs and SMF records for SEQJOB, including month-end and year-end runs.
- Any archived generations of files the job reads or writes.
- The scheduler export. Without it the order against other jobs is unknown.
- The real JCL. `app/jcl/SEQJOB.jcl:5` repeats the step name STEP2.

## Normalization spec

| Item | Rule | Evidence |
|---|---|---|
| Timestamps and run IDs | Mask | inference |
| Step names | Keep exact. A repeated name is the open question above. | `app/jcl/SEQJOB.jcl:5` |
| Step order | Must match exactly | `app/jcl/SEQJOB.jcl:2`, `app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:4` |
| Return codes per step | Must match exactly | inference |

A person must sign off on this list.

## Cases to cover

- Month end, quarter end, year end, leap day, DST change.
- A night with zero input and a night at maximum volume.
- The paths that run only at fiscal close. None are visible in the tree, which is a gap, not a clean bill.
- A step that fails. COND and IF/THEN are not modeled by the extractor, so any restart logic is unseen.

## Deviation register

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| (none yet) | | | | | | inference |

## Exit bar for wave 1

- Replay diff is clean, modulo the normalization spec and the register.
- Boundary cases pass.
- The harness is in version control and runs in CI.
- The register is signed by someone with authority.

Keep the harness after cutover as the regression suite.
