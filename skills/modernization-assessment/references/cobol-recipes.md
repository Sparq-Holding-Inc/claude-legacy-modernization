# COBOL recipes

A COBOL source file tells you five things: which programs it calls, which copybooks it includes, which files it opens, which DB2 tables it touches, and which CICS programs and files it uses. Run the recipes below with Grep, read the hits, and write one edge per fact.

Edge shape: `from`, `to`, `kind` (`call`, `include`, `data`), `mode` (`read`, `write`, `read_write`, data edges only), `confidence` (`high`, `medium`, `low`), `resolved` (`true` or `false`), and `evidence` (a list of `file:line`, the statement first, then any helper line).

Ids: a program is its PROGRAM-ID name (not the file name). A copybook is `cpy:STEM`. A program or copybook not in the tree is `ext:NAME`. A DB2 table is `ds:db2:TABLE`. A dataset is `ds:DSN`. A computed target is `?dynamic:PROGRAM:LINE` with `resolved=false`, `confidence=low`.

File types: programs are `.cbl .cob .cobol .pco .cbx`. Copybooks are `.cpy .copy`. Match extensions in any case. Copybook name = file name without extension, upper case. If two copybooks share a name, the first path in sorted order wins; report the other as a duplicate. If two programs share a PROGRAM-ID, keep the first and report the other.

## 1. Fixed-format rules (apply before trusting any hit)

Do these steps in order for every hit.

1. **Free format.** Run `^\s*>>\s*SOURCE\s+FORMAT\s+(IS\s+)?FREE` (case-insensitive) on each program. If it hits, the file is free format. Do not guess. Report it as unparsed ("free-format COBOL, not parsed") and write no edges from it. Also treat a file as free format if hits show code starting in columns 1 to 6.
2. **Column 7 is the indicator.** Count 6 characters, the 7th is the indicator.
   - `*` or `/`: the whole line is a comment. Ignore every hit on it.
   - `-`: continuation of the previous line (step 5).
   - space or anything else (including `D`): normal code.
3. **Columns 1 to 6 and 73 to 80 are ignored.** Code lives in columns 8 to 72. Text past column 72 is a sequence number or noise. A keyword that starts after column 72 is not code. An `END-EXEC` past column 72 does not count, so that EXEC is unterminated.
4. **Inline comment.** `*>` outside a literal starts a comment to the end of the line. Ignore text after it.
5. **Continuation.** A line with `-` in column 7 continues the line before it.
   - If the previous line ends inside an open literal (an odd count of quote marks, where `''` inside a literal counts as zero): drop the leading spaces of the new line, drop the opening quote that starts the new line's text, and append the rest directly with no space. The literal runs to column 72 of the previous line, spaces included.
   - Otherwise join with one space.
   - The statement's line number is the first physical line.
6. **Literals.** Text inside quotes is data, not code. A `CALL`, `COPY` or `EXEC` inside a quoted string is not a statement. A continuation line that starts with a quote is inside a literal: check the line above.
7. **Statements span lines.** Treat a newline as a space. `COPY` on one line and the name on the next is one statement. Same for `CALL`, `SELECT`, `OPEN`.
8. **EXEC blocks.** `EXEC CICS`, `EXEC SQL`, `EXEC SQLIMS`, `EXEC DLI` run to the nearest `END-EXEC`. Inside a block, COBOL verbs (`CALL`, `MOVE`, `OPEN`) are not COBOL statements. A `CALL` inside `EXEC SQL` is a stored procedure call: no edge.
9. **Unterminated EXEC.** Count EXEC starts and END-EXEC per file (recipe 11). If they differ, find the EXEC with no END-EXEC. Write no edge for it. Report it: `file: line N: EXEC CICS has no END-EXEC, statement not parsed`. Never drop it silently.
10. **Hit inside a comment or literal.** Ignore it. Exceptions: the VALUE and MOVE literals you read as values (recipe 4), and embedded JCL text (recipe 12).
11. **Copybooks.** A COPY pulls the copybook text into the program. A CALL, MOVE, VALUE or EXEC inside a copybook counts for every program that copies it. Report such evidence as the copybook `file:line` first, then the program's COPY line. Search copybooks too (glob `**/*.cpy`, `**/*.copy`) when the name you resolve is not defined in the program.
12. **No PROGRAM-ID.** Report the file as unparsed ("no PROGRAM-ID found").

