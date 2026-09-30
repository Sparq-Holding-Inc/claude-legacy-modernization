# 04 Estimate

Every number here is inference. No historical velocity, no team size and no target platform was supplied, so nothing is calibrated. These are planning ranges in engineer-weeks, not quotes. The first real number comes from wave 2, when the team's measured velocity replaces the rates below. Re-run this estimate then.

## Method

Each wave is the sum of four terms. The last three matter more than lines of code.

1. Port. Program lines in the wave (from `modernization-assessment/01-inventory.md`) times a rate for transliteration into the target with a working comparison harness: 1 to 2 engineer-weeks per 1,000 lines where port difficulty is low, 2 to 4 where it is medium, 4 to 7 where it is high, 5 to 8 for IMS and MQ code with no direct target.
2. Boundary work. The edges that cross the wave boundary: shared datasets, contract edges to programs in other waves, scheduler links. This is where the data facade, the routing facade and the scheduler bridge are paid for.
3. Equivalence harness. The oracle, the normalization spec and the deviation register from `modernization-assessment/06-test-strategy.md`.
4. Cutover. Rehearsals and the rollback procedure.

Inputs, computed from `graph.json` and `waves.json`:

| Wave | Programs | Program lines | Jobs, procs, scheduler nodes | Contract edges touching it, and crossing | Shared datasets | Confidence | Evidence |
|---|---|---|---|---|---|---|---|
| 1 | 0 | 0 | 6, 0, 0 | 0, 0 | 0 | high | analysis field wave_seed, `modernization-assessment/waves.json:5` |
| 2 | 5 | 1,084 | 5, 0, 0 | 7, 7 | 5 | high | analysis field wave_seed, `modernization-assessment/waves.json:56` |
| 3 | 7 | 2,679 | 0, 0, 0 | 14, 14 | 6 | high | analysis field wave_seed, `modernization-assessment/waves.json:107` |
| 4 | 0 | 0 | 7, 3, 0 | 0, 0 | 0 | high | analysis field wave_seed, `modernization-assessment/waves.json:155` |
| 5 | 9 | 3,683 | 28, 2, 17 | 34, 26 | 6 | high | analysis field wave_seed, `modernization-assessment/waves.json:202` |
| 6 | 9 | 7,972 | 0, 0, 0 | 57, 33 | 7 | high | analysis field wave_seed, `modernization-assessment/waves.json:315` |
| 7 | 13 | 7,071 | 9, 1, 2 | 12, 12 | 4 | high | analysis field wave_seed, `modernization-assessment/waves.json:365` |

Wave 6 is the largest in lines because of COACTUPC alone, at 3,368 lines. Wave 5 is small in lines and large in everything else. It has 45 job and scheduler units to rewrite, 26 contract edges that cross its boundary and the three must-not-break items. That is why lines of code would mislead here.

## Ranges

| Wave | Port | Boundary | Harness | Cutover | Total, engineer-weeks | Confidence in the range | Evidence |
|---|---|---|---|---|---|---|---|
| 1. Environment and utility jobs | 3 to 6 | included | 0 | 0 | 3 to 6 | medium | inference |
| 2. Read-only batch utilities | 2 to 3 | 2 to 4 (read adapter over the legacy files) | 2 to 4 (the first harness, the decimal type) | 1 to 2 | 7 to 13 | medium | inference |
| 3. Sign-on, menus, read-only screens | 5 to 11 | 3 to 6 (routing facade), 2 to 5 (authentication) | 3 to 6 | 1 to 2 | 14 to 30 | low | inference |
| 4. GDG, internal reader, build | 1 to 2 | 0 | 0 | 0 | 1 to 2 | medium | inference |
| 5. Nightly batch cycle | 15 to 26 for programs, 13 to 27 for the 45 job and scheduler units | 9 to 18 (write-side data facade, generation catalog, scheduler bridge) | 8 to 14 | 3 to 6 | 48 to 91 | low | `app/cbl/CBTRN02C.cbl:256`, `app/jcl/COMBTRAN.jcl:24` |
| 6. Online transactions that update the masters | 32 to 48 | 5 to 10 (key allocation, coexistence), 9 (nine screen maps) | 6 to 10 | 3 to 6 | 55 to 83 | low | `app/cbl/COBIL00C.cbl:212`, `app/cbl/COTRN02C.cbl:444` |
| 7. DB2, IMS and MQ | 35 to 57 | 7 to 12 (data migration, MQ) | 6 to 12 | 3 to 6 | 51 to 87 | very low | inference |
| Total | | | | | 179 to 312 | low | inference |

