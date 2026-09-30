# 06 Test strategy

"It passes the tests" is not the bar here, because the legacy system has none. The bar is this: for the inputs the system actually sees, the new implementation produces the same outputs as the old one, and where it does not, someone decided that on purpose and wrote it down in the deviation register below.

## What the tree gives us as an oracle

The tree holds inputs and no expected outputs.

- Sample inputs exist in two forms: 300 daily transactions and 50 records each of accounts, cards, cross references, customers and category balances, as ASCII text and as EBCDIC files (`app/data/ASCII/dailytran.txt:1`, `app/data/ASCII/acctdata.txt:1`, `app/data/EBCDIC/AWS.M2.CARDDEMO.DALYTRAN.PS:1`). Money in the ASCII text carries a trailing sign overpunch, for example a positive amount ending in a letter and a negative amount ending in a closing brace.
- No archived outputs are in the tree: no generation of the transaction backup, the rejects file, the report, the statements or the interest transactions. The generation groups that would hold them keep only five generations each (`app/jcl/DEFGDGB.jcl:25`, `app/jcl/DEFGDGB.jcl:26`), so anything older was archived elsewhere or is gone.
- Running the legacy programs on the sample inputs would give a characterization oracle, which is the weakest of the four and is provisional. It encodes what the code says.

What I would ask the client to supply, in this order:

1. Thirteen months of daily posting input files (DALYTRAN) with the masters, rejects and transaction master each run produced. This covers a month end and a year end, and makes parallel run and replay possible (`app/jcl/POSTTRAN.jcl:30`).
2. The archived generations of TRANREPT, TRANSACT.BKUP, SYSTRAN, COMBINED, DALYREJS and TCATBALF.BKUP, and where anything older than five generations went (`app/jcl/TRANREPT.jcl:80`, `app/jcl/TRANBKP.jcl:33`).
3. Job logs, return codes and scheduler run history for the daily, weekly and monthly chains. The CA-7 listing shows 1058 runs of CLOSEFIL, so history exists (`app/scheduler/CardDemo.ca7:24`).
4. Whatever left the building: the branch migration EXPORT file consumers and the statement files (`app/cbl/CBEXPORT.cbl:8`).
5. CICS journals or transaction logs for the online writers, for replay (`app/cbl/COBIL00C.cbl:233`).
6. The MQ traffic capture for COACCT01 and COPAUA0C, if wave 7 is in scope.

## Oracle per wave

Different waves use different oracles. The strongest available is chosen first.

| Wave | Oracle | Boundary compared | Evidence |
|---|---|---|---|
| 1 | Parallel run. Both implementations read the same master snapshot | Read-back listing and return code | `app/jcl/READCARD.jcl:22` |
| 2 | Parallel run on a snapshot, plus a CBEXPORT to CBIMPORT round trip | The three CBACT01C outputs and EXPORT.DATA, byte for byte | `app/jcl/READACCT.jcl:32`, `app/cbl/CBEXPORT.cbl:65` |
| 3 | Replay of captured screen and COMMAREA transcripts, and a golden master of the user file, the Db2 rows and TRANTYPE.PS | Per option transcripts, records and rows | `app/cbl/COMEN01C.cbl:156`, `app/app-transaction-type-db2/jcl/TRANEXTR.jcl:76` |
| 4 | Golden master from archived TRANREPT generations, then parallel run on a copy of the transaction backup | The report text, and the JCL text CORPT00C writes to the queue | `app/jcl/TRANREPT.jcl:80`, `app/cbl/CORPT00C.cbl:517` |
| 5 | Golden master from archived statements, then parallel run | The statement text and HTML files | `app/jcl/CREASTMT.JCL:79` |
| 6 | Parallel run of posting and of the month-end chain, on copies of the masters; replay of journals for the online writers | Masters, rejects file, category balances, interest transactions and the rebuilt transaction master after each run | `app/jcl/POSTTRAN.jcl:23`, `app/jcl/INTCALC.jcl:22`, `app/jcl/COMBTRAN.jcl:23` |
| 7 | Replay of MQ traffic, plus IMS unload and load comparison | Message pairs and unloaded segments | `app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:35`, `app/app-authorization-ims-db2-mq/jcl/UNLDPADB.JCL:39` |

