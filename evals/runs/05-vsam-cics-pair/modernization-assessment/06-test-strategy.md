# Test strategy

The tree holds no datasets, no JCL and no archived outputs. The only data definition is the CSD file entry (app/csd/DEMO.CSD:1). The oracle has to come from the client.

## Oracle per wave

| Wave | Oracle | Strength | Needs from the client | Evidence |
|---|---|---|---|---|
| 1 (PROGR, TRNR) | Golden master: a production extract of ACCTDAT plus the screen or COMMAREA output the legacy PROGR returns for each key. Fall back to a CICS journal replay of TRNR. | strong if the extract exists; otherwise provisional | An ACCTDAT extract, key list, and TRNR transaction logs | app/cbl/PROGR.cbl:7, app/csd/DEMO.CSD:6 |
| 2 (PROGW, TRNW) | Parallel run if the legacy region can stay up. Otherwise replay of TRNW inputs from CICS journals, then byte-compare the resulting KSDS records. | strong with parallel run | TRNW input captures, a before and after KSDS snapshot | app/cbl/PROGW.cbl:7, app/csd/DEMO.CSD:4 |

Characterization tests generated from the source are the weakest option. With programs this small they would only restate the two CICS calls. Label any coverage built that way provisional (inference).

## Must-not-break: "the nightly batch cycle"

**This item maps to no unit in the tree.** There is no JCL, proc, scheduler, or batch program (modernization-assessment/graph.json:25). Both entry points are online transactions (app/csd/DEMO.CSD:4, app/csd/DEMO.CSD:6). I have not invented a mapping. If the batch cycle reads or loads ACCTDAT, it is a third user of the layout in app/cpy/ACCTREC.cpy and needs its own anchor in wave 2. The oracle for that is archived batch outputs (GDG generations, reports, partner extracts) and job logs. The client must supply them.

## Normalization spec (for a human to sign)

| Item | Rule | Evidence |
|---|---|---|
| ACCT-BAL | Compare as decimal with scale 2, zero tolerance. Never a float. Compare raw packed bytes too, including the sign nibble (C, D or F). | app/cpy/ACCTREC.cpy:3 |
| ACCT-ID | Compare as an 11-digit zoned field. Keep leading zeros. | app/cpy/ACCTREC.cpy:2 |
| KSDS order | Keep key order. EBCDIC and ASCII sort differently, and the key is numeric display. Confirm no consumer depends on the order. | app/cbl/PROGR.cbl:9 |
| Timestamps, task numbers | Ignore. None are in the record. | app/cpy/ACCTREC.cpy:1 |
| Padding | The record has no filler, so compare byte for byte. | app/cpy/ACCTREC.cpy:1 |

## Targeted cases

- Balance boundaries: zero, negative zero, maximum 999999999.99, minimum negative, and a record with an invalid sign nibble already in the file (bad data that is already there).
- Account IDs: 00000000000, 99999999999, and a key that is absent. Neither program checks a response code (app/cbl/PROGR.cbl:7, app/cbl/PROGW.cbl:7), so the legacy behavior on NOTFND and DUPREC is an abend. The port must reproduce it or record a deviation.
- Write then read: a TRNW followed by a TRNR for the same key must round-trip across the old and new implementations in both orders. This is the contract edge (modernization-assessment/graph.json:92).
- Fiscal close: ask whether any path runs only at month-end or year-end. None is visible here.

## Exit bar

Wave 1 is done when the replay diff of TRNR is clean modulo the spec above, every balance and key case passes, and the harness runs in CI. Wave 2 adds the round-trip cases and a reconcile of KSDS contents after the cutover rehearsal. The deviation register is signed by someone who can sign it. The harness is kept after cutover as the regression suite.

## Deviation register

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| none yet | none yet | none yet | none yet | none yet | none yet | inference |
