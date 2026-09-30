# 03 Waves

Target state: refactor. Machine-readable plan: `modernization-assessment/waves.json`. Scores behind the blast radius and confidence columns: `modernization-assessment/risks.json`. Seed the plan started from: `modernization-assessment/03a-wave-seed.md`.

The plan keeps the extractor's seven families. It makes two changes, each with a cited reason. It leaves the largest wave uncut, for a reason given below. A plan with few deviations is a fine answer.

## The plan at a glance

| Wave | Name | Units | Blast radius | Confidence | What it unblocks | Evidence |
|---|---|---|---|---|---|---|
| 1 | Environment and utility jobs | 6 | low | medium | The target environment. No port. A chore | `modernization-assessment/waves.json:5`, `app/jcl/CBADMCDJ.jcl:27` |
| 2 | Read-only batch utilities and the data import | 10 | low | medium | The proven toolchain, decimal type and comparison harness | `modernization-assessment/waves.json:56`, `app/cbl/CBACT01C.cbl:231` |
| 3 | Sign-on, menus and read-only screens | 7 | medium | medium | The routing facade and the authentication decision | `modernization-assessment/waves.json:107`, `app/cpy/COMEN02Y.cpy:28` |
| 4 | GDG, internal reader and build jobs | 10 | low | low | Nothing on the port path. A chore | `modernization-assessment/waves.json:155`, `app/jcl/INTRDRJ1.JCL:17` |
| 5 | Nightly batch cycle | 56 | high | low | Wave 6 and the archived generations that become golden masters | `modernization-assessment/waves.json:202`, `app/cbl/CBTRN02C.cbl:256` |
| 6 | Online transactions that update the masters | 9 | high | low | Retirement of CICS and of the legacy masters | `modernization-assessment/waves.json:315`, `app/cbl/COBIL00C.cbl:212` |
| 7 | DB2, IMS and MQ subsystems | 25 | medium | low | Retirement of the legacy scheduler bridge and the DB2 reference-data pipeline | `modernization-assessment/waves.json:365`, `app/scheduler/CardDemo.ca7:43` |

No wave has high confidence. The seed lists computed calls in waves 3, 5, 6 and 7, and those waves cannot be high by rule. Waves 1, 2 and 4 are held down by files the extractor could not read (assembler, the CA-7 listing) and by the unmodeled internal-reader chain. Evidence for the computed calls: `modernization-assessment/03a-wave-seed.md:35`, `modernization-assessment/03a-wave-seed.md:49`, `modernization-assessment/03a-wave-seed.md:57`, `modernization-assessment/03a-wave-seed.md:65`.

## Changes to the seed

| Unit | From | To | Reason | Confidence | Evidence |
|---|---|---|---|---|---|
| job:CREADB2 | 1 | 7 | It runs DB2 DDL and loads through IKJEFT01, reading control members the extractor lists as not parsed. Anything that touches DB2 belongs in the subsystem wave. The job card also says TYPRUN=SCAN | high | `app/app-transaction-type-db2/jcl/CREADB21.jcl:2`, `app/app-transaction-type-db2/jcl/CREADB21.jcl:52`, `app/app-transaction-type-db2/ctl/DB2CREAT.ctl:35` |
| job:TXT2PDF1 | 4 | 5 | It converts STATEMNT.PS, which CREASTMT writes through CBSTM03A in wave 5, and CA-7 triggers it right after CREASTMT. In wave 4 it has no input to test and delivers nothing nameable | medium | `app/jcl/TXT2PDF1.JCL:33`, `app/jcl/CREASTMT.JCL:91`, `app/scheduler/CardDemo.ca7:468`, `app/scheduler/CardDemo.ca7:495` |

Changes I considered and did not make:

