# 06 Test strategy

"Correct" here means: for the files this cycle really sees, the new reader and writer produce the same bytes and the same decoded money values as the legacy programs, and any difference is in the Deviation Register.

The tree holds one dataset and no test data, expected outputs or job logs. The oracle has to come from the client.

## Oracle per wave

| Wave | Oracle (strongest first) | What to ask the client for | Status | Evidence |
|---|---|---|---|---|
| 1. Reader | Golden master from archived generations of `SPARQ.TEST.MASTER`. Run legacy `PGMR` and the new reader over the same files and diff what each one reads. | Several archived copies of the file, including an empty one and the largest seen. SYSOUT and return codes from past READJOB runs. | Provisional until files arrive | `app/jcl/READJOB.jcl:3`, `app/jcl/READJOB.jcl:4` |
| 2. Writer | Parallel run if the old writer can still run: both write from the same input and the files are compared byte for byte. Otherwise captured past outputs. Characterization tests from the source are the last choice and are provisional. | Past copies of the file, the input that fed each one, WRITEJOB job logs. | Provisional until files arrive | `app/jcl/WRITEJOB.jcl:3`, `app/cbl/PGMW.cbl:14` |

A parallel run of the reader is cheap because it only reads. For the writer, `DISP=(NEW,CATLG,DELETE)` means the legacy and new writers cannot share one dataset name, so each writes to its own name and the files are compared afterwards (`app/jcl/WRITEJOB.jcl:3`).

## Normalization spec

Short on purpose. Each line is a claim that a difference does not matter, and a person signs off on each.

| Item | Rule | Why | Evidence |
|---|---|---|---|
| `LR-AMT` | Compare as a decimal with **zero tolerance**. Never as a float. Compare the raw packed bytes as well, including the sign nibble. | Packed decimal rounds and truncates differently from IEEE floats. | `app/cpy/LAYOUTX.cpy:3` |
| `LR-KEY` | Compare as bytes. Decide whether an ASCII port may re-encode it. If key order matters to a consumer, sort in EBCDIC order. | Collating sequence differs. | `app/cpy/LAYOUTX.cpy:2` |
| Record padding | Do not normalize until the record-length question is answered. Compare the full record length as written. | A 15-byte copybook record against `LRECL=80` leaves 65 bytes whose fill value is unknown. | `app/jcl/WRITEJOB.jcl:4`, inference |
| Record order | Treat as significant. The file is sequential and the reader takes records in file order. | A consumer may depend on order. | `app/cbl/PGMR.cbl:14` |
| Timestamps and run IDs | None in the layout, so nothing to strip. | The copybook holds only a key and an amount. | `app/cpy/LAYOUTX.cpy:1` |

## Targeted cases

- **Zero-record file.** `PGMR` reads once with no end-of-file clause and no `FILE STATUS` (`app/cbl/PGMR.cbl:14`, `app/cbl/PGMR.cbl:6`). What the legacy program does on an empty file is the behavior to reproduce, and it is not known (inference).
- **Maximum size file.** `SPACE=(TRK,(1,1))` allows one primary track and one secondary (`app/jcl/WRITEJOB.jcl:4`). Find out what the largest real file is.
- **Second run.** `DISP=(NEW,CATLG,DELETE)` fails when the dataset already exists (`app/jcl/WRITEJOB.jcl:3`). If the cycle is nightly, something has to delete or rotate the file first. That step is not in this tree (inference).
- **Uninitialized record.** `PGMW` writes `LAYOUT-REC` with no value moved in (`app/cbl/PGMW.cbl:14`). Capture exactly which bytes the legacy program writes, since a runtime may fill them with spaces or low values.
- **Bad data already in the file.** A non-numeric key or an invalid packed sign in `LR-AMT`. The new reader must behave the way the legacy one does (`app/cpy/LAYOUTX.cpy:3`).
- **Boundary amounts.** `9999999.99` and its negative, zero, and the smallest cent (`app/cpy/LAYOUTX.cpy:3`).
- **Boundary dates.** The layout has no date. If the real cycle has month-end or year-end variants, they sit in jobs not in this tree.

## Job order the harness must keep

`graph.json` holds no temporal edges, because no scheduler was parsed (`modernization-assessment/graph.json:383`). Logically the writer must run before the reader on the same dataset (inference). The harness must run them in that order and the client must confirm the real order.

## Exit bar per wave

A wave is done when the replay diff is clean modulo the normalization spec and the register below, every targeted case passes, the harness is under version control and runs in CI, and someone with authority has signed the register. Not when the port compiles.

## Deviation Register

Empty. No intentional differences have been approved.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| (none yet) | | | | | | inference |

Candidates to raise, none decided: writing an uninitialized record (`app/cbl/PGMW.cbl:14`), and the `NEW,CATLG,DELETE` failure on a rerun (`app/jcl/WRITEJOB.jcl:3`).

## After cutover

Keep the harness. It becomes the regression suite for the modernized pair, and it is the only executable specification of the file format.
