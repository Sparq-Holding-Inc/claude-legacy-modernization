# JCL recipes

JCL files give you jobs, steps, PROCs, the programs each step runs, the datasets each DD names, and step order. This file tells you how to read them with Grep, Glob and Read.

Node ids: a job is `job:NAME`. A step is `step:JOB.STEP`. A step from a PROC call is `step:JOB.CALLSTEP.PROCSTEP`. A PROC is `proc:NAME`. A dataset is `ds:DSN`. A program is its bare name. A program or PROC with no source in the tree is `ext:NAME`. All names are upper case.

Every edge has: from, to, kind, mode, confidence, resolved, evidence. Evidence is `path:line`, path relative to the scan root, line is the first line of the statement. Every edge in this file is `resolved: true`, even when the target is `ext:`.

| Fact | from | to | kind | mode | confidence |
|---|---|---|---|---|---|
| Job holds a step | job:J | step:J.S | include | none | high |
| Caller step holds PROC step | step:J.S | step:J.S.PS | include | none | high |
| Step runs a program | step | PROG or ext:PROG | call | none | high |
| Step runs a PROC | step | proc:P or ext:P | call | none | high |
| Utility step uses a dataset | step | ds:DSN | data | read or write | medium |
| Program uses a dataset through a DD | PROG | ds:DSN | data | from COBOL | high |
| Step order | step | next step | temporal | none | high |

Two more fact lists are not edges: runtime-named starts and utility writes (section 7). Keep them as lists.

All patterns are case-insensitive. Pass `-i` to Grep. In the examples, `rg -n -i -e` is the same search. A JCL statement is easy to misread with a pattern alone. Use Grep to find files and statements. Then Read each JCL file top to bottom. JCL files are short.

## 1. Find the files

Glob: `**/*.{jcl,JCL,job,JOB}` for jobs and `**/*.{prc,PRC,proc,PROC}` for PROCs. Other extensions are not read. A COBOL file may hold JCL text in a literal. That is not JCL. Do not scan `.cbl` files with the patterns below.

## 2. Read the cards

- A statement starts with `//` in columns 1 and 2. `//*` is a comment. `/*` is a delimiter. A line that starts with neither is data or noise. Skip it.
- Read columns 3 to 71 only. Columns 72 to 80 are not code.
- Layout: name, then blank, then operation (JOB, EXEC, DD, PROC, PEND), then blank, then operands. The name may be empty.
- The operand field ends at the first blank outside quotes and parentheses. Text after that is a comment.
- If the operand field ends in a comma, the next `//` line continues it. Take that line's operands from its first non-blank character. Comment lines between are skipped.
- A DD whose name field is blank is a concatenation member (section 5). A `//` line that starts with blanks and has operands only is a continuation of the statement above.
- Split operands at commas outside quotes and parentheses. `KEY=value` gives a keyword. A bare word is positional.
- Statements you ignore: IF, THEN, ELSE, ENDIF, SET, OUTPUT, INCLUDE, JCLLIB, XMIT. Steps inside an IF block count as normal steps in file order. COND= is not read. JCLLIB ORDER is not used: a PROC is found by member name (section 4).
- Read the first line of a continued statement as its evidence line.

## 3. Jobs and steps

**Fact: job.** Pattern: `^//([^*\s]\S*)?\s+JOB\b`. Files: JCL files. Hit name is the job. If the name is blank, use the file name without extension. Node `job:NAME`, entry point. Two jobs with one name: keep the first, note the second. Several JOB cards in one file make several jobs. Traps: `//* JOB` comments do not match.

**Fact: step.** Pattern: `^//([^*\s]\S*)?\s+EXEC\s`. Each hit is a step of the nearest JOB or PROC above it. Step name is the label. No label: name it `S001`, `S002` by its position among the unit's steps. If a name repeats inside one job, call the later ones `NAME#2`, `NAME#3`. Edge job to step, include, high, evidence the EXEC line.

**Fact: step runs a program.** Pattern: `^//([^*\s]\S*)?\s+EXEC\s+(\S*,)?PGM=[^,\s]+`. Read the name after `PGM=`. If a COBOL file in the tree has that PROGRAM-ID, the target is the bare name. Check with Grep `PROGRAM-ID\.\s+NAME\b` on the COBOL files. Otherwise the target is `ext:NAME`. Edge step to target, call, high. Trap: a PGM= name with `&` is a symbol. In a PROC step, fill it from the symbol table (section 4). If you cannot, write `ext:` with the raw text and say the symbol is not resolved. Utilities such as SORT, IEFBR14, IDCAMS, IEBGENER, IKJEFT01, DSNUTILB are `ext:` calls.

