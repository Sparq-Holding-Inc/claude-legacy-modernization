# 06 Test strategy

"Correct" here means: for the inputs this system sees, the refactored code produces the same files, balances, rejects and report lines as the COBOL, or someone decided otherwise and wrote it in the Deviation Register. The tree has no tests (inference: no test source or test JCL was seen in the file counts at `modernization-assessment/graph.json:24`). The oracle has to come from data and job output.

## What the tree gives us

| Asset | What it is | Use | Confidence | Evidence |
|---|---|---|---|---|
| Sample master files, EBCDIC and ASCII | Account, card, cross-reference, customer, category and discount group data, plus a daily transaction file | Input fixtures for waves 2, 5 and 6. Not production data, so not a replay source. | medium | `app/data/EBCDIC/AWS.M2.CARDDEMO.DALYTRAN.PS:1`, `app/data/ASCII/dailytran.txt:1` |
| The flat file the refresh job reloads | ACCTFILE reloads the account VSAM file from `ACCTDATA.PS` | The account refresh has a built-in input and an output, so it can be diffed directly | high | `app/jcl/ACCTFILE.jcl:56`, `app/jcl/ACCTFILE.jcl:61` |
| Generation datasets | Posting writes `DALYREJS(+1)`, the report job writes `TRANSACT.BKUP(+1)`, `TRANSACT.DALY(+1)` and `TRANREPT(+1)` | In production, every past generation is a dated golden master. Ask for them. | high | `app/jcl/POSTTRAN.jcl:38`, `app/jcl/TRANREPT.jcl:33`, `app/jcl/TRANREPT.jcl:55`, `app/jcl/TRANREPT.jcl:80` |
| Reject return code | CBTRN02C ends with return code 4 when anything was rejected | A cheap exit-status assertion | high | `app/cbl/CBTRN02C.cbl:229`, `app/cbl/CBTRN02C.cbl:230` |

Not in the tree: production volumes, a month-end or fiscal year-end sample, the archived reports, SMF or job logs, CICS journals. Telemetry is `none`, so nothing here says which jobs run.

## Oracle per wave

| Wave | Oracle | Why | Confidence | Evidence |
|---|---|---|---|---|
| 1 | None needed. A checklist that the target datasets exist with the same keys, record sizes and share options. | Utility jobs hold no logic. | medium | `app/jcl/ACCTFILE.jcl:40`, `app/jcl/ACCTFILE.jcl:41` |
| 2 | Golden master. Run the read jobs on the sample masters and compare the DISPLAY output. | Read-only, deterministic. | medium | `app/jcl/READACCT.jcl:1` |
| 3 | Characterization tests on the screens, labeled provisional. Capture the 3270 screen text for a scripted session. | Weakest oracle, and the only one available without CICS journals. Ask for the journals. | low | `app/cbl/COSGN00C.cbl:39` |
| 4 | None needed beyond a build check. | Build and definition jobs. | medium | `app/jcl/DEFGDGD.jcl:39` |
| 5 | Golden master per refresh job: load the same flat file, then compare the resulting key sequence and records. | Each refresh is delete, define and reload. | medium | `app/jcl/CARDFILE.jcl:75`, `app/jcl/XREFFILE.jcl:64` |
| 6 | Parallel run, if the client can allow it. Otherwise replay of captured daily transaction files against a snapshot of the masters taken before the run, diffed against the archived generations. | Money moves here. The weaker oracles are not enough for the item that must not break. | low (not yet confirmed possible) | `app/jcl/POSTTRAN.jcl:23`, `app/jcl/TRANREPT.jcl:59` |
| 7 | Replay of CICS journals if they exist. Otherwise scripted-session characterization, labeled provisional. | Online updates write the same files as wave 6, so the file state after a session is the oracle. | low | `app/cbl/COACTUPC.cbl:573` |
| 8, 9 | Golden master of the IMS unload files and DB2 extracts. | Each job emits a file. | low | `app/app-authorization-ims-db2-mq/cbl/PAUDBUNL.CBL:186`, `app/app-transaction-type-db2/jcl/TRANEXTR.jcl:87` |

## The three must-not-break items

