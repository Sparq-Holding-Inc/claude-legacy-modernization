# 06 Test strategy

The bar: for the inputs this system sees, the new code writes and returns the same records as the old code. Where it differs, someone decided that and wrote it down.

## Where the oracle comes from

The tree holds no data, no job output, no logs and no reports. It names one file, SPARQ.TEST.ACCTDAT.KSDS (`app/csd/DEMO.CSD:2`), but holds no copy of it. The oracle has to come from the client. Ask for these, in this order:

1. A parallel run: the same TRNW and TRNR inputs sent to old and new code against copies of the same file. Ask whether the old system can stay up for this. Teams often assume it cannot.
2. Captured TRNR and TRNW traffic from CICS journals or transaction logs, over a window that includes month end and fiscal year end.
3. Archived outputs: prior generations of any report, extract or statement built from the ACCTDAT file, and above all what the nightly batch cycle produces. The batch is the item that must not break, and its archived outputs are golden masters.
4. Unloads of the ACCTDAT file taken at known times, and SMF or CICS statistics for TRNR and TRNW. These also fill the telemetry gap in `05-dead-code.md`.

If none arrives, the fallback is characterization tests generated from the two programs. That is the weakest oracle and every result is provisional. It would only prove what the source says, and the source does not say where the key or record comes from (`app/cbl/PROGR.cbl:6-11`, `app/cbl/PROGW.cbl:6-11`).

## Oracle by wave

| Wave | Oracle | What is compared | Provisional | Evidence |
|---|---|---|---|---|
| 1. PROGR | Captured TRNR traffic replayed against a snapshot of the file | the record returned for each key, decoded field by field, and the response for a missing key | no, if traffic is supplied | `app/cbl/PROGR.cbl:7-10` |
| 2. PROGW | Parallel run on copies of the file, with archived batch outputs as a second check | the whole file after the run, decoded, and the response for a duplicate key | yes, until the batch is seen | `app/cbl/PROGW.cbl:7-10` |

## Normalization spec (each line needs a human sign off)

- **Packed decimal.** ACCT-BAL is COMP-3, S9(9)V99 (`app/cpy/ACCTREC.cpy:3`). Compare decoded values in a decimal type, with zero tolerance. Compare the sign nibble on its own, because a different sign nibble (C or F for positive) may matter to a batch reader. That is inference.
- **Collating sequence.** The key is 11 digits in display form (`app/cpy/ACCTREC.cpy:2`). Digits sort the same way in EBCDIC and ASCII, so key order should not change. This holds only if every key is all digits. Bad data with letters or spaces would sort differently. That is inference. Test it with the real file.
- **REDEFINES.** ACCTREC has none (`app/cpy/ACCTREC.cpy:1-3`). Nothing to branch on.
- **Padding and low values.** Decide whether a key of spaces or binary zeros matters. Neither program sets the key or the record (`app/cbl/PROGR.cbl:6-11`, `app/cbl/PROGW.cbl:6-11`), so the value they use at run time comes from storage the source does not fill.
- **Record length.** The layout adds to 17 bytes (inference from `app/cpy/ACCTREC.cpy:2-3`). No file definition with a record length is in the tree, and the extractor does not compare lengths (`modernization-assessment/graph.json:20`). Confirm the length with the client.
- **Record ordering.** Compare the file in key order. Ask whether any batch reader depends on it.
- **Job order.** No temporal edges exist in the tree, because no scheduler or JCL was seen (`modernization-assessment/graph.json:30`). Get the batch order from the client. Ask too whether CICS closes the file during the batch window. Both are open questions.
- **Timestamps and run ids.** The record has none (`app/cpy/ACCTREC.cpy:2-3`). Nothing to normalize there.

## Cases to add on purpose

- Missing key on TRNR, and a duplicate key on TRNW. Neither program tests a response code (`app/cbl/PROGR.cbl:7-10`, `app/cbl/PROGW.cbl:7-10`). By default an unhandled CICS condition ends the task abnormally. That is inference, so record what the old system actually does.
- The balance limits: the largest and smallest values the field holds, zero, and a negative balance (`app/cpy/ACCTREC.cpy:3`).
- Bad data already in the file: keys that are not all digits, a balance with an invalid packed sign or digit.
- The empty file and the largest file the old system holds.
- Month end, quarter end, fiscal year end, leap day. Which days matter depends on the batch cycle, which is not in the tree.
- Whatever runs only at fiscal close. Ask the client. The tree cannot say.

## Deviation Register

Nothing may differ without a row. One candidate is open from the start.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| D-1 | Both programs use ACCT-ID as the key without setting it, so the key is whatever storage holds | To be decided. Either reproduce the legacy value or reject the request. | The source may be a stub. The client must say. | pending | unknown | `app/cbl/PROGR.cbl:9`, `app/cbl/PROGW.cbl:9` |

## Exit bar per wave

A wave is done when the replay diff is clean apart from the normalization spec and the register, every case above passes, the harness is under version control and runs in CI, and someone with the authority has signed the register. It is not done when the port compiles. Keep the harness after cutover. It becomes the regression suite, and it is the only executable specification this system has.
