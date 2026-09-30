# 06 Test strategy

Applied from the behavioral-equivalence skill. "It passes the tests" is not the bar. The legacy system has no tests. The bar is that for the inputs this system really sees, the port produces the same outputs, and where it does not, someone decided that on purpose and wrote it down.

## What the tree gives us as an oracle, and what it does not

The tree holds input data and no expected outputs. It has sample masters and a 300 record daily transaction file in EBCDIC and in ASCII (`app/data/ASCII/dailytran.txt:1`, `app/data/EBCDIC/AWS.M2.CARDDEMO.DALYTRAN.PS`), compiled runtime bundles that let the legacy programs run off the mainframe (`samples/m2/mf/CardDemo_runtime.zip`, `samples/m2/unikix/UniKix_CardDemo_runtime_v1.zip`), and a catalog listing of the datasets from a 2022 run (`app/catlg/LISTCAT.txt:1`). The catalog shows that the reject, interest, backup and report GDGs each retain five generations (`app/catlg/LISTCAT.txt:696`, `app/catlg/LISTCAT.txt:1112`, `app/catlg/LISTCAT.txt:1541`, `app/catlg/LISTCAT.txt:1643`), but the listing is the catalog entry, not the data. So the outputs have to come from one of two places.

- Run the legacy on the runtime bundle with the sample inputs, and treat what it writes as a golden master. That is weak evidence because it was not produced by the client's system on the client's data.
- Ask the client to supply, in this order: (1) the retained GDG generations of DALYREJS, SYSTRAN, TRANSACT.BKUP, TRANSACT.COMBINED and TRANREPT; (2) 12 months of daily transaction files and the job logs for the posting cycle; (3) the printed and archived reports and statements, including the month-end and year-end ones; (4) SMF or job accounting records for the last 12 months, which are also the telemetry the dead-code register lacks; (5) CICS journals or terminal scripts for the online screens; (6) the extract files sent to partners, if any leave the building. I found no partner extract in the tree. The one FTP job is a test file put on a fixed host (`app/jcl/FTPJCL.JCL:40`).

## Oracle per wave

Different waves legitimately use different oracles. The strongest one available is listed first.

| Wave | Oracle | Why this one | Confidence | Evidence |
|---|---|---|---|---|
| 1 Utilities | Characterization. Return codes and the resulting catalog entries after each job. | No data flows through these jobs. The catalog is the only observable. | medium | `app/jcl/DEFGDGB.jcl:25`, `app/catlg/LISTCAT.txt:1527` |
| 2 Read-only readers | Parallel run of legacy and port on the same master snapshot, and a golden master from the retained outputs if the client has them | Read-only, so there is no risk in running both. The sample masters are 50 records each. | high | `app/data/ASCII/acctdata.txt:1`, `app/cbl/CBACT01C.cbl:29` |
| 3 Sign-on, menus, screens | Scripted screen sessions on the legacy region, replayed on the port, with the screen text compared. CICS journals if the client has them. | The screens read only. The sign-on and menu route through a table, so every table row is a test. | medium | `app/cpy/COMEN02Y.cpy:28`, `app/cbl/COSGN00C.cbl:223` |
| 4 Data load utilities | Golden master. The file content after each reload, key by key, and the alternate index contents. | The jobs are deterministic given their inputs. | medium | `app/jcl/ACCTFILE.jcl:61`, `app/jcl/TRANIDX.jcl:52` |
| 5 Posting, interest, statements, report | Parallel run on the daily transaction file, with the whole TRANSACT rebuild cycle inside the harness. Replay of 12 months of daily files including month-end and year-end. Golden master from the retained GDG generations. | The strongest option, and it is available because the old system stays up. The posting writes the account master, so the parallel run has to start from a copy of it. | medium | `app/jcl/POSTTRAN.jcl:23`, `app/cbl/CBTRN02C.cbl:256`, `scripts/run_full_batch.sh:47` |
| 6 Online maintenance | Shadow replay. The same recorded transactions run against a copy of the masters on each side, then the master state is compared, not the screens. | Online writes cannot be run twice on one master, so each side gets its own copy. | medium | `app/cbl/COACTUPC.cbl:573`, `app/cbl/COBIL00C.cbl:212` |
| 7 Authorization, DB2, IMS | Golden master from the unload jobs. UNLDPADB and TRANEXTR output is an executable description of the data. MQ messages replayed for COPAUA0C. | The DBD, PSB and DDL are not read, so characterization from source is not enough. | low | `app/app-authorization-ims-db2-mq/jcl/UNLDPADB.JCL:39`, `app/app-transaction-type-db2/jcl/TRANEXTR.jcl:88` |

