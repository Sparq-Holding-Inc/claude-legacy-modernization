# 04 Estimate

This is an estimate by wave, given as a range, with the assumptions it is most sensitive to. It is inference throughout. There is no velocity data for this team, no telemetry, and no client staffing, so I rank waves against each other with more confidence than I state absolute numbers.

## Method

- Unit: engineer weeks, meaning one engineer for one week. A refactor to services in a new language is assumed. Client acceptance testing, infrastructure and platform procurement are not counted.
- Team assumed: four engineers, at least one who can read COBOL, JCL and VSAM, and a behavioral-equivalence harness that gets built during wave 2 (see `modernization-assessment/06-test-strategy.md`).
- What moves the estimate, in the order I weighted it: the number and kind of edges that cross the wave boundary (not lines of code), whether an oracle exists, god modules and large programs inside the wave, business logic in databases, and whether anyone on the team reads COBOL. Lines of code are shown only as color.
- The boundary edges I counted are the data hubs, the contract edges and the scheduler edges in `modernization-assessment/02-coupling.md`. Wave 5 has by far the most, which is why it is the largest even though it has fewer lines than wave 6.

## Ranges by wave

| Wave | Range (engineer weeks) | Main driver | Confidence | Evidence |
|---|---|---|---|---|
| 1 Setup utilities and fences | 1 to 3 | Retiring jobs and rotating a credential. No logic. | medium | `app/jcl/FTPJCL.JCL:33` |
| 2 Read only batch | 4 to 8 | Four record layouts, an assembler date routine, one broken job. | medium | `app/cbl/CBACT01C.cbl:231`, `app/cbl/CBIMPORT.cbl:63` |
| 3 Sign on, menus, read screens | 8 to 16 | Router facade, screen replay oracle, read path over legacy masters. | low | `app/cpy/COMEN02Y.cpy:21` |
| 4 Build and demo jobs | 1 to 3 | Retirement. TXT2PDF1 depends on a tool not in the tree. | medium | `app/jcl/TXT2PDF1.JCL:31` |
| 5 Batch that writes the masters | 24 to 52 | Data facade, three must-not-break items, 51 units, scheduler cut over. | low | `app/cbl/CBTRN02C.cbl:256`, `app/jcl/TRANBKP.jcl:40` |
| 6 Online writers | 12 to 26 | COACTUPC alone is about 4,200 lines with 43 REDEFINES, and the transaction id scheme must change. | low | `app/cbl/COACTUPC.cbl:3888`, `app/cbl/COBIL00C.cbl:212` |
| 7 IMS, DB2 and MQ | 20 to 50 | Unread subsystems and an undecided target. The range is a placeholder, not an estimate. | low | inference |
| Harness and oracle, across waves | 8 to 16 | Capture, normalization spec, replay runner, deviation register. | medium | inference |
| Total | 78 to 174 | | low | inference |

Read the total as "roughly a person-year and a half to about three and a third person-years, with wave 5 and wave 7 deciding which end". If wave 7 is descoped or kept as a mainframe island, the total drops to about 58 to 124.

## Assumptions the ranges are most sensitive to

Each is stated so that the client's engineers can say it is false.

