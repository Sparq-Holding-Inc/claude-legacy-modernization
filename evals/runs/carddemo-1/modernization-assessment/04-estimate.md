# 04 Estimate

Basis: engineer-weeks, shown for two delivery modes side by side, conventional (no AI coding assistance) and AI-assisted (engineers using an AI coding agent, with human review). No `--delivery` flag was given, so both are quoted and neither is the headline. This plugin carries no calibrated productivity data. Every rate below is a planning assumption, not a benchmark. Replace them with the team's measured velocity after wave 2.

Understanding the code is not charged. This assessment did it. What remains is the client's answers in `00-summary.md`.

Size context: 44 COBOL programs and 55 JCL jobs (`01-inventory.md`). The COBOL is about 2,900 lines in the five posting and report files alone (`app/cbl/CBTRN02C.cbl:731`). The ranges are for a team that has someone who reads COBOL and JCL.

| Wave | Conventional (eng-weeks) | AI-assisted (eng-weeks) | Largest term | Confidence | Evidence |
|---|---|---|---|---|---|
| 1 Utility jobs | 3 to 5 | 2 to 4 | Replacing the job runner | medium | `app/jcl/CBADMCDJ.jcl:1` |
| 2 Read-only batch | 5 to 8 | 3 to 5 | Byte-exact reader harness | medium | `app/cbl/CBACT01C.cbl:29` |
| 3 Online inquiry | 8 to 14 | 6 to 10 | Facade over the menu cycle | low | `app/cbl/COMEN01C.cbl:201` |
| 4 Build jobs | 2 to 4 | 1 to 3 | Build toolchain choice | medium | `app/jcl/DEFGDGD.jcl:39` |
| 5 Reference loads and handshake | 8 to 14 | 6 to 11 | CICS handshake replacement; CBSTM03A rewrite | medium | `app/jcl/CLOSEFIL.jcl:26` |
| 6 Posting, refresh, report | 20 to 36 | 16 to 30 | Oracle, rehearsals, cutover | low | `app/cbl/CBTRN02C.cbl:51` |
| 7 Online writers | 14 to 24 | 10 to 18 | Shared-store facade; id assignment | low | `app/cbl/COBIL00C.cbl:41` |
| 8 Authorization subsystem | 12 to 22 | 10 to 18 | IMS data model, unread | low | `app/app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl:24` |
| 9 Authorization screens and DB2 | 8 to 14 | 6 to 11 | God module behind a facade | low | `app/app-authorization-ims-db2-mq/cbl/COPAUS0C.cbl:322` |
| Total | 80 to 141 | 60 to 110 | | low | inference |

## What shrinks with AI assistance and what does not

- **Port.** An agent transliterates COBOL well when a comparison harness exists. The cost moves to review. Assumption: review takes about a quarter of the authoring time it replaces for the straight batch programs (waves 2 and 5), and about half for CBTRN02C, CBTRN03C and the online programs, because their defects are in behaviour, not syntax.
- **Boundary work and harness code.** Partly. The code is quick to write. Choosing the boundary is not.
- **Oracle, approvals, rehearsals, cutover windows, client availability.** These do not shrink. In wave 6 they are the longest term, and the AI-assisted range there is only slightly lower for that reason.

## Where an agent can and cannot port

- Strong: CBACT01C to CBACT03C, CBCUS01C, CBEXPORT, CBIMPORT (straight reads and writes with a copybook layout), and the IDCAMS define and REPRO jobs.
- Weak: anything whose correct behaviour is a defect in the source. CBTRN03C ends its loop with NEXT SENTENCE on the first out-of-window record, re-adds the last amount at end of file, and never writes the last card's account total (risk pass, `risks.json`). A transliteration would silently repair those. Whether to preserve them is a business decision, not a port task. CBSTM03A uses ALTER with GO TO and control-block pointers and is the hardest program in the tree, so it needs human design.
- Not assessable: waves 8 and 9 until the IMS DBD and PSB files and the DB2 DDL are read.

## The assumptions the range is most sensitive to

1. Assumes the client can supply a month of real daily transaction input and the matching before-and-after master files. If they can only supply the 9 sample files in `app/data/`, wave 6 roughly doubles, because the oracle has to be built from scratch.
2. Assumes the CA-7 listing and the Control-M file describe the same schedule and POSTTRAN is gated as the CA-7 shows (`app/scheduler/CardDemo.ca7:70`). If production runs a third schedule, wave 6 grows by two to four weeks of reconciliation.
3. Assumes the shared-store facade lets ported batch code read and write the CICS VSAM records directly. If it cannot, and a copy must be synchronised, waves 6 and 7 together roughly double.
4. Assumes the 28 computed calls resolve as the cartographer's sets show (`02-coupling.md`). If an outside COMMAREA can name other programs, wave 3 and wave 7 each grow by about a third.
