# 04 Estimate

These are ranges in engineer-weeks, per wave, for a refactor to services with Claude Code doing the mechanical port and a team reviewing and testing. They are not a quote. The number I would defend in a steering committee is the sensitivity list at the end, not the total.

## Method

Lines of code are a sanity check, not the driver. The estimate is driven, in rough order of weight, by:

1. Coupling edges that cross the wave boundary. I counted them from `graph.json` and the plan: call, contract and temporal edges with exactly one end in the wave, and datasets shared with another wave.
2. Whether a behavioral oracle exists. In this tree it is thin. There are seed data files and no archived outputs (see `06-test-strategy.md`).
3. God modules in the wave. The graph finds none. COACTUPC is a size outlier.
4. Business logic held outside the application: the reject and validation rules live in COBOL, the layout contracts live in IDCAMS and SORT cards, and the reference data lives in DB2.
5. Whether the team can read COBOL and JCL. I assume at least two engineers can.

Excluded: the target platform build, data cutover and freeze planning, UI redesign beyond a like-for-like conversion of the BMS maps, security review, performance work and any component that is not in the tree.

## Per wave

Lines are program lines from `graph.json` (analysis: node `loc`). The crossing counts are computed from the edges and the plan (analysis). Ranges are in engineer-weeks.

| Wave | Units | Program lines | Crossing edges (call, contract, temporal) | Shared datasets | Range | What sets it | Evidence |
|---|---|---|---|---|---|---|---|
| 1 | 17 | 0 (342 JCL) | 8, 0, 11 | 0 | 3 to 6 | Scheduler, GDG replacement, the CICS file bracket. Mostly configuration. | `app/jcl/CLOSEFIL.jcl:26`, `app/jcl/DEFGDGB.jcl:24` |
| 2 | 15 | 1,097 | 0, 7, 6 | 5 | 3 to 6 | Six small programs. The harness (print and compare) is built here and reused. CBACT01C needs the assembler routine replaced. | `app/cbl/CBACT01C.cbl:231` |
| 3 | 7 | 2,679 | 22, 14, 0 | 6 | 6 to 12 | Seven BMS screens, the COMMAREA and the router that sends XCTL to the right platform. Sign-on has to be equivalent, including plain-text password compare or its replacement. | `app/cbl/COSGN00C.cbl:223`, `app/cpy/COMEN02Y.cpy:21` |
| 4 | 29 (18 to port) | 0 (796 JCL) | 14, 0, 8 | 14 | 5 to 10 | Loaders and the record contracts in their IDCAMS cards. The data facade is designed here even though wave 5 leans on it. | `app/jcl/ACCTFILE.jcl:40`, `app/jcl/CARDFILE.jcl:85` |
| 5 | 23 | 3,670 | 22, 26, 10 | 14 | 14 to 26 | The must-not-break cycle: posting, interest, report, statements, and the transaction master lifecycle. Verification is most of the work. CBSTM03A uses ALTER. | `app/cbl/CBTRN02C.cbl:256`, `app/cbl/CBSTM03A.CBL:300` |
| 6 | 9 | 7,972 | 18, 33, 0 | 7 | 16 to 30 | COACTUPC alone is 3,368 lines with 43 REDEFINES and 51 GO TO. COCRDUPC (21 GO TO) and COCRDLIC (16 GO TO) are next. COBIL00C is small but writes both shared masters. | `app/cbl/COACTUPC.cbl:4066`, `app/cbl/COCRDUPC.cbl:251` |
| 7 | 23 | 7,071 | 4, 12, 1 | 4 | 20 to 45 | IMS, DB2 and MQ. I could not read the definitions. The low end assumes the authorization module can be strangled. | `app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:400` |
| Total | 123 | 22,489 | | | 67 to 135 | | analysis |

## Where Claude Code helps and where it does not

