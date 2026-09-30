# 06 Test strategy

The bar is not that the port passes tests. The legacy system has none. The bar is that for the inputs this system really sees, the new implementation produces the same outputs as the old one, and where it does not, someone decided that on purpose and wrote it down.

This file follows the `behavioral-equivalence` skill. Target state is refactor, so every wave is judged at its boundary, not by comparing source.

## What the tree offers as an oracle

The tree holds datasets, but they are seed data, not production. There is one day of daily transactions (300 records, stamped 2022-06-10), 50 accounts, 50 cards, 50 cross-references, 50 customers and small reference files, most in both an ASCII and an EBCDIC copy (`app/data/ASCII/dailytran.txt:1`, `app/data/ASCII/acctdata.txt:1`). It also holds a catalog listing of the datasets (`app/catlg/LISTCAT.txt:1`) and, as archives, the Micro Focus and UniKix runtime kits under `samples/m2/`. The runtime kits matter: they may let the legacy system run off the mainframe to generate golden masters. That needs confirming.

There are no archived outputs, no production inputs and no telemetry in the tree. One day of seed data has no month-end, no quarter-end and no fiscal-year-end. It cannot stand alone as an oracle for anything that runs at close.

## Oracle per wave

In descending strength. Always ask for the strongest first. Teams assume a parallel run is impossible and are often wrong.

| Wave | Oracle to ask for | Fallback | Confidence | Evidence |
|---|---|---|---|---|
| 1 | A before and after catalog listing and the resource inventory from the CSD | Review only. There is little output to compare | high | `app/catlg/LISTCAT.txt:1`, `app/jcl/CBADMCDJ.jcl:27` |
| 2 | Golden master from archived reports of the read jobs, or the legacy utilities run on the rehost kit against the seed data | Characterization tests from the source, labeled provisional | low | `app/jcl/READACCT.jcl:32`, `app/data/ASCII/acctdata.txt:1` |
| 3 | Captured 3270 sessions replayed against both front doors, from CICS journals if the client has them | Scripted sign-on and menu paths for all 25 transactions | low | `app/cbl/COMEN01C.cbl:185`, `app/cpy/COMEN02Y.cpy:28` |
| 4 | None needed for the application jobs beyond a run of each on both sides |  | medium | `app/jcl/DEFGDGD.jcl:27` |
| 5 | Parallel run of the nightly cycle on the same daily feed. Failing that, replay of archived cycles: the daily transaction file plus the transaction backup, reject and report generations it produced | Golden master from those generations alone. The seed data as a last resort, labeled provisional | low | `app/jcl/POSTTRAN.jcl:23`, `app/jcl/DEFGDGB.jcl:25` |
| 6 | Replay of captured online input with paired before and after master records, plus a parallel run for a week of paired screens | Scripted cases per screen from the edit rules | low | `app/cbl/COBIL00C.cbl:212`, `app/cbl/COACTUPC.cbl:573` |
| 7 | MQ message capture and an IMS database unload before and after | Unknown until the IMS and DB2 members are read | low | inference |

The generation bases hold five generations at most (`app/jcl/DEFGDGB.jcl:25`), and the report base is defined with two different limits (`app/jcl/DEFGDGB.jcl:37`, `app/jcl/REPTFILE.jcl:27`). The client should copy what exists before the next cycle rolls it off.

## Normalize before you diff

A naive diff will fail for reasons that do not matter, and it will also hide the ones that do. Each row below is a small assertion that a difference does not matter. A person signs off each one.

