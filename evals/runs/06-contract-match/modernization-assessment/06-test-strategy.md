# 06 Test strategy

The bar is not "it passes the tests". The bar is: for the inputs this system really sees, the new implementation writes the same bytes as the old one, and every difference is a decision someone wrote down.

Anchor from the scoping answer: **the nightly batch cycle must not break**. The tree does not name a nightly cycle or a scheduler. I assume the two jobs are part of it (inference). The anchor therefore attaches to the one thing that crosses between them: the bytes of SPARQ.TEST.MASTER and the order the jobs run in.

## The tree holds no datasets

The tree has JCL and source but no data. The one dataset is named only in the DDs (`app/jcl/WRITEJOB.jcl:3`, `app/jcl/READJOB.jcl:3`). The oracle has to come from the client's own runs. What I would ask them to supply is in the last section.

## Oracle for wave 1, strongest first

| Rank | Oracle | Available here | Confidence | Evidence |
|---|---|---|---|---|
| 1 | Parallel run: new and old writer process the same run, outputs diffed byte for byte | Unknown. It depends on whether the old jobs can stay up beside the new ones. Ask before assuming no. | low | inference |
| 2 | Replay of captured production inputs and outputs | Unknown. PGMW takes no input file in this tree (`app/cbl/PGMW.cbl:13`), so what varies run to run is unclear. | low | inference |
| 3 | Golden master from archived copies of the dataset | Possible. The DSN carries no generation suffix, so prior runs may not be kept automatically (`app/jcl/WRITEJOB.jcl:3`). Ask for archived copies or backups. | low | inference |
| 4 | Characterization tests generated from the source | Always possible. Weakest, and provisional. It encodes what the code says, not what it did. | medium | `app/cbl/PGMW.cbl:14` |

Use rank 3 for PGMR (feed it real legacy-written files) and rank 1 or 3 for PGMW. If only rank 4 is available, label all wave 1 coverage provisional.

## Normalization spec (each line is a claim that a difference does not matter)

Keep this list short and have a person sign it.

| Item | Rule | Why | Evidence |
|---|---|---|---|
| Money field LR-AMT | Compare as decimal, zero tolerance, also compare the sign nibble | Packed decimal S9(7)V99 is 5 bytes. A float type would round, and a different sign nibble is a real difference. | `app/cpy/LAYOUTX.cpy:3` |
| Key field LR-KEY | Compare as raw bytes, no case or trim rules | It is X(10). Do not let a port trim or re-encode it. | `app/cpy/LAYOUTX.cpy:2` |
| Record length and padding | Decide and record: 15 byte records or 80 byte padded records. Pad byte compared, not ignored. | Layout says 15 bytes, the DD says LRECL=80. | `app/jcl/WRITEJOB.jcl:4` |
| Bytes of unset fields | Do not normalize them away. Compare them, then decide with a person. | PGMW writes the record with no MOVE, so the bytes depend on storage defaults. | `app/cbl/PGMW.cbl:14` |
| Timestamps, run ids, page numbers | None in the layout, so nothing to ignore | The record has only the two fields. | `app/cpy/LAYOUTX.cpy:1` |
| Record ordering | One record is written per run in this tree. Ordering is not a factor here. | Single WRITE. | `app/cbl/PGMW.cbl:14` |

Mainframe traps that apply: packed decimal (yes, the amount), collating sequence (only if a downstream sort or compare on LR-KEY exists, so ask), REDEFINES (none in LAYOUTX), padding and low values (yes), job order (see below).

## Cases to add on purpose

- Amount at the extremes: 0, 9999999.99, negative values, and the sign nibble variants.
- A key of all spaces, and a key with low values.
- A run against an existing dataset. `DISP=(NEW,CATLG,DELETE)` should fail at allocation (`app/jcl/WRITEJOB.jcl:3`). The replacement must behave the same or the change is a registered deviation.
- The reader started before the writer has ever run. The dataset does not exist, so the read fails loudly (inference).
- The reader on a file that holds more than one record. PGMR reads only the first (`app/cbl/PGMR.cbl:14`), and a port must not "fix" that unless a deviation is signed.
- Bad data already in the real file. I cannot know what is there. Ask for a sample.
- Boundary dates and fiscal close paths. The record carries no date, so these matter only through whatever feeds the nightly cycle outside this tree (inference). Ask what runs at month end and year end.

## Order the harness must keep

The graph holds no ordering edge between the jobs, because no scheduler was parsed (`02a-edge-tables.md`). The rule to keep is: WRITEJOB runs before READJOB in the same cycle. That comes from the data hub, so it is inference. The scheduler export replaces it with a fact.

## Deviation register

Nothing differs without a row. It is empty today. Two decisions will probably need rows once the client answers: what bytes PGMW writes for fields it never sets (`app/cbl/PGMW.cbl:14`), and which record length is authoritative (`app/jcl/WRITEJOB.jcl:4`).

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact |
|---|---|---|---|---|---|
| none yet | | | | | |

## Exit bar for wave 1

- The byte diff of SPARQ.TEST.MASTER is clean, modulo the normalization spec and the register.
- Every case above passes.
- The harness is in version control and runs in CI.
- The deviation register is signed by someone who has the authority.

The harness stays after cutover. It becomes the regression suite for the new jobs.

## What to ask the client to supply

- Two or more real copies of SPARQ.TEST.MASTER, or archived copies, from ordinary days and from month end and year end.
- The job log or SYSOUT of recent WRITEJOB and READJOB runs, with return codes and run times.
- A directory listing or catalog entry that shows the real RECFM and LRECL and the record count.
- The scheduler export that shows where these two jobs sit in the nightly cycle.
- The list of every other reader of the dataset, including partner extracts and utility steps.
- Any report or file produced downstream of READJOB.