Ask whether a parallel run is possible for wave 6 before settling for less. Posting is a file in and files out, so it can run on a copy without the legacy system going down. Teams often assume it cannot.

## Normalization spec

Every entry here asserts that a difference does not matter, and each is a place a real bug can hide. A person with authority signs the list.

| Item | Rule | Why | Evidence |
|---|---|---|---|
| Processed and original timestamps on rows the run creates | Mask the value, and assert the format and that it lies inside the run window | The program stamps the current time | `app/cbl/CBTRN02C.cbl:437`, `app/cbl/CBACT04C.cbl:496` |
| Generation numbers, job numbers and run dates in dataset names | Compare by generation order, not by name | GDG names carry the date | `app/jcl/POSTTRAN.jcl:38` |
| Money | Compare as decimal with zero tolerance, never as floating point. Decode the sign overpunch. Prefer byte equality of the zoned field | The fields are S9(9)V99 and S9(10)V99 in display form, and a float port adds rounding defects that are real | `app/cpy/CVTRA05Y.cpy:10`, `app/cpy/CVACT01Y.cpy:7` |
| Interest | Truncate, do not round, to two places | The COMPUTE has no ROUNDED clause | `app/cbl/CBACT04C.cbl:464` |
| Balance overflow | Reproduce the silent truncation of high-order digits, or record it as a deviation | The validation field is 9 integer digits and the account balance is 10, with no SIZE ERROR | `app/cbl/CBTRN02C.cbl:187`, `app/cbl/CBTRN02C.cbl:403` |
| Key order | Compare against the order a KSDS browse returns, not the target language's sort | EBCDIC puts letters before digits. Keys that mix them, such as the account group id and the user id, order differently in ASCII | `app/cpy/CVTRA02Y.cpy:6`, `app/cpy/CSUSR01Y.cpy:18` |
| Padding of type records | Decide whether zero fill or space fill counts. The Db2 unload pads with zeros where the copybook filler is spaces | The bytes differ and downstream reads the same 60 bytes | `app/app-transaction-type-db2/jcl/TRANEXTR.jcl:80`, `app/cpy/CVTRA03Y.cpy:7` |
| DISPLAY output | Do not diff it. Assert the processed and rejected counts and the return code only | Programs DISPLAY every record, which is a log, not an output | `app/cbl/CBTRN03C.cbl:180`, `app/cbl/CBTRN02C.cbl:227` |
| Return codes | Assert equal. Posting sets 4 when any record is rejected | Scheduler conditions read it | `app/cbl/CBTRN02C.cbl:230` |
| Current date | Inject a clock. Do not mask | The online report computes its date ranges from it | `app/cbl/CORPT00C.cbl:215` |

Keep this list short. Anything not on it is compared exactly.

## Targeted cases

Production replay covers the common path well and the dangerous paths badly. Add these.

