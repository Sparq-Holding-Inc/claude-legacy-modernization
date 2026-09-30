# 06 Test strategy: what "correct" means

The bar is not "the port compiles" or "it passes tests written with the port". For the inputs this system actually sees, the new implementation must produce the same outputs as the old one, and any difference must be a decision written in the Deviation Register.

The three must-not-break items are the anchors. Each has an oracle, a normalization spec and boundary cases below. Where they land in the wave plan is in `modernization-assessment/03-waves.md`.

## What the tree gives us as an oracle

The tree holds vendor sample data and a catalog listing. It holds no production input, no production output, no job log, no SMF record and no CICS journal.

| Source | What it is | Use | Confidence | Evidence |
|---|---|---|---|---|
| Sample daily transactions, 300 records, also as EBCDIC fixed 350 byte records | Vendor seed data with sign overpunch characters in the amount field. | Smoke tests and unit level cases for posting. Not a production oracle. | high | `app/data/ASCII/dailytran.txt:1`, `app/cpy/CVTRA05Y.cpy:10` |
| Sample masters: 50 accounts, cards, cross references and customers, 7 transaction types, 18 categories | Vendor seed data. | Seed state for parallel runs on a copy. | high | `app/data/ASCII/acctdata.txt:1`, `app/data/ASCII/carddata.txt:1` |
| Catalog listing dated 09/01/22 | Shows five generations of the report, the transaction backup and the reject file. Only the names, not the contents. | Proves generations existed. Says how many can still exist. | high | `app/catlg/LISTCAT.txt:1528`, `app/catlg/LISTCAT.txt:1537`, `app/catlg/LISTCAT.txt:1639`, `app/catlg/LISTCAT.txt:692` |
| GDG limits | The report, backup, reject and combined files keep 5 generations, and most scratch the oldest. Only the last five runs of each survive on disk. | The archive on disk is a week of dailies at most. Ask for tape or HSM archives for the fiscal cycle. | high | `app/catlg/LISTCAT.txt:1535`, `app/catlg/LISTCAT.txt:1637`, `app/jcl/DEFGDGB.jcl:25` |
| The unload jobs for IMS and DB2 | UNLDPADB, UNLDGSAM and TRANEXTR write flat files of the authorization and transaction type data. | Free comparison files for wave 7. | medium | `app/app-authorization-ims-db2-mq/jcl/UNLDPADB.JCL:38`, `app/app-transaction-type-db2/jcl/TRANEXTR.jcl:72` |

## What to ask the client for

1. One full business cycle of the real DALYTRAN.PS files, plus the account, card, cross reference and category balance masters before and after each posting run. The tree has no producer for DALYTRAN.PS (`app/jcl/POSTTRAN.jcl:30`).
2. The archive of the report, reject and transaction backup generations beyond the last five, including a month end and, for anything financial, a fiscal year end.
3. CICS journals or transaction logs and SMF job records for the last 12 months. These are the telemetry for `modernization-assessment/05-dead-code.md` and the captured inputs for replay.
4. Statements, partner extracts and regulatory reports that left the building, with dates.
5. The real schedule. The CA-7 listing is not parsed and the wrapper scripts disagree with each other (`app/scheduler/CardDemo.ca7:70`, `scripts/run_posting.sh:13`).

## Oracle per wave

| Wave | Oracle | Why | Provisional | Evidence |
|---|---|---|---|---|
| 1. Environment and utility jobs | Characterization: return codes and resulting catalog entries. | Nothing produces business data. | yes | `samples/jcl/LISTCAT.jcl:1`, inference |
| 2. Read-only batch extracts | Golden master from archived READACCT, READCARD, READCUST and READXREF output if the client has it. Else characterization on the sample masters. | The programs only display or extract. | yes until archives are supplied | `app/jcl/READACCT.jcl:1`, `app/cbl/CBACT01C.cbl:231` |
| 3. Sign-on, menu and read-only screens | Shadow traffic: replay the same terminal input to legacy and new and diff the screens. It is safe because nothing writes. Sign-on uses test users only. | Best oracle in the plan and the cheapest. | no, once a journal capture exists | `app/cbl/COSGN00C.cbl:223`, `app/cbl/COMEN01C.cbl:184` |
| 4. Build and reference-data backup jobs | None needed for the build jobs. DEFGDGD copies compare byte for byte. | Utility copies. | yes | `app/jcl/DEFGDGD.jcl:28` |
| 5. Batch window | Parallel run. Legacy and new posting process the same DALYTRAN.PS against copies of the same masters, and the results are diffed. For the report, golden master from the last five archived generations of TRANREPT, then a parallel run over a cycle. | Posting writes the system of record, so a replay against a copy is the only way to see a silent balance error. | no for posting once inputs exist, yes for the report until archives are supplied | `app/jcl/POSTTRAN.jcl:23`, `app/jcl/TRANREPT.jcl:80` |
| 6. Online updates | Captured production traffic replay against copies of the masters, diffing the master images afterward. | Online updates cannot be shadowed, because shadow writes would double-post. | yes until a journal is supplied | `app/cbl/COACTUPC.cbl:4066`, `app/cbl/COBIL00C.cbl:233` |
| 7. Authorization and transaction-type subsystems | Parallel run of the MQ traffic in shadow mode, and the IMS and DB2 unload files. | Authorization is real time and customer visible. | yes | `app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:35` |