Characterization tests generated from the source encode what the code says and not what it does. Where a wave falls back to them, say that in the wave's exit note and label the coverage provisional.

## Normalization spec (for a human to sign off)

Every entry is an assertion that a difference does not matter, and each is a place a bug can hide. Keep this list short.

| Entry | What is ignored | Why it is safe, and the limit | Confidence | Evidence |
|---|---|---|---|---|
| N1 | Processing timestamps on posted and interest records | They come from the clock at run time. Compare every other field. Keep the original timestamp field, which comes from the input. | high | `app/cbl/CBTRN02C.cbl:692`, `app/cbl/CBTRN02C.cbl:693` |
| N2 | The timestamp on online payments and transactions | Taken from the region clock. | high | `app/cbl/COBIL00C.cbl:251` |
| N3 | GDG generation numbers and job numbers | Assigned by the system. Compare by position in the generation list. | high | `app/jcl/POSTTRAN.jcl:38` |
| N4 | Physical VSAM layout: control interval free space, record order inside a control interval | Not visible to programs. Key order is visible and is not ignored. | medium | `app/jcl/TRANBKP.jcl:54` |
| N5 | Trailing spaces and low values in fixed width padding | Decide once whether spaces and binary zeros count as equal. The filler is large (178 bytes in the account record), so this matters. | medium | `app/cpy/CVACT01Y.cpy:1` |
| N6 | Page, date and run headers in the printed report | Only if the report prints the run date. The record and total lines are not ignored. | medium | `app/cbl/CBTRN03C.cbl:173` |
| N7 | The order of records with equal sort keys | The report sorts by card number only, so the order within one card is whatever the sort utility produced, because equal-key order is not guaranteed and the control cards set no EQUALS option. Confirm that order was incidental. Downstream consumers may depend on it. | low | `app/jcl/TRANREPT.jcl:47`, `app/jcl/TRANREPT.jcl:41` |

Not ignored, on purpose. Money. Every amount field in the masters and the daily file is signed DISPLAY numeric with two implied decimals (`app/cpy/CVACT01Y.cpy:1`, `app/cpy/CVTRA05Y.cpy:1`). Compare in a decimal type with zero tolerance. Interest is `balance * rate / 1200` with no ROUNDED, so it truncates, and a port that rounds is wrong (`app/cbl/CBACT04C.cbl:464`). Collating sequence. A KSDS returns records in EBCDIC key order, and the programs may depend on it, so compare after sorting in EBCDIC order or load the target in the same order. The tree carries both encodings of the sample data, which makes this a direct test (`app/data/ASCII/acctdata.txt:1`). REDEFINES. COACTUPC has 43 and CBTRN02C and CBACT04C have two each, so every branch that reads an overlaid layout needs a case (`app/cbl/COACTUPC.cbl:573`, `app/cbl/CBTRN02C.cbl:256`).

## Cases to add beyond replay

Replay covers the common path. These are the dangerous ones.

