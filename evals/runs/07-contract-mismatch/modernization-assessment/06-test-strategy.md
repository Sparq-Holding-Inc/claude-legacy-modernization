# 06 Test strategy

The bar is this: for the inputs the nightly batch cycle sees, the new reader and writer produce the same outputs as the old ones. Where they do not, someone decided that on purpose and wrote it down in the deviation register. Target state is refactor, so the behavior stays and the code is restructured.

## The oracle problem

The tree holds no datasets, no job output, no logs and no reports. It holds two programs, two copybooks and two JCL members. So the oracle has to come from the client. There is no telemetry (`--telemetry none`), so nothing tells us which runs are typical.

Ask the client to supply:

1. **Archived copies of SPARQ.TEST.MASTER**, or of what it is copied to. The DD creates a new non-generation dataset each run (`app/jcl/WRITEJOB.jcl:3`), so prior runs exist only if someone copied them. Ask whether it is a GDG upstream, or copied to backup.
2. **SYSOUT and return codes of WRITEJOB and READJOB** for at least one full business cycle, including month end.
3. **The scheduler export** for the nightly cycle, so the job order is known and not assumed.
4. **Every consumer of the dataset outside this tree**, and the layout each one uses.
5. **An answer on the record length.** 15 bytes, or 80 (`app/jcl/WRITEJOB.jcl:4`).

## Oracle per wave

| Wave | Oracle, strongest available first | Why | Evidence |
|---|---|---|---|
| 1. Reader (`PGMR`, `job:READJOB`) | Captured copy of a real SPARQ.TEST.MASTER written by the legacy PGMW, replayed into the new reader, with the return code and SYSOUT compared. If no copy exists, run the legacy WRITEJOB once in a test region and capture what it writes. | The reader's only input is the dataset. The reader writes nothing, so its output is its return code and SYSOUT. | `app/jcl/READJOB.jcl:3`, `app/cbl/PGMR.cbl:14` |
| 2. Writer (`PGMW`, `job:WRITEJOB`) | Parallel run, if the legacy job can stay up: run both writers against the same trigger, and compare the two datasets byte for byte. Otherwise golden master from the archived copies above. | The writer's only output is the dataset. It has no input file. | `app/cbl/PGMW.cbl:13`, `app/jcl/WRITEJOB.jcl:3` |

Characterization tests generated from the source are the weakest oracle. In this tree they would only say that PGMW writes one record and PGMR reads one, and they would encode the unfilled record. Use them only where the four sources above cannot be had, and label the coverage provisional.

## The contract edge, tested at the wave boundary

The medium contract edge, PGMW to PGMR (`app/cbl/PGMR.cbl:11`, `app/cbl/PGMW.cbl:11`), gets its own test and it runs in both waves.

- **Layout equality test.** Parse the same file with the layout from `LAYOUTX` and with the layout from `LAYOUTY` and assert the same offsets, lengths and types. By the PIC clauses they are equal (`app/cpy/LAYOUTX.cpy:2`, `app/cpy/LAYOUTX.cpy:3`, `app/cpy/LAYOUTY.cpy:2`, `app/cpy/LAYOUTY.cpy:3`). The test keeps them equal after a change to either.
- **Record length test.** Assert the length of the record the writer produces, against the `LRECL=80` on the DD (`app/jcl/WRITEJOB.jcl:4`). If they disagree, the test fails, and the client decides which is right. Do not port past this until they have.
- **Cross wave test.** In wave 1 the new reader reads a file the legacy writer made. In wave 2 the new writer produces the file and the new reader reads it. Both must pass, and the second is the one that proves the cutover.

## Normalize before you diff

The normalization spec is short, and each entry is a place a bug can hide. A human signs it off.