### Daily transaction posting (job POSTTRAN, program CBTRN02C)

What to compare after one run: the transaction master, the category balance file, the account master, the reject file and the return code.

Behaviors the harness has to reproduce. They are what the program does, and some may be defects:

| Behavior | Detail | Evidence |
|---|---|---|
| Validation order | The cross-reference lookup runs first (reason 100). The account lookup runs only if that passed (reason 101). | `app/cbl/CBTRN02C.cbl:371`, `app/cbl/CBTRN02C.cbl:385`, `app/cbl/CBTRN02C.cbl:397` |
| Over-limit and expired are tested separately, and the second overwrites the first | A transaction that is both over the limit and after expiry is rejected with reason 103, not 102. Reproduce, then decide in the Deviation Register. | `app/cbl/CBTRN02C.cbl:410`, `app/cbl/CBTRN02C.cbl:417` |
| Over-limit formula | Cycle credit minus cycle debit plus the amount, compared to the credit limit | `app/cbl/CBTRN02C.cbl:403` |
| Expiry compare | A text compare of the expiration date against the first 10 characters of the original timestamp | `app/cbl/CBTRN02C.cbl:414` |
| Balance update | The amount is added to the current balance. A non-negative amount goes to the cycle credit, a negative amount to the cycle debit. | `app/cbl/CBTRN02C.cbl:547`, `app/cbl/CBTRN02C.cbl:548`, `app/cbl/CBTRN02C.cbl:551` |
| Category balance | Created if absent, updated otherwise | `app/cbl/CBTRN02C.cbl:495`, `app/cbl/CBTRN02C.cbl:503`, `app/cbl/CBTRN02C.cbl:526` |
| A failed account rewrite sets reason 109 after the transaction was already written | Whether the transaction file and the account file can disagree is a question for the client | `app/cbl/CBTRN02C.cbl:556` |
| The transaction master is emptied before each posting run, and posting opens it for output | TRANBKP copies it to a backup generation, deletes the cluster and defines a new one, and CBTRN02C opens it with OPEN OUTPUT. A rerun of POSTTRAN therefore replaces the day's transactions, not appends. The history lives in the backup generations. Confirm with the client that this is intended. | `app/jcl/TRANBKP.jcl:33`, `app/jcl/TRANBKP.jcl:40`, `app/jcl/TRANBKP.jcl:54`, `app/cbl/CBTRN02C.cbl:256` |
| Return code 4 on any reject | Exit status is part of the contract with the scheduler | `app/cbl/CBTRN02C.cbl:230` |

### Account and card master refresh (jobs ACCTFILE, CARDFILE, XREFFILE, CUSTFILE)

Each job deletes the cluster, defines it again and reloads from a flat file (`app/jcl/ACCTFILE.jcl:25`, `app/jcl/ACCTFILE.jcl:36`, `app/jcl/ACCTFILE.jcl:61`). Compare the record count, the key set, byte equality of each record and the alternate index paths (`app/jcl/CARDFILE.jcl:83`, `app/jcl/CARDFILE.jcl:100`). The order matters. In `run_posting.sh` the account reload runs before posting, so any balance posted yesterday and not written back to the flat file is lost at the reload (`scripts/run_posting.sh:17`, `scripts/run_posting.sh:26`). Whether that is the intended design or a demo shortcut is the first question to put to the client (inference). If it is intended, the refactored code must reproduce it.

### Transaction report (job TRANREPT, program CBTRN03C, screen CORPT00C)

Compare the 133-column report file line by line (`app/jcl/TRANREPT.jcl:78`). The date range is hard-coded in the job (`app/jcl/TRANREPT.jcl:43`, `app/jcl/TRANREPT.jcl:44`) and the sort key is a byte offset into the transaction record (`app/jcl/TRANREPT.jcl:41`, `app/jcl/TRANREPT.jcl:42`). The harness must cover both producers of the report, the batch job and the online screen that submits the same procedure (`app/cbl/CORPT00C.cbl:94`).

## Normalization spec (for a human to sign)

Each row is an assertion that a difference does not matter.

