# 06 Test strategy

The bar is not "it passes the tests". For the inputs this system actually sees, the new code must produce the same outputs as the old, and any difference must be decided on purpose and written in the Deviation Register below.

The tree holds no datasets, no JCL, no logs and no archived reports. The only dataset is a name in the CSD file. So the oracle cannot come from files in the tree. It has to come from the live file, CICS records and job output the client supplies. The list of what to ask for is in the last section. Evidence: analysis field `meta.files_seen`, `app/csd/DEMO.CSD:1-3`.

## Oracle per wave

| Wave | Oracle (strongest first) | Why | Confidence | Evidence |
|---|---|---|---|---|
| 1 (PROGR) | Parallel run. Send the same TRNR requests to the legacy and the new program and diff the response code and the returned record bytes. | The transaction only reads. Running it twice has no side effect, so this is safe and cheap. Fall back to a golden master from a KSDS snapshot if the legacy region cannot stay up. | medium | `app/cbl/PROGR.cbl:7-11`, inference |
| 2 (PROGW) | Captured traffic replay against a restored copy of the KSDS. Apply the same recorded TRNW requests to a copy on each side, then diff the file byte for byte and the response codes. | A live parallel run against one file would give a duplicate key on the second write. The replay has to run against copies. The capture window must cover month end and fiscal year end. | low | `app/cbl/PROGW.cbl:7-11`, inference |
| Both, provisional | Characterization tests from the source. | Weakest, because it encodes what the code says. Use only if no snapshot or capture exists, and label the coverage provisional. | low | inference |

Neither program takes a visible input, because neither sets its key. See the open question in `00-summary.md`. Until the client says how the key arrives, a request capture has no input to replay. Evidence: `app/cbl/PROGR.cbl:4-9`, inference.

## Normalization spec

Every line here says a difference does not matter. Each is a place a defect can hide. Keep the list short and have a human sign it.

| # | Normalize | Rule | Confidence | Evidence |
|---|---|---|---|---|
| N1 | Task and terminal identifiers, timestamps, task numbers in any CICS output or log | Ignore. | medium | inference |
| N2 | Anything else | Do not normalize. In particular, compare the balance with zero tolerance. | high | `app/cpy/ACCTREC.cpy:3` |

Deliberately not normalized:

- **Packed decimal balance.** `ACCT-BAL` is `S9(9)V99 COMP-3`, 11 digits and a sign, 6 bytes. Compare it in a decimal type with zero tolerance. Compare the sign nibble too. A port that writes a different sign nibble (C or F for positive) changes the bytes other programs read. Evidence: `app/cpy/ACCTREC.cpy:3`.
- **Key and record length.** The key is `PIC 9(11)`, zoned display, 11 bytes. The layout gives 17 bytes per record. The real length is in the VSAM cluster, which the tree does not hold. Confirm it. Evidence: `app/cpy/ACCTREC.cpy:2-3`, inference.
- **Key order.** A KSDS returns records in key order. Digits sort the same in EBCDIC and ASCII, but a legacy record with a space or letter in the key would not. Diff order, and test any non-numeric key already in the file. Evidence: `app/cpy/ACCTREC.cpy:2`, inference.
- **REDEFINES.** None in ACCTREC, so there is no branch to cover. Evidence: `app/cpy/ACCTREC.cpy:1-3`.
- **Padding and low values.** The record has no filler. An uninitialized field in the WRITE area would go to the file as stored. Decide, with a human, whether such bytes must be reproduced. Evidence: `app/cbl/PROGW.cbl:4-9`, inference.
- **Response codes.** The programs have no RESP option. An unhandled not found or duplicate key ends the task in an abend. The abend is behavior. Compare it, or record a deviation. Evidence: `app/cbl/PROGR.cbl:7-10`, `app/cbl/PROGW.cbl:7-10`, inference.

## Targeted cases

Production replay covers the common path. Add these on purpose.

