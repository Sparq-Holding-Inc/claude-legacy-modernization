# 06 Test strategy: behavioral equivalence

The bar: for the inputs this system sees, the new code produces the same outputs as the legacy code.
Where it does not, someone decided that on purpose and wrote it in the Deviation Register. Target state is
`refactor`, so the legacy code and the new code must agree on the bytes of SPARQ.TEST.MASTER during
coexistence.

## The oracle

The tree holds no datasets, no archived reports and no logs. It holds source only (`graph.json` lists
2 COBOL files, 1 copybook and 2 JCL files: `modernization-assessment/graph.json:1`). The oracle has to
come from job output, logs and reports the client supplies.

What to ask the client for:

1. A hex dump of SPARQ.TEST.MASTER as WRITEJOB last produced it, and every archived generation, if the
   real dataset is a generation data group. Golden master, level 3 of the oracle ladder.
2. The catalog entry (LISTCAT) for the dataset: RECFM, LRECL, BLKSIZE. It settles the 15 byte layout
   against LRECL=80 question (`app/cpy/LAYOUTX.cpy:3`, `app/jcl/WRITEJOB.jcl:4`).
3. Job logs and SMF step records for READJOB and WRITEJOB for at least 12 months, with return codes
   and times. They show the nightly order and are the telemetry for the dead-code register
   (`modernization-assessment/05-dead-code.md:1`).
4. The scheduler export. The temporal edges are missing (`analysis` field `warnings`).
5. A list of every other program or partner that reads or writes the dataset.
6. Whether legacy can stay up, so a parallel run is possible. Ask before settling for less.

## Oracle per wave

| Wave | Oracle | Why | Strength | Evidence |
|---|---|---|---|---|
| 1. Reader (PGMR, READJOB) | Parallel run if legacy stays up: both readers read the same archived or live copy of the dataset and the return codes and decoded records are compared. Reading is side-effect free. | The job reads with DISP=SHR and writes nothing, so a parallel run costs little. | strongest available | `app/jcl/READJOB.jcl:3`, `app/cbl/PGMR.cbl:13` |
| 2. Writer (PGMW, WRITEJOB) | Golden master from archived copies of the dataset, then parallel run of legacy and new writers into two datasets, compared byte for byte. | The output is a single file, so a byte diff is the assertion. | medium, until an archived copy exists | `app/cbl/PGMW.cbl:14`, `app/jcl/WRITEJOB.jcl:3` |
| Fallback for either wave | Characterization tests generated from source. | Only if no archived output can be had. Label the coverage provisional. It encodes what the code says, not what it did. | weak | inference |

## Normalization spec (each line needs human sign-off)

| Item | Rule | Why it is safe or where a bug can hide | Evidence |
|---|---|---|---|
| Packed decimal `LR-AMT` | Compare in a decimal type, tolerance zero. Compare the raw bytes as well, including the sign nibble (C, D or F). | An IEEE float would round. A different sign nibble is a real difference to any reader that checks it. | `app/cpy/LAYOUTX.cpy:3` |
| Record length and padding | Decide, from LISTCAT, whether the stored record is 15 or 80 bytes, and what the padding is (spaces or low values). Then compare with that rule. | The copybook and the JCL disagree. Padding that "does not matter" to PGMR may matter to another reader. | `app/cpy/LAYOUTX.cpy:3`, `app/jcl/WRITEJOB.jcl:4` |
| Unset record fields | Do not normalize. Record the observed legacy bytes and raise a Deviation Register row. | PGMW writes the record with no MOVE before it, so the legacy output may hold whatever the buffer held. A port cannot copy that on purpose. | `app/cbl/PGMW.cbl:14` |
| Collating sequence | Compare `LR-KEY` as bytes. Do not sort in the harness. | EBCDIC and ASCII order differ. Nothing in the tree sorts, but an unseen reader may depend on key order. | `app/cpy/LAYOUTX.cpy:2` |
| Timestamps and run identifiers | Strip only from job logs. The record holds none. | The record has just a key and an amount. | `app/cpy/LAYOUTX.cpy:1` |
| Record ordering | Compare in file order. Do not treat order as incidental. | The file is sequential. One record is written per run in this tree, but a consumer may rely on order. | `app/cbl/PGMW.cbl:7` |
| REDEFINES | None in the tree. Nothing to test. | The copybook has no REDEFINES. | `app/cpy/LAYOUTX.cpy:1` |

## Targeted cases

- First run: the dataset does not exist. Legacy creates it (`app/jcl/WRITEJOB.jcl:3`).
- Rerun the same night after a failure. DISP=NEW,CATLG,DELETE meets an existing dataset. Record what the
  legacy job does, and what the scheduler does around it.
- Amount extremes: 9,999,999.99, 0.00, negative amounts, and the smallest step of 0.01.
- Bad data already in the file: an invalid packed field, a key of spaces or low values, a short record.
  PGMR does not use the amount (`app/cbl/PGMR.cbl:14`), so a bad amount passes today. Decide whether
  the port must also pass it.
- Empty dataset, and a dataset of exactly one record.
- Boundary dates. The tree has no date logic, so month-end and fiscal-close cases only apply if the
  client's nightly cycle sends month-end data through this dataset. Ask.

## Order the harness must keep

| Before | After | Evidence |
|---|---|---|
| WRITEJOB | READJOB | `app/cbl/PGMW.cbl:13`, `app/cbl/PGMR.cbl:13` |

That order is implied by the data edge. No scheduler or step order enforces it in the tree, so it is
inference. Get the scheduler export to confirm it (`analysis` field `warnings`).

## Deviation Register (starting rows)

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| DEV-001 | PGMW writes the record without setting its fields | To be decided. Explicit initial values, or reproduce the archived bytes | Reproducing storage contents by accident is not portable | pending | Any reader of the amount field | `app/cbl/PGMW.cbl:14` |
| DEV-002 | Copybook record is 15 bytes, JCL says LRECL=80 | To be decided from LISTCAT | The two must not disagree in the target | pending | Every reader of the dataset, in or out of this tree | `app/cpy/LAYOUTX.cpy:3`, `app/jcl/WRITEJOB.jcl:4` |

Both rows are candidates. Nothing differs until a row is signed.

## Exit bar per wave

A wave is done when the replay diff is clean modulo the normalization spec and the register, every targeted
case passes, the harness is in version control and runs in CI, and the register is signed by someone with
authority. Not when the port compiles. Keep the harness after cutover as the regression suite.