**Fact: step runs a PROC.** Pattern: `^//([^*\s]\S*)?\s+EXEC\s+(PROC=[A-Z0-9#@$]+|[A-Z#@$][A-Z0-9#@$]*([,\s]|$))`. The name is `PROC=NAME` or the first bare word. The PGM= pattern does not match these lines. Target `proc:NAME` if a PROC with that name was found (section 4), else `ext:NAME`. Edge step to target, call, high. DDs on this step with no `PROCSTEP.` prefix are ignored.

## 4. PROCs

**Find them.** Pattern: `^//([^*\s]\S*)?\s+(PROC|PEND)(\s|$)`. In a `.prc` or `.proc` file the PROC name is the file name without extension, whatever the PROC card says. In a `.jcl` file an in-stream PROC is named by the label on its PROC card. An in-stream PROC runs from `PROC` to `PEND`. After `PEND` you are back in the job. Read PROC files first. If two PROCs share a name, keep the first. Create node `proc:NAME` for each.

**Defaults.** `//NAME PROC A=1,B=2` gives defaults A=1, B=2.

**Symbols.** The EXEC card may carry `KEY=value` operands. Pattern: `^//([^*\s]\S*)?\s+EXEC\s+\S*,[A-Z0-9#@$]+=`. Skip PGM, PROC, PARM, COND, REGION, TIME, ACCT, ADDRSPC, DPRTY, DYNAMNBR, PERFORM, RD, CCSID, MEMLIMIT, PARMDD, and any key with a dot. The rest are symbols. Value order: EXEC card first, then PROC default. Replace `&NAME` and `&NAME.` in DSN and PGM values. A double period `&HLQ..DATA` leaves one period. Pattern to find use: `&[A-Z0-9#@$]+`. PARM values are not substituted.

**Expand.** For each EXEC PROC step, read the PROC's steps as children of the caller. Child id is `step:JOB.CALLSTEP.PROCSTEP`. Edge caller step to child: include, high, evidence two lines (the caller EXEC line, the PROC step line). Each child runs its PGM= as in section 3. The call edge to the program has the PROC step line as evidence, in the PROC file. A PROC step that itself calls a PROC is not expanded.

**Overrides.** Pattern: `^//[A-Z0-9#@$]+\.[A-Z0-9#@$]+\s+DD(\s|$)`. It sits in the job after the EXEC PROC card. `PROCSTEP.DDNAME` replaces only the parameters it names in that DD of that PROC step. Other parameters stay. If the PROC step has no such DD, the override adds one. The override line replaces the PROC DD line as evidence. In-stream data under an override belongs to that DD.

## 5. DD statements

**Find them.** Pattern for a DD with a DSN: `^//([^*\s]\S*)?\s+DD\s+(\S*,)?DSN(AME)?=[^,\s]+`. The DSN may sit on a continuation line. Pattern: `^//\s+(\S*,)?DSN(AME)?=`. DISP may also be on a continuation line: `^//\s+(\S*,)?DISP=`. Read the statement whole.

**Dataset name.** Take the value of DSN or DSNAME. Remove single quotes at the ends. Make it upper case. Fill symbols. Remove one trailing `(...)`: a GDG offset `(0)`, `(-1)`, `(+1)` or a member `(SORTCARD)`. Node `ds:NAME`. Absolute generations such as `.G0001V00` stay as written.

**Make no dataset for a DD when any of these holds:**
- DD name is STEPLIB, JOBLIB, SYSPRINT, SYSOUT, SYSUDUMP, SYSABEND, SYSDBOUT, SYSTSPRT, SYSMDUMP, CEEDUMP, or starts with SORTWK.
- The DD is `DD *` or `DD DATA`. Pattern: `^//([^*\s]\S*)?\s+DD\s+(\*|DATA)(\s|,|$)`.
- The DD has `SYSOUT=`, or `DUMMY` as a bare operand.
- No DSN. A referback such as `DSN=*.S1.OUT` is skipped.
- The DSN starts with `&&` (temporary).
- `DSN=NULLFILE`.
- A `&` symbol is left after filling.
Pattern to spot these: `DSN(AME)?=&&|\bDUMMY\b|DSN(AME)?=NULLFILE|SYSOUT=`.

**Concatenation.** A DD with a blank name continues the DD above it. It takes the same DD name. Pattern: `^//\s+DD\s`.

**DISP to mode.** Take the first subfield of DISP. Pattern: `DISP=\(?[A-Z]*`.