| Item | Treatment | Why | Evidence |
|---|---|---|---|
| Processing timestamps on posted and interest records | Compare the format, not the value | They come from the wall clock | `app/cbl/CBTRN02C.cbl:693`, `app/cbl/CBACT04C.cbl:614` |
| Interest transaction ids | Compare exactly, with the run date held fixed | Built from the run date and a counter. INTCALC fixes the date in its PARM | `app/cbl/CBACT04C.cbl:476`, `app/jcl/INTCALC.jcl:22` |
| Money in signed zoned and packed fields | Compare as decimals with zero tolerance. Never as floats | Legacy arithmetic is fixed-point. A float port produces rounding differences that are real defects | `app/cpy/CVTRA05Y.cpy:10`, `app/cpy/CVACT01Y.cpy:7` |
| The sign of zoned amounts | Normalize the sign nibble and the overpunch character before comparing text and EBCDIC versions | The ASCII copy shows positive 7 as G and negative zero as a brace | `app/data/ASCII/dailytran.txt:1`, `app/data/ASCII/dailytran.txt:2` |
| Interest arithmetic | Truncate, do not round | The COMPUTE has no ROUNDED clause, and the result is stored in two decimals | `app/cbl/CBACT04C.cbl:464`, `app/cbl/CBACT04C.cbl:168` |
| The posting limit test | Keep the 9-digit intermediate until a person rules on it | It truncates a sum the balances can hold. See DR-2 | `app/cbl/CBTRN02C.cbl:187`, `app/cbl/CBTRN02C.cbl:403` |
| Record order in a KSDS | Compare in EBCDIC key order, not ASCII | Digits and letters sort the other way round. The user file mixes both, such as ADMIN001 and USER0001 | `app/jcl/ESDSRRDS.jcl:36`, `app/jcl/ESDSRRDS.jcl:41` |
| Order of report detail within one card | Treat as incidental only after asking the business | The sort has one key and no tie rule | `app/jcl/TRANREPT.jcl:46` |
| Report layout, page size and totals | Compare the 133-byte lines exactly, including headers, page breaks every 20 lines and totals | It is a printed report | `app/cbl/CBTRN03C.cbl:131`, `app/cbl/CBTRN03C.cbl:282`, `app/jcl/TRANREPT.jcl:78` |
| Reject file | Compare the 350-byte record and the 80-byte trailer with its reason code and text | The trailer is the only record of why a transaction failed | `app/cbl/CBTRN02C.cbl:385`, `app/jcl/POSTTRAN.jcl:34` |
| Return code | Compare. The posting run ends with 4 when any transaction is rejected | A scheduler may branch on it | `app/cbl/CBTRN02C.cbl:230` |
| Filler, spaces and low values | Decide once per file and write it down | Fixed-width records pad with either | `app/cpy/CVACT01Y.cpy:17` |
| Generation addressing | Run the cycle in the same order and assert which generation each step created and read | (+1) and (0) resolve differently depending on what ran before | `app/jcl/COMBTRAN.jcl:24`, `app/jcl/TRANREPT.jcl:33` |
| Date validation results | Compare accept or reject and the message number | Callers test the message number as text | `app/cbl/CSUTLDTC.cbl:116`, `app/cbl/COTRN02C.cbl:400` |

Keep the list short. The last four rows are the ones most likely to hide a real bug.

## Cover the input space deliberately

Replay covers the common path. Add targeted cases for the paths below. Where a path is in the code, it is cited.

| Case | What to check | Evidence |
|---|---|---|
| Unknown card, unknown account | Reasons 100 and 101 and the reject record | `app/cbl/CBTRN02C.cbl:385`, `app/cbl/CBTRN02C.cbl:397` |
| Over the limit, and expired, and both at once | Reasons 102 and 103. When both hold, the later one overwrites the earlier | `app/cbl/CBTRN02C.cbl:410`, `app/cbl/CBTRN02C.cbl:417` |
| A sum larger than 999,999,999.99 | The truncation in the limit test | `app/cbl/CBTRN02C.cbl:403` |
| Several transactions on one account in one run | Each sees the balance the earlier ones left, so order matters | `app/cbl/CBTRN02C.cbl:547` |
| A first transaction for a new category on an account | The create branch of the category balance | `app/cbl/CBTRN02C.cbl:508` |
| An account whose discount group has no rate | The DEFAULT group fallback | `app/cbl/CBACT04C.cbl:436` |
| Month-end and fiscal year-end | The monthly interest cycle and the combine step. Dates that fall on a leap day | `app/scheduler/CardDemo.controlm:64`, `app/jcl/COMBTRAN.jcl:24` |
| An empty daily file, and a file at the largest size the old system took | Return code, empty outputs, the reject GDG still created | `app/jcl/POSTTRAN.jcl:38` |
| The report with a date range that differs from the DATEPARM file | Which filter wins, and where the loop ends | `app/cbl/CBTRN03C.cbl:173`, `app/cbl/CBTRN03C.cbl:177` |
| Two users adding transactions at once | The highest-key-plus-one allocation | `app/cbl/COBIL00C.cbl:212`, `app/cbl/COTRN02C.cbl:444` |
| Bad data already in the files | The legacy behavior on records that break their own rules. It is often neither an error nor a sane result | `app/data/ASCII/dailytran.txt:2` |
| The refresh chain run out of order, and a run when CICS still holds the files | What fails and how | `scripts/run_full_batch.sh:13`, `scripts/run_full_batch.sh:66` |

## Mainframe traps for this system

| Trap | Where | Evidence |
|---|---|---|
| Packed and binary fields | Counters and page size in the report use COMP-3, the posting code uses binary | `app/cbl/CBTRN03C.cbl:129`, `app/cbl/CBTRN02C.cbl:142` |
| Collating sequence | KSDS browse order feeds the transaction list, the user list and the highest-key search | `app/cbl/COTRN02C.cbl:444`, `app/cbl/COUSR00C.cbl:39` |
| REDEFINES | 43 in COACTUPC and 12 in COTRTLIC. Test every branch that reads either layout | `app/cbl/COACTUPC.cbl:573`, `app/app-transaction-type-db2/cbl/COTRTLIC.cbl:620` |
| Fixed byte offsets in JCL | The sort and index cards break silently if the layout moves | `app/jcl/TRANREPT.jcl:41`, `app/jcl/TRANIDX.jcl:27` |
| Job order | The temporal edges in `graph.json` are the orders the harness must keep | `scripts/run_full_batch.sh:47`, `app/scheduler/CardDemo.controlm:5` |
| The assembler routines | COBDATFT formats a date and MVSWAIT waits. Neither is parsed | `app/cbl/CBACT01C.cbl:231`, `app/cbl/COBSWAIT.cbl:38` |

