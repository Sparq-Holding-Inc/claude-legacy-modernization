# Graph model

How you assemble `graph.json` from recipe hits. The recipes say what to search for. This file says what to do with the hits: which node to make, which id it gets, which edge to write, how to resolve a target, and what to record when you cannot.

Rule zero: write an edge only for a line you saw. Evidence is `{"file", "line"}`, path relative to the scanned root, forward slashes, line from the hit.

## 1. File kinds

Glob the tree once. Skip folders `.git`, `.hg`, `.svn`, `node_modules`, `.venv`, `venv`, `modernization-assessment`. Sort paths. Extensions are matched without regard to case.

| Kind | Extensions | Content check |
|---|---|---|
| COBOL program | `.cbl .cob .cobol .pco .cbx` | needs a `PROGRAM-ID` |
| Copybook | `.cpy .copy` | none |
| JCL job | `.jcl .job` | a `//NAME JOB` card makes a job |
| PROC | `.prc .proc` (also an in-stream `//NAME PROC`) | none |
| BMS map | `.bms` | none |
| CICS system definition | `.csd` | none |
| Control-M XML | `.xml .ctm .controlm` | `<DEFTABLE`, `<FOLDER` or `<SMART_FOLDER` near the top |
| Shell wrapper | `.sh .ksh .bash` | see the scheduler recipes |

Content checks (case-insensitive):

```
PROGRAM-ID\.?[[:space:]]+[A-Z0-9][A-Z0-9_-]*
>>[[:space:]]*SOURCE[[:space:]]+FORMAT[[:space:]]+(IS[[:space:]]+)?FREE
^//[^[:space:]]*[[:space:]]+(JOB|PROC)\b
^[^[:space:]]+[[:space:]]+DFHMSD\b
```

Rules:
- A free-format COBOL file is not parsed. Add to `unparsed`.
- A COBOL file with no `PROGRAM-ID` is not parsed. Add to `unparsed`.
- A second program with a `PROGRAM-ID` already seen, or a second copybook with the same member name, is a duplicate. The first path in sorted order wins. Add the other to `unparsed` as kind `duplicate`.
- A JCL file that holds no JOB card and is not a `.prc/.proc` file is read as a job named for its file stem.
- The map name is the label before `DFHMSD`, else the file stem.
- Files of these types are never read: `.asm .mac` (assembler), `.ddl .dcl .sql` (DB2), `.dbd .psb` (IMS), `.ctl` (control cards), `.pli .pl1` (PL/I), `.rexx .rex` (REXX), `.nat` (Natural). Add one `unparsed` entry per extension: kind `unread`, file the first path, reason "N file(s) of type .ext (what) are not read. Also: <two more paths>". Files with no extension or an unknown one that look like source are listed the same way.

## 2. Nodes

Every node has: `id`, `path`, `unit_type`, `lang`, `loc`, `last_modified`, `entry_point`. Optional: `line`, `note`, `entry_evidence`.

| Thing | id | unit_type | lang |
|---|---|---|---|
| COBOL program | bare `PROGRAM-ID`, upper case | `online_txn`, `batch` or `subprogram` | cobol |
| Copybook | `cpy:MEMBER` (file stem) | copybook | cobol |
| BMS map | `map:NAME` | map | bms |
| JCL job | `job:NAME` (JOB card label) | jcl_job | jcl |
| JCL step | `step:JOB.STEP`, proc step `step:JOB.STEP.PROCSTEP`, repeat `step:JOB.STEP#2`, no name `S001` by position | jcl_step | jcl |
| PROC | `proc:NAME` (file stem for `.prc/.proc`, else the PROC label) | proc | jcl |
| Dataset | `ds:DSN`; unmapped DD `ds:dd:PROGRAM.DDNAME`; DB2 table `ds:db2:TABLE` | dataset | null |
| Scheduler job | `sch:FOLDER/JOB`; wrapper `sch:<path>` | scheduler_job | scheduler |
| Not in the tree | `ext:NAME` | external | null |
| Computed target | `?dynamic:SOURCE:LINE` | external | null |

- Upper-case every name. Names collide across kinds, so the prefix is not optional.
- `path` is the file, or null for datasets, `ext:` and `?dynamic:` nodes and for a job that is not in the tree. A step's path is the file holding the `EXEC` line (the PROC file for a proc step), with `line` set. A step has loc 0.
- `loc`: count lines. COBOL and copybooks: lines with a non-blank code area. Use Grep count mode with `^.{6}[^*/].{0,64}[^ ]`. Other files: non-blank lines, count mode with `\S`. Write 0 for steps and datasets. A count is approximate. Say so in `meta.limits`.
- `last_modified`: null unless you hold a date (section 9).
- `entry_point`: see section 6.
- A copybook is a node even if no program uses it, so that unused copybooks can be listed.
- Create a node when the first hit needs it. If an edge points to an id with no node, make an `external` node for it with note "referenced but never defined".