| Ignore | Reason | Risk if wrong | Evidence |
|---|---|---|---|
| Timestamps written by `FUNCTION CURRENT-DATE`, run date, job names and generation numbers | They change on every run | A timestamp used as a key or in a sort would hide a defect | `app/cbl/CBTRN02C.cbl:693` |
| Page numbers and run-date lines in the report header | Same | Medium. Read the report layout first. | `app/cbl/CBTRN03C.cbl:51` |
| Trailing spaces in fixed-width records | Padding | Low. A field of low values is not a field of spaces, so compare those exactly. | inference |

Do not normalize: any money field. Use a fixed-point decimal type with zero tolerance. The account and transaction amounts are signed packed or zoned decimal fields (inference: the COBOL ADD at `app/cbl/CBTRN02C.cbl:547` works on COMP-3 or DISPLAY fields, and the picture clauses are in the copybooks CVACT01Y and CVTRA05Y, which I did not open).

Traps to test on this system:

- **Collating sequence.** The KSDS returns records in EBCDIC key order. The report sorts by card number as a zoned decimal (`app/jcl/TRANREPT.jcl:41`), and the sort control is JCL SORT, not COBOL. Compare the order explicitly.
- **Record length.** The reject record is 430 bytes, the transaction backup is 350 (`app/jcl/POSTTRAN.jcl:36`, `app/jcl/TRANREPT.jcl:31`). The extractor did not compare these with the copybooks (`modernization-assessment/graph.json:20`).
- **Job order.** The list of orders to keep is the ordering table in `modernization-assessment/02a-edge-tables.md:162`.

## Targeted cases

| Case | Why | Evidence |
|---|---|---|
| Empty daily transaction file | Zero-record batch | `app/cbl/CBTRN02C.cbl:206` |
| Card number not in the cross-reference, account missing | Reasons 100 and 101 | `app/cbl/CBTRN02C.cbl:385`, `app/cbl/CBTRN02C.cbl:397` |
| Amount exactly equal to the limit; one cent over | Boundary of `>=` | `app/cbl/CBTRN02C.cbl:407` |
| Transaction on the expiry date; one day after | Text compare of dates | `app/cbl/CBTRN02C.cbl:414` |
| Over the limit and expired in one transaction | Reason overwritten | `app/cbl/CBTRN02C.cbl:410`, `app/cbl/CBTRN02C.cbl:417` |
| Negative amount (a payment or refund) | Debit branch | `app/cbl/CBTRN02C.cbl:551` |
| First transaction for an account and category | Create branch | `app/cbl/CBTRN02C.cbl:503` |
| Month end, year end, leap day in the report range | The range is two hard-coded dates | `app/jcl/TRANREPT.jcl:43` |
| Rerun of POSTTRAN the same day, with and without TRANBKP in front | `DALYREJS(+1)` creates a new generation each time, and the transaction file is opened for output | `app/jcl/POSTTRAN.jcl:38`, `app/cbl/CBTRN02C.cbl:256` |
| Interest run (CBACT04C) after posting, with a balance and rate that leave a fraction of a cent | Interest is the category balance times the rate over 1200 with no ROUNDED clause, so it truncates. A decimal port that rounds is a defect against the legacy. | `app/cbl/CBACT04C.cbl:465` |

## Deviation Register

Empty, and it should stay empty until a human decides. First candidates to put to the client:

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| DR-001 | Over-limit and expired in the same transaction reports reason 103 | Not decided | Not decided | Not decided | Reject file contents and any downstream reader of the reason code | `app/cbl/CBTRN02C.cbl:417` |
| DR-002 | Report date range is hard-coded to 2022-01-01 to 2022-07-06 in the batch job | Not decided | Not decided | Not decided | The scheduled report cannot be a current one as it stands | `app/jcl/TRANREPT.jcl:43` |
| DR-003 | Account reload from flat file before posting in the wrapper | Not decided | Not decided | Not decided | Balances | `scripts/run_posting.sh:17` |

## Exit bar for wave 6

Replay diff clean for the whole business cycle including a month end, every targeted case passing, the harness in version control and run in CI, and the register signed by someone who can sign it. Keep the harness after cutover: it is the only executable specification.
