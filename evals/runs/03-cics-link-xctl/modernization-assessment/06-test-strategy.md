# 06 Test strategy

A ported PROGA, PROGB, PROGC or PROGD is correct when, for the inputs the system really sees, it invokes
the same programs in the same order, ends the same way, and leaves the same COMMAREA behind. Where it
differs, someone decided that and wrote it down.

The stated must-not-break item is the nightly batch cycle. The tree holds no batch program, JCL, scheduler
definition or dataset, so no oracle for that cycle can be defined from it. The strategy below covers the
CICS wave. The batch cycle needs the artifacts listed at the end.

## What the wave produces, so what to compare

The four programs write no dataset (`app/cbl/PROGA.cbl:1-26`). Their output is control flow:

- which program is entered, in what order, through LINK or XCTL
- the COMMAREA each callee receives, if any
- the ending condition: a normal RETURN, or an abend and its code

The comparison is a trace, not a file diff.

## The oracle per wave

Wave 1 has no archived output to use as a golden master. In order of strength:

| Oracle | Available? | Use | Confidence | Evidence |
|---|---|---|---|---|
| Parallel run: legacy and new receive the same COMMAREA, and the two traces are diffed | Unknown. Ask whether legacy PROGA can stay up beside the port | Preferred | low | inference |
| Replay of captured COMMAREA traffic from CICS journals, transaction logs or auxiliary trace | Unknown. Ask | Second choice. The capture window must cover month end and year end, in case a name is used only then | low | inference |
| Golden master from archived output | None found. These programs write none | Not applicable | high | `app/cbl/PROGA.cbl:1-26` |
| Characterization tests generated from this source | Available now | Last resort. Label all coverage provisional | high | `app/cbl/PROGA.cbl:12-26` |

If the client supplies none of the first two, the harness starts from the characterization cases below.

## Normalization spec

Every line is a claim that a difference does not matter. Keep it short. A human signs it off.

- task numbers, timestamps and trace sequence numbers
- storage addresses in dumps
- trailing spaces in the 8 byte program name. It is a fixed width field padded with spaces
  (`app/cbl/PROGA.cbl:7`, `app/cbl/PROGA.cbl:9`). Do not normalize a name that differs in content.

Nothing else. In particular do not normalize call order, and do not normalize the abend code.

## Mainframe traps that apply to these programs

- **Fixed width names and padding.** The COMMAREA is `PIC X(8)` (`app/cbl/PROGA.cbl:9`). A name shorter than
  eight characters is space padded. Low values in the field are not a blank. Decide whether they must behave
  the same, and write it down.
- **Character set.** A name reaches the LINK as EBCDIC bytes. A port on ASCII or Unicode may change case
  handling or padding. Test lower case names, because CICS program names are upper case.
- **XCTL does not return.** Lines 23 to 26 run only if the XCTL at line 20 fails and the failure is handled.
  The source has no handler (`app/cbl/PROGA.cbl:20-26`, inference). A port that treats XCTL as a call would
  run them. The harness must assert that control does not return.
- **No COMMAREA on XCTL.** The two XCTL commands pass none (`app/cbl/PROGA.cbl:20-25`). The callee sees an
  empty COMMAREA. A port that forwards one changes behavior.
- **No `RESP`.** No command has a `RESP` option (`app/cbl/PROGA.cbl:12-25`). A missing program most
  likely abends the task. The port must abend the same way, not return an error code.
- **Packed decimal, collating sequence, REDEFINES, job order.** Not present in this tree. They apply to the
  batch cycle once its source arrives.

## Targeted cases

These come from the source. They cover the dangerous paths that replay covers badly.

| Case | Input | Expected legacy behavior to capture | Confidence | Evidence |
|---|---|---|---|---|
| No COMMAREA | EIBCALEN of zero | The MOVE reads a field that has no data area. Likely an abend. Capture the code | low | inference, `app/cbl/PROGA.cbl:9`, `app/cbl/PROGA.cbl:15` |
| Name is PROGB, PROGC or PROGD | COMMAREA holds that name | LINK runs it and returns. Then the XCTL to PROGC runs | medium | `app/cbl/PROGA.cbl:15-20` |
| Name is PROGA | COMMAREA holds `PROGA` | PROGA calls itself. Capture nesting and any limit hit | low | inference |
| Name not defined in the region | COMMAREA holds a name that does not exist | PGMIDERR with no handler. Likely an abend | medium | inference, `app/cbl/PROGA.cbl:16-18` |
| Name is spaces or low values | COMMAREA blank | Same as above. Capture the exact code | low | inference |
| Normal path | A valid name | Sequence: PROGB, the LINK target, then PROGC, with no return to PROGA | high | `app/cbl/PROGA.cbl:12-22` |
| Failed XCTL | PROGC not installed | Does control reach line 23, or does the task abend? This decides whether PROGD is ever entered | low | inference, `app/cbl/PROGA.cbl:20-23` |

Boundary dates, empty and enormous batches, and fiscal close paths do not apply to these four programs.
None has date logic or file I/O. They apply in full to the batch cycle.

## Deviation Register

Nothing may differ without a row here. No deviation is recorded yet. The port has not started.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact |
|---|---|---|---|---|---|
| none yet | | | | | |

## Exit bar for wave 1

- The trace diff is clean, modulo the normalization spec and the deviation register.
- Every targeted case above passes, or its difference is in the register.
- The harness is under version control and runs in CI.
- The register is signed by someone with authority to sign it.

Not when the port compiles, and not when it passes tests written alongside the port.

## Keep the harness after cutover

The trace comparison becomes the regression suite for the modernized routing chain. Budget to maintain it.

## What to ask the client to supply for the nightly batch cycle

The batch cycle has no oracle in this tree. To define one, ask for:

- the JCL, procs and scheduler definitions for the cycle, so the temporal edges can be extracted
- the source of every batch program in the cycle, and the copybooks and record layouts it uses
- GDG generations of every report, extract and posting file for at least 12 months, including month end and
  fiscal year end. Each is a dated golden master
- job logs and SMF records that show which programs ran, with return codes and run times. They double as
  telemetry for the dead-code register
- files sent to partners and the regulatory and statement archives
- the way CICS and batch share data: VSAM files, DB2 tables, queues or EXCI calls. Without this, the tree
  cannot show whether these four programs touch the batch cycle at all