| Case | Why | Evidence |
|---|---|---|
| Amount that makes the credit limit test exactly equal | The test is greater than or equal | `app/cbl/CBTRN02C.cbl:407` |
| A record that is both over the limit and after account expiry | The second reason overwrites the first, so the reject file says 103, not 102 | `app/cbl/CBTRN02C.cbl:410`, `app/cbl/CBTRN02C.cbl:417` |
| Expiry date equal to the transaction date | The comparison is on the first ten characters as text | `app/cbl/CBTRN02C.cbl:414` |
| Unknown card, account not found, and a category balance row that does not exist yet | Reject reasons 100 and 101, and the create branch of the balance update | `app/cbl/CBTRN02C.cbl:385`, `app/cbl/CBTRN02C.cbl:397`, `app/cbl/CBTRN02C.cbl:503` |
| Account REWRITE that reports a bad key after the transaction is posted | Reason 109 is set and nothing rejects the row | `app/cbl/CBTRN02C.cbl:556` |
| Zero-record daily file, and a file at the largest size the old system took | The empty and the enormous | `app/cbl/CBTRN02C.cbl:202` |
| Negative amounts, including the closing-brace overpunch | Credit and debit cycle totals split on the sign | `app/cbl/CBTRN02C.cbl:548` |
| Interest rate of zero, a missing group falling back to DEFAULT, and an account whose group id is blank after an online update | The last is the private layout in COACTUPC | `app/cbl/CBACT04C.cbl:214`, `app/cbl/CBACT04C.cbl:436`, `app/cbl/COACTUPC.cbl:432` |
| The final account at end of file | It is updated in the loop's else branch | `app/cbl/CBACT04C.cbl:220` |
| Balance times rate with a fractional cent | Truncation against rounding | `app/cbl/CBACT04C.cbl:464` |
| Report with no matching records, one transaction, and a page boundary exactly at 20 lines | Page size is 20 and totals count as lines | `app/cbl/CBTRN03C.cbl:131`, `app/cbl/CBTRN03C.cbl:282` |
| Report input with a record outside the date range | NEXT SENTENCE ends the read loop | `app/cbl/CBTRN03C.cbl:177` |
| Report last record at end of file | Its amount appears to be added to the page total a second time | `app/cbl/CBTRN03C.cbl:198` |
| Monthly report run in December and on the last day of February, and the yearly report | The month end is computed by date arithmetic | `app/cbl/CORPT00C.cbl:225`, `app/cbl/CORPT00C.cbl:230` |
| Batch report with its date symbols against the online report's | Two paths, two parameter sources | `app/jcl/TRANREPT.jcl:43`, `app/cbl/CORPT00C.cbl:220` |
| Refresh input with a duplicate key, and one out of order | The IDCAMS REPRO behavior is the oracle | `app/jcl/ACCTFILE.jcl:61` |
| Alternate index rebuilt at the byte offsets in the control cards | The offsets restate the layouts | `app/jcl/CARDFILE.jcl:85`, `app/jcl/XREFFILE.jcl:74`, `app/jcl/TRANFILE.jcl:84` |
| Backup step forced to return code 8, then the delete step | Legacy deletes the master anyway | `app/jcl/TRANBKP.jcl:37` |
| Two users adding a transaction or paying a bill at the same moment | The next id is the highest key plus one, with no lock in the program (inference) | `app/cbl/COBIL00C.cbl:212`, `app/cbl/COTRN02C.cbl:444` |
| An id generated by interest against an id from the daily file | Three schemes share one key space (inference) | `app/cbl/CBACT04C.cbl:476`, `app/cbl/COBIL00C.cbl:217` |
| Paths that run only at month end | The interest and merge chain is the fiscal close | `app/jcl/INTCALC.jcl:22`, `app/jcl/COMBTRAN.jcl:23` |
| Statement input with more than 10 transactions on a card and more than 51 cards | The in-storage table is 51 by 10 | `app/cbl/CBSTM03A.CBL:226` |

## Orders the harness must keep

The temporal edges in `graph.json` are the list. The three schedule sources disagree, so the first job of the harness is to make the client say which is production.

| Chain | Order | Evidence |
|---|---|---|
| Shell wrapper, posting | CLOSEFIL, ACCTFILE, TCATBALF, TRANBKP, POSTTRAN, TRANIDX, OPENFIL | `scripts/run_posting.sh:13`, `scripts/run_posting.sh:26`, `scripts/run_posting.sh:34` |
| Shell wrapper, full batch | Refresh jobs, POSTTRAN, INTCALC, TRANBKP, COMBTRAN, TRANIDX, OPENFIL | `scripts/run_full_batch.sh:47`, `scripts/run_full_batch.sh:51`, `scripts/run_full_batch.sh:55`, `scripts/run_full_batch.sh:58` |
| Control-M, daily | CLOSEFIL, TRANBKP, WAITSTEP, OPENFIL | `app/scheduler/CardDemo.controlm:4`, `app/scheduler/CardDemo.controlm:8` |
| Control-M, monthly | CLOSEFIL, INTCALC, COMBTRAN, WAITSTEP, OPENFIL | `app/scheduler/CardDemo.controlm:66`, `app/scheduler/CardDemo.controlm:72` |
| CA-7, from the unparsed listing | CLOSEFIL, CBPAUP0J, POSTTRAN, WAITSTEP, OPENFIL | `app/scheduler/CardDemo.ca7:43`, `app/scheduler/CardDemo.ca7:70` |

