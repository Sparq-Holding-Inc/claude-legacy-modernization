# 04 Estimate

Target state: refactor. Telemetry: none. There is no time-and-motion data for this team, so every number below is `inference`. Read the assumptions before the ranges.

## Method

The unit is engineer-weeks of one developer who can read COBOL and JCL. It includes the porting, the harness for that wave, and the wave's share of parallel-run time. It excludes environment provisioning, security review, and business acceptance.

Each range comes from five drivers, in this order of weight, taken from the assessment skill:

1. Coupling edges that cross the wave boundary. I counted call and contract edges in `graph.json` between units placed in different waves.
2. Whether an oracle exists. There is none in the tree. See `06-test-strategy.md`.
3. Programs that behave like god modules. None meets the extractor's rule. COACTUPC (3368 lines) is the closest.
4. Business logic in the database. Wave 8 only.
5. Whether the team can read the source language. Unknown. Open question 8 in `00-summary.md`.

A range is a low case and a high case, not a confidence interval.

## Per wave

| Wave | Range (engineer-weeks) | Cross-wave call and contract edges | What drives it | Confidence | Evidence |
|---|---|---|---|---|---|
| 1. Read-only batch extracts and setup | 6 to 12 | 14 (all inbound: later waves read its layouts) | Toolchain bring-up, the assembler date routine, packed decimal export, the generation dataset replacement | medium | inference |
| 2. Transaction report | 3 to 6 | 1 | Small program, but two quirks to decide and a byte-exact compare | medium | `app/cbl/CBTRN03C.cbl:177` |
| 3. Master and reference data refresh | 4 to 8 | 11 | No COBOL. Data-store load, state diff, and the delete-before-load fix | medium | `app/jcl/ACCTFILE.jcl:25` |
| 4. Daily transaction posting | 12 to 24 | 24 | One 619-line program, three masters, no restart point, three disagreeing schedulers, a shadow run | low | `app/cbl/CBTRN02C.cbl:440` |
| 5. Online sign-on, menus and inquiry | 10 to 20 | 35 | The router, the authentication redesign, 8 programs, the screen layer | low | `app/cpy/COMEN02Y.cpy:28` |
| 6. Online maintenance and payment | 16 to 32 | 50 | 10 programs including a 3368-line one, one key scheme for all writers, 45 edges out to waves 5, 1, 4, 7 and 8 | low | `app/cbl/COACTUPC.cbl:573` |
| 7. Month-end interest and statements | 14 to 28 | 25 | ALTER and control-block addressing in CBSTM03A, a real month-end shadow run, the missing REXX exec | low | `app/cbl/CBSTM03A.CBL:300` |
| 8. Authorization and transaction-type modules | 16 to 40 | 16 | IMS, DB2 and MQ. Outside what the extractor reads. Wide range on purpose. | low | inference |
| Total | 81 to 170 | | | low | inference |

The account master is touched by units in 7 of the 8 waves, and the transaction master by units in 6. That is why the middle waves cost more than their line counts suggest (inference from `graph.json` and `waves.json`).

## The assumptions that move the number

Each is stated so it can be shown false.

1. **The shared masters stay where they are through wave 6.** The plan assumes batch and online read and write the same VSAM files until wave 6 ends. If the client wants batch on a new platform while CICS stays, add a two-way data sync. Waves 3 to 6 then grow by roughly a third to a half. Evidence that it matters: 13 datasets are touched from more than one wave, led by the account master (`app/cbl/CBTRN02C.cbl:51`, `app/cbl/COBIL00C.cbl:41`).
2. **The client can supply archived generations.** The plan assumes at least 13 months of TRANSACT.BKUP and TRANREPT generations exist (`app/jcl/TRANBKP.jcl:29`, `app/jcl/TRANREPT.jcl:80`). If they do not, waves 2 and 4 lose their oracle and lean on tests generated from source, and their test effort roughly doubles.
3. **CA-7 is stale and Control-M plus the scripts are live.** If the CA-7 listing is live, wave 4 also depends on the IMS purge job that CA-7 runs ahead of posting (`app/scheduler/CardDemo.ca7:43`, `app/scheduler/CardDemo.ca7:70`), and the wave 4 range moves up by 4 to 8.
4. **Fourteen programs share one account layout and it is the one in the tree.** `CVACT01Y` is included by 14 programs. If any utility step reads the account file with offsets that are not in the tree, waves 3 and 4 grow by 2 to 4 each. The extractor found 62 contract edges and every one is high confidence, so this holds for COBOL and is untested for control cards.
5. **The menu table is a routing table.** Wave 6 assumes a router can send one menu entry to a new screen while the rest stay legacy (`app/cbl/COMEN01C.cbl:156`). If the screens share state through the COMMAREA in ways beyond `COCOM01Y`, waves 5 and 6 merge into one wave and the sum of their ranges applies to a single cutover.
6. **The client fixes the report and interest quirks, or accepts them.** Waves 2, 4 and 7 assume each deviation in `06-test-strategy.md` gets a decision within a week. Each undecided one adds a cycle of parallel-run time.
7. **Nothing in wave 8 needs more than the ranges above.** No score in that wave rests on read DL/I or SQL. This is the least reliable line in the table.

## Where Claude Code helps and where it does not

Strong, with a working harness:

- The small readers: CBACT02C, CBACT03C, CBCUS01C, and the record layouts from `CVACT02Y`, `CVACT03Y` and `CVCUS01Y`. Mechanical transliteration.
- The IDCAMS delete, define and repro jobs in wave 3, as data-store loads, and the state-diff tooling for them.
- The comparison harness itself: the normalizer, the diff, the replay driver, the generation archive reader.
- The BMS screens in waves 5 and 6, as transliteration to a new screen layer, with the COMMAREA layout as the contract.
- Layout classes from copybooks, with zoned and packed decimal mapped to a decimal type (`app/cpy/CVTRA05Y.cpy:10`).

Weak, where a person must decide:

- Intent behind the quirks. Why a later reject code overwrites an earlier one (`app/cbl/CBTRN02C.cbl:410`, `app/cbl/CBTRN02C.cbl:417`), and whether the double count in the report total is wanted (`app/cbl/CBTRN03C.cbl:200`). Code says what it does, not whether the business wants it.
- CBSTM03A file-open dispatch through ALTER and the TIOT (`app/cbl/CBSTM03A.CBL:300`, `app/cbl/CBSTM03A.CBL:272`).
- Anything in IMS DL/I, DB2 SQL or MQ calls in wave 8.
- The order of the daily cycle. That is a fact about production, not about the source.
- Locking and concurrency between CICS and batch. The tree shows CEMT commands (`app/jcl/CLOSEFIL.jcl:26`), not the locking the target needs.

## What is not in the range

- The REXX exec for PDF conversion is not in the tree (`app/jcl/TXT2PDF1.JCL:31`).
- The FTP partner destination in FTPJCLS, if it is live (`app/jcl/FTPJCL.JCL:33`).
- Any programs or jobs that exist on the mainframe and not in this tree. Open question 4 in `00-summary.md` asks.
