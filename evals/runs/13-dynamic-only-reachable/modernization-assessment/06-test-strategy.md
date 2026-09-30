# 06 Test strategy

Handed off from the assessment to the `behavioral-equivalence` skill. The bar is that for the inputs
this system actually sees, the new implementation gives the same outputs as the old one. Where it does
not, someone decided that on purpose and wrote it down.

The client said the nightly batch cycle must not break. That is the anchor for every choice below.

## The oracle problem in this tree

The tree holds no datasets. The JCL maps no DD (`app/jcl/MAINJOB.jcl:2`) and the programs open no
file (`app/cbl/PGMMAIN.cbl:1-10`). There is no record layout to compare and no expected output on file.
So the oracle has to come from job output, logs and reports, and from the inputs the job was given.

The job's real input is one value. `PGMMAIN` reads a program name with `ACCEPT` and calls it
(`app/cbl/PGMMAIN.cbl:8`, `app/cbl/PGMMAIN.cbl:9`). So the harness has two parts to prove: that the
dispatcher routes each name to the same program, and that each routed program behaves the same. The
second part cannot be designed until the target set is known.

## Oracle per wave

There is one wave.

| Rank | Oracle | Status for wave 1 | Evidence |
|---|---|---|---|
| 1 | Parallel run of legacy and new dispatcher on the same nightly input | Ask first. It is the strongest and this job is small enough that it may be possible. It needs the legacy job to stay up | inference |
| 2 | Replay of captured production input: the `SYSIN` values and any files the called programs read | The best realistic choice. The capture window must include a month-end and a fiscal year-end | inference |
| 3 | Golden master from archived output: job logs, `SYSOUT`, reports and extracts from past runs | Likely available for a nightly cycle. Ask for it | inference |
| 4 | Characterization tests written from the source | Last resort. `PGMMAIN` has no logic to characterize beyond routing, and `HIDDEN01` only returns (`app/cbl/HIDDEN01.cbl:4`). The coverage would be provisional | `app/cbl/PGMMAIN.cbl:9` |

## What to ask the client to supply

1. The `SYSIN` (or `PARM`) history for `job:MAINJOB` for at least 12 months. This gives the real set of
   names and closes the open computed call (`app/cbl/PGMMAIN.cbl:8`).
2. The full JCL as it actually runs, including any `SYSIN`, DD statements, procs and overrides. The copy
   in the tree has none (`app/jcl/MAINJOB.jcl:2`).
3. The scheduler export, so the nightly cycle order is known, plus the job log and SMF records for the
   run history. These also serve as the telemetry for the dead-code register.
4. The load library listing, to see which modules `PGMMAIN` could call.
5. Archived generations of every report or extract the nightly cycle produces.
6. Any extract sent to a partner from that cycle. It is an executable specification of the format.

## Normalization spec

Every entry is a claim that a difference does not matter. Keep this list short and have a person sign
it. Nothing in this tree is a money field, so the money rule below is written for the programs the
dispatcher calls, which are not yet known (inference, `app/cbl/PGMMAIN.cbl:9`).

| Item | Rule | Why it may hide a bug | Evidence |
|---|---|---|---|
| Timestamps, job numbers, run IDs, page numbers | Mask before diff | A run ID that drives a downstream lookup is not noise | inference |
| Packed decimal (`COMP-3`) and money | Compare in a decimal type with zero tolerance. Do not use floats | Rounding and truncation differ from IEEE floats. That is a defect, not noise | inference |
| Record order | Keep the legacy order until a person confirms it was incidental | A downstream consumer may depend on it | inference |
| Collating sequence | Test the sort order, since EBCDIC and ASCII differ | Only matters if a called program sorts or reads a keyed file | inference |
| Padding and low values | Decide which differences matter and write it down | Fixed-width records pad with spaces or binary zeros | inference |
| `WS-PGM-NAME` padding | The name is `PIC X(8)`, so compare it padded to eight characters | A trailing-space difference could route to a different target | `app/cbl/PGMMAIN.cbl:5` |

## Targeted cases

Production replay covers the common name well and the dangerous names badly. Add these:

- A blank name and an all-spaces name. The call has no `ON EXCEPTION` clause (`app/cbl/PGMMAIN.cbl:9`),
  so the legacy behavior is whatever the runtime does. Capture it.
- A name that is not in any library. Same reason.
- The name `HIDDEN01`, to check the call and return path (`app/cbl/HIDDEN01.cbl:4`).
- The name `PGMMAIN` itself, to see what the legacy runtime does with a self-call
  (inference, `app/cbl/PGMMAIN.cbl:2`).
- A name longer than eight characters, which `ACCEPT` would truncate (inference,
  `app/cbl/PGMMAIN.cbl:5`).
- A run with no input at all, since the JCL supplies none (`app/jcl/MAINJOB.jcl:2`).
- Month-end, quarter-end and year-end runs of the nightly cycle, and the run that only happens at
  fiscal close, which is the most common source of a failure found after cutover.
- A zero-record run and a run at the largest volume the cycle has seen.
- Whatever bad data the called programs already carry. The new system must reproduce what the legacy
  one does on it.

## Order the harness must keep

The tree has one step inside one job, so there is one ordering edge inside the tree and no ordering
edge between jobs (`app/jcl/MAINJOB.jcl:2`). The order between jobs in the nightly cycle is not
visible, because no scheduler was parsed. The harness cannot check that order until the scheduler
export arrives.

## Deviation Register

Nothing may differ from the legacy behavior without a row here. It starts with the one deviation the
refactor target already requires and the one open decision.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact |
|---|---|---|---|---|---|
| D-001 | `PGMMAIN` calls any name it is given (`app/cbl/PGMMAIN.cbl:9`) | The dispatcher routes only to a fixed registry of known targets | The refactor target replaces a free call on an input string with an explicit list. Proposed, not yet agreed | Not yet approved | Any name outside the registry stops working. The `SYSIN` history must show none is in use |
| D-002 | A blank, missing or unknown name has no handler in the source (`app/cbl/PGMMAIN.cbl:9`) | To be decided | The legacy runtime behavior must be captured first, then a person decides whether to copy it or not | Not yet approved | Unknown until the caller of the job is known |

## Exit bar for wave 1

Wave 1 is done when all of these hold:

- the replay diff is clean, modulo the normalization spec and the deviation register
- every targeted case above passes, including the ones that are only a runtime error in the legacy system
- the harness is under version control and runs in CI
- the deviation register is signed by someone with the authority to sign it
- the set of names `PGMMAIN` has been given is known, and `HIDDEN01` is either shown to be live or kept

Not when the port compiles, and not when it passes tests written alongside the port.

## After cutover

Keep the harness. It becomes the regression suite for the modernized dispatcher, and it is the only
executable specification this job has ever had.
