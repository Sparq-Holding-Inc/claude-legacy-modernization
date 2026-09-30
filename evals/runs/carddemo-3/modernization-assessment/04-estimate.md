# 04 Estimate

The estimate is a range per wave, in engineer-weeks, for a small team that has at least one person
who can read COBOL and JCL and that uses Claude Code for the mechanical work. Every figure is
inference. The counts under it are facts from `graph.json`. Treat the figures as a first bracket and
replace them with measured velocity after waves 1 and 2.

## Method

I did not estimate from lines of code. I weighted, in this order:

1. Contract and data edges that cross the wave boundary. Of 62 contract edges, 46 cross a boundary,
   and 26 of those touch wave 5 (`analysis`, computed from `waves.json` and `graph.json`).
2. Whether an oracle exists. There are sample data files and a catalog listing in the tree, and no
   archived production output (`app/data/ASCII/dailytran.txt:1`, `app/catlg/LISTCAT.txt:1`).
3. God modules and near-god programs inside the wave.
4. Logic held outside the application. Almost none: business rules are in COBOL, and DB2 holds one
   reference table (`app/app-transaction-type-db2/ctl/DB2CREAT.ctl:35`). Order and layout are held in JCL.
5. Whether the team can read the source language. Unknown, and it moves every row.

The effort per wave is the sum of four parts: the harness and oracle, the port, the boundary
(facade or data service), and for online waves the screens.

## Per wave

| Wave | Range (engineer-weeks) | What the range is made of | Confidence | Evidence |
| --- | --- | --- | --- | --- |
| 1. Utility jobs | 1 to 3 | Pipeline proof. Six jobs, most of them replaced by configuration | medium | `app/jcl/CBADMCDJ.jcl:27` |
| 2. Read-only batch | 3 to 6 | Five programs, 1,084 lines, plus the decimal and overpunch handling every later wave reuses | medium | `app/data/ASCII/acctdata.txt:1` |
| 3. Sign-on, menus, views | 8 to 16 | Seven programs, 2,679 lines, seven screens, the router and the COMMAREA back stack | medium | `app/cpy/COMEN02Y.cpy:28` |
| 4. Build tooling | 0.5 to 2 | Delete and replace with the build pipeline | medium | inference |
| 5. Nightly cycle | 24 to 48 | Harness and parallel run 8 to 16. Posting, interest and reports 6 to 12. Statements and the control block program 4 to 8. Scheduler and order 3 to 6. Data service 3 to 6 | low | `app/cbl/CBTRN02C.cbl:256` |
| 6. Online writers | 16 to 32 | `COACTUPC` alone 5 to 10. The other eight programs 6 to 12. Nine screens 3 to 6. Cutover 2 to 4 | low | `app/cbl/COACTUPC.cbl:573` |
| 7. Subsystem | 16 to 40 | Low confidence. IMS, DB2 and MQ files were not read | low | `app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:62` |
| Total | 68 to 147 | About 70 to 150 engineer-weeks | low | inference |

The upper bound of wave 7 is wide on purpose. It is the wave I know least about.

## The assumptions the ranges are most sensitive to

Each is stated so that a client engineer can say it is false.

| Assumption | If it is false | Evidence |
|---|---|---|
| Off-mainframe archives cover at least 12 months of daily input and BKUP generations, including one fiscal year end. The catalog shows only five generations kept for the transaction backup base | Wave 5 takes the upper bound, and its parallel run must last through a fiscal close. Replay cannot cover month end | `app/catlg/LISTCAT.txt:1639` |
| One of the four order sources is the production order, and the client can say which | The 3 to 6 weeks for order and scheduler roughly doubles, because the order has to be reverse engineered from job logs | `scripts/run_full_batch.sh:13`, `app/scheduler/CardDemo.ca7:43` |
| The legacy VSAM stays the owner of the account and transaction masters through wave 6, behind a data service | Waves 5 and 6 merge, their ranges add, and the parallel run spans both. The facade saving of 3 to 6 weeks goes, and the blast radius of the merged wave is the largest in the plan | `app/jcl/ACCTFILE.jcl:25` |
| Screens are rebuilt one for one. The tree holds 21 BMS maps: 7 in wave 3, 9 in wave 6, 1 in wave 5 and 4 in wave 7 | If the target UX is new, the screen part drops out and requirements discovery replaces it | `app/bms/COSGN00.bms:1` |
| The authorization database is a plain hierarchy. A secondary index database appears in the unload job | If it is used at run time, the IMS part of wave 7 roughly doubles | `app/app-authorization-ims-db2-mq/jcl/DBPAUTP0.jcl:32` |
| The batch report gets its date range from exactly two places, the SORT card and the DATEPARM file, and interest gets its date only from the PARM | If a third source exists, for example an operator who edits DATEPARM by hand, the report work in wave 5 grows by one to two weeks | `app/jcl/TRANREPT.jcl:43`, `app/jcl/TRANREPT.jcl:73`, `app/jcl/INTCALC.jcl:22` |

## Where Claude Code can do the mechanical port

It is strong at transliteration when there is a harness to check it. In this tree that means:

| Work | Why it suits | Evidence |
|---|---|---|
| The three read and print programs | Open, read loop, DISPLAY, about 130 lines each | `app/cbl/CBACT02C.cbl:29`, `app/cbl/CBACT03C.cbl:29`, `app/cbl/CBCUS01C.cbl:29` |
| The four user screens over one VSAM file | Plain create, read, update and delete against one layout | `app/cbl/COUSR01C.cbl:39`, `app/cbl/COUSR02C.cbl:360` |
| The reload jobs | Delete, define and load. They become data loaders | `app/jcl/CUSTFILE.jcl:35`, `app/jcl/DISCGRP.jcl:25` |
| Turning the wrapper order and Control-M conditions into a scheduler graph | The edges are already extracted | `app/scheduler/CardDemo.controlm:3` |
| The harness itself: log parsers, the normalization spec, the diff tool | It is generated from the job output and reviewed by a person | inference |

It is weak where the code encodes intent that nobody wrote down:

| Work | Why it needs a person | Evidence |
|---|---|---|
| `CBSTM03A` | ALTER, GO TO and a walk of the job's own control blocks to read DD names. A port must decide what the intent was | `app/cbl/CBSTM03A.CBL:266`, `app/cbl/CBSTM03A.CBL:300` |
| `COACTUPC` | 3,368 lines of field edits, with SSN part rules held in REDEFINES | `app/cbl/COACTUPC.cbl:117` |
| The report quirks | The loop exit at the date filter and the doubled last amount are decisions for the business, not for a translator (inference from the source) | `app/cbl/CBTRN03C.cbl:177`, `app/cbl/CBTRN03C.cbl:200` |
| The cycle order | Four sources disagree and no source line says which is right | `app/scheduler/CardDemo.controlm:3` |
| IMS, MQ and the assembler routines | Not modeled, or not parsed | `app/asm/COBDATFT.asm:1`, `app/asm/MVSWAIT.asm:1` |
| The REXX exec behind the PDF step | Not in the tree | `app/jcl/TXT2PDF1.JCL:31` |
