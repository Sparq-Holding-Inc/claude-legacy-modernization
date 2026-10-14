# 03 Waves

Target state: refactor. Nine waves, cut from the extractor's seed (`03a-wave-seed.md`) with one deviation. The units, order and evidence are in `waves.json`.

| Wave | Name | Units | Blast radius | Confidence | Unblocks | Evidence |
|---|---|---|---|---|---|---|
| 1 | Setup and utility jobs | 7 | low | medium | Job runner and JCL conversion | `app/jcl/CBADMCDJ.jcl:1` |
| 2 | Read-only batch dumps and import | 10 | low | medium | Layout copybooks and the diff harness | `app/jcl/READACCT.jcl:1` |
| 3 | Sign-on, menus, read-only screens | 7 | medium | medium | The navigation convention | `app/cbl/COMEN01C.cbl:184` |
| 4 | Build, compile and GDG jobs | 11 | low | medium | Generation datasets for wave 6. Mostly a chore wave | `app/jcl/DEFGDGD.jcl:39` |
| 5 | Reference-data refresh, statements | 25 | medium | medium | The close and open bracket for wave 6 | `scripts/remote_refresh.sh:23` |
| 6 | Master refresh, posting, report | 30 | high | low | Wave 7. The nightly cycle on the new platform | `app/jcl/POSTTRAN.jcl:23` |
| 7 | Online screens that write | 9 | high | low | Retiring the CICS file definitions | `app/cbl/COACTUPC.cbl:573` |
| 8 | Authorization and DB2 unload and load | 16 | medium | low | Wave 9, and the IMS and MQ runtimes | `app/app-authorization-ims-db2-mq/cbl/DBUNLDGS.CBL:222` |
| 9 | Authorization screens, type maintenance | 8 | medium | low | Nothing; can be deferred | `app/app-transaction-type-db2/cbl/COTRTLIC.cbl:338` |

## Why this order

The seed puts read-only work first, then writers, then the DB2/IMS/MQ subsystems, and the evidence supports it. Waves 1 and 2 are cheap and prove the toolchain and the harness on read paths before any write path moves. Wave 6 carries all three must-not-break items, so it comes after the harness has been used twice.

## The one real tension: wave 6 before wave 7

Batch writers (wave 6) and online writers (wave 7) share the same account, card and transaction masters (`02-coupling.md`, pattern 1). Dependency wins over the quadrant: the risk assessor scored `CBTRN02C`, `CBTRN03C` and `CORPT00C` high-high, and a high-high unit that everything depends on cannot go last. What makes it movable is a **facade over the three VSAM masters** (`ACCTDATA`, `TRANSACT`, `TCATBALF`), built in wave 6 and used by the online writers in wave 7. Without it, wave 6 would leave the online screens reading a store the batch job no longer updates.

The alternative, moving the online writers first, was rejected: they depend on the same masters, and the three biggest ones (`COACTUPC` at 3,368 lines, `COCRDUPC`, `COTRN02C`) are scored low-confidence, so they should wait for the harness.

## Deviation

| Unit | From | To | Reason | Evidence |
|---|---|---|---|---|
| job:CARDFILE | 5 | 6 | The account and card refresh is one must-not-break operation run as ACCTFILE then CARDFILE. The seed cut it in two | `scripts/remote_refresh.sh:20` |

## Waves with computed calls

Waves 3, 6, 7 and 9 contain programs with computed calls (`03a-wave-seed.md:38`), so none gets high confidence. The cartographer read every one of the 28 and found literal targets only (`02-coupling.md`, the honest boundary), which is why waves 3 is medium rather than low. That is inference from reading, not a control-flow proof.

## Not placed

`CBTRN01C` is unplaced. See `05-dead-code.md`.