| Item | Rule | Evidence |
|---|---|---|
| Packed decimal amount | Compare as a decimal type with zero tolerance. Never use a float. The field is `S9(7)V99 COMP-3`. | `app/cpy/LAYOUTX.cpy:3` |
| Key text | Compare bytes. The `X(10)` field is EBCDIC on the legacy side. If the target is ASCII, convert the text field only and never the packed field. | `app/cpy/LAYOUTX.cpy:2` |
| Record padding | Decide whether trailing bytes up to 80 matter. Write the decision down. It depends on the LRECL answer. | `app/jcl/WRITEJOB.jcl:4` |
| Timestamps, run ids, page numbers | Mask in SYSOUT only. The dataset has none, on the source we have. | inference |
| Record order | One record per run, so order is not an issue today. Revisit if the client says the file holds more. | `app/cbl/PGMW.cbl:14` |

## Cover the input space deliberately

- **Bad data that is already in there.** PGMW writes its record without filling it in (`app/cbl/PGMW.cbl:13`, `app/cbl/PGMW.cbl:14`). Inference: the packed field may hold bytes that are not a valid packed number. The new reader must reproduce what the legacy reader does with such a record, which is nothing, because PGMR never looks at a field (`app/cbl/PGMR.cbl:14`). A port that validates the packed field would fail on real files, and that would be a behavior change.
- **The empty file.** PGMR reads one record with no end of file handling (`app/cbl/PGMR.cbl:14`). Test an empty dataset. Inference: the legacy behavior is not defined by the source.
- **Rerun.** Run WRITEJOB twice without a delete. The legacy DD is `DISP=(NEW,CATLG,DELETE)` (`app/jcl/WRITEJOB.jcl:3`). Inference: the second run fails. The new writer must do the same, or the deviation register must say why not.
- **Failed run.** Abend PGMW after the open. The third DISP subparameter deletes the dataset. Test that READJOB then fails the same way the legacy one does.
- **Order.** Run READJOB before WRITEJOB, and against a stale copy. The extractor found no scheduler, so nothing in the tree enforces the order (`analysis.warnings`).
- **Boundary dates.** Month end and, if the client says the cycle is financial, fiscal year end. The tree has no date logic, so this is a question about the cycle, not the code.

## Mainframe traps for this system

- **Packed decimal.** The one numeric field is `COMP-3` (`app/cpy/LAYOUTX.cpy:3`, `app/cpy/LAYOUTY.cpy:3`).
- **Data transfer to the target platform.** In wave 1 the reader runs on the target and the writer still runs on the mainframe. The file must cross as binary, with only the text field converted. This is inference, and it is the most likely place for wave 1 to fail.
- **Collating sequence.** Not a factor while the file is sequential (`app/cbl/PGMR.cbl:7`, `app/cbl/PGMW.cbl:7`), and it becomes one if a key sorted file replaces it.
- **`REDEFINES`.** None in either copybook.
- **Job order.** The one temporal edge the harness must keep is writer before reader. It comes from the data, and no scheduler states it.

## Deviation register

Nothing differs from legacy behavior yet. The rows below are open decisions found during the assessment. None is approved.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| DR-1 | Record written without being filled in. Content undefined. | Open. Decide: reproduce, or write defined values. | Undefined bytes cannot be compared. | Pending | Unknown consumers outside the tree | `app/cbl/PGMW.cbl:14`, inference |
| DR-2 | Record layout kept as two copybooks with different field names. | Open. Decide: one copybook for both programs. | Removes the drift hazard. | Pending | None expected, both are 15 bytes | `app/cpy/LAYOUTX.cpy:1`, `app/cpy/LAYOUTY.cpy:1` |
| DR-3 | LRECL 80 on the DD, layout of 15 bytes. | Open. Decide which is right. | Two sources disagree. | Pending | Any outside reader | `app/jcl/WRITEJOB.jcl:4` |

## Exit bar per wave

A wave is done when:

- the replay diff is clean, modulo the normalization spec and the deviation register,
- the contract tests above pass, along with every boundary case listed,
- the harness is under version control and runs in CI,
- the deviation register is signed by someone with the authority to sign it.

Not when the port compiles. Not when it passes tests written beside the port.

Keep the harness after cutover. It becomes the regression suite for the modernized system.
