# 03 Waves

Target state: **refactor**. The plan is in `waves.json`. It starts from the extractor's seed (`03a-wave-seed.md`) and records no deviations. Nine waves, 123 units placed, and one unit (CBTRN01C) not placed. Confidence is never high for a wave with computed calls, and four waves have them.

The sequence follows the data, not the call graph. Reference masters first (wave 5), then the cycle that updates them in batch (wave 6), then the online programs that update the same files (wave 7). The three must-not-break items all land in wave 6, so wave 6 is where the equivalence harness has to be at its strongest and where the rollback has to be rehearsed.

| Wave | Name | Family | Units | LOC | Blast radius | Confidence | Unblocks | Evidence |
|---|---|---|---|---|---|---|---|---|
| 1 | Environment and dataset definition jobs | batch-utility | 7 | 0 | low | medium | Target environment only. A chore. | `app/jcl/CBADMCDJ.jcl:1` |
| 2 | Master file read and list jobs | batch-readonly | 10 | 1,084 | low | medium | Tested layouts for account, card, customer | `app/jcl/READACCT.jcl:1` |
| 3 | Sign-on, menus and inquiry screens | online-readonly | 7 | 2,679 | medium | low | The online shell for wave 7 | `app/csd/CARDDEMO.CSD:317` |
| 4 | Build, compile and GDG definition jobs | batch-data-jobs | 11 | 0 | low | medium | Backup generation groups for wave 6 | `app/jcl/DEFGDGD.jcl:39` |
| 5 | Card, cross-reference, customer master refresh, statements, export | batch-writers | 26 | 1,355 | medium | medium | Reference masters and the batch window for wave 6 | `app/jcl/CARDFILE.jcl:36` |
| 6 | Daily posting, account master refresh, transaction report | batch-writers | 29 | 2,328 | high | low | Wave 7, statements, the first named business result | `app/jcl/POSTTRAN.jcl:23` |
| 7 | Online account, card, bill pay, transaction and user updates | online-writers | 9 | 7,972 | high | low | Retiring the VSAM masters and CICS | `app/cbl/COACTUPC.cbl:573` |
| 8 | Authorization feed and unload (IMS, DB2, MQ) | subsystem | 16 | 2,602 | medium | low | Wave 9 | `app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:956` |
| 9 | Authorization screens and transaction type maintenance | subsystem | 8 | 4,469 | medium | low | Nothing. A stop point. | `app/app-transaction-type-db2/cbl/COTRTLIC.cbl:338` |
| Total | | | 123 | 22,489 | | | | inference |

LOC are the inventory counts per program (`modernization-assessment/01-inventory.md:20`), summed by hand per wave.

## Why the order is defensible

1. **Wave 5 before wave 6.** CBTRN02C looks up the card in the cross-reference file before it looks at the account (`app/cbl/CBTRN02C.cbl:371`, `app/cbl/CBTRN02C.cbl:380`). The cross-reference master has no writer in the program set (`modernization-assessment/graph.json:28710`), so it is only ever rebuilt by the XREFFILE job (`app/jcl/XREFFILE.jcl:64`). Posting cannot run in the target until that rebuild is ported.
2. **Wave 6 before wave 7.** The online programs read and write the files that posting updates. The contract edges from CBTRN02C to COBIL00C, COTRN02C and COACTUPC are all high (`modernization-assessment/02a-edge-tables.md:37`, `modernization-assessment/02a-edge-tables.md:42`, `modernization-assessment/02a-edge-tables.md:35`).
3. **Wave 3 before wave 7.** Every online screen is reached through sign-on and the menu (`app/cbl/COMEN01C.cbl:156`). Wave 3's low confidence comes from the six programs that make computed calls.
4. **Waves 8 and 9 last.** None of the three must-not-break items passes through them. They run on IMS, DB2 and MQ, which need other skills, and four of their definition types are unread (`modernization-assessment/graph.json:27433`).

## Wave 6 in increments

Wave 6 has 29 units. One sentence describes it, so I did not cut it into waves. I did plan three increments with their own boundary and rollback, cut at the articulation points CBTRN02C and CBTRN03C (analysis field `articulation_points`). The detail belongs in `07-wave-6-plan.md` (run `/modernize-scan --wave 6`).

| Increment | Units | Boundary to assert | Rollback | Evidence |
|---|---|---|---|---|
| 6a Posting | ACCTFILE, TCATBALF, TRANBKP, POSTTRAN, TRANIDX, CBTRN02C, CSUTLDTC, run_posting.sh | Account, transaction, category balance files and the reject file after one run | Switch the scheduler entry back to the COBOL job. Restore the account and transaction masters from the generation backup that TRANBKP writes. | `scripts/run_posting.sh:17`, `scripts/run_posting.sh:23`, `app/jcl/POSTTRAN.jcl:23` |
| 6b Report | TRANREPT, REPROC, proc TRANREPT, CBTRN03C, CORPT00C | The 133-byte report file | Keep the COBOL job. The report only reads, so rollback is a scheduler switch. | `app/jcl/TRANREPT.jcl:59`, `app/jcl/TRANREPT.jcl:78`, `app/cbl/CORPT00C.cbl:94` |
| 6c Interest and combine | INTCALC, COMBTRAN, CBACT04C, run_interest_calc.sh | Account and category balances after the monthly run | Restore from the generation backup, then rerun | `scripts/run_interest_calc.sh:19`, `scripts/run_interest_calc.sh:26`, `app/cbl/CBACT04C.cbl:41` |

Both ACCTFILE and CBTRN02C write the account master, so both move in 6a (`app/jcl/ACCTFILE.jcl:61`, `app/cbl/CBTRN02C.cbl:554`). The remaining jobs in the wave (DALYREJS, DEFGDGB, PRTCATBL, REPRTEST, REPTFILE, SORTTEST, TRANFILE) follow the increment they feed, or are test or definition jobs. Which is which is a question for the client (inference).

## Facade candidates

- **COPAUS0C, COTRN00C, COTRN01C** are god modules. Put a screen-level facade in front of them and port behind it (inference, from `analysis.god_modules`).
- **The five VSAM masters.** While batch is in the target and online is on CICS (waves 6 to 7), the masters have two owners. A single owner must be chosen, and the other side reads through an adapter. Which side owns them is the biggest design decision in the plan, and the assessment cannot make it for the client (inference).

## Not placed

CBTRN01C. See `05-dead-code.md`.
