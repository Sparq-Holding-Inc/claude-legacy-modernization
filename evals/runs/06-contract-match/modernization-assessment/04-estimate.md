# 04 Estimate

Every number here is inference. No port velocity was measured, and no telemetry or oracle exists yet.
The ranges are engineer-days for one engineer who reads COBOL and JCL, and they include the harness for
the wave. They are not a quote. The size of the system is 32 lines of COBOL, 3 lines of copybook and 9
lines of JCL (`app/cbl/PGMR.cbl:16`, `app/cbl/PGMW.cbl:16`, `app/cpy/LAYOUTX.cpy:3`). The port is small.
The evidence that it is correct is the work.

## Method

The estimate is not built from line counts. It is built from what the skill weighs, in order:

| Driver | What this tree shows | Effect on the range | Evidence |
|---|---|---|---|
| Coupling edges crossing the wave boundary | One contract edge, PGMW to PGMR, on one dataset | Sets the harness. One boundary file to compare | `app/cbl/PGMW.cbl:11`, `app/cbl/PGMR.cbl:11` |
| Behavioral oracle | None in the tree. The dataset name is here, its contents are not | The largest swing. See assumption 3 | inference |
| God modules in the wave | None | No facade work | analysis, field `god_modules` |
| Logic in the database | No DB2 node exists in the graph | None | analysis, field `node_counts` |
| Someone who reads the source language | Unknown | Assumed yes. If not, add the time to learn it | inference |

## Ranges per wave

| Wave | Range (engineer-days) | What is in it | Evidence |
|---|---|---|---|
| 1. Reader job | 3 to 6 | Port PGMR and the READJOB step, build the LAYOUTX decoder, prove the new reader opens and reads the legacy file | `app/cbl/PGMR.cbl:13` |
| 2. Writer job | 4 to 8 | Port PGMW and the WRITEJOB allocation, golden master compare of the output file, decide the uninitialized record and LRECL questions | `app/cbl/PGMW.cbl:14`, `app/jcl/WRITEJOB.jcl:4` |
| Shared: oracle collection and harness | 3 to 10 | Get a saved copy of the dataset and job output, set up the normalization spec and the deviation register | inference |

Total: about 10 to 24 engineer-days. The spread is mostly the shared line, and the shared line is mostly
one question: does an oracle exist.

## The assumptions the range is most sensitive to

1. **The file on disk holds 15 byte records.** The copybook gives 15 bytes by hand
   (`app/cpy/LAYOUTX.cpy:2`, `app/cpy/LAYOUTX.cpy:3`) and the DD says `LRECL=80`
   (`app/jcl/WRITEJOB.jcl:4`). If the real file holds 80 byte records with 65 bytes of filler, wave 2
   grows by about 1 to 3 days. The port then has to reproduce the filler value, and the reader has to
   skip it.
2. **The two jobs in the tree are the whole nightly cycle.** No scheduler was parsed
   (`analysis`, field `warnings`). If the scheduler export names other jobs that read or write
   SPARQ.TEST.MASTER, each extra reader adds about 1 to 2 days, and the cut between wave 1 and wave 2
   moves.
3. **A saved copy of the dataset or of the job output exists.** If it does, the harness is a golden
   master compare. If it does not, the harness has to be built from characterization tests, the
   weakest oracle. Add about 3 to 5 days, and every wave stays provisional.
4. **PGMW is the real program and not a stub.** It writes a record it never fills
   (`app/cbl/PGMW.cbl:13`, `app/cbl/PGMW.cbl:14`). If the client has a fuller version, the tree is not
   the system, and this estimate does not apply to it.

## Where Claude Code can do the mechanical port, and where it cannot

| Part | Claude Code | Why | Evidence |
|---|---|---|---|
| PGMR and PGMW transliteration | Strong | Each is a sequential open, one I/O statement, close. There is no branching | `app/cbl/PGMR.cbl:13`, `app/cbl/PGMW.cbl:13` |
| Packed decimal codec for LR-AMT | Strong with a test | The encoding is fixed and checkable with known byte strings | `app/cpy/LAYOUTX.cpy:3` |
| JCL allocation to target storage semantics | Partial | The NEW, CATLG and DELETE dispositions map to a design choice, not a translation | `app/jcl/WRITEJOB.jcl:3` |
| What the record means | Cannot | No field names beyond LR-KEY and LR-AMT and no rules in the code | `app/cpy/LAYOUTX.cpy:2` |
| Why LRECL=80, and whether writing an unfilled record is intended | Cannot | The intent is not in the source. It needs the client | `app/jcl/WRITEJOB.jcl:4`, `app/cbl/PGMW.cbl:14` |
