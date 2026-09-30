# 06 Test strategy

The bar is not that the port compiles or that its own tests pass. The bar is that for the inputs this system actually sees, the new code produces the same outputs as the old, and any difference was decided on purpose and written in the deviation register below. This file applies the `behavioral-equivalence` skill to the seven waves in `03-waves.md`.

## What oracle exists here

The tree holds seeded test data, not production data: nine flat files in ASCII and thirteen in EBCDIC (`app/data/ASCII/dailytran.txt:1`, `app/data/EBCDIC/AWS.M2.CARDDEMO.DALYTRAN.PS`), an IMS unload (`app/app-authorization-ims-db2-mq/data/EBCDIC/AWS.M2.CARDDEMO.IMSDATA.DBPAUTP0.dat`), and a catalog listing of 3,956 lines (`app/catlg/LISTCAT.txt:1`). The daily file has 300 transactions and the account, card, cross reference and customer files have 50 records each. That is a synthetic oracle, rank 4 in the skill's order, so every coverage claim built only on it is **provisional**.

The stronger oracles are on the client's mainframe and are not in the tree. The system writes almost all of them as generation data groups:

| Oracle source | What it holds | Evidence |
|---|---|---|
| TRANSACT.BKUP generations | One copy of the transaction master per run of TRANBKP | `app/jcl/TRANBKP.jcl:29-33` |
| SYSTRAN generations | Every interest transaction INTCALC made | `app/jcl/INTCALC.jcl:37-41` |
| DALYREJS generations | Every reject POSTTRAN wrote, with a reason code | `app/jcl/POSTTRAN.jcl:34-38` |
| TRANREPT generations | Every transaction report ever produced | `app/jcl/TRANREPT.jcl:76-80` |
| TCATBALF.BKUP generations and TCATBALF.REPT | Category balance snapshots and a printed listing | `app/jcl/PRTCATBL.jcl:35-41` |
| STATEMNT.PS and STATEMNT.HTML | Customer statements | `app/jcl/CREASTMT.JCL:71-75` |
| READACCT outputs | Three formats of the whole account master | `app/jcl/READACCT.jcl:37-48` |
| EXPORT.DATA | The branch export, an executable spec of that format | `app/jcl/CBEXPORT.jcl:30-38` |
| Job logs, SMF, CA-7 run history | Which jobs ran, return codes and elapsed time; also telemetry for `05-dead-code.md` | inference: not in the tree |
| CICS journals | Captured online inputs for replay | inference: not in the tree |

**Ask the client to supply, in this order:** twelve months of TRANSACT.BKUP, DALYREJS, SYSTRAN and TRANREPT generations including a month end and a fiscal year end; the DALYTRAN files that produced them; the account, card, cross reference and customer masters as of the start of that period; job logs for the same period; a sample of CICS transaction logs; and a copy of the CA-7 definitions.

## Oracle per wave

| Wave | Oracle | Rank | Why | Evidence |
|---|---|---|---|---|
| 1 | Job return codes and catalog state | 4 | Nothing to compare except that the GDG bases exist | `app/jcl/DEFGDGB.jcl:24` |
| 2 | READACCT and the READ jobs' outputs from the legacy system, replayed on the same masters | 3 | Archived files exist and are cheap to diff | `app/jcl/READACCT.jcl:37` |
| 3 | Screen and COMMAREA capture from legacy CICS, replayed against the router | 2 if journals exist, else 4 | Sign on and menu are deterministic | `app/cpy/COMEN02Y.cpy:28` |
| 4 | Loaded file equals the flat file input, record for record | 3 | REPRO copies the input | `app/jcl/ACCTFILE.jcl:61` |
| 5 | Parallel run: legacy and target process the same DALYTRAN and compare all three masters, the reject file, the SYSTRAN file and the report | 1 | The old system stays up until wave 5 exits | `app/jcl/POSTTRAN.jcl:23` |
| 6 | Replay of captured online updates, then a master diff | 2 | Journals or a scripted session | `app/cbl/COACTUPC.cbl:3894` |
| 7 | Replay of MQ messages and IMS unloads against the adapters | 2 | The unload file shows the shape | `app/app-authorization-ims-db2-mq/jcl/UNLDPADB.JCL:33` |

