# 06 Test strategy

The bar for every wave is the one in the `behavioral-equivalence` skill: for the inputs this system
really sees, the new code produces the same outputs as the old, and every difference was decided on
purpose and written down. This file picks the oracle per wave, lists what must be normalized before
a diff, lists the cases that replay will not cover, and starts the Deviation Register.

## What the tree gives us as an oracle

The tree holds datasets, so the oracle does not have to start from job logs alone. What it holds:

| Asset | What it is | Evidence |
|---|---|---|
| Seed masters | 50 rows each of accounts, cards, xref and customers, in ASCII, with EBCDIC copies in `app/data/EBCDIC` | `app/data/ASCII/acctdata.txt:1`, `app/data/ASCII/carddata.txt:1` |
| Daily input | 300 daily transactions, 350 bytes each | `app/data/ASCII/dailytran.txt:300` |
| Catalog listing | `LISTCAT` output from 2022-09-01 with cluster attributes and GDG generation names | `app/catlg/LISTCAT.txt:1` |
| GDG generations | Only names, not contents. The transaction backup base shows five generations kept, the reject base five | `app/catlg/LISTCAT.txt:1639`, `app/catlg/LISTCAT.txt:692` |
| Export file | An EBCDIC export file of 250,000 bytes that the import job reads | `app/jcl/CBIMPORT.jcl:28` |

These are seed data, not production. They can start a harness. They cannot stand in for a business
cycle. The GDG limits also mean that the archive of reports and posting output is only as long as the
limit, unless the client copies it elsewhere. I ask for that below.

## Oracle per wave

| Wave | Oracle, strongest first | What I would ask the client for | Evidence |
|---|---|---|---|
| 1 | Cluster attributes from the catalog listing; no behavioral oracle needed | The current `LISTCAT` of production and the RACF profile listing | `app/catlg/LISTCAT.txt:1` |
| 2 | Parallel run. The programs are read-only, so run legacy and new nightly against one copy of the masters and diff the outputs | Nothing beyond a copy of the masters | `app/jcl/READACCT.jcl:35` |
| 3 | Captured CICS traffic, replayed: COMMAREA, screen fields and the file state afterward. Fall back to characterization tests, which are provisional | CICS journals or transaction logs for one business cycle including month end | inference |
| 4 | None. Delete and replace with the build pipeline | Nothing | inference |
| 5 | Parallel run on the same daily input from the same starting masters. Diff the resulting `TRANSACT`, `ACCTDATA`, `TCATBALF`, reject file, interest file and report | 12 months of daily input files and generations of the transaction backup, the reject file and the report, and one fiscal year end | `app/jcl/POSTTRAN.jcl:28` |
| 6 | Captured online traffic replayed against a copy of the masters, diffing each master record after each transaction | Journals covering account updates, card updates, bill payments and user changes | `app/cbl/COBIL00C.cbl:233` |
| 7 | Shadow traffic for the authorization program: copy the MQ requests to the new code, compare the decision, write nothing | A day of authorization requests and replies, plus the IMS unload | `app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:62` |

For wave 5, say early to the client that a parallel run is possible and worth its cost. The nightly
cycle has one input and a small set of outputs, which is the good case for it.

## Normalize before you diff

Every line here is an assertion that a difference does not matter. Each one needs a person's
signature before the harness may use it.

