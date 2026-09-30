# 04 Estimate

These are ranges in engineer-weeks, per wave, for a team that can read COBOL and JCL and has Claude Code doing the mechanical port. They are not a quote. Every number is `inference`. The counts they rest on are in `modernization-assessment/waves.json` and `modernization-assessment/graph.json`.

## Method

For each wave I added three parts and then widened the sum by about 30 percent each way.

1. **Port work.** Program lines divided by an assumed rate for the difficulty band in `modernization-assessment/risks.json`. The rates are my assumptions, with Claude Code doing the transliteration against a working harness: about 400 lines a week for difficulty 1 or 2, about 200 for 3, about 120 for 4 or 5. A JCL job that is an IDCAMS or SDSF step counts as a quarter of a week. Lines are the extractor's own count (`analysis`, no `cloc`).
2. **Boundary work.** Each contract, data or temporal edge that crosses the wave line needs an adapter or a facade and a test. I counted them from `modernization-assessment/02a-edge-tables.md` and priced each at about half a week.
3. **Oracle and harness.** A fixed amount per wave, more when no oracle exists. See `modernization-assessment/06-test-strategy.md`.

Not in these numbers: data migration itself, redesign of the 21 BMS screens as a new front end beyond a like-for-like port, environment and CI build, and any parallel-run infrastructure. Those are separate lines in a plan.

## Per wave

| Wave | Units | Program lines | Estimate (engineer-weeks) | What drives it | Confidence | Evidence |
|---|---|---|---|---|---|---|
| 1 Operations utilities | 14 | 0 (8 jobs, 281 JCL lines) | 6 to 10 | First harness and CI, scheduler integration, the hard-coded CICS region name | medium | `app/jcl/CLOSEFIL.jcl:26` |
| 2 Read-only batch extracts | 15 | 1,097 | 6 to 10 | Two assembler routines to reimplement, the first COBOL port | medium | `app/cbl/CBACT01C.cbl:231` |
| 3 Sign-on, menus and read-only screens | 7 | 2,679 | 14 to 24 | Seven BMS screens, the menu facade to legacy, a shared data path | medium | `app/cbl/COMEN01C.cbl:156` |
| 4 Build and file-transfer support | 11 | 0 (8 jobs, 3 procs) | 2 to 4 | Mostly retirement, a few GDG definitions | medium | `app/jcl/DEFGDGD.jcl:27` |
| 5 Nightly batch cycle | 42 | 3,670 | 34 to 56 | CBSTM03A with ALTER and control-block walks, CBTRN02C, CBACT04C, CBTRN03C, 24 jobs, GDG semantics, parallel run | medium | `app/cbl/CBSTM03A.CBL:300` |
| 6 Online writers | 9 | 7,972 | 35 to 60 | COACTUPC at 3,368 lines, COCRDUPC, two-file updates, key generation | medium | `app/cbl/COACTUPC.cbl:4100` |
| 7 Authorization, DB2 reference and MQ services | 25 | 7,071 | 45 to 80 | IMS, DB2 and MQ objects, real-time decision logic, unparsed definitions | low | `app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:668` |
| Total | 123 | 22,489 | 142 to 244 | | low | `inference` |

The total is wide on purpose. Its width is mostly waves 5 to 7.

## The assumptions the range is most sensitive to

These are stated so a client engineer can prove them wrong.

1. **Assumes the client can supply archived generations of TRANSACT.BKUP, DALYREJS and TRANREPT that cover at least one month-end.** If none exist, wave 5 has only characterization tests written from source, and its verification cost roughly doubles, which adds 12 to 20 engineer-weeks. The generation group is defined with a limit of five (`app/jcl/DEFGDGB.jcl:26`), so only five recent generations can exist on the system, and older ones would have to come from an archive.
2. **Assumes the production order of the daily cycle is the one in the shell wrapper.** If the CA-7 chain is the real order (`app/scheduler/CardDemo.ca7:70`), which runs POSTTRAN straight after CBPAUP0J and skips the refresh and backup jobs, wave 5 must test both orders and grows by about a third, 11 to 19 engineer-weeks.
3. **Assumes the IMS, DB2 and MQ objects in wave 7 can be replaced by target-platform services without reproducing IMS behavior.** If the client requires hierarchical segment access and checkpoint restart to behave as they do now (`app/app-authorization-ims-db2-mq/cbl/CBPAUP0C.cbl:199`), wave 7 roughly doubles.
4. **Assumes the 28 computed calls resolve as set out in `modernization-assessment/02-coupling.md`.** If a program name reaches those XCTLs from a table or a queue outside the tree, waves 3 and 6 need a new cut, and the estimate for both grows by about a quarter.

## What moves the estimate here, in order of weight

- **Edges across the boundary.** Wave 5 has the most: the account master alone has four writers and eleven readers (`analysis.data_hubs`), and the transaction master history depends on one generation group that three routes write.
- **Behavioral oracle.** None is in the tree. The sample data under `app/data/ASCII/dailytran.txt:1` seeds a demo, not a production replay. Availability of archived output is the largest unknown.
- **God modules.** The extractor names three, but two are small (COTRN00C and COTRN01C have a fan-in of 1). COPAUS0C is the real one and is in wave 7. See `modernization-assessment/02-coupling.md`.
- **Logic in the database.** DB2 holds the transaction-type table and the authorization fraud table, and IMS holds pending authorizations. The DDL, DCLGEN and DBD files are not parsed (`modernization-assessment/00-summary.md`), so wave 7 cannot be sized with confidence.
- **People who can read the source.** Not known. If the client team cannot read COBOL and JCL, every wave grows, most in waves 5 and 7. This is a question for the client.

## Where Claude Code can do the mechanical port and where it cannot

| Area | Judgment | Evidence |
|---|---|---|
| IDCAMS, SDSF and sort jobs turned into workflow steps | Strong. Mechanical, with a run comparison against the job output | `app/jcl/ACCTFILE.jcl:25` |
| Flat readers such as CBACT02C, CBACT03C, CBCUS01C | Strong. Read a keyed file and display | `app/cbl/CBACT02C.cbl:29` |
| Record layouts from copybooks | Strong. Field by field, with decimal types | `app/cpy/CVACT01Y.cpy:7` |
| Simple BMS screens with one file read | Strong for logic, and the screen design is a separate decision | `app/cbl/COTRN01C.cbl:205` |
| CBTRN02C posting and CBACT04C interest | Medium. The arithmetic transliterates. The intent behind reason codes, the truncating divide, and the mixed field widths must be settled by people | `app/cbl/CBTRN02C.cbl:403`, `app/cbl/CBACT04C.cbl:464` |
| CBTRN03C report totals | Weak until the intended totals are decided. The end-of-file branch and NEXT SENTENCE change what a port should reproduce | `app/cbl/CBTRN03C.cbl:177`, `app/cbl/CBTRN03C.cbl:200` |
| CBSTM03A statements | Weak. ALTER and a walk over control blocks describe mechanism, not intent. Write it from the statement output, not from the source | `app/cbl/CBSTM03A.CBL:300`, `app/cbl/CBSTM03A.CBL:266` |
| COACTUPC and COCRDUPC | Medium to weak. The volume of validation is large and the rules are undocumented | `app/cbl/COACTUPC.cbl:4100` |
| COPAUA0C and the IMS programs | Weak. Behavior lives in IMS and MQ objects that are not in the tree | `app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:668` |
| Assembler routines COBDATFT and MVSWAIT | Small, but no tool here reads them. Reimplement from the source and test | `app/asm/COBDATFT.asm:1` |
