# 06 Test strategy

This follows the `behavioral-equivalence` skill. The bar is not "it passes the tests". For the inputs this system actually sees, the new implementation must give the same outputs as the old one. Where it does not, someone decided that on purpose and wrote it down.

## What must not break

The client's item is "the nightly batch cycle". The tree holds one batch job, `job:MAINJOB`, and no scheduler, so nothing in it says that job runs nightly or is the cycle (`app/jcl/MAINJOB.jcl:1`, `analysis` field `warnings`). I have not invented that mapping. Until the client confirms it, `job:MAINJOB` is a candidate anchor, and the test strategy below is written so it holds if the mapping is confirmed. See Open Question 1 in `00-summary.md`.

## The tree holds no datasets

The extractor found no dataset node, and the job has no DD statements (`app/jcl/MAINJOB.jcl:2`, `analysis` field `node_counts`). So the oracle cannot come from files in the tree. It has to come from job output, logs and reports. What I would ask the client to supply:

1. Job logs for MAINJOB for the last 12 months: JES output with return codes, step names and run times. Include at least one month end and one year end.
2. SMF type 30 step records, or the site's equivalent, showing which programs ran, including OLDPGM, with what return code.
3. The full JCL as run, with every DD statement, STEPLIB and PARM, plus the compile listing or load module date of PGMMAIN, OLDPGM and NEWPGM.
4. Anything the cycle produces that people or partners read: archived reports, statements, extract files, or GDG generations. Each is a golden master with a date on it.
5. The scheduler export, so job order across jobs is known.
6. Whether both systems can run on the same night. A parallel run is the strongest oracle, and teams often wrongly assume it is impossible.

## Oracle per wave

| Wave | Oracle, strongest first | Coverage label | Evidence |
|---|---|---|---|
| 1 | 1. Parallel run of MAINJOB on the same nightly input, over a window that holds a month end. 2. Replay of archived job logs, return codes and any archived outputs. 3. Characterization tests from the source, only as a last resort. | Provisional until the client supplies items 1 to 4 above. | inference |

Characterization tests from the source would prove almost nothing here. They encode what the code says, and the code says GOBACK (`app/cbl/OLDPGM.cbl:4`, `app/cbl/NEWPGM.cbl:4`). Do not let a green run of them stand in for equivalence.

## What the harness asserts at the wave 1 boundary

| Assertion | Why | Evidence |
|---|---|---|
| Step S1 runs and ends with the same return code as legacy | It is the only observable the tree shows. | `app/jcl/MAINJOB.jcl:2` |
| PGMMAIN calls OLDPGM, then NEWPGM, in that order | The order is in the source. Today both bodies are empty, so the order changes nothing, but a real body added later would make it matter. There is no temporal edge for it in the graph. | `app/cbl/PGMMAIN.cbl:4`, `app/cbl/PGMMAIN.cbl:5` |
| OLDPGM is still called | Dropping it as dormant would break the call. See `05-dead-code.md`. | `app/cbl/PGMMAIN.cbl:4` |
| Every dataset, report or extract the client names is identical to legacy after normalization | The client has to name them. None is visible. | inference |
| Job order across jobs is kept | The temporal edges are the list of orders to keep. None exist in the graph yet. | `analysis` (field `edge_counts`) |

## Normalization spec

Keep this short, and have a human sign it off. Every entry asserts that a difference does not matter, and each is a place a real bug can hide.

| Item | Rule | Evidence |
|---|---|---|
| Timestamps, run IDs, JES job numbers, page numbers | Mask before the diff | inference |
| Run time and elapsed time | Ignore, but log any large change | inference |
| Trailing whitespace and record padding | Decide which differences matter, with the client, and write it down | inference |
| Record order in any output | Treat as significant until the client says it was incidental | inference |
| Money fields, if any appear | Compare in a decimal type with zero tolerance. Never IEEE floats. | inference |

The mainframe traps of packed decimal, EBCDIC collating order and REDEFINES do not arise in the tree. None of the three programs has a DATA DIVISION (`app/cbl/PGMMAIN.cbl:1`). They will need entries the moment real source arrives.

## Input space to cover deliberately

- Boundary dates: month end, quarter end, fiscal year end, leap day, DST change. The capture window must include them.
- The empty run: a night with no input.
- The enormous run: the largest night the old system handled.
- Bad data already in the system: the new code must reproduce the legacy behavior on it.
- Paths that only run at fiscal close. The tree shows no test of a date, so none is visible, but the tree may be a fragment. Ask the client.

## Exit bar for wave 1

Wave 1 is done when all of these hold:

- The replay or parallel-run diff is clean, modulo the normalization spec and the Deviation Register.
- Every boundary case above passes.
- The harness is under version control and runs in CI.
- The Deviation Register is signed by someone with the authority to sign it.

Not when the port compiles. Not when it passes the tests written alongside the port. Keep the harness after cutover as the regression suite for the modernized system, and budget for maintaining it.

## Deviation Register

No deviation is proposed yet, so there are no rows. The first candidate, if the client decides it: retire OLDPGM. That would be a row here, with the approver and the downstream impact. It is not a decision for the assessor.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
