# 06 Test strategy

The bar: for the inputs this system actually sees, the new code produces the same outputs as the old, and every difference was decided on purpose and written down.

The tree holds no dataset, no JCL, no CSD and no test (`01-inventory.md`). The four programs read and write no file (`app/cbl/PROGA.cbl:1-26`). So the oracle cannot come from data files. It has to come from CICS transaction traffic, job output, logs and reports the client holds. The nightly batch cycle, which must not break, has no unit in this tree, so its oracle is described only as a request to the client (below).

## Oracle, per boundary

There are no waves (`03-waves.md`). The first candidate boundary is the PROGA hub and the three programs it calls.

| Boundary | Oracle, strongest first | What to ask the client for | Confidence | Evidence |
|---|---|---|---|---|
| PROGA and its callees (the online chain) | 1. Parallel run: the old and new region both receive the same transaction input, and the outputs are diffed. 2. Captured traffic replay: COMMAREA in, task outcome out, over a window that includes month-end and year-end. 3. Characterization tests from the source, provisional only. | CICS journals or transaction logs for the transactions that start PROGA. CICS monitoring or SMF 110 records showing which programs ran. Any archived screen or report the transaction produced. Whether a second region can take a copy of the traffic. | low | inference |
| The nightly batch cycle | 1. Parallel run of the cycle. 2. Archived GDG generations of every report, extract and posting file, each a dated golden master. 3. Job logs and return codes per step. | JCL and PROCs for the cycle, the scheduler export, the GDG bases with their generations, job logs for at least one month-end and one year-end, and the extract files that go to partners. | low | inference |

Do not settle for characterization tests until parallel run and captured replay have been asked about and refused.

## What the harness has to record at PROGA

PROGA's behavior depends on a value it does not choose: the COMMAREA program name moved at `app/cbl/PROGA.cbl:15` and used at `app/cbl/PROGA.cbl:16`. So the harness records, for every replayed task:

- the COMMAREA content and its length on entry to PROGA
- the sequence of programs called, with LINK or XCTL, and where control ended
- the task outcome, including any abend code

The recorded COMMAREA names are also the bound the computed call is missing, so the same capture feeds the dead-code register (`05-dead-code.md`).

## Normalization spec

Every entry below asserts that a difference does not matter. A human signs each one.

| Item | Normalize? | Why | Evidence |
|---|---|---|---|
| Task numbers, timestamps, terminal ids, region names | Yes | Change on every run. | inference |
| Trailing spaces in the 8 byte program name in the COMMAREA | Decide in writing | The field is PIC X(8), so a short name is space padded. A port that trims or does not trim can change which program is found. | `app/cbl/PROGA.cbl:7` |
| Case of the program name | No | A lower case name is a different program in some regions. Test both. | inference |
| EBCDIC to ASCII conversion of names and content | No | The name has to survive the conversion exactly. | inference |
| Order of programs called | No | Order is the behavior: LINK returns, XCTL does not. | `app/cbl/PROGA.cbl:12`, `app/cbl/PROGA.cbl:16`, `app/cbl/PROGA.cbl:20` |
| Abend codes | No | A failed LINK or XCTL ends the task abnormally by default (inference). The code is part of the outcome. | `app/cbl/PROGA.cbl:16` |

Not applicable here, and stated so nobody looks for them: packed decimal and COMP fields (none in the four programs), REDEFINES (none), collating order (no sorted or keyed file), record padding and low values (no record). If the real system turns out larger, revisit each.

## Cases to add beyond replay

- **COMMAREA names a program that exists**, one for each program the client says is valid.
- **COMMAREA names itself** (PROGA). It would link to itself.
- **COMMAREA names a program that does not exist.** The legacy behavior is an abnormal end of the task by default (inference). Capture it, and decide whether the new code should match.
- **No COMMAREA, or a COMMAREA shorter than 8 bytes.** PROGA does not check the length before the MOVE (`app/cbl/PROGA.cbl:15`). What the old code does with that is behavior, so capture it.
- **The XCTL to PROGC** is the last thing PROGA does on its normal path (`app/cbl/PROGA.cbl:20`). Assert that control does not come back and that nothing after it runs.
- **PROGD is not called** on the normal path. Assert it. If the new code runs PROGD, that is the difference to catch (`app/cbl/PROGA.cbl:23`).
- **The XCTL fails.** Force PROGC to be missing in the old region and record what happens. This is the only way the statement at line 23 could run.
- **Boundary dates**: month-end, quarter-end, fiscal year-end, leap day and daylight saving changes, for whatever transactions start PROGA. The tree gives no date logic, so this is cover for the callers.
- **The paths that run only at fiscal close.** Ask the client which COMMAREA names show up only then. A name seen once a year is the dead-code mistake in the making.

## Deviation Register

Nothing may differ without a row here. The rows below are candidates raised by this assessment. None is approved.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| D-1 | XCTL never returns, so the RETURN and the XCTL to PROGD after it do not run. | Not decided. A plain call in the port would run them. | Not changed yet. This row exists so the port does not change it by accident. | Not approved | PROGD could be called when it never was. | `app/cbl/PROGA.cbl:20`, `app/cbl/PROGA.cbl:23`, `app/cbl/PROGA.cbl:26` |
| D-2 | The LINK target comes from the COMMAREA with no check of length or content. | Not decided. A router with an allow list would refuse names the old code accepts. | Not changed yet. | Not approved | A caller passing an unlisted name would be refused where the old code linked to it. | `app/cbl/PROGA.cbl:15`, `app/cbl/PROGA.cbl:16` |

## Exit bar, per wave

No wave exists, so this is the bar the first wave has to meet:

- replay diff is clean, modulo the normalization spec and the Deviation Register
- every case above passes
- the harness is under version control and runs in CI
- the Deviation Register is signed by someone with the authority to sign it

Not when the port compiles, and not when it passes tests written alongside the port.

## Keep the harness after cutover

The comparison harness becomes the regression suite for the modernized system. Budget to maintain it.
