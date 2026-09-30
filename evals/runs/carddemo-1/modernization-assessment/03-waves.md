# 03 Waves

Target state: refactor. Seven waves. The plan is in `waves.json` and the scores behind it are in `risks.json`. Every unit in the plan is a node in `graph.json`. Every unit is assigned to a wave or listed as unassigned with a reason.

## How I cut it

Two rules from the assessment skill drove the cut, and one fact from the graph made it easy.

1. Order by learning per unit of blast radius. Low port difficulty and low blast radius first, then high difficulty with low blast radius, then low difficulty with high blast radius once the equivalence harness is proven, then everything that is high on both, last.
2. Never split a strongly connected component. The three are COSGN00C with COMEN01C and COADM01C, COTRN00C with COTRN01C, and COPAUS0C with COPAUS1C. Each sits inside one wave.
3. The fact: every write to a shared master comes from wave 6. Waves 1, 2, 4, 5 and 7 only read the masters, and wave 3 owns stores no other wave touches (the user file and the Db2 table). So waves can coexist with the legacy system without dual writes until wave 6. I checked this by placing each unit and listing the datasets that more than one wave touches. Only six datasets showed up (the account, card, cross reference, customer and transaction masters and the cross reference index path), and only wave 6 writes any of them. Evidence: `app/cbl/CBTRN02C.cbl:554`, `app/cbl/COACTUPC.cbl:4064`, `app/cbl/COBIL00C.cbl:379`, `app/cbl/CBACT04C.cbl:356`.

The waves are not the same size. Waves 1 and 2 are small on purpose. They exist to learn something cheaply, and each delivers something a business owner can name.

## Summary

| Wave | Name | Units | Quadrants inside it | Blast radius | Confidence | Evidence |
|---|---|---|---|---|---|---|
| 1 | Read-only master readers | 6 | low-low | low | medium | `app/cbl/CBACT02C.cbl:29`, `app/jcl/READCARD.jcl:22` |
| 2 | Hard-pattern batch utilities | 6 | high-low, low-low | low | medium | `app/cbl/CBACT01C.cbl:231`, `app/cbl/CBEXPORT.cbl:65` |
| 3 | Administration front door | 18 | low-high, high-low, low-low, one high-high | medium | medium | `app/cbl/COSGN00C.cbl:223`, `app/app-transaction-type-db2/jcl/TRANEXTR.jcl:76` |
| 4 | Read-only inquiry and the transaction report | 11 | high-high, high-low, low-low | medium | medium | `app/cbl/CBTRN03C.cbl:173`, `app/cbl/CORPT00C.cbl:94` |
| 5 | Account statements | 3 | high-high | medium | low | `app/cbl/CBSTM03A.CBL:300`, `app/jcl/CREASTMT.JCL:79` |
| 6 | Money core | 42 | high-high, low-high, low-low | high | medium | `app/jcl/POSTTRAN.jcl:23`, `app/jcl/TRANBKP.jcl:37` |
| 7 | IMS and MQ authorization and MQ services | 15 | high-high, high-low | high | low | `app/app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl:25`, `app/app-vsam-mq/cbl/COACCT01.cbl:115` |

Twenty-three units are not ported at all. They are listed at the end.

## Where the plan puts a high-high unit early, said plainly

- Wave 3 holds one high-high unit: `job:TRANEXTR` (difficulty 3, blast radius 3). It unloads the Db2 type table into the file the transaction report reads. It stays in wave 3 because a datastore moves with its writers, and moving the Db2 module without its unloader would leave the unloader reading a table it does not own. Its own comment says it runs daily, and Control-M says weekly (`app/app-transaction-type-db2/jcl/TRANEXTR.jcl:19`, `app/scheduler/CardDemo.controlm:57`).
- Wave 4 holds three: CBTRN03C, CORPT00C and `job:TRANREPT`, all 3 and 3. It is the halfway point of a seven wave plan. It is the weakest placement in the plan. The argument for it is that the report is read-only, is rerunnable from the transaction backup, and can run in parallel with the legacy job on a copy of the same inputs. The argument against it is that the client named the report and the numbers it prints can be wrong without any job failing (`app/cbl/CBTRN03C.cbl:198`). If the harness from waves 1 to 3 is not proven by then, hold this wave.
- Wave 5 holds three (CBSTM03A, CBSTM03B, `job:CREASTMT`). The largest, CBSTM03A, scores 5 for port difficulty and is rewritten from what it does, not ported (`app/cbl/CBSTM03A.CBL:300`).

## The waves

### Wave 1. Read-only master readers

Units: CBACT02C, CBACT03C, CBCUS01C, job:READCARD, job:READXREF, job:READCUST.

