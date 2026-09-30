# 06 Test strategy

Definition of "correct": for the inputs these jobs actually see, the new reader and writer produce the
same return codes, the same messages and the same bytes in SPARQ.TEST.MASTER as the legacy ones. Where
they differ, someone decided it on purpose and wrote it down in the Deviation Register below.

## The oracle problem in this tree

The tree holds the name of one dataset and none of its contents (`app/jcl/WRITEJOB.jcl:3`). It holds no
job output, no logs, no reports. So the oracle has to come from the client. What to ask for, in order of
strength:

1. **A parallel run.** Run legacy and new versions of WRITEJOB and READJOB against the same inputs in a
   test region and diff the results. PGMW reads no input (`app/cbl/PGMW.cbl:13`, `app/cbl/PGMW.cbl:14`),
   so a parallel run of the writer needs no input capture. This is the cheapest strong oracle in the
   system. Ask whether a test region exists.
2. **Saved copies of SPARQ.TEST.MASTER.** The dataset is not a generation dataset. The DSN carries no
   generation suffix (`app/jcl/WRITEJOB.jcl:3`), so prior runs are probably replaced, not kept. Ask
   whether backups, copies sent downstream, or an archive exist. Inference.
3. **Job logs and SMF records** for both jobs over the last 12 months. They give return codes, run times
   and run dates, and double as the telemetry the dead-code register lacks (see
   `modernization-assessment/05-dead-code.md`).
4. **Anything that leaves the building.** Ask what reads this dataset outside the tree: partner extracts,
   reports, transfers. A file that left is an executable specification of the format.
5. **Characterization tests from the source.** The weakest. Use them only if 1 to 4 are unavailable, and
   label the coverage provisional.

## Oracle per wave

| Wave | Oracle | Boundary compared | Evidence |
|---|---|---|---|
| 1. Reader job (PGMR, READJOB) | Parallel run if a test region exists, otherwise a saved copy of the dataset replayed through legacy and new readers | Return code, file status, and SYSOUT. PGMR writes nothing else | `app/cbl/PGMR.cbl:13`, `app/cbl/PGMR.cbl:14`, `app/jcl/READJOB.jcl:4` |
| 2. Writer job (PGMW, WRITEJOB) | Golden master: the legacy writer's output file, captured byte for byte | The dataset SPARQ.TEST.MASTER and its allocation attributes | `app/cbl/PGMW.cbl:14`, `app/jcl/WRITEJOB.jcl:3`, `app/jcl/WRITEJOB.jcl:4` |

Wave 1 has a weak boundary. PGMR discards the record it reads (`app/cbl/PGMR.cbl:14`), so a port that
decodes the record wrongly would still pass a return-code check. The harness for wave 1 therefore adds a
test-only assertion that the new decoder reads LR-KEY and LR-AMT from a legacy-written file as the
reference decoder does. That assertion tests something legacy PGMR never did. It is there because wave 2
depends on it.

## Normalization spec

Every line is an assertion that a difference does not matter. Each needs a human sign-off.

| Item | Rule | Why | Evidence |
|---|---|---|---|
| LR-AMT | Compare as a decimal type with zero tolerance. Never a float | Packed decimal, 7 integer digits and 2 decimals, COMP-3 | `app/cpy/LAYOUTX.cpy:3` |
| LR-AMT sign nibble | Compare the raw bytes as well as the decoded value | A strict decoder can reject a packed field that the legacy reader never decoded. See Traps | `app/cpy/LAYOUTX.cpy:3`, `app/cbl/PGMR.cbl:14` |
| LR-KEY | Compare bytes, then compare after code page conversion if the target is ASCII | PIC X(10) in EBCDIC. A conversion can change sort order and equality | `app/cpy/LAYOUTX.cpy:2` |
| Record padding | Compare the record as written, with the record length taken from the real dataset | The DD says LRECL=80. The copybook is 15 bytes by hand | `app/jcl/WRITEJOB.jcl:4`, `app/cpy/LAYOUTX.cpy:2` |
| Dataset name, space and disposition | Compare the allocation, not just the content | SPACE=(TRK,(1,1)) and NEW,CATLG,DELETE are part of the behavior | `app/jcl/WRITEJOB.jcl:3`, `app/jcl/WRITEJOB.jcl:4` |
| Timestamps, run ids | Nothing to normalize in the source. Any found in the real output must be listed here first | Neither program writes a date or a counter | `app/cbl/PGMW.cbl:14` |
| Record order | One record is written, so order does not arise. If the real file holds more, order is behavior until shown otherwise | Downstream consumers may depend on order. Inference | `app/cbl/PGMW.cbl:14` |

