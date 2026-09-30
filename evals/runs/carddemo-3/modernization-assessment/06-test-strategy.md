# 06 Test strategy: what "correct" means for each wave

"It passes the tests" is not the bar, because the legacy system has none. The bar is this: for the inputs the system sees, the new implementation produces the same outputs as the old one. Where it does not, someone decided that on purpose and wrote it down in the deviation register at the end of this file.

The client named three things that must not break: daily transaction posting, the account and card master refresh, and the transaction report. They are the anchors. Waves 4 and 5 hold them.

## What oracle exists in this tree

The tree holds datasets, but only seed data and one catalog listing. It holds no output of any run. That decides the strength of every oracle below.

| Source | What it gives | Strength | Evidence |
|---|---|---|---|
| Seed input files | 300 daily transactions and 50 records each for accounts, cards, cross references, customers and category balances, in ASCII and EBCDIC. Inputs for a replay. | Input only. No expected output. | `app/data/ASCII/dailytran.txt:1`, `app/data/ASCII/acctdata.txt:1` |
| Catalog listing captured after a run | Record counts after some run: the account master shows 311 updates, and the transaction master holds 311 records. A count-level check. What produced the 311 is not stated. It is consistent with 300 posted transactions plus 11 interest transactions (inference). | Coarse. Counts only. | `app/catlg/LISTCAT.txt:67`, `app/catlg/LISTCAT.txt:3598` |
| Off-mainframe runtimes | Two runtime packages for the sample (Micro Focus and UniKix). They would let the legacy code run on a laptop and produce baseline output from the seed. I did not open them. | Characterization. It encodes what the code does on the seed, not what production does. | inference: `samples/m2/mf/CardDemo_runtime.zip` and `samples/m2/unikix/UniKix_CardDemo_runtime_v1.zip` exist |
| GDG generations | Prior runs of the backup, report and reject files. But every base is defined with LIMIT(5) and SCRATCH, so only five generations survive. | Shallow. Ask for the tape or report archive. | `app/jcl/DEFGDGB.jcl:26`, `app/jcl/DALYREJS.jcl:26` |
| CICS journals for replay | None. Every CICS file is defined with JOURNAL(NO) and RECOVERY(NONE). There is no journal to replay online traffic from. | Not available. | `app/csd/CARDDEMO.CSD:7`, `app/csd/CARDDEMO.CSD:9` |
| Job logs and SMF | Not in the tree. They would also give telemetry for the dead-code register. | Ask for them. | inference |

## Oracle per wave

Different waves legitimately use different oracles. The strongest first.

| Wave | Oracle to use | Fallback, labeled provisional | Evidence |
|---|---|---|---|
| 1 | Return codes and the generation bases created. No data. | None needed. | `app/jcl/DEFGDGB.jcl:24` |
| 2 | Print and compare: the READ jobs write files, so a diff against the legacy output on the same masters is exact. | Seed masters run through the off-mainframe runtime. | `app/jcl/READACCT.jcl:32` |
| 3 | Scripted screens compared field by field against the legacy screens on the seed masters. Sign-on outcomes for known users. | Recorded sessions. Not in the tree. | `app/cbl/COSGN00C.cbl:223` |
| 4 | Load the seed PS files with the legacy loader and the ported loader, then compare the read-back from the wave 2 print jobs. Compare key counts and the alternate index results. | Catalog record counts. | `app/jcl/ACCTFILE.jcl:61`, `app/catlg/LISTCAT.txt:64` |
| 5 | Parallel run if the client can provide a production daily file: legacy and new both post it and the masters, the reject file and the report are diffed. Otherwise replay of captured daily files over a window that includes month end and year end. | Golden master from archived reports and reject files. Last, characterization from the seed through the off-mainframe runtime. | `app/jcl/POSTTRAN.jcl:23`, `app/jcl/TRANREPT.jcl:59` |
| 6 | Screen scripts that end in a master comparison, run against both platforms, with the wave 5 posting run afterward to see that writers do not disagree. | Characterization. | `app/cbl/COACTUPC.cbl:4066`, `app/cbl/COBIL00C.cbl:212` |
| 7 | Not assessed here. The message contracts, IMS segments and DB2 tables need their own oracle. | | inference |

Ask the client first whether a parallel run is possible for wave 5. Teams assume it is not and are often wrong. The batch window closes CICS files and the legacy job can stay up on the same daily file.

## What I would ask the client to supply