## 3. Edges

Fields: `src`, `dst`, `kind`, `mode`, `evidence` (non-empty), `resolved`, `confidence`, `note`.

| kind | from -> to | what you saw |
|---|---|---|
| call | program -> program | `CALL`, `EXEC CICS LINK`, `EXEC CICS XCTL` |
| call | step -> program | `EXEC PGM=` |
| call | step -> proc | `EXEC PROC=` or `EXEC name` |
| call | scheduler job -> job | MEMNAME, or a submit in a wrapper |
| include | program or copybook -> copybook | `COPY`, `EXEC SQL INCLUDE` |
| include | job -> step, step -> proc step | containment |
| data | program -> dataset | a file the program opens, a CICS file call, an SQL table |
| data | step -> dataset | only when the step's program has no source in the tree |
| contract | program -> program | writer to reader of one dataset |
| temporal | step -> step | executable steps of one job, in file order |
| temporal | scheduler job -> scheduler job, job -> job | scheduler recipes |

Rules:
- Only `data` edges carry `mode` (`read`, `write`, `read_write`). Others have null.
- One edge per `(src, dst, kind, mode)`. A second hit adds its evidence to the first. The higher confidence wins. Notes are joined with "; ".
- Evidence is sorted by file then line, with no repeats.
- A `COPY` inside a copybook is an `include` from the copybook, cited at its own line. A statement that sits in a copybook but is read by a program carries two evidence entries: the line in the copybook and the `COPY` line in the program.
- `COPY REPLACING` is not applied. A copybook counts as written.
- Step order: use the executable steps (those with a program), including steps inside a proc, in file order. The step that calls a proc is not itself in the order.
- Step to dataset edges use the first DISP value: `OLD` or `SHR` is `read`, anything else is `write`, no DISP is no edge. Confidence medium, note "mode inferred from DISP, the program is not in the tree". Skip these DDs: STEPLIB, JOBLIB, SYSPRINT, SYSOUT, SYSUDUMP, SYSABEND, SYSDBOUT, SYSTSPRT, SYSMDUMP, CEEDUMP, SORTWK*, in-stream data, SYSOUT=, DUMMY, no DSN, `&&temp`, an unresolved `&SYMBOL`, `*.stepref`, NULLFILE. Drop a `(member)` suffix from a DSN.
- Program to dataset edges for a batch file need the whole chain: `SELECT ... ASSIGN TO ddname`, the `OPEN` mode, a JCL step that runs this program with a DD of that name. Mode: `INPUT` read, `OUTPUT` or `EXTEND` write, `I-O` read_write. Evidence: the SELECT line, the OPEN line, the DD line. Confidence high. Strip the prefixes `UT-S-`, `DA-S-`, `AS-S-`, `UT-A-`, `DA-A-`, `S-`, `AS-`, `UT-`, `DA-` from the ASSIGN name. Several steps run the program: one edge per dataset, modes merged.
- If no step in the tree maps the DD: dataset `ds:dd:PROGRAM.DDNAME`, edge resolved false, confidence low, note "DD x is not mapped by any JCL in the tree".
- CICS file calls: the file name resolves through a CSD `DEFINE FILE ... DSNAME(...)` to `ds:DSNAME`. No definition: `ds:FILENAME`, note "CICS file X, no CSD DEFINE FILE found". `READ`, `READNEXT`, `READPREV`, `STARTBR`, `ENDBR`, `RESETBR`, `UNLOCK` are read. `WRITE`, `REWRITE`, `DELETE` are write.
- SQL: `ds:db2:TABLE`, table from `FROM`, `JOIN` (read), `INSERT INTO`, `UPDATE` (write), `DELETE FROM` (write only). Mode read_write if both. Confidence high.

## 4. Resolving targets

