# 06 Test strategy

This follows the `behavioral-equivalence` skill. The bar is: for the inputs the nightly batch cycle
sees in production, the ported job produces the same outputs as the legacy job, and every difference
is written down and approved.

## The tree holds no datasets

Neither program opens a file, and the job has no DD statement (`app/cbl/PGMMAIN.cbl:1`,
`app/cbl/HIDDEN01.cbl:1`, `app/jcl/MAINJOB.jcl:2`, and `analysis`, field `data_hubs`, which is empty).
No dataset can be replayed from this tree. The oracle has to come from job output, logs and reports
the client holds. `inference`

**What to ask the client to supply**

| Ask | Why | Confidence | Evidence |
|---|---|---|---|
| Job logs or SMF records for `MAINJOB`, twelve months, including a month end and a year end | Show return codes, run time and which programs ran. They also settle what `ACCEPT` supplied | low | `app/cbl/PGMMAIN.cbl:8` |
| The `SYSIN` member, wrapper or scheduler entry that feeds `WS-PGM-NAME` | The JCL in the tree does not supply the name | medium | `app/jcl/MAINJOB.jcl:2` |
| Every program the run-time name can select, with its source | The callee set is open, so the harness boundary is open | low | `app/cbl/PGMMAIN.cbl:9` |
| Archived reports, extracts and generations the callee produces, and the files sent to partners | Each is a dated golden master | low | inference |
| What "the nightly batch cycle" contains, as a list of jobs and their order | The tree has one job and no scheduler | low | `analysis`, field `warnings` |

## Oracle per wave

| Wave | Oracle, strongest first | Provisional? | Evidence |
|---|---|---|---|
| 1 (`job:MAINJOB`, `PGMMAIN`) | 1. Parallel run of the legacy and the ported job on the same nightly input, if the legacy job can stay up. Ask first. 2. Replay of captured run-time inputs against the port. 3. Golden master from archived job output and reports. 4. Characterization tests, only if 1 to 3 are unavailable | Yes until the callee set is bounded and one of 1 to 3 exists. Characterization coverage is provisional | `modernization-assessment/waves.json:8` |

There is only one wave, so there is one oracle decision.

## Normalization spec, for wave 1

Each line asserts that a difference does not matter. A human signs off the list.

| Item | Rule | Risk if wrong | Evidence |
|---|---|---|---|
| Job return code | Compare exactly. It is the one output the tree shows, because `PGMMAIN` ends with `GOBACK` | A silent change of return code changes what the scheduler does next | `app/cbl/PGMMAIN.cbl:10` |
| Timestamps, run IDs, job numbers, page numbers in job output | Mask before diffing | A real change hidden under a mask | inference |
| Packed decimal and rounding | Not present in the two programs. Add a zero-tolerance decimal rule when the callee arrives, if it has money fields | Float rounding is a defect, not noise | inference |
| Record order and collating sequence | Not present here. Confirm for the callee's files | An ASCII sort reorders a key sequence silently | inference |
| Trailing whitespace and padding | Decide per output once outputs are known | Padding a partner extract breaks the partner | inference |

## Input space to cover on purpose

| Case | Why | Confidence | Evidence |
|---|---|---|---|
| Every program name seen in the run-time input over twelve months | The name selects the whole behavior of the job | low | `app/cbl/PGMMAIN.cbl:9` |
| A blank name | `WS-PGM-NAME` has no initial value and `ACCEPT` may leave it blank | medium | `app/cbl/PGMMAIN.cbl:5` |
| A name that does not resolve to a program | The `CALL` has no exception handling, so the legacy run-time decides what happens. The port must reproduce it, and the harness must capture it | medium | `app/cbl/PGMMAIN.cbl:9` |
| No `SYSIN` present | The JCL has none. Whether the job abends or takes a default is not shown | low | `app/jcl/MAINJOB.jcl:2` |
| Month end, quarter end, year end and leap day runs | The cycle is nightly, so paths that fire only at close are the main risk. Which callee runs at close is unknown | low | inference |
| `HIDDEN01` named as the callee | It is in the tree and is the one known candidate. Expected result is a return with no output | medium | `app/cbl/HIDDEN01.cbl:4` |

## Job order

The temporal edges in `graph.json` are the orders the harness must keep. There are none: the tree has
no scheduler and one step (`analysis`, field `warnings`, and `app/jcl/MAINJOB.jcl:2`). If the nightly
cycle has more jobs, this section is incomplete. `inference`

## Deviation Register

Empty. No intentional difference is proposed. Nothing gets to differ without a row here.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| none yet | | | | | | inference |

## Exit bar for wave 1

Wave 1 is done when all of these hold:

- the replay or parallel-run diff is clean, apart from the normalization spec and the register
- every case in the input-space table passes
- the harness is under version control and runs in CI
- the register is signed by someone with the authority to sign it
- the callee set has been named by the client, and every callee has an oracle

Not when the port compiles, and not when it passes tests written alongside it.

## Keep the harness after cutover

The harness becomes the regression suite. Budget to maintain it. `inference`
