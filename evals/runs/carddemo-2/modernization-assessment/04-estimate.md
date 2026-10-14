# 04 Estimate

**Basis: engineer-weeks, shown two ways: conventional (no AI coding assistance) and AI-assisted (engineers using an AI coding agent, with human review). No `--delivery` flag was given, so no single headline figure is chosen.** This plugin carries no calibrated productivity data. Every rate and reduction below is a planning assumption, not a benchmark, and the team's measured velocity from wave 2 replaces it.

Target state is refactor. The system is small: 22,489 lines of COBOL in 44 programs (`modernization-assessment/01-inventory.md:20`), 55 JCL jobs and 62 copybooks (`modernization-assessment/graph.json:24`). Size is not what drives the estimate. The oracle, the shared files and the unread definitions are.

## Per wave

| Wave | Conventional (eng-weeks) | AI-assisted (eng-weeks) | What drives it | Confidence | Evidence |
|---|---|---|---|---|---|
| 1 Environment and definitions | 2 to 4 | 1 to 3 | Target provisioning, not code. AI does not shorten access requests. | medium | `app/jcl/CBADMCDJ.jcl:1` |
| 2 Read jobs | 3 to 5 | 2 to 3 | 1,084 lines, no computed calls, a first oracle | medium | `app/cbl/CBACT01C.cbl:29` |
| 3 Sign-on, menus, inquiry | 8 to 14 | 5 to 9 | 2,679 lines, BMS maps, 28 computed calls across the online set to resolve first | low | `app/cbl/COMEN01C.cbl:156` |
| 4 Build and GDG jobs | 1 to 3 | 1 to 2 | Mostly retired, not ported | medium | `app/jcl/DEFGDGD.jcl:39` |
| 5 Reference master refresh and export | 6 to 10 | 4 to 7 | Four rebuild jobs with alternate indexes, 1,355 lines, the CICS window jobs | medium | `app/jcl/CARDFILE.jcl:83` |
| 6 Posting, account refresh, report | 20 to 32 | 14 to 22 | Oracle and parallel run, packed decimal, the destructive daily cycle, JCL built inside COBOL | low | `app/jcl/POSTTRAN.jcl:23` |
| 7 Online updates | 24 to 40 | 16 to 28 | 7,972 lines, COACTUPC alone is 3,368, 9 programs with computed calls | low | `app/cbl/COACTUPC.cbl:573` |
| 8 Authorization feed | 14 to 24 | 10 to 18 | IMS and DB2 definitions not read, no mapped DDs for the unload programs | low | `app/app-authorization-ims-db2-mq/cbl/PAUDBLOD.CBL:244` |
| 9 Authorization screens, transaction types | 16 to 28 | 11 to 20 | 4,469 lines, god module COPAUS0C, DB2 | low | `app/app-authorization-ims-db2-mq/cbl/COPAUS0C.cbl:322` |
| Total | 94 to 160 | 64 to 112 | Sum of the rows above | | inference |

Waves 1 to 6, which carry the three must-not-break items, total 40 to 68 conventional and 27 to 46 AI-assisted (inference: sum of the rows). Waves 7 to 9 are over half of the total, and none of the three must-not-break items needs them.

## Wave 6 split by term

| Term | Conventional | AI-assisted | Does AI assistance shrink it? | Evidence |
|---|---|---|---|---|
| Port (2,328 lines plus the wrapper scripts and the wave's jobs) | 5 to 8 | 2 to 4 | Yes. Transliteration is the strong case when a comparison harness exists. Review replaces authoring. | `app/cbl/CBTRN02C.cbl:547` |
| Boundary work (facade over the shared masters, scheduler switch) | 4 to 6 | 3 to 5 | Partly. The code is quick. Choosing who owns the masters is not. | `modernization-assessment/graph.json:28699` |
| Equivalence harness and normalization spec | 5 to 8 | 4 to 6 | Partly. Harness code is quick. Getting archived generations and signing the spec is not. | `modernization-assessment/06-test-strategy.md:1` |
| Parallel run, rehearsal, cutover window | 6 to 10 | 5 to 7 | No. Calendar time, client availability and approvals. | `scripts/run_posting.sh:12` |

## Assumptions the range is most sensitive to

These are claims, and each can be tested.

1. **Assumes a parallel run or archived generations covering a month end exist.** If neither exists and the oracle is characterization tests only, the harness term in wave 6 roughly doubles and its confidence drops further. Test: ask for the generations behind `DALYREJS` and `TRANSACT.BKUP` (`app/jcl/POSTTRAN.jcl:38`, `app/jcl/TRANREPT.jcl:33`).
2. **Assumes the 28 computed calls are the screen-transfer idiom and resolve to a closed list of program names.** If they reach into tables built at run time, wave 3 and wave 7 grow by half. Test: read the 28 call sites listed at `modernization-assessment/05a-dead-code-candidates.md:61`.
3. **Assumes review costs a quarter of the authoring time it replaces, about 0.5 engineer-weeks per 1,000 lines for the AI-assisted case.** If reviewers must re-derive the business rule behind every paragraph, the AI-assisted port term loses most of its advantage. Test: time wave 2.
4. **Assumes the unread definitions (IMS DBD and PSB, DB2 DDL, assembler) hold no logic that wave 6 depends on.** The assembler date routines COBDATFT and MVSWAIT sit next to the date handling of posting and are not read (`modernization-assessment/graph.json:27459`). If posting calls them through a path the extractor missed, wave 6 grows.
5. **Assumes the demo data shape is the production shape.** Production volume, the real key lengths and any alternate index usage are not in the tree.

## What an AI coding agent can and cannot do here

| Can, with a harness | Cannot, or should not | Evidence |
|---|---|---|
| Transliterate the paragraphs of CBTRN02C, CBTRN03C and CBACT04C into a decimal-safe language, and the IDCAMS rebuild jobs into provisioning code | Decide that a truncating divide (`/ 1200` with no ROUNDED) is intended, or that the reason code 103 overwriting 102 is acceptable. Those are Deviation Register decisions. | `app/cbl/CBACT04C.cbl:465`, `app/cbl/CBTRN02C.cbl:417` |
| Generate the replay harness and the diff and normalization code | Obtain the oracle, which is a client action | `modernization-assessment/06-test-strategy.md:1` |
| Read the 28 computed call sites and list the candidate targets | Prove a target set closed without the program-name tables, or the CICS definition changes made after the CSD export | `app/csd/CARDDEMO.CSD:317` |
| Port the 3,368-line COACTUPC with a screen-level harness | Infer undocumented rules in the long validation paragraphs without a test per rule | `app/cbl/COACTUPC.cbl:573` |

Not charged: discovery. The graph, the waves and the risk register already exist (`modernization-assessment/waves.json:1`, `modernization-assessment/risks.json:1`). What remains are the client's answers in `00-summary.md`.