| Wave | Assumption | If it is false | Confidence | Evidence |
|---|---|---|---|---|
| 2 | The account, card, cross reference and customer records are zoned decimal with no packed fields, so the four copybooks port with a plain decimal type. | If production files differ from the copybooks (packed fields, other layouts), wave 2 grows by half and every later wave inherits the error. | medium | `app/cpy/CVACT01Y.cpy:7`, `app/cpy/CVCUS01Y.cpy:17` |
| 2 | The assembler routine COBDATFT is a plain date formatter. | If it uses installation tables, add one to two weeks. | low | `app/cbl/CBACT01C.cbl:231` |
| 3 | The 17 program names in the two menu tables are the whole routing set, and COMMAREA returns only name the calling program. | If the COMMAREA can carry other names, the router facade needs a real routing table and wave 3 roughly doubles. | medium | `app/cpy/COMEN02Y.cpy:28`, `app/cpy/COADM02Y.cpy:29` |
| 5 | The run order in `scripts/run_full_batch.sh` and the wrapper scripts is the production order. | If CA-7 is production, POSTTRAN starts behind the IMS purge job CBPAUP0J, and wave 5 needs a bridge to wave 7 that adds four to eight weeks. | medium | `scripts/run_full_batch.sh:47`, `app/scheduler/CardDemo.ca7:70` |
| 5 | Nothing outside this tree reads the account, transaction and category balance masters. | If extracts, reports or partner feeds also read them, the data facade needs their layouts too, and wave 5 grows by about a third. | low | inference |
| 5 | A parallel run through at least one month end, and ideally a year end, is possible. | If it is not, wave 5 needs a synthetic oracle built from source, which is the weakest kind, and adds six to ten weeks. | low | inference |
| 5 | CBSTM03A is rewritten from what it does, not transliterated. | A transliteration that keeps the ALTER and control block code adds work and risk, and wave 5 grows by four to eight weeks. | medium | `app/cbl/CBSTM03A.CBL:300`, `app/cbl/CBSTM03A.CBL:266` |
| 6 | The wave 5 data facade exists and both stacks write through it. | If the facade does not exist, waves 5 and 6 cannot run apart, and the two roughly merge. | medium | `app/cbl/COBIL00C.cbl:512`, `app/cbl/CBTRN02C.cbl:34` |
| 7 | The DB2, IMS and MQ objects are documented elsewhere and the target is chosen. | The range is only a placeholder. Without them, wave 7 is not estimable. | low | inference |

The sentence I would defend in front of a committee is this: wave 5 roughly doubles if there is no way to run legacy and new side by side on real month end input, because the harness is then the work and the port is the easy part.

## Where Claude Code can do the mechanical port, and where it cannot

| Kind of work | Units | Can Claude Code do it | Confidence | Evidence |
|---|---|---|---|---|
| Transliterate plain read and print programs and IDCAMS reloads | CBACT02C, CBACT03C, CBCUS01C, ACCTFILE, TCATBALF, TRANTYPE, TRANCATG | Yes, with a golden master test harness | high | `app/cbl/CBCUS01C.cbl:78`, `app/jcl/ACCTFILE.jcl:61` |
| Generate test cases from copybooks and sample data | All waves | Yes, and label the coverage provisional | high | `app/data/ASCII/dailytran.txt:1` |
| Port record I/O and arithmetic in the posting program | CBTRN02C | Partly. The port is easy, and the reject rules are not: two checks can both fire and the last one wins, and a failed balance rewrite is not written to the reject file. Someone must decide which is intended. | medium | `app/cbl/CBTRN02C.cbl:410`, `app/cbl/CBTRN02C.cbl:417`, `app/cbl/CBTRN02C.cbl:554` |
| Reproduce the interest arithmetic | CBACT04C | Partly. It can match the truncation exactly. It cannot tell whether truncation, the empty fee routine, or the fixed run date is intended. | medium | `app/cbl/CBACT04C.cbl:464`, `app/cbl/CBACT04C.cbl:518` |
| Rewrite statements | CBSTM03A | No, not by transliteration. ALTER, GO TO and control block walking have no target equivalent. It can write the new version from a spec and test it against the golden statements. | medium | `app/cbl/CBSTM03A.CBL:300` |
| Design the router facade and the data access facade | Waves 3, 5, 6 | No. These are design decisions with consequences for every later wave. It can draft and test them. | medium | inference |
| Decide the meaning of "master refresh" and the fate of the reload jobs | ACCTFILE, CARDFILE | No. That is the client's answer, not a source fact. | high | `scripts/remote_refresh.sh:16` |
| IMS, DB2 and MQ semantics | Wave 7 | No, not from this tree. The objects are unread. | high | `app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:262` |
