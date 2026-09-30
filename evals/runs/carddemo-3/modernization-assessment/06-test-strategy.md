# 06 Test strategy

"It passes the tests" is not the bar here. The tree has no tests. The bar is that for the inputs this system really sees, the new code produces the same outputs as the old, and where it does not, someone decided that on purpose and wrote it down in the deviation register below. This applies the `behavioral-equivalence` skill to the plan in `modernization-assessment/03-waves.md`.

## What the tree gives us and what it does not

The tree does hold datasets, so this is not a no-oracle case. It holds inputs only:

- Sample input files for every master and for the daily transaction file, in two encodings: `app/data/ASCII/dailytran.txt` (300 records of 350 bytes plus a line end) and `app/data/EBCDIC`. They are synthetic. The plan cannot claim they cover month end, year end or bad data.
- A listing of the VSAM catalog (`app/catlg/LISTCAT.txt:1`).
- Two runtime bundles for running the system off the mainframe, `samples/m2/mf/CardDemo_runtime.zip` and `samples/m2/unikix/UniKix_CardDemo_runtime_v1.zip`. I did not open them. They may give the emulator that produces golden masters.

It holds no expected output at all: no posted transaction file, no reject file, no report, no statement, no balance after a run. Those outputs have to be produced by running the legacy jobs, or taken from the client's archives.

## Oracle per wave

The oracles in order of strength are parallel run, captured production traffic replay, golden masters from archived outputs, and characterization tests generated from source (weakest, provisional).

| Wave | Oracle | Why | What to ask the client for | Evidence |
|---|---|---|---|---|
| 1 | None needed. Compare return codes and the resulting CICS file state. | No logic. | Names of the CICS regions and how the CEMT fences are used. | `app/jcl/CLOSEFIL.jcl:26` |
| 2 | Golden master from archived SYSOUT of the READ jobs, plus sample input run through the legacy programs on an emulator. Provisional if only the emulator. | The programs print records. | Archived listings from the last year end. | `app/cbl/CBACT02C.cbl:23` |
| 3 | Captured 3270 sessions from CICS journals, replayed against the new screens. Otherwise characterization tests, labeled provisional. | Screen logic has no batch archive. | CICS journal or transaction logs, and the terminal traffic for a month. | `app/cbl/COMEN01C.cbl:156` |
| 4 | None. | Build and demo jobs. | Which build jobs still run. | `app/jcl/TXT2PDF1.JCL:31` |
| 5 | Parallel run for posting and interest. Golden masters from archived generations for the report, the rejects and the statements. | The gold standard exists here: both systems can read the same daily file. | Whether the old system may stay up for at least one month end and a year end. The generation groups keep five generations only (`app/jcl/DEFGDGB.jcl:26`), so ask for older archives. | `app/cbl/CBTRN02C.cbl:256` |
| 6 | Captured production traffic replay plus a diff of the masters after each scripted scenario. | Online writers change the masters in ways only a diff shows. | CICS journals with before and after images of ACCTDAT, CARDDAT and TRANSACT. | `app/cbl/COBIL00C.cbl:379` |
| 7 | Shadow traffic on the message queues, with the new decision logged and not acted on. | A real time approve or decline has no archived answer. | Queue definitions, and the IMS and DB2 definitions. | `app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:262` |

## Normalization spec

Every line is an assertion that a difference does not matter, and so a place a bug can hide. The list is short on purpose and needs a human signature.

| Normalize | Rule | Why it may be safe | Confidence | Evidence |
|---|---|---|---|---|
| Processing timestamp | Ignore TRAN-PROC-TS when comparing posted records. Compare the date part only when a report uses it. | CBTRN02C stamps it from the clock, and the report filters on its first 10 characters. | medium | `app/cbl/CBTRN02C.cbl:437`, `app/cbl/CBTRN03C.cbl:173` |
| Generated transaction ids | For interest records, compare the id after removing the run date prefix, which comes from the job PARM. For bill payment, compare in sequence order only. | The interest id is the PARM date plus a counter. The bill payment id is the last key plus one. | medium | `app/cbl/CBACT04C.cbl:476`, `app/cbl/COBIL00C.cbl:216` |
| Generation numbers | Compare generation (+1) outputs by run, not by generation name. | GDG relative numbers change with every run. | high | `app/jcl/POSTTRAN.jcl:38` |
| SYSOUT DISPLAY lines | Ignore, except the counts CBTRN02C prints (processed and rejected) and its return code of 4 when rejects exist. | The DISPLAY text is diagnostic. The counts and the return code are behavior. | medium | `app/cbl/CBTRN02C.cbl:227`, `app/cbl/CBTRN02C.cbl:229` |
| Record padding | Compare fixed width records after right trimming the FILLER area only, never a data field. | FILLER holds spaces or low values. | medium | `app/cpy/CVTRA05Y.cpy:18` |
| Report page breaks | None. Compare headers, page totals and account totals as printed. | Page totals are behavior. | medium | `app/cbl/CBTRN03C.cbl:282` |

