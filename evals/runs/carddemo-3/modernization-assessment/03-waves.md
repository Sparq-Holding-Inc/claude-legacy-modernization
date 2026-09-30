# 03 Waves

Target state: refactor. The plan is in `modernization-assessment/waves.json:1`, the extractor's seed
is in `03a-wave-seed.md`, and the scores behind it are in `modernization-assessment/risks.json:1`.

## Plan at a glance

| Wave | Name | Units | Blast radius | Confidence | Evidence |
|---|---|---|---|---|---|
| 1 | Batch utility jobs and platform readiness | 6 | low | medium | `app/jcl/CBADMCDJ.jcl:1` |
| 2 | Read-only batch over the masters | 10 | low | medium | `app/jcl/READACCT.jcl:1` |
| 3 | Sign-on, menus and read-only online views | 7 | medium | medium | `app/csd/CARDDEMO.CSD:317` |
| 4 | Build tooling, GDG bases and demo jobs | 9 | low | medium | `app/jcl/DEFGDGD.jcl:39` |
| 5 | The nightly batch cycle: posting, master refresh, interest, report, statements | 56 | high | medium | `app/jcl/POSTTRAN.jcl:23` |
| 6 | Online writers of the account, card, transaction and user masters | 9 | high | medium | `app/cbl/COACTUPC.cbl:573` |
| 7 | Authorization, IMS, DB2 and MQ subsystem | 26 | high | low | `app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:956` |

One program, `CBTRN01C`, is not placed (see the end). The three must-not-break items all sit in
wave 5.

## How I treated the seed

The extractor cut the waves from facts only, in a fixed family order. I kept that order and made
three changes, each logged in `waves.json` under `deviations`. I did not move a unit for its name,
and I did not cut wave 5 for its size. The reasons follow.

| Unit | From | To | Reason | Evidence |
|---|---|---|---|---|
| job:CREADB2 | 1 | 7 | The extractor could not see DB2. The job's SYSTSIN members are in `.ctl` files it lists as not parsed, and they run DSN and create the DB2 transaction type table | `app/app-transaction-type-db2/jcl/CREADB21.jcl:58`, `app/app-transaction-type-db2/ctl/DB2TIAD1.ctl:16`, `app/app-transaction-type-db2/ctl/DB2CREAT.ctl:35` |
| job:IMSMQCMP | 4 | 7 | The extractor saw the libraries the compile job reads, not what it builds. The PARM and the MQ copy library show an IMS and MQ program | `samples/jcl/IMSMQCMP.jcl:28`, `samples/jcl/IMSMQCMP.jcl:64` |
| job:TXT2PDF1 | 4 | 5 | The CA-7 listing, not parsed by the extractor, triggers it from CREASTMT. It reads the file CBSTM03A writes, and I score it high-high, so it must not lead the wave that produces its input | `app/scheduler/CardDemo.ca7:495`, `app/jcl/TXT2PDF1.JCL:33` |

### Why wave 5 stays whole

It holds 56 units and one sentence describes it: every batch job that reloads or appends to a
shared master, or to a GDG the cycle shares. The 17 scheduler artifacts in it are the same jobs
listed again, so the work is about 28 jobs, 9 programs and 2 procs. Two facts stop me cutting it.

1. The report writes a generation the merge reads. `TRANREPT` writes `TRANSACT.BKUP(+1)` and
   `COMBTRAN` reads `TRANSACT.BKUP(0)` (`app/jcl/TRANREPT.jcl:33`, `app/jcl/COMBTRAN.jcl:24`).
   The report is not independent of posting.
2. The wrapper scripts chain the reload jobs, posting, interest and the merge in one run
   (`scripts/run_full_batch.sh:17`). The seed rule moves chained jobs together.

I checked the four reasons in the skill. Reason 1 (a must-not-break item forces a unit elsewhere)
does not apply: everything the three items need is in wave 5, except the CA-7 trigger from
`CBPAUP0J`, which I handle as an interface (below). Reason 2 (size plus one argument) fails on the
two facts above. Reason 3 applies to the three moves in the table. Reason 4 (a high-high unit placed
early) applies once: `TXT2PDF1`. No other high-high unit sits in waves 1 to 4
(`modernization-assessment/risks.json:1`).

## Wave 1. Batch utility jobs and platform readiness

Units: `job:CBADMCDJ`, `job:DEFCUST`, `job:ESDSRRDS`, `job:FTPJCLS`, `job:LISTFILS`, `job:RACFCMDS`.
Blast radius low, confidence medium.

These run no application program and touch no dataset another entry point uses. None is called by
anything. It is a chore wave and I say so: its only value is proving the build, deploy, diff and
rollback pipeline before a real program moves. Most of it is not ported. `RACFCMDS` becomes the
target's access model, `FTPJCLS` and `ESDSRRDS` carry credentials in the job stream and should be
replaced and rotated (`app/jcl/FTPJCL.JCL:33`, `app/jcl/ESDSRRDS.jcl:36`), and `DEFCUST` deletes one
cluster and defines a different one (`app/jcl/DEFCUST.jcl:25`). `CBADMCDJ` loads the CICS
definitions of the whole online estate (`app/jcl/CBADMCDJ.jcl:27`); its target is routing
configuration for wave 3.

