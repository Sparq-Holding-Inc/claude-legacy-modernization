# 04 Estimate

This is an estimate by method, per wave. It is inference throughout. Effort is in person-days for a
small team that can read COBOL and JCL, with a target runtime and a decimal type already chosen. The
estimate is driven by the edges crossing each wave boundary, not by lines of code. The tree is 32
lines of COBOL and 9 lines of JCL (`app/cbl/PGMR.cbl:16`, `app/cbl/PGMW.cbl:16`,
`app/jcl/READJOB.jcl:4`, `app/jcl/WRITEJOB.jcl:5`). Line count would say a day. The coupling says
otherwise.

## Range per wave

| Wave | Range (person-days) | Driver | Confidence | Evidence |
|---|---|---|---|---|
| 1. Reader side | 3 to 8 | Toolchain proof, reading a packed decimal record in the target, a harness that decodes the dataset. Two units. | low | `app/cbl/PGMR.cbl:13`, `app/cpy/LAYOUTX.cpy:3` |
| 2. Writer of the master file | 4 to 10 | One contract edge and one data hub to prove equal byte for byte, and no oracle in the tree. Two units. | low | `app/cbl/PGMW.cbl:14`, `app/jcl/WRITEJOB.jcl:4` |
| Test harness and oracle capture (shared) | 3 to 8 | Getting archived outputs, job logs and a scheduler export from the client. Mostly waiting. | low | inference |
| Total | 10 to 26 | | low | inference |

Do not read the total as a commitment. This tree is a fragment. It has no CICS, no scheduler, no
data and no tests. It may be all of the system or one corner of a large one. The range assumes it is
the whole system.

## Assumptions the range is most sensitive to

1. Assumes PGMR is the only reader of SPARQ.TEST.MASTER. If other programs outside this tree read it,
   wave 2 roughly doubles, because each reader is another consumer of the layout to prove equal
   (`analysis` field `data_hubs` counts one reader, in this tree only).
2. Assumes the 15 byte copybook record and the LRECL=80 in the JCL can be reconciled by a decision, for
   example that the runtime pads to 80. If real files hold 15 byte records that other tools read, or 80
   byte records with a used filler that the copybook does not describe, wave 1 and wave 2 each add 2 to
   4 days to find and fix the disagreement (`app/cpy/LAYOUTX.cpy:3`, `app/jcl/WRITEJOB.jcl:4`).
3. Assumes an archived copy of SPARQ.TEST.MASTER, or a job log of a WRITEJOB run, can be had. If not,
   the oracle is characterization from source, which is provisional, and PGMW's unset record
   (`app/cbl/PGMW.cbl:14`) cannot be settled from the source. Add 3 to 5 days and mark wave 2 provisional.

## What moves the estimate here

In rough order of weight, for this tree:

- Coupling edges crossing the wave boundary: one contract edge, one data hub, zero calls.
- Behavioral oracle: none in the tree.
- God modules: none. Fan-in is zero (`analysis` field `god_modules`).
- Business logic in a database: none seen. No DB2 in the tree.
- Team skill: unknown. Ask whether anyone at the client can read the source.

## Where Claude Code can do the mechanical port, and where it cannot

| Part | Claude Code | Confidence | Evidence |
|---|---|---|---|
| Transliterating PGMR and PGMW into the target language | Strong, given a test harness. Each is one open, one read or write, one close. | high | `app/cbl/PGMR.cbl:13`, `app/cbl/PGMW.cbl:13` |
| Packed decimal encode and decode of `S9(7)V99 COMP-3` in a decimal type | Strong, and checkable by unit test against known byte strings. | high | `app/cpy/LAYOUTX.cpy:3` |
| Rewriting the two JCL jobs into the target scheduler | Strong for the step and the DD. The DISP and DCB semantics need a human decision. | medium | `app/jcl/WRITEJOB.jcl:3` |
| Deciding what PGMW should write when it moves no data into the record | Cannot. It needs an archived output or an owner who knows the intent. | low | `app/cbl/PGMW.cbl:14` |
| Deciding whether LRECL=80 or the 15 byte layout is the truth | Cannot. It needs the catalog entry for the dataset. | low | `app/jcl/WRITEJOB.jcl:4` |
| Finding the nightly order and other readers of the dataset | Cannot. It is not in the tree. | low | `analysis` field `warnings` |
