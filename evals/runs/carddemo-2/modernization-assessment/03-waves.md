# 03 Waves

Target state: **refactor**. The plan is in `waves.json` and the scores behind it are in `risks.json`. Nine waves, cut at the articulation points from `02-coupling.md`. No strongly connected component is split.

## The rule I used, and where I broke it

Earliest waves maximize learning per unit of blast radius, not business value. `migration-risk-assessor` scores each unit on two axes and I ordered by quadrant: low difficulty and low blast first, then high difficulty and low blast, then low difficulty and high blast, and last the high and high units, which are strangled behind a facade and not ported whole.

The order is:

| Waves | Quadrant that dominates | What is in them |
|---|---|---|
| 1 | low-low | Read-only master listings |
| 2 | high-low | Batch programs with packed decimal and REDEFINES that only read |
| 3, 4 | low-high | Master refresh, transaction report |
| 5 | low-high, with high-low screens riding along | Online front door and read-only screens |
| 6, 7, 8, 9 | high-high | Posting, month end, online writers, optional modules |

I broke the rule in three places, and I want them visible.

1. **Wave 5 holds six high-low screens, which the rule would put in wave 2.** They cannot move alone. Every one of them transfers back into the sign-on and menu programs, and those three form one strongly connected component that must move together (`app/cbl/COSGN00C.cbl:231`, `app/cbl/COMEN01C.cbl:201`, `app/cbl/COADM01C.cbl:168`). The menu program reaches them through a computed call (`app/cbl/COMEN01C.cbl:156`). So the screens ride with the front door, and the front door is low-high.
2. **Wave 5 also holds one high-high unit, CSUTLDTC, in the first half of the plan.** It is a 114 line date routine that three programs call and that gets its acceptance rules from the runtime (`app/cbl/CSUTLDTC.cbl:116`). It has to move before CORPT00C and COTRN02C. Its port is small. Its risk is a silent change in which dates are accepted, so it gets the targeted date cases in `06-test-strategy.md` before anything else is built on it.
3. **Wave 6, the posting wave, is a high-high wave placed before the online writers in wave 8.** That follows the quadrant rule between the two. The reason to say it plainly is that the user's first must-not-break item is in the middle of the plan, not at the end. It has to wait for waves 3, 4 and 5, because those give it its data builder, its report oracle and its screen oracle.

## What the waves are

| Wave | Name | Units | Blast | Unblocks | Evidence |
|---|---|---|---|---|---|
| 1 | Read-only master listings | 3 programs, 4 jobs, 1 proc | low | KSDS read layer and zoned decimal codec for CVACT02Y, CVACT03Y, CVCUS01Y | `app/cbl/CBACT02C.cbl:29`, `app/jcl/PRTCATBL.jcl:47` |
| 2 | Packed decimal and REDEFINES patterns | 3 programs, 3 jobs | low | Packed decimal and multi-record codec, export and import round trip | `app/cbl/CBACT01C.cbl:67`, `app/cpy/CVEXPORT.cpy:24` |
| 3 | Master refresh | 12 jobs, 3 GDG setup jobs, 1 wrapper, 4 Control-M jobs | high | Byte exact master builds, fenced CICS close and open | `app/jcl/ACCTFILE.jcl:40`, `scripts/remote_refresh.sh:17` |
| 4 | Transaction report | 1 program, 1 job, 1 proc | high | The report diff oracle, one copy of logic that exists three times | `app/jcl/TRANREPT.jcl:59`, `app/cbl/CBTRN03C.cbl:177` |
| 5 | Online front door and read-only screens | 11 programs | high | Routing facade, screen oracle for wave 6 | `app/cbl/COMEN01C.cbl:156`, `app/cpy/COMEN02Y.cpy:28` |
| 6 | Daily transaction posting | 1 program, 4 jobs, 1 wrapper, 4 Control-M jobs | high | Month end wave, and the online writers | `app/cbl/CBTRN02C.cbl:256`, `app/jcl/TRANBKP.jcl:40` |
| 7 | Month end interest, combine and statements | 3 programs, 4 jobs, 2 wrappers, 5 Control-M jobs | high | Retirement of the shell wrappers | `app/cbl/CBACT04C.cbl:464`, `app/jcl/COMBTRAN.jcl:48` |
| 8 | Online writers | 7 programs | high | Retirement of the shared VSAM masters | `app/cbl/COBIL00C.cbl:212`, `app/cbl/COACTUPC.cbl:858` |
| 9 | Optional authorization, transaction type and MQ modules | 13 programs, 8 jobs, 2 Control-M jobs | high | Removal of IMS, DB2 and MQ | `app/cpy/COMEN02Y.cpy:89`, `app/app-transaction-type-db2/jcl/MNTTRDB2.jcl:30` |

