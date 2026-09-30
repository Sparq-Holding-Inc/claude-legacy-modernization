# How the CardDemo draft truth is labeled

Status: DRAFT. Every label is unconfirmed until Gary reviews it.

This file is the labeling guide. The labelers were separate Claude subagents.
They read the CardDemo source directly. They never saw the extractor code or
its output. Each COBOL partition was labeled twice, independently. The two
passes were compared and every disagreement was settled by reading the source
(see `ADJUDICATION.md`).

## Rules for a labeler

1. Do not open, run or read anything under `skills/`, `hooks/`, or
   `evals/*.py` in the plugin folder. Do not read other labelers' files in
   `evals/carddemo/labels/`.
2. Read the source. Use `grep`, `sed`, `cat`. You may write throwaway scripts
   in your own scratch space to count or list things. Check what a script
   tells you against the source lines before you trust it.
3. Be exhaustive. Missing an edge counts against the extractor as a false
   alarm, so a gap in the truth hurts the wrong party.
4. When something is unclear, label your best reading and write the
   file:line and your doubt in `notes`.

## Benchmark

Root: `/Users/phillipmorehead/Legacy Modernization Assessor Plugin/bench/carddemo`
(AWS CardDemo, commit `59cc6c2fd7ebd7ef7925cad552a01a4b8b6e4d5e`).
All paths in labels are relative to that root, for example `app/cbl/COSGN00C.cbl`.

In scope: `app/cbl`, `app/cpy`, `app/cpy-bms`, `app/bms`, `app/jcl`,
`app/proc`, `app/csd`, `app/scheduler`, and `scripts/*.sh`.

Out of scope, do not label: `app/app-*` (IMS, DB2, MQ extensions), `app/asm`,
`app/maclib`, `app/ctl`, `app/data`, `app/catlg`, `samples`.

## Node ids

| Kind | Id | Example |
|---|---|---|
| COBOL program | the PROGRAM-ID, upper case | `CBTRN02C` |
| copybook | `cpy:` + name | `cpy:CVTRA05Y` |
| JCL job | `job:` + job name | `job:POSTTRAN` |
| JCL step | `step:JOB.STEP` | `step:POSTTRAN.STEP15` |
| step inside a PROC call | `step:JOB.STEP.PROCSTEP` | `step:TRANREPT.STEP05R.PRC001` |
| repeated step name in one job | add `#2`, `#3` | `step:TRANREPT.STEP05R#2` |
| PROC | `proc:` + name | `proc:REPROC` |
| dataset | `ds:` + DSN | `ds:AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS` |
| DD not mapped by any JCL | `ds:dd:PROGRAM.DDNAME` | `ds:dd:CBACT01C.ACCTFILE` |
| Control-M job | `sch:FOLDER_NAME/JOBNAME` | `sch:DAILY-TransactionBackup/CLOSEFIL` |
| shell wrapper | `sch:` + path | `sch:scripts/run_full_batch.sh` |
| name not in scope | `ext:` + name | `ext:CEEDAYS`, `ext:DFHAID`, `ext:IDCAMS` |
| computed target | `?dynamic:PROGRAM:LINE` | `?dynamic:COMEN01C:149` |

A name is a program in scope when a file in `app/cbl` has that PROGRAM-ID.
A name is a copybook in scope when `app/cpy` or `app/cpy-bms` holds a file with
that stem, ignoring case.

## Edge kinds

Every edge has `src`, `dst`, `kind`, `mode`, `resolved`, `evidence` (a list of
`{file, line}`) and an optional `note`. `mode` is null except on data edges.

The evidence line is the first physical line of the statement, for example the
line holding `EXEC CICS XCTL`, `CALL`, `COPY` or `SELECT`. When several
statements produce the same edge, list each one once.

### call

* `CALL 'X'`, `EXEC CICS LINK PROGRAM('X')`, `EXEC CICS XCTL PROGRAM('X')`:
  program to program `X` (or `ext:X`). `resolved` true.