Parallel run in wave 5 is possible because the legacy jobs keep running; the shim from `03-waves.md` decides which side owns the schedule. Ask the client before assuming it is not.

## Normalization spec

Every line is a claim that a difference does not matter. Each is a place a bug can hide, so a person signs this list.

| Item | Rule | Why | Evidence |
|---|---|---|---|
| Processing timestamp on posted transactions | Ignore TRAN-PROC-TS on records CBTRN02C writes | It is the run clock | `app/cbl/CBTRN02C.cbl:693` |
| Timestamps on interest transactions | Ignore both timestamps in the SYSTRAN records | Same clock | `app/cbl/CBACT04C.cbl:496-498` |
| Job numbers, GDG generation names, catalog dates | Ignore | Assigned by the system | `app/jcl/POSTTRAN.jcl:38` |
| Interest transaction ids | Compare exactly, given the same PARM | PARM date plus a 6 digit counter | `app/cbl/CBACT04C.cbl:476-479` |
| Online transaction ids | Do not compare values, compare that each is unique and above the previous maximum | They are the highest key plus one | `app/cbl/COBIL00C.cbl:212-219` |
| Money fields | Compare as decimal with zero tolerance. Account fields are S9(10)V99, the transaction amount S9(09)V99, all DISPLAY, none packed | Floating point would be a defect | `app/cpy/CVACT01Y.cpy:7-14`, `app/cpy/CVTRA05Y.cpy:10` |
| Interest arithmetic | Truncate, do not round, to two decimals | The COMPUTE has no ROUNDED | `app/cbl/CBACT04C.cbl:464-465` |
| Sign overpunch | Decode signed DISPLAY fields to numbers before comparing. The ASCII data keeps the EBCDIC overpunch letters, for example a trailing brace for a positive zero | A byte diff of ASCII against EBCDIC output will fail on every signed field | `app/data/ASCII/acctdata.txt:1` |
| Key order | Compare in EBCDIC collating order for any keyed browse or sort | A VSAM key file returns records in key order and downstream code may depend on it; an ASCII sort puts digits before letters and EBCDIC does the reverse | `app/jcl/COMBTRAN.jcl:28-30`, `app/cbl/CBACT04C.cbl:437` |
| Record padding | Trailing spaces in text fields are equal; low values are not equal to spaces until a person decides | Fixed width records | `app/jcl/POSTTRAN.jcl:36` |
| Reject records | Compare the 350 byte transaction and the 80 byte trailer, including the four digit reason | Trailer is the audit trail | `app/cbl/CBTRN02C.cbl:176-182` |
| Report text | Compare after removing only the run date in the header; keep page breaks, totals and edited numbers | The edited pictures set the output format | `app/cpy/CVTRA07Y.cpy:30`, `app/cpy/CVTRA07Y.cpy:54` |
| Return codes | Compare exactly; CBTRN02C ends with 4 when it rejects | Downstream jobs may test it | `app/cbl/CBTRN02C.cbl:229-231` |
| SYSOUT and DISPLAY lines | Ignore | CBTRN03C prints every record it reads | `app/cbl/CBTRN03C.cbl:180` |
| REDEFINES | Test every branch that reads either layout | Two layouts over the same bytes | `app/cbl/CBTRN02C.cbl:135`, `app/cbl/CBTRN02C.cbl:160` |

## Cases to add beyond replay

Replay covers the common path. These paths need cases of their own. A hand check against the seeded data (300 transactions, 50 accounts, 50 cross references), done on initial balances and ignoring accumulation, found no missing card, no missing account and no expired account, and 13 transactions over the credit limit. So the seed exercises one of the five reject reasons (inference from my own check, not a script), and the rest need synthetic cases.