## Each wave against the four tests

A wave is valid only if it can be deployed on its own behind a flag or facade, rolled back on its own, asserted equal at its edge, and named by a business person.

| Wave | Deploy and roll back | Test boundary | Named deliverable | Evidence |
|---|---|---|---|---|
| 1 | Scheduler picks the legacy or new job. Rollback is picking the other one | SYSOUT and report file of each job | Card, xref, customer and category balance listings on the new stack | `app/jcl/READCARD.jcl:1`, `app/jcl/PRTCATBL.jcl:47` |
| 2 | Same. Nothing reads these outputs, so rollback is trivial | The three CBACT01C files and the export file | Account extract and branch export and import on the new stack | `app/jcl/READACCT.jcl:1`, `app/jcl/CBEXPORT.jcl:32` |
| 3 | Legacy IDCAMS jobs stay runnable. Add a pre-refresh unload of each master, because none of the four master jobs takes a backup today (inference) | Every record and every KEYS, RECORDSIZE and AIX definition | Master data refresh on the new platform | `app/jcl/ACCTFILE.jcl:22`, `app/jcl/CARDFILE.jcl:85` |
| 4 | The proc name TRANREPT is the switch. CORPT00C keeps running `EXEC PROC=TRANREPT`, and the proc library order decides which implementation answers | The 133 byte report file | The transaction report, scheduled and from the online menu | `app/cbl/CORPT00C.cbl:94`, `app/jcl/TRANREPT.jcl:23` |
| 5 | The facade routes each menu option to legacy or new. Rollback is routing back | The 3270 datastream per step | Sign-on, menus and inquiry screens on the new stack | `app/cbl/COMEN01C.cbl:156`, `app/cbl/COADM01C.cbl:145` |
| 6 | Parallel run on copies of the masters, then cutover per cycle. Rollback is re-running the legacy job from the previous generation of the transaction backup | Transaction master, account master, category balances, reject file, return code | Daily posting on the new stack | `app/jcl/POSTTRAN.jcl:23`, `app/jcl/TRANBKP.jcl:23` |
| 7 | Same pattern, one cycle per month | New system transactions, account balances, statement file | Month end interest and statements on the new stack | `app/jcl/INTCALC.jcl:22`, `app/jcl/CREASTMT.JCL:79` |
| 8 | The wave 5 facade routes one screen at a time | Master images before and after each session | Account, card, transaction, bill payment and user maintenance on the new stack | `app/cbl/COTRN02C.cbl:444`, `app/cbl/COUSR01C.cbl:175` |
| 9 | inference: one module at a time behind the facade | IMS, DB2 and MQ state | Authorization, transaction type and MQ services | inference |

## The waves in detail

### Wave 1. Read-only master listings (CBACT02C, CBACT03C, CBCUS01C, READCARD, READXREF, READCUST, PRTCATBL, REPROC)

Each program reads one master in key order and prints it. They are about 130 lines and mostly file status handling. They write nothing, and no program consumes what they print. That is why this is the place to prove the build, the KSDS read path and the diff harness. PRTCATBL adds the first SORT with symbol offsets typed in the JCL (`app/jcl/PRTCATBL.jcl:47`), and REPROC is the unload proc that later waves reuse (`app/proc/REPROC.prc:21`).

The wave also gives a cheap readback. After wave 3 refreshes a master, these listings prove it.

CBTRN01C is not in this wave, although it scores low-low. Nothing runs it. If the client confirms it is used, it belongs here.

### Wave 2. Packed decimal and REDEFINES patterns (CBACT01C, CBEXPORT, CBIMPORT, READACCT, CBEXPORT job, CBIMPORT job)

