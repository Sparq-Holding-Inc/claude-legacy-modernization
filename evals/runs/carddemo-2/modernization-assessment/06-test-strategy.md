# 06 Test strategy

The bar is not that the port compiles or passes tests someone wrote next to it. The bar is that, for the inputs this system really sees, the new implementation produces the same outputs as the old one. Where it does not, someone decided that on purpose and wrote it in the deviation register below.

## What the tree gives us as an oracle, and what it does not

The tree holds input fixtures and no outputs. There are 300 daily transactions and 50 each of accounts, cards, customers and xrefs, in ASCII and in EBCDIC (`app/data/ASCII/dailytran.txt:1`, `app/data/ASCII/acctdata.txt:1`). There is no reject file, no printed report, no statement, no master image taken after a run, no SMF record and no job log. So today the only oracle we can build is **characterization**: run the legacy code on the fixtures and record what it did. That is the weakest kind, because it encodes what the code does on 300 hand-made rows, and the fixtures contain none of the month end or bad data cases below. Every result built on it is provisional until the client supplies production captures.

What to ask the client for is at the end of this file. Ask for it in the first week. Every wave from 3 onward gets cheaper if the answer is yes.

## Oracle per wave

| Wave | Boundary to compare | Oracle, strongest available | Weakness | Evidence |
|---|---|---|---|---|
| 1 Read-only listings | SYSOUT lines from CBACT02C, CBACT03C, CBCUS01C and the PRTCATBL report file | Golden master from archived SYSOUT if the client has it, else characterization on the fixtures | DISPLAY output is diagnostic, so normalize it hard | `app/cbl/CBACT02C.cbl:29`, `app/jcl/PRTCATBL.jcl:47` |
| 2 Packed decimal and REDEFINES | The three CBACT01C output files, and the CBEXPORT file | Characterization, plus the CBEXPORT to CBIMPORT round trip, which must return the source records | CBACT01C replaces a zero debit with a literal, so the output is not a plain copy | `app/cbl/CBACT01C.cbl:236`, `app/cbl/CBEXPORT.cbl:65` |
| 3 Master refresh | Every record and every KEYS, RECORDSIZE and AIX definition of the rebuilt masters | Parallel run: build the same master from the same PS file on both sides and diff record by record and definition by definition | Only proves the build. The refresh path may be a test environment reset, not production | `app/jcl/ACCTFILE.jcl:40`, `app/catlg/LISTCAT.txt:1` |
| 4 Transaction report | The 133 byte report file, and the generations written to the transaction backup group | Golden master from the archived TRANREPT generations, plus a parallel run on a copy of the transaction master so the legacy backup group is not touched | Only 5 generations are kept, and the date window was fixed in the JCL | `app/jcl/DEFGDGB.jcl:37`, `app/jcl/TRANREPT.jcl:43` |
| 5 Online front door and screens | The 3270 datastream per transaction step | Captured CICS terminal sessions replayed against both, or screen scrapes | inference: no session captures exist in the tree | inference |
| 6 Daily posting | The transaction master, account master, category balances, reject file and return code, after each run | Parallel run of the same daily file on copies of the masters | Needs the legacy system to stay up, and a real daily file | `app/cbl/CBTRN02C.cbl:256`, `app/jcl/POSTTRAN.jcl:23` |
| 7 Month end | New system transactions, account balances after interest, and the statement file | Parallel run across a real month end, plus archived statements | Runs once a month, so each cycle of evidence costs a month | `app/jcl/INTCALC.jcl:22`, `app/cbl/CBACT04C.cbl:464` |
| 8 Online writers | Master images before and after each session | Replay of captured sessions, plus a master diff after each | inference: needs journals or captures the tree does not hold | inference |
| 9 Optional modules | IMS, DB2 and MQ state | Needs its own strategy, since this plugin does not analyze those technologies | Unknown | inference |

## Normalization spec

Every line here says that a difference does not matter. Each is a place a bug can hide. Keep the list short and have a person sign it.