| Candidate | Why not | Confidence | Evidence |
|---|---|---|---|
| Cut wave 5 at CBTRN02C, CBTRN03C, CBACT04C or CBSTM03A, all articulation points | One sentence describes the wave: the cycle the wrappers and schedulers chain into one order. Of its 56 units, 17 are scheduler nodes and 9 are programs. A cut would split units that the scheduler order and the shared GDG generations tie together | medium | analysis field articulation_points, `scripts/run_full_batch.sh:47`, `app/jcl/COMBTRAN.jcl:24` |
| Move the four READ jobs from wave 2 into wave 5 because CA-7 chains them between CLOSEFIL and OPENFIL | CA-7 is not parsed, and I do not know it is the production scheduler. A ported job can be launched by the legacy scheduler and waited on. If the client confirms CA-7 as production, this changes, and wave 2 shrinks to CBIMPORT | low | `app/scheduler/CardDemo.ca7:340`, `app/scheduler/CardDemo.ca7:421`, `app/scheduler/CardDemo.ca7:453` |
| Move sign-on and the menus later, since every online program returns to them | They are the routing facade. Ported first, they can forward to legacy transactions by name. Ported last, the legacy front door would have to be kept alive for nothing | medium | `app/cbl/COMEN01C.cbl:185`, `app/cpy/COMEN02Y.cpy:28` |
| Move a high-high unit from an early wave | None is in an early wave. Waves 1 to 4 hold no high-high unit | high | `modernization-assessment/risks.json:2` |

## Are the waves valid

A wave is valid only if all four tests hold. Wave 1 and wave 4 do not pass the fourth, and I say so instead of dressing them up.

| Wave | Deploys independently | Rolls back independently | Testable boundary | A stakeholder can name it | Confidence | Evidence |
|---|---|---|---|---|---|---|
| 1 | yes | yes | weak: little output to compare | no, a chore | medium | `samples/jcl/LISTCAT.jcl:1` |
| 2 | yes | yes | yes: printable output of each utility | weakly: reference data listings | medium | `app/jcl/READACCT.jcl:32` |
| 3 | yes, behind a routing facade | yes, by pointing the transactions back at legacy | yes: screen data stream | yes: the new front door | medium | `app/cbl/COSGN00C.cbl:223` |
| 4 | yes | yes | weak | no, a chore | medium | `app/jcl/DEFGDGD.jcl:27` |
| 5 | only with a data facade and a scheduler bridge | only if rollback restores the masters, which the delete and define jobs make hard | yes: daily feed and masters in, masters, rejects and report out | yes: the nightly cycle runs on the new platform | low | `app/jcl/TRANBKP.jcl:40`, `app/cbl/CBTRN02C.cbl:256` |
| 6 | per transaction, behind the facade | per transaction | yes: screens plus master records | yes: maintenance runs on the new platform | low | `app/cbl/COBIL00C.cbl:234` |
| 7 | unknown | unknown | unknown until the IMS and DB2 members are read | yes: pending authorizations | low | inference |

Wave 4 could be dropped as a wave and its three application jobs handled inside wave 5's scheduler port. I left it because the family test separates it and merging for tidiness is not a reason on the list.

## Where the must-not-break items land

All three are in wave 5. That is the largest and least safe wave, and the plan says so.

| Item you named | Unit in the tree | Wave | Confidence | Evidence |
|---|---|---|---|---|
| Daily transaction posting | job:POSTTRAN and CBTRN02C | 5 | high | `app/jcl/POSTTRAN.jcl:23`, `app/cbl/CBTRN02C.cbl:256` |
| The account and card master refresh | job:ACCTFILE and job:CARDFILE, which the wrapper labels Refresh Account Master file and Refresh Card Master | 5 | medium | `scripts/remote_refresh.sh:16`, `scripts/remote_refresh.sh:19`, `app/jcl/ACCTFILE.jcl:25`, `app/jcl/CARDFILE.jcl:36` |
| The transaction report | job:TRANREPT, proc:TRANREPT, CBTRN03C, and CORPT00C which submits the proc from CICS | 5 | medium | `app/jcl/TRANREPT.jcl:1`, `app/jcl/TRANREPT.jcl:59`, `app/cbl/CORPT00C.cbl:94` |

Each maps to a unit, but two map thinly. The refresh jobs appear only in developer FTP wrappers, and TRANREPT appears in no scheduler. See Open Questions in `modernization-assessment/00-summary.md`.

## What must sit behind a facade first