## Mainframe traps that apply

- **Packed decimal.** LR-AMT is `S9(7)V99 COMP-3` (`app/cpy/LAYOUTX.cpy:3`). Use a decimal type in the
  target. Zero tolerance.
- **An unfilled record with a packed field.** PGMW writes LAYOUT-REC and moves nothing into it
  (`app/cbl/PGMW.cbl:13`, `app/cbl/PGMW.cbl:14`). What lands in the file depends on the contents of the
  record buffer. If those bytes are not a valid packed value, a strict decoder in the target fails on
  legacy data that legacy code passes over. Inference. Capture the real bytes first.
- **Record length.** The DD says LRECL=80 and the extractor does not compare it with the copybook
  (`app/jcl/WRITEJOB.jcl:4`, `meta.limits` in `modernization-assessment/graph.json`). Depending on
  compiler options, a mismatch between the record description and the DD can fail the OPEN or leave
  padding. Inference. The engineers must say which.
- **Collating sequence.** LR-KEY is PIC X(10) (`app/cpy/LAYOUTX.cpy:2`). If the target sorts in ASCII, any
  ordered use of the key changes. Nothing in this tree orders by it, so it matters only for consumers
  outside the tree.
- **Job order.** The graph has no temporal edge. The order WRITEJOB before READJOB is inferred from the
  dispositions (`app/jcl/WRITEJOB.jcl:3`, `app/jcl/READJOB.jcl:3`). The harness must keep it, and must
  also test READJOB run first: the legacy behavior is an allocation failure.

## Boundary cases to add

| Case | Expected legacy behavior | Evidence |
|---|---|---|
| WRITEJOB run when the dataset already exists | Allocation fails, because the disposition is NEW. Inference | `app/jcl/WRITEJOB.jcl:3` |
| READJOB run when the dataset does not exist | Allocation fails on a DD with DISP=SHR. Inference | `app/jcl/READJOB.jcl:3` |
| READJOB on an empty dataset | PGMR has no AT END clause and no FILE STATUS, so an end-of-file read is likely an abend. Inference | `app/cbl/PGMR.cbl:14` |
| READJOB on a record with a bad packed sign | Legacy passes, because PGMR never decodes the field. Inference | `app/cbl/PGMR.cbl:14`, `app/cpy/LAYOUTX.cpy:3` |
| Month end, quarter end, fiscal year end runs | Unknown. Neither program reads a date and no scheduler was parsed. Ask which run dates matter | `app/cbl/PGMW.cbl:13` |

## Deviation Register

Nothing differs without a row. These rows are proposed and none is approved. The register starts here and
moves into version control with the harness.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| DEV-1 | Writes a record it never fills | To be decided: reproduce the bytes, or write a defined record | An unfilled record is a defect, if the tree is the real program | pending | The reader ignores the record. Consumers outside the tree are unknown | `app/cbl/PGMW.cbl:14` |
| DEV-2 | Fails at allocation when the dataset exists | To be decided: fail the same way, or replace the file | The failure is legacy behavior that a nightly cycle probably works around | pending | The nightly cycle order and any cleanup step outside the tree | `app/jcl/WRITEJOB.jcl:3` |
| DEV-3 | Reader opens the dataset with no end-of-file handling | To be decided | Same behavior may be wanted for a like-for-like check | pending | Abend on an empty file | `app/cbl/PGMR.cbl:14` |

## Exit bar per wave

A wave is done when all of these hold:

- the replay or parallel run diff is clean, apart from the normalization spec and the deviation register;
- every boundary case above passes, or has a signed deviation;
- the harness is in version control and runs in CI;
- the deviation register is signed by someone with the authority to sign it.

A wave is not done because the port compiles, or because it passes tests the porter wrote.

## Keep the harness

The comparison harness is the regression suite for the new system. Budget for keeping it after cutover.