- Deployable alone: the new programs run under the same job names against the same masters, read-only.
- Rollback: point the job step back at the legacy program. There is no state to undo.
- Testable boundary: the read-back listing and the SYSOUT text. This is where the harness is built.
- A business owner can name it: verification that the masters are right after the refresh.
- Unblocks: the fixed-width record codec, the EBCDIC to Unicode handling and the harness itself. The records are 150, 50 and 500 bytes (`app/cpy/CVACT02Y.cpy:4`, `app/cpy/CVACT03Y.cpy:4`, `app/cpy/CVCUS01Y.cpy:4`).

### Wave 2. Hard-pattern batch utilities

Units: CBACT01C, CBEXPORT, CBIMPORT, job:READACCT, job:CBEXPORT, job:CBIMPORT.

- Deployable alone: read-only against the masters, and the output datasets are scratch or export files.
- Rollback: rerun the legacy job. The outputs are regenerated, not updated.
- Testable boundary: byte comparison of the three CBACT01C outputs, of EXPORT.DATA, and a CBEXPORT to CBIMPORT round trip (`app/cbl/CBEXPORT.cbl:65`, `app/cbl/CBIMPORT.cbl:37`).
- Business name: the branch migration extract (`app/cbl/CBEXPORT.cbl:8`). The consumers outside the tree are unknown.
- Unblocks: signed decimal money, packed decimal, OCCURS DEPENDING ON, REDEFINES and the assembler date routine. The transaction report and the statement program reuse them (`app/cbl/CBACT01C.cbl:231`, `app/cbl/CBTRN03C.cbl:129`).

### Wave 3. Administration front door

Units: COSGN00C, COMEN01C, COADM01C, COUSR00C, COUSR01C, COUSR02C, COUSR03C, COTRTLIC, COTRTUPC, COBTUPDT, CSUTLDTC, job:DUSRSECJ, job:CREADB2, job:MNTTRDB2, job:TRANEXTR, job:TRANTYPE, job:TRANCATG, job:DEFGDGD.

- Deployable alone behind program-name routing: the menus route through two tables of program names, so each option is re-pointed on its own (`app/cpy/COMEN02Y.cpy:28`, `app/cpy/COADM02Y.cpy:29`). The user file and the Db2 table have writers only in this wave.
- Rollback: revert the table entry or the program definition. Revert the reference files from the TRANTYPE and TRANCATG backup generations.
- Testable boundary: screen and COMMAREA transcripts per option, the user file records, the Db2 rows and the TRANTYPE.PS bytes from TRANEXTR.
- Business name: who can sign in, and administration of users and transaction types.
- Unblocks: waves 4 and 6 can flip an option at a time. CSUTLDTC is available to CORPT00C, COTRN02C and COACTUPC (`app/cbl/CORPT00C.cbl:392`, `app/cbl/COTRN02C.cbl:393`, `app/cbl/COACTUPC.cbl:4232`).
- Watch: sign-on compares a clear text password in eight bytes (`app/cbl/COSGN00C.cbl:223`, `app/cpy/CSUSR01Y.cpy:21`). Refactoring it as it stands carries the weakness over. That is a decision, not a default.

### Wave 4. Read-only inquiry and the transaction report

Units: COTRN00C, COTRN01C, COACTVWC, COCRDSLC, COCRDLIC, CORPT00C, CBTRN03C, job:TRANREPT, proc:TRANREPT, proc:REPROC, job:PRTCATBL.

- Deployable alone: the report job is switched job by job with a parallel run. The online programs are re-pointed in the menu table from wave 3.
- Rollback: switch the job or the table entry back.
- Testable boundary: the TRANREPT dataset text, compared line by line after the normalization spec; the JCL text that CORPT00C writes to the queue; screen transcripts for the inquiry programs.
- Business name: transaction reporting and account, card and transaction inquiry. This is the wave where business value shows.
- Unblocks: legacy read access to the masters ends here, so wave 6 has only writers left to move. The internal reader queue is retired (`app/cbl/CORPT00C.cbl:517`).
- Watch: the batch job hard-codes a 2022 date range in two places (`app/jcl/TRANREPT.jcl:43`, `app/jcl/TRANREPT.jcl:44`) and the online path computes its own (`app/cbl/CORPT00C.cbl:220`, `app/cbl/CORPT00C.cbl:247`, `app/cbl/CORPT00C.cbl:429`). Two paths produce the report and they do not read the same parameters.

### Wave 5. Account statements

Units: CBSTM03A, CBSTM03B, job:CREASTMT.