Column guard used in all patterns below (do not shorten it): `^.{6}[^*/](.{0,63}[^A-Z0-9_-])?`. It drops comment lines, drops keywords after column 72, and stops a keyword matching inside a longer word (`END-CALL`, `WS-CALL`). It does not catch quotes or `*>` before the keyword, so still read the line. All patterns use the Grep `-i` option and `output_mode: content` with `-n`.

## 2. Programs (PROGRAM-ID)

Pattern: `^.{6}[^*/].{0,63}PROGRAM-ID\s*\.?\s+[A-Z0-9][A-Z0-9_-]*`
Glob: `**/*.{cbl,cob,cobol,pco,cbx}`. The name after PROGRAM-ID is the node id. Calls resolve against this name. Trap: the PROGRAM-ID can differ from the file name.

## 3. Static CALL 'LITERAL'

Pattern: `^.{6}[^*/](.{0,63}[^A-Z0-9_-])?CALL\s+['"][^'"]+['"]`
Glob: programs, plus copybooks.
Target: the text between the quotes, upper case, trimmed. Resolve: if a program with that PROGRAM-ID exists, `to` is that name. Otherwise `to = ext:NAME`.
Edge: `kind=call`, `resolved=true`, `confidence=high`, evidence = the CALL line.
Traps: a CALL inside an EXEC block is not a call. A literal split by a continuation line: join it (step 5).

## 4. Dynamic CALL variable

Patterns:
- `^.{6}[^*/](.{0,63}[^A-Z0-9_-])?CALL\s+[A-Z0-9][A-Z0-9_-]*`
- `^.{6}[^*/](.{0,63}[^A-Z0-9_-])?CALL\s*$` (name on the next line)

The first pattern also matches `DISPLAY 'CALL FAILED'`, a CALL inside EXEC SQL, and `' CALL X'` on a continuation line. Read each hit: ignore it if the CALL sits in a literal (odd quote count before it), inside an EXEC block, or on a `-` line that continues a literal. A name followed by `(` is subscripted (`CALL TBL(IDX)`): dynamic only.

Resolve the variable V in this order (the same four rules apply to `PROGRAM(V)` in recipe 5 and `FILE(V)` in recipe 9):

1. Subscripted or reference-modified (`V(...)`): dynamic only. Skip to the end.
2. List every mention of V in the program and its copybooks. Grep `(^|[^A-Z0-9_-])V([^A-Z0-9_-]|$)` (replace V). Classify each hit:
   - **VALUE:** a level `01`-`77` item (not `88`) with `VALUE 'LIT'`. VALUE may be on the next line. Search: `(^|[^A-Z0-9_-])[0-9][0-9]\s+V\s[^.]*VALUE\s+(IS\s+)?['"]` with Grep multiline on.
   - **Literal MOVE:** `MOVE 'LIT' TO ... V`. The receiver list can have several names. Also read a literal continued over lines.
   - **Name MOVE:** `MOVE SRC TO V`. If SRC is itself a constant (VALUE only, rule 3), SRC's literal is a candidate. Follow one hop only.
   - **Other receiver:** any `MOVE` of a non-literal (`SPACES`, a number, a name that is not a constant), `ACCEPT V`, `INITIALIZE V`, `STRING ... INTO V`, `UNSTRING ... INTO V`, `SET V TO`, `READ ... INTO V`, `EXEC CICS ... INTO(V)` or `SET(V)`.
3. **Constant:** V has a VALUE literal and no MOVE of any kind, no other receiver. Treat V as that literal. Edge: `resolved=true`, `confidence=high`, evidence = call line, then VALUE line. No dynamic edge.
4. **Literal moves:** otherwise, each distinct literal moved to V (or moved from a constant name) is a candidate. Edge per candidate: `resolved=true`, `confidence=medium`, evidence = call line, then the MOVE line (and the VALUE line for a constant source). V's own VALUE is not a candidate when V is also a receiver.
5. **Always add a dynamic edge** unless V is a constant: `to = ?dynamic:PROGRAM:LINE` (LINE = line of the CALL or EXEC), `resolved=false`, `confidence=low`, evidence = call line. The candidates may not be all the values.
6. No candidates at all: only the dynamic edge.

Candidate literal not in the tree: `to = ext:NAME`.

## 5. EXEC CICS LINK and XCTL