| Case | Why | Evidence |
|---|---|---|
| Reject 100, card not in cross reference | Never exercised by the seed | `app/cbl/CBTRN02C.cbl:385` |
| Reject 101, account missing | Never exercised by the seed | `app/cbl/CBTRN02C.cbl:397` |
| Reject 102, over limit, and 103, expired, on the same record | Reason 103 overwrites 102, so only one code shows | `app/cbl/CBTRN02C.cbl:407-420` |
| Reject 109 at rewrite | The reason is set after the transaction is written and nothing checks it | `app/cbl/CBTRN02C.cbl:554-559` |
| Transaction with no category balance record | Takes the create branch | `app/cbl/CBTRN02C.cbl:495-499` |
| Negative, zero and maximum amounts | Credit and debit branch on sign | `app/cbl/CBTRN02C.cbl:548-552` |
| Expiry date equal to the transaction date | String comparison on ten characters | `app/cbl/CBTRN02C.cbl:414` |
| Account with no group, group not in the rate table, rate of zero | Falls back to DEFAULT, or skips | `app/cbl/CBACT04C.cbl:214`, `app/cbl/CBACT04C.cbl:436-438` |
| Month end, quarter end, fiscal year end, leap day | Interest runs monthly in the scheduler | `app/scheduler/CardDemo.controlm:66-72` |
| Empty daily file and the largest one the master can hold | The empty case must still recreate the master and end with return code 0 | `app/cbl/CBTRN02C.cbl:202-219` |
| Second run of INTCALC with the same PARM | Duplicate keys reach COMBTRAN | `app/jcl/INTCALC.jcl:22`, `app/jcl/COMBTRAN.jcl:48` |
| Transaction report with a record outside the window | The loop ends at the first such record; a port must copy or log it | `app/cbl/CBTRN03C.cbl:173-178` |
| Report with one card, and with the last card's total | Last account total is never written and the last amount is added twice | `app/cbl/CBTRN03C.cbl:198-203` |
| Online request for the monthly, yearly and custom report | Both windows come from the screen | `app/cbl/CORPT00C.cbl:214-255` |
| Bad data already in the files | The legacy behavior on it is the spec | inference: needs the client's masters |
| The paths that run only at fiscal close | The single most common cause of a failure found six months after cutover | `app/scheduler/CardDemo.controlm:65-89` |

## Order the harness must keep

The temporal edges are the orders a harness must not disturb. Nothing in the tree enforces them by completion: the wrappers use `sleep`.

| Order | Reason | Evidence |
|---|---|---|
| CLOSEFIL before every refresh, OPENFIL after | The only barrier between batch and online | `scripts/run_posting.sh:13`, `scripts/run_posting.sh:34` |
| DEFGDGB and DALYREJS before TRANBKP, POSTTRAN, INTCALC, COMBTRAN | Generation bases must exist | `app/jcl/DEFGDGB.jcl:24-59` |
| TRANBKP before POSTTRAN | POSTTRAN opens the master for output | `scripts/run_posting.sh:23`, `scripts/run_posting.sh:26` |
| POSTTRAN before INTCALC | Interest reads the category balances posting updates | `scripts/run_full_batch.sh:47`, `scripts/run_full_batch.sh:51` |
| INTCALC before COMBTRAN | COMBTRAN merges the SYSTRAN generation | `scripts/run_interest_calc.sh:19`, `scripts/run_interest_calc.sh:26` |
| XREFFILE before INTCALC | INTCALC reads the cross reference by its alternate index | `app/jcl/XREFFILE.jcl:72-103`, `app/cbl/CBACT04C.cbl:394-395` |
| TRANEXTR before TRANTYPE and TRANCATG | The DB2 unload writes their input files | `app/app-transaction-type-db2/jcl/TRANEXTR.jcl:73`, `app/jcl/TRANTYPE.jcl:57` |
| CBPAUP0J before POSTTRAN, if CA-7 is right | Trigger chain in an unparsed scheduler | `app/scheduler/CardDemo.ca7:43`, `app/scheduler/CardDemo.ca7:70` |

## Deviation register