- Case: upper-case every name before you compare it.
- Program: match a call literal to a node by `PROGRAM-ID`, not by file name. Trim spaces. `PGM=` and `LINK PROGRAM(...)` the same way.
- Copybook: match `COPY NAME` to a copybook file stem anywhere in the tree. There is no library search order. If two files share a stem, the first sorted path was kept. `COPY 'NAME'` in quotes is the same.
- PROC: match to a `.prc/.proc` file stem or an in-stream PROC label.
- No match: point to `ext:NAME` and create that node. The edge stays `resolved` true, confidence unchanged. Note: "program not in the scanned tree", "copybook not in the scanned tree" or "cataloged PROC not in the scanned tree". System names (CEEDAYS, IDCAMS, IEFBR14, SQLCA, DFHAID) all land here.
- Computed target (`CALL WS-NAME`, `PROGRAM(WS-NAME)`): see section 5.
- Dataset names: strip quotes, drop a trailing `(member)`, fill `&SYMBOL.` from the EXEC parameters, then the PROC defaults. If a symbol stays, skip the DD.

## 5. Dynamic calls

For a variable target, work these rules in order:
1. Constant. The name has a `VALUE` literal and nothing in the program moves, reads or accepts into it. Treat it as that literal. Edge to the target, confidence high, note "via constant NAME", evidence the call line plus the VALUE line.
2. Literal moves. Every literal moved into the name is a candidate. One edge each, confidence medium, note "via NAME, a literal is moved to it". Evidence: call line plus each MOVE line.
3. Remainder. Unless rule 1 held, the set may be incomplete. Also write an edge to `?dynamic:SOURCE:LINE`: kind as the call (`call`, or `data` with a mode for a CICS file name), `resolved` false, confidence low, note "target NAME is computed", plus "; the literals found may not be all of them" when rule 2 found some.
4. A subscripted name (`WS-TAB(3)`) is rule 3 only.

SOURCE is the program id. If the statement lives in a copybook, SOURCE is `PROGRAM/COPYBOOKSTEM`. LINE is the line in the file where the statement starts. Create the node once, note "computed target, cannot be resolved statically". Computed calls are never dropped. List each one in `analysis.unresolved_dynamic` as `{"src", "dst", "evidence"}`.

## 6. Entry points and unit types

Entry points (`entry_point` true):
- Every JCL job that has a file in the tree.
- Every scheduler job and every wrapper node.
- Every program named in a CSD `DEFINE TRANSACTION ... PROGRAM(x)`. Set `entry_evidence` to the CSD line and note "CSD transaction TXN". If the program has no source, the `ext:` node gets the flag.
- A placeholder job (JCL not in the tree) is not an entry point.

Program unit_type, first rule that holds:
1. `online_txn`: it holds `EXEC CICS`, or a CSD `DEFINE PROGRAM` or a transaction names it.
2. `batch`: a step in the tree runs it, directly or through a proc.
3. `subprogram`: another program in the tree calls it, with a call edge between two different programs.
4. `batch`.

## 7. Facts that make no edge

These go into `analysis`, not into `edges`.

Embedded JCL. A COBOL literal that holds JCL text can be submitted at run time. Search COBOL files:

```
//[A-Z0-9#@$]*[[:space:]]+EXEC\b
```

Read the line. If it sits in a quoted literal and names `PROC=NAME`, `PGM=NAME` or a bare `NAME` (a bare name is a proc), keep it. A literal can continue on the next line with a `-` in column 7: read it whole. Keep only names that match a proc or a program in the tree. Write `{"src": program, "dst": "proc:NAME" or program, "evidence": {file, line}}` once per program and target, in `analysis.embedded_jcl`. The target and the programs its proc runs are `unknown` in dead code, never `unreachable`.

Runtime-named programs. Read these in JCL:
- `EXEC PGM=DFSRRC00` with `PARM='DLI,PROG,...'` (or `DBB`, `BMP`): the second item is the program. How: "IMS region PARM".
- `EXEC PGM=IKJEFT01` (or `IKJEFT1A`, `IKJEFT1B`) with an in-stream card `RUN PROGRAM(NAME)` or `RUN PROG(NAME)`: how "TSO RUN PROGRAM". A card starting `DSN SYSTEM(` names `DSN`, how "DB2 command processor".

```
RUN[[:space:]]+PROG(RAM)?[[:space:]]*\(
^[[:space:]]*DSN[[:space:]]+SYSTEM[[:space:]]*\(
PGM=(DFSRRC00|IKJEFT01|IKJEFT1A|IKJEFT1B)
```

Write `{"src": "step:ID", "dst": program id if the program is in the tree else "ext:NAME", "how", "evidence"}` in `analysis.runtime_named`. No edge. For reachability the program counts as reached from that step. The step is not recorded as running it, so its DD names stay unmapped (section 3).

Utility writes. In an `IDCAMS` step, read the in-stream cards. A card ends at a line that does not end in `-` or `+`. Join continuations. Ignore text after column 72 and `/* */` comments.

