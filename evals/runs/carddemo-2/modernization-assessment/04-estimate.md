# 04 Estimate

This is a range per wave, in engineer-weeks, with the assumptions that move it most. There is no single number, and no calibration data behind it. It is a judgment from the coupling, the oracle and the code I read, and it should be replaced by measured velocity after wave 1.

## Method

Engineer-weeks for a small team: one engineer who can read COBOL and JCL, one who builds the harness, and Claude Code for mechanical porting. The range includes writing the harness pieces the wave needs and getting the diff clean. It excludes:

- the decision on the target runtime for the CICS transactions and the BMS screens,
- environments and licences,
- waiting on the client for captures, sign-off or answers,
- remediation of the security findings, which are the plain text passwords and the credential in `app/jcl/FTPJCL.JCL:34`.

What moves the estimate, in order of weight: how many coupling edges cross the wave boundary, whether a behavioral oracle exists, god modules inside the wave (none here), how much of the behavior lives in JCL and not in code, and whether anyone on the team reads the source language. Lines of code are a sanity check only.

Crossing edges come from `graph.json`. The contract counts below count both endpoints, and they are understated for the reason given in `02-coupling.md`: the extractor records IDCAMS loads as reads.

## Ranges

| Wave | Range (weeks) | Program lines | Contract edges crossing | Datasets shared with other waves | Oracle today | Evidence |
|---|---|---|---|---|---|---|
| 1 Read-only listings | 2 to 4 | 389 | 2 | 3 | Fixtures only. The harness bring-up dominates | `app/cbl/CBACT02C.cbl:29` |
| 2 Packed decimal and REDEFINES | 3 to 6 | 1091 | 10 | 5 | Fixtures only | `app/cbl/CBACT01C.cbl:67` |
| 3 Master refresh | 3 to 6 | none (15 jobs) | 0 | 10 | Parallel build from the same PS files is possible | `app/jcl/ACCTFILE.jcl:40` |
| 4 Transaction report | 3 to 5 | 545 | 0 | 4 | Archived report generations, if the client has them | `app/cbl/CBTRN03C.cbl:177` |
| 5 Online front door | 10 to 18 | 4915 | 18 | 6 | None in the tree | inference |
| 6 Daily posting | 8 to 16 | 619 | 15 | 4 | Parallel run possible, but needs a real daily file | `app/cbl/CBTRN02C.cbl:256` |
| 7 Month end | 8 to 14 | 1498 | 12 | 6 | Parallel run, one cycle a month | `app/cbl/CBACT04C.cbl:464` |
| 8 Online writers | 14 to 26 | 6348 | 37 | 7 | None in the tree | `app/cbl/COACTUPC.cbl:858` |
| 9 Optional modules | 16 to 40, low confidence | 7071 | 12 | 4 | None. IMS, DB2 and MQ are outside this analysis | inference |

Waves 1 to 8 together come to about 51 to 95 engineer-weeks. With wave 9 as a placeholder, about 67 to 135. The waves are not independent, so do not treat the sum as a schedule. Wave 7 also needs at least three month end cycles of evidence, so it takes at least three calendar months whatever the effort.

Why the numbers land where they do:

- **Waves 1 and 2** are small in lines. Most of the cost is building the codec and the diff tool the other waves reuse, and the low end assumes that tool takes about two weeks.
- **Wave 3** has no COBOL. The cost is the verification: key lengths, record sizes, three alternate index offsets, and the CICS fence (`app/jcl/CARDFILE.jcl:85`, `app/jcl/XREFFILE.jcl:74`, `app/jcl/TRANFILE.jcl:84`).
- **Wave 6** is one 619 line program, and it is more expensive than its size because of what surrounds it. It shares the account and transaction masters with 11 readers each, opens its output file assuming TRANBKP ran, and needs a parallel run environment.
- **Wave 8** is the largest contract count and the largest program in the tree. I did not read COACTUPC, so this is the least certain of the core waves.

## The assumptions the ranges are most sensitive to

1. **The client can supply a real oracle.** This assumes production daily files and before and after images of the masters for at least three posting cycles. If only the 300 fixture transactions are available (`app/data/ASCII/dailytran.txt:1`), waves 4, 6 and 7 roughly double, because every equivalence claim needs hand built cases and month end evidence has to be manufactured.
2. **The refresh jobs are a production process.** This assumes the account and card master refresh is a real job that stays a batch operation. The wrappers reach the mainframe through an FTP tunnel (`scripts/remote_refresh.sh:3`), which looks like a test environment reset. If that is what they are, wave 3 shrinks to about one or two weeks, because the target platform's load tooling replaces the jobs, and what the user means by must-not-break for the second item changes.
3. **New batch code can keep writing the same VSAM files, or synchronized copies of them, while the online programs read them.** If the datastore has to change at wave 6, add a synchronization layer. Waves 6 and 7 grow by about 30 to 50 percent and wave 8 has to move earlier, since the online writers are the other side of that sync (`app/cbl/COBIL00C.cbl:212`, `app/cbl/COTRN02C.cbl:444`).
4. **The IMS purge job is not in the live daily chain.** If the CA-7 listing is the truth and CBPAUP0J runs ahead of POSTTRAN (`app/scheduler/CardDemo.ca7:43`), wave 6 takes on an IMS dependency and grows by three to six weeks.

## Where Claude Code helps and where it does not

Strong, with a working harness: transliteration of plain batch COBOL and JCL into the target. That covers wave 1, the record codec in wave 2, IDCAMS steps into load scripts in wave 3, the report formatting in wave 4 including the edited pictures (`app/cpy/CVTRA07Y.cpy:1`), and CBTRN02C itself, which is a plain paragraph structure of about 600 lines.

Weak or unsafe without a person:

- **Inferring intent.** Which of the legacy behaviors are rules and which are accidents. Examples: a reject reason that is overwritten by a later check (`app/cbl/CBTRN02C.cbl:414`), a literal replacing zero (`app/cbl/CBACT01C.cbl:237`), the loop exit in the report (`app/cbl/CBTRN03C.cbl:177`). Each needs an answer in the deviation register.
- **Job lifecycle design.** Why TRANBKP empties the transaction master and COMBTRAN refills it (`app/jcl/TRANBKP.jcl:40`, `app/jcl/COMBTRAN.jcl:48`) is an operating procedure, and the code does not say why.
- **No modern equivalent.** ALTER and control block reads in the statement program (`app/cbl/CBSTM03A.CBL:266`, `app/cbl/CBSTM03A.CBL:300`). This is redesign, not transliteration.
- **Runtime semantics.** The date rules from the Language Environment service (`app/cbl/CSUTLDTC.cbl:116`), and packed decimal rounding.
- **The undocumented 3368 lines of account validation** in COACTUPC (`app/cbl/COACTUPC.cbl:858`).
- **IMS, DB2 and MQ code.** Outside what this plugin analyzes.

## What the ranges do not include

The scheduler replacement, the target platform choice, the data cutover itself, and the decommissioning of the mainframe. Those are separate work streams that the wave plan depends on.
