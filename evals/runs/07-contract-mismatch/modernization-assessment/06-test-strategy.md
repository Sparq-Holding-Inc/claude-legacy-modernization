# 06 Test strategy

"Correct" for this system means: for the inputs the nightly batch cycle sees, the new `READJOB` and `WRITEJOB` leave `SPARQ.TEST.MASTER` and every other output the same, byte for byte, except where a signed row in the Deviation Register says otherwise.

The tree holds one dataset, no archived outputs, no job logs, and no expected-result files (`modernization-assessment/01-inventory.md`). The oracle must therefore come from the client. Nothing in the tree supplies it.

## Oracle per wave

| Wave | Preferred oracle | Fallback | What to ask the client for | Evidence |
|---|---|---|---|---|
| 1 (PGMR, READJOB) | Captured production input: real generations of `SPARQ.TEST.MASTER`, with the reader's output (return code and `SYSOUT`) for each | Golden master from archived copies of the file | Several nights of the file as written by `WRITEJOB`, and the `READJOB` log for each night | `app/jcl/READJOB.jcl:3`, `app/jcl/READJOB.jcl:4` |
| 2 (PGMW, WRITEJOB) | Parallel run: legacy and new `WRITEJOB` on the same inputs, outputs compared byte for byte | Golden master from archived generations of the file | Archived copies of `SPARQ.TEST.MASTER` across a month end, and how the dataset is cleared before each run | `app/jcl/WRITEJOB.jcl:3` |

Characterization tests from source are **not** acceptable as the only oracle for wave 2. PGMW writes `LAYOUT-REC` without moving a value into it (`app/cbl/PGMW.cbl:14`), so source-derived expectations would encode undefined bytes. Label any such test provisional.

## Normalization spec (to be signed by a human)

Keep it short. Each line says a difference does not matter and can hide a bug.

| Item | Proposed rule | Risk if wrong | Evidence |
|---|---|---|---|
| Packed decimal `LR-AMT` / `LY-VALUE` | Compare as decimal, tolerance **zero**. Never as float. Compare the raw bytes first, including the sign nibble | A float port rounds money. A sign nibble difference (`C` against `F`) looks the same as a number but is a different byte | `app/cpy/LAYOUTX.cpy:3`, `app/cpy/LAYOUTY.cpy:3` |
| Record length | Compare all 80 bytes of each record, not only the 15 byte layout | Another consumer reading the padding would see a change | `app/jcl/WRITEJOB.jcl:4` |
| Padding after byte 15 | Do not normalise until the client says what it holds (spaces, low values, or garbage) | The padding is part of the file today | inference |
| Record order | Treat order as significant. It is a sequential file | A reader may depend on the order | `app/cbl/PGMR.cbl:7` |
| Dataset catalog attributes | Compare record format, record length and block size from the catalog. Do not normalise | The reader DD has no DCB and takes its attributes from the catalog entry | `app/jcl/READJOB.jcl:3` |
| Timestamps, run IDs | None are in the tree. Do not add a rule until a real file shows one | | inference |

## Input space to cover on purpose

- **Empty file.** A `WRITEJOB` run that writes zero records. PGMW as written writes exactly one (`app/cbl/PGMW.cbl:14`), so ask whether the real job ever writes more or fewer.
- **Rerun after a failure.** `DISP=(NEW,CATLG,DELETE)` fails when the dataset exists (`app/jcl/WRITEJOB.jcl:3`). Test what the cycle does on a rerun, and make the new job behave the same.
- **Reader before writer.** If `READJOB` runs before `WRITEJOB` in a night, it reads the previous night's file or fails allocation. The legacy behavior must be reproduced, or recorded as a deviation. inference
- **Month end and fiscal year end.** The tree does not say what the cycle does at those points. Ask.
- **The uninitialised record.** One case where the new `WRITEJOB` output is compared with an archived real file. If the archived `LR-AMT` bytes are not valid packed decimal, record it as a finding and decide in the Deviation Register whether to reproduce or fix it.

## Job order the harness must keep

| Before | After | Why | Confidence | Evidence |
|---|---|---|---|---|
| `job:WRITEJOB` | `job:READJOB` | READJOB reads the dataset WRITEJOB creates | medium. Deduced from the data edge, no scheduler edge exists | `app/jcl/WRITEJOB.jcl:3`, `app/jcl/READJOB.jcl:3` |

## Deviation Register

Empty at the start. Nothing is allowed to differ without a row here.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| DR-1 (open) | PGMW writes a record whose fields are never set | To be decided: reproduce, or initialise | Decision needed before wave 2 | not yet | Any consumer that validates `LR-AMT` | `app/cbl/PGMW.cbl:14` |
| DR-2 (open) | `LAYOUTX` and `LAYOUTY` both describe the record under different names | One shared definition | Prevents silent drift | not yet | Wave 2 | `app/cpy/LAYOUTX.cpy:1`, `app/cpy/LAYOUTY.cpy:1` |

## Exit bar

A wave is done when:

- the replay diff is clean, modulo the normalization spec and the register;
- the boundary cases above pass;
- the harness is in version control and runs in CI;
- the register is signed by someone who can sign it.

Keep the harness after cutover as the regression suite.
