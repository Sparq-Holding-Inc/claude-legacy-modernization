# 04 Estimate

Unit of effort: one engineer-week, with Claude Code doing the mechanical port and a person reviewing and verifying. These are ranges, and none of them is calibrated against this team's real velocity. Wave 1 is where the calibration happens. Replace these numbers with measured ones after it.

## Method

1. Port effort per unit comes from its port difficulty score in `risks.json`. Programs, in engineer-days: score 1 is 0.5 to 1, score 2 is 2 to 4, score 3 is 5 to 9, score 4 is 10 to 18, score 5 is 20 to 40. JCL jobs are smaller: 0.5 to 1, 1 to 2, 2 to 4, 4 to 8, 8 to 12.
2. Verification effort is the port effort times a factor set by blast radius: 0.75 for scores 1 and 2, 1.25 for score 3, 1.75 for scores 4 and 5. Verification is the normalization spec, the targeted boundary cases, the parallel or replay run and the deviation register. It outweighs the port on anything that writes a master.
3. Procs and scheduler entries are not scored. Each gets 0.5 to 1 engineer-day.
4. Each wave adds fixed overhead for what it has to build once: the harness in wave 1, the routing and online test driver in wave 3, the report diff and queue replacement in wave 4, the facade and cutover in wave 6, the IMS and MQ toolchain in wave 7.

The method follows the weight order the skill gives: coupling edges crossing the wave boundary first, then oracle availability, god modules, logic held outside the application, and whether the team can read COBOL and JCL. Lines of code do not enter it.

## Per wave

| Wave | Units scored | Port (days) | Verification (days) | Overhead (days) | Range (engineer-weeks) | Evidence |
|---|---|---|---|---|---|---|
| 1 Read-only master readers | 6 | 3 to 6 | 2 to 4 | 20 to 35 | 5 to 9 | inference from `risks.json`, driver `app/cbl/CBACT02C.cbl:29` |
| 2 Hard-pattern batch utilities | 6 | 18 to 32 | 13 to 24 | 5 to 10 | 7 to 13 | inference from `risks.json`, driver `app/cbl/CBACT01C.cbl:231` |
| 3 Administration front door | 18 | 50 to 96 | 50 to 97 | 8 to 15 | 22 to 42 | inference from `risks.json`, driver `app/cbl/COSGN00C.cbl:223` |
| 4 Read-only inquiry and the transaction report | 9 plus 2 procs | 37 to 68 | 34 to 62 | 11 to 22 | 16 to 30 | inference from `risks.json`, driver `app/cbl/CBTRN03C.cbl:198` |
| 5 Account statements | 3 | 27 to 53 | 34 to 66 | 5 to 10 | 13 to 26 | inference from `risks.json`, driver `app/cbl/CBSTM03A.CBL:300` |
| 6 Money core | 23 plus 19 scheduler entries | 80 to 151 | 132 to 251 | 50 to 99 | 52 to 100 | inference from `risks.json`, driver `app/cbl/COACTUPC.cbl:418` |
| 7 IMS and MQ authorization and MQ services | 15 | 125 to 233 | 123 to 232 | 20 to 40 | 54 to 101 | inference from `risks.json`, driver `app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:35` |
| Total | 101 | | | | 169 to 321 | inference |

Wave 6 carries about a third of the total on 6 of the 44 programs. That is the right shape. It is where the writers, the destructive reload jobs and the ordering all sit. Wave 7 carries another third on 10 programs, which is why the scope decision on it matters more than any other.

Raw effort is not elapsed time. At four engineers the total is 42 to 80 calendar weeks before sequencing losses. Waves 1 and 2 can overlap, and wave 3 can start once wave 1's harness runs.

## The assumptions the range is most sensitive to

Each is stated so it can be checked and found wrong.

1. Assumes the six writers in wave 6 can sit behind one account and transaction access facade and cut over at one switch. If they must cut over one at a time with dual writes to the old and new stores, wave 6 roughly doubles, to about 104 to 200 engineer-weeks. Evidence for the assumption: four programs write ACCTDATA and three write TRANSACT, all through the same copybook layouts (`app/cbl/CBACT04C.cbl:356`, `app/cbl/COBIL00C.cbl:512`).
2. Assumes the client can supply at least 13 months of daily posting input files with the masters, rejects and report generations they produced, including a month end and a year end. If only the 300 sample records in `app/data/ASCII/dailytran.txt:1` exist, verification factors rise from 1.75 to 2.5 for blast scores 4 and 5, wave 6 rises from 52 to 100 up to 63 to 121 engineer-weeks, and the total rises from 169 to 321 up to 200 to 379.
3. Assumes the IMS and MQ authorization module is in scope. If the client retires it, wave 7 drops out and the total falls by 54 to 101 engineer-weeks. That module is 10 programs, and the extractor cannot model it (`app/app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl:25`).
4. Assumes the menu keeps routing by program name while both stacks run, so an option can be re-pointed by editing one table entry. If the new stack needs a gateway in front of the CICS transactions, add 8 to 15 engineer-weeks, once, to wave 3 (`app/cpy/COMEN02Y.cpy:28`).
5. Assumes at least one engineer on the team reads COBOL, JCL and IDCAMS. If nobody does, every wave's verification grows, and I would add about 20 percent to the total.

## Where Claude Code does the mechanical port, and where it cannot

Strong, with a harness:

- Record layouts from copybooks into typed structures and codecs, including zoned decimal with trailing sign overpunch, which is how the sample data is stored (`app/data/ASCII/dailytran.txt:1`). Waves 1 and 2.
- Sequential readers, sorters and report writers: CBACT02C, CBACT03C, CBCUS01C, CBEXPORT, CBIMPORT.
- IDCAMS delete, define and REPRO jobs into loaders (`app/jcl/ACCTFILE.jcl:25`).
- Menu tables and screen maps into a router and view definitions (`app/cpy/COMEN02Y.cpy:28`).
- Characterization test drafts and deviation register drafts from the source.

Weak. It infers what the code says, not what the business meant:

- The reject reason logic in CBTRN02C, where the second failure overwrites the first and a failed account rewrite still writes the transaction (`app/cbl/CBTRN02C.cbl:407`, `app/cbl/CBTRN02C.cbl:554`).
- The control flow of CBTRN03C, where NEXT SENTENCE ends the read loop (`app/cbl/CBTRN03C.cbl:177`).
- The ALTER driven state machine and the control block walk in CBSTM03A (`app/cbl/CBSTM03A.CBL:300`, `app/cbl/CBSTM03A.CBL:266`). These have no clean target. They are rewritten from what the job produces.
- Whether the private account update layout in COACTUPC is a defect or an intended behavior (`app/cbl/COACTUPC.cbl:418`).
- Which of the three schedules is the production order (`app/scheduler/CardDemo.ca7:70`, `app/scheduler/CardDemo.controlm:8`, `scripts/run_posting.sh:26`).
- Language Environment date service semantics behind CSUTLDTC, including the message number CORPT00C tolerates (`app/cbl/CSUTLDTC.cbl:116`, `app/cbl/CORPT00C.cbl:399`).
- Anything IMS or MQ without the runtime to observe (`app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:35`).

## What would make this estimate wrong first

Wave 1 will show the real cost of the harness and the real velocity per program. If wave 1 takes more than 9 engineer-weeks, scale every wave's overhead and verification up by the same ratio and re-issue this file.