| First subfield | Mode |
|---|---|
| SHR | read |
| OLD | read |
| NEW | write |
| MOD | write |
| empty, as in `(,CATLG)` | write |
| anything else | write |
| no DISP | no mode, no step edge |

The second and third subfields (CATLG, DELETE, PASS, KEEP) are ignored. A utility step does not change this table. Its cards add separate facts (section 7).

**Edge 1: utility step to dataset.** Use it only when the step's program is not in the tree (it is `ext:`). For each usable DD with a DISP: edge step to `ds:DSN`, data, mode from the table, medium, note `mode inferred from DISP, the program is not in the tree`. Evidence: the DD line, plus the line each filled symbol came from. A DD read and a DD written on one dataset make two edges. Do not merge them into read_write.

**Edge 2: program to dataset.** Use it when the step's program is in the tree. Take each usable DD of the step. Match the DD name to a COBOL `SELECT ... ASSIGN TO ddname` in that program. On a match, edge program to `ds:DSN`, data, high. The mode comes from the COBOL OPEN and I/O verbs, never from DISP. Evidence: the COBOL SELECT and OPEN lines, then the DD line, then any symbol source line. If several steps run the program, do this for each step. If no JCL step in the tree has that DD name, the dataset is `ds:dd:PROG.DDNAME`, low, resolved false. That belongs to the COBOL recipes. Write no step data edge when the program is in the tree.

## 6. Step order

Walk the steps of one job in file order. Replace each EXEC PROC step by its child steps. Keep only steps that run a PGM. Drop EXEC PROC callers. For each neighbor pair write an edge, kind temporal, high, evidence the first step's line, then the second's. Steps that run `ext:` programs count. Job-level order only. Order is textual. IF and COND are not applied.

## 7. Utility steps

Read cards only for these programs: IDCAMS, IKJEFT01, IKJEFT1A, IKJEFT1B, DFSRRC00. The step may be a PROC step. In-stream cards sit under `DD *` or `DD DATA`, ended by `/*` or a `//` line. Cut each card at column 72. Remove `/* ... */` comments. A card ending in `-` or `+` continues on the next line. Join the pieces with one blank. The card's line is its first line.