| Item | Rule | Evidence |
|---|---|---|
| Processing timestamp on posted transactions | Mask bytes 305 to 330 of a transaction record written by a posting run. It is the run clock. Do not mask it on records carried in from the backup | `app/cbl/CBTRN02C.cbl:437`, `app/cbl/CBTRN02C.cbl:438` |
| Timestamps on interest transactions | Both timestamps are the run clock. The transaction ID is the PARM date plus a counter, so it is deterministic and is compared | `app/cbl/CBACT04C.cbl:476`, `app/cbl/CBACT04C.cbl:496` |
| Job and step names in statements | CBSTM03A reads them from z/OS control blocks. Mask anything derived from them | `app/cbl/CBSTM03A.CBL:266`, `app/cbl/CBSTM03A.CBL:284` |
| SYSOUT DISPLAY lines | CBTRN03C displays every record it reads. Exclude the text from equivalence. Keep the counts and return code | `app/cbl/CBTRN03C.cbl:180`, `app/cbl/CBTRN02C.cbl:227` |
| Generation numbers and dataset names | Compare by position in the generation group, not by name | `app/jcl/POSTTRAN.jcl:38` |
| VSAM physical layout | Do not compare control intervals or free space. Compare key order and record bytes | `app/jcl/ACCTFILE.jcl:40` |
| Money fields | **Never normalize.** They are zoned decimal with an implied decimal point and a trailing sign, compared as decimal with zero tolerance. COMP-3 fields the same | `app/cpy/CVACT01Y.cpy:7`, `app/cbl/CBACT01C.cbl:67` |
| Record padding | Fixed width records pad with spaces. The reject record is 350 bytes of data plus an 80 byte trailer. Compare byte for byte and decide separately what padding may differ | `app/cbl/CBTRN02C.cbl:176`, `app/jcl/POSTTRAN.jcl:34` |
| Record order | The reject file is in input order. The transaction master is in key order under EBCDIC collation. The report is in card number order, and the order of rows inside one card depends on how the SORT breaks ties. Confirm whether anything downstream depends on that | `app/jcl/TRANREPT.jcl:46` |

The EBCDIC trap applies to the master files. A KSDS returns records in EBCDIC key order. Several keys are character fields, for example TRAN-ID PIC X(16) (`app/cpy/CVTRA05Y.cpy:5`). If any of them hold letters, ASCII and EBCDIC give a different order, and a port that sorts in ASCII changes the order silently (inference: the tree does not show what the production keys look like).

## Targeted cases the fixtures do not cover

Production replay covers the common path. These are the dangerous ones. Each maps to a line that shows the rule.

**Posting (CBTRN02C)**
- A card number that is not in the xref, an account that does not exist, an overlimit amount and an expired account each give a different reject code, 100 to 103 (`app/cbl/CBTRN02C.cbl:385`, `app/cbl/CBTRN02C.cbl:397`, `app/cbl/CBTRN02C.cbl:410`, `app/cbl/CBTRN02C.cbl:417`).
- A transaction that is both overlimit and after expiry. The second check overwrites the first, so the reject reason is 103 (`app/cbl/CBTRN02C.cbl:407`, `app/cbl/CBTRN02C.cbl:414`). A port that reports the first failure is wrong.
- A balance exactly at the credit limit. The test is greater than or equal (`app/cbl/CBTRN02C.cbl:407`).
- A positive amount and a negative amount, which go to different cycle totals (`app/cbl/CBTRN02C.cbl:548`).
- A category balance record that exists and one that does not (`app/cbl/CBTRN02C.cbl:495`).
- A transaction ID already in the master. The write fails and the program abends (`app/cbl/CBTRN02C.cbl:564`, `app/cbl/CBTRN02C.cbl:577`).
- An empty daily file. The transaction master must still come out empty and the return code must be 0. Any reject makes it 4 (`app/cbl/CBTRN02C.cbl:229`).
- A run against a transaction master that is not empty. Opening for output is what the program does, so record what the legacy runtime does (`app/cbl/CBTRN02C.cbl:256`).

**Report (CBTRN03C)**
- A record exactly on the start date and one on the end date. Both are inclusive (`app/cbl/CBTRN03C.cbl:173`).
- A record outside the date window in the middle of the file. NEXT SENTENCE leaves the loop (inference, from the COBOL rule that it continues after the next period) (`app/cbl/CBTRN03C.cbl:177`, `app/cbl/CBTRN03C.cbl:206`).
- The last record of the file. The end of file branch adds the last amount a second time before writing page and grand totals, and never writes the last card's account total (inference) (`app/cbl/CBTRN03C.cbl:197`, `app/cbl/CBTRN03C.cbl:200`).
- Exactly 20 lines to a page, with a card change on the page boundary (`app/cbl/CBTRN03C.cbl:131`, `app/cbl/CBTRN03C.cbl:282`).
- A file with no records in the window at all.

**Interest and statements**
- A rate of zero skips the calculation (`app/cbl/CBACT04C.cbl:214`).
- A missing disclosure group falls back to DEFAULT (`app/cbl/CBACT04C.cbl:436`).
- A balance whose monthly interest has a third decimal of 5 or more. The COMPUTE truncates, and an IEEE float port would round (`app/cbl/CBACT04C.cbl:464`).
- A statement run at a month boundary and at year end (`app/jcl/CREASTMT.JCL:79`).

**Refresh**
- An empty source file, a source file with a duplicate key, and a record shorter than RECORDSIZE (`app/jcl/ACCTFILE.jcl:40`, `app/jcl/ACCTFILE.jcl:61`).

**Bad data already in the files**
- An account with a zero cycle debit. CBACT01C writes 2525.00 in its place (`app/cbl/CBACT01C.cbl:236`).
- An account whose expiry date is before the transaction origin date (`app/cbl/CBTRN02C.cbl:414`).