1. One production daily transaction file and the masters as they stood before it, with every output of that run (rejects, report, statements).
2. Twelve months of archived transaction reports and reject files, and the tape or report archive behind the five-generation GDG limit. Include month end and fiscal year end.
3. Job logs or SMF for the last 12 months. They tell us which jobs and programs ran, with which return codes.
4. The producer of the daily transaction file. Nothing in the tree writes it. Its layout is CVTRA06Y, and CBTRN02C translates it into the master layout field by field (`app/cbl/CBTRN02C.cbl:425`).
5. Confirmation of which order of the batch cycle is real: the three wrappers, Control-M and the CA-7 listing disagree (`02-coupling.md`).
6. The contents of the DATEPARM dataset that the standalone report job reads, and whether that job or the online screen is the one in use (`app/jcl/TRANREPT.jcl:73`).

## Normalize before you diff

A naive diff of these outputs fails on things that do not matter. Every entry below is a small assertion that a difference is not a defect. Each is a place a real bug can hide, so keep the list short and have a person sign it.

| Item | Treatment | Why | Evidence |
|---|---|---|---|
| Processed timestamp on posted transactions | Ignore the value. Compare that it is present and in the same format. | CBTRN02C writes the run clock. | `app/cbl/CBTRN02C.cbl:437`, `app/cbl/CBTRN02C.cbl:438` |
| Transaction ids on interest transactions | Compare the pattern (10 character date plus 6 digit suffix). Compare the suffix order. | Built from the PARM date and a counter. The PARM date is fixed in the JCL. | `app/cbl/CBACT04C.cbl:476`, `app/jcl/INTCALC.jcl:22` |
| Transaction ids on online adds and bill payments | Compare that each id is the highest key plus 1. Do not compare the value across runs. | Depends on what was in the file first. | `app/cbl/COBIL00C.cbl:212`, `app/cbl/COTRN02C.cbl:444` |
| GDG generation numbers and dataset names | Compare content by position: the latest generation. | (+1) and (0) resolve differently on a new platform. | `app/jcl/TRANREPT.jcl:33`, `app/jcl/COMBTRAN.jcl:24` |
| Report page count, header dates and the run date | Ignore. Compare detail lines and totals. | The report carries the window and page numbers. | `app/cbl/CBTRN03C.cbl:282` |
| Money fields | Compare as decimal with zero tolerance. No floating point. | The amounts are zoned decimal S9(9)V99 and S9(10)V99, added without ROUNDED and without SIZE ERROR. IEEE floats would round differently. | `app/cpy/CVTRA05Y.cpy:10`, `app/cpy/CVACT01Y.cpy:7`, `app/cbl/CBTRN02C.cbl:547` |
| Sign encoding in the text seed | Decode the sign overpunch before comparing. The ASCII seed carries it in the last digit. | The amount field ends in a letter for a positive digit. | `app/data/ASCII/dailytran.txt:1` |
| Record order in a KSDS | Compare in key order. Do not compare file order. Confirm the order was incidental before ignoring it. | A KSDS returns records in key order, and downstream programs may depend on it. | `app/jcl/COMBTRAN.jcl:28` |
| Sort collation | Do not normalize. Test it. The report sorts card number as zoned decimal, and COMBTRAN sorts transaction id as characters. An ASCII port orders letters and digits differently from EBCDIC. | A silent reorder of the report or of the rebuilt master. | `app/jcl/TRANREPT.jcl:41`, `app/jcl/COMBTRAN.jcl:28` |
| Trailing spaces and low values in fixed records | Decide per file and write it down. | Fixed width records pad with spaces or binary zeros. | `app/cpy/CVTRA05Y.cpy:18` |
| SYSOUT counts (records processed, rejected) | Compare. They are the cheapest check. | CBTRN02C prints them and sets return code 4 on any reject. | `app/cbl/CBTRN02C.cbl:229` |

Money is stored three ways in this system, and the spec has to name each. The core posting and account files use zoned decimal, so an overpunch error is as silent as a packed one. The export record packs money (`app/cpy/CVEXPORT.cpy:50`, `app/cpy/CVEXPORT.cpy:71`) and mixes in a binary field for the cycle debit (`app/cpy/CVEXPORT.cpy:57`). The IMS authorization segment packs credit limits, balances and approved amounts (`app/app-authorization-ims-db2-mq/cpy/CIPAUSMY.cpy:23`). The report and statement counters are packed too (`app/cbl/CBTRN03C.cbl:129`). Compare all of them in a decimal type with zero tolerance, after decoding.