## Wave 2. Read-only batch over the masters

Units: `CBACT01C`, `CBACT02C`, `CBACT03C`, `CBCUS01C`, `CBIMPORT`, and the jobs `READACCT`,
`READCARD`, `READCUST`, `READXREF`, `CBIMPORT`. Blast radius low, confidence medium.

They read the account, card, xref and customer masters and write only their own outputs, so each
can be deployed and rolled back alone. The layouts they read (`app/cpy/CVACT01Y.cpy:4`,
`app/cpy/CVACT02Y.cpy:4`, `app/cpy/CVACT03Y.cpy:4`) are the ones waves 3, 5 and 6 must read
correctly. Two cautions. `CBIMPORT` opens a card output DD that its job never provides
(`app/cbl/CBIMPORT.cbl:233`), so it may not run as shipped. `CBACT01C` calls an assembler routine
that was not parsed (`app/cbl/CBACT01C.cbl:231`).

It unblocks the first real proof of decimal and sign handling. The sample data shows the signs are
overpunched zoned decimal, for example `{` and `G` in the amount fields (`app/data/ASCII/dailytran.txt:1`,
`app/data/ASCII/acctdata.txt:1`).

## Wave 3. Sign-on, menus and read-only online views

Units: `COSGN00C`, `COMEN01C`, `COADM01C`, `COACTVWC`, `COCRDSLC`, `COTRN00C`, `COTRN01C`.
Blast radius medium, confidence medium.

This is the front door. Sign-on, the two menus and the two transaction views are two strongly
connected components and move whole. Every online transaction is reached through the menu tables
(`app/cpy/COMEN02Y.cpy:28`, `app/cpy/COADM02Y.cpy:29`), so once this wave is live the estate can be
switched program by program behind it. That is why the wave is worth doing early even though it
holds the most-called programs (fan-in 12 for `COSGN00C` and `COMEN01C`, `analysis`, field `fan_in`).

Facade dependency, stated plainly: until waves 5, 6 and 7 move, this wave must route to legacy
programs and carry the COMMAREA back stack (see the last row of the computed call table in
`02-coupling.md`). Confidence stays medium because six of the seven units make computed calls that I
bounded by reading, not by proof. `COACTVWC` prints the SSN and FICO score
(`app/cbl/COACTVWC.cbl:497`), so access rules must be carried over. `COSGN00C` compares a clear text
password (`app/cbl/COSGN00C.cbl:223`); porting it faithfully carries that over, so record the decision.

## Wave 4. Build tooling, GDG bases and demo jobs

Units: `job:CBLDBMS`, `job:CICCMP`, `job:CNJBATMP`, `job:DEFGDGD`, `job:INTRDRJ1`, `job:INTRDRJ2`,
`proc:BUILDBAT`, `proc:BUILDBMS`, `proc:BUILDONL`. Blast radius low, confidence medium.

Nothing here is business behavior. Three compile jobs and three build procs are replaced by the
target build pipeline. `DEFGDGD` defines three GDG bases (`app/jcl/DEFGDGD.jcl:27`). The two internal
reader jobs are a demonstration that one job submits another (`app/jcl/INTRDRJ1.JCL:17`). It is a
chore wave that unblocks nothing, and the plan should delete it rather than port it.

## Wave 5. The nightly batch cycle

Blast radius high, confidence medium. It holds the three must-not-break items and 14 of the
24 high-high units in the tree (`modernization-assessment/risks.json:1`).

| Must-not-break item | Units in this wave | Evidence |
|---|---|---|
| Daily transaction posting | `job:POSTTRAN`, `CBTRN02C`, `job:TRANBKP`, `job:COMBTRAN`, `job:TRANIDX`, `job:DALYREJS`, `job:CLOSEFIL`, `job:OPENFIL` | `app/jcl/POSTTRAN.jcl:23` |
| Account and card master refresh | `job:ACCTFILE`, `job:CARDFILE`, and by the same pattern `job:XREFFILE`, `job:CUSTFILE` | `app/jcl/ACCTFILE.jcl:25`, `app/jcl/CARDFILE.jcl:36` |
| Transaction report | `job:TRANREPT`, `proc:TRANREPT`, `proc:REPROC`, `CBTRN03C`, `CORPT00C`, `CSUTLDTC`, `job:REPTFILE` | `app/jcl/TRANREPT.jcl:59`, `app/cbl/CORPT00C.cbl:94` |

The rest is interest (`CBACT04C`, `job:INTCALC`), statements (`CBSTM03A`, `CBSTM03B`,
`job:CREASTMT`, `job:TXT2PDF1`), the export (`CBEXPORT`, `job:CBEXPORT`), the other reference reloads,
the GDG definers, two sample test jobs, the timer, and the 17 scheduler artifacts (13 Control-M jobs
and 4 wrapper scripts).

### Port order inside the wave

