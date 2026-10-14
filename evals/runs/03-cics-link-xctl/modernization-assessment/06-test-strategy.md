# 06 Test strategy

The bar is that the new code gives the same outputs as the old for the inputs production sees, and that every difference is on purpose and written down.

## What the tree gives us

There are no datasets, no JCL, no GDGs, no copybooks (`modernization-assessment/graph.json` field `meta.files_seen`). The oracle has to come from job output, logs, reports and CICS records. The client must supply them.

## Oracle, by what can be had

| Piece | Oracle | Strength | Evidence |
|---|---|---|---|
| PROGB, PROGC, PROGD | None needed. Each only returns. The test is that PROGA reaches them and control comes back or does not. | n/a | `app/cbl/PROGB.cbl:4` |
| PROGA routing | Captured CICS transaction traces or journals: commarea in, the sequence of programs out. Replay them. | strong if the capture covers a cycle | `app/cbl/PROGA.cbl:15` |
| Fallback | Characterization tests from the source: one case each for the LINK to PROGB, XCTL to PROGC, and XCTL to PROGD. | weak and provisional. It encodes what the code says, not what it does. | `app/cbl/PROGA.cbl:12` |
| Nightly batch cycle | Not assessable. Nothing in the tree is batch. Ask for its JCL, scheduler export and the last year of job output and SYSOUT. | none yet | inference |

Parallel run is the first thing to ask about for PROGA. The program holds no data, so running both versions side by side on the same traffic is cheap if the region allows it.

## Cases that must be covered

- The commarea values production really sends to the computed LINK (`app/cbl/PROGA.cbl:16`). Include blank, short and unknown program names. The legacy behavior on a bad name (a PGMIDERR abend or a handled error) is the thing to reproduce. PROGA has no HANDLE or RESP clause, so inference: it abends. Confirm.
- The XCTL at line 20 followed by the XCTL at line 23. Test which of the two actually ends the task (`app/cbl/PROGA.cbl:23`).
- Fiscal-close and month-end traffic, if PROGA's caller varies by period. Ask.

## Normalization spec

Short on purpose. Ignore task numbers, timestamps and terminal ids. Do not ignore abend codes or the order of programs invoked: they are the behavior. Packed decimal and collating sequence do not arise, since no data is touched. Have a person sign it.

## Deviation register

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| none yet | | | | | | inference |

## Exit bar

Replay diff is clean modulo the normalization spec and register. Every case above passes. The harness is in version control and runs in CI. The register is signed. Keep the harness after cutover as the regression suite.