| Work | Claude Code does | A person must do | Evidence |
|---|---|---|---|
| Read and print programs (CBACT02C, CBACT03C, CBCUS01C), the READ jobs | The port. They are transliteration once a harness exists. | Approve the harness. | `app/cbl/CBACT02C.cbl:29` |
| IDCAMS loaders (ACCTFILE, CARDFILE, XREFFILE and the rest) | The port of the delete, define and load steps. | Decide what replaces KEYS, RECORDSIZE and the alternate index offsets. | `app/jcl/ACCTFILE.jcl:40`, `app/jcl/CARDFILE.jcl:85` |
| BMS maps and the screen programs in waves 3 and 6 | The like-for-like conversion of a fixed field list. | Decide the UI, the session model and what replaces the COMMAREA. | `app/cpy/COMEN02Y.cpy:21` |
| CBTRN02C, CBTRN03C, CBACT04C | The port line by line, once the oracle is fixed. | Decide every behavior that looks like a defect (see the deviation register). The rules are not written down anywhere: reject code precedence, the sign of the cycle debit, the last-record total. | `app/cbl/CBTRN02C.cbl:414`, `app/cbl/CBTRN03C.cbl:197` |
| CBSTM03A (ALTER and GO TO) | A port only if a test-first harness exists. It is weak at inferring the control flow from ALTER. | Write the characterization cases first. | `app/cbl/CBSTM03A.CBL:300` |
| COACTUPC | Transliteration in slices, behind a facade. | Decide what the lock, rewrite and rollback semantics should be on recoverable stores. | `app/cbl/COACTUPC.cbl:4100` |
| Scheduler chains and the trigger order | Translate the wrappers. | Decide which of the four orders is the real one. | `scripts/run_full_batch.sh:29`, `app/scheduler/CardDemo.ca7:70` |
| DB2, IMS and MQ | Little until someone reads the definitions. | Everything: the data model, the messaging contract, the authorization decision rules. | inference |

## What the range is most sensitive to

Each is a claim that can be checked and that moves a wave.

1. **One record-level data facade serves ACCTDATA, TRANSACT, TCATBALF, CARDXREF and CUSTDATA to both platforms.** Fourteen shared datasets cross the wave 4 and wave 5 boundary (analysis). If the client will not accept a shared store and wants each writer to own its data, waves 5 and 6 each roughly double, because ACCTDATA needs a synchronization design across four writers.
2. **The oracle is more than the seed data.** The tree holds 300 synthetic daily transactions and 50 records per master (`app/data/ASCII/dailytran.txt:1`) and no output from any run. If the client can supply a year of archived reports and one production daily file, wave 5 is at the low end. If not, wave 5 adds 6 to 10 weeks of characterization cases and every correctness claim stays provisional.
3. **The 28 computed XCTL sites all resolve to programs in the tree.** I bounded them to the CSD-defined online set (`02-coupling.md`). COCRDSEC is defined in the CSD with no source in the tree (`app/csd/CARDDEMO.CSD:211`). If it is one of several missing programs, wave 6 grows by their size, which I cannot see.
4. **The authorization module can be strangled, not rewritten.** COPAUA0C scores 5 and 5 (`app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:400`). If the IMS hierarchy has no relational equivalent, wave 7 roughly doubles.
5. **The client accepts the CA-7 trigger as a scheduler constraint.** CA-7 runs POSTTRAN after CBPAUP0J (`app/scheduler/CardDemo.ca7:70`). If the client wants posting independent of the IMS purge, add 2 to 4 weeks to wave 5 to re-cut and prove the trigger.
6. **The team has two or more engineers who read COBOL and JCL.** If it has none, review time rises 30 to 50 percent in every wave and Claude Code becomes the only reader of the source. That is a risk, not a plan.

## Reading the total

The total is the sum of the low ends and the sum of the high ends. Waves 5, 6 and 7 are about 75 percent of it, and wave 7 is the least certain. If I had to move one number I would ask for the archived report and daily file (item 2), because it decides wave 5, which holds two of the three must-not-break items.
