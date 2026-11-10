# CICS recipes

A CICS system definition file (CSD) gives you three facts. Which transaction ids start which programs. Which programs are online. Which dataset sits behind each CICS file name. Use them to mark entry points and to join online code to batch code on one dataset.

Node ids: programs are bare names. A dataset is `ds:DSN`. A program named in the CSD with no source in the tree is `ext:NAME`.

Edge shape: from, to, kind, mode, confidence, resolved, evidence (`path:line`, path from the scan root).

| Fact | Result |
|---|---|
| DEFINE TRANSACTION with PROGRAM | node PROG is an entry point and online. Note `CSD transaction TRNX`. Evidence is the DEFINE TRANSACTION line. No edge. |
| DEFINE PROGRAM | node PROG is online. Not an entry point by itself. |
| DEFINE FILE with DSNAME | CICS file name maps to `ds:DSNAME`. Used by the data edges below. |
| EXEC CICS file command on FILE('X') | PROG to `ds:DSNAME` (or `ds:X`), data, high, resolved true. Evidence is the COBOL lines only. |

All patterns are case-insensitive. Pass `-i`.

## 1. Find the CSD files

Glob: `**/*.{csd,CSD}`. Names are case-blind. CSD files are short. Grep to locate, then Read the file whole.

## 2. Read the entries

A DEFINE starts a block. The block is the DEFINE line and every line after it up to the next DEFINE. A line whose first non-blank character is `*` is a comment. Skip it. Attributes (GROUP, PROGRAM, DSNAME, STATUS) may sit on the DEFINE line or on lines below it.

Pattern: `^\s*DEFINE\s+(TRANSACTION|PROGRAM|FILE)\s*\(\s*[^)\s]+\s*\)`. The name in the first parentheses is the transaction id, program name or CICS file name. Upper-case it.

Attribute pattern: `(^|[^A-Z0-9_-])(PROGRAM|DSNAME)\s*\(\s*[^)\s]+\s*\)`. Take attributes only from after the first `)` of the DEFINE. The pattern also hits `DEFINE PROGRAM(PGMX)` lines. Ignore those hits. Another command (ALTER, INSTALL) between two DEFINEs is not part of the block. Do not take its attributes. If two CSD files define one name, keep the first.

## 3. Transaction to program

**Fact:** transaction TRNW runs PROGW.
**Run on:** `**/*.csd`.
**Read:** the DEFINE TRANSACTION block. Its `PROGRAM(name)` is the program. No PROGRAM attribute: no fact.
**Resolve:** if a COBOL file has `PROGRAM-ID. NAME`, the node is the bare name. Check with Grep `PROGRAM-ID\.\s+NAME\b` on the COBOL globs. Else the node is `ext:NAME`, with note `CSD transaction TRNX maps to a program with no source in the tree`, and it is an entry point.
**Result:** `entry_point: true`, entry evidence is `csd-path:line` of the DEFINE TRANSACTION line. Unit type online.
**Confidence:** high. Nothing is guessed.
**Traps:** the PROGRAM attribute is often on the next line. Read the block, not one line. A transaction id is not a program name. A program can have many transaction ids. A program named by LINK or XCTL is not an entry point because of that.

## 4. Online programs

**Fact:** a program is online.
**Pattern:** `^\s*DEFINE\s+PROGRAM\s*\(\s*[^)\s]+\s*\)`.
**Result:** mark the program online. A program is also online if its source holds `EXEC CICS` (Grep `EXEC\s+CICS\b` on the COBOL globs) or if a transaction names it. Online wins over batch and subprogram when you set unit types.
**Confidence:** high.
**Traps:** a DEFINE PROGRAM is not an entry point. Only a transaction makes one.

## 5. File name to dataset

**Fact:** CICS file ACCTDAT is dataset SPARQ.TEST.ACCTDAT.KSDS.
**Pattern:** `^\s*DEFINE\s+FILE\s*\(\s*[^)\s]+\s*\)` for the file name. Then `DSNAME\s*\(\s*[^)\s]+\s*\)` inside that block.
**Read:** file name from the DEFINE FILE parentheses. Dataset from DSNAME in the same block. No DSNAME: no fact.
**Use it with the COBOL commands.** Find them: `EXEC\s+CICS\s+(READ|READNEXT|READPREV|STARTBR|ENDBR|RESETBR|UNLOCK|WRITE|REWRITE|DELETE)\b` and read the `FILE(...)` or `DATASET(...)` operand, in the same EXEC block.
- Literal `FILE('ACCTDAT')`: look the name up in the CSD. Found: dataset `ds:` plus the DSNAME. Not found: dataset `ds:ACCTDAT`, note `CICS file ACCTDAT, no CSD DEFINE FILE found`.
- Variable operand: follow the COBOL recipes. A literal moved to the variable gives medium. A computed name gives a low, unresolved edge.

