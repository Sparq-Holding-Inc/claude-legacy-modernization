# 06 Test strategy

The skill for this file is `behavioral-equivalence`. The bar is not that the port passes tests. The bar is that for the inputs this system actually sees, the new implementation produces the same outputs as the old one, and that every difference was decided on purpose and written down.

## What the tree gives us and what it does not

There are no datasets in the tree that hold production outputs. What it holds are seeds, meaning inputs and starting state:

- Sample ASCII files: 300 daily transactions and the master seed files (`app/data/ASCII/dailytran.txt:1`, `app/data/ASCII/acctdata.txt:1`, `app/data/ASCII/cardxref.txt:1`).
- The same data in EBCDIC form, one file per dataset, for example `AWS.M2.CARDDEMO.DALYTRAN.PS` under `app/data/EBCDIC`.
- The loaders that turn the seeds into the masters (`app/jcl/ACCTFILE.jcl:61`, `app/jcl/TRANFILE.jcl:74`).

Seeds allow characterization tests: run the legacy programs on them and record what comes out. That is the weakest oracle in the ladder, because it records what the code does, not what the business needed. Label every test built this way provisional. The oracle has to come from the client's job output, logs and reports, and from archived generations. Section "What to ask the client to supply" says what to ask for.

## Oracle per wave

| Wave | Oracle, strongest available | Fallback | What the harness compares | Evidence |
|---|---|---|---|---|
| 1. Read-only extracts | Archived output of READACCT, READCARD, READCUST, READXREF (golden master) | Seed files run through the legacy programs | Job output and the three CBACT01C output datasets | `app/jcl/READACCT.jcl:32` |
| 2. Transaction report | Archived TRANREPT generations (golden master, byte compare) | Legacy run on the seed daily file | The 133 byte report lines and the three total lines | `app/jcl/TRANREPT.jcl:80`, `app/cbl/CBTRN03C.cbl:51` |
| 3. Master refresh | Parallel run: load the same flat file with legacy and new, diff the loaded files | Seed files | Full record content and key order of each loaded master | `app/jcl/ACCTFILE.jcl:56` |
| 4. Daily posting | Parallel run on a copy of the masters, fed the real daily file. Second choice: replay a captured daily file and its archived masters | Seed daily file against seed masters | The three masters after posting, the reject generation, the return code, the job log counters | `app/jcl/POSTTRAN.jcl:28`, `app/jcl/POSTTRAN.jcl:38` |
| 5. Online inquiry and sign-on | Captured CICS transaction logs replayed as screen inputs | Scripted sessions on the seed masters | Screen output per input, the COMMAREA passed on each transfer | `app/cbl/COMEN01C.cbl:156` |
| 6. Online maintenance | Captured CICS transaction logs, replayed on a masters copy | Scripted sessions | Record changes in the masters after each transaction, and the messages shown | `app/cbl/COACTUPC.cbl:573` |
| 7. Month end | Parallel run through a real month end. The capture window must include month end and fiscal year end | Archived statements and SYSTRAN generations | Statements (text and HTML), interest transactions, the account master after interest | `app/jcl/CREASTMT.JCL:79`, `app/jcl/INTCALC.jcl:22` |
| 8. Authorization, transaction type | Captured MQ traffic and IMS unloads | Not assessed | Reply messages and the unloaded databases | inference |

Ask whether a parallel run is possible for waves 3, 4 and 7 before accepting anything weaker. The legacy system stays up during the whole plan, so it probably is.

## Normalization spec

Every row is a small assertion that a difference does not matter. Each is a place a real bug can hide. Keep the list short and have a person sign it off.