```
^[[:space:]]*(DELETE|ALTER|DEFINE|REPRO|BLDINDEX|IMPORT|EXPORT)\b
```

- `DELETE x` or `ALTER x`: dataset x, verb as written.
- `DEFINE CLUSTER (NAME(x) ...`: dataset x, verb DEFINE.
- `REPRO`, `BLDINDEX`, `IMPORT`, `EXPORT`: dataset of `OUTFILE(dd)` through that DD's DSN, else `OUTDATASET(x)`.
- Skip any name with `&`.

Write `{"src": "step:ID", "dst": "ds:DSN", "verb", "evidence"}` in `analysis.utility_writes`. The step's own data edge still comes from DISP (so it reads as a read). The utility write is the only sign it writes.

## 8. Contract edges

A contract edge says: this program writes a record, that program reads it, through one dataset. The record layout is an undocumented interface.

Method:
1. For each program and dataset, merge the data edges to one record: modes (`read_write` counts as both), evidence, and layouts.
2. Layouts: the copybooks that define the record of that file. These are copybooks pulled in under the file's `FD`, and copybooks that define the 01 record named in `READ file INTO rec`, `WRITE rec FROM x`, or CICS `INTO(rec)`/`FROM(rec)`. A record the program declares itself has no layout.
3. For every dataset except `ds:db2:*`: writers are programs whose modes include write, readers include read.
4. For every writer W and reader R with W different from R, write `W -> R`, kind `contract`:
   - Confidence high, if the layout sets share a copybook. Note "DSN: same layout copybook NAME on both sides".
   - Confidence medium otherwise. Note "DSN: same dataset, layout copybooks differ or are unknown (writer [..], reader [..]). Verify by hand."
   - Evidence: all of the writer's and the reader's evidence for that dataset.
   - Two datasets joining the same pair: one edge, evidence merged, the higher confidence, notes joined.

High means a shared layout copybook. It does not prove the program reads the record through it. Say so in `meta.limits`.

Example. Program PGMW writes `ds:SPARQ.TEST.MASTER` with `COPY LAYOUTX` under its FD. PGMR reads it with `COPY LAYOUTX` under its FD. Edge `PGMW -> PGMR` contract high. If PGMR copied `LAYOUTY`, the same edge is medium.

## 9. Dormancy

A node is dormant when it is reachable from an entry point, is a program or copybook, and its last-modified date is more than N years before the as-of date. N is 5 unless the user says otherwise. As-of is today unless the user gives a date.

You cannot read git history. So `last_modified` is null on every node, unless the user supplies dates (a paste of per-file last-commit dates, a `git log` listing, a CSV). Dates in source comments or change logs are not last-modified dates. Do not use them for this.

Without dates:
- Leave `analysis.dead_code_candidates.dormant` empty.
- Add the warning: "No last-modified dates exist. The dormant bucket was NOT computed. An empty dormant list means not measured."
- Set `meta.git_dates` false. Set `analysis.dormant_years` and `analysis.as_of` anyway.
- In `dead-code.json`, give the dormant bucket as empty and say "not measured".

With dates: write `YYYY-MM-DD` to each node, compute the bucket, and write each reason as "reachable, last modified DATE, older than N years".

## 10. Reachability and dead code buckets

Walk `call` and `include` edges from every entry point. Add the program a runtime-named record points to. Reached means visited. Candidates are programs, copybooks and procs.

- No entry point in the tree: nothing is unreachable. Every candidate is `unknown`, reason "no entry points in the tree", and a warning says so.
- A reachable computed call exists: every unreached program is `unknown`, and so is every copybook or proc that such a program reaches. Reason names the first computed call. The rest stay `unreachable`.
- Embedded JCL from a reachable program: its target and the programs its proc runs move from `unreachable` to `unknown`. Warn: "N proc or program(s) are named only in JCL text inside COBOL. No edge exists, so they are unknown, not unreachable."
- Otherwise unreached is `unreachable`, reason "no static path from any entry point and no reachable computed call in the tree".

## 11. Unparsed, limits, warnings

`unparsed`: list of `{"kind", "file", "reason"}`. Kinds: `cobol`, `scheduler`, `unread`, `duplicate`, `error`. Every file you saw and could not read goes here. Also a statement you saw and could not parse, for example "line 40: EXEC SQL has no END-EXEC, statement not parsed".