## The three anchors

### Daily transaction posting (job POSTTRAN, program CBTRN02C)

Compare after a posting run, for the same input:

| What to compare | How | Evidence |
|---|---|---|
| Transaction master after the run | Every record, key by key. Ignore only the processed timestamp, which the program sets from the clock. | `app/cbl/CBTRN02C.cbl:437`, `app/cbl/CBTRN02C.cbl:438` |
| Account master after the run | Current balance, cycle credit and cycle debit for every account, as decimal values with zero tolerance. | `app/cbl/CBTRN02C.cbl:547`, `app/cbl/CBTRN02C.cbl:549` |
| Category balance file after the run | Every record, including records created by the run. | `app/cbl/CBTRN02C.cbl:503`, `app/cbl/CBTRN02C.cbl:527` |
| Reject file | Record content and the 80 byte trailer with reason code and text. | `app/cbl/CBTRN02C.cbl:447`, `app/jcl/POSTTRAN.jcl:36` |
| Counts and return code | Transactions processed, rejected, and return code 4 when any are rejected. | `app/cbl/CBTRN02C.cbl:227`, `app/cbl/CBTRN02C.cbl:229` |
| Order of the surrounding jobs | TRANBKP before POSTTRAN before TRANIDX, with CLOSEFIL first and OPENFIL last. | `scripts/run_posting.sh:13`, `scripts/run_posting.sh:23`, `scripts/run_posting.sh:26`, `scripts/run_posting.sh:30`, `scripts/run_posting.sh:34` |

### Account and card master refresh (jobs ACCTFILE and CARDFILE)

The result is a function of the flat file, so the oracle is the loaded file plus its definition.

| What to compare | How | Evidence |
|---|---|---|
| Record content after the load | Every record of the account and card masters against the flat files. | `app/jcl/ACCTFILE.jcl:61`, `app/jcl/CARDFILE.jcl:75` |
| Key and record definition | Account key of 11 bytes and record size 300, card key of 16 bytes and record size 150, card alternate index on bytes 11 to 26 with non-unique keys. | `app/jcl/ACCTFILE.jcl:40`, `app/jcl/CARDFILE.jcl:54`, `app/jcl/CARDFILE.jcl:85` |
| CICS file state | Files closed and reopened around the load. ACCTFILE has no close or open step of its own, so its state depends on the wrapper. | `app/jcl/CARDFILE.jcl:26`, `app/jcl/ACCTFILE.jcl:22` |
| What survives a refresh | Balances written by posting since the last load are replaced. The harness must show whether the flat file is regenerated in production. | `scripts/run_posting.sh:16`, `app/jcl/ACCTFILE.jcl:57` |

### The transaction report (job TRANREPT, program CBTRN03C, started online by CORPT00C)

| What to compare | How | Evidence |
|---|---|---|
| The 133 byte report lines | Every line, in order, after normalization. | `app/jcl/TRANREPT.jcl:78`, `app/cbl/CBTRN03C.cbl:85` |
| The two date windows | The SORT window (hardcoded 2022-01-01 to 2022-07-06 in the batch job) and the DATEPARM window (CBTRN03C). CORPT00C passes the user's dates to both. Test with a window that differs between the two. | `app/jcl/TRANREPT.jcl:42`, `app/jcl/TRANREPT.jcl:43`, `app/cbl/CBTRN03C.cbl:173`, `app/cbl/CORPT00C.cbl:220` |
| Totals | Page, account and grand totals. See DR-001 to DR-003. | `app/cbl/CBTRN03C.cbl:287`, `app/cbl/CBTRN03C.cbl:297` |
| Descriptions | Type and category descriptions come from files loaded from a DB2 table. Test with a changed description. | `app/jcl/TRANREPT.jcl:69`, `app/jcl/TRANREPT.jcl:71`, `app/jcl/TRANTYPE.jcl:54` |
| Side effect on the backup generation | The report chain cuts a new TRANSACT.BKUP generation. A run between TRANBKP and COMBTRAN changes what COMBTRAN reads. | `app/jcl/TRANREPT.jcl:33`, `app/jcl/COMBTRAN.jcl:24` |
| Online submit path | CORPT00C builds the job stream and writes it to a queue. Test that the generated job stream is identical for a given date pair. | `app/cbl/CORPT00C.cbl:94`, `app/cbl/CORPT00C.cbl:517` |

