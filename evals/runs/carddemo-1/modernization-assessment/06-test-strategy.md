# 06 Test strategy

"Correct" here means: for the inputs this system sees, the ported cycle produces the same files and reports as the legacy cycle, and every difference is a row in the deviation register. Telemetry is none, so no archive of production runs has been confirmed. The tree holds sample data only, ASCII and EBCDIC copies of the master files and a daily transaction file (`app/data/ASCII/dailytran.txt`, `app/data/EBCDIC/AWS.M2.CARDDEMO.DALYTRAN.PS`). That is a smoke test, not an oracle.

## Oracle per wave

| Wave | Oracle | Strength | Confidence | Evidence |
|---|---|---|---|---|
| 1, 4 | Characterization from source and job return codes | Weak, provisional | medium | `app/jcl/DEFCUST.jcl:1` |
| 2 | Golden master: run the legacy READ jobs on a master snapshot, diff the output | Strong once a snapshot exists | medium | `app/jcl/READACCT.jcl:1` |
| 5 | Golden master of each rebuilt VSAM file, record by record | Strong | medium | `app/jcl/CUSTFILE.jcl:71` |
| 6 | Parallel run on a month of real daily input, then replay of archived generations | Strongest, needs the client | low | `app/jcl/POSTTRAN.jcl:30` |
| 3, 7, 9 | Replay of captured CICS traffic from journals | Strong if journals exist | low | `app/csd/CARDDEMO.CSD:25` |
| 8 | Characterization until the IMS files are read | Weak, provisional | low | `app/app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl:24` |

## The three must-not-break items

### Daily transaction posting

- **Inputs:** the daily transaction file, the cross-reference, account and category-balance files (`app/jcl/POSTTRAN.jcl:30`, `app/jcl/POSTTRAN.jcl:32`, `app/jcl/POSTTRAN.jcl:39`, `app/jcl/POSTTRAN.jcl:41`).
- **Outputs to diff:** the transaction file, the account file, the category-balance file, and the reject file (`app/jcl/POSTTRAN.jcl:28`, `app/jcl/POSTTRAN.jcl:34`).
- **What is compared:** whole-record equality on all four, with the reject reason codes 100 to 103 (`app/cbl/CBTRN02C.cbl:370`, `app/cbl/CBTRN02C.cbl:393`).
- **Money:** the program computes the running balance in fixed-point (`app/cbl/CBTRN02C.cbl:403`). Use a decimal type in the target and zero tolerance on every amount.
- **Targeted cases:** a card not in the cross-reference (100); an account missing (101); an over-limit transaction (102); a transaction dated after account expiry (103); an empty daily file; a file with duplicate transaction ids; and a rerun after a mid-run abend. The risk pass found no restart logic, so a rerun would post twice. That is a legacy defect, so it goes in the deviation register as an open item, not a test to match.
- **Order:** the temporal edges `TRANBKP` to `POSTTRAN` to `TRANIDX` must hold (`scripts/run_posting.sh:23`, `scripts/run_posting.sh:26`, `scripts/run_posting.sh:30`).

### The account and card master refresh

- **Inputs:** the flat files that ACCTFILE and CARDFILE load (`app/jcl/ACCTFILE.jcl:61`, `app/jcl/CARDFILE.jcl:71`).
- **Outputs to diff:** the rebuilt account and card VSAM clusters, record by record, plus the key length and record size (`app/jcl/ACCTFILE.jcl:36`, `app/jcl/ACCTFILE.jcl:41`).
- **Targeted case:** run the refresh while the CICS files are open, to see what happens. CLOSEFIL does not close the card file (`app/jcl/CLOSEFIL.jcl:26`, `app/csd/CARDDEMO.CSD:25`).
- **Open item:** `run_posting.sh` runs ACCTFILE before POSTTRAN (`scripts/run_posting.sh:17`, `scripts/run_posting.sh:26`). Reloading the account file from a flat file would reset balances on every run. Either the flat file is rewritten somewhere outside the tree, or that wrapper is not what production runs. Ask before building the harness.

