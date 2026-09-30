# 06 Test strategy

Wave 1 is the only wave: `job:WRITEJOB`, `PGMW`, `job:READJOB`, `PGMR`. "Correct" means: for the
inputs this system really sees, the new pair produces the same bytes in `SPARQ.TEST.MASTER` and the
same step results as the old pair. Every difference is either covered by the normalization spec
below or written in the deviation register on purpose.

## The oracle

The tree names one dataset (`app/jcl/WRITEJOB.jcl:3`) but holds no data. There is no sample file, no
archived output, no report, no job log and no test. So no oracle exists in the tree. It has to come
from the client.

Chosen oracle for wave 1, strongest first:

1. **Parallel run.** Both jobs are tiny and `PGMW` takes no input file (`app/cbl/PGMW.cbl:6`,
   `app/cbl/PGMW.cbl:13`). Running the old and new writer side by side is cheap. Ask first whether it
   is possible. Teams assume it is not, and are often wrong.
2. **Golden master from archived outputs.** If a parallel run is not possible, use archived copies of
   `SPARQ.TEST.MASTER` from each night's run, if any were kept.
3. **Characterization tests from the source.** Last resort. It encodes what the code says, not what
   it does, so any coverage from it is provisional. Nothing more is available today.

### What to ask the client to supply

| Ask | Why | Evidence |
|---|---|---|
| Copies of `SPARQ.TEST.MASTER` after each run, over a full business cycle including month end and year end | Each copy is a golden master with a date on it | `app/jcl/WRITEJOB.jcl:3` |
| The catalog entry for the dataset (record format, record length, block size) | The DD says `LRECL=80` and the layouts are 15 bytes. The real length decides the compare | `app/jcl/WRITEJOB.jcl:4`, `app/cpy/LAYOUTX.cpy:3` |
| Job logs or SMF records for `WRITEJOB` and `READJOB`, 12 months | Return codes and run order. They double as telemetry for `05-dead-code.md` | inference: no logs in the tree |
| The scheduler export | The only source of the order these two jobs run in | `app/jcl/READJOB.jcl:3` |
| The `SYSOUT` from both jobs | Both jobs allocate one. Neither program writes to it in source, so any content came from the runtime | `app/jcl/WRITEJOB.jcl:5`, `app/jcl/READJOB.jcl:4` |
| Any other job, partner extract or utility that reads the file | Each is another reader of the same 15 bytes | inference: the extractor reads only what is in the tree |

## Normalization spec

Every line below is a claim that a difference does not matter. Each is a place a real bug can hide.
A human signs the list before the first diff is trusted.

| Item | Rule | Evidence |
|---|---|---|
| Amount field `LR-AMT` | Compare as a decimal value with zero tolerance. Use a decimal type in the target. Never a float. Also compare the raw bytes, because a valid packed number has more than one sign nibble | `app/cpy/LAYOUTX.cpy:3` |
| Key field `LR-KEY` | Compare byte for byte. Decide whether trailing blanks and low values count as the same | `app/cpy/LAYOUTX.cpy:2` |
| Record length and padding | The DD says 80, the record is 15. Decide which bytes past 15 are compared, once the real catalog entry is known | `app/jcl/WRITEJOB.jcl:4` |
| Record order | One record is written, so order is not visible today. Assume it matters until the client says otherwise | `app/cbl/PGMW.cbl:14` |
| Timestamps and run ids | None appear in the record. If the real file adds them, list them here | `app/cpy/LAYOUTX.cpy:2-3` |
| Collating sequence | The file is sequential, not a keyed VSAM file, so no key order is read back. Treat any sort in the new system as a difference to review | `app/cbl/PGMR.cbl:7` |
| Job order | `WRITEJOB` before `READJOB`. This is the one order the harness must keep, and it is not in any scheduler artifact we have | `app/jcl/WRITEJOB.jcl:3`, `app/jcl/READJOB.jcl:3` |

## Cover the input space on purpose

Replay covers the common night well. These are the cases replay will miss.

| Case | What to check | Evidence |
|---|---|---|
| Amount at its limits: 9999999.99, 0, negative, negative zero | The packed field holds nine digits and a sign. Boundary values are where a rounding or a sign rule differs | `app/cpy/LAYOUTX.cpy:3` |
| A record that holds invalid packed data | `PGMW` fills no field, so the file may already hold bytes that are not valid packed decimal (inference). `PGMR` never unpacks the amount, so the legacy read does not care. A port that unpacks it may fail where the old one did not | `app/cbl/PGMW.cbl:14`, `app/cbl/PGMR.cbl:14` |
| An empty dataset | `PGMR` has no end of file handling, so the legacy step may end abnormally (inference). The new step must do the same or the difference goes in the register | `app/cbl/PGMR.cbl:14` |
| A dataset that already exists when `WRITEJOB` starts | `DISP=(NEW,...)` on an existing name fails in the job step allocation (inference). Find out what deletes the old dataset each night | `app/jcl/WRITEJOB.jcl:3` |
| `READJOB` run before `WRITEJOB` | Expected result is a loud failure on a missing dataset (inference). The new scheduler must not reorder them | `app/jcl/READJOB.jcl:3` |
| Month end, quarter end, year end, leap day | Nothing in the two programs reads a date. Still capture across those nights, because the data written may vary with them | inference: the writer's source of data is unknown |
| Layout drift test | Change one copybook in a copy of the tree and confirm the harness fails. That proves the check works | `app/cpy/LAYOUTX.cpy:2`, `app/cpy/LAYOUTY.cpy:2` |

## Mainframe traps that apply here

- **Packed decimal.** `LR-AMT` and `LY-VALUE` are `S9(7)V99 COMP-3` (`app/cpy/LAYOUTX.cpy:3`,
  `app/cpy/LAYOUTY.cpy:3`). Zero tolerance on the value. Both `C` and `F` are valid positive sign
  nibbles, so compare the bytes as well as the number.
- **`REDEFINES`.** There is none in either copybook. Nothing to test.
- **Record padding.** The `LRECL=80` against a 15 byte record is the item to settle first.
- **Job order.** The temporal edge the harness must keep is not in `graph.json`, because no scheduler
  was parsed. Take it from the scheduler export when it arrives.

## Deviation register

Nothing is approved. The register starts empty and nothing may differ without a row in it.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact |
|---|---|---|---|---|---|
| none yet | | | | | |

### Candidates to raise with the client

These are the behaviors most likely to need a row. They are for the client's engineers to decide.

| ID | Candidate | Evidence |
|---|---|---|
| C1 | The legacy writer writes a record without setting any field. The new writer should write defined values. That is a change on purpose and needs a signature | `app/cbl/PGMW.cbl:14` |
| C2 | One shared copybook replaces two. Names change from `LR-`/`LY-` to one set. The bytes must not change | `app/cpy/LAYOUTX.cpy:2-3`, `app/cpy/LAYOUTY.cpy:2-3` |
| C3 | The reader gains end of file and file status handling. The legacy reader has none | `app/cbl/PGMR.cbl:14` |

## Exit bar for wave 1

Wave 1 is done when all four hold. Not when the port compiles.

- The replay or parallel diff is clean, apart from the normalization spec and the deviation register.
- Every case in the table above passes.
- The harness is under version control and runs in CI.
- The deviation register is signed by someone with the authority to sign it.

After cutover, keep the harness. It becomes the regression suite for the new pair, and it is the
only executable statement of what `SPARQ.TEST.MASTER` holds.