Start-line pattern: `^.{6}[^*/](.{0,63}[^A-Z0-9_-])?EXEC\s+CICS\s+(LINK|XCTL)\b`
Whole statement (Grep multiline on): `^.{6}[^*/](.{0,63}[^A-Z0-9_-])?EXEC\s+CICS\s+(LINK|XCTL)\b[\s\S]*?END-EXEC`
Also check `EXEC\s+CICS\s*$` hits (verb on the next line).
In the statement, read `PROGRAM(...)`: a quoted literal, or a name, or a name with `(subscript)`. Resolve it with recipe 4 rules. Edge `kind=call` for both LINK and XCTL. The evidence line is the line with `EXEC`, not the `PROGRAM(` line.
Traps: a comment line inside the block hides nothing; skip it. If another `EXEC` appears before the `END-EXEC`, the first is unterminated (rule 9). `START`, `RETURN TRANSID`, `RUN` and `READQ`/`WRITEQ` are not extracted (see Not covered).

## 6. COPY

Patterns:
- `^.{6}[^*/](.{0,63}[^A-Z0-9_-])?COPY\s+['"]?[A-Z0-9][A-Z0-9_-]*`
- `^.{6}[^*/](.{0,63}[^A-Z0-9_-])?COPY\s*$` (name on the next line)

Glob: programs and copybooks (nested COPY).
Name: the first word after COPY, quotes removed, upper case. Ignore `OF lib` / `IN lib`. `REPLACING ==a== BY ==b==` is ignored; the copybook is still included. The statement ends at the period, which may be on a later line (`COPY 'X'` then `.` below).
Resolve: if a `.cpy`/`.copy` file with that stem exists, `to = cpy:NAME`. Otherwise `to = ext:NAME`.
Edge: `kind=include`, `resolved=true`, `confidence=high`. `from` = the program, or `cpy:X` when the COPY is inside copybook X. Evidence = the line holding the word COPY. Only direct COPYs: a program does not get an edge for a copybook nested in its copybook; the copybook has its own edge.
Trap: REPLACING text is not applied. If a record or CALL name depends on it, read the copybook and label what you infer.

## 7. EXEC SQL INCLUDE

Pattern: `^.{6}[^*/](.{0,63}[^A-Z0-9_-])?EXEC\s+SQL\s+INCLUDE\s+[A-Z0-9][A-Z0-9_-]*` and `EXEC\s+SQL\s*$` (INCLUDE on the next line).
Only when INCLUDE is the first word after `EXEC SQL`. Resolve like COPY: `cpy:NAME` if in the tree, else `ext:NAME` (`ext:SQLCA`). Edge `kind=include`, `high`, evidence = the EXEC line. No table edge from this block.

## 8. File I/O: SELECT, OPEN, record layout

SELECT pattern (Grep multiline on): `^.{6}[^*/](.{0,63}[^A-Z0-9_-])?SELECT\s+(OPTIONAL\s+)?[A-Z0-9][A-Z0-9_-]*\s+ASSIGN\s+(TO\s+)?(['"][^'"]+['"]|[A-Z0-9][A-Z0-9_-]*)`
Read: file name = word after SELECT. DD name = the ASSIGN operand (quotes removed, upper case). Strip one leading prefix if present: `UT-S-`, `DA-S-`, `AS-S-`, `UT-A-`, `DA-A-`, `S-`, `AS-`, `UT-`, `DA-`. Example: `UT-S-SYSOUT` gives `SYSOUT`.
Organization (same statement, up to the period): `ORGANI[SZ]ATION\s+(IS\s+)?(INDEXED|RELATIVE|SEQUENTIAL|LINE\s+SEQUENTIAL)`. INDEXED = VSAM KSDS, RELATIVE = VSAM RRDS. Use it as a note on the dataset.
Trap: `ASSIGN TO EXTERNAL X` or `DYNAMIC`: the pattern takes the keyword as the name. Read the line and use the real name. A `SELECT` with no `ASSIGN` is SQL, ignore.

OPEN patterns:
- `^.{6}[^*/](.{0,63}[^A-Z0-9_-])?OPEN\s+(INPUT|OUTPUT|I-O|EXTEND)\b`
- `^.{6}[^*/](.{0,63}[^A-Z0-9_-])?OPEN\s*$`

Read the whole statement. A mode word applies to every file name after it until the next mode word or a word that is not a SELECTed file. `OPEN INPUT A B OUTPUT C` gives A and B read, C write.

Mode comes only from OPEN: `INPUT` = read, `OUTPUT` = write, `EXTEND` = write, `I-O` = read_write. READ, WRITE, REWRITE and CLOSE do not change mode. A file opened in two ways in one program (or in two OPENs) merges: more than one distinct mode gives read_write. A SELECT with no OPEN gives no edge.

