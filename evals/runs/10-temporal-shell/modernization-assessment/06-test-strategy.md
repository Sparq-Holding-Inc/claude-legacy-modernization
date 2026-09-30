# 06 Test strategy

Follows the `behavioral-equivalence` skill. What must not break: the nightly batch cycle. In this tree that is the wrapper `scripts/nightly.sh` and the two jobs it submits, JOBA and JOBB.

"Correct" here means: for every night the old chain ran, the new chain submits the same jobs in the same order, stops in the same situations, and each job ends with the same return code and the same output, except where someone decided otherwise and wrote it in the Deviation Register.

## The oracle problem

The tree holds no datasets and no data edges. Every step runs the IEFBR14 no-op utility (`jcl/JOBA.jcl:2`, `jcl/JOBB.jcl:2`) with no DD statements. So there are no output files in the tree to compare, and no archived generations to use as golden masters. The oracle has to come from what the running system leaves behind: job output, logs and reports. Characterization tests from source would only assert that a no-op ends with return code 0. That is provisional and proves almost nothing.

Chosen oracle for wave 1, strongest first:

1. **Parallel run.** Run the refactored chain beside the legacy chain on the same nightly trigger and diff job order, return codes and output. Ask for this first. The chain is small and the jobs appear to write nothing, so running both is probably cheap. Teams assume it is impossible and are often wrong.
2. **Replay from captured job history.** If parallel run is refused, replay against the archived job log record of the last 12 months, including a month-end, a quarter-end and a fiscal year-end.
3. **Characterization from the source** only for the failure behavior of the wrapper (below), labeled provisional.

## What to ask the client to supply

- JES job logs or SMF job records for JOBA and JOBB for at least 12 months: start and end times, return codes per step, and which nights the chain aborted.
- Whatever archived SYSOUT, reports or extracts JOBA and JOBB produced. In this tree they run IEFBR14, so ask whether the real jobs differ.
- The definition of `submit` (`scripts/nightly.sh:4`): does it wait for the job, and what does it return?
- What triggers `scripts/nightly.sh` each night, and its history: cron, an enterprise scheduler, or an operator.
- Proof that JOBC has not run since it was retired (`scripts/nightly.sh:2`).
- Any downstream job, partner feed or report that consumes the output of JOBA or JOBB.

## What the harness asserts

| Assertion | Why it matters | Evidence |
|---|---|---|
| JOBA is submitted before JOBB | The only order the tree enforces. It is the temporal edge `job:JOBA` to `job:JOBB`, medium confidence. | `scripts/nightly.sh:4`, `scripts/nightly.sh:5` |
| If the JOBA submit fails, JOBB is not submitted and the wrapper exits non-zero | `set -e` aborts the chain. This failure behavior is part of what must not break. | `scripts/nightly.sh:3` |
| JOBC is never submitted | The submit line is commented out. A refactored chain that picks it up again would change the cycle. | `scripts/nightly.sh:6` |
| Each job ends with the same return code as legacy | The only observable result of an IEFBR14 step in the tree. | `jcl/JOBA.jcl:2`, `jcl/JOBB.jcl:2` |
| Whether JOBB waits for JOBA to finish is the same as legacy | Depends on `submit`, which is undefined in the tree. Decide before porting, and record any change as a deviation. | inference |

## Normalization spec

Every entry is a claim that a difference does not matter. A human signs off on each.

- Job numbers (JOBnnnnn), submit and start and end timestamps, run dates in headers, sysout page numbers.
- Elapsed time: compare order, not durations, unless the client names a service window.
- Trailing whitespace and fixed-width padding in captured output.
- Do not normalize away submit order or return codes. They are the assertions.

## Mainframe traps, and which apply here

- **Job order.** Applies. The temporal edge is the only order in the tree, and it comes from a shell wrapper, not from the JCL.
- **Packed decimal, collating sequence, `REDEFINES`, record padding.** No datasets, COBOL programs or record layouts exist in this tree, so none applies to wave 1. They apply the moment the real jobs run application programs. See the second sensitivity in `04-estimate.md`.

## Cases beyond the common path

- **Boundary dates.** A run on month-end, quarter-end, fiscal year-end, leap day, and the two DST transitions, because the cycle is nightly and its trigger time may shift.
- **Failure of JOBA.** Force a non-zero result and check the wrapper stops before JOBB. Only meaningful once `submit` is defined.
- **Failure of JOBB.** Check the wrapper's exit status and that nothing else is submitted.
- **A night the trigger fires twice, or not at all.** The tree shows no lock or guard, so record what legacy does.
- **The bad data that is already there.** Not applicable in this tree, because there is no input data. Ask whether the real jobs read any.
- **Fiscal close.** Ask whether any real work only runs at fiscal close. IEFBR14 gives no hint.

## Deviation Register

Nothing differs from legacy without a row here.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact |
|---|---|---|---|---|---|
| DEV-001 | `jcl/JOBC.jcl` exists but is never submitted (`scripts/nightly.sh:6`) | Removed from the estate | Retired per `scripts/nightly.sh:2` | pending, client owner | None expected. Confirm nothing else submits it |
| DEV-002 (candidate) | Order is submission order set by shell line order (`scripts/nightly.sh:4`, `scripts/nightly.sh:5`) | Scheduler-enforced completion dependency | Only if `submit` turns out to be asynchronous | pending, client owner | JOBB could start later than it did before |

## Exit bar for wave 1

Wave 1 is done when:

- the replay or parallel-run diff is clean, modulo the normalization spec and the Deviation Register
- the boundary cases above pass, including the JOBA failure case
- the harness is in version control and runs in CI
- the Deviation Register is signed by someone with authority to sign it

Not when the refactored chain compiles or runs once.

## After cutover

Keep the harness. It becomes the regression suite for the modernized chain, and for any real job later added behind the wrapper.
