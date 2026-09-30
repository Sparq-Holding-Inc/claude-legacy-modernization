# 06. Test strategy — behavioral equivalence

One wave, one boundary. This file defines what "correct" means for it, and then says plainly
that the definition available is a thin one.

## The problem in one paragraph

**This tree contains no datasets.** There are no `ds:` nodes in `graph.json`, `analysis.data_hubs`
is empty, and `app/jcl/MAINJOB.jcl` has two lines — a JOB card and an EXEC card — with no DD
statement of any kind (`app/jcl/MAINJOB.jcl:1-2`). None of the three COBOL programs has a DATA
DIVISION or a FILE SECTION; each goes IDENTIFICATION DIVISION straight to PROCEDURE DIVISION
(`app/cbl/PGMMAIN.cbl:3`, `app/cbl/PGMLIVE.cbl:3`, `app/cbl/PGMDEAD.cbl:3`). No file is read, no
file is written, no record layout is shared, no report is produced. So the oracle cannot come from
data. It has to come from **job output, return codes and logs**, and from what the client can be
asked to supply.

## The oracle, per wave

| Wave | Boundary | Oracle | Rank | Why not stronger | Evidence | Confidence |
|---|---|---|---|---|---|---|
| 1 | `job:MAINJOB` submission → job completion | Parallel run of the job on both platforms, comparing **condition codes per step, SYSOUT/JESMSGLG text, and the fact that `PGMMAIN` called `PGMLIVE` and both returned** | 1 (parallel run), but over a near-empty output surface | There is no data output to diff. Parallel run is the right *mechanism* and it still only gets you a return code and a message log. | `app/jcl/MAINJOB.jcl:2`, `app/cbl/PGMMAIN.cbl:4` | high |

Parallel run is cheap here precisely because the job does nothing: it can be run repeatedly on both
platforms with no side effects to unwind (`analysis` — no dataset edges exist). Do not settle for
characterization tests generated from the source. The source is four statements; generating tests
from it would assert only that `GOBACK` returns (`app/cbl/PGMLIVE.cbl:4`), which is a tautology.

## What to assert at the wave-1 boundary

| # | Assertion | How | Evidence | Confidence |
|---|---|---|---|---|
| 1 | Step `S1` ends with the same condition code on both platforms | Capture MAXCC and the step CC from JESMSGLG on the source platform; compare with the runner's exit code on the target. Expect 0. | `app/jcl/MAINJOB.jcl:2` | high |
| 2 | The job itself ends with the same overall return code | Job-level MAXCC | `app/jcl/MAINJOB.jcl:1` | high |
| 3 | `PGMMAIN` actually invoked `PGMLIVE`, and `PGMLIVE` returned control | The call is the only behaviour in the system worth preserving. On the source platform, prove it with a CALL trace or a temporary DISPLAY in a copy of the load module; on the target, with the runner's call log. **Do not** prove it by reading the ported source — that is the thing under test. | `app/cbl/PGMMAIN.cbl:4`, `app/cbl/PGMLIVE.cbl:4` | medium |
| 4 | No dataset is created, opened or altered by the run | List the job's dataset activity from SMF type 14/15 (or the DD list in JESYSMSG) on both platforms; both must be empty of application datasets. This is the assertion that protects against a port that "helpfully" adds a log file the nightly cycle then trips over. | `app/jcl/MAINJOB.jcl:2` | medium |
| 5 | Elapsed time and region size stay within the nightly window's tolerance | SMF type 30. Only matters because the must-not-break item is a *cycle*, where a job that runs long is a job that breaks the cycle. | `app/jcl/MAINJOB.jcl:1` | medium |

Assertions 1 and 2 are the whole exit bar in practice. Assertions 3 to 5 are what stops the port
from passing for the wrong reason: a program that never ran at all would also return 0.

## Normalization spec

Short, because there is almost nothing to normalize. Every line is a human-signed assertion that a
difference does not matter.

| Field | Rule | Why it is safe to ignore | Evidence | Confidence |
|---|---|---|---|---|
| Job ID (`JOB00123`) | strip | Assigned by JES per submission. | `app/jcl/MAINJOB.jcl:1` | high |
| Timestamps in JESMSGLG | strip | Wall clock. | `app/jcl/MAINJOB.jcl:1` | high |
| System/LPAR name, JES node | strip | Platform identity is the thing being changed. | `app/jcl/MAINJOB.jcl:1` | high |
| CPU time, elapsed time, region used | compare against a **threshold**, not for equality | Assertion 5 above. Equality is meaningless across platforms; a ceiling is not. | `app/jcl/MAINJOB.jcl:1` | medium |
| Accounting field `(ACCT)` on the JOB card | strip | Chargeback, not behaviour. | `app/jcl/MAINJOB.jcl:1` | high |
| Trailing whitespace on SYSOUT lines | strip | Fixed-width print padding. | `app/jcl/MAINJOB.jcl:1` | high |
| Condition codes | **zero tolerance, exact match** | This is the assertion. | `app/jcl/MAINJOB.jcl:2` | high |