Resolve the DD to a dataset: find the JCL step that runs this program (`EXEC PGM=PROGRAM`) and the DD card with the same name; its DSN is the dataset (see the JCL recipes). Edge: `from` program, `to = ds:DSN`, `kind=data`, `confidence=high`, `resolved=true`, evidence = SELECT line, OPEN line(s), then the JCL DD line. A DD that is DUMMY or has no DSN gives no edge. If no JCL step maps the DD: `to = ds:dd:PROGRAM.DD`, `resolved=false`, `confidence=low`, evidence = SELECT and OPEN lines.

Record layout (optional note, used to compare a writer and a reader): Grep `FD\s+FILE` and read the `01` names under it. Also `READ file ... INTO rec` and `WRITE|REWRITE rec FROM var`. If the `01` record is defined in a copybook the program copies (Grep `^.{6}[^*/]\s*01\s+REC` in the copybooks), that copybook is the layout. A record the program defines itself has none.

## 9. EXEC CICS file I/O

Pattern (Grep multiline on): `^.{6}[^*/](.{0,63}[^A-Z0-9_-])?EXEC\s+CICS\s+(READ|READNEXT|READPREV|STARTBR|ENDBR|RESETBR|UNLOCK|WRITE|REWRITE|DELETE)\b[\s\S]*?END-EXEC`
Read `FILE(...)` or `DATASET(...)`: quoted literal, name, or subscripted name. Resolve with recipe 4. The verb must be exactly one of the list (`READQ`, `WRITEQ`, `DELETEQ` are queues: not extracted). A statement with no FILE/DATASET gives nothing.
Verb to mode: READ, READNEXT, READPREV, STARTBR, ENDBR, RESETBR, UNLOCK = read. WRITE, REWRITE, DELETE = write. `READ ... UPDATE` is still read.
Per file name across the program: collect all verbs; more than one distinct mode gives read_write. Evidence = every EXEC line for that file, in order.
Dataset: `ds:FILENAME`, unless a CSD `DEFINE FILE` names a DSNAME (then `ds:DSN`; see the CICS definitions recipe). Literal: `confidence=high`, `resolved=true`. From a variable with literal moves: each candidate `medium`, plus a dynamic data edge (`?dynamic:PROGRAM:LINE`, `resolved=false`, `low`, same mode). Constant name: `high`. Otherwise dynamic edge only.

## 10. EXEC SQL tables

Pattern (Grep multiline on): `^.{6}[^*/](.{0,63}[^A-Z0-9_-])?EXEC\s+SQL\b[\s\S]*?END-EXEC`
Quick finder, one line each (also lists table names; read the block for the rest): `(^|[^A-Z0-9_-])(FROM|JOIN|INSERT\s+INTO|UPDATE|DELETE\s+FROM)\s+[A-Z]`
Skip INCLUDE blocks (recipe 7). In each block find tables with these rules (case-insensitive), table name = letters, digits, `_ $ # @ .`, starting with a letter. A `:name` is a host variable, not a table.
- `FROM t1 [alias], t2 [alias]` and `JOIN t`: read. Every comma-listed table after FROM is read.
- `INSERT INTO t`: write. `UPDATE t`: write. `DELETE FROM t`: write (not read).
- Within one block, a table with both read and write is read_write. Across blocks of the program, merge the same way (one read block plus one write block gives read_write).
- `DUAL` is not a table.
Edge: `to = ds:db2:TABLE`, `kind=data`, `confidence=high`, `resolved=true`. Evidence = the line with `EXEC SQL` of each block that touches the table.
Traps (false positives): `FROM` inside `EXTRACT(YEAR FROM d)`, `TRIM(x FROM y)`, `SUBSTRING(x FROM 1)`; names defined by `WITH x AS (...)`; the inner `FROM` of a subselect. Drop these by reading the block. `DECLARE c CURSOR FOR SELECT ... FROM t` is read. `OPEN c` / `FETCH c` / `CLOSE c` add nothing. A host variable table name (`FROM :TBL`) is not resolved: say so.

## 11. Unterminated EXEC check

Counts, per file: `^.{6}[^*/](.{0,63}[^A-Z0-9_-])?EXEC\s+(CICS|SQL|SQLIMS|DLI)\b` against `^.{6}[^*/](.{0,63}[^A-Z0-9_-])?END-EXEC` (Grep `output_mode: count`). Counts count lines, so a one-line `EXEC ... END-EXEC` counts once on each side. If starts exceed ends, find the EXEC with no END-EXEC and report it (rule 9). If a line holds two EXEC starts, count by reading.

