# 06 Test strategy

The legacy tree holds no tests, and no archived outputs or datasets (the repository carries source, JCL and layouts only). The oracle therefore has to come from the client's production environment. Everything below is a request to the client, ranked by strength.

## Oracle per wave

| Wave | Oracle | What to ask the client for | Strength | Evidence |
|---|---|---|---|---|
| 1, 4 | Job return codes and listings | Last 90 days of JES output for the setup and build jobs | weak, enough for low-risk work | inference |
| 2 | Golden master | One archived copy of each READ* job's output, next to the master file snapshot it read | medium | `app/jcl/READACCT.jcl:1` |
| 3 | Characterization of screens | CICS journal or recorded 3270 sessions for sign-on and the menus | medium | inference |
| 5 | Golden master | Archived statement and export output, plus the flat files each reload read | medium | `app/jcl/CARDFILE.jcl:36` |
| 6 | Parallel run, falling back to replay | The old and new platforms both process the same daily transaction file for at least one month-end. Fall back to archived `TRANSACT.BKUP` and `DALYREJS` generations | strong if parallel run is possible | `app/jcl/POSTTRAN.jcl:23` |
| 7 | Captured traffic replay | CICS journals for the account, card and transaction update screens across a month-end | medium | inference |
| 8, 9 | Characterization tests, provisional | DB2 DDL, IMS DBD and PSB, and an unload of the authorization database | weak | inference |

Ask first whether a parallel run is possible for wave 6. Teams assume not and are often wrong.

## The three must-not-break anchors

| Item | What to compare | Normalization | Evidence |
|---|---|---|---|
| Daily transaction posting | After `CBTRN02C`: the transaction master, the account master balances, the category-balance file, and the reject file | Zero tolerance on every monetary field. Ignore the timestamp written at post time. Do not ignore record order in `DALYREJS` | `app/jcl/POSTTRAN.jcl:23` |
| Account and card master refresh | After ACCTFILE and CARDFILE: every record in the rebuilt KSDS files and the alternate index and path, record for record | Keys and contents exact. Ignore the cluster's physical attributes | `app/jcl/ACCTFILE.jcl:22` |
| Transaction report | The report file `CBTRN03C` writes for a fixed date range, on both the batch and the online path | Ignore page headers and run dates. Date parameters are inputs, not noise. The report's totals must match to the cent | `app/proc/TRANREPT.prc:57` |

## Normalization spec (starting list, needs a human to sign)

- Timestamps written at run time, and job and generation numbers. Everything else on the three anchors compared exactly.
- Money: compare in a decimal type. `COMP-3` fields round and truncate differently from floats, so a float port is a defect. Tolerance is zero.
- Order: a KSDS returns records in EBCDIC key order. A port that sorts in ASCII changes the order. The report sorts by card number (`app/jcl/TRANREPT.jcl:37`). Treat order as significant until a downstream consumer is shown not to care.
- Padding and low values in fixed-width records. Decide which matter and write it down.
- `REDEFINES`: test both branches wherever a program reads either layout.

## Cases to add beyond replay

- Month-end, year-end, leap day. Posting expiry is compared as text against the transaction timestamp (`app/cbl/CBTRN02C.cbl:414`), so test dates at the boundary.
- A zero-record daily file, and one at the largest size the old system took.
- Bad data already in the masters. Reject reason 109 never reaches the reject file (`app/cbl/CBTRN02C.cbl:556`). Reproduce that, then decide in the register whether to keep it.
- The report's date window, which the batch job hard-codes (`app/jcl/TRANREPT.jcl:43`) and the online screen overrides (`app/cbl/CORPT00C.cbl:94`).
- Overlap: run the posting wrapper's jobs with no sleep between them, as the script does (`scripts/run_posting.sh:20`), and confirm the result does not depend on timing.
- The interest run, month-end only (`app/scheduler/CardDemo.controlm:69`), which updates account balances and is easy to miss.

## Job order to preserve

The temporal edges are in `02a-edge-tables.md`. The orders the harness must keep: close files, refresh masters, post, define the alternate index, open files (`scripts/run_posting.sh:13`). Control-M and the shell wrappers disagree on the order (`02-coupling.md`), so confirm which is production before encoding one.

## Deviation Register

Nothing differs from legacy without a row here. Pre-seeded with candidates, all unapproved.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| D-1 | Reject reason 109 is set but not written to the reject file | not decided | possible defect | unapproved | Reject-file consumers | `app/cbl/CBTRN02C.cbl:556` |
| D-2 | Expiry compared as a string against the first 10 bytes of the timestamp | not decided | possible defect | unapproved | Which transactions post | `app/cbl/CBTRN02C.cbl:414` |
| D-3 | Last transaction appears to be added twice to report totals at end of file (reviewer's reading, not a run) | not decided | possible defect | unapproved | Report totals | `app/cbl/CBTRN03C.cbl:198` |
| D-4 | `TRANREPT` proc member declares itself `REPROC` and its first step calls `PROC=REPROC` | not decided | possible copy-paste error | unapproved | Online report path | `app/proc/TRANREPT.prc:1` |

## Exit bar per wave

A wave is done when the replay diff is clean modulo the normalization spec and the register, every boundary case passes, the harness is in version control and runs in CI, and someone with authority has signed the register. The harness stays after cutover as the regression suite.