| Case | Wave | What it checks | Confidence | Evidence |
|---|---|---|---|---|
| Key present, key absent | 1 | The read result and the not found abend. | medium | `app/cbl/PROGR.cbl:7-10` |
| Existing key, new key | 2 | The duplicate key abend and the add. | medium | `app/cbl/PROGW.cbl:7-10` |
| Balance at the maximum, zero, and negative | 1 and 2 | Nine integer digits, two decimals, and the sign nibble. | medium | `app/cpy/ACCTREC.cpy:3` |
| Bad data already in the file: a bad sign nibble, a non-digit key byte | 1 and 2 | The legacy behavior on records that break their own rules. | low | `app/cpy/ACCTREC.cpy:2-3`, inference |
| Empty file, and the largest file the KSDS has held | 1 and 2 | Boundaries of the file. | low | inference |
| Abend in the middle of a WRITE task | 2 | The implicit syncpoint: the write commits or backs out as one unit. | low | `app/cbl/PROGW.cbl:7-11`, inference |
| Month end and fiscal year end | 2 | The paths that run only at close. None is visible in the tree. Ask the client which run then. | low | inference |
| Order against the nightly batch cycle | 2 | The batch cycle is the client's must-not-break item, and the temporal order against TRNW cannot be tested until its source is supplied. | low | analysis field `meta.files_seen` |

## Job order the harness must keep

The temporal edges in `graph.json` are the list of orders the harness must keep. There are none, because the tree has no JCL or scheduler. The order between TRNW and the nightly batch cycle is therefore unknown, and it is the first thing to learn. Evidence: analysis field `edge_counts` (temporal 0), inference.

## Deviation Register

Nothing may differ from the legacy without a row here. It starts empty. The candidates below are proposals for the client's engineers to decide, not approved changes.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| DR-1 (candidate) | An unhandled not found on READ ends the task in an abend. | Undecided. Keep the abend, or return a handled response. | The abend is the current behavior, and no one may have chosen it. | not approved | Any caller that relies on the abend. Unknown. | `app/cbl/PROGR.cbl:7-10`, inference |
| DR-2 (candidate) | An unhandled duplicate key on WRITE ends the task in an abend. | Undecided. | As above. | not approved | Any process that retries or reconciles after the abend. Unknown. | `app/cbl/PROGW.cbl:7-10`, inference |
| DR-3 (candidate) | The record is written with whatever bytes the working storage holds when the key and balance are not set. | Undecided. A typed record could not hold uninitialized bytes. | The source does not set either field. | not approved | The bytes other programs read. Unknown. | `app/cbl/PROGW.cbl:4-9`, inference |

## Exit bar per wave

A wave is done when all of these hold. Not when the port compiles, and not when it passes tests written alongside the port.

1. The replay diff is clean, modulo the normalization spec and the Deviation Register.
2. Every targeted case above passes.
3. The harness is under version control and runs in CI.
4. The Deviation Register is signed by someone with the authority to sign it.

For wave 2 add: the order against the nightly batch cycle has been replayed and passes. It cannot be closed until the batch source is supplied.

## Keep the harness after cutover

The comparison harness becomes the regression suite for the new system. Budget to maintain it. It is the only executable specification this system will have.

## What to ask the client to supply

1. A snapshot of the ACCTDAT KSDS (a REPRO or export) and its cluster definition (key offset and length, record size, share options, recovery and logging).
2. CICS journals or transaction logs for TRNR and TRNW covering at least one month end and one fiscal year end, and the SMF or CICS statistics for the last 12 months (this doubles as telemetry for `05-dead-code.md`).
3. The source, JCL, procs and scheduler definitions of the nightly batch cycle, and its job logs and output generations (GDG) for at least a month.
4. Reports and extracts that the batch cycle or the transactions produced and the business kept.
5. The installed CSD definition for ACCTDAT, TRNR and TRNW in production.