| Item | Rule | Why it may be ignored | Evidence |
|---|---|---|---|
| Processing timestamp on posted transactions | Ignore `TRAN-PROC-TS` on posted records. Compare only its date portion. | Set from the run clock at post time | `app/cbl/CBTRN02C.cbl:693` |
| Interest transaction timestamps | Ignore `TRAN-ORIG-TS` and `TRAN-PROC-TS` on system-made records. | Same clock call | `app/cbl/CBACT04C.cbl:497`, `app/cbl/CBACT04C.cbl:498` |
| Generation numbers and job ids | Compare generation content, not names like `(+1)`. Ignore job numbers and SYSOUT page headers. | Assigned by the system | `app/jcl/POSTTRAN.jcl:38` |
| Record padding | Compare fixed-width records after right-trimming spaces in text fields only. Compare low-values as data. | Padding differs by platform. Low-values may carry meaning. | `app/cpy/CVACT01Y.cpy:17` |
| Report page length | Keep it. Page size 20 lines is part of the output. | Not ignorable. | `app/cbl/CBTRN03C.cbl:131` |
| Order of records | Keep the legacy order. Key order for KSDS reads. Card number then key for the report sort. | Downstream consumers may depend on it | `app/jcl/TRANREPT.jcl:46` |
| Money | Zero tolerance. Compare as decimal with the same scale (2 places). | Any difference is a defect | `app/cpy/CVTRA05Y.cpy:10`, `app/cpy/CVACT01Y.cpy:7` |

## Traps to test on purpose

- **Zoned decimal money.** The master files hold money as signed zoned decimal, not packed, for example `S9(09)V99` in the transaction record (`app/cpy/CVTRA05Y.cpy:10`) and `S9(10)V99` in the account record (`app/cpy/CVACT01Y.cpy:7`). The sign is overpunched in the last digit. Packed decimal is used in the export file (`app/cpy/CVEXPORT.cpy:50`) and in counters. Port to a decimal type, never to floating point.
- **Truncation.** Interest is computed without ROUNDED (`app/cbl/CBACT04C.cbl:464`). A port that rounds gives a different cent.
- **Sign logic.** Posting adds a non-negative amount to the cycle credit and a negative one to the cycle debit (`app/cbl/CBTRN02C.cbl:548`, `app/cbl/CBTRN02C.cbl:549`, `app/cbl/CBTRN02C.cbl:551`). Test zero.
- **Collating sequence.** The KSDS keys are character fields. A KSDS reads in EBCDIC key order, and the report sorts card numbers as zoned decimal (`app/jcl/TRANREPT.jcl:41`). A port that sorts in ASCII changes the order of any key that mixes letters and digits. The sample transaction ids are all digits, so the seed data will not show this. Ask for real ids.
- **REDEFINES.** The online card update redefines the card number, CVV and expiry for numeric edits (`app/cbl/COCRDUPC.cbl:93`, `app/cbl/COCRDUPC.cbl:111`). The report launcher redefines its JCL text as an array of lines (`app/cbl/CORPT00C.cbl:126`). Test every branch that reads either view.
- **Job order.** The temporal edges in `graph.json` are the orders to keep. The four disagreeing orders in `02-coupling.md` are the first thing to resolve. The harness must run the accepted order and fail if a step starts before the step it reads from has finished.
- **Date strings.** Expiry is compared as text (`app/cbl/CBTRN02C.cbl:414`). The date parts in the report filter are text too (`app/cbl/CBTRN03C.cbl:173`). A port that parses dates may change the result on malformed dates.

## Cases to add beyond replay

Replay covers the common path. These are the dangerous ones.