## Deviation register

Every difference between old and new behavior needs a row. These candidates come from reading the code. None is approved. Approval belongs to someone at the client with the authority to sign it. The New behavior column is blank on purpose.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| DR-1 | A failed REWRITE of the account sets reason 109 after the transaction is already posted, and no reject is written | to be decided | a posted transaction with no matching balance update goes unreported | pending | reject file, reconciliation | `app/cbl/CBTRN02C.cbl:554`, `app/cbl/CBTRN02C.cbl:556` |
| DR-2 | The credit-limit test sums into a 9-digit field while balances are 10 digits, so a large sum truncates | to be decided | may accept an over-limit transaction | pending | posted balances, reject file | `app/cbl/CBTRN02C.cbl:187`, `app/cbl/CBTRN02C.cbl:403` |
| DR-3 | When a transaction is both over the limit and expired, only reason 103 is recorded | to be decided | one of two reasons is lost | pending | reject file consumers | `app/cbl/CBTRN02C.cbl:410`, `app/cbl/CBTRN02C.cbl:417` |
| DR-4 | The report adds the last amount again at end of file, and NEXT SENTENCE ends the read loop at the first out-of-range record | to be decided | totals may be overstated and output may be cut short. Inference from reading, not observed | pending | printed report, anyone reconciling it | `app/cbl/CBTRN03C.cbl:177`, `app/cbl/CBTRN03C.cbl:200` |
| DR-5 | The account listing prints 2525.00 when the cycle debit is zero | to be decided | a fixed value replaces real data | pending | any consumer of that listing | `app/cbl/CBACT01C.cbl:237` |
| DR-6 | Interest truncates instead of rounding, falls back to a DEFAULT rate group, and fees are not implemented | to be decided | money differs from a rounded calculation | pending | account balances, statements | `app/cbl/CBACT04C.cbl:464`, `app/cbl/CBACT04C.cbl:437`, `app/cbl/CBACT04C.cbl:518` |
| DR-7 | The interest run date and the report date range are fixed in JCL | to be decided | a job that ignores the calendar | pending | interest ids, report contents | `app/jcl/INTCALC.jcl:22`, `app/jcl/TRANREPT.jcl:43` |
| DR-8 | New transaction keys come from the highest key plus one in online code, from the feed id in batch, and from a date string in interest | to be decided | three rules in one key space | pending | key collisions across writers | `app/cbl/COBIL00C.cbl:217`, `app/cbl/CBTRN02C.cbl:425`, `app/cbl/CBACT04C.cbl:476` |
| DR-9 | Sign-on compares a clear-text password, and the seed job and the FTP job hold credentials in clear text | to be decided | a security defect, not behavior to keep | pending | sign-on, the user security file | `app/cbl/COSGN00C.cbl:223`, `app/jcl/FTPJCL.JCL:33`, `app/jcl/ESDSRRDS.jcl:36` |
| DR-10 | TRANBKP empties the transaction master each cycle after copying it, so its content is one cycle's postings | to be decided | history may live only in backup generations. Ask whether that is intended | pending | online transaction list, report | `app/jcl/TRANBKP.jcl:40`, `app/cbl/CBTRN02C.cbl:256` |

## Exit bar per wave

A wave is done when the replay diff is clean apart from the normalization spec and the deviation register, every targeted case passes, the harness is under version control and runs in CI, and the register is signed. It is not done when the port compiles, and it is not done when it passes tests written beside the port. Those tests encode the porter's understanding, which is what is under test.

| Wave | Extra exit condition |
|---|---|
| 1 | The inventory of CICS resources, identities and storage matches the legacy listing |
| 2 | The harness runs unattended and the decimal type is fixed |
| 3 | Every transaction reachable from the legacy menu is reachable from the new one, and returns to a working menu |
| 4 | None beyond the common bar |
| 5 | At least two full cycles match on posting, refresh and report. The generation assertions pass. A rollback rehearsal restores the masters |
| 6 | Each screen passes on a paired run. Key allocation is proven safe under concurrent use |
| 7 | To be set when the IMS and DB2 members are read |

## Keep the harness after cutover

The comparison harness becomes the regression suite for the new system. Budget for maintaining it. Teams throw it away at cutover and lose the only executable specification the system had.

## What to ask the client to supply

1. Any archived generations of the transaction backup, reject and report datasets, with the daily input for each, before they roll off the five-generation limit.
2. A week of captured CICS input and output, and journals if kept.
3. Archived printed reports, statements and any file sent to a partner.
4. Job logs or SMF records for twelve months, which also answer the dead-code questions.
5. Whether a parallel run is possible, and whether the runtime kits under `samples/m2/` can run the legacy code for golden masters.
6. The month-end and fiscal-year-end calendars, and which jobs run at close.