* `EXEC PGM=X` in JCL: step to program `X` (or `ext:X`).
* `EXEC PROC=X` or `EXEC X` in JCL: step to `proc:X`.
* Control-M job to the JCL job named in `MEMNAME`: `sch:` to `job:`.
* Shell wrapper to each JCL job it submits: `sch:` to `job:`.

Variable targets. A target that is a data name, not a literal, follows these
rules. Apply them per program.

1. **Constant.** The name has a `VALUE` literal in working storage (or a
   copybook the program copies) AND is never the receiving field of a MOVE,
   STRING, READ INTO, ACCEPT or similar anywhere in the program. Treat it as
   that literal. One edge, `resolved` true.
2. **Literal moves.** Any `MOVE 'LIT' TO name` in the program, and any
   `MOVE const TO name` where `const` is a constant under rule 1, gives one
   candidate edge per distinct literal. `resolved` true, and `note` says
   `via <name>`. Do not try to follow control flow. Every literal moved to the
   name counts.
3. **Dynamic remainder.** If the name is not a pure constant (rule 1), ALSO
   emit one edge to `?dynamic:PROGRAM:LINE` with `resolved` false, where LINE
   is the line of the CALL or XCTL. The target set is not proven complete.
   If there are no literal moves at all, the dynamic edge is the only edge.
4. **Subscripted names** such as `NAME(IDX)` are dynamic only. No candidates.

### include

* `COPY NAME` in a program or copybook: to `cpy:NAME`, or `ext:NAME` when the
  copybook is not in scope. One edge per (source, copybook). Give every COPY
  statement as evidence.
* `job:X` to each of its top-level steps `step:X.S`.
* A PROC call step to each expanded proc step (`step:JOB.S` to
  `step:JOB.S.P`).

### data

Program to dataset. `mode` is `read`, `write` or `read_write`.

Batch programs (SELECT and ASSIGN):

* The DD name is the ASSIGN target. If it has hyphens (`UT-S-NAME`), use the
  part after the last hyphen.
* Mode comes from the OPEN statements for that file across the whole
  program. INPUT gives read. OUTPUT or EXTEND gives write. I-O gives
  read_write. A mix of read and write gives read_write. A file that is
  selected but never opened gets no edge.
* The dataset is found in JCL. Find every step that runs the program, either
  `EXEC PGM=<program>` or inside a PROC. Find the DD with the same name in
  that step. A DD in the calling job named `PROCSTEP.DDNAME` overrides the
  proc's own DD. Take its `DSN`, drop a trailing `(...)` (GDG generation or PDS
  member), and use `ds:<DSN>`. Symbolic parameters like `&CNTLLIB` take the
  value from the EXEC statement or the PROC defaults.
* One edge per (program, dataset). If the program runs in several steps with
  different DSNs, emit one edge for each.
* If no step runs the program, or the DD is missing from the step, use
  `ds:dd:PROGRAM.DDNAME` with `resolved` false.
* Skip DD statements that are `DUMMY`, `SYSOUT=`, in-stream (`*` or `DATA`),
  temporary (`&&NAME`) or `DSN=NULLFILE`.

Online programs (`EXEC CICS`):

* `READ`, `STARTBR`, `READNEXT`, `READPREV`, `ENDBR`, `RESETBR`: read.
  `WRITE`, `REWRITE`, `DELETE`: write. A program that does both: read_write.
  `READ ... UPDATE` counts as read. The `REWRITE` that follows counts as write.
* The file name is `FILE(...)` or `DATASET(...)`. A variable follows the
  variable-target rules above (constant, literal moves, dynamic).
* A CICS file name maps to a DSN through `DEFINE FILE(name) DSNAME(dsn)` in
  `app/csd`. Use `ds:<DSN>`. If the CSD has no entry, use `ds:<FILENAME>`.
* A dynamic file name gives an edge to `?dynamic:PROGRAM:LINE` with mode set
  and `resolved` false.

Each data edge also carries `layout_copybooks`: a list of `cpy:` ids, empty if
none can be found. A layout copybook is one of:

* a `COPY` inside the file's `FD` entry, or
* the copybook that defines the 01-level record used in `READ f INTO rec`,
  `WRITE fd-rec FROM rec`, `REWRITE fd-rec FROM rec`, or CICS `INTO(rec)` or
  `FROM(rec)`. Open the copybooks to see which one defines `01 rec`.

JCL steps whose program is NOT in scope (`ext:` programs such as IDCAMS or
SORT) get data edges from the step instead: `step:` to `ds:`. Mode from DISP:
NEW or MOD gives write. OLD or SHR gives read. No DISP: skip and note it.
Skip STEPLIB, JOBLIB, SYSPRINT, SYSOUT, SYSUDUMP, SYSABEND, SYSDBOUT,
SYSTSPRT and the DD types skipped above. Do not read in-stream IDCAMS control
cards. Only DD statements count. Give a note that says so.

### contract

Not labeled by hand. It is derived from the data edges by rule: for each
dataset, every program that writes it (write or read_write) pairs with every
other program that reads it (read or read_write). The edge runs writer to
reader. Confidence is high when the two `layout_copybooks` lists share a
copybook, otherwise medium. See `derive_contract.py`.

### temporal

* Inside one JCL job: each executable step to the next executable step, in
  file order. A PROC call step is a container, so use its expanded steps in
  its place. Only `EXEC PGM=` steps are executable.
* Control-M: job A to job B when A has `<OUTCOND NAME="N" ... SIGN="+"/>` and
  B has `<INCOND NAME="N" .../>`. Ignore `SIGN="-"`. Match on NAME alone.
  Folder level OUTCOND elements belong to the folder, not a job: ignore them.
  Edge is `sch:` to `sch:`.
* Shell wrapper: a line that names a JCL file (`put jcl/CLOSEFIL.jcl`) is a
  submit. Consecutive submits in file order give `job:A` to `job:B`. Skip
  comment lines. Skip references built from variables.

## Fixed format COBOL

* Columns 1 to 6 are sequence numbers. Column 7 is the indicator: `*` or `/`
  is a comment, `-` continues the previous line. Code lives in columns 8 to
  72. Columns 73 to 80 are noise.
* A statement can span lines. Give the first line.
* A keyword inside a string literal is not a statement. `'GNP CALL FAILED'`
  is not a call.

## Not labeled

Maps (`app/bms`) get no edges. `EXEC CICS SEND MAP`, `RETURN TRANSID`, IMS,
MQ and DB2 are out of scope. Do not label them.

## Output

Write one JSON file to the path you were given.

```json
{
  "partition": "O1",
  "pass": "A",
  "programs": {
    "COACTUPC": {"path": "app/cbl/COACTUPC.cbl", "program_id": "COACTUPC", "has_exec_cics": true}
  },
  "nodes": [ {"id": "job:POSTTRAN", "unit_type": "jcl_job", "entry_point": true} ],
  "edges": [
    {"src": "COACTUPC", "dst": "cpy:CSMSG01Y", "kind": "include", "mode": null,
     "resolved": true, "evidence": [{"file": "app/cbl/COACTUPC.cbl", "line": 123}], "note": ""},
    {"src": "COACTUPC", "dst": "ds:AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS", "kind": "data",
     "mode": "read_write", "resolved": true, "layout_copybooks": ["cpy:CVACT01Y"],
     "evidence": [{"file": "app/cbl/COACTUPC.cbl", "line": 3900}], "note": "FILE(LIT-ACCTFILENAME) is ACCTDAT, CSD DSNAME"}
  ],
  "entry_points": [ {"id": "COSGN00C", "via": "CSD TRANSACTION(CC00)", "evidence": [{"file": "app/csd/CARDDEMO.CSD", "line": 378}]} ],
  "unparsed": [ {"file": "app/scheduler/CardDemo.ca7", "reason": "CA-7 is not Control-M"} ],
  "notes": ["anything odd, with file:line"]
}
```

Leave out keys you do not use. Finish by printing how many edges of each kind
you labeled.