## Cover the input space deliberately

Replay covers the common path. These are the dangerous paths in this code, from reading it.

| Area | Cases to add | Evidence |
|---|---|---|
| Posting rejects | Card missing from the cross reference (100). Account missing (101). Over the limit (102). Expired account (103). Both 102 and 103 at once: the later check overwrites the earlier reason. | `app/cbl/CBTRN02C.cbl:385`, `app/cbl/CBTRN02C.cbl:397`, `app/cbl/CBTRN02C.cbl:410`, `app/cbl/CBTRN02C.cbl:417` |
| Posting boundaries | Amount exactly at the limit (the test is `>=`). Expiry on the day of the transaction. Leap day. Year end. A negative amount, which goes to the debit bucket as a negative number. An amount near the S9(9)V99 width of the work balance, which is narrower than the account fields. | `app/cbl/CBTRN02C.cbl:407`, `app/cbl/CBTRN02C.cbl:414`, `app/cbl/CBTRN02C.cbl:548`, `app/cbl/CBTRN02C.cbl:187` |
| Posting shape | Zero-record daily file. All records rejected (return code 4). A new category balance key versus an existing one. | `app/cbl/CBTRN02C.cbl:229`, `app/cbl/CBTRN02C.cbl:495` |
| Master lifecycle | Run TRANBKP, POSTTRAN, INTCALC, TRANBKP, COMBTRAN, TRANIDX in the order of `run_full_batch.sh`, twice. Check that the transaction master is empty when POSTTRAN starts and complete after COMBTRAN. | `scripts/run_full_batch.sh:29`, `scripts/run_full_batch.sh:47`, `scripts/run_full_batch.sh:58` |
| Interest | An account with no category balance rows. A rate of zero. A missing group that falls back to DEFAULT. The run date fixed in the JCL: run it twice and check for duplicate ids. | `app/cbl/CBACT04C.cbl:437`, `app/jcl/INTCALC.jcl:22` |
| Report window | The SORT window and the DATEPARM window equal, then the second narrower, then wider. An empty window. Leap day and year end inside the window. A card with no cross reference or type row. A window that spans a page break. | `app/jcl/TRANREPT.jcl:43`, `app/cbl/CBTRN03C.cbl:173`, `app/cbl/CBTRN03C.cbl:282` |
| Report screen | Blank, invalid and reversed dates in CORPT00C, checked through CSUTLDTC. The same date written into both places of the generated job. | `app/cbl/CORPT00C.cbl:220`, `app/cbl/CORPT00C.cbl:235`, `app/cbl/CSUTLDTC.cbl:116` |
| Master refresh | Reload from the seed PS files twice, with the file absent and present. Check the key length, the record size and, for the card file, that the alternate index returns the same card for an account. Check that a refresh after a posting run discards the posted balances. | `app/jcl/ACCTFILE.jcl:25`, `app/jcl/CARDFILE.jcl:85`, `scripts/run_posting.sh:17` |
| Bad data already in there | Ask for it. Legacy files hold records that break their own rules, and the port must reproduce what the legacy code does with them. I cannot see any in the seed. | inference |
| Fiscal close | The monthly interest cycle and any path that only runs at close. This is where a modernization fails six months after cutover. | `app/scheduler/CardDemo.controlm:66` |

## Mainframe traps for the spec

| Trap | Where it applies here | Evidence |
|---|---|---|
| Decimal arithmetic | All balance updates use ADD and COMPUTE on zoned fields with no ROUNDED and no SIZE ERROR. Use a decimal type with fixed scale and reproduce truncation on overflow, or record it as a deviation. | `app/cbl/CBTRN02C.cbl:547`, `app/cbl/CBACT04C.cbl:464` |
| `REDEFINES` | The export layout and the job text in CORPT00C use it. Test every branch that reads either view. | `app/cbl/CORPT00C.cbl:126`, `app/cpy/CVEXPORT.cpy:1` |
| Job order | The temporal edges in `graph.json` are the orders the harness must keep. Three wrappers hold three orders. | `scripts/run_posting.sh:26`, `scripts/run_interest_calc.sh:19` |
| Files that CICS holds open | A batch job that writes a master while CICS has it open behaves differently. The harness must run the bracket. | `app/jcl/CLOSEFIL.jcl:26` |

## Deviation register