**Not in this spec, deliberately:** no floating-point tolerance, no decimal rounding rule, no
EBCDIC/ASCII collating rule, no `REDEFINES` branch coverage, no record-padding rule. Those are the
traps that sink real mainframe ports, and none of them applies, because there is no arithmetic, no
record and no sort anywhere in the tree (`app/cbl/PGMMAIN.cbl:4-5`, `app/cbl/PGMLIVE.cbl:4`).
**If the real nightly cycle arrives and it has any of those, this spec is not reusable — it was
written for a fragment.**

## Input-space coverage

The skill's checklist asks for boundary dates, empty and enormous inputs, accumulated bad data, and
fiscal-close paths. Applied honestly to this wave:

| Case class | Applicable? | Why | Evidence | Confidence |
|---|---|---|---|---|
| Boundary dates (month end, fiscal year end, leap day) | **no** | No program reads a date. There is no DATA DIVISION to hold one. | `app/cbl/PGMMAIN.cbl:3` | high |
| Empty and enormous inputs | **no** | No input file exists. | `app/jcl/MAINJOB.jcl:2` | high |
| Accumulated bad data | **no** | No data. | `analysis` (`data_hubs` empty) | high |
| Fiscal-close-only paths | **no** | No conditional logic; the procedure divisions are a CALL and two GOBACKs. | `app/cbl/PGMMAIN.cbl:4-5`, `app/cbl/PGMLIVE.cbl:4` | high |
| Job resubmission / restart | **yes** | A nightly cycle restarts failed steps. Run the job twice and confirm the second run is identical and harmless. This is the only genuine input-space case the tree supports. | `app/jcl/MAINJOB.jcl:1` | medium |
| Job run with `PGMDEAD` deleted from the load library | **yes** | `05-dead-code.md` proposes deleting `PGMDEAD`. Prove the cycle is unaffected by running wave 1 with it gone. | `app/cbl/PGMDEAD.cbl:2` | high |

One meaningful case and one deletion-safety case. That is the true coverage available.

## Deviation register

Empty at assessment time, and it should stay empty for this wave. A port of two no-op programs
that needs a behavioural deviation has gone wrong.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | none yet — `app/cbl/PGMLIVE.cbl:4` |

The one plausible entry is a target runner that emits a log file where the mainframe job emitted
none. If that happens it is a deviation and it needs a row, because a new file appearing in a
nightly cycle's working directory is exactly the kind of thing that breaks the cycle later.

## Exit bar for wave 1

- Parallel run diff clean under the normalization spec above, across at least five consecutive
  nightly slots (`app/jcl/MAINJOB.jcl:1`).
- Assertions 1 to 5 pass, including the "creates no dataset" check (`app/jcl/MAINJOB.jcl:2`).
- Resubmission case and the `PGMDEAD`-deleted case both pass (`app/cbl/PGMDEAD.cbl:2`).
- Harness is in version control and runs in CI. Given the boundary is a return code and a text
  diff, this is a shell script and there is no excuse for it not existing.
- Deviation register signed, even if it is empty. An empty register that someone signed is worth
  more than no register.

Keep the harness after cutover. It is the only executable specification this job will ever have
(`app/jcl/MAINJOB.jcl:1`).

## What to ask the client for

Because no oracle exists in the tree, these are the inputs that turn this strategy from a plan into
a test:

| # | Ask | Turns which weakness into strength | Evidence | Confidence |
|---|---|---|---|---|
| 1 | Archived JESMSGLG / JESYSMSG from three real runs of `MAINJOB`, including one month-end | Gives a golden master for the SYSOUT diff instead of a baseline captured today | `app/jcl/MAINJOB.jcl:1` | high |
| 2 | SMF type 30 records for `MAINJOB` over 30 days | Supplies the elapsed-time ceiling for assertion 5, and doubles as the runtime telemetry the dead-code register is missing | `app/jcl/MAINJOB.jcl:1` | high |
| 3 | SMF type 14/15 for `MAINJOB` | Proves empirically that the job touches no dataset, rather than inferring it from the absence of DD cards | `app/jcl/MAINJOB.jcl:2` | medium |
| 4 | The scheduler definition that submits `MAINJOB` | Establishes what the nightly cycle actually is and what runs either side of this job. No scheduler artifact was parsed. | `analysis.warnings` | high |
| 5 | Confirmation that the supplied load modules were compiled from these exact sources | If not, everything above tests the wrong artifact | `app/cbl/PGMMAIN.cbl:2` | medium |

Items 2 and 4 are the two that would most change this assessment, not just this test strategy.