| Item | Rule | Why | Evidence |
|---|---|---|---|
| Processing timestamps | Mask `TRAN-PROC-TS` on rows the batch stamps. Keep `TRAN-ORIG-TS` from the input | Posting and interest stamp the wall clock | `app/cbl/CBTRN02C.cbl:437`, `app/cbl/CBACT04C.cbl:496` |
| Interest transaction ids | Compare after fixing the PARM date | The id is the PARM date plus a counter | `app/cbl/CBACT04C.cbl:476` |
| GDG generation names | Compare by relative position, not by the G number | `(0)` and `(+1)` resolve at run time | `app/jcl/COMBTRAN.jcl:24` |
| SYSOUT | Exclude it, but keep the return code. Posting ends with 4 when any record was rejected | The programs DISPLAY full records and counters | `app/cbl/CBTRN02C.cbl:229`, `app/cbl/CBTRN03C.cbl:180` |
| Money | Compare as decimals, zero tolerance, after decoding sign overpunch. Never as floats | The masters are signed zoned decimal. In the ASCII files `{` is a positive zero and `G` a positive seven | `app/data/ASCII/dailytran.txt:1`, `app/cpy/CVACT01Y.cpy:7` |
| Padding | Decide space or low-values for the FILLER areas and record it | The account record ends with 178 bytes of FILLER | `app/cpy/CVACT01Y.cpy:17` |
| Order of report lines within a card | Do not normalize until the client confirms nobody depends on it | The SORT has no EQUALS request, so I cannot tell from the source whether input order is kept within a card (inference) | `app/jcl/TRANREPT.jcl:46` |
| Order of browse results | Keep the legacy key order, and test with keys that mix letters and digits | A KSDS returns key order, and EBCDIC and ASCII sort them differently | `app/jcl/DUSRSECJ.jcl:35` |

## Cover the input space deliberately

Replay covers the common night. These cases need targeted inputs. Each names the source line that
makes it a case.

| Area | Case | Evidence |
|---|---|---|
| Posting | Unknown card (reason 100), unknown account (101), over limit (102), expired account (103), and a zero record input | `app/cbl/CBTRN02C.cbl:385`, `app/cbl/CBTRN02C.cbl:410`, `app/cbl/CBTRN02C.cbl:417` |
| Posting | A category balance row that does not exist yet, so the create path runs | `app/cbl/CBTRN02C.cbl:503` |
| Posting | An amount that pushes a ten digit account field past a nine digit work field | `app/cbl/CBTRN02C.cbl:403` |
| Posting | The account rewrite that fails after the transaction is already written | `app/cbl/CBTRN02C.cbl:556` |
| Interest | A rate of zero, a missing disclosure group that falls to DEFAULT, and a balance whose interest has a fraction under one hundredth (there is no rounding) | `app/cbl/CBACT04C.cbl:436`, `app/cbl/CBACT04C.cbl:464` |
| Interest | The monthly run at month end and at fiscal year end, and a second run with the same PARM | `app/scheduler/CardDemo.controlm:64`, `app/jcl/INTCALC.jcl:22` |
| Report | A date range narrower than the SORT range, a range of one day, a leap day, and a card with more than 20 lines so the page break runs | `app/cbl/CBTRN03C.cbl:173`, `app/cbl/CBTRN03C.cbl:282` |
| Report | The monthly report in December and the yearly report | `app/cbl/CORPT00C.cbl:223`, `app/cbl/CORPT00C.cbl:250` |
| Refresh | ACCTFILE and CARDFILE rerun after a failure between the delete and the define, and the non-unique alternate index on the card file | `app/jcl/CARDFILE.jcl:83` |
| Cycle | A failed backup step followed by the delete | `app/jcl/TRANBKP.jcl:40`, `app/jcl/TRANBKP.jcl:51` |
| Cycle | The report or a sample job run between posting and the merge | `app/jcl/TRANREPT.jcl:33`, `samples/jcl/REPRTEST.jcl:33` |
| Bad data | Every generation of the reject file the client can supply, since it holds the data that already broke the rules | `app/jcl/POSTTRAN.jcl:34` |
| Fiscal close | Interest and merge at the close, the one path that runs monthly | `app/scheduler/CardDemo.controlm:64` |

## Mainframe traps for the spec