| Case | Why | Confidence | Evidence |
|---|---|---|---|
| Card number missing from the cross reference (reject 100) | The reject file is the only output of the failure. | high | `app/cbl/CBTRN02C.cbl:40` |
| Account not found (reject 101), over the limit (102), card expired (103), and a record that is both 102 and 103 | When both apply, 103 overwrites 102. Decide if that is kept. | high | `app/cbl/CBTRN02C.cbl:410`, `app/cbl/CBTRN02C.cbl:417` |
| First transaction for an account and category, when the category balance record is missing | The program creates it. | high | `app/cbl/CBTRN02C.cbl:503` |
| Reject count above zero | The job ends with return code 4, which an operator or scheduler may act on. | medium | `app/cbl/CBTRN02C.cbl:230` |
| An empty daily transaction file | Posting must end clean and TRANSACT stays empty. | medium | `app/cbl/CBTRN02C.cbl:256` |
| Account with no disclosure group | Interest falls back to the DEFAULT group. | high | `app/cbl/CBACT04C.cbl:437` |
| Month end, December roll over, leap day | The monthly report end date is computed with INTEGER-OF-DATE, and the yearly report is fixed at 12/31. | high | `app/cbl/CORPT00C.cbl:225`, `app/cbl/CORPT00C.cbl:230`, `app/cbl/CORPT00C.cbl:250` |
| Report date that the LE date service flags with message 2513 | The report screen accepts it as valid. | high | `app/cbl/CORPT00C.cbl:399`, `app/cbl/CORPT00C.cbl:419` |
| Report through the online path and through the batch job, with the same window | Two copies of the steps exist and one has a fixed 2022 window. | high | `app/jcl/TRANREPT.jcl:43`, `app/proc/TRANREPT.prc:41` |
| Two bill payments at once | The next transaction id is the highest key plus one. | medium | `app/cbl/COBIL00C.cbl:212`, `app/cbl/COBIL00C.cbl:217` |
| The full posting cycle run twice in a row | TRANBKP resets the file and the backup GDG keeps five generations. The second run must not lose the first. | medium | `app/jcl/TRANBKP.jcl:40`, `app/jcl/DEFGDGB.jcl:25` |
| A failed backup step before the delete | The delete step has no COND. Decide whether the port keeps that. | medium | `app/jcl/TRANBKP.jcl:37`, `app/jcl/TRANBKP.jcl:51` |
| The paths that only run at fiscal close | Monthly interest and the combine step, the yearly report, and the statement run. | high | `app/jcl/INTCALC.jcl:22`, `app/jcl/COMBTRAN.jcl:48`, `app/jcl/CREASTMT.JCL:79` |

## Job order the harness must keep

The temporal edges in `modernization-assessment/graph.json` are the orders the harness must keep. The ones that carry the must-not-break items are below. Two schedulers disagree about what comes before POSTTRAN, so the harness should run both orders until the client says which is production.

| Order | Source | Confidence | Evidence |
|---|---|---|---|
| CLOSEFIL, then the refresh jobs, then TRANBKP, then POSTTRAN, then INTCALC, then TRANBKP, then COMBTRAN, then TRANIDX, then OPENFIL | Full batch wrapper | high | `scripts/run_full_batch.sh:13`, `scripts/run_full_batch.sh:47`, `scripts/run_full_batch.sh:51`, `scripts/run_full_batch.sh:55`, `scripts/run_full_batch.sh:58`, `scripts/run_full_batch.sh:62`, `scripts/run_full_batch.sh:66` |
| CLOSEFIL, ACCTFILE, TCATBALF, TRANBKP, POSTTRAN, TRANIDX, OPENFIL | Posting wrapper | high | `scripts/run_posting.sh:13`, `scripts/run_posting.sh:17`, `scripts/run_posting.sh:20`, `scripts/run_posting.sh:23`, `scripts/run_posting.sh:26`, `scripts/run_posting.sh:30`, `scripts/run_posting.sh:34` |
| CLOSEFIL, then CBPAUP0J, then POSTTRAN, then WAITSTEP, then OPENFIL | CA-7 listing, not parsed by the extractor (inference) | medium | `app/scheduler/CardDemo.ca7:43`, `app/scheduler/CardDemo.ca7:70`, `app/scheduler/CardDemo.ca7:97`, `app/scheduler/CardDemo.ca7:124` |
| CLOSEFIL, TRANBKP, WAITSTEP, OPENFIL | Control-M daily folder | high | `app/scheduler/CardDemo.controlm:5`, `app/scheduler/CardDemo.controlm:9`, `app/scheduler/CardDemo.controlm:15`, `app/scheduler/CardDemo.controlm:21` |
| CLOSEFIL, INTCALC, COMBTRAN, WAITSTEP, OPENFIL | Control-M monthly folder | high | `app/scheduler/CardDemo.controlm:66`, `app/scheduler/CardDemo.controlm:70`, `app/scheduler/CardDemo.controlm:76`, `app/scheduler/CardDemo.controlm:82` |
| The report needs the transaction file POSTTRAN wrote. No scheduler or wrapper orders it. | Data dependency only (inference) | medium | `app/jcl/TRANREPT.jcl:26`, `app/cbl/CBTRN02C.cbl:34` |

