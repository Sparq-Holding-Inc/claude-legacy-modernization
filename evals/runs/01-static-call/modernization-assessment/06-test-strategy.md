# 06 Test strategy

Skill: `behavioral-equivalence`. The bar is not "it compiles" and not "it passes the tests written with the
port". The bar is that the new implementation produces the same outputs as the old one on the inputs the
system actually sees, and that every difference is written down on purpose.

## The tree holds no datasets

Neither program opens a file, so there is no master to diff. The oracle has to come from job output, logs
and return codes (`app/cbl/PROGA.cbl:5`, `app/cbl/PROGA.cbl:7`, `app/cbl/PROGB.cbl:4`). The observable
behavior of the pair is small: one line written by DISPLAY, a call that returns, and a normal end.

## Oracle for wave 1

| Rank | Oracle | Available? | Evidence |
|---|---|---|---|
| 1 | Parallel run of the legacy job and the port on the same nightly input | Ask. The tree cannot say. With no dataset the input is the job's parameters and its place in the cycle. | inference |
| 2 | Captured job output replayed against the port | Ask the client for the job logs from the nightly cycle | inference |
| 3 | Golden master from archived job output | Ask the client for archived SYSOUT of the job that runs PROGA. The DISPLAY line is in it on every run. | `app/cbl/PROGA.cbl:5` |
| 4 | Characterization tests from source | Available now. Weakest. Encodes what the code says, not what it does. Provisional. | `app/cbl/PROGA.cbl:6` |

Chosen oracle: rank 3 if the client supplies archived SYSOUT, otherwise rank 4, labeled provisional. This is
a decision made from what the tree offers, and the client should confirm it.

## What to ask the client for

- The JCL member and the scheduler entry that run PROGA, and the place of that job in the nightly batch cycle.
- SYSOUT, return codes and elapsed times from the job for a full cycle. It should include month-end.
- The compile and link options for both programs, in particular DYNAM, so the call can be tested as it
  actually binds.
- The name of anything that reads the job log or the return code of this job.

## Normalization spec

| Item | Decision | Why it might hide a bug | Evidence |
|---|---|---|---|
| Job name, job number, run timestamp in SYSOUT | Ignore | Only if nothing keys on them | inference |
| The DISPLAY text `CALL FAILED IF WE GET HERE` | Keep exact. Do not normalize it | It prints on every run, ahead of the call, so a log scraper may depend on it | `app/cbl/PROGA.cbl:5` |
| Return code | Compare exactly | PROGA ends with STOP RUN and sets none, so a port that returns a different code changes step condition tests | `app/cbl/PROGA.cbl:7` |
| Packed decimal, collating sequence, REDEFINES | Not applicable. No data items exist | None | `app/cbl/PROGB.cbl:3` |

Keep the list short and have a human sign it.

## Targeted cases

- The normal run: PROGA prints its line, calls PROGB, PROGB returns, PROGA stops.
- PROGB missing from the load library. There is no ON EXCEPTION at `app/cbl/PROGA.cbl:6`. Capture what the
  legacy job does, since a port that continues silently changes the batch cycle. Inference.
- Boundary dates, empty input and bad legacy data: none of them reach code here, because neither
  program reads input. Say so in the harness README, so nobody adds cases to look busy.
- The job placed in the cycle at month-end and at year-end: the job stream around it may behave differently
  even if these two programs do not. Inference.

## Job order

`graph.json` holds no temporal edges, because there is no scheduler or JCL in the tree. The orders the harness
must keep are unknown. Getting them from the client is the first task of the wave.

## Deviation Register

Empty. No intentional difference has been agreed.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| none yet | The DISPLAY at line 5 says a call failed, and prints on every run | Not decided | Not decided | Not decided | Unknown. A log scraper may match the text | `app/cbl/PROGA.cbl:5` |

The first candidate entry is that DISPLAY. Do not change its text without an approver's name in this row.

## Exit bar for wave 1

- The replay diff is clean, modulo the normalization spec and the register above.
- The normal run and the missing-module case both pass.
- The harness is under version control and runs in CI.
- The register is signed by someone who can sign it.

## After cutover

Keep the harness. It becomes the regression suite for the port and is the only executable specification of the
job. Budget for its upkeep.