This is a suggestion I can defend from the edges. The wave is one delivery for rollback purposes but
not one work package.

1. Build the order first. Capture one night of the legacy cycle from the job logs and the GDG
   generations, and turn the order in `scripts/run_full_batch.sh:13` into a dependency graph with the
   generation numbers made explicit. Decide which of the four sources of order is real before any
   code moves.
2. Reference reloads: `TRANTYPE`, `TRANCATG`, `DISCGRP`, `XREFFILE`, `CUSTFILE`, `DUSRSECJ`, then
   `ACCTFILE`, `CARDFILE` and `TCATBALF`. These are load procedures, not logic. The two must-not-break
   refresh jobs go last in this group because they replace the masters posting updates.
3. Read-only consumers in shadow, one night at a time and diffed against the legacy output: the
   report (`CBTRN03C`, `TRANREPT`, `CORPT00C`), statements (`CBSTM03A` and `CBSTM03B`, then
   `TXT2PDF1`), `PRTCATBL` and `CBEXPORT`. They own no master. The report's write of a new BKUP
   generation is a side effect and goes in the Deviation Register.
4. The posting cycle last, in parallel run on the same daily input: `TRANBKP`, `POSTTRAN`
   (`CBTRN02C`), `INTCALC` (`CBACT04C`), `COMBTRAN`, `TRANIDX`, wrapped by `CLOSEFIL` and `OPENFIL`.
5. Replace the 17 scheduler artifacts and the wrappers with one definition, after one order is chosen.
6. Not ported: `WAITSTEP` and `COBSWAIT` (a 36 second timer), `REPRTEST` and `SORTTEST` (samples that
   write production GDGs). See `do_not_port` in `modernization-assessment/risks.json:1`.

### The interface I would hold behind a facade

Waves 5 and 6 write the same two masters. If posting moves to a new store in wave 5 while the
online writers still write VSAM in wave 6, two systems own the account and transaction masters for
the length of wave 6. My answer: keep the legacy VSAM as the owner through the end of wave 6 and put
a record-level data service in front of `ACCTDATA` and `TRANSACT`, used by new batch and by the
legacy online region alike. The data cutover is then the last step of wave 6, not of wave 5. If the
client cannot accept that, waves 5 and 6 merge and the estimate in `04-estimate.md` changes.

The CA-7 trigger from `CBPAUP0J` to `POSTTRAN` (`app/scheduler/CardDemo.ca7:70`) is also an
interface: the new scheduler must emit or emulate that completion event until wave 7 retires the
IMS job, if the trigger is real.

## Wave 6. Online writers of the masters

Units: `COACTUPC`, `COCRDUPC`, `COCRDLIC`, `COBIL00C`, `COTRN02C`, `COUSR00C`, `COUSR01C`,
`COUSR02C`, `COUSR03C`. Blast radius high, confidence medium.

`COACTUPC` is 3,368 lines with 43 REDEFINES and is the largest program in the tree
(`app/cbl/COACTUPC.cbl:119`). `COBIL00C` and `COTRN02C` choose the next transaction id by reading the
highest key (`app/cbl/COBIL00C.cbl:212`, `app/cbl/COTRN02C.cbl:444`). `COBIL00C` moves a ten digit
balance into a nine digit amount (`app/cbl/COBIL00C.cbl:224`). Every unit makes a computed call. The
wave unblocks retiring the CICS files and the close and open jobs in the nightly cycle. Four of its
nine units are high-high, so the harness from wave 5 must be proven before it starts.

## Wave 7. Authorization, IMS, DB2 and MQ subsystem

Units: 13 programs, 10 jobs, `proc:BLDCIDB2` and 2 scheduler artifacts. Blast radius high,
confidence low.

It holds the card authorization decision program with packed decimal and MQ
(`app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:62`), the IMS purge that CA-7 chains before
posting (`app/app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl:25`), and the DB2 transaction type
maintenance. Confidence is low because the IMS DBD and PSB files, the DB2 DDL and DCLGEN files and
the `.ctl` members were not read, and MQ is not modeled. The three IMS load and unload programs and
their jobs are data movement tools and are replaced by migration tooling, not ported. Reassess this
wave after those files are read. It unblocks decommissioning IMS, DB2 and MQ.

## Scores on thin evidence

39 of the 99 scored units carry confidence low in `modernization-assessment/risks.json:1`, 52 carry medium and 8 carry high. The low ones are units I scored from the graph, the size and a search for risky constructs, without reading the whole program. The ones that matter for sequencing are `COACTUPC`, `COCRDUPC` and `COACTVWC` in waves 3 and 6, and every unit in wave 7. A wrong score there moves a unit between quadrants, so read those programs before the wave is committed.

## Not placed

| Unit | Reason | Evidence |
|---|---|---|
| CBTRN01C | Not reached by any static edge, no JCL runs it, and 28 computed calls could target it. It reads only. Confirm with the client whether it is a retired copy of the posting program | `app/cbl/CBTRN01C.cbl:154`, `app/cbl/COACTUPC.cbl:956` |