| Trap | Where it bites here | Evidence |
|---|---|---|
| Packed and zoned decimal | The masters are zoned. The export layout is packed. The statement total is packed | `app/cpy/CVEXPORT.cpy:50`, `app/cbl/CBSTM03A.CBL:64` |
| Silent truncation | A ten digit balance is moved into a nine digit amount with no size error phrase | `app/cbl/COBIL00C.cbl:224` |
| Collating sequence | User ids such as ADMIN001 and USER0001 mix letters and digits | `app/jcl/DUSRSECJ.jcl:35` |
| REDEFINES | 43 in the account update program, 7 in the export layout. Test every branch | `app/cbl/COACTUPC.cbl:119`, `app/cpy/CVEXPORT.cpy:1` |
| Record padding | FILLER in every master record | `app/cpy/CVTRA05Y.cpy:18` |
| Job order | The 133 temporal edges are the orders the harness must keep. 25 are `medium` | `analysis` (field `edge_counts`) |
| Table slots | The menu table has room for 12 entries and holds 11. The count guards the last slot | `app/cpy/COMEN02Y.cpy:94`, `app/cbl/COMEN01C.cbl:128` |
| Steps that may not run | `COND=` and `IF MAXCC` change which steps run and are not in the graph | `app/jcl/TRANBKP.jcl:51` |

## Deviation Register, first entries

None of these is approved. Every row says pending, because I cannot approve a change to behavior on
the client's behalf. The legacy behavior column is what the source says, and where I inferred the run
time effect from the source I say so.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| D-01 | The report read loop ends at the first record outside the date range, so totals may not print (inference: NEXT SENTENCE ends the loop) | Skip the record and go on | The loop exit looks unintended | pending | Report totals when DATEPARM is narrower than the SORT range | `app/cbl/CBTRN03C.cbl:177` |
| D-02 | The last transaction is added a second time to the page and grand totals, and the last account's total is never printed (inference) | Count once and print the last total | Looks like a defect | pending | Every archived report differs from a corrected one | `app/cbl/CBTRN03C.cbl:200` |
| D-03 | Reject reason 109 is set after the balance and the transaction were written, and nothing acts on it (inference) | Treat it as a reject and roll back | The record is neither rejected nor counted | pending | The reject file and the return code | `app/cbl/CBTRN02C.cbl:556` |
| D-04 | Amounts wider than nine digits are cut with no error | Wider decimal type and an explicit size error | Silent loss of money | pending | Bill payment and posting on large balances | `app/cbl/COBIL00C.cbl:224` |
| D-05 | The report job writes a new generation of the transaction backup | The report reads a snapshot and writes no backup | The side effect changes what the merge reads | pending | The backup generation count | `app/jcl/TRANREPT.jcl:33` |
| D-06 | The backup step's failure does not stop the delete, and the define is skipped (inference) | Define first or swap atomically | A failed night can leave no master | pending | Recovery procedure | `app/jcl/TRANBKP.jcl:40` |
| D-07 | User passwords are stored and compared in clear text | Hashed, with a migration | Credential exposure | pending | Every user, and the security team | `app/cbl/COSGN00C.cbl:223` |
| D-08 | Full transaction records, with card numbers, are written to the job log | Masked or removed | Card number exposure in logs | pending | Anyone who reads SYSOUT for support | `app/cbl/CBTRN03C.cbl:180` |
| D-09 | The interest run date is a constant in the job | Derived from the business date | A stale PARM repeats transaction ids | pending | Interest ids and the merge | `app/jcl/INTCALC.jcl:22` |
| D-10 | The batch report range is a constant in the SORT card | Passed as a parameter | The range is fixed at 2022 | pending | Whoever runs the batch report | `app/jcl/TRANREPT.jcl:43` |

## Exit bar per wave

A wave is done when the replay or parallel diff is clean apart from the normalization spec and the
register, every case in the table above passes, the harness is in version control and runs in CI,
and the register is signed by someone with the authority to sign it. Not when the port compiles.

## Keep the harness after cutover

The harness becomes the regression suite. Budget for it in wave 7's end, not in wave 1's start.