**Dates.** Month end, quarter end, fiscal year end and leap day 2024-02-29 for the expiry and processing date compares. There is no time zone in the timestamps, so daylight saving is not a case here.

## Order the harness must keep

The temporal edges in `graph.json` are the orders the harness must reproduce. These are the ones that change results:

- Close the CICS files, then refresh, then open them (`scripts/remote_refresh.sh:13`, `scripts/remote_refresh.sh:50`).
- Back up and empty the transaction master, then post, then rebuild the alternate index (`scripts/run_posting.sh:23`, `scripts/run_posting.sh:26`, `scripts/run_posting.sh:30`).
- The report writes a backup generation, so it must not run between the transaction backup and the combine (`app/jcl/TRANREPT.jcl:33`, `app/jcl/COMBTRAN.jcl:24`). Test that case with the legacy jobs to see what happens.
- Interest, then backup, then combine, then rebuild the alternate index (`scripts/run_interest_calc.sh:19`, `scripts/run_interest_calc.sh:23`, `scripts/run_interest_calc.sh:26`, `scripts/run_interest_calc.sh:30`).

Until the client says which scheduler is live, run the harness under the shell order and record the other two as open (see `02-coupling.md`).

## Deviation register

Nothing gets to differ without a row here. The rows below are behaviors I found in the legacy code that look wrong. None is approved. The default for each is to reproduce the legacy behavior until someone with authority signs a change.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact |
|---|---|---|---|---|---|
| D-001 | Report grand total counts the last transaction amount twice (`app/cbl/CBTRN03C.cbl:200`). Inference | Reproduce | Not changed | Unassigned | Printed report totals |
| D-002 | Report leaves its loop at the first record outside the date window, with no totals (`app/cbl/CBTRN03C.cbl:177`). Inference | Reproduce | Not changed | Unassigned | Report is short and silent when the window is narrower than the SORT window |
| D-003 | Two failed checks give the last reason, not the first (`app/cbl/CBTRN02C.cbl:414`) | Reproduce | Not changed | Unassigned | Reject file reason codes |
| D-004 | Reject reason 109 is set after posting and never written (`app/cbl/CBTRN02C.cbl:556`) | Reproduce | Not changed | Unassigned | None seen |
| D-005 | Zero cycle debit becomes 2525.00 in the account extract (`app/cbl/CBACT01C.cbl:237`) | Reproduce | Not changed | Unassigned | Extract file consumers, if any |
| D-006 | Interest truncates and does not round (`app/cbl/CBACT04C.cbl:464`) | Reproduce, with a decimal type | Not changed | Unassigned | Every account balance |
| D-007 | The transaction backup deletes the master even if the backup step failed (`app/jcl/TRANBKP.jcl:37`). Inference | Do not reproduce. Make the delete depend on a good backup | Data loss path | Unassigned | Nothing should depend on it |
| D-008 | Passwords are stored and compared as plain text (`app/cbl/COSGN00C.cbl:223`) | Decision needed | Security | Unassigned | Sign-on and the user file |
| D-009 | Each report run writes a generation of the transaction backup group that COMBTRAN reads as generation 0 (`app/jcl/TRANREPT.jcl:33`, `app/jcl/COMBTRAN.jcl:24`). Inference on the effect | Decision needed. Reproducing it keeps the hazard, and dropping it changes what the group holds | Silent change to what COMBTRAN combines | Unassigned | Transaction master rebuild |

## Exit bar for each wave

A wave is done when all four are true:

- The replay or parallel run diff is clean, apart from the normalization spec and the register.
- Every targeted case above that applies to the wave passes.
- The harness is under version control and runs in CI.
- A person with the authority to sign has signed the register.

## Keep the harness after cutover

The comparison harness becomes the regression suite for the new system. Budget to maintain it. It is the only executable specification this system has ever had.

## What to ask the client to supply

1. At least 12 months of daily transaction files (DALYTRAN), with the matching reject files, return codes and job logs. Include one fiscal year end.
2. Images of the account, category balance and transaction masters before and after at least three posting cycles, including a month end.
3. The archived report generations (TRANREPT), the statement files, and the printed or PDF statements. Tell us the real generation limits, because the tree defines the report group twice with limits of 5 and 10 (`app/jcl/DEFGDGB.jcl:38`, `app/jcl/REPTFILE.jcl:27`).
4. SMF type 30 records, or the scheduler run history, so we know which jobs run and in what order.
5. CICS journals or terminal session captures for the online programs.
6. Which scheduler is live: Control-M, CA-7, the shell wrappers, or something else.
7. Whether the refresh jobs are a production process or a test environment reset. This changes what must-not-break means for the second item.
8. The code page used for the EBCDIC files, and whether sign overpunch is in use, since the fixtures come in both forms (`app/data/ASCII/acctdata.txt:1`).