- Deployable alone: the statement job reads the cross reference, account and customer masters and a re-sorted copy of the transaction master (TRXFL), and writes text and HTML files (`app/jcl/CREASTMT.JCL:45`, `app/jcl/CREASTMT.JCL:83`).
- Rollback: rerun the legacy job.
- Testable boundary: the statement text and HTML files. The 51 by 10 in-storage table caps the input, so the boundary cases include a card with more than 10 transactions and a run with more than 51 cards (`app/cbl/CBSTM03A.CBL:226`).
- Business name: customer statements. The client did not name them, so this wave's scores are provisional.
- Unblocks: retires the code that walks the TCB and TIOT control blocks (`app/cbl/CBSTM03A.CBL:266`), and the TXT2PDF converter, which is not ported (`app/jcl/TXT2PDF1.JCL:24`).

### Wave 6. Money core

Programs: CBTRN02C, CBACT04C, COBIL00C, COTRN02C, COACTUPC, COCRDUPC. Jobs: job:POSTTRAN, job:INTCALC, job:COMBTRAN, job:TRANBKP, job:TRANIDX, job:TCATBALF, job:DISCGRP, job:ACCTFILE, job:CARDFILE, job:XREFFILE, job:CUSTFILE, job:TRANFILE, job:DEFGDGB, job:DALYREJS, job:REPTFILE, job:CLOSEFIL, job:OPENFIL. Scheduler entries: 19 (every `sch:` node).

- Deployable alone: the six writers sit behind one account and transaction access facade. The facade is the deployable unit and the switch. The scheduler entries move last, because they hold the order the harness must keep.
- Rollback: every step before the store cutover is reversible by pointing the facade back at VSAM. The store cutover is a one-way door and gets its own go or no-go.
- Testable boundary: the masters after each posting run, the rejects file, the interest transactions and the transaction master after COMBTRAN. The full list is in `06-test-strategy.md`.
- Business name: posting, interest, balances, and refreshing the account and card masters. Two of the three things the client named.
- Order inside the wave: (1) the facade, with the legacy programs going through it; (2) the online writers one at a time behind the menu, COTRN02C, COBIL00C, COCRDUPC, then COACTUPC; (3) daily posting in shadow on a copy of the masters, then cutover; (4) interest and COMBTRAN in shadow through at least three month ends; (5) the refresh, backup and index jobs replaced by loaders; (6) CLOSEFIL, OPENFIL and WAITSTEP retired, and one scheduler kept.
- Watch: COACTUPC is 15 percent of the COBOL and writes the account through a private layout (`app/cbl/COACTUPC.cbl:418`). TRANBKP deletes the transaction master even when its backup step fails (`app/jcl/TRANBKP.jcl:37`). The delete-and-reload jobs replace masters from flat files no job in the tree creates (`app/jcl/ACCTFILE.jcl:61`).

### Wave 7. IMS and MQ authorization and MQ services

Units: COPAUA0C, COPAUS0C, COPAUS1C, COPAUS2C, CBPAUP0C, PAUDBLOD, PAUDBUNL, DBUNLDGS, COACCT01, CODATE01, job:CBPAUP0J, job:DBPAUTP0, job:LOADPADB, job:UNLDPADB, job:UNLDGSAM.

- This wave is a scope decision. The extractor does not read IMS or MQ. The programs and their JCL are here so the plan is complete, and every score in this wave is low confidence except where noted.
- Deployable alone: it has its own CICS resource definitions (`app/app-authorization-ims-db2-mq/csd/CRDDEMO2.csd`, `app/app-vsam-mq/csd/CRDDEMOM.csd`) and its own IMS database.
- Rollback: re-enable the legacy definitions.
- Testable boundary: MQ message pairs for COACCT01, CODATE01 and COPAUA0C; DL/I call traces for the IMS programs.
- Business name: card authorization decisions and the authorization inquiry screens.
- COPAUA0C (difficulty 5, blast radius 4) is the highest scored unit outside the money core and decides authorizations in real time (`app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:5`). CBPAUP0C deletes IMS segments and CA-7 runs it before POSTTRAN (`app/scheduler/CardDemo.ca7:43`, `app/scheduler/CardDemo.ca7:70`).

## Boundaries between waves

