# 03 Waves

Target state: refactor. The plan is `waves.json`. It starts from the extractor's seed (`03a-wave-seed.md`) and changes one thing. Nine waves, 123 units placed, one unit unplaced.

| Wave | Name | Blast radius | Confidence | Unblocks | Evidence |
|---|---|---|---|---|---|
| 1 | Utility and admin jobs | low | medium | The job runner and deployment path | `app/jcl/DEFCUST.jcl:1` |
| 2 | Read-only extract batch | low | medium | Verified readers for the VSAM layouts | `app/cbl/CBACT01C.cbl:29` |
| 3 | Online inquiry screens | medium | low | The navigation layer for wave 7 | `app/cbl/COMEN01C.cbl:201` |
| 4 | Build and data-definition jobs | low | medium | The new build toolchain. A chore, it unblocks no business capability | `app/jcl/DEFGDGD.jcl:39` |
| 5 | Reference-data loads and the CICS handshake | medium | medium | The handshake wave 6 needs | `app/jcl/CLOSEFIL.jcl:26` |
| 6 | Posting, master refresh and transaction report | high | low | All three must-not-break items | `app/cbl/CBTRN02C.cbl:51` |
| 7 | Online maintenance and payment screens | high | low | Retires the second writer of the account and transaction files | `app/cbl/COACTUPC.cbl:573` |
| 8 | Authorization and unload subsystem | medium | low | Retires the IMS region | `app/app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl:24` |
| 9 | Authorization screens and transaction-type DB2 | medium | low | Retires DB2 and IMS | `app/app-transaction-type-db2/cbl/COBTUPDT.cbl:137` |

## Why this order

Dependency decides, not risk. Wave 6 is the riskiest wave and it still goes sixth, because it needs wave 5's file handshake (`app/jcl/OPENFIL.jcl:26`) and wave 2's tested readers, and because its writers must be live before the online writers in wave 7 can be retired. The risk pass puts CBTRN02C, CBACT04C and several online programs in high-high. None of them can move later without breaking a dependency, so the plan does not move them. What makes them movable is a shared-store facade: the new batch code reads and writes the same VSAM records as CICS until wave 7 ships.

## The one deviation

`job:CARDFILE` moves from wave 5 to wave 6. The client named "the account and card master refresh" as one thing. ACCTFILE is in wave 6 and the wrapper submits ACCTFILE then CARDFILE back to back (`scripts/remote_refresh.sh:17`, `scripts/remote_refresh.sh:20`). Left in wave 5, the refresh would straddle two waves and have no single testable boundary.

## Wave 6 is not cut

It has 30 units, over the 25 guideline. One sentence describes it: the batch ledger cycle. CBTRN02C and CBACT04C both update the account and category-balance files (`app/cbl/CBTRN02C.cbl:51`, `app/cbl/CBACT04C.cbl:28`), so cutting at the CBACT04C articulation point would split two writers of one file across waves. The wave plan (`--wave 6`) will sequence it internally: refresh jobs, then posting, then report, then the monthly interest cycle.

## What each wave's confidence rests on

- Waves 3, 7 and 9 hold the online programs. They carry the 28 computed calls, so they cannot be high (`02-coupling.md`).
- Wave 6 is low for four reasons: CORPT00C makes a computed call (`app/cbl/CORPT00C.cbl:548`); the CA-7 listing that triggers POSTTRAN through CBPAUP0J was not parsed (`app/scheduler/CardDemo.ca7:70`); nothing in the tree produces the daily transaction file; and the shell scripts run POSTTRAN then sleep 10 seconds with no completion check (`scripts/run_posting.sh:26`, `scripts/run_posting.sh:27`).
- Wave 8 is low because the IMS DBD and PSB files and the DB2 DDL are not read (`app/app-authorization-ims-db2-mq/ims/DBPAUTP0.dbd`).

## Not placed

CBTRN01C. No static edge reaches it (`app/cbl/CBTRN01C.cbl:23`).