**IDCAMS.** Patterns: `^\s*(DELETE|ALTER|DEFINE|REPRO|BLDINDEX|IMPORT|EXPORT)\b` on JCL files, and `\bNAME\s*\(\s*[A-Z0-9#@$]`. Per joined card, take the first rule that fits:
1. `DELETE name` or `ALTER name` or `DELETE (name)`. The name is the dataset. Verb DELETE or ALTER.
2. `DEFINE kind ... NAME(name)`. The first NAME( gives the dataset. Verb DEFINE.
3. REPRO, BLDINDEX, IMPORT, EXPORT. If `OUTFILE(dd)` is present, the dataset is that DD's DSN on this step. Else if `OUTDATASET(name)` is present, use that. Verb is the command. No target found: no fact.
Each gives a utility write: from the step, dataset `ds:NAME`, verb, evidence the card line. A name must start with a letter, digit, `#`, `@` or `$`. A quoted name or a `&` symbol gives no fact.

**TSO and DB2 (IKJEFT01, IKJEFT1A, IKJEFT1B).** Patterns: `\bRUN\s+PROG(RAM)?\s*\(` and `^\s*DSN\s+SYSTEM\s*\(`. `RUN PROGRAM(NAME)` gives a runtime-named start: from the step, to NAME (bare if it has source, else `ext:NAME`), how `TSO RUN PROGRAM`, evidence the card line. A card that starts `DSN SYSTEM(` gives a start of `ext:DSN`, how `DB2 command processor`. BIND and other subcommands give nothing.

**IMS (DFSRRC00).** Patterns: `PGM=DFSRRC00` and `PARM=\(?'?(DLI|DBB|BMP),`. Read PARM split by commas. If token 1 is DLI, DBB or BMP and token 2 is 1 to 8 name characters, that is a program start. How `IMS region PARM`, evidence the EXEC line. A `&` in the PARM gives nothing.

A runtime-named start is not an edge. Use it to mark the named program as run by that step. A utility write is not an edge. Use it to mark the dataset as changed by that step.

## 8. Worked examples

**06-contract-match.** `rg -n -i -e '^//([^*\s]\S*)?\s+(JOB|EXEC)\b|^//\S*\s+DD\s' app/jcl`
```
WRITEJOB.jcl:1 JOB   WRITEJOB.jcl:2 EXEC PGM=PGMW
WRITEJOB.jcl:3 OUTFILE DD DSN=SPARQ.TEST.MASTER,DISP=(NEW,CATLG,DELETE),
READJOB.jcl:2 EXEC PGM=PGMR   READJOB.jcl:3 INFILE DD DSN=SPARQ.TEST.MASTER,DISP=SHR
```
Write: `job:WRITEJOB` include `step:WRITEJOB.S1` (WRITEJOB.jcl:2); `step:WRITEJOB.S1` call `PGMW` (:2); same for READJOB and PGMR. PGMW and PGMR have source, so use Edge 2. SELECT OUT-FILE ASSIGN TO OUTFILE matches DD OUTFILE: `PGMW` data write `ds:SPARQ.TEST.MASTER`, high, evidence PGMW.cbl:6, PGMW.cbl:13, WRITEJOB.jcl:3. Reader: read, PGMR.cbl:6, :13, READJOB.jcl:3. No step data edge. Fixture 07 is identical in JCL. Only the copybooks differ, so the contract edge is medium.

**08-temporal-steps.** `rg -n -i -e '^//([^*\s]\S*)?\s+EXEC\s' app/jcl`
```
SEQJOB.jcl:2 STEP1 PGM=PGMA   :3 STEP2 PGM=PGMB   :4 STEP3 PGM=PGMC   :5 STEP2 PGM=IEFBR14
```
The last STEP2 repeats, so it is `STEP2#2`. Edges: job include each step (`step:SEQJOB.STEP2#2` at :5); STEP1 call PGMA, STEP2 call PGMB, STEP3 call PGMC, `STEP2#2` call `ext:IEFBR14`; temporal STEP1 to STEP2 (:2, :3), STEP2 to STEP3 (:3, :4), STEP3 to `STEP2#2` (:4, :5).

**16-proc-expansion.** `rg -n -i -e '^//\S*\s+(EXEC|PROC|PEND|DD)\b' app/jcl app/proc`
```
RUNPROC.jcl:2 S1 EXEC PROC=COPYPROC,INDSN=SPARQ.OVERRIDE.IN
RUNPROC.jcl:3 CP01.OUTFILE DD DSN=SPARQ.OVERRIDE.OUT,DISP=(NEW,CATLG)
RUNPROC.jcl:4 S2 EXEC PGM=IEFBR14
COPYPROC.prc:1 PROC INDSN=SPARQ.DEFAULT.IN  :2 CP01 EXEC PGM=PGMCOPY
COPYPROC.prc:3 INFILE DD DSN=&INDSN,DISP=SHR  :4 OUTFILE DD DSN=SPARQ.PROC.OUT,DISP=(NEW,CATLG)
```
Write: `step:RUNPROC.S1` call `proc:COPYPROC` (:2); include `step:RUNPROC.S1.CP01` (RUNPROC.jcl:2, COPYPROC.prc:2); `step:RUNPROC.S1.CP01` call `PGMCOPY` (COPYPROC.prc:2); `step:RUNPROC.S2` call `ext:IEFBR14`; temporal CP01 to S2 (COPYPROC.prc:2, RUNPROC.jcl:4); S1 is a caller, so no temporal edge starts at it. `&INDSN` comes from the EXEC card, so INFILE is `ds:SPARQ.OVERRIDE.IN`. PGMCOPY reads it: evidence PGMCOPY.cbl:6, :15, COPYPROC.prc:3, RUNPROC.jcl:2. The override replaces DSN on OUTFILE, so PGMCOPY writes `ds:SPARQ.OVERRIDE.OUT`: PGMCOPY.cbl:7, :16, RUNPROC.jcl:3. `ds:SPARQ.PROC.OUT` and `ds:SPARQ.DEFAULT.IN` get no edge.

**24-dsn-forms.** `rg -n -i -e '^//([^*\s]\S*)?\s+DD\s' app/jcl`
```
:3 SORTIN DD DSN=SPARQ.GDG.BASE(0),DISP=SHR     :4 SORTOUT DD DSN=SPARQ.GDG.BASE(+1),DISP=(NEW,CATLG)
:5 SYSIN DD DSN=SPARQ.CNTL(SORTCARD),DISP=SHR   :6 WORK DD DSN=&&TEMP,DISP=(NEW,PASS)
:7 DUMMYDD DD DUMMY   :8 NULLDD DD DSN=NULLFILE   :9 SYSOUT DD SYSOUT=*
```
SORT has no source, so `step:DSNJOB.S1` call `ext:SORT` (:2) and Edge 1 applies: `ds:SPARQ.GDG.BASE` data read medium (:3); `ds:SPARQ.GDG.BASE` data write medium (:4); `ds:SPARQ.CNTL` data read medium (:5). Lines 6 to 9 make nothing. Two separate edges to one dataset.

**26-wave-seed-families.** `rg -n -i -e 'EXEC\s+PGM=|DISP=' app/jcl`
```
LOADJOB.jcl:2 IDCAMS  :3 MASTOUT DISP=OLD     SETUP.jcl:2 IEFBR14  :3 D1 DISP=(NEW,CATLG,DELETE)
UPDJOB.jcl:3 OUTFILE DISP=OLD (PGMUPD, in tree)   RPTJOB.jcl:3 INFILE DISP=SHR, :4 REPORT DISP=(NEW,...)
```
`step:LOADJOB.S1` call `ext:IDCAMS`; data read medium `ds:SPARQ.TEST.MASTER` (:3), since OLD reads. `step:SETUP.S1` call `ext:IEFBR14`; data write medium `ds:SPARQ.TEST.SCRATCH` (:3). UPDJOB runs PGMUPD, which has source: no step edge. PGMUPD data write `ds:SPARQ.TEST.MASTER`, evidence PGMUPD.cbl:6, :12, UPDJOB.jcl:3. DISP=OLD is ignored there. RPTJOB: PGMRPT reads `ds:SPARQ.TEST.MASTER` (RPTJOB.jcl:3) and writes `ds:SPARQ.TEST.REPORT` (RPTJOB.jcl:4).

**29-utility-facts.** `rg -n -i -e '^\s*(DELETE|DEFINE|REPRO)\b|RUN\s+PROG|^\s*DSN\s+SYSTEM|PGM=DFSRRC00' app/jcl`
```
LOADMAST.jcl:7 DELETE SPARQ.TEST.MASTER -   :9 DEFINE CLUSTER (NAME(SPARQ.TEST.MASTER) -   :11 REPRO INFILE(INFILE) OUTFILE(OUTFILE)
DB2JOB.jcl:5 DSN SYSTEM(DB2P)   :6 RUN PROGRAM(PGMSQL) PLAN(PLANX)   BINDJOB.jcl:4 DSN SYSTEM(DB2P)
IMSJOB.jcl:2 EXEC PGM=DFSRRC00,PARM='DLI,PGMIMS,PSBX'
```
Edges: `step:LOADMAST.S1` call `ext:IDCAMS`; data read medium `ds:SPARQ.TEST.FLAT` (:4) and `ds:SPARQ.TEST.MASTER` (:5, DISP=OLD). Utility writes on `ds:SPARQ.TEST.MASTER`: DELETE (:7), DEFINE (:9), REPRO (:11, OUTFILE(OUTFILE) is DD OUTFILE). `step:DB2JOB.S1` and `step:BINDJOB.S1` call `ext:IKJEFT01`; `step:IMSJOB.S1` calls `ext:DFSRRC00`. Runtime-named starts: DB2JOB.S1 to `ext:DSN` (:5), to `PGMSQL` (:6); BINDJOB.S1 to `ext:DSN` (:4); IMSJOB.S1 to `PGMIMS` (:2). The BIND card gives nothing. Mark PGMSQL and PGMIMS as run, not dead.

**27-jcl-text-in-cobol.** `rg -n -i -e '^//\S*\s+EXEC' app` finds only MAINJOB.jcl:2 and LATERPRC.prc:2. PGMMAIN.cbl:6 holds `"//STEP1 EXEC PROC=LATERPRC"` in a literal. Nothing starts at column 1 there, so the pattern skips it. Write no edge from it. Keep `proc:LATERPRC` and `PGMLATER` as unknown reachability, not dead.

## 9. Not covered

- SORT control cards and other in-stream control cards (ICETOOL, IEBGENER, FTP).
- IF/THEN/ELSE, COND=, RESTART. Order is textual.
- Nested PROC calls, INCLUDE members, JCLLIB search order, `PARM.step=` overrides, DD overrides that name a step through a PROC call two levels deep.
- Jobs submitted through the internal reader (`SYSOUT=(,INTRDR)`, `IEBGENER` to a reader, or a COBOL literal holding JCL). Report them as limits.
- Quoted or symbolic names on IDCAMS cards. INFILE/INDATASET on REPRO, LISTCAT, PRINT, EXPORT targets other than OUTFILE/OUTDATASET.
- DB2 BIND, DSNTEP2 or DSNUTILB control cards. They are `ext:` calls only.
- IMS PSB names, and any DFSRRC00 PARM with a symbol.
- Scheduler files that submit jobs (Control-M, shell). See the scheduler recipes.
- Programs in assembler, PL/I or other languages. A step that runs one is still an `ext:` or bare call.