## Deviation register (seeded)

Nothing gets to differ from legacy without a row here. These are the legacy behaviors I found that a client may not want reproduced. Every row is proposed. None is approved.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| DR-01 | When a transaction is both over the limit and after expiry, the reject reason is 103 and 102 is lost | Undecided. Either keep, or record both | Reason precedence is not documented | Pending, client | Reject file consumers and reconciliation by reason | `app/cbl/CBTRN02C.cbl:410`, `app/cbl/CBTRN02C.cbl:417` |
| DR-02 | If the account rewrite fails after the category balance was updated, a 109 flag is set but the transaction is still written | Undecided | A partial posting is not visible to the caller | Pending, client | Balance and history can disagree | `app/cbl/CBTRN02C.cbl:556`, `app/cbl/CBTRN02C.cbl:442` |
| DR-03 | Interest truncates and is never rounded | Undecided. Keep for equivalence, then decide | A change moves every interest transaction | Pending, client | Statements, ledger, regulatory reports | `app/cbl/CBACT04C.cbl:464` |
| DR-04 | The interest run date is a JCL constant (2022-07-18) that becomes the transaction id prefix | Pass the run date in | A constant date is a defect if not changed each run | Pending, client | Transaction ids, sort order in the combine step | `app/jcl/INTCALC.jcl:22`, `app/cbl/CBACT04C.cbl:476` |
| DR-05 | The next transaction id is the highest key plus one, for payments and added transactions | Use a generated key | Two users can take the same id | Pending, client | Ids seen by users and downstream sorts | `app/cbl/COBIL00C.cbl:217`, `app/cbl/COTRN02C.cbl:444` |
| DR-06 | The sign-on compares an 8 byte password in clear | Hashed credentials | Security. The client is unlikely to want this reproduced. | Pending, client | Every user record and the user admin screens | `app/cbl/COSGN00C.cbl:223`, `app/cpy/CSUSR01Y.cpy:21` |
| DR-07 | The report screen treats LE message 2513 as a valid date | Undecided | Not documented | Pending, client | Which report windows are accepted | `app/cbl/CORPT00C.cbl:399` |
| DR-08 | The batch report job has a fixed 2022 date window, and it also writes a TRANSACT.BKUP generation | Parameterize the window, and stop writing a backup generation | The window is a leftover, and the extra generation pushes real backups off a five deep GDG | Pending, client | Backup retention and the archived report set | `app/jcl/TRANREPT.jcl:43`, `app/jcl/TRANREPT.jcl:33`, `app/jcl/DEFGDGB.jcl:25` |
| DR-09 | The TRANREPT GDG is defined with limit 5 in one job and limit 10 in another | One limit | Retention depends on which job ran | Pending, client | How many report generations are kept | `app/jcl/DEFGDGB.jcl:37`, `app/jcl/REPTFILE.jcl:27` |
| DR-10 | The delete of the transaction file runs even if the backup step failed | Stop the delete if the backup fails | Data loss on a failed backup | Pending, client | The transaction history | `app/jcl/TRANBKP.jcl:37`, `app/jcl/TRANBKP.jcl:51` |

## The exit bar per wave

A wave is done when the replay diff is clean modulo the normalization spec and the deviation register, every case above that applies passes, the harness is under version control and runs in CI, and someone with the authority signs the deviation register. Not when the port compiles. Not when it passes tests written beside the port, because those encode the porter's understanding, which is the thing under test.

## Keep the harness after cutover

The comparison harness becomes the regression suite for the modernized system. Budget for it. The temporal rows above and the deviation register go with it. Teams routinely throw the harness away at cutover and lose the only executable specification the system had.
