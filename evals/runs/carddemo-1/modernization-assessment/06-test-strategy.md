# 06 Test strategy

The legacy system has no tests in the tree. "It passes the tests" is not the bar. The bar for this refactor: for the inputs this system actually sees, the new code produces the same outputs as the old code, and where it does not, someone decided that on purpose and wrote it in the deviation register.

## What the tree gives us as an oracle, and what it does not

The tree holds sample data, not production data. There are 50 accounts and 300 daily transactions in ASCII, and the same files in EBCDIC (`app/data/ASCII/acctdata.txt:1`, `app/data/ASCII/dailytran.txt:1`). There is also a 2022 catalog listing (`app/catlg/LISTCAT.txt:1`). That is enough to start a harness and a characterization test. It is the weakest kind of oracle, so every wave that relies only on it is provisional.

Telemetry is `none`. Nothing in the tree says which jobs ran in the last 12 months. The CA-7 run counts are identical on the jobs I sampled, so I treat them as template values (`app/scheduler/CardDemo.ca7:24`).

Where the real oracle comes from in this shop, in the order I would ask for it:

| Source | What it gives | Where the tree points to it | Evidence |
|---|---|---|---|
| Archived generations | Every generation of the report, reject, backup and system transaction groups is a dated golden master. Each group keeps five (`LIMIT(5)`), so ask for offline copies. | The catalog lists five report generations. | `app/jcl/DEFGDGB.jcl:24`, `app/catlg/LISTCAT.txt:1535` |
| Daily input files | The daily transaction file that POSTTRAN reads. It has a producer outside the tree. | POSTTRAN reads DALYTRAN.PS. | `app/jcl/POSTTRAN.jcl:30` |
| Job logs and SMF records | Which jobs ran, return codes, run times. Also the telemetry for the dead code register. | Not in the tree. | inference |
| Extract files that left the building | The branch export and the FTP file are executable specifications of their formats. | The export and FTP jobs. | `app/jcl/CBEXPORT.jcl:43`, `app/jcl/FTPJCL.JCL:40` |
| CICS journals and recorded sessions | Captured screen inputs for replay. | The main CSD defines 18 transactions. | `app/csd/CARDDEMO.CSD:306` |
| Report and statement archives | Printed transaction reports, statements, PDFs. | Statement and report jobs. | `app/jcl/CREASTMT.JCL:87`, `app/jcl/TXT2PDF1.JCL:39` |

Ask the client to supply, before wave 5 starts: month end and fiscal year end generations of the report, rejects, backup and system transaction groups, a snapshot of the account, category balance and transaction masters before and after one posting run, and the daily input for that run.

## Oracle per wave

| Wave | Oracle | Strength | Boundary the diff runs at | Evidence |
|---|---|---|---|---|
| 1. Environment and utility | None needed. A smoke test that the target pipeline deploys and the scheduler runs a no-op. | n/a | The pipeline | inference |
| 2. Read-only listings and import | Golden master: run the legacy listing job on the EBCDIC sample and on a client snapshot, and compare the three output files and the SYSOUT counts. | 3 with a snapshot, 4 with the sample | The output datasets | `app/jcl/READACCT.jcl:1`, `app/cbl/CBACT01C.cbl:231` |
| 3. Read-only screens and menu spine | Recorded sessions replayed against the same masters. Compare each screen's fields and the COMMAREA passed on. Add the sign on cases. | 2 if journals exist, otherwise 4 | Screen output and COMMAREA | `app/cbl/COSGN00C.cbl:223`, `app/cbl/COMEN01C.cbl:156` |
| 4. Build and generation plumbing | The build is reproducible. A generation group test that the last five versions are kept and read the same way as (0) and (+1). | 4 | The generation semantics | `app/jcl/DEFGDGB.jcl:24` |
| 5. Nightly batch core | Parallel run. The same daily file and the same starting masters go through the legacy and the new cycle. Compare the resulting account, category balance and transaction masters, the reject file, the system transactions and the return codes. For the report, replay the same date range and compare the 133 byte lines. | 1 for posting, 3 for the report if archives exist | The masters, the reject file, and the report file | `app/jcl/POSTTRAN.jcl:23`, `app/jcl/TRANREPT.jcl:66` |
| 6. Online writers | Transaction replay with before and after record images of the account, card, transaction and user files. Shadow the new screens for a period. | 2 | Record images | `app/cbl/COACTUPC.cbl:4100`, `app/cbl/COBIL00C.cbl:212` |
| 7. Subsystems | MQ message replay. An IMS unload and load round trip. A table by table compare of the DB2 reference data. A file compare of the type and category extracts. | 2 or 3 | Messages, unload files, tables | `app/app-transaction-type-db2/jcl/TRANEXTR.jcl:72`, `app/app-authorization-ims-db2-mq/jcl/UNLDPADB.JCL:48` |

The must-not-break anchors each get their own comparison, in wave 5:

| Anchor | What to compare | Evidence |
|---|---|---|
| Daily transaction posting | Account master, category balance master, transaction master, reject file with its 80 byte trailer, and the return code (4 when any transaction is rejected). | `app/cbl/CBTRN02C.cbl:230`, `app/jcl/POSTTRAN.jcl:34` |
| Account and card master refresh | The masters after ACCTFILE and CARDFILE, key by key, plus the card alternate index. | `app/jcl/ACCTFILE.jcl:61`, `app/jcl/CARDFILE.jcl:75`, `app/jcl/CARDFILE.jcl:110` |
| Transaction report | The 133 byte report lines for a fixed date range, first from the batch job and then from the online path. | `app/jcl/TRANREPT.jcl:76`, `app/cbl/CORPT00C.cbl:94` |

## Normalize before you diff

Agree this list, write it down, and have a human sign each line. Each entry says that a difference does not matter, and each is a place a real bug can hide.

| Entry | Why the difference is safe | What it must not hide | Evidence |
|---|---|---|---|
| Processed timestamp on posted transactions | It is the wall clock of the run. | The date part must match, because the report filters on it. | `app/cbl/CBTRN02C.cbl:437` |
| Interest transaction ids | Built from the PARM date and a counter that restarts every run. | Uniqueness in the transaction master, and the order of the counter. | `app/cbl/CBACT04C.cbl:476`, `app/jcl/INTCALC.jcl:22` |
| Job numbers, run dates and SYSOUT banner lines | They vary by run. | The counts the programs display (processed and rejected). | `app/cbl/CBTRN02C.cbl:227` |
| Generation numbers (+1) and (0) | They name a slot, not content. | Which generation each job reads. | `app/jcl/COMBTRAN.jcl:24`, `app/jcl/TRANBKP.jcl:33` |
| DISPLAY output of records | Debug print to SYSOUT. | Nothing on the data path. Compare counts, not lines. | `app/cbl/CBTRN03C.cbl:180` |
| Trailing spaces in fixed length records | Padding. | Low values versus spaces in fields that a later program reads. Decide and write it down. | `app/jcl/POSTTRAN.jcl:36`, `app/jcl/TRANREPT.jcl:78` |
| MQ message ids and expiry | They vary by message. | Correlation ids and reply queue names. | `app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:745` |

Nothing else is normalized. Money fields have zero tolerance. Compare them in a decimal type, never a float.

## Mainframe traps the harness has to handle

| Trap | Where it shows up here | Evidence |
|---|---|---|
| Zoned decimal with an overpunched sign | The sample daily file carries signed amounts as a trailing letter. The record layout is `S9(09)V99` with no separate sign. A port that reads the last byte as a digit is wrong. | `app/data/ASCII/dailytran.txt:1`, `app/cpy/CVTRA06Y.cpy:10` |
| Packed decimal | The report's line counter and page size are COMP-3, and the statement job uses packed tables. | `app/cbl/CBTRN03C.cbl:129`, `app/cbl/CBSTM03A.CBL:64` |
| No ROUNDED | Interest is a divide with no rounding, so the result truncates. A float or a rounding library gives a different cent. | `app/cbl/CBACT04C.cbl:464` |
| Field width | The overlimit test stores its work value in nine integer digits while the account's balances have ten. | `app/cbl/CBTRN02C.cbl:187`, `app/cpy/CVACT01Y.cpy:7` |
| String comparison of dates | Expiry and report ranges compare ISO date text, not date values. | `app/cbl/CBTRN02C.cbl:414`, `app/cbl/CBTRN03C.cbl:173` |
| Collating sequence | The report sorts by card number as zoned decimal on a character field, and the masters return in key order. Sort in EBCDIC order or prove ASCII gives the same rows. | `app/jcl/TRANREPT.jcl:41`, `app/jcl/TRANREPT.jcl:46` |
| REDEFINES | Two layouts over the same bytes: the CORPT00C job text is read as 1,000 lines, and CBACT01C redefines a date. Test every branch that reads either. | `app/cbl/CORPT00C.cbl:126`, `app/cbl/CBACT01C.cbl:137` |
| Record padding and low values | Record lengths 133, 350 and 430 with fixed blocks. | `app/jcl/TRANREPT.jcl:78`, `app/jcl/POSTTRAN.jcl:36` |
| Job order | The order in the temporal edges of `graph.json` is the list the harness must keep. Posting must not run before the backup. | `scripts/run_posting.sh:23`, `scripts/run_posting.sh:26` |
| Files closed for batch | The online files are closed around the cycle and the card and customer files are handled differently. | `app/jcl/CLOSEFIL.jcl:26`, `app/jcl/CARDFILE.jcl:26` |
| RETURN-CODE semantics | Posting ends with 4 when it rejects anything. A scheduler condition may read it. | `app/cbl/CBTRN02C.cbl:229` |

## Cover the input space on purpose

Production replay covers the common path and misses the dangerous ones. Add these cases for wave 5, and the matching ones for the online path in wave 6.

