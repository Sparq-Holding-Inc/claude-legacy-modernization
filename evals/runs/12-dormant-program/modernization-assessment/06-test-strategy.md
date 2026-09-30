# 06 Test strategy

Follows the `behavioral-equivalence` skill. What must not break: the nightly batch cycle. Definition of correct for wave 1: for the inputs MAINJOB actually sees, the modernized job runs the same steps in the same order and ends with the same return codes and the same job log content, and any difference is written in the deviation register.

## The problem with this tree

The tree holds no datasets. The step has no DD statements and the programs read and write nothing (`app/jcl/MAINJOB.jcl:2`, `app/cbl/PGMMAIN.cbl:4`). There are no record layouts to compare, so the oracle cannot be a file diff. It has to come from job output, logs and reports. A test written from this source alone would compare `GOBACK` to `GOBACK` and pass. That proves nothing about the deployed system, which is why the ask list below matters more than any tool.

## Oracle for wave 1

| Rank | Oracle | Verdict for wave 1 | Evidence |
|---|---|---|---|
| 1 | Parallel run of legacy and new MAINJOB on the same inputs, diffing the job log and return codes | Preferred. Ask whether the legacy system can stay up for it. No datasets means little to isolate | inference |
| 2 | Replay of captured runs. The capture window must include month-end and fiscal year-end | Needs the job logs. Ask for them | inference |
| 3 | Golden master from archived job logs, SYSOUT and reports for the last 12 months | Likely available at any mainframe shop. Ask | inference |
| 4 | Characterization tests from source | Last resort. Provisional. It would only assert the call order at `app/cbl/PGMMAIN.cbl:4` and `app/cbl/PGMMAIN.cbl:5` | `app/cbl/PGMMAIN.cbl:4` |

## What to ask the client to supply

1. Job logs (JES output) and return codes for MAINJOB for at least 12 months, covering month-end and fiscal year-end.
2. The scheduler export that places MAINJOB in the nightly cycle: its predecessors, successors and run calendar.
3. SMF records or any run history showing whether OLDPGM has executed (`app/cbl/PGMMAIN.cbl:4`). This is also the telemetry that firms up `05-dead-code.md`.
4. The compiled load modules for OLDPGM and NEWPGM, or confirmation that the four line sources are what is deployed (`app/cbl/OLDPGM.cbl:4`, `app/cbl/NEWPGM.cbl:4`).
5. Anything MAINJOB produces that leaves the building: reports, extracts, partner files, messages. None is visible in the tree.

## Normalization spec (draft, needs human sign-off)

| Item | Rule | Why it is safe | Evidence |
|---|---|---|---|
| Job number, timestamps, run dates in the log | Mask | They differ on every run | inference |
| Step elapsed time and CPU time | Drop | Platform dependent | inference |
| Return code of each step | Compare exactly, tolerance zero | It is the one hard signal this job gives | `app/jcl/MAINJOB.jcl:2` |
| Order of calls inside PGMMAIN | Compare exactly | The order is the only behavior in the source | `app/cbl/PGMMAIN.cbl:4` |

No money fields, packed decimal, `REDEFINES`, or collating sequence issues exist in the tree, so the usual mainframe traps do not apply here. Re-check that if the load modules turn out to differ from the source.

## Job order

The temporal edges the harness must keep: step order inside MAINJOB, which is one step (`app/jcl/MAINJOB.jcl:2`), and the call order OLDPGM then NEWPGM (`app/cbl/PGMMAIN.cbl:4`, `app/cbl/PGMMAIN.cbl:5`). Order across jobs is unknown because no scheduler artifact was parsed, and the harness cannot keep an order nobody has told it.

## Targeted cases

| Case | Why | Evidence |
|---|---|---|
| Normal nightly run | The common path | `app/jcl/MAINJOB.jcl:2` |
| A run at month-end and a run at fiscal year-end | The paths that run only at close, where failures are found six months late | inference |
| A run with OLDPGM removed or stubbed | Settles whether OLDPGM has any effect. Do this in a copy, never in production | `app/cbl/PGMMAIN.cbl:4` |
| A run where a step fails | Checks that the cycle stops or continues as it does today | inference |

## Deviation register

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact |
|---|---|---|---|---|---|
| (empty) | | | | | |

Nothing may differ from the legacy run without a row here.

## Exit bar for wave 1

- Replay or parallel diff is clean, modulo the normalization spec and the deviation register.
- Every targeted case above passes.
- The harness is under version control and runs in CI.
- The deviation register is signed by someone with the authority to sign it.

Keep the harness after cutover. It becomes the regression suite for the modernized job.