`meta.limits`: copy this list, then add limits of your own (a pattern you could not write, a file kind you skipped).
- COBOL is read as fixed format. Free format files are listed as not parsed.
- COPY REPLACING is not applied. A copybook is expanded as written.
- A variable call target is resolved only from VALUE clauses and literal MOVEs in the same program.
- A called subprogram gets no DDs from its caller's JCL step.
- SORT and most in-stream control cards are not read. IDCAMS cards are read for the datasets they change, as facts only. The dataset mode on a utility step's edge comes from DISP. A card that uses a symbol is skipped.
- The program a step runs is read from PARM for DFSRRC00 and from a RUN PROGRAM card for IKJEFT01. Other drivers that start a program by name are not read.
- IF/THEN/ELSE and COND= in JCL are not modeled. Step order is file order.
- Nested PROC calls and INCLUDE members are not followed. JCL text inside a COBOL literal is noticed but makes no edge.
- EXEC CICS RETURN TRANSID, START and SEND MAP are not edges.
- Only Control-M XML and shell wrappers that name JCL files are read as schedulers.
- DCB, LRECL and RECFM are not read.
- A contract edge is high when both sides COPY the same layout. High means shared layout, not proven equal.
- LINK and XCTL are both call edges. Control flow is not modeled.
- The graph was assembled by reading search hits. Line counts are approximate. Dormancy is not computed without supplied dates.

`analysis.warnings`: free text lines. Include every warning named in this file, the scheduler recipes, and any step repeated in a job: "FILE:LINE: job J repeats a step name. This one is called J.STEP#2."

## 12. Large trees

Above about 60 source files, do not build one graph in one pass.
1. Partition by top-level folder (one partition per folder under the root; loose files at the root form one). Count files with Glob per folder.
2. Extract each partition separately. Use one `dependency-cartographer` agent per partition. Give each its folder, this file and the recipes. Each writes `partition-<folder>.json`: nodes, edges, unparsed, and a data table of `{program, dataset, modes, layouts, evidence}` for every program-to-dataset pair. It may Glob outside its folder to see whether a name exists, but it writes only what its own files say.
3. Targets outside the partition are written as `ext:NAME`.
4. Merge. Concatenate nodes and edges. Apply the duplicate rule (first partition in sorted order keeps the id). Join evidence on equal keys.
5. Resolve cross-partition targets last. For each `ext:NAME` edge, look for a program, copybook or proc of that name in another partition. Found: rewrite the edge to the real id and delete the `ext:` node if nothing else points to it. The edge stays as written, confidence unchanged. Not found: leave it.
6. Derive contract edges from the merged data tables (section 8), so a dataset shared across partitions gets its writer-reader pairs. Layout sets come from each table row.
7. Run entry points, reachability and dead code (section 10) on the merged graph.

Label as `inference` anything you did not compute on the merged tables: a cycle across partitions, a layout you did not compare, a reachability you did not walk. Say so in `analysis.warnings`, and set `"inference": true` on the downstream entry. Say in `00-summary.md` which partitions were done and which checks were skipped.

## 13. Graph file shape

`graph.json` top-level keys, in this order:
- `schema_version`: `"0.2"`.
- `meta`: `{"tool", "version", "target" (root folder name), "git_dates" (false), "cloc" (false), "limits", "files_seen" (count per file kind)}`.
- `nodes`: sorted by id. Downstream files take unit ids from here. Waves hold programs, jobs, procs and scheduler jobs only. Steps, copybooks and datasets move with their owner.
- `edges`: sorted by kind, src, dst, mode.
- `unparsed`.
- `analysis`.

Edge rules downstream relies on: every `src` and `dst` is a node id. A `?dynamic:` target is `resolved` false. An unresolved edge is never `high`. No duplicate keys.

`analysis` keys the lean method fills:
- `as_of`, `dormant_years`
- `entry_points`, `dead_code_candidates` (`unreachable`, `dormant`, `unknown`), `dead_code_reasons` (id to text)
- `unresolved_dynamic`, `embedded_jcl`, `runtime_named`, `utility_writes`
- `unscheduled_jobs`, `warnings`
- `sccs`, `self_recursive`, `fan_in`, `fan_out`, `data_hubs`, `articulation_points`, `god_modules`, `wave_seed`: worked in `graph-analysis.md`. Fill them only as far as it says. A key you cannot fill is omitted, not guessed. Waves and risks cite `sccs` and `dead_code_candidates` ids.
- `reachable_nodes`, `reachable_programs`, `structure_basis`: fill when you walked reachability.

Keys the lean method drops: `edge_counts`, `node_counts`, `articulation_basis`. They add nothing a reader needs.