Seeded with what I found while reading. Every row is a decision for a person; "Approved by" is empty on purpose. Nothing may differ without a signed row.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| D-001 | Transaction report adds the last record's amount to the totals a second time at end of file | To decide: reproduce or fix | Looks like a defect | pending | Grand total and last page total on every report | `app/cbl/CBTRN03C.cbl:198-203` |
| D-002 | Transaction report ends at the first record outside the date window | To decide | Looks like a defect; input is sorted by card, not date | pending | A report can be silently short | `app/cbl/CBTRN03C.cbl:173-178` |
| D-003 | Last account total never written | To decide | Looks like a defect | pending | Last card's subtotal missing | `app/cbl/CBTRN03C.cbl:181-184` |
| D-004 | A failed account rewrite in posting is swallowed after the transaction is written | To decide | Money can post without an account update | pending | Account balance versus transaction master | `app/cbl/CBTRN02C.cbl:554-559` |
| D-005 | When a record is both over limit and expired only reason 103 is written | To decide | Loses a reason | pending | Reject file consumers | `app/cbl/CBTRN02C.cbl:407-420` |
| D-006 | Interest truncates to two decimals | Keep unless the business says otherwise | Rounding would change money | pending | Every account with interest | `app/cbl/CBACT04C.cbl:464-465` |
| D-007 | Over limit test subtracts the cycle debit, which is stored negative | To decide | Sign convention may be wrong | pending | Which transactions are rejected | `app/cbl/CBTRN02C.cbl:403-405`, `app/cbl/CBTRN02C.cbl:551` |
| D-008 | Dates are hardcoded in JCL: interest PARM and the report sort window | Parameters | Intended change | pending | Ids and windows | `app/jcl/INTCALC.jcl:22`, `app/jcl/TRANREPT.jcl:43-44` |
| D-009 | Sign on compares a clear text password | Hash | Intended change; touches the user load job and three programs | pending | Every user | `app/cbl/COSGN00C.cbl:223`, `app/jcl/DUSRSECJ.jcl:35-44` |
| D-010 | Online transaction ids are the highest key plus one | Sequence | Race with posting | pending | Duplicate or gapped ids | `app/cbl/COBIL00C.cbl:212-219`, `app/cbl/COTRN02C.cbl:444-451` |
| D-011 | Online payment and manual add write a transaction but not the category balance | To decide | The batch path updates it | pending | Interest base | `app/cbl/COBIL00C.cbl:233`, `app/cbl/CBTRN02C.cbl:440` |
| D-012 | Two GDG definitions of TRANREPT, limits 10 and 5 | One | Inconsistent | pending | Retention of reports | `app/jcl/REPTFILE.jcl:25-28`, `app/jcl/DEFGDGB.jcl:36-40` |

## Exit bar per wave

A wave is done when all four hold:

- the replay diff is clean modulo the normalization spec and the signed deviation register;
- every targeted case above that belongs to the wave passes;
- the harness is under version control and runs in CI;
- the deviation register is signed by someone with the authority to sign it.

| Wave | Extra condition | Evidence |
|---|---|---|
| 1 | Legacy CLOSEFIL and OPENFIL still run; GDG bases exist on the target | `app/jcl/CLOSEFIL.jcl:26` |
| 2 | The target reads all four record layouts byte for byte | `app/cpy/CVACT01Y.cpy:4` |
| 3 | Every menu option routes, including those still on legacy CICS | `app/cpy/COMEN02Y.cpy:28-89` |
| 4 | Each loaded file equals its flat file | `app/jcl/DISCGRP.jcl:54` |
| 5 | A full month of parallel runs, including a month end, with no unexplained diff in three masters, rejects, SYSTRAN and the report | `app/jcl/POSTTRAN.jcl:23` |
| 6 | A scripted concurrent batch and online session ends with equal masters | `app/cbl/COACTUPC.cbl:3894` |
| 7 | Every adapter passes replay; IMS, DB2 and MQ schemas have been read and reconciled | `app/app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl:25` |

## Keep the harness after cutover

The comparison harness becomes the regression suite for the modernized system. Budget for maintaining it. Teams routinely throw it away at cutover and lose the only executable specification the system ever had.