These are the only batch programs with COMP-3, OCCURS and REDEFINES. CBACT01C also calls an assembler date routine (`app/cbl/CBACT01C.cbl:231`), replaces a zero debit with 2525.00 (`app/cbl/CBACT01C.cbl:236`), and fills an array with fixed amounts (`app/cbl/CBACT01C.cbl:256`). None of these change a master. The team can make its mistakes on the decimal and record codec here. The scores for CBEXPORT and CBIMPORT are low confidence, because I scored them from the graph and the copybook and did not read the programs.

### Wave 3. Master refresh (must-not-break item 2)

Twelve refresh and fence jobs, three GDG setup jobs, `remote_refresh.sh` and the weekly Control-M disclosure group folder. There is no COBOL in it. Each job deletes a master, defines it again with a key length and record size typed in the JCL, and reloads it from a flat file (`app/jcl/ACCTFILE.jcl:25`, `app/jcl/ACCTFILE.jcl:36`, `app/jcl/ACCTFILE.jcl:61`). Card, xref and transaction also define an alternate index at a hard-coded offset (`app/jcl/CARDFILE.jcl:85`, `app/jcl/XREFFILE.jcl:74`, `app/jcl/TRANFILE.jcl:84`).

The difficulty is low and the blast radius is high. A refresh from a stale flat file resets the balances that posting updated, and nothing in the account job backs the master up first (inference). CLOSEFIL and OPENFIL travel with the wave because they fence it, and they close only five files (`app/jcl/CLOSEFIL.jcl:26`).

Do not treat this as settled until the client says whether these are production jobs or a test environment reset. The wrappers reach the system through an FTP tunnel (`scripts/remote_refresh.sh:3`), which looks like the second.

The USRSEC reload (DUSRSECJ) is in this wave because the wrapper runs it. It copies user IDs and passwords, so the harness must not copy that dataset to a test system as it is.

### Wave 4. Transaction report (must-not-break item 3)

CBTRN03C, the TRANREPT job and the TRANREPT proc. The report reads the transaction master through a fresh backup, and the xref, transaction type and category files. The new report can run beside the old one and be diffed. It is not read-only, though. Every run writes a new generation of the transaction backup group that TRANBKP writes and COMBTRAN reads as generation 0 (`app/jcl/TRANREPT.jcl:33`, `app/jcl/COMBTRAN.jcl:24`). A new report running beside the legacy one must not write to the legacy group, and the decision on whether the new report writes a backup at all goes in the deviation register (D-009). That side effect, and the fact that the report is on the must-not-break list, is why the blast radius is high.

The logic exists three times: in the job, in the proc, and in JCL text built by CORPT00C (`app/jcl/TRANREPT.jcl:37`, `app/proc/TRANREPT.prc:39`, `app/cbl/CORPT00C.cbl:100`). This wave puts one implementation behind the name TRANREPT. CORPT00C does not change in this wave, because it runs `EXEC PROC=TRANREPT` (`app/cbl/CORPT00C.cbl:94`). It moves in wave 5.

Three decisions come with it, all in `06-test-strategy.md`: the fixed 2022 date window in the SORT symbols (`app/jcl/TRANREPT.jcl:43`), the duplicate step name STEP05R (`app/jcl/TRANREPT.jcl:23`, `app/jcl/TRANREPT.jcl:37`), and two latent defects in the report program that need a yes or no in the deviation register (`app/cbl/CBTRN03C.cbl:177`, `app/cbl/CBTRN03C.cbl:197`).

### Wave 5. Online front door and read-only screens

Sign-on, both menus, the six read-only screens, CORPT00C and CSUTLDTC. The wave builds the routing facade. After it, each later online screen can be strangled on its own by pointing one menu option at the new code. Two cross-wave dependencies:

- The main menu table already lists COPAUS0C from the optional authorization module as option 11 (`app/cpy/COMEN02Y.cpy:89`). The facade has to route that option to legacy code until wave 9.
- Sign-on compares the password as plain text (`app/cbl/COSGN00C.cbl:223`). Do not port that without a decision (D-008 in the register).

Confidence is low. I scored the online programs from the graph and their headers, and I read only the parts cited in `risks.json`.

### Wave 6. Daily transaction posting (must-not-break item 1)