## 12. Embedded JCL text

Pattern (no column guard, the text sits inside a literal): `['"]//[A-Z0-9#@$]*\s+EXEC\s+((PROC|PGM)=)?[A-Z0-9#@$]{1,8}`
Read the word after `EXEC` (after `PROC=` or `PGM=`; bare word means PROC). The literal can start on the line after `VALUE`. This is not a call edge. Record it as `embedded_jcl: PROGRAM -> proc:NAME` (or the program name for `PGM=`) with `file:line`, only when that proc or program exists in the tree. Effect: the target is not dead; call it unknown, not unreachable.

## Worked examples

**01-static-call.** Grep recipe 3 on `**/*.cbl`: hit `PROGA.cbl:6: CALL 'PROGB'.` Recipe 4 also hits `PROGA.cbl:5: DISPLAY 'CALL FAILED...'`: CALL is inside a literal, ignore it. Edge: `PROGA -> PROGB call high resolved=true, PROGA.cbl:6`.

**02-dynamic-call.** Recipe 4 hit `PROGA.cbl:9: CALL WS-PGM-NAME.` Mentions of `WS-PGM-NAME`: line 5 (no VALUE), line 8 `ACCEPT WS-PGM-NAME` (receiver). No candidates. Edge: `PROGA -> ?dynamic:PROGA:9 call low resolved=false, PROGA.cbl:9`.

**03-cics-link-xctl.** Recipe 5 multiline hits at lines 12-14, 16-18, 20-22, 23-25 in `PROGA.cbl`.
- Line 12 `PROGRAM('PROGB')`: `PROGA -> PROGB call high, :12`.
- Line 16 `PROGRAM(WS-ANY-PGM)`: only `MOVE DFHCOMMAREA TO WS-ANY-PGM` (line 15), a non-literal receiver. `PROGA -> ?dynamic:PROGA:16 call low false, :16`.
- Line 20 `PROGRAM(WS-NEXT-PGM)`: line 19 `MOVE 'PROGC' TO WS-NEXT-PGM`. `PROGA -> PROGC call medium true, [:20, :19]` and `PROGA -> ?dynamic:PROGA:20 call low false, :20`.
- Line 23 `PROGRAM(LIT-PGM-D)`: line 5 `VALUE 'PROGD'`, no moves. Constant: `PROGA -> PROGD call high true, [:23, :5]`. No dynamic edge.

**04-shared-copybook.** Recipe 6 on `**/*.cbl`: `PROGA.cbl:5`, `PROGB.cbl:5`, `COPY SHARED01.` Edges: `PROGA -> cpy:SHARED01 include high :5`, `PROGB -> cpy:SHARED01 include high :5`.

**14-exec-sql.** Recipe 7 hits `PROGSQL.cbl:5` (SQLCA, not in tree) and `:6` (DCLCUST, in `app/cpy`). Edges: `-> ext:SQLCA include :5`, `-> cpy:DCLCUST include :6`. Recipe 10 blocks start at lines 9, 15, 20, 23: `FROM CUSTOMER` read, `UPDATE ORDERS` write, `INSERT INTO AUDIT_LOG` write, `DELETE FROM STAGING` write (not read). Edges: `ds:db2:CUSTOMER read :9`, `ds:db2:ORDERS write :15`, `ds:db2:AUDIT_LOG write :20`, `ds:db2:STAGING write :23`, all `high`. `:WS-NAME` is a host variable.

**15-fixed-format.** Recipe 6 on `**/*.{cbl,cpy}` returns `PROGMAIN.cbl:8` `REAL1`, `:11` `REAL3 REPLACING`, `REAL1.cpy:2` `REAL4`, `PROGTWO.cbl:5` `REAL4`. The `COPY\s*$` pattern hits `PROGMAIN.cbl:9`; read line 10 for `REAL2`. Comments on lines 1-3 (`*`, `/`) do not hit because of the guard. Recipe 3 hits `PROGMAIN.cbl:16` `call 'PROGLOW'` and `:17` `CALL 'PROGTWO' USING`. Line 15 (`-` continuation of a literal that holds CALL) is excluded by reading; line 20's `CALL 'Z'` is in columns 73+, so the guard drops it. Edges: `PROGMAIN -> cpy:REAL1 :8`, `cpy:REAL2 :9`, `cpy:REAL3 :11`, `cpy:REAL1 -> cpy:REAL4 :2` (in REAL1.cpy), `PROGTWO -> cpy:REAL4 :5`, `PROGMAIN -> PROGLOW call :16`, `PROGMAIN -> PROGTWO call :17`. All high.

