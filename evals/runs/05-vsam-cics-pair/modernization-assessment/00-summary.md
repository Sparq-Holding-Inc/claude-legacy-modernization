# 00 Summary

## Scoping answers

All three came as flags. No default was applied and nothing was asked.

| Question | Answer | Source |
|---|---|---|
| Target state | refactor | `--target refactor` |
| What must not break | the nightly batch cycle | `--must-not-break` |
| Runtime telemetry | none | `--telemetry none` |

Because telemetry is `none`, every dead-code claim is provisional.

## What is in the tree

Two CICS online programs, one copybook, one CSD file, and nothing else. PROGW writes the ACCTDAT
account file (`app/cbl/PROGW.cbl:7`). PROGR reads it (`app/cbl/PROGR.cbl:7`). Both include the same
layout copybook (`app/cpy/ACCTREC.cpy:1-3`). The CSD maps them to transactions TRNW and TRNR
(`app/csd/DEMO.CSD:4`, `app/csd/DEMO.CSD:6`). The extractor found 4 nodes and 5 edges, all high
confidence, with 0 computed calls and 0 files not parsed.

## Wave count

**1 wave.** The system is two programs over one file. I did not invent a second wave. Inside the wave,
PROGR is ported and proven first, then PROGW. Detail in `03-waves.md`. If the system were ten times
larger, the cut would be at the dataset seam.

## Single largest risk

The must-not-break item cannot be assessed from what was provided. The tree holds no JCL, no
scheduler and no batch program (`graph.json` `meta.files_seen` shows 0 of each), yet the nightly batch
cycle presumably reads or writes ACCTDAT. Any batch program that reads the file by offset depends on
the 17 byte record in `app/cpy/ACCTREC.cpy:1-3`, including the COMP-3 balance at
`app/cpy/ACCTREC.cpy:3`. A refactor that changes that encoding or layout breaks it silently. This is
`inference` about what lies outside the tree. It drives PROGW to blast radius 4 in `risks.json`.

## Scores

| Unit | Port difficulty | Blast radius | Quadrant | Confidence | Evidence |
|---|---|---|---|---|---|
| PROGR | 1 | 2 | low-low | medium | `app/cbl/PROGR.cbl:7` |
| PROGW | 2 | 4 | low-high | low | `app/cbl/PROGW.cbl:7`, `app/cpy/ACCTREC.cpy:3` |

## Other findings

| Finding | Confidence | Evidence |
|---|---|---|
| The programs look like stubs: no input, no key set, no error handling. Scores are for this code only. | medium | `app/cbl/PROGR.cbl:4-10`, `app/cbl/PROGW.cbl:4-10` (inference) |
| The CSD names a TEST dataset. The tree may not be the production definition. | medium | `app/csd/DEMO.CSD:2` |
| The dormant bucket is empty because no last-modified dates exist, not because the code is recent. | high | `modernization-assessment/05-dead-code.md:14` |

## Files not parsed and extractor limits that touch this system

Not parsed: nothing was skipped (`unparsed` in `graph.json` is empty).

These limits from `meta.limits` matter here:

- JCL `IF/THEN/ELSE` and `COND=` are not modeled, and JCL is not present at all.
- `EXEC CICS RETURN TRANSID`, `START` and `SEND MAP` are not edges. The two programs use none of them.
- Only Control-M XML and shell wrappers that name JCL files are read as schedulers. The tree has none.
- A called subprogram gets no DDs from its caller's JCL step. No calls exist here.

## Open Questions for the client's engineers

1. Where is the nightly batch cycle? Send its JCL, PROCs, scheduler definitions and the list of
   programs that open ACCTDAT. Without them, the must-not-break item has no evidence behind it.
2. Is `SPARQ.TEST.ACCTDAT.KSDS` (`app/csd/DEMO.CSD:2`) the production file, or a test copy? What is
   the production dataset name, its key offset and length, and its record size? The IDCAMS
   DEFINE CLUSTER is not in the tree.
3. Are PROGR and PROGW the real production programs, or stubs for a demo? Neither takes input, sets
   ACCT-ID, or handles a failed call (`app/cbl/PROGR.cbl:4-10`, `app/cbl/PROGW.cbl:4-10`). Where does
   the real key come from?
4. Does the production CSD file definition allow ADD and READ? The definition in the tree sets no
   operation attributes (`app/csd/DEMO.CSD:1-3`), and PROGW performs a WRITE.
5. When does the batch cycle run against ACCTDAT relative to the online day? Is the file closed to CICS
   during the batch window, or shared? That order is a temporal edge the harness must keep.
6. Do any other programs, extracts or partner feeds read ACCTDAT by column offset? Whatever left the
   building is a contract on the 17 byte record.
7. Can the client supply 12 months of CICS transaction statistics or SMF data for TRNR and TRNW, so the
   dead-code and dormancy calls can move from provisional to evidence?
8. Are the last-modified dates for the source recoverable from a version control system? The extractor
   found none, so the dormancy rule could not run.
9. Who at the client can read COBOL and sign the normalization spec and the deviation register in
   `06-test-strategy.md`?
