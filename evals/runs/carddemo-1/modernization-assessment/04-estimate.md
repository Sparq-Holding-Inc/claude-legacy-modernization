# 04 Estimate

Every number here is inference. It is a range in engineer weeks (EW), per wave, and it is not a quote. The method is stated so the client's engineers can argue with it. Nothing in the tree gives a velocity, a team, or a production data volume. The ranges assume Claude Code does the mechanical port inside a working equivalence harness, and that the team has someone who can read COBOL and JCL.

## Method

For each wave I add four parts, then widen the range where confidence is low.

1. **Port.** Program lines from `graph.json`, at a rate that depends on the kind of code. I use about 1,500 to 3,000 lines per EW for plain file I/O, 400 to 800 for computation dense or screen code with maps, and 200 to 400 for DB2, IMS or MQ code, all with a harness in place.
2. **Harness.** The oracle, the normalization spec and the diff tool. It is built once in wave 2 and extended in each later wave.
3. **Boundary work.** What the edges crossing the wave boundary cost. I count them from the plan (below). This weighs more than lines.
4. **Cutover and rollback.** The switch, the parallel run, and the way back.

Edges that cross each wave's boundary, counted from `graph.json` and `modernization-assessment/waves.json` (call, contract and temporal edges with one end in the wave and the other in another wave):

| Wave | Call | Contract | Temporal | Total | Evidence |
|---|---|---|---|---|---|
| 1 | 0 | 0 | 0 | 0 | inference: counted from the plan |
| 2 | 0 | 7 | 0 | 7 | inference: counted from the plan |
| 3 | 22 | 14 | 0 | 36 | inference: counted from the plan |
| 4 | 0 | 0 | 0 | 0 | inference: counted from the plan |
| 5 | 4 | 26 | 1 | 31 | inference: counted from the plan |
| 6 | 18 | 33 | 0 | 51 | inference: counted from the plan |
| 7 | 4 | 12 | 1 | 17 | inference: counted from the plan |

Wave 6 has the most crossing edges, and wave 3 has 22 call edges that come almost entirely from the online writers, which is why the router is the main cost of wave 3.

## Per wave

| Wave | Range (EW) | Basis | Confidence | Evidence |
|---|---|---|---|---|
| 1. Environment and utility jobs | 3 to 6 | Six small jobs (257 lines of JCL). Most of the work is building the target pipeline, secrets handling, and the scheduler skeleton. Rotating the FTP credential is included. | medium | `app/jcl/FTPJCL.JCL:33`, inference for the rest |
| 2. Read-only listings and import | 8 to 15 | 1,084 lines of programs and 5 jobs. Port 2 to 3. Harness v1 4 to 8. Read access to the legacy masters or a snapshot 2 to 4. | medium | `app/cbl/CBACT01C.cbl:231`, inference for the rest |
| 3. Read-only screens and menu spine | 15 to 27 | 2,679 lines of programs and about 1,700 lines of BMS maps. Port 6 to 10. The router that hands the COMMAREA to mainframe programs 6 to 12. Screen capture tests 3 to 5. | medium | `app/cbl/COMEN01C.cbl:156`, `app/cpy/COMEN02Y.cpy:28` |
| 4. Build and generation plumbing | 1 to 3 | Retirement, plus one retention decision. | medium | `app/jcl/DEFGDGB.jcl:24` |
| 5. Nightly batch core | 30 to 50 | 3,683 lines of programs, 28 jobs, 2 procs, 4 wrappers and 13 scheduler jobs. Port about 10 to 15, of which CBSTM03A is 3 to 5. Job conversion 6 to 10. Scheduler and wrapper replacement 3 to 6. Parallel run and report oracle 8 to 14. Cutover and rollback 3 to 5. | medium | `app/cbl/CBTRN02C.cbl:256`, `app/jcl/TRANBKP.jcl:37` |
| 6. Online writers | 28 to 49 | 7,972 lines of programs (COACTUPC alone is 3,368) and about 2,000 lines of BMS maps. Port 16 to 27. Strangling behind the router 6 to 10. Screen capture tests 6 to 12. | low | `app/cbl/COACTUPC.cbl:4100` |
| 7. Subsystems | 26 to 55 | 7,071 lines of programs. Port 18 to 35. Target stores and queues 8 to 20. The DDL, DBD and PSB files are not read, so the range is wide. | low | `app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:874` |
| All waves | 111 to 205 | The sum of the ranges. The waves are not fully sequential, so calendar time is shorter than the sum divided by team size only if the router and harness are done first. | low | inference |

## Assumptions the ranges are most sensitive to

Each is written so it can be proven false.