- **Boundary dates.** Month end, quarter end, fiscal year end, leap day, and the December to January rollover in the online report's date math (`app/cbl/CORPT00C.cbl:223`). The monthly interest folder runs at month end (`app/scheduler/CardDemo.controlm:64`).
- **The empty and the enormous.** A zero record daily file. An empty report range. A file at the size the old cluster allowed (`app/jcl/ACCTFILE.jcl:37`).
- **Every reject reason.** Card not in the cross reference (100), account not found (101), over the limit (102), expired card (103) (`app/cbl/CBTRN02C.cbl:385`, `app/cbl/CBTRN02C.cbl:397`, `app/cbl/CBTRN02C.cbl:410`, `app/cbl/CBTRN02C.cbl:417`). Include a transaction exactly at the limit and one on the expiry date.
- **Credits and debits.** The sign decides which cycle counter grows (`app/cbl/CBTRN02C.cbl:548`).
- **A category balance row that does not exist.** Posting creates it (`app/cbl/CBTRN02C.cbl:473`). The default disclosure group fallback in interest (`app/cbl/CBACT04C.cbl:437`) and a zero rate that skips the calculation (`app/cbl/CBACT04C.cbl:214`).
- **The bad data already in there.** Card numbers with letters, which the report sorts as zoned decimal. Accounts with no cross reference row. Reproduce what the legacy code does with them, even when that is neither an error nor a sane result.
- **A report and a backup in the same window.** A report run between a backup and the combine changes which generation the combine reads (`app/jcl/TRANREPT.jcl:33`, `app/jcl/COMBTRAN.jcl:24`).
- **The paths that only run at fiscal close.** The monthly interest cycle, and the combine of the system transactions into the master.

## Deviation register, opened

These are legacy behaviors I found that the client may not want reproduced. None is approved. Each stays a row until a named person signs it. Rows marked inference come from my reading and need an archived output or a run to confirm.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| DR-01 | Sign on upper cases the password and compares clear text to a stored 8 byte password. | Not decided. Options are hashed storage and a case rule. | Clear text credentials in a system of record. | Open | Every user record, the three user maintenance screens, and any partner that reads the file. | `app/cbl/COSGN00C.cbl:132`, `app/cbl/COSGN00C.cbl:223`, `app/cpy/CSUSR01Y.cpy:21` |
| DR-02 | The report loop appears to stop at the first record outside the date range (inference). | Not decided. | The sort already filters by the same dates, so it may never show. If the two ranges differ, the report is silently short. | Open | The transaction report. | `app/cbl/CBTRN03C.cbl:173`, `app/cbl/CBTRN03C.cbl:177` |
| DR-03 | At end of file the report appears to add the last amount to the page and grand totals a second time (inference). | Not decided. | A total may be overstated by one transaction. Check against an archived report. | Open | The transaction report totals. | `app/cbl/CBTRN03C.cbl:198`, `app/cbl/CBTRN03C.cbl:203` |
| DR-04 | If the account rewrite fails after validation, posting still writes the transaction and counts it as posted. | Not decided. | A transaction can post with no balance change and no reject row. | Open | Account balances and the reject file. | `app/cbl/CBTRN02C.cbl:554`, `app/cbl/CBTRN02C.cbl:559` |
| DR-05 | The interest run date and the report date range are typed into JCL. | Parameters. | A stale date silently produces an old range or a repeated id prefix. | Open | Interest transaction ids, the report range. | `app/jcl/INTCALC.jcl:22`, `app/jcl/TRANREPT.jcl:43` |
| DR-06 | Two online programs allocate the next transaction key as the last key plus one. | A key service. | Two users at once can collide, and the batch writers use other schemes. | Open | The transaction master, the alternate index. | `app/cbl/COBIL00C.cbl:212`, `app/cbl/COTRN02C.cbl:444` |
| DR-07 | The report job writes a new backup generation as a side effect, and COMBTRAN reads the newest one. | The ported report does not write the backup. | The side effect changes what the combine reads. | Open | The transaction master after the monthly combine. | `app/jcl/TRANREPT.jcl:33`, `app/jcl/COMBTRAN.jcl:24` |
| DR-08 | The overlimit test uses a nine digit work field against ten digit balances. | Same width as the account fields. | A balance over nine digits would truncate and compare wrong. | Open | The reject decision on very large balances. | `app/cbl/CBTRN02C.cbl:187`, `app/cbl/CBTRN02C.cbl:403` |
| DR-09 | The import job opens a card output file its JCL never defines. | Define it, or drop the card output. | The job as shipped cannot complete. | Open | The branch migration path. | `app/cbl/CBIMPORT.cbl:233`, `app/jcl/CBIMPORT.jcl:33` |

## The exit bar per wave

A wave is done when all four hold:

- The replay diff is clean, apart from the normalization list and the deviation register.
- Every boundary case above that applies to the wave passes.
- The harness is under version control and runs in CI.
- The deviation register is signed by someone with authority to sign it.

Not when the port compiles, and not when it passes tests written alongside the port. Those tests encode the porter's reading, which is the thing under test.

## Keep the harness after cutover

The comparison harness becomes the regression suite for the modernized system. Budget to maintain it. Do not throw it away at cutover. It is the only executable specification this system has ever had.