### The transaction report

- **Inputs:** the transaction file, cross-reference, type and category files, and a date window (`app/jcl/TRANREPT.jcl:26`, `app/jcl/TRANREPT.jcl:67`, `app/jcl/TRANREPT.jcl:73`).
- **Output to diff:** the 133-column report (`app/jcl/TRANREPT.jcl:78`). Compare as text after the normalization below.
- **Two paths:** the batch job with its window fixed to 2022 (`app/jcl/TRANREPT.jcl:43`) and the online path where CORPT00C fills in the dates (`app/cbl/CORPT00C.cbl:220`). Test both. The fixed window returns RC 0 with an empty report on current data (risk pass, `risks.json`), so the batch test must set the window.
- **Layout test:** assert that bytes 263 for 16 and 305 for 10 of the transaction record are the card number and processing date (`app/jcl/TRANREPT.jcl:41`, `app/jcl/TRANREPT.jcl:42`).
- **Known source behaviour:** CBTRN03C has three behaviours a port would change (`risks.json`). Capture the legacy output first, then decide each one in the deviation register.

## Normalization spec (needs human sign-off)

| Field | Rule | Why it is safe | Evidence |
|---|---|---|---|
| Processing timestamp on posted transactions | Ignore the value, check the format | The program stamps run time (`app/cbl/CBTRN02C.cbl:693`) | `app/cbl/CBTRN02C.cbl:693` |
| Report page and run date headers | Mask | They change every run | `app/cbl/CBTRN03C.cbl:129` |
| Generation numbers (+1) | Compare by position, not number | GDG numbers differ per run | `app/jcl/TRANREPT.jcl:33` |
| Monetary fields | No tolerance, decimal type | Fixed-point source | `app/cpy/CVTRA05Y.cpy:4` |
| Record order | Key order for VSAM, input order for sequential files | A KSDS returns key order, and a port that sorts in ASCII changes it | `app/jcl/TRANREPT.jcl:46` |
| Fixed-width padding | Compare raw bytes, no trimming | Reports and VSAM are fixed width | `app/jcl/POSTTRAN.jcl:36` |

Collating sequence matters in two places. The report sorts on the card number as zoned decimal (`app/jcl/TRANREPT.jcl:41`), which is safe. Any sort on a text field must be tested under EBCDIC order.

## Cases the harness must add

- Month-end and year-end dates. The interest cycle runs monthly with a hard-coded run parameter, `2022071800` (risk pass, `risks.json`), and that becomes part of the transaction id. If it is not changed, ids repeat. Test two consecutive months.
- Zero-record and maximum-size daily files.
- Bad data already in the files. The sample data is the only source until the client supplies production snapshots.
- The sequence TRANREPT then TRANBKP then COMBTRAN. The report also writes the backup generation, so a report run in between changes what `BKUP(0)` means (`app/jcl/TRANREPT.jcl:33`, `app/jcl/COMBTRAN.jcl:24`).

## What to ask the client for

1. Archived generations of the posting reject file, the transaction backup and the report, for at least three months including a quarter-end.
2. A snapshot of every master file before and after one real posting run.
3. SMF or scheduler logs that show which of CA-7 and Control-M is live.
4. CICS journals for one week, for waves 3 and 7.

## Deviation register (starts empty)

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| D-001 | Posting has no restart, so a rerun after an abend posts twice | Not decided | Open item | Not approved | Account and category balances | `app/cbl/CBTRN02C.cbl:556` |
| D-002 | Report loop exits on the first out-of-window record; last card total never written | Not decided | Open item | Not approved | Report totals | `app/cbl/CBTRN03C.cbl:166` |

## Exit bar for wave 6

The replay diff over the parallel-run month is clean modulo the normalization spec and the register. Every targeted case above passes. The harness is in version control and runs in CI. The register is signed by someone who can sign it. The harness stays after cutover as the regression suite.