CBTRN02C, the POSTTRAN job, and the jobs that keep the transaction master in a state it can run against: TRANBKP, TRANIDX and the reject GDG definition. It is strangled, not ported. The new posting reads the same daily file, writes to copies of the masters, and the diff is signed off cycle by cycle. Cutover happens when the diff is clean for enough cycles, including a month end. The report from wave 4 and the screens from wave 5 give two independent views of the transaction master to compare.

The reason TRANBKP moves with the program: CBTRN02C opens the transaction master for output (`app/cbl/CBTRN02C.cbl:256`), which only works on a file that TRANBKP just emptied (`app/jcl/TRANBKP.jcl:40`). Porting one without the other breaks the cycle.

There are two more things the plan cannot settle yet: which scheduler is live, and whether an IMS purge job runs ahead of posting (`app/scheduler/CardDemo.ca7:43`). See the open questions in `00-summary.md`.

### Wave 7. Month end interest, combine and statements

CBACT04C rewrites every account balance (`app/cbl/CBACT04C.cbl:352`), writes system transactions that COMBTRAN merges back into the transaction master (`app/jcl/COMBTRAN.jcl:48`), and CBSTM03A prints the statements from the result. The interest is a truncated COMPUTE (`app/cbl/CBACT04C.cbl:464`), and the statement program uses ALTER and reads control blocks (`app/cbl/CBSTM03A.CBL:300`, `app/cbl/CBSTM03A.CBL:266`). Both are hard ports, and the statement program has no equivalent in a modern runtime. The date passed to INTCALC is a fixed PARM (`app/jcl/INTCALC.jcl:22`).

It runs once a month, so each cycle of evidence costs a month. Start collecting the month end captures at the start of wave 3.

`run_full_batch.sh` and `run_interest_calc.sh` end here because they name jobs from waves 3, 6 and 7. They are only valid once all of those have moved.

### Wave 8. Online writers

COACTUPC, COCRDUPC, COTRN02C, COBIL00C and the three user maintenance programs. They write masters while users are on the system, and COBIL00C and COTRN02C choose the next transaction ID as the highest key plus one (`app/cbl/COBIL00C.cbl:212`, `app/cbl/COTRN02C.cbl:444`). COACTUPC is 3368 lines and I did not read it (`app/cbl/COACTUPC.cbl:858`). Treat its score as a placeholder. After this wave no legacy program writes the shared VSAM files.

### Wave 9. Optional authorization, transaction type and MQ modules

A placeholder for three modules on IMS, DB2 and MQ, which this plugin does not analyze. Cut it into three waves once someone has assessed those technologies. The transaction type module goes first because it has the least IMS. COPAUS0C and COPAUS1C are a strongly connected component and move together (`app/app-authorization-ims-db2-mq/cbl/COPAUS0C.cbl:316`, `app/app-authorization-ims-db2-mq/cbl/COPAUS1C.cbl:168`).

## What is not in a wave

| Unit | Why | Evidence |
|---|---|---|
| CBTRN01C | No runner in the tree. A wave 1 candidate if it turns out to be live | `app/cbl/CBTRN01C.cbl:5` |
| COBSWAIT and job WAITSTEP | A fixed 36 second pause. The new scheduler replaces it with a completion dependency | `app/jcl/WAITSTEP.jcl:26` |
| Compile jobs and procs | The new build pipeline replaces them | `samples/jcl/BMSCMP.jcl:1` |
| CBADMCDJ, RACFCMDS | CSD and security definitions. Replaced by routing and access configuration in the target | `app/jcl/CBADMCDJ.jcl:1`, `samples/jcl/RACFCMDS.jcl:1` |
| DEFCUST, ESDSRRDS, FTPJCLS, INTRDRJ1, INTRDRJ2, LISTFILS, REPRTEST, SORTTEST | Demo, test or stale jobs. Confirm with the client and retire | `app/jcl/DEFCUST.jcl:37`, `app/jcl/FTPJCL.JCL:34` |

## If the system were ten times larger

I would cut waves 5 to 8 by application area, and I would not do it by program. Account, card, transaction and user maintenance are already separate groups in the menu tables (`app/cpy/COMEN02Y.cpy:28`, `app/cpy/COADM02Y.cpy:29`). Each would get a read-only wave and a writer wave. The batch side would stay as it is, because its boundaries are the datasets, and a larger system would just have more datasets on the same pattern.
