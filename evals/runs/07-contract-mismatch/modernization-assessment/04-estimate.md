# 04 Estimate

Target state: refactor. Every figure is a range in engineer days for a team that has one person who can read COBOL and JCL. These are inference. There is no telemetry, no team history and no velocity to measure, so nothing here is a measured number.

## Method

The system is 32 lines of COBOL, 6 lines of copybook and 9 lines of JCL (`01-inventory.md`). Lines of code do not move the estimate. What moves it is the edges that cross a wave boundary, and there is one: the contract edge on SPARQ.TEST.MASTER (`app/cbl/PGMW.cbl:6`, `app/cbl/PGMR.cbl:6`). I estimate the harness and the environment for each wave, then the port. The port itself is a small share of each wave.

## Per wave

| Wave | Port | Harness and environment | Total range | Method | Evidence |
|---|---|---|---|---|---|
| 1. Reader (`PGMR`, `job:READJOB`) | 0.5 to 1 day | 3 to 6 days: toolchain, capture of a golden dataset, transfer of packed data to the target platform | 4 to 7 days | Bottom up, from the edge that crosses the boundary | `app/jcl/READJOB.jcl:3`, inference |
| 2. Writer (`PGMW`, `job:WRITEJOB`) | 1 to 2 days | 3 to 6 days: byte comparison of the produced file, allocation and delete handling for the new dataset | 4 to 8 days | Bottom up | `app/jcl/WRITEJOB.jcl:3`, inference |
| Both waves together | | Deviation register, sign off, wiring the scheduler order that the tree does not define | 2 to 4 days more | Inference | `app/jcl/WRITEJOB.jcl:1`, inference |

Total: about 10 to 19 engineer days. Most of it is harness and environment. Wave 1 pays for the toolchain that wave 2 reuses.

## The assumptions this range is most sensitive to

1. **The two record layouts are the same 15 bytes, and the file holds 15 byte records.** The PIC clauses agree (`app/cpy/LAYOUTX.cpy:2`, `app/cpy/LAYOUTX.cpy:3`, `app/cpy/LAYOUTY.cpy:2`, `app/cpy/LAYOUTY.cpy:3`). The DD says `LRECL=80` (`app/jcl/WRITEJOB.jcl:4`). If the file really holds 80 byte records, or if a consumer outside this tree expects them, wave 2 roughly doubles, and wave 1 grows by two to three days.
2. **SPARQ.TEST.MASTER has one writer and one reader.** That is what `analysis.data_hubs` shows for this tree. If another program outside the tree reads it, each extra consumer adds a boundary test and about two days to wave 2.
3. **An oracle can be had.** Wave 1 assumes the client can supply one archived copy of SPARQ.TEST.MASTER, or the SYSOUT of a good run. If none exists, the oracle has to be built by running the legacy writer, and both waves move up by two to three days. If the legacy system cannot be run at all, the coverage is provisional (see `06-test-strategy.md`).

## What moves the estimate

- **Coupling edges across the boundary.** One, medium. That is small, and it is where the risk sits.
- **Behavioral oracle.** None in the tree. This is the largest unknown.
- **God modules.** None (`analysis`, field `god_modules`).
- **Logic in the database.** No EXEC SQL appears in either program (`app/cbl/PGMR.cbl:13`, `app/cbl/PGMW.cbl:13` are plain file I/O), so none is visible in the tree. Stored procedures elsewhere would not show.
- **Who can read the source.** The estimate assumes one person can.

## What Claude Code can do, and what it cannot

- **Mechanical port, with a good harness.** Both programs are transliteration: open, one read or one write, close (`app/cbl/PGMR.cbl:13`, `app/cbl/PGMW.cbl:13`). The copybooks map to a record type with a decimal field. The DD parameters become a dataset definition on the new platform. Claude Code is strong at this and it needs little review.
- **Not from the source.** The intent of the unfilled output record (`app/cbl/PGMW.cbl:14`), the meaning of LRECL 80 against a 15 byte layout, whether the TEST dataset name is real, and the order of the two jobs in the nightly cycle. Nobody can infer these from the code. They need the client's engineers. Do not let a port decide them.
