# 06 Test strategy

Skill: `behavioral-equivalence`. The bar is that, for the inputs this system actually sees, the new
implementation makes the same calls in the same order and returns the same results as the old one. Any
difference is decided and written down.

## What the tree gives me as an oracle

Nothing. The tree holds four COBOL programs and no dataset, no JCL, no archived output, no job log and no
CICS journal (analysis: `meta.files_seen`, `node_counts`). So the oracle must come from the client. The
observable behavior of wave 1 is small: for a given COMMAREA, which programs get control, in what order,
and how the task ends.

## Oracle for wave 1, strongest first

| Rank | Oracle | What to ask the client for | Provisional? | Evidence |
|---|---|---|---|---|
| 1 | Parallel run | Can the old and new PROGA run side by side on the same inputs in a test region, with the program invocation sequence compared? | no | inference |
| 2 | Captured traffic replay | CICS journals or transaction logs holding the COMMAREA values and the resulting program sequence, over a window that includes month-end and fiscal year-end. | no | `app/cbl/PROGA.cbl:15`, `app/cbl/PROGA.cbl:16` |
| 3 | Golden master from archived outputs | Whatever the four programs cause to be written. None is visible: they hold no file, map or query. Ask whether their callers produce reports or extracts that depend on them. | no | inference |
| 4 | Characterization from source | Available now. It pins the order the code states: LINK PROGB, LINK the COMMAREA target, XCTL PROGC. It encodes what the code says, not what it does in production. | yes | `app/cbl/PROGA.cbl:12`, `app/cbl/PROGA.cbl:16`, `app/cbl/PROGA.cbl:20` |

Until the client supplies rank 1 to 3, all coverage here is provisional.

## The must-not-break item: the nightly batch cycle

There is no oracle for it in the tree, because there is nothing of it in the tree. No JCL, no scheduler
definition, no batch program (analysis: `meta.files_seen`). This is a gap in what I was given. It is not
a finding that the cycle is unaffected. Ask the client for:

- the JCL, PROCs and scheduler definitions of the nightly cycle, so the extractor can build the temporal
  edges, which today number none (analysis: `edge_counts`);
- archived generations of the cycle's outputs (GDG datasets, reports, partner extracts): each one is a
  golden master with a date on it;
- job logs and SMF records: return codes, run order and elapsed time per step;
- a statement of whether any batch step starts these four programs, for example through an external CICS
  interface, or writes the COMMAREA values that PROGA reads (inference).

## Cases to run for wave 1

Each case asserts the sequence of programs that receive control and the end state.

| Case | Input | Expected legacy behavior | Confidence | Evidence |
|---|---|---|---|---|
| Baseline | COMMAREA holds PROGB | PROGB, then PROGB again, then PROGC. PROGD is not run. | medium | `app/cbl/PROGA.cbl:12`, `app/cbl/PROGA.cbl:16`, `app/cbl/PROGA.cbl:20` |
| Target is PROGC | COMMAREA holds PROGC | PROGB, PROGC returns to PROGA, then PROGC by XCTL. | medium | `app/cbl/PROGA.cbl:16`, `app/cbl/PROGA.cbl:20` |
| Target is PROGD | COMMAREA holds PROGD | PROGB, PROGD returns, then PROGC by XCTL. PROGD runs only through the LINK. | medium | `app/cbl/PROGA.cbl:16`, `app/cbl/PROGA.cbl:20` |
| Name not installed | COMMAREA holds a name that does not exist | PGMIDERR at the LINK. With no RESP or HANDLE CONDITION the task abends. The port must abend the same way. | medium | inference: `app/cbl/PROGA.cbl:16` |
| Blank or short COMMAREA | No COMMAREA, or fewer than 8 bytes | PROGA reads DFHCOMMAREA with no EIBCALEN test. The result is whatever the region does. Capture it, do not guess. | low | inference: `app/cbl/PROGA.cbl:9`, `app/cbl/PROGA.cbl:15` |
| Lowercase or padded name | A name with lowercase letters or trailing spaces | Moved as 8 bytes unchanged. Confirm how the region matches it. | low | inference: `app/cbl/PROGA.cbl:7`, `app/cbl/PROGA.cbl:15` |
| Transfer does not return | Any input | After XCTL to PROGC, lines 23 to 26 do not run. The port must not add a return path to PROGA. | medium | inference: `app/cbl/PROGA.cbl:20`, `app/cbl/PROGA.cbl:23-26` |
| Fiscal close paths | Inputs that appear only at month-end or year-end | Unknown. The source shows no date logic. Replay a window that includes close. | low | inference |

## Normalization spec

Keep it short and have a human sign off on each line. None of these programs holds a date, a number, a
record or a sort, so the mainframe traps (packed decimal, EBCDIC collating sequence, REDEFINES, record
padding) do not apply to them, and no field needs a tolerance (analysis: `edge_counts`,
`data_hubs`). What remains:

- ignore CICS task numbers, timestamps and terminal ids in any trace;
- compare the program sequence exactly, with no reordering allowed;
- compare abend codes exactly.

The traps apply as soon as the nightly batch cycle is in scope. Its normalization spec must be written
then, and the temporal edges from its scheduler are the list of orders the harness must keep.

## Deviation Register

Nothing gets to differ without a row here. One candidate exists now, pending a decision by the client.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| D-1 (pending) | Lines 23 to 26 are unreachable: XCTL to PROGD and a RETURN follow an XCTL that never returns. | Undecided: drop them, or keep them as written. | They add a call edge to PROGD that never fires. | not yet approved | Dropping them removes the only static caller of PROGD. Decide after PROGD's real callers are known. | inference: `app/cbl/PROGA.cbl:20`, `app/cbl/PROGA.cbl:23-26` |

## Exit bar for wave 1

The wave is done when all of these hold:

- replay diff is clean, modulo the normalization spec and the register;
- every case above passes, and the two low confidence cases have a captured legacy result, not a guess;
- the harness is under version control and runs in CI;
- the register is signed by someone with the authority to sign it;
- the callers of PROGA and the set of names in its COMMAREA are known, so the LINK at line 16 is bounded
  (`app/cbl/PROGA.cbl:16`).

A port that compiles is not done, and neither is one that passes tests written beside it.

## After cutover

Keep the harness. It becomes the regression suite for the modernized system, and the only executable
specification this tree has.