**Mode by command.** READ, READNEXT, READPREV, STARTBR, ENDBR, RESETBR, UNLOCK give read. WRITE, REWRITE, DELETE give write. One program that both reads and writes a dataset gets one edge with mode read_write. Per program and dataset, make one edge and list every command line as evidence.
**Edge:** program to dataset, data, mode as above, high for a literal, resolved true. Evidence: the EXEC CICS lines only. Put the CSD file and line in the note, for example `CICS file ACCTDAT, CSD DSNAME at app/csd/DEMO.CSD:2`.
**Why it matters:** a batch job that names the same dataset in a DD joins the online program on the same `ds:` node. Writers and readers of one dataset then get a contract edge (high if they share the layout copybook, medium if not).
**Traps:** the CICS file name and the dataset name differ. Never use the file name as the dataset when a CSD entry exists. DSNAME may be in a different CSD from the DEFINE FILE only if the block is split. Names with a trailing member are not stripped here.

## 6. Worked examples

**05-vsam-cics-pair.** `rg -n -i -e '^\s*DEFINE\s+(TRANSACTION|PROGRAM|FILE)\s*\(|DSNAME\s*\(|(^|[^A-Z0-9_-])PROGRAM\s*\(' app/csd`
```
DEMO.CSD:1 DEFINE FILE(ACCTDAT) GROUP(DEMO)      :2 DSNAME(SPARQ.TEST.ACCTDAT.KSDS)
DEMO.CSD:4 DEFINE TRANSACTION(TRNW) GROUP(DEMO)  :5 PROGRAM(PROGW) STATUS(ENABLED)
DEMO.CSD:6 DEFINE TRANSACTION(TRNR) GROUP(DEMO)  :7 PROGRAM(PROGR) STATUS(ENABLED)
DEMO.CSD:8 DEFINE PROGRAM(PROGW)                 :9 DEFINE PROGRAM(PROGR)
```
Result: PROGW and PROGR are online and entry points (evidence DEMO.CSD:4 and :6). Then `rg -n -i -e "EXEC\s+CICS\s+(READ|WRITE)" app/cbl` finds PROGW.cbl:7 `WRITE FILE('ACCTDAT')` and PROGR.cbl:7 `READ FILE('ACCTDAT')`. Edges: PROGW data write `ds:SPARQ.TEST.ACCTDAT.KSDS`, high, evidence PROGW.cbl:7. PROGR data read, high, PROGR.cbl:7. Both include `cpy:ACCTREC` (line 5). Same layout on both sides, so PROGW to PROGR contract, high.

**26-wave-seed-families.** DEMO.CSD:1 `DEFINE FILE(MSTFILE)`, :2 `DSNAME(SPARQ.TEST.MASTER)`, :4 `TRANSACTION(TRNV)` with `PROGRAM(PGMVIEW)` at :5, :6 `TRANSACTION(TRNW)` with `PROGRAM(PGMEDIT)` at :7. PGMVIEW and PGMEDIT are entry points (evidence :4 and :6). PGMVIEW.cbl:4 `READ FILE('MSTFILE')` gives PGMVIEW data read `ds:SPARQ.TEST.MASTER`. PGMEDIT.cbl:4 `WRITE FILE('MSTFILE')` gives PGMEDIT data write the same node. Batch jobs (RPTJOB, UPDJOB, AUDJOB) name that dataset in a DD, so they meet the online programs there.

**27-jcl-text-in-cobol.** SUB.CSD:1 `DEFINE TRANSACTION(TRNS)`, :2 `PROGRAM(PGMSUB)`, :3 `DEFINE PROGRAM(PGMSUB)`. PGMSUB is an entry point (SUB.CSD:1), online. It also holds JCL text in a literal (PGMSUB.cbl:6). That text is not read as JCL by the patterns here.

**22-rw-modes (no CSD).** `rg -n -i -e "EXEC\s+CICS\s+(READ|REWRITE|STARTBR|READNEXT|ENDBR|DELETE)" app/cbl`. No CSD exists. PROGCICS data read_write `ds:RWFILE` (READ UPDATE :4, REWRITE :5). Data read `ds:BRFILE` (:6, :7, :9). Data write `ds:DELFILE` (:10). Each note says `no CSD DEFINE FILE found`. PROGCICS is online because it holds EXEC CICS, but it is not an entry point.

## 7. Not covered

- DEFINE for MAPSET, TDQUEUE, TSMODEL, CONNECTION and other resource types. Only TRANSACTION, PROGRAM and FILE are read.
- GROUP and LIST membership, and which groups are installed. A DEFINE is taken as live. STATUS(DISABLED) is not checked.
- CSD batch utility commands (ALTER, COPY, APPEND, ADD GROUP).
- Transaction attributes such as TWASIZE, PROFILE, REMOTESYSTEM. Remote transactions are not resolved.
- Dynamic installs, RDO outside the CSD, and CICS tables in assembler (DFHPCT, DFHFCT).
- The DSNAME of a remote or shared file (RLS, FILE with REMOTESYSTEM).
- CICS file commands that use no FILE or DATASET operand.
