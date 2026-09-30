# 06 Test strategy

Follows the `behavioral-equivalence` skill. The bar is not that the port compiles. It is that for the inputs the system really sees, the new code produces the same outputs as the old, and every difference was decided on purpose.

What must not break: the nightly batch cycle. Nothing in the tree ties PROGA or PROGB to it, so the first job of this strategy is to get that link from the client.

## No datasets in the tree

The tree holds no dataset, no file declaration and no JCL (`graph.json` `meta.files_seen`). The oracle therefore cannot come from files the programs read or write. It has to come from job output, logs and reports. PROGA writes nothing itself. Its observable behavior is its return code plus whatever the named target does (`app/cbl/PROGA.cbl:9`).

## Oracle per wave

| Wave | Oracle, strongest first | Coverage label | Evidence |
|---|---|---|---|
| 1 (PROGB, PROGA) | 1. Parallel run of the old and new job step on the same input card, if the old job can stay up. 2. Replay of captured input cards and job output across a full cycle, month-end included. 3. Archived job logs as a golden master. 4. Characterization tests from source, only if 1 to 3 are unavailable, and labeled provisional. | Provisional until the client confirms which oracle exists | inference |

Parallel run should be easy to ask for here. The programs do no I/O, so running old and new side by side has no side effects of its own. The targets PROGA calls may. Ask.

## Ask the client to supply

- The JCL job, or scheduler entry, that runs PROGA, and the SYSIN or console value that feeds its ACCEPT (`app/cbl/PROGA.cbl:8`).
- Every distinct value of that input over the last 12 months, with run dates. This is also the dead-code telemetry.
- Job logs or SMF records for those runs: return codes, run times and abend codes.
- The archived output of whatever each named target produces.
- The operator procedure for a failed step, because PROGA's CALL has no ON EXCEPTION (`app/cbl/PROGA.cbl:9`).

## Normalization spec

Every row is a claim that a difference does not matter. A human signs off on the list.

| Item to normalize | Rule | Risk if wrong | Evidence |
|---|---|---|---|
| Job ID, run time, job log timestamps | Mask | A real timing or ordering change is hidden | inference |
| Return code | Do not normalize. Compare exactly. | none | `app/cbl/PROGB.cbl:4` |
| Padding of the 8 byte name field | Compare trimmed. A short name arrives space padded. | A name with trailing junk is treated as valid | `app/cbl/PROGA.cbl:5` |
| Case of the name | Do not normalize until legacy behavior is observed. Mainframe load module names are upper case. | A lower case name that used to fail now succeeds | inference |
| Target program output | Whatever the target's own wave decides. Keep zero tolerance on money fields. | Rounding defects hide as noise | inference |

## Cover the input space on purpose

| Case | Why | Evidence |
|---|---|---|
| Every distinct name seen on the input card in 12 months | It is the only bound on what PROGA can call | `app/cbl/PROGA.cbl:9` |
| A name that matches no program | The CALL has no ON EXCEPTION, so today's behavior is a run-time abend. The port must reproduce that on purpose, or the difference goes in the deviation register. | `app/cbl/PROGA.cbl:9` |
| An empty or all-blank input | ACCEPT leaves the field blank or unchanged. What happens next is unknown. | `app/cbl/PROGA.cbl:8` |
| A name longer than 8 characters | The receiving field holds 8 bytes, so it is truncated or rejected. Check on the real platform, do not assume. | `app/cbl/PROGA.cbl:5` |
| A name that resolves to PROGB | The in-tree target. Expect return code 0 and no output. | `app/cbl/PROGB.cbl:4` |
| Month-end, quarter-end and fiscal year-end runs | Any target that only runs at close is the usual source of a late failure | inference |

## Mainframe traps that apply here

| Trap | Applies? | Evidence |
|---|---|---|
| Packed decimal and rounding | Not in this tree. It applies to the targets, which are unknown. | inference |
| Collating sequence | Not in this tree. No sort, no keyed file. | inference |
| REDEFINES, record padding | Not in this tree. The only data item is one 8 byte field. | `app/cbl/PROGA.cbl:5` |
| Job order | No temporal edge was found (`graph.json` `analysis.edge_counts` has calls only). The order that matters is in the client's JCL, not the tree. The harness must keep whatever it is. | inference |

## Deviation register

Nothing may differ without a row here. It starts empty.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact |
|---|---|---|---|---|---|
| D-001 | Reserved for the unknown-name abend behavior of PROGA | To be decided | To be decided | Unassigned | To be decided |

## Exit bar for wave 1

- Replay diff is clean, modulo the normalization spec and the deviation register.
- Every case in the input table above passes, including the unknown name case.
- The harness is under version control and runs in CI.
- The deviation register is signed by someone with the authority to sign it.
- The harness is kept after cutover as the regression suite.