Money fields are not on this list. They are compared in a decimal type with zero tolerance. The account and transaction records use signed zoned decimal with two decimals (`app/cpy/CVACT01Y.cpy:7`, `app/cpy/CVTRA05Y.cpy:10`), so a float in the port is a defect, not noise. The category balance is only nine digits before the decimal point (`app/cpy/CVTRA01Y.cpy:9`) and the report accumulators are the same size (`app/cbl/CBTRN03C.cbl:134`), so the port needs the same overflow behavior, or a recorded deviation.

## Cover the input space deliberately

Production replay covers the common path. These are the cases it will miss, each tied to the code that makes it special.

| Case | What to test | Confidence | Evidence |
|---|---|---|---|
| Reject reasons 100 to 103 | Unknown card, missing account, overlimit, expired account. Include a record that fails both the limit and the expiry check: the second check overwrites the first, so the reject file says 103. | high | `app/cbl/CBTRN02C.cbl:410`, `app/cbl/CBTRN02C.cbl:417` |
| A failed balance rewrite | Reason 109 is set after posting has already written the transaction, and no reject record is written. | high | `app/cbl/CBTRN02C.cbl:554` |
| First posting for an account and category | The category balance record is created, not updated. | high | `app/cbl/CBTRN02C.cbl:495` |
| Negative and zero amounts | A negative amount goes to the cycle debit and a zero amount to the credit. | high | `app/cbl/CBTRN02C.cbl:548` |
| Posting onto a non-empty transaction master | The program opens it for OUTPUT. Test with and without the TRANBKP step before it. | high | `app/cbl/CBTRN02C.cbl:256`, `app/jcl/TRANBKP.jcl:40` |
| Empty daily file and the maximum file | Zero records, and a file at the size the cluster allows (1 cylinder primary, 5 secondary as defined). | medium | `app/jcl/TRANBKP.jcl:55` |
| Interest edge cases | Zero rate skips the record. A missing group falls back to the DEFAULT group. The result is truncated, not rounded. | high | `app/cbl/CBACT04C.cbl:214`, `app/cbl/CBACT04C.cbl:437`, `app/cbl/CBACT04C.cbl:464` |
| Run date supplied by the job | INTCALC always passes 2022071800. Test with the real run date as a parameter. | high | `app/jcl/INTCALC.jcl:22` |
| Report windows | Monthly (last day computed by subtracting one day from the first of next month), yearly (12-31), custom with a date that fails CEEDAYS, and the batch job's fixed window. Include leap day and December to January. | high | `app/cbl/CORPT00C.cbl:229`, `app/cbl/CORPT00C.cbl:250`, `app/cbl/CORPT00C.cbl:399`, `app/jcl/TRANREPT.jcl:43` |
| Fiscal close paths | The monthly interest chain (INTCALC, TRANBKP, COMBTRAN) and the yearly report. These run rarely and no one sees a break for weeks. | medium | `app/scheduler/CardDemo.controlm:66`, `scripts/run_interest_calc.sh:19` |
| The master reload | Reload the account and card masters from the flat files and diff every field. Then run posting and check the balance did not reset silently. | high | `app/jcl/ACCTFILE.jcl:25`, `app/jcl/CARDFILE.jcl:36` |
| Concurrent online writes | Two bill payments at once, to expose the transaction id scheme. | high | `app/cbl/COBIL00C.cbl:212` |
| Bad data already in the files | Records that break their own rules, such as an account with no cross reference. The port must reproduce what legacy does with them. | medium | inference |

## Mainframe traps for the spec