## Normalization spec

Every row asserts that a difference does not matter. Each is a place a real bug can hide. A person with authority signs the list.

| Item | Rule | Why it may hide a bug | Evidence |
|---|---|---|---|
| Processed timestamp in a transaction | Mask TRAN-PROC-TS. Compare TRAN-ORIG-TS exactly. | The program sets it from the run clock. A port that sets it from the original timestamp would look equal after the mask. | `app/cbl/CBTRN02C.cbl:437`, `app/cpy/CVTRA05Y.cpy:16` |
| Generation numbers, job names and run ids | Mask. | A wrong generation read looks like a name difference. | `app/jcl/COMBTRAN.jcl:24`, `app/catlg/LISTCAT.txt:1537` |
| Money fields | Compare as decimal values with zero tolerance. Never use a binary float. Account amounts are S9(10)V99 and transaction amounts S9(9)V99. They are zoned decimal with a sign overpunch, not packed. | Rounding differences are real defects. A port that reads the overpunch wrongly flips the sign. | `app/cpy/CVACT01Y.cpy:7`, `app/cpy/CVTRA05Y.cpy:10`, `app/data/ASCII/dailytran.txt:1` |
| Working balance width | The posting program computes the overlimit test in a S9(9)V99 field while the account fields are S9(10)V99. Test a balance at 1,000,000,000.00 and above. | High order digits can be lost without an error, and the overlimit check then passes. | `app/cbl/CBTRN02C.cbl:187`, `app/cpy/CVACT01Y.cpy:8` |
| Record padding | Decide spaces or low values, then fix it. The reject record is 350 data bytes and an 80 byte trailer. | A padding difference in a fixed width interface is a real break for a reader that uses offsets. | `app/cbl/CBTRN02C.cbl:83`, `app/cbl/CBTRN02C.cbl:84` |
| Key order of the masters | Compare in key order and record which order the legacy files return. Do not assume ASCII order. Alphanumeric keys such as user ids sort differently in EBCDIC and ASCII. | Browse screens and SORT input depend on the order. | `app/jcl/ACCTFILE.jcl:40`, `app/cbl/COUSR00C.cbl:284` |
| Order of equal sort keys | Do not normalize away. The report SORT keys on card number only, so the order within a card is whatever the sort utility does. | Order inside a card may be depended on and is not specified. | `app/jcl/TRANREPT.jcl:46` |
| Trailing whitespace | Trim only in the report, and only trailing. | A shifted column is a real defect. | `app/jcl/TRANREPT.jcl:78` |

## Boundary and input cases to add on top of replay

| Case | Why | Evidence |
|---|---|---|
| Transaction for an unknown card (reason 100) and for a card whose account is missing (reason 101). | Two reject paths. | `app/cbl/CBTRN02C.cbl:385`, `app/cbl/CBTRN02C.cbl:397` |
| Overlimit only, expired only, and both. | Reason 103 overwrites 102 when both apply. | `app/cbl/CBTRN02C.cbl:410`, `app/cbl/CBTRN02C.cbl:417` |
| A transaction dated exactly on the account expiration date. | The comparison is on ten character date strings and uses `>=`. | `app/cbl/CBTRN02C.cbl:414` |
| Negative and positive amounts. | The sign decides cycle credit or cycle debit. | `app/cbl/CBTRN02C.cbl:548`, `app/cbl/CBTRN02C.cbl:551` |
| A category balance that does not exist yet, and one that does. | Two paths: create and rewrite. | `app/cbl/CBTRN02C.cbl:495`, `app/cbl/CBTRN02C.cbl:498` |
| A zero record daily file, and an empty transaction master for the report. | Empty input paths. The report's end of file branch runs on the first read. | `app/cbl/CBTRN03C.cbl:197`, `app/cbl/CBTRN02C.cbl:202` |
| A duplicate transaction id. | The write to the keyed master can fail, and the program abends. | `app/cbl/CBTRN02C.cbl:564`, `app/cbl/CBTRN02C.cbl:577` |
| A failed account rewrite. | The transaction is still written and the reason is not reported. | `app/cbl/CBTRN02C.cbl:554`, `app/cbl/CBTRN02C.cbl:559` |
| Month end: INTCALC with a real run date, then TRANBKP, COMBTRAN and TRANIDX. | The job carries a hardcoded date. This is the path that only runs at close. | `app/jcl/INTCALC.jcl:22`, `scripts/run_interest_calc.sh:19`, `scripts/run_interest_calc.sh:23`, `scripts/run_interest_calc.sh:26` |
| Fiscal year end, leap day and a daylight saving change in the report window. | Date handling calls the language runtime date service and compares strings. | `app/cbl/CSUTLDTC.cbl:116`, `app/cbl/CORPT00C.cbl:392` |
| An account with no matching disclosure group. | The interest run falls back to a group named DEFAULT. | `app/cbl/CBACT04C.cbl:437` |
| Bad data already in the masters. | Legacy files hold records that break their own rules. Take them from the real archives, not the vendor sample. | inference |