| Case | Why | Evidence |
|---|---|---|
| Card number not in the cross-reference (reject 100) | The daily file can hold cards the master lacks | `app/cbl/CBTRN02C.cbl:385` |
| Account missing for a valid card (reject 101) | Master out of step with the cross-reference | `app/cbl/CBTRN02C.cbl:397` |
| Amount over the limit, equal to the limit, and one cent under (reject 102) | The test is `>=` on a computed balance | `app/cbl/CBTRN02C.cbl:407` |
| Transaction dated after account expiry (reject 103) | String compare on the first 10 characters | `app/cbl/CBTRN02C.cbl:414` |
| A transaction that is both over the limit and expired | The later code overwrites the earlier one, so only 103 is recorded | `app/cbl/CBTRN02C.cbl:410`, `app/cbl/CBTRN02C.cbl:417` |
| First transaction for an account and category | The category balance record is created, not updated | `app/cbl/CBTRN02C.cbl:495` |
| Zero-record daily file | Return code and empty reject generation | `app/cbl/CBTRN02C.cbl:229` |
| Reject count above zero | The job ends with return code 4. No script in the tree checks it. | `app/cbl/CBTRN02C.cbl:230` |
| Duplicate transaction id in the daily file | The write fails and the program abends after earlier records are already posted | `app/cbl/CBTRN02C.cbl:566`, `app/cbl/CBTRN02C.cbl:577` |
| Report over an empty window, one record, and a page-boundary count | The end-of-file total lines behave differently at each | `app/cbl/CBTRN03C.cbl:200`, `app/cbl/CBTRN03C.cbl:282` |
| Interest for the last account read, and for an account with no rate | The last account is not updated, and the default group is the fallback | `app/cbl/CBACT04C.cbl:220`, `app/cbl/CBACT04C.cbl:437` |
| Month end, quarter end, fiscal year end, leap day | Interest and statement runs | `app/jcl/INTCALC.jcl:22` |
| A file at the maximum the old cluster allows | The transaction master is defined with 1 primary and 5 secondary cylinders | `app/jcl/TRANBKP.jcl:55` |
| Bad data already in the masters | A port must reproduce the legacy behavior on it, which may be neither an error nor a sane result | inference |
| A rerun of POSTTRAN after a partial run | There is no restart step. The rerun posts the same records again | `app/jcl/POSTTRAN.jcl:23` |

## Deviation register

Nothing gets to differ without a row here. These rows are seeded from what I found in the code. Approval is pending on every one. No row is decided.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact |
|---|---|---|---|---|---|
| D-001 | At end of file the report adds the last amount again to the page total and the grand total (`app/cbl/CBTRN03C.cbl:200`, `app/cbl/CBTRN03C.cbl:203`) | Proposed: count each transaction once. Undecided. | The printed totals disagree with the detail lines by one amount | pending | Anyone who reconciles the report totals |
| D-002 | The total for the last account is never written, because the total is written only when the card number changes (`app/cbl/CBTRN03C.cbl:183`) | Proposed: write it. Undecided. | Missing line | pending | Same |
| D-003 | When a transaction fails more than one check, the later code overwrites the earlier one (`app/cbl/CBTRN02C.cbl:410`, `app/cbl/CBTRN02C.cbl:417`) | Proposed: record all reasons. Undecided. | Reject file hides a reason | pending | Whoever works the reject file |
| D-004 | If the account rewrite fails, code 109 is set and nothing acts on it. The transaction file is written anyway (`app/cbl/CBTRN02C.cbl:554`, `app/cbl/CBTRN02C.cbl:556`) | Proposed: treat as a failure. Undecided. | Silent loss of a balance update | pending | Balance and transaction master disagree |
| D-005 | The last account read has no interest applied to its balance (`app/cbl/CBACT04C.cbl:220`) | Proposed: apply it. Undecided. | Paragraph is on a branch the loop cannot reach | pending | One account's balance each month |
| D-006 | Interest truncates to the cent (`app/cbl/CBACT04C.cbl:464`) | Proposed: keep truncation and test it. | Any change moves every interest cent | pending | All interest |
| D-007 | The interest run date is fixed in the JCL and the report window is fixed at 2022-01-01 to 2022-07-06 (`app/jcl/INTCALC.jcl:22`, `app/jcl/TRANREPT.jcl:43`, `app/jcl/TRANREPT.jcl:44`) | Proposed: take dates as parameters, as the online route already does (`app/cbl/CORPT00C.cbl:220`). | A fixed date repeats the same transaction id prefix every month | pending | Transaction key uniqueness, report window |
| D-008 | The report program displays each full transaction record, with its card number, to the job log (`app/cbl/CBTRN03C.cbl:180`). The interest program displays each category balance record (`app/cbl/CBACT04C.cbl:193`). | Proposed: remove the card number from logs. | Card numbers in job output | pending | Log retention, audit |
| D-009 | Sign-on compares a clear-text password (`app/cbl/COSGN00C.cbl:223`), user maintenance stores it as typed (`app/cbl/COUSR01C.cbl:157`) and the seed job carries default users (`app/jcl/DUSRSECJ.jcl:35`) | New: a real authentication mechanism. | Clear-text credentials | pending | Every online user |
| D-010 | Online screens take the highest key plus one as the new transaction id (`app/cbl/COBIL00C.cbl:212`, `app/cbl/COTRN02C.cbl:444`) | Proposed: one key scheme for all writers. | Two sessions can collide | pending | Transaction master keys, the alternate index |
| D-011 | Batch closes CICS files by name in five jobs, against a fixed region (`app/jcl/CLOSEFIL.jcl:26`, `app/jcl/CARDFILE.jcl:26`, `app/jcl/CUSTFILE.jcl:26`, `app/jcl/TRANFILE.jcl:26`) | New: locking in the target, no console commands. | Region name is hard-coded in several places | pending | Batch window |
| D-012 | The report stops at the first record outside its date window, because NEXT SENTENCE leaves the loop (`app/cbl/CBTRN03C.cbl:177`). The SORT step removes such records beforehand, so the job never shows it. | Proposed: filter, do not stop. | Program is right only because of an earlier step | pending | Only if the SORT step is dropped |