| Boundary | Crossing edges | What crosses | Evidence |
|---|---|---|---|
| 1 and 6 | 2 contract | Card and customer masters read in wave 1, written by COCRDUPC and COACTUPC in wave 6 | `app/cbl/CBACT02C.cbl:120`, `app/cbl/COCRDUPC.cbl:1478`, `app/cbl/CBCUS01C.cbl:120`, `app/cbl/COACTUPC.cbl:4086` |
| 2 and 6 | 10 contract | CBEXPORT and CBACT01C read masters that wave 6 writes | `app/cbl/CBEXPORT.cbl:41`, `app/cbl/CBACT01C.cbl:29` |
| 3 and 4 | 10 call | Wave 4 programs return to the menu and sign-on in wave 3 | `app/cbl/COTRN00C.cbl:123`, `app/cbl/COTRN00C.cbl:108` |
| 3 and 6 | 15 call | Wave 6 online programs return to the menu and sign-on in wave 3 | `app/cbl/COBIL00C.cbl:130`, `app/cbl/COACTUPC.cbl:939` |
| 3 and 7 | 2 call | COPAUS0C returns to the menu and sign-on | `app/app-authorization-ims-db2-mq/cbl/COPAUS0C.cbl:236`, `app/app-authorization-ims-db2-mq/cbl/COPAUS0C.cbl:669` |
| 4 and 6 | 1 call, 12 contract | COCRDLIC hands over to COCRDUPC, and the report and inquiry programs read what wave 6 writes | `app/cbl/COCRDLIC.cbl:554`, `app/cbl/COTRN00C.cbl:593` |
| 6 and 7 | 12 contract | COPAUA0C and COPAUS0C read masters that wave 6 writes | `app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:525`, `app/app-authorization-ims-db2-mq/cbl/COPAUS0C.cbl:869` |

Every crossing is a read across a master, or a return to the menu. The menu is the one place all the calls converge, and it is in wave 3. That is why the plan moves it before the online waves.

CA-7 chains CBPAUP0J (wave 7) ahead of POSTTRAN (wave 6) (`app/scheduler/CardDemo.ca7:70`). Wave 6 has to keep that trigger working while wave 7 is still legacy.

## If the system were ten times larger

I would cut by business function first: accounts, cards, transactions, users and reports. Inside each I would apply the same rule: readers before writers, reference data before state, and the front door once the harness is proven. I would cut the money core by dataset, one wave per master with all of its writers, and that is only possible if a service can front each master. Here it would not pay. The account master has four writers and the transaction master three, and one facade is cheaper than two services.

## Not ported

| Unit | Reason | Evidence |
|---|---|---|
| CBTRN01C | Verification prototype that nothing runs. CBTRN02C posts | `app/cbl/CBTRN01C.cbl:5` |
| COBSWAIT | Sleeps through an assembler routine so CICS file open and close can finish | `app/cbl/COBSWAIT.cbl:38` |
| job:WAITSTEP | Runs COBSWAIT. An explicit dependency replaces it | `app/jcl/WAITSTEP.jcl:22` |
| job:CBLDBMS | Build job | `samples/jcl/BMSCMP.jcl:38` |
| job:CICCMP | Build job | `samples/jcl/CICCMP.jcl:41` |
| job:CIDBCMP | Build job | `samples/jcl/CICDBCMP.jcl:54` |
| job:CNJBATMP | Build job | `samples/jcl/BATCMP.jcl:42` |
| job:IMSMQCMP | Build job | `samples/jcl/IMSMQCMP.jcl:37` |
| job:REPRTEST | Sample and test job | `samples/jcl/REPRTEST.jcl:23` |
| job:SORTTEST | Sample and test job | `samples/jcl/SORTTEST.jcl:19` |
| job:LISTFILS | Catalog listing utility | `samples/jcl/LISTCAT.jcl:27` |
| job:RACFCMDS | RACF commands. The new identity setup replaces them | `samples/jcl/RACFCMDS.jcl:19` |
| job:TXT2PDF1 | Vendor REXX text to PDF converter | `app/jcl/TXT2PDF1.JCL:24` |
| job:FTPJCLS | Demonstration FTP with a user id and password in the in-stream data. Rotate the credential | `app/jcl/FTPJCL.JCL:34`, `app/jcl/FTPJCL.JCL:35` |
| job:INTRDRJ1 | Demonstration of the internal reader | `app/jcl/INTRDRJ1.JCL:14` |
| job:INTRDRJ2 | Target of INTRDRJ1 | `app/jcl/INTRDRJ2.JCL:7` |
| job:DEFCUST | Defines clusters under a different high-level qualifier that no program reads. Provisional | `app/jcl/DEFCUST.jcl:22` |
| job:ESDSRRDS | Builds demonstration ESDS and RRDS user files from in-stream records with clear text passwords. Provisional | `app/jcl/ESDSRRDS.jcl:36` |
| job:CBADMCDJ | Installs CICS resource definitions. Carry the transaction to program map and the JOBS queue into the new runtime configuration | `app/jcl/CBADMCDJ.jcl:27` |
| proc:BLDCIDB2, proc:BUILDBAT, proc:BUILDBMS, proc:BUILDONL | Build procedures | `samples/proc/BLDCIDB2.prc:1`, `samples/proc/BUILDBAT.prc:1`, `samples/proc/BUILDBMS.prc:1`, `samples/proc/BUILDONL.prc:1` |
| cpy:UNUSED1Y | Not a movable unit. No program includes it. Delete it | `app/cpy/UNUSED1Y.cpy:1` |