## Deviation register

Nothing is allowed to differ from the legacy behavior without a row here. These are the candidates found so far. Every "New behavior" cell is open. The owner decides, and signs in "Approved by".

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| DR-1 | The online account update writes its group id into the ZIP position and blanks the group id position | Open. Recommend fix | The record loses a field and month-end interest changes for edited accounts | | CBACT04C reads the group id, so interest for edited accounts falls to DEFAULT rates | `app/cbl/COACTUPC.cbl:432`, `app/cpy/CVACT01Y.cpy:15`, `app/cbl/CBACT04C.cbl:436` |
| DR-2 | When a transaction fails two validations, the second reason replaces the first | Open | The reject file loses the over-limit reason | | Reject reports that read the reason code | `app/cbl/CBTRN02C.cbl:410`, `app/cbl/CBTRN02C.cbl:417` |
| DR-3 | A failed account REWRITE sets reason 109 after the posting, and the transaction is still written | Open. Recommend reject | The transaction is posted with no balance update | | Account balances and the transaction master disagree | `app/cbl/CBTRN02C.cbl:554`, `app/cbl/CBTRN02C.cbl:564` |
| DR-4 | The transaction master delete step runs even when the backup step failed | Open. Recommend stop on failure | History can be lost | | Every later job that reads the backup generations | `app/jcl/TRANBKP.jcl:37`, `app/jcl/TRANBKP.jcl:51` |
| DR-5 | The report may add the last transaction to the page and grand totals twice, and a record outside the date range ends the loop | Open. Recommend fix, after confirming on real data | The printed totals can be wrong with no error | | Anyone who reads the report totals | `app/cbl/CBTRN03C.cbl:177`, `app/cbl/CBTRN03C.cbl:198` |
| DR-6 | Interest is truncated to two places, never rounded | Open | The COMPUTE has no ROUNDED clause | | Every interest transaction, every month | `app/cbl/CBACT04C.cbl:464` |
| DR-7 | Passwords are stored and compared as eight clear characters | Open. Recommend hash | Security | | Sign-on and user maintenance, and the in-stream seed users | `app/cbl/COSGN00C.cbl:223`, `app/jcl/DUSRSECJ.jcl:35` |
| DR-8 | The next transaction id is the highest key plus one, read without a lock | Open. Recommend a sequence | Two users can be given the same id | | The transaction master key space that batch also writes | `app/cbl/COBIL00C.cbl:212`, `app/cbl/COTRN02C.cbl:444` |
| DR-9 | The batch report has a fixed 2022 date range in its JCL, and interest passes a fixed PARM date | Open | The report as shipped selects only 2022 rows, and interest ids repeat if the PARM does | | The batch report and the system transactions | `app/jcl/TRANREPT.jcl:43`, `app/jcl/INTCALC.jcl:22` |

## Exit bar for each wave

A wave is done when all of these hold. Not when the port compiles.

- The replay or parallel run diff is clean, modulo the normalization spec and the deviation register.
- Every targeted case for the wave passes, including the ones above that belong to it.
- The harness is under version control and runs in CI.
- The deviation register is signed by someone with the authority to sign it.
- For wave 6 only: the store cutover has its own go or no-go, because it is the one step that cannot be rolled back.

## Keep the harness after cutover

The comparison harness becomes the regression suite for the modernized system. Budget for its upkeep. It is the only executable specification this system has ever had.