## Deviation Register

Nothing differs without a row here. These are the candidates found while reading. None is approved. Until a person with authority signs, the new implementation reproduces the legacy behavior.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| DR-001 | At end of file the report adds the last transaction amount again to the page total and writes page and grand totals, so the last transaction is counted twice in the grand total. | Reproduce until signed. Proposed: count once. | Looks like a defect. Reading of the code, so inference until a real report confirms it. | not yet | Anyone who reconciles the report grand total. | `app/cbl/CBTRN03C.cbl:198` |
| DR-002 | The last account total is written only when the card number changes, so the final account has no total line. | Reproduce until signed. | Looks like a defect. | not yet | Report readers. | `app/cbl/CBTRN03C.cbl:181` |
| DR-003 | A record outside the DATEPARM window executes NEXT SENTENCE, which leaves the loop rather than skipping the record. | Reproduce until signed. Proposed: skip and continue. | Only matters when the DATEPARM window is narrower than the SORT window. | not yet | The online report, which passes the same dates to both. | `app/cbl/CBTRN03C.cbl:173` |
| DR-004 | A transaction that is both overlimit and expired is rejected with reason 103 only. | Reproduce until signed. | Second test overwrites the first. | not yet | Anyone reading reject reasons. | `app/cbl/CBTRN02C.cbl:407` |
| DR-005 | A failed account rewrite sets reason 109 but the transaction is still written to the master and nothing is rejected. | Reproduce until signed. Proposed: reject and roll back. | Silent divergence between master and account balance. | not yet | Reconciliation of account balances. | `app/cbl/CBTRN02C.cbl:554` |
| DR-006 | The balance test uses a S9(9)V99 working field against S9(10)V99 account fields. | Reproduce until signed. Proposed: widen. | Truncation without error above 999,999,999.99. | not yet | Overlimit decisions on very large balances. | `app/cbl/CBTRN02C.cbl:187` |
| DR-007 | The batch report job has a hardcoded date window of 2022-01-01 to 2022-07-06. | Take the window as a parameter. | A fixed 2022 window returns nothing for current data. | not yet | The scheduled report. | `app/jcl/TRANREPT.jcl:42` |
| DR-008 | The interest job runs with a hardcoded date of 2022-07-18 in its PARM. | Take the run date as a parameter. | Interest transactions carry that date. | not yet | Month end. | `app/jcl/INTCALC.jcl:22` |
| DR-009 | Online bill payment and add transaction build ids by reading the last key and adding 1. | Use a sequence that cannot collide with batch ids. | Race and collision with batch posting. | not yet | Transaction keys. | `app/cbl/COBIL00C.cbl:212` |
| DR-010 | Sign-on compares the stored password field directly. | Replace with the target identity service. | Security. | not yet | All users. | `app/cbl/COSGN00C.cbl:223` |

## Exit bar per wave

A wave is done when all of these hold:

- The replay or parallel run diff is clean, modulo the normalization spec and the Deviation Register.
- Every boundary case above that applies to the wave passes.
- The harness is under version control and runs in CI.
- The Deviation Register rows for the wave are signed by someone with the authority to sign.
- The order of the jobs in the wave matches the order in the wrapper or scheduler.

Not when the port compiles, and not when it passes tests someone wrote alongside the port.

## Keep the harness after cutover

The comparison harness becomes the regression suite for the modernized system. Budget for maintaining it. It is the only executable specification this system has ever had.