Wave 7 is a guess. The IMS database definitions, the DB2 DDL and the MQ set-up are all in the not-parsed list, so no one has read what the port must reproduce. The total shows a 1.8 to 1 spread for that reason. Two figures are not in the total: calendar time, which depends on team size, and the migration of production data volumes, which the tree does not size.

## The assumptions the ranges are most sensitive to

Stated so that each can be shown wrong.

1. Assumes the target store can give ordered browse by key and REWRITE semantics on the account and transaction files behind one data facade that both platforms use during coexistence. If it cannot, and the masters must be replicated instead, waves 5 and 6 each add roughly 8 to 12 weeks for reconciliation, because two copies of the account master would then be updated by different code (`app/cbl/CBTRN02C.cbl:554`, `app/cbl/COBIL00C.cbl:379`).
2. Assumes at least two complete archived cycles exist for the oracle in wave 5: the transaction backup, reject and report generations, and the daily input each was made from. The generation bases hold five at most (`app/jcl/DEFGDGB.jcl:25`), so the client must capture them now. If none exist, wave 5 verification roughly doubles, adding 8 to 14 weeks, and the oracle becomes characterization only.
3. Assumes the IMS, DB2 and MQ members read the way the COBOL implies. Nothing verifies this. If the client wants the authorization subsystem redesigned instead of ported, discard the wave 7 range.
4. Assumes at least two people on the client side can read COBOL, JCL and IDCAMS. If not, add 20 to 30 percent to every wave for discovery.

Two claims worth the most to a steering committee: if the 28 jobs and 17 scheduler nodes in wave 5 turn out to share one small set of patterns (delete, define, REPRO), the 13 to 27 week job term falls by about a third, since 10 of the 28 jobs are IDCAMS delete, define and REPRO reloads (`app/jcl/ACCTFILE.jcl:25`). If the CA-7 listing is confirmed as the production scheduler, wave 2 shrinks by four jobs and their programs and wave 5 grows by the same amount, with no net change in the total.

## Where Claude Code can do the port, and where it cannot

| Work | Claude Code | Why | Confidence | Evidence |
|---|---|---|---|---|
| Transliterating small read-only programs with a diff harness (wave 2, most of wave 3) | strong | Short programs, no hidden rules, output to compare | medium | `app/cbl/CBACT02C.cbl:29`, `app/cbl/COTRN01C.cbl:39` |
| IDCAMS delete, define and REPRO jobs into target storage scripts | strong | Repeating pattern, mechanical | medium | `app/jcl/ACCTFILE.jcl:25`, `app/jcl/TRANFILE.jcl:35` |
| Generating the comparison harness, the normalization spec and the layout-to-record mapping from the copybooks | strong | Structured and checkable | medium | `app/cpy/CVTRA05Y.cpy:1`, `app/cpy/CVACT01Y.cpy:4` |
| Reading a screen program and proposing the equivalent service | medium | Works when the rules are in the code. The 3,368-line COACTUPC needs a human owner for each edit rule | low | `app/cbl/COACTUPC.cbl:573` |
| Recovering intent from undocumented rules (reject codes, the 2525.00 substitution, the fixed sort offsets) | weak | The code says what it does, not whether it is wanted. A person decides each one and writes it in the deviation register | medium | `app/cbl/CBTRN02C.cbl:556`, `app/cbl/CBACT01C.cbl:237`, `app/jcl/TRANREPT.jcl:41` |
| CBSTM03A, which uses ALTER and walks z/OS control blocks | weak | No clean equivalent. Redesign the statement flow from its output, not its source | medium | `app/cbl/CBSTM03A.CBL:300`, `app/cbl/CBSTM03A.CBL:266` |
| Job order, GDG generations and the daily cycle definition | weak | The definition is spread over four artifacts that disagree. The client must say which is right | medium | `scripts/run_posting.sh:26`, `app/scheduler/CardDemo.ca7:70` |
| IMS, DB2 and MQ behavior | weak, and unread | The definitions are not parsed | low | inference |
| The authentication design | not a port | A decision about identity, not a translation | medium | `app/cbl/COSGN00C.cbl:223` |

## What the ranges leave out

Non-functional work (security review, performance tuning, operations and monitoring), the cost of running both platforms during coexistence, user training, and any change to what the system does. The plan is a behavior-preserving refactor. Anything in the deviation register that the client wants changed on purpose is extra scope.