**17-quoted-copy.** Recipe 6 hits `PROGQ.cbl:5` (`COPY 'QUOTED1'`, period on line 6), `:7` (`COPY "QUOTED2".`), `:8` (`COPY QUOTED3 OF SOMELIB.`). Edges to `cpy:QUOTED1`, `cpy:QUOTED2`, `cpy:QUOTED3`, include, high, lines 5, 7, 8.

**18-continued-literal.** Recipe 5 hit `PROGA.cbl:10` XCTL `PROGRAM(WS-NEXT-PGM)`. Grep mentions of `WS-NEXT-PGM`: line 5 (no VALUE), line 9 `-    'ONE' TO WS-NEXT-PGM.` Column 7 of line 9 is `-`, so read line 8: `MOVE 'PROG` runs to column 72, so the literal is `PROGONE`. Edges: `PROGA -> PROGONE call medium true, [:10, :8]` and `PROGA -> ?dynamic:PROGA:10 call low false, :10`.

**21-exec-sql-call.** Recipe 4 hit `PROGS.cbl:5: CALL MYPROC(:WS-X)` lies between `EXEC SQL` (line 4) and `END-EXEC` (line 6). Stored procedure call. No edge.

**22-rw-modes.** `PROGBAT`: SELECT at line 6 (`MAST-FILE`, DD `MASTDD`, INDEXED), OPEN `I-O` at line 15, so `read_write`. JCL `RWJOB.jcl:3` maps `MASTDD` to `SPARQ.RW.MASTER`. Edge: `PROGBAT -> ds:SPARQ.RW.MASTER data read_write high, [PROGBAT.cbl:6, :15, RWJOB.jcl:3]`. `PROGCICS`: recipe 9 hits lines 4-5 `RWFILE` (READ + REWRITE: read_write), 6, 7-8, 9 `BRFILE` (STARTBR, READNEXT, ENDBR: read), 10 `DELFILE` (DELETE: write). Edges: `ds:RWFILE read_write [:4, :5]`, `ds:BRFILE read [:6, :7, :9]`, `ds:DELFILE write [:10]`, all high.

**23-subscripted-target.** Recipe 5 hit `PROGA.cbl:10`, `PROGRAM(TBL-PGM(WS-IDX))`. Subscripted, so the `MOVE 'PROGB' TO TBL-PGM(1)` (line 9) is not a candidate. Edge: `PROGA -> ?dynamic:PROGA:10 call low false, :10`.

**25-unterminated-exec.** The file starts with a byte order mark then a comment with CALL 'GHOST': the guard drops it. Recipe 3 hit `PROGE.cbl:5` gives `PROGE -> PROGF call high :5`. Recipe 11: one EXEC start, zero END-EXEC. The start is line 6 (`EXEC CICS LINK PROGRAM('LOST')`). Write no edge to LOST. Report `app/cbl/PROGE.cbl: line 6` as not parsed.

## Not covered

- **Free-format source:** report as unparsed. Offer a best-effort read only if asked, and label every edge inference, confidence low.
- **REPLACING text:** not applied to copybook content.
- **EXEC CICS START, RETURN TRANSID, RUN, READQ/WRITEQ/DELETEQ (queues), SEND/RECEIVE MAP:** not extracted. Report them as unextracted if the user asks; label anything you add inference.
- **EXEC DLI / SQLIMS blocks:** found as blocks but not mined for segments or tables.
- **SQL `MERGE INTO t`, `LOCK TABLE`, `TRUNCATE`:** not matched by the table rules. If you see MERGE INTO, report a write on that table as inference, `medium`.
- **CALL with `ADDRESS OF`/`CALL procedure-pointer`, entry points (`ENTRY 'X'`), `CANCEL`:** not extracted.
- **Dynamic names assembled by STRING, tables loaded from files, or values set in another program:** dynamic edge only.
- **Computed file names in `ASSIGN`:** use the real name from the line; label inference if it needs a JCL guess.
- **Value flow beyond one hop:** `MOVE A TO B`, `MOVE B TO V` where A is the constant: only the first hop is followed.
- **Tab characters and non-UTF-8 text:** columns can shift, and Grep may skip bytes it cannot decode. If a file gives suspiciously few hits, Read it.