Nothing gets to differ without a row here. These are the candidates I found by reading. None is approved. Each needs a decision and a signature from someone with the authority. The default for every row is to reproduce the legacy behavior until someone signs a change. The claims are from reading the code, not from running it, so each row is inference until the harness confirms it.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| DR-1 | At the end of the report, the last transaction amount is added again to the page and account totals before the page and grand totals are written. The last account's own total line is not written. | Not decided. Default: reproduce. | Looks like a defect. It changes the report total. | Nobody yet | Finance reads the grand total. inference | `app/cbl/CBTRN03C.cbl:197`, `app/cbl/CBTRN03C.cbl:200` |
| DR-2 | A record outside the date window ends the report loop instead of being skipped. If the DATEPARM window is narrower than the SORT window, the report stops at the first such record, and the input is sorted by card number, not by date. | Not decided. Default: reproduce. | A truncated report with no error. | Nobody yet | The report may be short with no message. inference | `app/cbl/CBTRN03C.cbl:173`, `app/cbl/CBTRN03C.cbl:177` |
| DR-3 | The account REWRITE failure sets reason 109 in a field nothing reads afterward, and the transaction is still written. | Not decided. Default: reproduce. | A posted transaction with no balance update. | Nobody yet | Balance and history disagree. inference | `app/cbl/CBTRN02C.cbl:440`, `app/cbl/CBTRN02C.cbl:554` |
| DR-4 | Two validation checks can both fail and only the last reason is kept. The work balance is one digit narrower than the account fields. | Not decided. Default: reproduce. | Reject reasons on the reject file depend on check order. | Nobody yet | Anything that reads the reject file by reason. | `app/cbl/CBTRN02C.cbl:403`, `app/cbl/CBTRN02C.cbl:187` |
| DR-5 | The debit bucket accumulates negative amounts, and the limit check subtracts it. | Not decided. Default: reproduce. | Sign convention is not written anywhere. | Nobody yet | Every limit decision. | `app/cbl/CBTRN02C.cbl:403`, `app/cbl/CBTRN02C.cbl:551` |
| DR-6 | The interest job passes a fixed date in its PARM, so the ids of the interest transactions repeat every run. | Not decided. | COMBTRAN merges on that id and loads a KSDS, so duplicate ids can drop records. | Nobody yet | The transaction master and the report. inference | `app/jcl/INTCALC.jcl:22`, `app/cbl/CBACT04C.cbl:476` |
| DR-7 | Interest is computed with no rounding clause. The fees step is a stub. | Not decided. Default: reproduce. | Rounding is by truncation. | Nobody yet | Every interest amount. | `app/cbl/CBACT04C.cbl:464`, `app/cbl/CBACT04C.cbl:518` |
| DR-8 | On a failed customer rewrite, the account update issues SYNCPOINT ROLLBACK, but the files are defined RECOVERY(NONE), so the account rewrite is not backed out. | Not decided. | The program believes it rolled back. | Nobody yet | Account and customer data disagree after a failure. inference | `app/cbl/COACTUPC.cbl:4100`, `app/csd/CARDDEMO.CSD:9`, `app/csd/CARDDEMO.CSD:59` |
| DR-9 | New transaction ids are the highest key plus 1, with no lock. | Not decided. | Two concurrent adds can collide. | Nobody yet | Online adds and bill payments. | `app/cbl/COBIL00C.cbl:212`, `app/cbl/COTRN02C.cbl:444` |
| DR-10 | The standalone report job repeats a step name and fixes a 2022 date window in the SORT cards. The online path takes the window from the screen. | Not decided. | Two paths to one report with different rules. | Nobody yet | Which path finance uses. | `app/jcl/TRANREPT.jcl:37`, `app/jcl/TRANREPT.jcl:43` |
| DR-11 | Sign-on compares the typed password to the stored value as plain text, and the stored value is 8 characters in the clear. | Not decided. | Security. | Nobody yet | Every user. | `app/cbl/COSGN00C.cbl:223`, `app/cpy/CSUSR01Y.cpy:21` |

## Exit bar

A wave is done when:

1. The replay or parallel diff is clean, modulo the normalization spec and the deviation register.
2. Every targeted boundary case above passes for the units in that wave.
3. The harness is under version control and runs in CI.
4. The deviation register is signed by someone with the authority to sign it.

Not when the port compiles, and not when it passes tests written alongside the port. Those tests encode the porter's understanding, which is the thing under test.

## Keep the harness after cutover

The comparison harness becomes the regression suite for the modernized system. Budget for maintaining it. The executable specification of this system is not in the source. It is in this harness, in the normalization spec and in the deviation register.
