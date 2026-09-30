# 06 Test strategy

Definition of correct: for the inputs this system actually sees, the ported jobs produce the same outputs as
the legacy jobs, and any difference is written in the Deviation Register with a named approver. The legacy system
has no tests, and the tree has no data files at all, so there is no oracle in the tree. Evidence: analysis:
`node_counts` in `modernization-assessment/graph.json` (one dataset node and no data). The oracle has to come from
job output, job logs and the archived copies of the file, which the client must supply (see "What to ask the
client" below).

The must-not-break item is `the nightly batch cycle`. It maps to no unit in this tree: there is no scheduler, and no
job or program is named for a cycle. It is not turned into a test anchor here, and no mapping is invented. The
nearest anchors are the two jobs and the file between them. Evidence: analysis: `warnings` in
`modernization-assessment/graph.json`, `app/jcl/READJOB.jcl:1`, `app/jcl/WRITEJOB.jcl:1`.

## Oracle per wave

| Wave | Oracle, strongest first | Provisional | What can be compared | Evidence |
|---|---|---|---|---|
| 1. Reader side | Parallel run: PGMR is read-only and the DD is DISP=SHR, so the ported reader can run beside the legacy one on the same copy of the file. Then golden inputs from archived copies of the file. Then characterization tests. | The characterization tests are provisional. | Only the return code and the abend behavior. PGMR uses no field and prints nothing. | `app/jcl/READJOB.jcl:3`, `app/cbl/PGMR.cbl:14` |
| 2. Writer side | Parallel run: run the new writer into a differently named dataset next to the legacy WRITEJOB and compare the bytes. Replay does not apply, because PGMW reads no input. Fallback: an archived copy of the file as a golden master. | Any check against source alone is provisional. | The output file (bytes, length and attributes) and the return code. | `app/jcl/WRITEJOB.jcl:3`, `app/cbl/PGMW.cbl:13` |

Notes on the parallel run for wave 2. The legacy job allocates `SPARQ.TEST.MASTER` as NEW with a fixed name, so
the comparison run must write to another name, and the legacy dataset must not be touched. Evidence:
`app/jcl/WRITEJOB.jcl:3`. This is a question for the client: can a shadow run of WRITEJOB be allowed? Teams
often assume it cannot and are wrong. Inference.

## Normalization spec (each line is a place a bug can hide)

A human must sign off on this list.

| # | Difference to ignore | Default | Why it may hide a bug | Evidence |
|---|---|---|---|---|
| N1 | Bytes 16 to 80 of each record, if the file really has LRECL=80 | Do not ignore. Compare them. Decide after the real LRECL is known | The layout is 15 bytes and the JCL says 80. What fills the rest is undefined in the source | `app/jcl/WRITEJOB.jcl:4`, `app/cpy/LAYOUTX.cpy:3` |
| N2 | The content of `LR-KEY` and `LR-AMT`, if the legacy output changes from run to run | Do not mask until two legacy runs are compared. Then mask only the bytes that differ | PGMW moves nothing into its record, so the content may be storage left over from something else | `app/cbl/PGMW.cbl:14` |
| N3 | The sign nibble of the packed amount (`C` against `F` for positive) | Compare the raw bytes first. Compare as decimal with zero tolerance only if a human signs it | The sign nibble is part of the contract the reader depends on | `app/cpy/LAYOUTX.cpy:3`, `app/cpy/LAYOUTY.cpy:3` |
| N4 | Timestamps, run ids, sequence numbers, page numbers | None exist in the tree. Add none | Nothing to normalize | `app/cbl/PGMW.cbl:12` |
| N5 | Record order | The file holds one record, so order does not arise. Recheck if the real file has more | The writer writes once. A reader that reads more than once would depend on order | `app/cbl/PGMW.cbl:14` |

## Cover the input space deliberately

| Case | Program | Why | Evidence |
|---|---|---|---|
| Empty file (zero records) | PGMR | The READ has no AT END and no FILE STATUS. The legacy program likely ends abnormally at end of file. A port has to match that or record a deviation. Inference | `app/cbl/PGMR.cbl:14`, `app/cbl/PGMR.cbl:6` |
| Short record (fewer than 15 bytes) and long record (80 bytes) | PGMR | Tests the length question raised by LRECL=80 against a 15 byte layout | `app/jcl/WRITEJOB.jcl:4`, `app/cpy/LAYOUTY.cpy:1` |
| Invalid packed decimal in the amount (spaces, low-values, bad sign) | PGMR | PGMR never decodes the amount, so it accepts any bytes. A port that decodes the amount eagerly into a decimal type would fail on data the legacy job accepts. Inference | `app/cbl/PGMR.cbl:14`, `app/cpy/LAYOUTY.cpy:3` |
| Valid packed decimal at the limits of `S9(7)V99`, negative, and zero | PGMW output and PGMR input | Covers the sign and the digit count of the field both sides share | `app/cpy/LAYOUTX.cpy:3` |
| Dataset already exists | WRITEJOB | The job allocates NEW under a fixed name. Legacy behavior is likely an allocation failure. The port must match or the deviation goes in the register. Inference | `app/jcl/WRITEJOB.jcl:3` |
| Reader runs before the writer | READJOB | The file does not exist. Legacy behavior is likely an allocation failure. Inference | `app/jcl/READJOB.jcl:3` |
| Boundary dates, month end, fiscal close | none | No date is handled in this tree, so none can be targeted. Ask the client whether the nightly cycle has a close variant | `app/cbl/PGMW.cbl:12` |

## Mainframe traps that apply here

- **Packed decimal.** Both copybooks hold a `COMP-3` amount. In the target, use a decimal type and zero tolerance
  on money. Evidence: `app/cpy/LAYOUTX.cpy:3`, `app/cpy/LAYOUTY.cpy:3`.
- **Two copybooks for one file.** Byte compatible today. Keep one schema in the target, and add a test that fails if
  the writer and the reader schema differ. Evidence: `app/cpy/LAYOUTX.cpy:1`, `app/cpy/LAYOUTY.cpy:1`.
- **Record padding and low values.** Decide which differences matter (N1 and N2 above) and write it down.
  Evidence: `app/jcl/WRITEJOB.jcl:4`.
- **Job order.** The harness must keep the writer before the reader. This comes from the shared dataset, not from a
  scheduler edge, because no scheduler was given. `graph.json` has no temporal edges here. Inference. Evidence:
  `app/jcl/WRITEJOB.jcl:3`, `app/jcl/READJOB.jcl:3`.
- **Collating sequence and `REDEFINES`.** Neither arises. The file is sequential and no copybook redefines a field.
  Evidence: `app/cbl/PGMR.cbl:7`, `app/cpy/LAYOUTX.cpy:1`.

## Deviation Register

Nothing is approved yet. These rows are proposals that the ported system will force a decision on. None may go live
without a name in the Approved by column.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| DR-1 | Two copybooks, LAYOUTX and LAYOUTY, describe the same 15 bytes with different field names | One shared schema for the file | Removes the silent drift risk on the contract edge | not approved | None expected if the bytes are equal. Any other reader of the file must be found first | `app/cpy/LAYOUTX.cpy:1`, `app/cpy/LAYOUTY.cpy:1` |
| DR-2 | WRITEJOB asks for LRECL=80 for a 15 byte layout | Open. One record length, chosen on purpose | The two are inconsistent, and the real catalog entry is not known | not approved | Every reader of the file, including any outside the tree | `app/jcl/WRITEJOB.jcl:4` |
| DR-3 | PGMW writes a record it never fills | Open. A defined record, or the same undefined content | A defined record is safer. It changes the bytes | not approved | Any reader that treats the bytes as data | `app/cbl/PGMW.cbl:14` |
| DR-4 | WRITEJOB fails or misbehaves if the dataset exists, probably | Open. A rerunnable write, or the same behavior | A nightly job cannot be rerun in the legacy form. Inference | not approved | The nightly cycle, which cannot be checked without the scheduler | `app/jcl/WRITEJOB.jcl:3` |

## Exit bar per wave

A wave is done when all of these hold. A port that compiles is not done.

| Wave | Bar | Evidence |
|---|---|---|
| 1 | The replay or parallel diff of return codes is clean for the golden inputs, modulo the normalization spec. Every case in the input table for PGMR passes. The harness is under version control and runs in CI. The register rows that touch the reader (DR-1, DR-2) are signed by someone with the authority to sign them | `app/cbl/PGMR.cbl:14`, `app/jcl/READJOB.jcl:3` |
| 2 | The new writer's output is byte for byte the legacy output, modulo N1 to N3, and the wave 1 reader and the legacy reader both accept it. Every case for PGMW and WRITEJOB passes. DR-2 to DR-4 are signed | `app/cbl/PGMW.cbl:14`, `app/jcl/WRITEJOB.jcl:3` |

Keep the harness after cutover. It becomes the regression suite, and the only executable specification of the
file. Inference.

## What to ask the client to supply

1. A binary copy of `SPARQ.TEST.MASTER` as WRITEJOB last produced it, with its catalog entry (RECFM, LRECL, block
   size). This settles N1 and DR-2.
2. Two or more archived copies of the file from different days, or the reason none exist. The name has no
   generation suffix, so archives may not exist. Inference. Evidence: `app/jcl/WRITEJOB.jcl:3`.
3. Job logs or SMF records for READJOB and WRITEJOB across a full business cycle, including a month end, with return
   codes. This is also the telemetry that would firm up the dead-code register.
4. The scheduler export for the nightly batch cycle, and which jobs make it up.
5. A list of every other program, job and partner that reads or writes the file.
6. Permission to run a shadow WRITEJOB into another dataset name.