| Trap | Where it applies here | Confidence | Evidence |
|---|---|---|---|
| Packed decimal | Not in the account and transaction copybooks, which are zoned. COMP-3 appears in the report page counter and in statement working storage. Compare in a decimal type either way. | high | `app/cbl/CBTRN03C.cbl:129`, `app/cbl/CBSTM03A.CBL:64` |
| Collating sequence | The masters are KSDS files in key order, and the JCL sorts use character keys. EBCDIC order differs from ASCII. Test the order of TRANSACT by id and the sort by card number. | high | `app/jcl/TRANREPT.jcl:46`, `app/jcl/CREASTMT.JCL:53` |
| REDEFINES | COACTUPC has 43 of them. Test each branch that reads either layout. | medium | `app/cbl/COACTUPC.cbl:83` |
| Record padding and low values | Fixed width records with FILLER. Decide which differences matter and write it down. | medium | `app/cpy/CVACT01Y.cpy:17` |
| Job order | The temporal edges are the list of orders the harness must keep: posting after the backup step and before the index rebuild, fences around all of them, and the sync delay of 36 seconds. | high | `scripts/run_posting.sh:23`, `app/jcl/WAITSTEP.jcl:26` |
| Byte offset contracts in JCL | Five JCL control cards read the transaction record by position. Pin them. | high | `app/jcl/TRANREPT.jcl:41`, `app/jcl/TRANIDX.jcl:27` |
| Encoding | The sample data exists in ASCII and EBCDIC. Confirm the two agree before trusting either. | medium | `app/data/ASCII/acctdata.txt:1` |

## Deviation register

Every behavior below is either wrong or doubtful in the legacy code. None is approved. No row may differ in the port until someone with authority signs it.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| DR-1 | When a transaction fails both the limit and the expiry check, the reject code is the later one, 103 | To be decided | Probably unintended | none yet | Reject file and its readers | `app/cbl/CBTRN02C.cbl:410` |
| DR-2 | A failed account rewrite after posting sets reason 109 but writes no reject record, and the transaction stays posted | To be decided | Silent loss of a reject | none yet | Balance and reject reports | `app/cbl/CBTRN02C.cbl:554` |
| DR-3 | New bill payment id is the last key plus one, so two users can collide | To be decided | Concurrency defect | none yet | Transaction master, report | `app/cbl/COBIL00C.cbl:212` |
| DR-4 | The interest run date is fixed in the JCL as 2022071800 | Run date supplied at run time | Stale constant | none yet | Ids of interest transactions | `app/jcl/INTCALC.jcl:22` |
| DR-5 | The batch report always uses the window 2022-01-01 to 2022-07-06 | Window passed as a parameter | Stale constant | none yet | The transaction report | `app/jcl/TRANREPT.jcl:43` |
| DR-6 | Interest is truncated, not rounded, and the fee routine is empty | To be decided | May be intended, and money is involved | none yet | Account balances | `app/cbl/CBACT04C.cbl:464`, `app/cbl/CBACT04C.cbl:519` |
| DR-7 | Sign on compares an 8 byte clear text password | Identity provider | Security | none yet | Every online transaction | `app/cbl/COSGN00C.cbl:223` |
| DR-8 | CBCUS01C writes each customer record, including the SSN, to SYSOUT | Mask or drop | Privacy | none yet | Listings | `app/cbl/CBCUS01C.cbl:78` |
| DR-9 | CBIMPORT opens a card output file that the job does not define | Define the DD or drop the file | Job cannot run as written | none yet | Branch import | `app/cbl/CBIMPORT.cbl:63` |
| DR-10 | The report generation group is defined twice with limits 10 and 5 | One limit | Retention differs by run order | none yet | Archived reports | `app/jcl/REPTFILE.jcl:27`, `app/jcl/DEFGDGB.jcl:38` |

## Exit bar per wave

A wave is done when the replay diff is clean, modulo the normalization spec and the register; every targeted case above passes; the harness is under version control and runs in CI; and the register is signed by someone with authority. Not when the port compiles, and not when it passes tests the porter wrote.

| Wave | Extra exit condition | Evidence |
|---|---|---|
| 2 | Golden masters stored for every read job, with the copybook in the harness. | `app/cpy/CVACT01Y.cpy:7` |
| 5 | At least one clean parallel month end for posting and interest, and a clean run through the yearly report window. Rollback tested from a backup generation. | `app/jcl/DEFGDGB.jcl:26` |
| 6 | Master diff clean after each online scenario, and the concurrency case passes. | `app/cbl/COBIL00C.cbl:512` |
| 7 | Shadow decisions match the legacy decision on captured messages, with any difference in the register. | inference |

## Keep the harness after cutover

The comparison harness becomes the regression suite for the modernized system. Budget for it. The tree's own wrapper scripts (`scripts/run_full_batch.sh:9`) are the closest thing to an executable specification of the nightly order, so encode them in the harness before they go.