CBTRN02C, CBTRN03C, CORPT00C, job:CARDFILE and job:TRANREPT are high port difficulty and high blast radius, and they are must-not-break items, so they cannot go last. They go fifth of seven. Four things have to exist before wave 5 starts:

1. A data-access facade over the account, card, cross-reference, customer, transaction, category-balance and user files. It must keep key order, REWRITE and browse semantics. New batch writers in wave 5 and legacy CICS writers until wave 6 both use it. Reason: `modernization-assessment/02-coupling.md:9`.
2. A scheduler bridge. The legacy scheduler keeps launching jobs and waits for the new ones to finish, because CA-7 runs POSTTRAN only after the IMS job CBPAUP0J and the weekly Control-M refresh waits for the DB2 job MNTTRDB2 (`app/scheduler/CardDemo.ca7:70`, `app/scheduler/CardDemo.controlm:34`).
3. A generation catalog that reproduces (+1) and (0) addressing, since COMBTRAN reads BKUP(0) and the report writes BKUP(+1) (`app/jcl/COMBTRAN.jcl:24`, `app/jcl/TRANREPT.jcl:33`).
4. A job-submission service to replace the internal reader that CORPT00C writes to (`app/cbl/CORPT00C.cbl:517`).

## Risk profile by wave

| Wave | low-low | high-low | low-high | high-high | Confidence | Evidence |
|---|---|---|---|---|---|---|
| 1 | 6 | 0 | 0 | 0 | medium | `modernization-assessment/risks.json:2` |
| 2 | 8 | 2 | 0 | 0 | medium | `modernization-assessment/risks.json:2` |
| 3 | 2 | 3 | 2 | 0 | medium | `modernization-assessment/risks.json:2` |
| 4 | 7 | 0 | 0 | 0 | low | `modernization-assessment/risks.json:2` |
| 5 | 8 | 2 | 13 | 14 | low | `modernization-assessment/risks.json:2` |
| 6 | 0 | 2 | 3 | 4 | low | `modernization-assessment/risks.json:2` |
| 7 | 1 | 10 | 0 | 11 | low | `modernization-assessment/risks.json:2` |

Wave 1 is all low-low, as the risk rules want for a first wave, but it proves nothing about the COBOL toolchain because it holds no COBOL. Wave 2 is where the toolchain is proved. Wave 5 holds 14 of the 29 high-high units and 13 of the 18 low-high units, which is why it is the wave to watch. Wave 7 has 11 high-high units on the thinnest evidence in the assessment.

One decision belongs to the steering committee. Waves 5 and 6 could swap. Moving the online writers first would put small interactive units ahead of the batch cycle that holds the must-not-break items, at the price of the same data-facade work in the other direction. The family order puts batch first, and I kept it. I have no evidence that the swap is better.

## Wave notes

Wave 1. Six jobs. job:DEFCUST names clusters that nothing reads, so it looks orphaned (`app/jcl/DEFCUST.jcl:25`, `app/jcl/DEFCUST.jcl:35`). job:FTPJCLS holds a host address and login in clear text (`app/jcl/FTPJCL.JCL:33`). Neither should be ported.

Wave 2. CBACT01C substitutes 2525.00 when the cycle debit is zero (`app/cbl/CBACT01C.cbl:237`) and calls the assembler date routine (`app/cbl/CBACT01C.cbl:231`). CBIMPORT selects a DD its JCL never maps (`app/cbl/CBIMPORT.cbl:63`).

Wave 3. Sign-on compares a clear-text password (`app/cbl/COSGN00C.cbl:223`). The authentication decision is separate from the port.

Wave 4. Seven of ten units are build tooling that CI replaces. See `do_not_port` in `modernization-assessment/risks.json:2159`.

Wave 5. Port order inside the wave is a job for `--wave 5`. The short version: the reference and refresh jobs first, then TRANBKP, POSTTRAN and TRANIDX as one tested chain, then interest and combine, then the report and the statements.

Wave 6. COACTUPC is 3,368 lines and should be strangled one screen at a time.

Wave 7. Read the IMS and DB2 members first. Until then any estimate for this wave is a guess.