## Exit bar per wave

A wave is done when all of these hold. Not when the port compiles. Not when it passes the tests the porter wrote alongside it, because those encode the porter's understanding, which is what is under test.

| Wave | Replay diff | Boundary cases | Deviation register | Evidence |
|---|---|---|---|---|
| 1 | Clean on the archived outputs, modulo the normalization spec | Empty file and largest file | Signed | inference |
| 2 | Byte-clean report on at least 13 archived generations | Empty window, page boundary, D-001 and D-002 decided | Signed | `app/cbl/CBTRN03C.cbl:200` |
| 3 | State diff of each loaded master, then a clean wave 4 shadow run seeded from it | Failed load leaves the old master intact | Signed | `app/jcl/ACCTFILE.jcl:25` |
| 4 | Shadow posting matches the legacy masters and reject file on a full month of daily files | All reject codes, first-of-category, duplicate id, rerun | Signed, D-003 and D-004 decided | `app/cbl/CBTRN02C.cbl:410` |
| 5 | Screen replay clean, router sends every entry to the intended screen | Every menu option in both tables | Signed, D-009 decided | `app/cpy/COMEN02Y.cpy:28` |
| 6 | Post-transaction master state identical to legacy for the replayed sessions | Concurrent add with two sessions, expiry date entry, card edit | Signed, D-010 decided | `app/cbl/COBIL00C.cbl:212` |
| 7 | Shadow month end and fiscal year end clean | Last account, no-rate account, leap day, D-005 to D-007 decided | Signed | `app/cbl/CBACT04C.cbl:220` |
| 8 | To be set by an IMS, DB2 and MQ specialist | | | inference |

In every wave the harness is under version control and runs in CI, and someone with authority to sign signs the register.

## Keep the harness after cutover

The comparison harness becomes the regression suite for the modernized system. Budget for maintaining it. The generation archive reader, the normalizer, and the replay driver are the only executable specification this system will ever have.

## What to ask the client to supply

Because the tree holds no output, the oracle depends on these. The list is also the top of the open questions in `00-summary.md`.

1. At least 13 months of archived generations: TRANREPT, DALYREJS, SYSTRAN, TRANSACT.BKUP, TRANSACT.COMBINED (`app/jcl/TRANREPT.jcl:80`, `app/jcl/POSTTRAN.jcl:38`, `app/jcl/INTCALC.jcl:41`, `app/jcl/COMBTRAN.jcl:37`).
2. Job logs or SMF records for the daily, weekly and monthly cycles, with return codes and elapsed times.
3. The real daily transaction file that POSTTRAN reads, and the job or feed that produces it (`app/jcl/POSTTRAN.jcl:31`). Nothing in the tree writes it.
4. The DATEPARM dataset that the batch report reads (`app/proc/TRANREPT.prc:72`). Nothing in the tree writes it.
5. Archived statements, text and HTML, for two month ends.
6. CICS transaction logs or journals covering the online screens for one full month.
7. The REXX exec for PDF conversion (`app/jcl/TXT2PDF1.JCL:31`).
8. Any partner extracts sent outside the building. Whatever left is an executable specification of the format.
