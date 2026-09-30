# 06 Test strategy

The bar: for the inputs this system really sees, the ported `PROGA` and `PROGB` produce the same outputs as the legacy ones, and any difference was chosen on purpose and recorded. The must-not-break item is "the nightly batch cycle". Target state is refactor, and telemetry is `none`.

## The oracle has to come from outside the tree

The tree holds no datasets, no JCL, no reports and no archived outputs (analysis field `data_hubs` is empty, and `01-inventory.md` lists no dataset). So the oracle has to come from job output, logs and reports the client holds. Ask the client to supply:

1. The values `PROGA` read at its `ACCEPT` (`app/cbl/PROGA.cbl:8`) over at least 12 months, covering month-end, quarter-end and fiscal year-end.
2. The job logs, return codes and SYSOUT for every run that started `PROGA`. Also SMF records showing which programs it called. These double as the telemetry the dead-code register lacks.
3. The nightly batch cycle: job names, order, the files each job reads and writes, and archived GDG generations of those files.
4. Output the called programs sent to partners or reports, since what left the building is already an executable specification.

## Oracle per wave

| Wave | Oracle, strongest available first | Confidence | Evidence |
|---|---|---|---|
| 1 (PROGA, PROGB) | Captured production input replay: the recorded `ACCEPT` values fed to the port, with the called programs' output diffed. Fallback: golden master from archived reports and job output. Last resort: characterization tests from source, labeled provisional. | low | `app/cbl/PROGA.cbl:8`, `app/cbl/PROGA.cbl:9`. The choice among the three is inference, since none of the data is in the tree. |

Parallel run is worth asking about first. `PROGA` is small and stateless in the tree, so running the old and new side by side on the same input is cheap if the old system stays up. Inference.

## Normalization spec

Keep it short and have a human sign it off.

| Item | Rule | Evidence |
|---|---|---|
| Timestamps, run ids, sequence and page numbers | Mask in both outputs. | inference |
| Trailing spaces in the program name | `WS-PGM-NAME` is `PIC X(8)`, so a short name is padded with spaces. Compare after trimming only if the legacy call also ignores the padding. | `app/cbl/PROGA.cbl:5` |
| Monetary fields in called programs | Decimal type, zero tolerance. None appears in the two programs, but the callees may use packed decimal. | inference |
| Record order and collating sequence | Not applicable to the two programs. The callees' sort order has to be confirmed once they are known. | inference |
| Job order | The graph holds no temporal edge, so no order can be taken from it. The nightly cycle's order must come from the client. | analysis field `edge_counts` |

## Boundary cases to add

- Empty input: a blank or zero-length name given to `CALL` (`app/cbl/PROGA.cbl:8`).
- A name longer than 8 characters, or in lower case.
- A name that matches no program. `CALL` has no `ON EXCEPTION`, so the legacy behavior is the runtime's own error path (`app/cbl/PROGA.cbl:9`). Reproduce it, or change it on purpose and log it below.
- A name that matches `PROGB`, which returns at once (`app/cbl/PROGB.cbl:4`).
- Any name that only appears at fiscal close. This is the path most often lost in a cutover (inference: the names in the input are not visible in the tree).

## Deviation register

Nothing may differ without a row here. One row is open now.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| D-001 | A name that matches no program makes the `CALL` fail in the runtime's own way, since nothing handles the failure | To be decided: reject names not in the registry, with a logged reason | Registry facade for wave 1 (`03-waves.md`) | not yet approved | Unknown until the callee set and the batch cycle are known | `app/cbl/PROGA.cbl:9`. Inference on the runtime behavior. |

## Exit bar for wave 1

- Replay diff is clean, modulo the normalization spec and the deviation register.
- Every boundary case above passes.
- The harness is under version control and runs in CI.
- The deviation register is signed by someone with authority to sign it.

Keep the harness after cutover. It is the regression suite for the modernized system and the only executable specification of what `PROGA` dispatched to.
