# 06 Test strategy

Definition of "correct" for wave 1, the nightly batch cycle. For the inputs the cycle sees in
production, the new implementation runs the same jobs, in the same order, with the same return codes,
and produces the same outputs. Where it differs, someone decided that on purpose and wrote it down.

## The tree holds no datasets

The tree has no dataset, no report, no extract and no archive (analysis field `data_hubs` is empty,
`meta.files_seen` counts zero programs). Each job runs only IEFBR14 with no DD statement
(`jcl/JOBA.jcl:2`, `jcl/JOBB.jcl:2`, `jcl/JOBC.jcl:2`). So the oracle cannot come from data in the tree. It
has to come from job output, logs and reports the client holds. What the harness can observe from the
tree alone is the order of two jobs and the stop rule of a wrapper (`scripts/nightly.sh:3`,
`scripts/nightly.sh:4`, `scripts/nightly.sh:5`). That is a thin oracle. It is why wave 1 is rated low
confidence.

## What to ask the client to supply

1. JES job logs and return codes for JOBA and JOBB from every night in the last 12 months, and SMF
   records if they exist. They give the real order, timing and return codes, and they are the telemetry
   for `05-dead-code.md`.
2. The scheduler or operator record of what starts `scripts/nightly.sh`, and at what time and time zone.
3. The definition of the `submit` command used on `scripts/nightly.sh:4`, and whether it waits for the job.
4. Every output the nightly cycle produces that a person or another system consumes: reports,
   extracts sent to partners, files read by later jobs. The must-not-break item names the cycle and
   not its outputs, so these are the real anchors.
5. Archived generations of those outputs, from GDG datasets or a report archive, covering at least
   one month-end and one year-end.
6. Run history for JOBC, to settle whether it is retired (`scripts/nightly.sh:2`).
7. The JCL and programs that JOBA and JOBB run in production, if they are not the IEFBR14 stubs in the tree.

## Oracle per wave

| Wave | Oracle | Why | Confidence | Evidence |
|---|---|---|---|---|
| 1 | First choice is a parallel run of the old wrapper and the new orchestration for at least one month-end. Fallback is a golden master built from archived job logs and return codes. Characterization tests from source are the last resort. | The jobs run no application code in the tree, so a parallel run costs little. It needs the old system to stay up and the new run to be in a mode that does not duplicate real side effects. | low | inference |

Characterization tests from the source would prove almost nothing here, because the source is two
lines per job and does nothing (`jcl/JOBA.jcl:2`). Label any such coverage provisional.

## Normalization spec

Every entry is a claim that a difference does not matter. Keep the list short and have a person sign it.

| Item | Rule | Confidence | Evidence |
|---|---|---|---|
| Job numbers and run IDs | Ignore. JES assigns them per run. | high | inference |
| Submit, start and end timestamps | Compare order and elapsed window, not the clock time. | medium | inference |
| Order of JOBA and JOBB | Do not normalize. Order is compared exactly. | medium | `scripts/nightly.sh:4`, `scripts/nightly.sh:5` |
| Return codes | Do not normalize. Compare exactly. | high | inference |
| Sysout page numbers and banner text | Ignore. | medium | inference |

Nothing about monetary fields, padding or record order is listed. No such data is in the tree. If the client
supplies outputs, add packed decimal, EBCDIC collating order and padding to this table then.

## Cases to cover on purpose

| Case | What it checks | Confidence | Evidence |
|---|---|---|---|
| JOBA submit fails | JOBB must not run. The wrapper stops on a failed command. | medium | `scripts/nightly.sh:3`, `scripts/nightly.sh:4` |
| JOBA is submitted but abends afterward | Unknown today. If `submit` returns at once, JOBB may run anyway. The answer must be recorded, and the new system must match it or the difference goes in the register. | low | inference |
| JOBB runs before JOBA completes | Shows whether the order was ever enforced. Decides whether the temporal edge is a real dependency. | low | `scripts/nightly.sh:5` |
| JOBC is not run | A negative test. The new system must not start JOBC unless the client says it still runs. | low | `scripts/nightly.sh:6` |
| Month-end and year-end night | The paths that only run at close. The capture window must include them. | medium | inference |
| Daylight saving change night | A job started by a time-of-day rule can run twice or not at all. | medium | inference |
| Leap day | Boundary date. | low | inference |
| A night with no work to do | The empty case. IEFBR14 with no DD returns at once, and the new system must not fail on empty. | medium | `jcl/JOBA.jcl:2` |

## Mainframe traps

Packed decimal, collating sequence, REDEFINES and record padding do not apply here. The tree has no
COBOL, no copybook and no dataset. Job order does apply: the temporal edge JOBA to JOBB is the list of
orders the harness must keep (analysis, `graph.json` edge kind `temporal`), and it stands on the order of two
lines (`scripts/nightly.sh:4`, `scripts/nightly.sh:5`).

## Deviation Register

Seeded with what this assessment already knows. Nothing differs from legacy without a row here. No row is
approved. Every row waits for a person with the authority to sign.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| DR-1 | JOBC is in the tree and the wrapper comment calls it retired. | JOBC is not ported and is not scheduled. | Proposed. Depends on the client confirming it is retired. | not yet approved | Unknown. Something outside the tree might submit it. | `scripts/nightly.sh:2`, `scripts/nightly.sh:6` |
| DR-2 | JOBB follows JOBA by the order of two submit lines. Whether it waits for JOBA to finish is unknown. | The target orchestration states the dependency explicitly, either as wait-for-completion or as a declared no-dependency. | Proposed. Depends on what the discovery in `04-estimate.md` finds. | not yet approved | Failure handling on a JOBA abend may change. | `scripts/nightly.sh:4`, `scripts/nightly.sh:5` |

## Exit bar for wave 1

- The replay or parallel run diff is clean for the order, return codes and outputs, modulo the
  normalization spec and the register.
- Every case in the table above passes, including a month-end night.
- The harness is under version control and runs in CI.
- The register is signed by someone with the authority to sign it.
- The client has answered the questions in `00-summary.md` about `submit`, JOBC and what the jobs run in
  production. Without those answers a clean diff proves only the thin oracle in this tree.

## Keep the harness

The harness becomes the regression suite for the target orchestration. Budget for its upkeep.
The order and return code check is small, and it is the only executable specification of the nightly
cycle that exists today (inference).