1. **Wave 5 assumes the ten refresh jobs are a demo or test reset, not a production step.** If they run in production before every posting, as `scripts/run_posting.sh:17` suggests, the account master is rebuilt from a flat file each cycle and wave 5 gains a data lineage task. That adds roughly 8 EW, and it changes what the harness compares.
2. **Wave 5 assumes an archived TRANREPT exists for at least one month end.** The catalog listing in the tree shows the report generation group at LIMIT 5, with five generations (`app/catlg/LISTCAT.txt:1535`, `app/catlg/LISTCAT.txt:1537`). Two jobs define it with different limits (`app/jcl/DEFGDGB.jcl:36`, `app/jcl/REPTFILE.jcl:27`). If nothing is archived, the report oracle is the sample data in the tree (300 daily transactions at `app/data/ASCII/dailytran.txt:1`), the oracle is characterization only, and the high end of wave 5 rises by about 30 percent.
3. **Wave 5 assumes CBSTM03A can be re-implemented from its output.** The control block walk only displays DD names (`app/cbl/CBSTM03A.CBL:266`, `app/cbl/CBSTM03A.CBL:276`). If the statement HTML and text must match byte for byte, add 3 EW.
4. **Wave 3 assumes the router can pass the COMMAREA unchanged.** It is one copybook (`app/cpy/COCOM01Y.cpy:1`). If mainframe programs need a translated layout, add 6 to 10 EW to wave 3 and the same to wave 6.
5. **Wave 2 assumes the four listing programs share one I/O skeleton.** CBACT02C, CBACT03C and CBCUS01C are about 130 lines with the same status and abend paragraphs (`app/cbl/CBACT02C.cbl:54`, `app/cbl/CBACT03C.cbl:54`, `app/cbl/CBCUS01C.cbl:54`). If the target needs different error handling per program, wave 2 grows by half.
6. **Wave 6 assumes COACTUPC's 3,368 lines are mostly table driven field edits.** I did not read the whole program. If the edits are irregular, that one unit is 8 to 12 EW.
7. **Wave 7 assumes IMS is replaced, not emulated.** With an emulator, take off about 10 EW and add a licence and a vendor dependency.

## Where Claude Code can do the mechanical port, and where it cannot

| Work | Claude Code | Why | Evidence |
|---|---|---|---|
| Record layouts from copybooks into typed schemas, including zoned and packed decimal | Strong, with a harness | The layouts are explicit. The account, transaction and card layouts are short. | `app/cpy/CVACT01Y.cpy:5`, `app/cpy/CVTRA05Y.cpy:5` |
| File I/O programs with no rules (the four listings, CBEXPORT, CBIMPORT) | Strong | Read, move, write. | `app/cbl/CBACT02C.cbl:70`, `app/cbl/CBEXPORT.cbl:271` |
| IDCAMS delete, define and REPRO jobs into load steps | Strong | The intent is in the card. | `app/jcl/ACCTFILE.jcl:25` |
| Test harness, normalizer and diff tool | Strong | It is code with a written spec. | inference |
| Interest and posting arithmetic (CBACT04C, CBTRN02C) | Partial | The arithmetic ports. What to do about no ROUNDED, the fixed type and category codes, and the swallowed rewrite failure is a decision. | `app/cbl/CBACT04C.cbl:464`, `app/cbl/CBACT04C.cbl:482`, `app/cbl/CBTRN02C.cbl:554` |
| The transaction report's totals | Weak | The code may double count the last record, and the loop may stop early. Intent has to come from an archived report, not from the source. | `app/cbl/CBTRN03C.cbl:177`, `app/cbl/CBTRN03C.cbl:198` |
| Statements (CBSTM03A) | Weak | ALTER, GO TO and control block addressing. Re-derive from the output. | `app/cbl/CBSTM03A.CBL:300` |
| Screen programs (COACTUPC, COCRDUPC) | Partial | Long edit chains. The screen behavior needs recorded sessions. | `app/cbl/COACTUPC.cbl:4100` |
| Date validation (CSUTLDTC) | Partial | It depends on what CEEDAYS accepts, which needs a table of cases. | `app/cbl/CSUTLDTC.cbl:29` |
| Wrapper timing and job order | Weak | The order rests on sleeps and submit order. | `scripts/run_posting.sh:14` |
| DB2, IMS and MQ programs | Weak | The DDL, DBD, PSB and control members are not read, and semantics live in them. | inference |
| Anything in an unread file (assembler, `.ctl`, `.ddl`, CA-7) | Not without the file being read | The extractor did not read it. | `app/asm/COBDATFT.asm:14` |

## What would change this estimate most

An answer to the questions in `00-summary.md` about telemetry, the archived reports, and whether the refresh jobs run in production. Those three swing wave 5 by more than any code fact.
